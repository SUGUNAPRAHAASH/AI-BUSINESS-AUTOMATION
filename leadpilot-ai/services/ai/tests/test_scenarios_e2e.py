import pytest
import json
import time
import random
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db import init_db, fetch_one, fetch_all, execute
from app.rag.ingest import ingest_knowledge_base_directory
from scripts.make_shopify_hmac import compute_shopify_hmac

API_KEY_HEADER = {"X-API-Key": "lp_secret_key_demo_2026"}


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    kb_dir = Path(__file__).resolve().parent.parent.parent.parent / "knowledge_base"
    if kb_dir.exists():
        await ingest_knowledge_base_directory(str(kb_dir))


@pytest.mark.asyncio
async def test_scenario_a_support_chat_rag():
    """Scenario A: Support chat with RAG fact retrieval and scope boundary handoff."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Whitening and weekend hours
        res1 = await client.post("/v1/chat", json={
            "message": "How much is teeth whitening and do you do weekend appointments?",
            "channel": "web"
        }, headers=API_KEY_HEADER)
        assert res1.status_code == 200
        data1 = res1.json()
        assert "$299" in data1["answer"]
        assert "Saturday" in data1["answer"] or "9:00 to 14:00" in data1["answer"]
        assert len(data1["citations"]) > 0
        assert any(
            any(name in c["source"].lower() for name in ["faq", "pricing", "opening_hours"])
            for c in data1["citations"]
        )

        # 2. Scope boundary ("Do you treat horses?")
        res2 = await client.post("/v1/chat", json={
            "message": "Do you treat horses?",
            "channel": "web"
        }, headers=API_KEY_HEADER)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["handoff"] is True
        assert "human" in data2["answer"].lower() or "not treat horses" in data2["answer"].lower()

        # Check outbox has handoff alert
        alert = await fetch_one("SELECT * FROM mock_outbox WHERE action = 'human_handoff_alert' ORDER BY created_at DESC LIMIT 1")
        assert alert is not None


@pytest.mark.asyncio
async def test_scenario_b_lead_capture():
    """Scenario B: Hot lead capture, scoring, CRM sync, and follow-up email dispatch."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        msg = "I'm interested in Invisalign, my name is Priya Nair, priya@example.com, I'd like to start next month, budget around 4000."
        res = await client.post("/v1/chat", json={
            "message": msg,
            "channel": "web"
        }, headers=API_KEY_HEADER)
        assert res.status_code == 200
        data = res.json()

        lead = data["lead_captured"]
        assert lead is not None
        assert lead["score"] == "hot"
        assert lead["email"] == "priya@example.com"
        assert "Invisalign" in lead["interest"]

        # Check database persistence
        db_lead = await fetch_one("SELECT * FROM leads WHERE lower(email) = 'priya@example.com'")
        assert db_lead is not None
        assert db_lead["score"] == "hot"

        # Check follow-up endpoint
        lead_id = db_lead["id"]
        res_followup = await client.post(f"/v1/leads/{lead_id}/followup", headers=API_KEY_HEADER)
        assert res_followup.status_code == 200
        assert "Invisalign" in res_followup.json()["subject"]


@pytest.mark.asyncio
async def test_scenario_c_email_triage():
    """Scenario C: Email classification, entity extraction, and approval routing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unique_id = f"e2e_msg_reschedule_{int(time.time() * 1000)}"
        res = await client.post("/v1/emails/triage", json={
            "message_id": unique_id,
            "from_addr": "patient@example.com",
            "subject": "Reschedule appointment on Friday",
            "body": "Hi, I need to reschedule my dental cleaning on Friday."
        }, headers=API_KEY_HEADER)
        assert res.status_code == 200
        data = res.json()
        assert data["category"] == "appointment"
        assert "Friday" in data["draft_reply"] or "reschedule" in data["draft_reply"].lower()

        # Approve reply
        email_id = data["id"]
        res_app = await client.post(f"/v1/emails/{email_id}/approve", headers=API_KEY_HEADER)
        assert res_app.status_code == 200
        assert res_app.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_scenario_d_document_extraction():
    """Scenario D: Invoice extraction, mathematical validation, and spreadsheet record."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        raw_text = (
            "Vendor: Dental Supplies Direct Inc.\n"
            "Invoice #: INV-2026-0891\n"
            "Invoice Date: 2026-10-15\n"
            "Item A | 2 | 45.00 | 90.00\n"
            "Item B | 4 | 35.00 | 140.00\n"
            "Item C | 2 | 110.00 | 220.00\n"
            "Subtotal: $450.00\n"
            "Tax: $36.00\n"
            "Total: $486.00\n"
        )
        files = {"file": ("sample_invoice.txt", raw_text.encode("utf-8"), "text/plain")}
        res = await client.post("/v1/documents/extract", files=files, headers=API_KEY_HEADER)
        assert res.status_code == 200
        data = res.json()
        assert data["vendor_name"] == "Dental Supplies Direct Inc."
        assert data["subtotal"] == 450.00
        assert data["tax"] == 36.00
        assert data["total"] == 486.00
        assert data["confidence"] >= 0.90


