import re
from typing import Dict, Any
from app.config import settings


def triage_email(
    message_id: str,
    from_addr: str,
    subject: str,
    body: str
) -> Dict[str, Any]:
    text = f"{subject}\n{body}".lower()

    # Extract entities
    entities: Dict[str, Any] = {}
    date_match = re.search(r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|next week|\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b', text, re.IGNORECASE)
    if date_match:
        entities["date"] = date_match.group(0)

    name_match = re.search(r'(?:hi|hello|dear|thanks,?)\s+([a-zA-Z]+)', body, re.IGNORECASE)
    if name_match:
        entities["name"] = name_match.group(1).title()

    # Detect category
    if any(k in text for k in ["reschedule", "appointment", "cancel appointment", "friday", "booking"]):
        category = "appointment"
        priority = "normal"
    elif any(k in text for k in ["pricing", "cost", "quote", "interested in invisalign", "veneers", "new patient"]):
        category = "sales"
        priority = "high"
    elif any(k in text for k in ["invoice", "bill", "receipt", "insurance claim", "payment", "charge"]):
        category = "billing"
        priority = "normal"
    elif any(k in text for k in ["lottery", "crypto", "viagra", "casino", "wire transfer", "prince"]):
        category = "spam"
        priority = "low"
    elif any(k in text for k in ["pain", "hurt", "bleeding", "swelling", "unhappy", "terrible", "lawyer", "refund"]):
        category = "support"
        priority = "high"
    else:
        category = "support"
        priority = "normal"

    # Evaluate needs_human rule
    needs_human = False
    human_reason = "Standard routine automated triage."

    if category == "spam":
        action = "none"
        draft = ""
    else:
        if any(k in text for k in ["unhappy", "terrible", "sue", "lawyer", "malpractice", "worst"]):
            needs_human = True
            priority = "high"
            human_reason = "Customer complaint / dissatisfaction or legal sensitivity."
            draft = "Dear Patient,\n\nWe are truly sorry to hear about your experience. A patient relations director from BrightSmile Dental has been notified and will call you directly to resolve this.\n\nWarm regards,\nBrightSmile Dental Management"
        elif any(k in text for k in ["refund", "dispute", "overcharged"]):
            needs_human = True
            priority = "high"
            human_reason = "Financial dispute / refund demand requiring accounting approval."
            draft = "Dear Patient,\n\nThank you for bringing this billing matter to our attention. Our finance manager is reviewing your account history and will reply within 24 hours.\n\nWarm regards,\nBrightSmile Dental Accounts"
        elif any(k in text for k in ["severe pain", "bleeding", "fever", "swollen face", "pus"]):
            needs_human = True
            priority = "high"
            human_reason = "Acute clinical symptoms or medical urgency."
            draft = "URGENT DENTAL ADVICE:\n\nPlease contact our emergency line immediately at (555) 019-9000 or proceed to your nearest urgent care facility if experiencing facial swelling affecting breathing."
        elif category == "appointment":
            needs_human = True if not settings.AUTO_REPLY_ENABLED else False
            human_reason = "Appointment rescheduling request pending receptionist confirmation." if needs_human else "Auto-confirmed appointment change."
            requested_date = entities.get("date", "your requested date")
            draft = f"Hello,\n\nThank you for contacting BrightSmile Dental. We have received your request to reschedule regarding {requested_date}. We have noted this on your file and will confirm your updated appointment time shortly.\n\nWarm regards,\nBrightSmile Dental Front Desk"
        else:
            needs_human = True if not settings.AUTO_REPLY_ENABLED else False
            draft = "Hello,\n\nThank you for reaching out to BrightSmile Dental. We have received your message and our team will get back to you shortly.\n\nBest regards,\nBrightSmile Dental"

        action = "auto_sent" if (not needs_human and settings.AUTO_REPLY_ENABLED) else "needs_approval"

    return {
        "category": category,
        "priority": priority,
        "entities": entities,
        "sentiment": "negative" if any(w in text for w in ["unhappy", "pain", "refund", "sue"]) else "neutral",
        "draft_reply": draft,
        "needs_human": needs_human,
        "reason": human_reason,
        "action": action
    }
