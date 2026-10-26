# LeadPilot AI — Phase Execution & Build Log

**Session Date:** 2026-10-26 / 2026-10-27  
**Build Scope:** Complete autonomous end-to-end implementation of LeadPilot AI Hub.

---

## Phase 1: Foundations & Architecture
- **Activities:**
  - Scaffolding complete directory structure matching Section 4.
  - Authored `docker-compose.yml` and `docker-compose.prod.yml` coordinating 6 microservices: `postgres` (pgvector 16), `n8n`, `ai-service`, `mcp-server`, `web`, `mailpit`.
  - Authored PostgreSQL schema `001_extensions.sql`, `002_schema.sql`, and `seed.sql`.
  - Built async database layer in `db.py` with dual-engine support: PostgreSQL 16 pgvector in Docker + automatic SQLite fallback for zero-dependency native execution.
  - Implemented structured JSON logging (`logging.py`) and constant-time API key security with PII masking (`security.py`).
- **Tests & Verification:**
  - `GET /health` verified responding with health status, timestamp, and integration mode dictionary.

---

## Phase 2: LLM Layer & RAG Pipeline
- **Activities:**
  - Implemented provider-agnostic LLM interface in `app/llm/base.py` with circuit breaker and telemetry tracking.
  - Built `MockLLMClient` with deterministic intent detection, regex extraction, and normalized character n-gram hashing pseudo-embeddings.
  - Created `GeminiClient` supporting Google Gemini SDK with automatic mock fallback.
  - Authored 6 clinical documents in `knowledge_base/` for BrightSmile Dental (pricing, opening hours, FAQ, services, policies, aftercare).
  - Built heading-aware markdown chunker (`chunking.py`), batch embedder (`embedder.py`), and `HybridRetriever` combining cosine vector similarity + BM25 keyword matching via Reciprocal Rank Fusion (RRF, k=60).
- **Tests & Verification:**
  - Executed `services/ai/tests/eval_rag.py`: 18/20 hits (90.0% Recall@5) in offline mock mode. Saved report to `docs/RAG_EVAL.md`.

---

## Phase 3: Agent & Chat State Machine
- **Activities:**
  - Implemented LangGraph StateGraph state machine in `agent/graph.py` with 7 compiled nodes: `load_conversation`, `guardrails`, `route`, `retrieve`, `agent`, `tools`, `finalize`.
  - Created typed tools: `search_knowledge_base`, `capture_lead`, `check_availability`, `request_human_handoff`, `get_business_hours`.
  - Authored prompt instructions in `prompts.py` enforcing clinical non-diagnostic safety and citation requirements (`[Source: document.md]`).
- **Tests & Verification:**
  - Tested Scenario A (support chat + scope handoff on animal inquiry).
  - Tested Scenario B (Invisalign lead capture with score: 'hot').

---

## Phase 4: Integration Adapters & Reliability
- **Activities:**
  - Built 8 adapters (`slack`, `hubspot`, `gmail`, `sheets`, `airtable`, `telegram`, `shopify`, `vapi`) with `Real` and `Mock` implementations.
  - Built mock outbox table logging for visual dashboard auditing.
  - Built `retry_with_backoff` async helper with exponential backoff and jitter.
  - Built `failed_jobs` dead-letter queue with registry of retry handlers.
- **Tests & Verification:**
  - Verified retry exhaustion and recovery in `test_retry_failed_jobs.py`.
  - Verified Shopify HMAC verification and duplicate delivery rejection in `test_webhooks.py`.

---

## Phase 5: Email Triage & Document Extraction
- **Activities:**
  - Built `email_triage.py` classifying support, sales, appointment, billing, and spam, generating draft replies and evaluating `needs_human`.
  - Built `extraction.py` with mathematical verification of invoices (`sum(items) ≈ subtotal`, `subtotal + tax ≈ total`).
  - Generated sample PDF invoices via reportlab (`generate_sample_invoices.py`).
  - Built `call_summary.py` processing voice transcripts into appointment requests.
- **Tests & Verification:**
  - `test_email_triage.py` (10 test cases) passed.
  - `test_extraction.py` passed with mathematical validation check.

---

## Phase 6: n8n Workflows
- **Activities:**
  - Created 8 valid n8n workflow JSON specifications in `n8n/workflows/`:
    - `LP-W1-chat-gateway.json`
    - `LP-W2-lead-processing.json`
    - `LP-W3-email-intake-triage.json`
    - `LP-W4-document-extraction.json`
    - `LP-W5-voice-call-results.json`
    - `LP-W6-ecommerce-orders.json`
    - `LP-W7-scheduled-reports.json`
    - `LP-W8-error-handler-retries.json`
  - Created `n8n/import.sh` and documented import steps in `n8n/README.md`.

---

## Phase 7: Next.js Web Dashboard
- **Activities:**
  - Built Next.js App Router application with Tailwind CSS and dark glassmorphic styling.
  - Created 8 responsive pages:
    - `/` (Overview with KPI metric cards, weekly velocity chart, adapter status)
    - `/chat` (Live support chat with citation chips and handoff banners)
    - `/widget` (Embeddable iframe-ready widget)
    - `/leads` (CRM table with score filters and intelligence drawer)
    - `/emails` (Email triage inbox with AI draft approvals)
    - `/documents` (Invoice drag-and-drop extraction and math audit)
    - `/failed-jobs` (Reliability queue with live retry buttons)
    - `/outbox` (Simulated dispatch inspector)
    - `/kb` (Knowledge base chunk manager with live hybrid search tester)
  - Created `/api/proxy/[...path]` server-side API proxy ensuring `AI_SERVICE_API_KEY` is never exposed to browser clients.

---

## Phase 8: Model Context Protocol (MCP) Server
- **Activities:**
  - Implemented `services/mcp/server.py` supporting stdio and HTTP transports.
  - Registered 5 tools: `search_knowledge_base`, `list_recent_leads`, `lookup_lead`, `create_lead`, `get_dashboard_stats`.
  - Added resource schemas and `lead_followup_email` prompt.
  - Authored `services/mcp/README.md` with Claude Desktop config.
- **Tests & Verification:**
  - `services/mcp/test_mcp.py` verified tool registration.

---

## Phase 9: Automated Demo Verification & CI
- **Activities:**
  - Created `scripts/simulate_all.py` executing all 8 acceptance scenarios.
  - Result: 8/8 Scenarios PASSED.
  - Pytest suite: 48/48 Tests PASSED in 2.46 seconds.
