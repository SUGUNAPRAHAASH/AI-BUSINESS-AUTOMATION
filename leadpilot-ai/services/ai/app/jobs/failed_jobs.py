import json
from datetime import datetime, timezone
from typing import Dict, Any, Callable
from app.db import execute, fetch_one, insert_mock_outbox
from app.integrations import hubspot_adapter, slack_adapter, email_adapter
from app.utils.logging import logger

JOB_HANDLER_REGISTRY: Dict[str, Callable[[Dict[str, Any]], Any]] = {}


def register_job_handler(job_type: str, handler: Callable[[Dict[str, Any]], Any]):
    JOB_HANDLER_REGISTRY[job_type] = handler


async def handle_crm_sync_retry(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await hubspot_adapter.upsert_contact(**payload)


async def handle_slack_alert_retry(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await slack_adapter.send_message(**payload)


async def handle_email_send_retry(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await email_adapter.send_email(**payload)


# Pre-register default handlers
register_job_handler("crm_sync", handle_crm_sync_retry)
register_job_handler("slack_alert", handle_slack_alert_retry)
register_job_handler("email_send", handle_email_send_retry)


async def retry_failed_job_by_id(job_id: str) -> Dict[str, Any]:
    """Execute registered job handler for a failed job record and update status."""
    job = await fetch_one("SELECT id, job_type, payload, attempts, status FROM failed_jobs WHERE id = ?", (job_id,))
    if not job:
        raise ValueError(f"Failed job with ID {job_id} not found.")

    handler = JOB_HANDLER_REGISTRY.get(job["job_type"])
    if not handler:
        raise ValueError(f"No registered handler for job type '{job['job_type']}'")

    payload = json.loads(job["payload"]) if isinstance(job["payload"], str) else job["payload"]
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        result = await handler(payload)
        await execute(
            "UPDATE failed_jobs SET status = 'resolved', attempts = attempts + 1, last_attempt_at = ? WHERE id = ?",
            (now_iso, job_id)
        )
        logger.info(f"Failed job {job_id} ({job['job_type']}) successfully resolved on retry.")
        return {"status": "resolved", "job_id": job_id, "result": result}
    except Exception as e:
        await execute(
            "UPDATE failed_jobs SET status = 'failed', attempts = attempts + 1, error = ?, last_attempt_at = ? WHERE id = ?",
            (str(e), now_iso, job_id)
        )
        logger.error(f"Retry attempt for job {job_id} failed: {e}")
        raise e
