import asyncio
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add services/ai to sys.path
ai_path = Path(__file__).resolve().parent.parent / "services" / "ai"
sys.path.insert(0, str(ai_path))
repo_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_path))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db import init_db
from app.rag.ingest import ingest_knowledge_base_directory
from scripts.make_shopify_hmac import compute_shopify_hmac

API_KEY_HEADER = {"X-API-Key": "lp_secret_key_demo_2026"}


async def run_all_scenarios():
    print("================================================================================")
    print("            LEADPILOT AI — AUTONOMOUS DEMO SCENARIOS VERIFICATION              ")
    print("================================================================================")
    print("Tenant: BrightSmile Dental | Mode: Mock-First / Local Offline Verification\n")

    await init_db()
    kb_dir = repo_path / "knowledge_base"
    await ingest_knowledge_base_directory(str(kb_dir))

    transport = ASGITransport(app=app)
    results = []

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Scenario A: Support chat with RAG
        t0 = time.time()
        try:
            r1 = await client.post("/v1/chat", json={
                "message": "How much is teeth whitening and do you do weekend appointments?",
                "channel": "web"
            }, headers=API_KEY_HEADER)
            d1 = r1.json()
            r2 = await client.post("/v1/chat", json={
                "message": "Do you treat horses?",
                "channel": "web"
            }, headers=API_KEY_HEADER)
            d2 = r2.json()
            ok = ("$299" in d1["answer"]) and (d2["handoff"] is True)
            results.append(("Scenario A: Support Chat with RAG", ok, f"Answer: {d1['answer'][:65]}...", int((time.time() - t0)*1000)))
        except Exception as e:
            results.append(("Scenario A: Support Chat with RAG", False, str(e), int((time.time() - t0)*1000)))

        # Scenario B: Lead Capture
        t0 = time.time()
        try:
            r = await client.post("/v1/chat", json={
                "message": "I'm interested in Invisalign, my name is Priya Nair, priya@example.com, I'd like to start next month, budget around 4000.",
                "channel": "web"
            }, headers=API_KEY_HEADER)
            d = r.json()
            lead = d.get("lead_captured", {})
            ok = (lead.get("score") == "hot") and (lead.get("email") == "priya@example.com")
            results.append(("Scenario B: Lead Capture & Scoring", ok, f"Lead: {lead.get('name')} | Score: {lead.get('score').upper()}", int((time.time() - t0)*1000)))
        except Exception as e:
            results.append(("Scenario B: Lead Capture & Scoring", False, str(e), int((time.time() - t0)*1000)))

        # Scenario C: Email Triage
        t0 = time.time()
        try:
            r = await client.post("/v1/emails/triage", json={
                "message_id": f"sim_email_{int(time.time()*1000)}",
                "from_addr": "clara.oswald@example.com",
                "subject": "Need to reschedule my Friday appointment",
                "body": "Hi, I need to reschedule my Friday cleaning."
            }, headers=API_KEY_HEADER)
            d = r.json()
            ok = (d.get("category") == "appointment") and (d.get("action") == "needs_approval")
            results.append(("Scenario C: Email Triage & Draft", ok, f"Category: {d.get('category')} | Needs Approval: True", int((time.time() - t0)*1000)))
        except Exception as e:
            results.append(("Scenario C: Email Triage & Draft", False, str(e), int((time.time() - t0)*1000)))

        # Scenario D: Document Extraction
        t0 = time.time()
        try:
            raw_invoice = "Vendor: Dental Supplies Direct Inc.\nInvoice #: INV-2026-0891\nInvoice Date: 2026-10-15\nItem A | 2 | 45.00 | 90.00\nSubtotal: $450.00\nTax: $36.00\nTotal: $486.00"
            files = {"file": ("invoice.txt", raw_invoice.encode("utf-8"), "text/plain")}
            r = await client.post("/v1/documents/extract", files=files, headers=API_KEY_HEADER)
            d = r.json()
            ok = (d.get("vendor_name") == "Dental Supplies Direct Inc.") and (d.get("total") == 486.00)
            results.append(("Scenario D: Document Extraction", ok, f"Vendor: {d.get('vendor_name')} | Total: ${d.get('total')}", int((time.time() - t0)*1000)))
        except Exception as e:
            results.append(("Scenario D: Document Extraction", False, str(e), int((time.time() - t0)*1000)))

        # Scenario E: Voice Call Results
        t0 = time.time()
        try:
            r = await client.post("/v1/calls/summarize", json={
                "external_call_id": f"vapi_sim_{int(time.time()*1000)}",
                "transcript": "Caller: Hi, my name is Marcus Vance. I need dental implants next Tuesday. Call me back at 555-349-8812."
            }, headers=API_KEY_HEADER)
            d = r.json()
            ok = ("Marcus Vance" in d.get("caller_name", "")) and (d.get("follow_up_needed") is True)
            results.append(("Scenario E: Voice Call Summary", ok, f"Caller: {d.get('caller_name')} | Intent: {d.get('intent')}", int((time.time() - t0)*1000)))
        except Exception as e:
            results.append(("Scenario E: Voice Call Summary", False, str(e), int((time.time() - t0)*1000)))

        # Scenario F: E-commerce Order
        t0 = time.time()
        try:
            order_id = int(time.time() * 1000) % 100000000
            payload = {"id": order_id, "email": "buyer@test.com", "total_price": "99.00", "line_items": [{"sku": "SKU-FLOSS-04", "quantity": 1}]}
            body = sys.modules["json"].dumps(payload).encode("utf-8")
            sig = compute_shopify_hmac("shopify_test_secret_key_12345", body)
            r1 = await client.post("/webhooks/shopify", content=body, headers={"X-Shopify-Hmac-Sha256": sig, "Content-Type": "application/json"})
            r2 = await client.post("/webhooks/shopify", content=body, headers={"X-Shopify-Hmac-Sha256": sig, "Content-Type": "application/json"})
            ok = (r1.json().get("status") == "processed") and (r2.json().get("status") == "duplicate")
            results.append(("Scenario F: Shopify Orders & Dedupe", ok, "Processed & Duplicate Rejected", int((time.time() - t0)*1000)))
        except Exception as e:
            results.append(("Scenario F: Shopify Orders & Dedupe", False, str(e), int((time.time() - t0)*1000)))

        # Scenario G: Failure Handling & Retry
        t0 = time.time()
        try:
            from app.db import execute
            job_id = f"job_fail_{int(time.time()*1000)}"
            await execute(
                "INSERT OR REPLACE INTO failed_jobs (id, job_type, payload, error, attempts, status, created_at) "
                "VALUES (?, 'crm_sync', '{\"email\": \"retry@patient.com\"}', '500 Timeout', 1, 'failed', datetime('now'))",
                (job_id,)
            )
            r = await client.post(f"/v1/admin/failed-jobs/{job_id}/retry", headers=API_KEY_HEADER)
            ok = (r.json().get("status") == "resolved")
            results.append(("Scenario G: Failure & Retry Queue", ok, f"Job {job_id} resolved on retry", int((time.time() - t0)*1000)))
        except Exception as e:
            results.append(("Scenario G: Failure & Retry Queue", False, str(e), int((time.time() - t0)*1000)))

        # Scenario H: MCP Integration
        t0 = time.time()
        try:
            from services.mcp.server import mcp
            tools = mcp.list_tools() if hasattr(mcp, "list_tools") else mcp._tool_manager.list_tools()
            ok = len(tools) >= 5
            results.append(("Scenario H: MCP Server & Tool Calling", ok, f"{len(tools)} tools registered in FastMCP", int((time.time() - t0)*1000)))
        except Exception as e:
            results.append(("Scenario H: MCP Server & Tool Calling", False, str(e), int((time.time() - t0)*1000)))

    # Print summary table
    print(f"{'#':<3} | {'Scenario Name':<38} | {'Status':<10} | {'Latency':<8} | {'Summary Output'}")
    print("-" * 105)
    all_passed = True
    for idx, (name, passed, detail, lat) in enumerate(results, 1):
        status_str = "PASS [OK]" if passed else "FAIL [X]"
        if not passed:
            all_passed = False
        print(f"{idx:<3} | {name:<38} | {status_str:<10} | {lat}ms{'':<4} | {detail}")
    print("-" * 105)
    print(f"\nFinal Result: {'ALL 8 SCENARIOS PASSED' if all_passed else 'SOME SCENARIOS FAILED'}\n")
    return all_passed


if __name__ == "__main__":
    passed = asyncio.run(run_all_scenarios())
    sys.exit(0 if passed else 1)
