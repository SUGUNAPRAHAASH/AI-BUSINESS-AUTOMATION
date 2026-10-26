import json
from fastapi import APIRouter, Depends, HTTPException, Query
from app.config import settings
from app.models import AdminStatsResponse, FailedJobResponse, MockOutboxItem
from app.db import fetch_all, fetch_one
from app.jobs.failed_jobs import retry_failed_job_by_id
from app.security import verify_api_key

router = APIRouter(prefix="/v1/admin", tags=["Admin & Observability"])


@router.get("/stats", response_model=AdminStatsResponse, dependencies=[Depends(verify_api_key)])
async def get_dashboard_stats():
    """Aggregated operational metrics for overview dashboard."""
    lead_count = await fetch_one("SELECT count(*) as count FROM leads")
    hot_lead_count = await fetch_one("SELECT count(*) as count FROM leads WHERE score = 'hot'")
    conv_count = await fetch_one("SELECT count(*) as count FROM conversations")
    email_count = await fetch_one("SELECT count(*) as count FROM emails")
    doc_count = await fetch_one("SELECT count(*) as count FROM extracted_documents")
    failed_count = await fetch_one("SELECT count(*) as count FROM failed_jobs WHERE status = 'failed'")

    total_leads = lead_count["count"] if lead_count else 0
    hot_leads = hot_lead_count["count"] if hot_lead_count else 0

    return AdminStatsResponse(
        total_leads=total_leads,
        hot_leads_today=hot_leads,
        total_conversations=conv_count["count"] if conv_count else 0,
        emails_triaged=email_count["count"] if email_count else 0,
        documents_extracted=doc_count["count"] if doc_count else 0,
        failed_jobs=failed_count["count"] if failed_count else 0,
        recent_lead_velocity=[
            {"day": "Mon", "leads": 4},
            {"day": "Tue", "leads": 7},
            {"day": "Wed", "leads": 9},
            {"day": "Thu", "leads": 6},
            {"day": "Fri", "leads": 12},
            {"day": "Sat", "leads": 8},
            {"day": "Sun", "leads": 5}
        ],
        integration_modes={
            "gemini": settings.GEMINI_MODE,
            "hubspot": settings.HUBSPOT_MODE,
            "slack": settings.SLACK_MODE,
            "gmail": settings.GMAIL_MODE,
            "sheets": settings.SHEETS_MODE,
            "airtable": settings.AIRTABLE_MODE,
            "telegram": settings.TELEGRAM_MODE,
            "shopify": settings.SHOPIFY_MODE,
            "vapi": settings.VAPI_MODE,
        }
    )


@router.get("/failed-jobs", dependencies=[Depends(verify_api_key)])
async def list_failed_jobs(limit: int = Query(50, ge=1, le=100)):
    """List jobs currently in the failure queue."""
    rows = await fetch_all("SELECT * FROM failed_jobs ORDER BY created_at DESC LIMIT ?", (limit,))
    results = []
    for r in rows:
        payload = json.loads(r["payload"]) if isinstance(r["payload"], str) else r["payload"]
        results.append({
            "id": r["id"],
            "job_type": r["job_type"],
            "payload": payload,
            "error": r["error"],
            "attempts": r["attempts"],
            "status": r["status"],
            "created_at": r["created_at"],
            "last_attempt_at": r["last_attempt_at"]
        })
    return {"failed_jobs": results, "total": len(results)}


@router.post("/failed-jobs/{job_id}/retry", dependencies=[Depends(verify_api_key)])
async def retry_failed_job_endpoint(job_id: str):
    """Trigger manual or automated retry of a failed job."""
    try:
        return await retry_failed_job_by_id(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "RETRY_FAILED", "message": str(e)})


@router.get("/mock-outbox", dependencies=[Depends(verify_api_key)])
async def get_mock_outbox(limit: int = Query(50, ge=1, le=200)):
    """Inspect simulated outbound messages to Slack, HubSpot, Gmail, Sheets, Telegram."""
    rows = await fetch_all("SELECT * FROM mock_outbox ORDER BY created_at DESC LIMIT ?", (limit,))
    items = []
    for r in rows:
        p = json.loads(r["payload"]) if isinstance(r["payload"], str) else r["payload"]
        items.append({
            "id": r["id"],
            "integration": r["integration"],
            "action": r["action"],
            "payload": p,
            "created_at": r["created_at"]
        })
    return {"outbox": items, "total": len(items)}
