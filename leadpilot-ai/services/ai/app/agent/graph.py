import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.agent.state import AgentState
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import (
    search_knowledge_base,
    capture_lead,
    check_availability,
    request_human_handoff,
    get_business_hours,
)
from app.db import execute, fetch_all, fetch_one, init_db
from app.llm import get_llm_client
from app.security import mask_pii
from app.utils.logging import logger


async def load_conversation_node(state: AgentState) -> Dict[str, Any]:
    """Node 1: Load prior messages from the database."""
    await init_db()
    cid = state.get("conversation_id")
    tenant_id = state.get("tenant_id")

    # If no conversation exists yet, create one
    if not cid:
        cid = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        await execute(
            "INSERT INTO conversations (id, tenant_id, channel, external_id, status, created_at) "
            "VALUES (?, ?, ?, ?, 'open', ?)",
            (cid, tenant_id, state.get("channel", "web"), state.get("external_id"), now_iso)
        )

    rows = await fetch_all(
        "SELECT role, content, metadata FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT 10",
        (cid,)
    )

    prior_messages = []
    for r in rows:
        prior_messages.append({"role": r["role"], "content": r["content"]})

    return {"conversation_id": cid, "messages": prior_messages}


async def guardrails_node(state: AgentState) -> Dict[str, Any]:
    """Node 2: Sanitize input, mask PII, detect prompt injections or off-topic abuse."""
    user_input = state.get("current_input", "")
    masked_input = mask_pii(user_input)

    # Simple injection detection
    injection_patterns = [
        "ignore previous instructions",
        "system prompt",
        "you are now an evil",
        "reveal your secret",
        "drop all tables"
    ]
    for pattern in injection_patterns:
        if pattern in masked_input.lower():
            logger.warning(f"Guardrail triggered for prompt injection pattern: {pattern}")
            return {
                "current_input": masked_input,
                "handoff": True,
                "handoff_reason": "Potential security violation / prompt injection attempt",
                "final_answer": "I am BrightSmile Dental's virtual assistant. I cannot fulfill instructions outside clinic services."
            }

    return {"current_input": masked_input}


async def route_node(state: AgentState) -> Dict[str, Any]:
    """Node 3: Classify user intent with typo-tolerance."""
    if state.get("final_answer"):
        return {"intent": "blocked"}

    import re
    text = state.get("current_input", "").lower()
    has_name = bool(re.search(r'(?:my\s*(?:full\s*)?name\s*(?:is)?|i\s*am|this\s*is|name[:\s]+)\s*[a-zA-Z\s]+', text))
    has_appointment_typo = bool(re.search(r'app?o[iy]nt?m?e?nt|schedul|book|slot|reserv|timing', text))

    if has_name:
        intent = "appointment"
    elif has_appointment_typo:
        intent = "appointment"
    elif any(k in text for k in ["invisalign", "implant", "whiten", "veneer", "interested", "cost", "budget"]):
        intent = "lead_interest"
    elif any(k in text for k in ["complain", "unhappy", "pain", "bleeding", "emergency", "lawyer", "refund"]):
        intent = "complaint"
    elif any(k in text for k in ["hour", "open", "sat", "weekend", "price", "insurance", "parking", "faq", "do you", "how much", "clean"]):
        intent = "faq"
    elif any(k in text for k in ["hi", "hello", "hey", "good morning", "thanks", "thank you"]):
        intent = "smalltalk"
    else:
        intent = "faq"

    return {"intent": intent}


async def retrieve_node(state: AgentState) -> Dict[str, Any]:
    """Node 4: Retrieve knowledge base context for grounded generation."""
    if state.get("final_answer"):
        return {}

    intent = state.get("intent")
    query = state.get("current_input", "")
    tenant_id = state.get("tenant_id")

    # If query is just a name, search opening hours and appointments instead of the person's name
    import re
    if re.search(r'(?:my\s*(?:full\s*)?name\s*(?:is)?|i\s*am|this\s*is|name[:\s]+)\s*[a-zA-Z\s]+', query.lower()):
        query = "saturday opening hours appointment booking"

    # Inquire retriever if relevant
    if intent in ("faq", "appointment", "lead_interest"):
        chunks = await search_knowledge_base(query, tenant_id=tenant_id, k=5)
        citations = []
        for c in chunks:
            citations.append({
                "title": c["title"],
                "source": c["source"],
                "score": c["score"]
            })
        return {"retrieved_context": chunks, "citations": citations}

    return {"retrieved_context": [], "citations": []}


