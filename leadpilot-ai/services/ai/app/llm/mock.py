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

        # 1. Lead extraction and tool calling across current and prior messages
        all_conversation_text = " ".join([m.get("content", "") for m in messages]) + " " + last_user_msg

        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', last_user_msg) or re.search(r'[\w\.-]+@[\w\.-]+\.\w+', all_conversation_text)
        phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', last_user_msg) or re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', all_conversation_text)
        budget_match = re.search(r'(?:budget\s*(?:around|of|is)?\s*[\$]?\s*(\d+[\d,]*))|([\$]\s*\d+[\d,]*)', last_user_msg, re.IGNORECASE)
        timeline_match = re.search(r'(?:start|in|within|next)?\s*(next\s*month|next\s*week|soon|immediately|\d+\s*(?:days|weeks|months))', last_user_msg, re.IGNORECASE)
        name_match = re.search(r'(?:my\s*(?:full\s*)?name\s*(?:is)?|i\s*am|this\s*is|name[:\s]+)\s*([a-zA-Z\s]+?)(?:,|$|\.|\b(?:my|email|phone|contact)\b)', last_user_msg, re.IGNORECASE)
        if not name_match:
            name_match = re.search(r'(?:my\s*(?:full\s*)?name\s*(?:is)?|i\s*am|this\s*is|name[:\s]+)\s*([a-zA-Z\s]+?)(?:,|$|\.|\b(?:my|email|phone|contact)\b)', all_conversation_text, re.IGNORECASE)

        # 2. Check for tool invocation needs
        msg_lower = last_user_msg.lower()
        extracted_name = name_match.group(1).strip() if name_match else None
        has_appointment = bool(re.search(r'app?o[iy]nt?m?e?nt|schedul|book|slot|reserve', msg_lower)) or bool(re.search(r'app?o[iy]nt?m?e?nt|schedul|book|slot|reserve', all_conversation_text.lower()))
        has_saturday = bool(re.search(r'sat(ur(day)?)?|weekend', msg_lower)) or bool(re.search(r'sat(ur(day)?)?|weekend', all_conversation_text.lower()))
        has_whitening = "whiten" in msg_lower or "whiten" in all_conversation_text.lower()
        has_invisalign = "invisalign" in msg_lower or "brace" in msg_lower or "invisalign" in all_conversation_text.lower()
        has_cleaning = "clean" in msg_lower or "checkup" in msg_lower or "exam" in msg_lower
        has_hours = "hour" in msg_lower or "open" in msg_lower or "time" in msg_lower

        patient_name = extracted_name or ("Priya Nair" if "priya" in all_conversation_text.lower() else "Valued Patient")
        contact_email = email_match.group(0) if email_match else None
        contact_phone = phone_match.group(0) if phone_match else None

        if extracted_name or email_match or phone_match:
            tool_calls.append(ToolCall(
                name="capture_lead",
                arguments={
                    "name": patient_name,
                    "email": contact_email,
                    "phone": contact_phone,
                    "interest": "Appointment Booking" if has_appointment else ("Invisalign" if has_invisalign else "Teeth Whitening"),
                    "budget_text": budget_match.group(0) if budget_match else None,
                    "timeline_text": "Saturday at 11:00 AM" if (has_appointment and has_saturday) else (timeline_match.group(0) if timeline_match else "Upcoming")
                }
            ))

        if "horse" in msg_lower or "dog" in msg_lower or "cat" in msg_lower:
            tool_calls.append(ToolCall(
                name="request_human_handoff",
                arguments={"reason": "Customer inquiry outside human dental practice scope (veterinary/animals)"}
            ))

        # 3. Construct response text
        if "horse" in msg_lower or "dog" in msg_lower or "cat" in msg_lower:
            content = "I apologize, but BrightSmile Dental is strictly a human dental practice. We do not treat animals or pets. If you have any inquiries regarding human dental care or would like to speak to our reception staff, I would be pleased to assist."
        elif (email_match or phone_match) and (has_appointment or "reserv" in all_conversation_text.lower() or "slot" in all_conversation_text.lower()):
            first_name = patient_name.split()[0].title() if patient_name else "there"
            contact_summary = []
            if contact_email:
                contact_summary.append(contact_email)
            if contact_phone:
                contact_summary.append(contact_phone)
            contact_str = " and ".join(contact_summary) if contact_summary else "your contact info"
            timing = "this Saturday at 11:00 AM" if has_saturday else "your requested time"
            content = f"Thank you so much, {first_name}! Your appointment has been officially confirmed for {timing} with Dr. Sarah Mitchell at BrightSmile Dental. We have dispatched a confirmation and calendar invitation to {contact_str}. Our clinical team looks forward to welcoming you!"
        elif extracted_name and not (email_match or phone_match):
            first_name = extracted_name.split()[0].title()
            content = f"Thank you, {first_name}! I have noted your details and reserved your appointment slot at BrightSmile Dental. Could you also share your phone number or email address so our reception team can send you the confirmation and calendar invite?"
        elif has_appointment and (has_saturday or "11" in msg_lower or "morning" in msg_lower):
            content = "We are open on Saturdays from 9:00 AM to 2:00 PM, and our 11:00 AM operatory slot is available! To reserve this appointment for you, could I please have your full name?"
        elif has_whitening:
            content = "Professional in-office teeth whitening at BrightSmile Dental is $299 for a 1-hour laser treatment. We also offer take-home kits for $199, and 0% financing over 3 months. Would you like to schedule an appointment or check available times?"
        elif has_invisalign:
            content = "BrightSmile Dental is a Premier Invisalign Provider! Treatment costs typically range between $3,500 and $5,500 depending on alignment complexity. We offer complimentary 3D digital scans. Would you like to book a consultation?"
        elif has_cleaning:
            content = "A regular dental exam, hygiene checkup, and standard cleaning at BrightSmile Dental is $120. We have slots open during weekdays and Saturday mornings. What day works best for you?"
        elif has_hours or has_saturday:
            content = "BrightSmile Dental is open Monday through Friday from 8:00 AM to 7:00 PM, and Saturdays from 9:00 AM to 2:00 PM for appointments and emergency care. We are closed on Sundays."
        elif has_appointment:
            content = "I would be happy to help you book an appointment! We are open Monday to Friday 8:00 AM - 7:00 PM and Saturday 9:00 AM - 2:00 PM. What day and preferred time work best for you?"
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
            content = "Hello and welcome to BrightSmile Dental! We provide general dental care, teeth whitening ($299), Invisalign, crowns, and Saturday emergency appointments. How can we assist with your smile today?"

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
