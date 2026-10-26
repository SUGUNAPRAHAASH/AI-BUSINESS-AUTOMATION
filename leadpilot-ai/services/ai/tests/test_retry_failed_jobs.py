import pytest
from app.jobs.retry import retry_with_backoff
from app.jobs.failed_jobs import register_job_handler, retry_failed_job_by_id
from app.db import execute, fetch_one, init_db


@pytest.mark.asyncio
async def test_retry_with_backoff_success():
    attempts = 0

    async def transient_work():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ConnectionError("Temporary network hiccup")
        return "SUCCESS"

    result = await retry_with_backoff(transient_work, max_attempts=3, initial_delay=0.01)
    assert result == "SUCCESS"
    assert attempts == 2


@pytest.mark.asyncio
async def test_retry_with_backoff_exhaustion():
    async def always_fails():
        raise TimeoutError("Endpoint unreachable")

    with pytest.raises(TimeoutError):
        await retry_with_backoff(always_fails, max_attempts=2, initial_delay=0.01)


@pytest.mark.asyncio
async def test_failed_job_registry_and_resolution():
    await init_db()
    # Insert simulated failed job
    job_id = "test_failed_job_01"
    await execute(
        "INSERT OR REPLACE INTO failed_jobs (id, job_type, payload, error, attempts, status, created_at) "
        "VALUES (?, 'crm_sync', '{\"email\": \"retry.test@example.com\"}', '500 Server Error', 1, 'failed', datetime('now'))",
        (job_id,)
    )

    result = await retry_failed_job_by_id(job_id)
    assert result["status"] == "resolved"

    updated = await fetch_one("SELECT status, attempts FROM failed_jobs WHERE id = ?", (job_id,))
    assert updated["status"] == "resolved"
    assert updated["attempts"] == 2
