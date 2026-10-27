import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from app.models import EmailTriageRequest, EmailTriageResponse
from app.features.email_triage import triage_email
from app.db import execute, fetch_all, fetch_one, insert_mock_outbox
from app.security import verify_api_key

router = APIRouter(prefix="/v1/emails", tags=["Emails & Triage"])


@router.post("/triage", response_model=EmailTriageResponse, dependencies=[Depends(verify_api_key)])
async def triage_email_endpoint(req: EmailTriageRequest):
    """Categorize incoming email, extract entities, evaluate needs_human, and draft response."""
    result = triage_email(
        message_id=req.message_id,
        from_addr=req.from_addr,
        subject=req.subject,
        body=req.body
    )
    email_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    await execute(
        "INSERT OR REPLACE INTO emails (id, tenant_id, message_id, from_addr, subject, body, category, entities, priority, draft_reply, action, created_at) "
        "VALUES (?, 'a0000000-0000-0000-0000-000000000001', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (email_id, req.message_id, req.from_addr, req.subject, req.body, result["category"], json.dumps(result["entities"]), result["priority"], result["draft_reply"], result["action"], now_iso)
    )

    # Intimate hospital side via email
    try:
        from app.integrations.gmail import EmailAdapter
        emailer = EmailAdapter()
        await emailer.send_hospital_intake_alert({
            "name": result["entities"].get("name") or req.from_addr.split("@")[0].title(),
            "email": req.from_addr,
            "phone": "Inquiry via Email",
            "doctor_name": "Clinic Triage Coordinator",
            "date_time": result["entities"].get("date") or "Triage Queue Pending",
            "service": f"Email Triage: {result['category'].upper()} ({result['priority'].upper()})",
            "score": "HOT" if result["priority"] == "high" else "WARM",
            "notes": f"Subject: {req.subject}\n\nDraft Reply Prepared:\n{result['draft_reply']}"
        })
    except Exception as e:
        pass

    result["id"] = email_id
    return EmailTriageResponse(**result)


@router.get("", dependencies=[Depends(verify_api_key)])
async def list_triaged_emails():
    """List triaged emails for review."""
    rows = await fetch_all("SELECT * FROM emails ORDER BY created_at DESC LIMIT 50")
    results = []
    for r in rows:
        ent = json.loads(r["entities"]) if isinstance(r["entities"], str) else r["entities"]
        results.append({
            "id": r["id"],
            "message_id": r["message_id"],
            "from_addr": r["from_addr"],
            "subject": r["subject"],
            "body": r["body"],
            "category": r["category"],
            "entities": ent,
            "priority": r["priority"],
            "draft_reply": r["draft_reply"],
            "action": r["action"],
            "created_at": r["created_at"]
        })
    return {"emails": results, "total": len(results)}


@router.post("/{email_id}/approve", dependencies=[Depends(verify_api_key)])
async def approve_email_reply(email_id: str):
    """Human approval: approves draft reply and dispatches via live EmailAdapter."""
    email_row = await fetch_one("SELECT * FROM emails WHERE id = ?", (email_id,))
    if not email_row:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": f"Email {email_id} not found"})

    await execute("UPDATE emails SET action = 'approved' WHERE id = ?", (email_id,))

    # Live dispatch to recipient
    from app.integrations.gmail import EmailAdapter
    emailer = EmailAdapter()
    send_res = await emailer.send_email(
        to_addr=email_row["from_addr"],
        subject=f"Re: {email_row['subject']}",
        body=email_row["draft_reply"]
    )
    return {"status": "approved", "email_id": email_id, "dispatch": send_res}



@router.post("/{email_id}/reject", dependencies=[Depends(verify_api_key)])
async def reject_email_reply(email_id: str):
    """Human rejection: marks draft as rejected."""
    email_row = await fetch_one("SELECT * FROM emails WHERE id = ?", (email_id,))
    if not email_row:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": f"Email {email_id} not found"})

    await execute("UPDATE emails SET action = 'rejected' WHERE id = ?", (email_id,))
    return {"status": "rejected", "email_id": email_id}
