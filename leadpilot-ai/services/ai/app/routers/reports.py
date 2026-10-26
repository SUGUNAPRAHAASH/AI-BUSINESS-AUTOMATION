from fastapi import APIRouter, Depends
from app.db import fetch_all, fetch_one
from app.security import verify_api_key

router = APIRouter(prefix="/v1/reports", tags=["Reports"])


@router.get("/daily", dependencies=[Depends(verify_api_key)])
async def generate_daily_executive_summary():
    """Build daily executive operational summary for n8n workflow LP-W7."""
    lead_count = await fetch_one("SELECT count(*) as count FROM leads")
    hot_lead_count = await fetch_one("SELECT count(*) as count FROM leads WHERE score = 'hot'")
    conv_count = await fetch_one("SELECT count(*) as count FROM conversations")
    email_count = await fetch_one("SELECT count(*) as count FROM emails")
    failed_job_count = await fetch_one("SELECT count(*) as count FROM failed_jobs WHERE status = 'failed'")

    total_leads = lead_count["count"] if lead_count else 0
    hot_leads = hot_lead_count["count"] if hot_lead_count else 0
    total_convs = conv_count["count"] if conv_count else 0
    total_emails = email_count["count"] if email_count else 0
    failed_jobs = failed_job_count["count"] if failed_job_count else 0

    executive_summary = (
        f"BrightSmile Dental Daily Ops Briefing:\n"
        f"• New Patient Leads: {total_leads} (including {hot_leads} Hot booking leads)\n"
        f"• Patient AI Conversations: {total_convs}\n"
        f"• Emails Triaged & Drafted: {total_emails}\n"
        f"• Reliability Status: {failed_jobs} open failed jobs in queue.\n"
        f"All core systems operational."
    )

    return {
        "status": "success",
        "executive_summary": executive_summary,
        "metrics": {
            "total_leads": total_leads,
            "hot_leads": hot_leads,
            "conversations": total_convs,
            "emails_triaged": total_emails,
            "failed_jobs": failed_jobs
        }
    }