@pytest.mark.asyncio
async def test_scenario_e_voice_call_result():
    """Scenario E: Voice call transcript processing, lead generation, and callback requirement."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        transcript = (
            "Caller: Hi, my name is Marcus Vance. I want to book a dental implant consultation next Tuesday morning. "
            "My phone is 555-349-8812."
        )
        unique_call_id = f"vapi_call_e2e_{int(time.time() * 1000)}"
        res = await client.post("/v1/calls/summarize", json={
            "external_call_id": unique_call_id,
            "transcript": transcript
        }, headers=API_KEY_HEADER)
        assert res.status_code == 200
        data = res.json()
        assert "Marcus Vance" in data["caller_name"]
        assert data["phone"] == "555-349-8812"
        assert data["follow_up_needed"] is True


@pytest.mark.asyncio
async def test_scenario_f_ecommerce_order_and_idempotency():
    """Scenario F: Shopify webhook verification, inventory update, low stock alert, and duplicate rejection."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unique_order_id = int(time.time() * 1000) % 100000000
        payload = {
            "id": unique_order_id,
            "email": "ecommerce.buyer@example.com",
            "total_price": "99.00",
            "line_items": [
                {"sku": "SKU-FLOSS-04", "quantity": 1, "price": "99.00"}
            ]
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        secret = "shopify_test_secret_key_12345"
        sig = compute_shopify_hmac(secret, body_bytes)

        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Hmac-Sha256": sig
        }

        # First delivery: success
        res1 = await client.post("/webhooks/shopify", content=body_bytes, headers=headers)
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["status"] == "processed"
        assert len(data1["low_stock_alerts"]) > 0

        # Second delivery: duplicate ignored
        res2 = await client.post("/webhooks/shopify", content=body_bytes, headers=headers)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["status"] == "duplicate"


@pytest.mark.asyncio
async def test_scenario_g_failure_handling_and_retry():
    """Scenario G: Failed job registration, status display, and successful retry."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        job_id = f"job_failed_crm_e2e_{int(time.time() * 1000)}"
        await execute(
            "INSERT OR REPLACE INTO failed_jobs (id, job_type, payload, error, attempts, status, created_at) "
            "VALUES (?, 'crm_sync', '{\"email\": \"retry_patient@example.com\", \"name\": \"Alex Mercer\"}', 'HTTP 500 Internal Error', 1, 'failed', datetime('now'))",
            (job_id,)
        )

        # Retry job via admin endpoint
        res = await client.post(f"/v1/admin/failed-jobs/{job_id}/retry", headers=API_KEY_HEADER)
        assert res.status_code == 200
        assert res.json()["status"] == "resolved"


@pytest.mark.asyncio
async def test_scenario_h_mcp_integration():
    """Scenario H: FastMCP tools query knowledge base and manage leads."""
    from services.mcp.server import mcp
    tools = mcp.list_tools() if hasattr(mcp, "list_tools") else mcp._tool_manager.list_tools()
    assert len(tools) >= 5

    # Test knowledge base tool search logic
    from app.rag.retriever import HybridRetriever
    r = HybridRetriever()
    results = await r.search("teeth whitening price")
    assert len(results) > 0
    assert any("$299" in c["content"] for c in results)
