from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models import LeadQualifyRequest, LeadResponse, LeadListResponse
from app.features.lead_scoring import qualify_lead_text
from app.db import execute, fetch_all, fetch_one, insert_mock_outbox
from app.security import verify_api_key

router = APIRouter(prefix="/v1/leads", tags=["Leads & CRM"])


@router.post("/qualify", response_model=LeadResponse, dependencies=[Depends(verify_api_key)])
async def qualify_lead_endpoint(req: LeadQualifyRequest):
    """Score and qualify lead text using rubric."""
    text = req.text or ""
    if not text and req.conversation_id:
        rows = await fetch_all(
            "SELECT content FROM messages WHERE conversation_id = ? AND role = 'user'",
            (req.conversation_id,)
        )
        text = " ".join([r["content"] for r in rows])

    result = await qualify_lead_text(text)
    return LeadResponse(**result)


@router.get("", response_model=LeadListResponse, dependencies=[Depends(verify_api_key)])
async def list_leads(
    score: Optional[str] = Query(None, pattern="^(hot|warm|cold)$"),
    limit: int = Query(20, ge=1, le=100)
):
    """List recent patient leads with optional score filter."""
    if score:
        rows = await fetch_all(
            "SELECT * FROM leads WHERE score = ? ORDER BY created_at DESC LIMIT ?",
            (score, limit)
        )
    else:
        rows = await fetch_all(
            "SELECT * FROM leads ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
    leads = [LeadResponse(**r) for r in rows]
    return LeadListResponse(leads=leads, total=len(leads))


@router.get("/{lead_id}", response_model=LeadResponse, dependencies=[Depends(verify_api_key)])
async def get_lead_by_id(lead_id: str):
    """Retrieve detailed lead record."""
    lead = await fetch_one("SELECT * FROM leads WHERE id = ?", (lead_id,))
    if not lead:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": f"Lead {lead_id} not found"})
    return LeadResponse(**lead)


@router.post("/{lead_id}/followup", dependencies=[Depends(verify_api_key)])
async def generate_and_send_followup(lead_id: str):
    """Generate personalized follow-up email for hot leads and send via mock/real outbox."""
    lead = await fetch_one("SELECT * FROM leads WHERE id = ?", (lead_id,))
    if not lead:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": f"Lead {lead_id} not found"})

    name = lead.get("name") or "Valued Patient"
    interest = lead.get("interest") or "Dental Care"
    email = lead.get("email")

    subject = f"Your BrightSmile Dental Consultation for {interest}"
    body = (
        f"Dear {name},\n\n"
        f"Thank you for contacting BrightSmile Dental regarding {interest}. "
        f"We would love to welcome you into our modern clinic for a complimentary 3D digital scan and consultation with our lead dentist.\n\n"
        f"Please reply with a preferred morning or afternoon time, or call us at (555) 019-9000.\n\n"
        f"Warm regards,\nBrightSmile Dental Patient Care Team"
    )

    outbox_id = None
    if email:
        outbox_id = await insert_mock_outbox("gmail", "send_followup_email", {
            "to": email,
            "subject": subject,
            "body": body
        })

    return {
        "status": "followup_generated",
        "lead_id": lead_id,
        "subject": subject,
        "body": body,
        "outbox_id": outbox_id
    }
