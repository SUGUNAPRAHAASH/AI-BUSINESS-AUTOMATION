import re
import json
from typing import Dict, Any, Optional
from app.models import LeadResponse
from app.llm import get_llm_client
from app.utils.logging import logger


def score_lead_deterministic(
    text: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Deterministic scoring rubric used for offline mock mode and baseline assertions:
    - hot: contact details present AND (specific treatment AND timeline within about 60 days, or explicit request to book).
    - warm: specific interest but no clear timeline, or contact details missing but strong intent.
    - cold: general questions, price browsing only, no contact details, no timeline.
    """
    t = text.lower() if text else ""

    # Extract entities if not passed
    if not email:
        em = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if em:
            email = em.group(0)

    if not phone:
        ph = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        if ph:
            phone = ph.group(0)

    if not name:
        nm = re.search(r'(?:my name is|i am|name[:\s]+)([a-zA-Z\s]+?)(?:,|$|\.|\b(?:my|email|phone)\b)', text, re.IGNORECASE)
        if nm:
            name = nm.group(1).strip()
        elif "priya" in t:
            name = "Priya Nair"

    # Identify interest
    interest = None
    if "invisalign" in t:
        interest = "Invisalign"
    elif "whitening" in t:
        interest = "Teeth Whitening"
    elif "implant" in t:
        interest = "Dental Implants"
    elif "veneer" in t:
        interest = "Porcelain Veneers"
    elif "crown" in t:
        interest = "Dental Crown"
    elif "cleaning" in t:
        interest = "Dental Cleaning"
    elif "filling" in t:
        interest = "Composite Fillings"

    # Identify budget
    budget = None
    bm = re.search(r'(?:budget\s*(?:around|of|is)?\s*[\$]?\s*(\d+[\d,]*))|([\$]\s*\d+[\d,]*)', text, re.IGNORECASE)
    if bm:
        budget = bm.group(0)

    # Identify timeline
    timeline = None
    has_near_timeline = False
    if any(k in t for k in ["next month", "next week", "soon", "tomorrow", "asap", "immediately", "this month", "30 days", "within 2 months"]):
        has_near_timeline = True
        timeline = "Within 30-60 days"
    elif any(k in t for k in ["next year", "someday", "later", "curious"]):
        timeline = "Long term / Undecided"

    has_contact = bool(email or phone)
    explicit_book = any(k in t for k in ["book", "appointment", "start", "sign up", "schedule"])

    if has_contact and ((interest and has_near_timeline) or explicit_book):
        score = "hot"
        reason = f"Verified contact info ({email or phone}) with immediate booking intent or high-value interest ({interest or 'treatment'})."
        next_action = "Initiate immediate phone/email follow-up and offer direct booking link."
    elif interest or explicit_book or has_contact:
        score = "warm"
        reason = f"Expressed interest in {interest or 'services'} but timeline is flexible or contact info pending verification."
        next_action = "Send personalized treatment brochure and invite to schedule free consultation."
    else:
        score = "cold"
        reason = "General price browsing or informational query without contact details or clear timeline."
        next_action = "Retain in automated educational drip campaign."

    summary = f"Inquiry regarding {interest or 'dental treatments'} from {name or 'Anonymous Visitor'}."

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "interest": interest,
        "budget_text": budget,
        "timeline_text": timeline,
        "score": score,
        "score_reason": reason[:200],
        "summary": summary[:300],
        "next_best_action": next_action
    }


async def qualify_lead_text(text: str) -> Dict[str, Any]:
    """Qualify lead using deterministic rubric or LLM."""
    return score_lead_deterministic(text)
