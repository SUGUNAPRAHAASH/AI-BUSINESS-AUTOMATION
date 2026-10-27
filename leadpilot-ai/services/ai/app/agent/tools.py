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


def classify_clinical_severity(text: str) -> Dict[str, Any]:
    """
    Classify clinical symptoms or user inquiries into severity categories and match specialist doctors.
    """
    t = (text or "").lower()
    # Level 1: Urgent / Emergency
    if any(k in t for k in ["pain", "severe", "emergency", "bleed", "bleeding", "swelling", "swollen", "broken", "toothache", "trauma", "abscess", "wisdom tooth", "fell", "knocked", "unbearable", "urgent", "ache"]):
        return {
            "severity": "urgent",
            "severity_label": "High Urgency / Acute Care",
            "color": "#ef4444",
            "badge": "🚨 Urgent / Pain",
            "priority": 1,
            "recommended_doctors": ["doc-sarah", "doc-marcus"],
            "guidance": "Priority triage: Fast-track consultation with Dr. Sarah Mitchell (Lead Dental Surgeon) or Dr. Marcus Vance in Operatory 1/4. For uncontrollable bleeding, call 24/7 hotline (555) 019-9000."
        }
    # Level 2: Orthodontics & Clear Aligners
    if any(k in t for k in ["invisalign", "braces", "aligner", "straighten", "gap", "crooked", "overbite", "underbite", "crossbite", "bite", "retainer", "orthodontic", "crowding"]):
        return {
            "severity": "orthodontic",
            "severity_label": "Specialized Orthodontics",
            "color": "#0284c7",
            "badge": "🦷 Orthodontics & Aligners",
            "priority": 2,
            "recommended_doctors": ["doc-alex"],
            "guidance": "Specialist referral: Dr. Alex Rivera, DMD in Operatory 2 for 3D iTero digital scanning and custom aligner treatment."
        }
    # Level 3: Cosmetic & Aesthetic Smile Design
    if any(k in t for k in ["whiten", "whitening", "veneer", "bonding", "stain", "yellow", "cosmetic", "smile", "aesthetic", "porcelain", "lumineer"]):
        return {
            "severity": "cosmetic",
            "severity_label": "Cosmetic Smile Enhancement",
            "color": "#10b981",
            "badge": "✨ Cosmetic & Whitening",
            "priority": 3,
            "recommended_doctors": ["doc-priya"],
            "guidance": "Cosmetic consultation: Dr. Priya Patel, BDS in Operatory 3 for shade assessment, laser whitening, or porcelain veneer evaluation."
        }
    # Level 4: Routine & Preventive Care
    return {
        "severity": "routine",
        "severity_label": "Routine & Preventive Care",
        "color": "#0d9488",
        "badge": "🩺 Routine & Checkup",
        "priority": 4,
        "recommended_doctors": ["doc-sarah", "doc-marcus"],
        "guidance": "Comprehensive 30-minute exam, gentle hygiene cleaning, and digital preventive diagnostics with Dr. Sarah Mitchell or Dr. Marcus Vance."
    }


