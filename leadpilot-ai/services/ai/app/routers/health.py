from datetime import datetime, timezone
from fastapi import APIRouter
from app.config import settings
from app.db import fetch_one
from app.models import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness check, DB verification, and integration mode status report."""
    db_ok = "connected"
    try:
        row = await fetch_one("SELECT 1 as alive")
        if not row:
            db_ok = "unresponsive"
    except Exception as e:
        db_ok = f"error: {str(e)}"

    return HealthResponse(
        status="healthy" if "error" not in db_ok else "degraded",
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_ok,
        embedding_dim=settings.EMBEDDING_DIM,
        modes={
            "gemini": settings.GEMINI_MODE,
            "hubspot": settings.HUBSPOT_MODE,
            "slack": settings.SLACK_MODE,
            "gmail": settings.GMAIL_MODE,
            "sheets": settings.SHEETS_MODE,
            "airtable": settings.AIRTABLE_MODE,
            "telegram": settings.TELEGRAM_MODE,
            "shopify": settings.SHOPIFY_MODE,
            "vapi": settings.VAPI_MODE,
        },
        last_llm_call="active"
    )
