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


def clean_patient_name(raw_name: Optional[str]) -> Optional[str]:
    """Clean conversational filler words, polite phrases, and punctuation from extracted patient names."""
    if not raw_name:
        return None
    import re
    cleaned = raw_name.strip()
    cleaned = re.sub(r'^(?:my\s*(?:full\s*)?name\s*(?:is)?|i\s*am|this\s*is|name[:\s]+)\s*', '', cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'\b(thank\s*you|thanks|please|pls|and|i\s*need|i\s*want|booking|appointment|here|hello|hi)\b.*$', '', cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'[,.!?_\-:]+$', '', cleaned).strip()
    words = cleaned.split()
    if words and len(cleaned) >= 2:
        return " ".join([w.capitalize() for w in words])
    return cleaned if len(cleaned) >= 2 else None


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
    name = clean_patient_name(name)

    # Multi-tier deduplication lookup: check conversation_id, email, then phone
    existing = None
    if conversation_id:
        existing = await fetch_one(
            "SELECT id, name, email, phone, crm_id FROM leads WHERE tenant_id = ? AND conversation_id = ? ORDER BY created_at DESC LIMIT 1",
            (tenant_id, conversation_id)
        )
    if not existing and email:
        existing = await fetch_one(
            "SELECT id, name, email, phone, crm_id FROM leads WHERE tenant_id = ? AND lower(email) = lower(?) LIMIT 1",
            (tenant_id, email)
        )
    if not existing and phone:
        existing = await fetch_one(
            "SELECT id, name, email, phone, crm_id FROM leads WHERE tenant_id = ? AND phone = ? LIMIT 1",
            (tenant_id, phone)
        )

    # Merge with previous values if this turn only added contact details
    if existing:
        name = name or existing.get("name")
        email = email or existing.get("email")
        phone = phone or existing.get("phone")

    # Determine lead score
    has_contact = bool(email or phone)
    has_specific_interest = bool(interest)
    has_near_timeline = bool(timeline_text and any(w in timeline_text.lower() for w in ["month", "week", "soon", "now", "immediate", "30", "60", "saturday", "tomorrow", "upcoming", "next"]))

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
    if existing:
        lead_id = existing["id"]
        await execute(
            "UPDATE leads SET name = COALESCE(?, name), email = COALESCE(?, email), phone = COALESCE(?, phone), "
            "interest = COALESCE(?, interest), budget_text = COALESCE(?, budget_text), "
            "timeline_text = COALESCE(?, timeline_text), score = ?, score_reason = ?, "
            "summary = ?, updated_at = ? WHERE id = ?",
            (name, email, phone, interest, budget_text, timeline_text, score, reason[:200], summary[:300], now_iso, lead_id)
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

    # Only dispatch real-time team alerts (Telegram & Slack) when contact details are present,
    # and avoid duplicate pings if an alert was already sent for this patient
    already_alerted = bool(existing and (existing.get("email") or existing.get("phone")))

    if has_contact and not already_alerted:
        from app.integrations.telegram import TelegramAdapter
        telegram = TelegramAdapter()
        await telegram.send_message(
            f"🚨 *NEW PATIENT LEAD CAPTURED!*\n\n"
            f"👤 *Name:* {name or 'Visitor'}\n"
            f"📧 *Email:* {email or 'N/A'}\n"
            f"📞 *Phone:* {phone or 'N/A'}\n"
            f"🦷 *Interest:* {interest or 'General Appointment'}\n"
            f"📊 *Score:* {score.upper()}\n"
            f"📝 *Summary:* {summary[:200]}"
        )

        from app.integrations.slack import SlackAdapter
        slack = SlackAdapter()
        await slack.send_message(
            text=f"🚨 New Patient Lead: {name or 'Visitor'} ({score.upper()})",
            blocks=[
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🚨 New Patient Lead Captured"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Name:* {name or 'Visitor'}"},
                        {"type": "mrkdwn", "text": f"*Score:* {score.upper()}"},
                        {"type": "mrkdwn", "text": f"*Email:* {email or 'N/A'}"},
                        {"type": "mrkdwn", "text": f"*Phone:* {phone or 'N/A'}"},
                        {"type": "mrkdwn", "text": f"*Interest:* {interest or 'General'}"},
                        {"type": "mrkdwn", "text": f"*Timeline:* {timeline_text or 'Soon'}"}
                    ]
                }
            ]
        )

        from app.integrations.airtable import AirtableAdapter
        airtable = AirtableAdapter()
        await airtable.create_record(fields={
            "Name": f"{name or 'Visitor'} (Score: {score.upper()})",
            "Notes": f"Email: {email or 'N/A'} | Phone: {phone or 'N/A'} | Interest: {interest or 'General'} | {summary[:200]}"
        })
    # Dispatch real HubSpot contact
    try:
        from app.integrations.hubspot import HubSpotAdapter
        hubspot = HubSpotAdapter()
        hs_res = await hubspot.upsert_contact(
            email=email or f"lead_{uuid.uuid4().hex[:6]}@patient.brightsmiledental.com",
            name=name,
            phone=phone,
            score=score,
            source="leadpilot_chat",
            summary=summary
        )
        if hs_res and hs_res.get("crm_id"):
            crm_id = str(hs_res["crm_id"])
            result["crm_id"] = crm_id
            await execute("UPDATE leads SET crm_id = ? WHERE id = ?", (crm_id, lead_id))
    except Exception as e:
        logger.error(f"HubSpot dispatch error: {e}")

    # Dispatch patient confirmation email if valid email is present
    if email and "@" in email and "example.com" not in email and "patient.brightsmiledental.com" not in email:
        try:
            from app.integrations.gmail import EmailAdapter
            emailer = EmailAdapter()
            email_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 580px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff;">
                <div style="text-align: center; padding-bottom: 16px; border-bottom: 2px solid #0d9488;">
                    <h1 style="color: #0d9488; margin: 0; font-size: 22px;">🦷 BrightSmile Dental</h1>
                    <p style="color: #64748b; font-size: 13px; margin: 4px 0 0 0;">Official Appointment Confirmation</p>
                </div>
                <div style="padding: 20px 0; color: #1e293b; line-height: 1.6;">
                    <p>Dear <strong>{name or 'Patient'}</strong>,</p>
                    <p>Your appointment reservation has been officially received and scheduled with our clinical team at BrightSmile Dental!</p>
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 16px 0;">
                        <p style="margin: 4px 0;"><strong>🏥 Clinic:</strong> BrightSmile Dental Suite 400</p>
                        <p style="margin: 4px 0;"><strong>📅 Time:</strong> {timeline_text or 'Upcoming'}</p>
                        <p style="margin: 4px 0;"><strong>🩺 Treatment / Interest:</strong> {interest or 'General Dentistry'}</p>
                        <p style="margin: 4px 0;"><strong>📞 Contact Registered:</strong> {phone or email}</p>
                    </div>
                    <p>If you need to reschedule or have any questions beforehand, reply directly to this email or call our desk at <strong>(555) 019-2831</strong>.</p>
                    <p style="margin-top: 24px;">Warm regards,<br><strong>BrightSmile Clinical Team</strong></p>
                </div>
                <div style="border-top: 1px solid #f1f5f9; padding-top: 12px; text-align: center; font-size: 11px; color: #94a3b8;">
                    BrightSmile Dental Clinic • 123 Healthcare Plaza, Suite 400 • Mon-Sat Services
                </div>
            </div>
            """
            await emailer.send_email(
                to_addr=email,
                subject=f"🦷 BrightSmile Dental: Appointment Confirmed for {name or 'You'}",
                body=email_html,
                is_html=True
            )
        except Exception as e:
            logger.error(f"Confirmation email dispatch error: {e}")

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
    """Flag conversation for human agent takeover and post Telegram / Slack notification."""
    now_iso = datetime.now(timezone.utc).isoformat()
    await execute(
        "UPDATE conversations SET status = 'handoff' WHERE id = ?",
        (conversation_id,)
    )
    from app.integrations.telegram import TelegramAdapter
    telegram = TelegramAdapter()
    await telegram.send_message(
        f"⚠️ *HUMAN STAFF HANDOFF REQUESTED!*\n\n"
        f"📋 *Reason:* {reason}\n"
        f"💬 *Conversation ID:* `{conversation_id}`"
    )
    from app.integrations.slack import SlackAdapter
    slack = SlackAdapter()
    await slack.send_message(
        text=f"⚠️ Human Staff Handoff: {reason}",
        blocks=[
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "⚠️ Front-Desk Human Handoff Needed"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Reason:* {reason}\n*Conversation ID:* `{conversation_id}`"}
            }
        ]
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