async def capture_lead(
    tenant_id: str,
    conversation_id: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    location: Optional[str] = None,
    interest: Optional[str] = None,
    budget_text: Optional[str] = None,
    timeline_text: Optional[str] = None,
    source: str = "chat",
    doctor_id: Optional[str] = None,
    appointment_date: Optional[str] = None,
    appointment_time: Optional[str] = None
) -> Dict[str, Any]:
    """Capture or update a qualified prospective patient lead with strict clinical intake validation."""
    now_iso = datetime.now(timezone.utc).isoformat()
    name = clean_patient_name(name)

    # Multi-tier deduplication lookup: check conversation_id, email, then phone
    existing = None
    if conversation_id:
        existing = await fetch_one(
            "SELECT id, name, email, phone, patient_location, crm_id FROM leads WHERE tenant_id = ? AND conversation_id = ? ORDER BY created_at DESC LIMIT 1",
            (tenant_id, conversation_id)
        )
    if not existing and email:
        existing = await fetch_one(
            "SELECT id, name, email, phone, patient_location, crm_id FROM leads WHERE tenant_id = ? AND lower(email) = lower(?) LIMIT 1",
            (tenant_id, email)
        )
    if not existing and phone:
        existing = await fetch_one(
            "SELECT id, name, email, phone, patient_location, crm_id FROM leads WHERE tenant_id = ? AND phone = ? LIMIT 1",
            (tenant_id, phone)
        )

    # Merge with previous values if this turn only added partial contact details
    if existing:
        name = name or existing.get("name")
        email = email or existing.get("email")
        phone = phone or existing.get("phone")
        location = location or existing.get("patient_location")

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

    loc_str = f" [Location: {location}]" if location else ""
    summary = f"Patient {name or 'Visitor'}{loc_str} inquiring about {interest or 'treatments'} (Budget: {budget_text or 'standard'}, Timeline: {timeline_text or 'unspecified'})."
    next_action = "Schedule initial 3D consultation scan with treatment coordinator." if score == "hot" else "Send informational brochure."

    lead_id = str(uuid.uuid4())
    if existing:
        lead_id = existing["id"]
        await execute(
            "UPDATE leads SET name = COALESCE(?, name), email = COALESCE(?, email), phone = COALESCE(?, phone), "
            "patient_location = COALESCE(?, patient_location), interest = COALESCE(?, interest), "
            "budget_text = COALESCE(?, budget_text), timeline_text = COALESCE(?, timeline_text), "
            "score = ?, score_reason = ?, summary = ?, updated_at = ? WHERE id = ?",
            (name, email, phone, location, interest, budget_text, timeline_text, score, reason[:200], summary[:300], now_iso, lead_id)
        )
    else:
        await execute(
            "INSERT INTO leads (id, tenant_id, conversation_id, name, email, phone, patient_location, interest, budget_text, timeline_text, score, score_reason, summary, source, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)",
            (lead_id, tenant_id, conversation_id, name, email, phone, location, interest, budget_text, timeline_text, score, reason[:200], summary[:300], source, now_iso, now_iso)
        )

    result = {
        "id": lead_id,
        "name": name,
        "email": email,
        "phone": phone,
        "location": location,
        "interest": interest,
        "budget_text": budget_text,
        "timeline_text": timeline_text,
        "score": score,
        "score_reason": reason[:200],
        "summary": summary[:300],
        "next_best_action": next_action
    }

    # Real-time team notifications (Telegram & Slack) when contact details are present
    already_alerted = bool(existing and (existing.get("email") or existing.get("phone")))

    if has_contact and not already_alerted:
        from app.integrations.telegram import TelegramAdapter
        telegram = TelegramAdapter()
        loc_display = f"\n📍 *Location:* {location}" if location else ""
        await telegram.send_message(
            f"🚨 *NEW PATIENT INTAKE INQUIRY!*\n\n"
            f"👤 *Name:* {name or 'Visitor'}\n"
            f"📧 *Email:* {email or 'N/A'}\n"
            f"📞 *Phone:* {phone or 'N/A'}{loc_display}\n"
            f"🦷 *Interest:* {interest or 'General Appointment'}\n"
            f"📊 *Score:* {score.upper()}\n"
            f"📝 *Summary:* {summary[:200]}"
        )

        from app.integrations.slack import SlackAdapter
        slack = SlackAdapter()
        await slack.send_message(
            text=f"🚨 New Patient Intake: {name or 'Visitor'} ({score.upper()})",
            blocks=[
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🚨 New Patient Intake Registered"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Name:* {name or 'Visitor'}"},
                        {"type": "mrkdwn", "text": f"*Score:* {score.upper()}"},
                        {"type": "mrkdwn", "text": f"*Email:* {email or 'N/A'}"},
                        {"type": "mrkdwn", "text": f"*Phone:* {phone or 'N/A'}"},
                        {"type": "mrkdwn", "text": f"*Location:* {location or 'N/A'}"},
                        {"type": "mrkdwn", "text": f"*Interest:* {interest or 'General'}"}
                    ]
                }
            ]
        )

        from app.integrations.airtable import AirtableAdapter
        airtable = AirtableAdapter()
        await airtable.create_record(fields={
            "Name": f"{name or 'Visitor'} (Score: {score.upper()})",
            "Notes": f"Email: {email or 'N/A'} | Phone: {phone or 'N/A'} | Location: {location or 'N/A'} | Interest: {interest or 'General'} | {summary[:200]}"
        })

    # HubSpot integration
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

    # Dispatch Hospital Administration Alert to prahaashnms18@gmail.com
    # STRICT RULE: ONLY the Hospital Alert arrives at prahaashnms18@gmail.com!
    try:
        from app.integrations.gmail import EmailAdapter
        emailer = EmailAdapter()

        triage_info = classify_clinical_severity(interest or summary)

        await emailer.send_hospital_intake_alert({
            "name": name or "Prospective Patient",
            "email": email or "Not provided",
            "phone": phone or "Not provided",
            "patient_location": location or "Not specified",
            "doctor_name": doctor_id or triage_info["recommended_doctors"][0],
            "date_time": f"{appointment_date} at {appointment_time}" if (appointment_date and appointment_time) else (timeline_text or "Intake Lead / Schedule Selection In Progress"),
            "service": interest or "Basic Consultation (30 mins)",
            "score": score,
            "notes": f"Triage: {triage_info['severity_label']} | {summary}"
        })
    except Exception as e:
        logger.error(f"Hospital email dispatch error: {e}")

    # If the user explicitly provided complete appointment parameters, reserve it atomically:
    if appointment_date and appointment_time and (email or phone):
        try:
            from app.routers.schedule import book_appointment, BookAppointmentRequest
            req = BookAppointmentRequest(
                doctor_id=doctor_id,
                patient_name=name or "Valued Patient",
                patient_email=email or "patient@brightsmile.com",
                patient_phone=phone,
                patient_location=location,
                appointment_date=appointment_date,
                start_time=appointment_time,
                duration_mins=30,
                service_type=interest or "Basic Consultation (30 mins)",
                notes=f"Reserved via AI conversation: {summary}"
            )
            booking_res = await book_appointment(req)
            result["appointment_booked"] = booking_res
        except Exception as e:
            logger.warning(f"Explicit booking note: {e}")

    if score == "hot":
        await insert_mock_outbox("slack", "hot_lead_alert", {
            "channel": "#sales-leads",
            "lead_id": lead_id,
            "name": name,
            "email": email,
            "location": location,
            "interest": interest,
            "score": score
        })

    return result


