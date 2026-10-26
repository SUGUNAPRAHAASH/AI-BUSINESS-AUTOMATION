# LeadPilot AI — REST API Reference Specification

All endpoints (except `/health` and signature-verified webhooks) require the authentication header:
```http
X-API-Key: lp_secret_key_demo_2026
```

All error responses strictly adhere to the following JSON format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of error.",
    "request_id": "uuid-v4"
  }
}
```

---

## 1. System & Health

### `GET /health`
Liveness probe, database connection status, and active mode for each third-party integration adapter.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-10-27T00:15:00Z",
  "database": "connected",
  "embedding_dim": 768,
  "modes": {
    "gemini": "mock",
    "hubspot": "mock",
    "slack": "mock",
    "gmail": "mock",
    "sheets": "mock",
    "airtable": "mock",
    "telegram": "mock",
    "shopify": "mock",
    "vapi": "mock"
  },
  "last_llm_call": "active"
}
```

---

## 2. Clinical Chat & Knowledge Base

### `POST /v1/chat`
Autonomous LangGraph agent support chat and lead qualification endpoint.

**Request Body:**
```json
{
  "tenant": "brightsmile",
  "channel": "web",
  "external_id": "session_user_001",
  "message": "How much is teeth whitening and do you do weekend appointments?"
}
```

**Response (200 OK):**
```json
{
  "answer": "Professional in-office teeth whitening at BrightSmile Dental is $299 for a 1-hour laser whitening treatment. We are open for weekend appointments on Saturdays from 9:00 to 14:00 [Source: pricing.md] [Source: opening_hours.md].",
  "citations": [
    {
      "title": "Pricing & Fee Guide",
      "source": "pricing.md",
      "score": 0.0328
    },
    {
      "title": "Operating Hours",
      "source": "opening_hours.md",
      "score": 0.0312
    }
  ],
  "lead_captured": null,
  "handoff": false,
  "conversation_id": "f1821830-662e-4b94-a479-578f1242d22b"
}
```

---

### `GET /v1/kb/search?q={query}`
Interactive hybrid search testing endpoint (Vector Cosine + Lexical BM25 RRF).

---

## 3. Lead Qualification & CRM

### `POST /v1/leads/qualify`
Evaluates natural language conversation turn or text snippet against the lead scoring rubric.

**Request Body:**
```json
{
  "text": "I'm interested in Invisalign, my name is Priya Nair, priya@example.com, start next month, budget 4000."
}
```

**Response (200 OK):**
```json
{
  "name": "Priya Nair",
  "email": "priya@example.com",
  "phone": null,
  "interest": "Invisalign",
  "budget_text": "4000",
  "timeline_text": "Within 30-60 days",
  "score": "hot",
  "score_reason": "Verified contact info (priya@example.com) with immediate booking intent or high-value interest (Invisalign).",
  "summary": "Inquiry regarding Invisalign from Priya Nair.",
  "next_best_action": "Initiate immediate phone/email follow-up and offer direct booking link."
}
```

---

### `POST /v1/leads/{id}/followup`
Generates a context-aware follow-up email for a qualified hot lead and dispatches via SMTP or Mock Outbox.

---

## 4. Email Triage & Approvals

### `POST /v1/emails/triage`
Categorizes incoming email, extracts entities, and drafts an empathetic reply.

**Request Body:**
```json
{
  "message_id": "msg_001",
  "from_addr": "patient@example.com",
  "subject": "Need to reschedule my Friday dental cleaning",
  "body": "Hi, I need to reschedule my Friday cleaning to next Tuesday."
}
```

---

### `POST /v1/emails/{id}/approve`
Human approval action: dispatches the AI-generated draft reply to the patient.

---

## 5. Document Extraction

### `POST /v1/documents/extract`
Accepts `multipart/form-data` file upload (PDF or image). Returns validated JSON and flags mathematical mismatches.

---

## 6. Webhooks

### `POST /webhooks/shopify`
Requires `X-Shopify-Hmac-Sha256` signature header. Verifies HMAC, decrements inventory, flags low-stock items, and rejects duplicates idempotently.

---

### `POST /webhooks/vapi`
Requires `x-vapi-secret` header. Summarizes call transcripts, extracts appointment requests, and triggers callback alerts.

---

## 7. Admin & Observability

### `GET /v1/admin/stats`
Aggregated operational metrics for dashboard overview.

### `GET /v1/admin/failed-jobs`
Retrieves dead-letter queue records.

### `POST /v1/admin/failed-jobs/{id}/retry`
Triggers immediate re-execution of a failed job.

### `GET /v1/admin/mock-outbox`
Returns visual audit log of all simulated external messages.
