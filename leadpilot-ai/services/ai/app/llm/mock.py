import re
import math
import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from app.llm.base import LLMResult, ToolCall


class MockLLMClient:
    """
    Deterministic, offline Mock LLM client.
    Generates intelligent responses for BrightSmile Dental demo scenarios,
    extracts entities via robust patterns, and generates deterministic normalized
    pseudo-embeddings so semantic vector ranking works offline with no network access.
    """

    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim

    async def generate(
        self,
        system: str,
        messages: List[Dict[str, str]],
        *,
        json_schema: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> LLMResult:
        start_time = time.time()
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        content = ""
        tool_calls: List[ToolCall] = []

        # 1. Lead extraction and tool calling
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', last_user_msg)
        phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', last_user_msg)
        budget_match = re.search(r'(?:budget\s*(?:around|of|is)?\s*[\$]?\s*(\d+[\d,]*))|([\$]\s*\d+[\d,]*)', last_user_msg, re.IGNORECASE)
        timeline_match = re.search(r'(?:start|in|within|next)?\s*(next\s*month|next\s*week|soon|immediately|\d+\s*(?:days|weeks|months))', last_user_msg, re.IGNORECASE)
        name_match = re.search(r'(?:my name is|i am|name[:\s]+)([a-zA-Z\s]+?)(?:,|$|\.|\b(?:my|email|phone)\b)', last_user_msg, re.IGNORECASE)

        # 2. Check for tool invocation needs
        msg_lower = last_user_msg.lower()
        if "invisalign" in msg_lower or "teeth whitening" in msg_lower or "cleaning" in msg_lower or "how much" in msg_lower or "weekend" in msg_lower or "hours" in msg_lower or "horses" in msg_lower:
            if "priya" in msg_lower or email_match or "interested" in msg_lower:
                # Capture lead tool call
                extracted_name = name_match.group(1).strip() if name_match else ("Priya Nair" if "priya" in msg_lower else None)
                tool_calls.append(ToolCall(
                    name="capture_lead",
                    arguments={
                        "name": extracted_name,
                        "email": email_match.group(0) if email_match else "priya@example.com",
                        "phone": phone_match.group(0) if phone_match else None,
                        "interest": "Invisalign" if "invisalign" in msg_lower else "Teeth Whitening",
                        "budget_text": budget_match.group(0) if budget_match else "4000",
                        "timeline_text": timeline_match.group(0) if timeline_match else "next month"
                    }
                ))
            else:
                # Search knowledge base tool call
                tool_calls.append(ToolCall(
                    name="search_knowledge_base",
                    arguments={"query": last_user_msg, "k": 5}
                ))

        if "horse" in msg_lower or "dog" in msg_lower or "cat" in msg_lower:
            tool_calls.append(ToolCall(
                name="request_human_handoff",
                arguments={"reason": "Customer inquiry outside human dental practice scope (veterinary/animals)"}
            ))

        # 3. Construct response text
        if "horse" in msg_lower or "treat horses" in msg_lower:
            content = "I apologize, but BrightSmile Dental is strictly a human dental clinic. We do not treat horses or any other animals. If you have any questions regarding human dental health, or would like to speak to our staff, I would be happy to connect you with our team."
        elif "teeth whitening" in msg_lower and "weekend" in msg_lower:
            content = "Professional in-office teeth whitening at BrightSmile Dental is $299 for a 1-hour laser whitening treatment. We are open for weekend appointments on Saturdays from 9:00 to 14:00 [Source: pricing.md] [Source: opening_hours.md]. Would you like me to check available slots for Saturday?"
        elif "priya" in msg_lower or ("invisalign" in msg_lower and email_match):
            content = "Thank you Priya! I've recorded your interest in Invisalign with your budget of around $4,000 for next month. A dedicated treatment coordinator from BrightSmile Dental will review your request and contact you at priya@example.com to arrange your complimentary 3D consultation scan."
        elif json_schema:
            content = json.dumps({
                "category": "support",
                "priority": "normal",
                "entities": {},
                "draft_reply": "Thank you for reaching out to BrightSmile Dental. We are processing your request.",
                "needs_human": False,
                "reason": "Standard inquiry",
                "action": "needs_approval"
            })
        else:
            content = f"Thank you for contacting BrightSmile Dental. Regarding your question: our team is pleased to assist with our full range of dental treatments and appointments. Please let us know how we can best support your smile!"

        latency_ms = int((time.time() - start_time) * 1000)
        return LLMResult(
            content=content,
            tool_calls=tool_calls,
            prompt_tokens=len(last_user_msg.split()) + 40,
            completion_tokens=len(content.split()) + 15,
            latency_ms=max(latency_ms, 8),
            model="mock-gemini-2.5",
            provider="mock"
        )

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Deterministic pseudo-embedding via character n-gram hashing.
        Produces consistent, normalized 768-dimensional vectors such that
        semantically related sentences share similar vector cosine scores!
        """
        results = []
        for text in texts:
            vec = [0.0] * self.embedding_dim
            clean_text = text.lower().strip()
            # Extract 3-grams and tokens
            tokens = re.findall(r'\b\w+\b', clean_text)
            ngrams = [clean_text[i:i+3] for i in range(max(0, len(clean_text) - 2))]
            combined = tokens + ngrams

            if not combined:
                combined = ["empty"]

            for item in combined:
                # Map token or 3-gram deterministically to dimensions
                h = int(hashlib.md5(item.encode("utf-8")).hexdigest(), 16)
                idx = h % self.embedding_dim
                val = ((h >> 8) % 1000) / 500.0 - 1.0  # value in [-1, 1]
                vec[idx] += val

            # Normalize to unit length
            norm = math.sqrt(sum(v * v for v in vec))
            if norm > 0:
                vec = [round(v / norm, 6) for v in vec]
            results.append(vec)

        return results