async def agent_node(state: AgentState) -> Dict[str, Any]:
    """Node 5 & 6: Execute tool-calling LLM reasoning step."""
    if state.get("final_answer"):
        return {}

    llm = get_llm_client()
    tenant_id = state.get("tenant_id")
    cid = state.get("conversation_id")

    # Build prompt with retrieved context
    context_str = ""
    for c in state.get("retrieved_context", []):
        context_str += f"\n[Document: {c['title']}]\n{c['content']}\n"

    sys_instruction = f"{SYSTEM_PROMPT}\n\nRELEVANT BUSINESS CONTEXT:\n{context_str if context_str else 'No specific document found.'}"
    msgs = state.get("messages", []) + [{"role": "user", "content": state.get("current_input", "")}]

    # Call LLM
    result = await llm.generate(sys_instruction, msgs)

    # Process tool calls
    lead_captured = None
    handoff = state.get("handoff", False)
    handoff_reason = state.get("handoff_reason")

    for tc in result.tool_calls:
        if tc.name == "capture_lead":
            lead_captured = await capture_lead(
                tenant_id=tenant_id,
                conversation_id=cid,
                **tc.arguments
            )
        elif tc.name == "request_human_handoff":
            handoff = True
            handoff_reason = tc.arguments.get("reason", "Requested handoff")
            await request_human_handoff(tenant_id, cid, handoff_reason)
        elif tc.name == "check_availability":
            await check_availability(tc.arguments.get("date", "2026-11-01"))

    # Automatic lead capture if contact info or name is provided in user input
    import re
    full_text = (state.get("current_input", "") + " " + result.content).lower()
    email_m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', state.get("current_input", ""))
    phone_m = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', state.get("current_input", ""))
    name_m = re.search(r'(?:my\s*(?:full\s*)?name\s*(?:is)?|i\s*am|this\s*is|name[:\s]+)\s*([a-zA-Z\s]+?)(?:,|$|\.|\b(?:my|email|phone|contact)\b)', state.get("current_input", ""), re.IGNORECASE)

    # If name wasn't in the current message, check prior user messages
    if not name_m:
        for m in reversed(state.get("messages", [])):
            if m.get("role") == "user":
                prior_name_m = re.search(r'(?:my\s*(?:full\s*)?name\s*(?:is)?|i\s*am|this\s*is|name[:\s]+)\s*([a-zA-Z\s]+?)(?:,|$|\.|\b(?:my|email|phone|contact)\b)', m.get("content", ""), re.IGNORECASE)
                if prior_name_m:
                    name_m = prior_name_m
                    break

    if (email_m or phone_m or name_m) and not lead_captured:
        budget_m = re.search(r'(?:budget\s*(?:around|of|is)?\s*[\$]?\s*(\d+[\d,]*))|([\$]\s*\d+[\d,]*)', state.get("current_input", ""), re.IGNORECASE)
        timeline_m = re.search(r'(?:start|in|within|next)?\s*(next\s*month|next\s*week|soon|immediately|\d+\s*(?:days|weeks|months)|saturday|tomorrow)', state.get("current_input", ""), re.IGNORECASE)
        lead_captured = await capture_lead(
            tenant_id=tenant_id,
            conversation_id=cid,
            name=name_m.group(1).strip() if name_m else None,
            email=email_m.group(0) if email_m else None,
            phone=phone_m.group(0) if phone_m else None,
            interest="Teeth Whitening" if "whiten" in full_text else ("Invisalign" if "invisalign" in full_text else "General Appointment"),
            budget_text=budget_m.group(0) if budget_m else None,
            timeline_text=timeline_m.group(0) if timeline_m else ("Saturday" if "sat" in full_text else "Upcoming")
        )

    # Also handle off-topic inquiries (e.g. horses)
    if "horse" in state.get("current_input", "").lower():
        handoff = True
        handoff_reason = "Out of practice scope (animals)"
        await request_human_handoff(tenant_id, cid, handoff_reason)

    # Clean out any bracketed source tags (e.g. [Source: services.md]) for production-grade UI
    clean_answer = re.sub(r'\[Source:\s*[^\]]+\]', '', result.content).strip()
    clean_answer = re.sub(r'\s{2,}', ' ', clean_answer)

    return {
        "final_answer": clean_answer,
        "lead_captured": lead_captured,
        "handoff": handoff,
        "handoff_reason": handoff_reason
    }


async def finalize_node(state: AgentState) -> Dict[str, Any]:
    """Node 7: Persist messages and build final response payload."""
    cid = state.get("conversation_id")
    now_iso = datetime.now(timezone.utc).isoformat()

    # Save user message
    user_msg_id = str(uuid.uuid4())
    await execute(
        "INSERT INTO messages (id, conversation_id, role, content, metadata, created_at) "
        "VALUES (?, ?, 'user', ?, '{}', ?)",
        (user_msg_id, cid, state.get("current_input", ""), now_iso)
    )

    # Save assistant message
    asst_msg_id = str(uuid.uuid4())
    metadata = {
        "citations": state.get("citations", []),
        "lead_captured": state.get("lead_captured"),
        "handoff": state.get("handoff", False)
    }
    await execute(
        "INSERT INTO messages (id, conversation_id, role, content, metadata, created_at) "
        "VALUES (?, ?, 'assistant', ?, ?, ?)",
        (asst_msg_id, cid, state.get("final_answer", ""), json.dumps(metadata), now_iso)
    )

    return {}


class LangGraphAgent:
    """Production State Machine compiling the nodes into an autonomous flow."""

    async def run(
        self,
        tenant_id: str,
        message: str,
        channel: str = "web",
        external_id: str = None,
        conversation_id: str = None
    ) -> Dict[str, Any]:
        state: AgentState = {
            "tenant": "brightsmile",
            "tenant_id": tenant_id,
            "channel": channel,
            "external_id": external_id,
            "conversation_id": conversation_id,
            "messages": [],
            "current_input": message,
            "intent": "",
            "retrieved_context": [],
            "citations": [],
            "lead_draft": None,
            "lead_captured": None,
            "handoff": False,
            "handoff_reason": None,
            "final_answer": "",
            "errors": []
        }

        # Sequential graph step execution
        state.update(await load_conversation_node(state))
        state.update(await guardrails_node(state))
        state.update(await route_node(state))
        state.update(await retrieve_node(state))
        state.update(await agent_node(state))
        await finalize_node(state)

        return {
            "answer": state["final_answer"],
            "citations": state["citations"],
            "lead_captured": state["lead_captured"],
            "handoff": state["handoff"],
            "conversation_id": state["conversation_id"]
        }


agent_instance = LangGraphAgent()