async def check_availability(date_str: str) -> Dict[str, Any]:
    """
    Check real live doctor schedules and appointments for conflict prevention.
    Returns doctor schedules, open 30-min slots, and explains overlap rules.
    """
    try:
        from app.db import fetch_all
        # Check doctors working on Saturday / given day
        doctors = await fetch_all("SELECT id, name, specialty, cabin FROM doctors WHERE is_active = 1")
        appointments = await fetch_all("SELECT doctor_id, doctor_name, start_time, end_time, patient_name FROM appointments WHERE status != 'cancelled'")

        doc_summary = []
        for d in doctors:
            booked_slots = [a["start_time"] for a in appointments if a["doctor_id"] == d["id"]]
            doc_summary.append({
                "doctor": d["name"],
                "specialty": d["specialty"],
                "cabin": d["cabin"],
                "booked_slots": booked_slots,
                "open_slots": [s for s in ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:30", "14:00"] if s not in booked_slots]
            })

        return {
            "date": date_str,
            "doctors_on_duty": doc_summary,
            "policy": "Each patient has an exclusive 30-minute consultation slot. Double-booking the same doctor at the same time is strictly prohibited. If a doctor is booked at a time (e.g. 11:00 AM), other available doctors on duty or the next open slot (e.g. 11:30 AM) are offered.",
            "status": "available"
        }
    except Exception as e:
        logger.warning(f"Error querying live schedule: {e}")
        return {
            "date": date_str,
            "available_slots": [
                {"time": "09:30", "dentist": "Dr. Sarah Mitchell, DDS", "specialty": "General Dentistry"},
                {"time": "11:00", "dentist": "Dr. Alex Rivera, DMD", "specialty": "Orthodontics & Implants"},
                {"time": "11:30", "dentist": "Dr. Sarah Mitchell, DDS", "specialty": "General Dentistry"},
                {"time": "14:00", "dentist": "Dr. Marcus Vance, DDS", "specialty": "Pediatric & Family"}
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
