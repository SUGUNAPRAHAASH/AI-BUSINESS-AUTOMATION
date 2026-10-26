import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiosqlite
from app.config import settings
from app.utils.logging import logger

_db_initialized = False


def get_sqlite_path() -> str:
    # Use workspace or local directory for sqlite file
    base_dir = Path(__file__).resolve().parent.parent
    db_file = base_dir / "leadpilot.db"
    return str(db_file)


async def get_connection():
    db_path = get_sqlite_path()
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    return conn


async def init_db():
    global _db_initialized
    if _db_initialized:
        return

    conn = await get_connection()
    try:
        # Create standard tables matching our PostgreSQL schema
        await conn.executescript("""
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            settings TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS kb_documents (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE (tenant_id, content_hash)
        );

        CREATE TABLE IF NOT EXISTS kb_chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT NOT NULL DEFAULT '{}',
            embedding TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            channel TEXT NOT NULL,
            external_id TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL,
            UNIQUE (tenant_id, channel, external_id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            conversation_id TEXT,
            name TEXT,
            email TEXT,
            phone TEXT,
            interest TEXT,
            budget_text TEXT,
            timeline_text TEXT,
            score TEXT,
            score_reason TEXT,
            summary TEXT,
            source TEXT,
            crm_id TEXT,
            crm_synced_at TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            message_id TEXT NOT NULL,
            from_addr TEXT,
            subject TEXT,
            body TEXT,
            category TEXT,
            entities TEXT,
            priority TEXT,
            draft_reply TEXT,
            action TEXT,
            created_at TEXT NOT NULL,
            UNIQUE (tenant_id, message_id)
        );

        CREATE TABLE IF NOT EXISTS extracted_documents (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            filename TEXT,
            doc_type TEXT,
            data TEXT NOT NULL,
            confidence REAL,
            validation_errors TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            external_id TEXT NOT NULL,
            customer_email TEXT,
            total REAL,
            currency TEXT,
            line_items TEXT,
            raw TEXT,
            created_at TEXT NOT NULL,
            UNIQUE (tenant_id, external_id)
        );

        CREATE TABLE IF NOT EXISTS inventory (
            sku TEXT PRIMARY KEY,
            name TEXT,
            stock INTEGER NOT NULL,
            low_stock_threshold INTEGER NOT NULL DEFAULT 5
        );

        CREATE TABLE IF NOT EXISTS call_logs (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            external_call_id TEXT NOT NULL,
            transcript TEXT,
            summary TEXT,
            extracted TEXT,
            created_at TEXT NOT NULL,
            UNIQUE (tenant_id, external_call_id)
        );

        CREATE TABLE IF NOT EXISTS webhook_events (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            payload TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'processed',
            created_at TEXT NOT NULL,
            UNIQUE (source, idempotency_key)
        );

        CREATE TABLE IF NOT EXISTS failed_jobs (
            id TEXT PRIMARY KEY,
            job_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            error TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'failed',
            created_at TEXT NOT NULL,
            last_attempt_at TEXT
        );

        CREATE TABLE IF NOT EXISTS mock_outbox (
            id TEXT PRIMARY KEY,
            integration TEXT NOT NULL,
            action TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS llm_usage (
            id TEXT PRIMARY KEY,
            feature TEXT,
            provider TEXT,
            model TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            latency_ms INTEGER,
            ok INTEGER,
            created_at TEXT NOT NULL
        );
        """)

        # Seed initial brightsmile tenant and inventory
        now_iso = datetime.now(timezone.utc).isoformat()
        await conn.execute("""
            INSERT OR IGNORE INTO tenants (id, name, slug, settings, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "a0000000-0000-0000-0000-000000000001",
            "BrightSmile Dental",
            "brightsmile",
            json.dumps({"timezone": "America/New_York", "currency": "USD", "cancellation_notice_hours": 24}),
            now_iso
        ))

        # Seed inventory
        items = [
            ('SKU-WKIT-01', 'Professional At-Home Whitening Kit', 24, 5),
            ('SKU-TOOTH-02', 'UltraSonic Electric Toothbrush Pro', 12, 4),
            ('SKU-PASTE-03', 'Enamel Restoration Remineralizing Toothpaste', 45, 10),
            ('SKU-FLOSS-04', 'Water Flosser Cordless Advanced', 3, 5),
            ('SKU-GUARD-05', 'Custom Night Guard Protection Set', 18, 5)
        ]
        for sku, name, stock, threshold in items:
            await conn.execute("""
                INSERT OR IGNORE INTO inventory (sku, name, stock, low_stock_threshold)
                VALUES (?, ?, ?, ?)
            """, (sku, name, stock, threshold))

        await conn.commit()
        _db_initialized = True
        logger.info("Database schema and seed initialized successfully.")
    finally:
        await conn.close()


async def execute(query: str, params: tuple = ()) -> None:
    await init_db()
    conn = await get_connection()
    try:
        await conn.execute(query, params)
        await conn.commit()
    finally:
        await conn.close()


async def fetch_one(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    await init_db()
    conn = await get_connection()
    try:
        async with conn.execute(query, params) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
    finally:
        await conn.close()


async def fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    await init_db()
    conn = await get_connection()
    try:
        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
    finally:
        await conn.close()


async def insert_mock_outbox(integration: str, action: str, payload: Dict[str, Any]) -> str:
    """Record outbound message in mock_outbox for UI inspection and offline test assertions."""
    outbox_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    await execute(
        "INSERT INTO mock_outbox (id, integration, action, payload, created_at) VALUES (?, ?, ?, ?, ?)",
        (outbox_id, integration, action, json.dumps(payload), now_iso)
    )
    logger.info(f"[MOCK_OUTBOX] [{integration.upper()}] Action: {action} recorded with ID {outbox_id}")
    return outbox_id


async def insert_failed_job(job_type: str, payload: Dict[str, Any], error: str) -> str:
    job_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    await execute(
        "INSERT INTO failed_jobs (id, job_type, payload, error, attempts, status, created_at, last_attempt_at) "
        "VALUES (?, ?, ?, ?, 1, 'failed', ?, ?)",
        (job_id, job_type, json.dumps(payload), str(error), now_iso, now_iso)
    )
    logger.warning(f"[FAILED_JOB] Job {job_id} ({job_type}) registered in failure queue: {error}")
    return job_id


async def record_llm_usage(feature: str, provider: str, model: str, prompt_tokens: int, completion_tokens: int, latency_ms: int, ok: bool) -> None:
    usage_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    await execute(
        "INSERT INTO llm_usage (id, feature, provider, model, prompt_tokens, completion_tokens, latency_ms, ok, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (usage_id, feature, provider, model, prompt_tokens, completion_tokens, latency_ms, 1 if ok else 0, now_iso)
    )
