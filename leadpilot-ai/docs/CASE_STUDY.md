# LeadPilot AI — Case Study: Autonomous Business Automation

## Executive Summary
Small medical and professional service practices spend 15 to 25 hours per week on repetitive front-desk administration: quoting treatment fees, qualifying patient inquiries across channels, retyping invoice line items, and manually dispatching appointment follow-ups.

**LeadPilot AI** was engineered as an autonomous operations hub that functions as a 24/7 virtual operations team. Built for a high-end demo clinic (**BrightSmile Dental**), the system answers patient inquiries with grounded RAG fact verification, scores leads into a CRM, triages incoming emails with draft generation, audits invoice mathematics, processes voice call summaries, and exposes its tool registry via the Model Context Protocol (MCP).

---

## 1. The Challenge
1. **Hallucination Risk in Medical/Fee Grounding:** General LLMs frequently invent clinical fees, conflicting weekend hours, or inappropriate medical advice.
2. **Third-Party API Vulnerabilities & Rate Limits:** Fragile automation workflows often collapse during third-party API downtime (e.g. HubSpot 500s or Shopify webhook retries).
3. **Fragmented Tooling:** Disconnected Zapier or Make zaps create data silos where chat leads, email requests, and voice call transcripts fail to sync to the core CRM.

---

## 2. The Solution & Architecture
We designed a hybrid architecture pairing a high-performance **Python FastAPI** AI service with a self-hosted **n8n** visual orchestrator, backed by **PostgreSQL 16 + pgvector** and a **Next.js** operational dashboard:

- **Grounded Knowledge Retrieval:** Document chunking splits files by markdown headings (#, ##, ###) with 100-character overlap. Inquiries are resolved via **Reciprocal Rank Fusion (RRF, k=60)** combining dense vector cosine similarity with lexical BM25 matching.
- **Autonomous Agent State Machine:** Built using LangGraph with 7 compiled stages (`load_conversation`, `guardrails`, `route`, `retrieve`, `agent`, `tools`, `finalize`) enforcing clinical scope boundaries and PII masking.
- **Mock-First Decoupled Adapters:** Every integration (Slack, HubSpot, Gmail, Sheets, Telegram, Shopify, Vapi) sits behind dual Real/Mock interfaces, guaranteeing 100% offline testability.
- **Dead-Letter Failure Recovery:** Exponential backoff with jitter and a dedicated `failed_jobs` queue enable operators to re-dispatch failed tasks with a single click.

---

## 3. Measured Results & Verification

| Metric / Benchmark | Measured Outcome |
|---|---|
| **RAG Retrieval Recall@5** | **90.0%** (18/20 ground-truth clinical fact pairs retrieved in top 5 chunks) |
| **Automated Test Suite** | **48 / 48 Tests Passed** (Executed in 2.46s across unit & E2E scenarios) |
| **Demo Scenarios (A to H)** | **100% Pass Rate** (Chat, Lead Capture, Email Triage, Invoice Audit, Voice, Shopify HMAC, Retries, FastMCP) |
| **API Response Latency** | Under **45ms** median response time in mock-first operational mode |
| **Build Integrity** | Standalone production bundle compiled cleanly across all 12 Next.js App Router routes |

---

## 4. Key Challenges & How They Were Resolved
- *Challenge: Substring Collision in Invoice Regex:* The total price regex pattern initially matched `Subtotal: $450.00` because `Total` was a substring.  
  *Resolution:* Applied strict regex word boundaries (`\bTotal[:\s]*` vs `\bSubtotal[:\s]*`), restoring 100% mathematical precision across multi-item invoices.
- *Challenge: Decoupled Multi-Platform Testing:* Ensuring external dependencies (Claude Desktop, n8n, HubSpot) can be tested deterministically in local environments.  
  *Resolution:* Implemented a mock outbox audit table (`mock_outbox`) and FastMCP compatibility layer that verifies tool registration and call execution offline.

---

## 5. Future Roadmap
1. **Fine-Tuned Small Language Models:** Deploying local quantized models (e.g., Llama 3.2 3B or Gemma 2) for zero-latency edge inference inside private medical LANs.
2. **Direct Telephony Audio Streaming:** Integrating Twilio or LiveKit WebRTC media streams directly into FastAPI for bidirectional sub-second voice synthesis.
3. **Multi-Tenant SSO & RBAC:** Role-based access control supporting enterprise dental franchises with hundreds of clinic branches.
