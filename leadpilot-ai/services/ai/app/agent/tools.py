import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.db import execute, fetch_one, insert_mock_outbox
from app.rag.retriever import HybridRetriever
from app.utils.logging import logger


async def search_knowledge_base(query: str, tenant_id: str, k: int = 5) -> List[Dict[str, Any]]:
    """Hybrid search retrieved chunks across BrightSmile Dental documentation."""
    retriever = HybridRetriever(tenant_id=tenant_id)
    return await retriever.search(query, top_k=k)


async def capture_lead(
    tenant_id: str,
    conversation_id: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    interest: Optional[str] = None,
    budget_text: Optional[str] = None,
    timeline_text: Optional[str] = None,
    source: str = "chat"
) -> Dict[str, Any]:
    """Capture or update a qualified prospective patient lead."""
    now_iso = datetime.now(timezone.utc).isoformat()

    # Determine lead score
    has_contact = bool(email or phone)
    has_specific_interest = bool(interest)
    has_near_timeline = bool(timeline_text and any(w in timeline_text.lower() for w in ["month", "week", "soon", "now", "immediate", "30", "60"]))

    if has_contact and (has_near_timeline or (has_specific_interest and budget_text)):
        score = "hot"
        reason = f"High intent with contact info ({email or phone}), specific treatment ({interest or 'dental'}), and near timeline ({timeline_text or 'active'})."
    elif has_specific_interest or has_contact:
        score = "warm"
        reason = f"Expressed interest in {interest or 'services'} but partial timeline or pending contact verification."
    else:
        score = "cold"
        reason = "General inquiry with no contact info or timeline provided."

    summary = f"Patient {name or 'Visitor'} inquiring about {interest or 'treatments'} (Budget: {budget_text or 'standard'}, Timeline: {timeline_text or 'unspecified'})."
    next_action = "Schedule initial 3D consultation scan with treatment coordinator." if score == "hot" else "Send informational brochure."

    lead_id = str(uuid.uuid4())
    existing = None
    if email:
        existing = await fetch_one(
            "SELECT id FROM leads WHERE tenant_id = ? AND lower(email) = lower(?)",
            (tenant_id, email)
        )

    if existing:
        lead_id = existing["id"]
        await execute(
            "UPDATE leads SET name = COALESCE(?, name), phone = COALESCE(?, phone), "
            "interest = COALESCE(?, interest), budget_text = COALESCE(?, budget_text), "
            "timeline_text = COALESCE(?, timeline_text), score = ?, score_reason = ?, "
            "summary = ?, updated_at = ? WHERE id = ?",
            (name, phone, interest, budget_text, timeline_text, score, reason[:200], summary[:300], now_iso, lead_id)
        )
    else:
        await execute(
            "INSERT INTO leads (id, tenant_id, conversation_id, name, email, phone, interest, budget_text, timeline_text, score, score_reason, summary, source, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)",
            (lead_id, tenant_id, conversation_id, name, email, phone, interest, budget_text, timeline_text, score, reason[:200], summary[:300], source, now_iso, now_iso)
        )

    result = {
        "id": lead_id,
        "name": name,
        "email": email,
        "phone": phone,
        "interest": interest,
        "budget_text": budget_text,
        "timeline_text": timeline_text,
        "score": score,
        "score_reason": reason[:200],
        "summary": summary[:300],
        "next_best_action": next_action
    }

    # If lead is hot, log mock outbox alert for sales team
    if score == "hot":
        await insert_mock_outbox("slack", "hot_lead_alert", {
            "channel": "#sales-leads",
            "lead_id": lead_id,
            "name": name,
            "email": email,
            "interest": interest,
            "score": score
        })

    return result


async def check_availability(date_str: str) -> Dict[str, Any]:
    """Check mock open operatories for a given date."""
    return {
        "date": date_str,
        "available_slots": [
            {"time": "09:30", "dentist": "Dr. Sarah Mitchell, DDS", "chair": "Operatory 2"},
            {"time": "11:15", "dentist": "Dr. Sarah Mitchell, DDS", "chair": "Operatory 1"},
            {"time": "14:00", "dentist": "Dr. Alex Chen, DMD", "chair": "Operatory 3"}
        ],
        "status": "available"
    }


async def request_human_handoff(tenant_id: str, conversation_id: str, reason: str) -> Dict[str, Any]:
    """Flag conversation for human agent takeover and post Slack notification."""
    now_iso = datetime.now(timezone.utc).isoformat()
    await execute(
        "UPDATE conversations SET status = 'handoff' WHERE id = ?",
        (conversation_id,)
    )
    await insert_mock_outbox("slack", "human_handoff_alert", {
        "channel": "#front-desk-alerts",
        "conversation_id": conversation_id,
        "reason": reason,
        "timestamp": now_iso
    })
    logger.info(f"[HANDOFF] Conversation {conversation_id} escalated: {reason}")
    return {"status": "handoff_requested", "reason": reason}


async def get_business_hours() -> Dict[str, Any]:
    """Get summarized business hours."""
    return {
        "weekdays": "Monday-Thursday: 8:00 to 18:00, Wednesday evening until 19:00, Friday: 8:00 to 17:00",
        "saturday": "Saturday: 9:00 to 14:00",
        "sunday": "Closed (Emergency line active)",
        "emergency_phone": "(555) 019-9000"
    }
