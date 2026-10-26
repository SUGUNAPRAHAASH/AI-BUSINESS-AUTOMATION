# LeadPilot AI — System Architecture & Design Specification

## 1. System Overview

**LeadPilot AI** is an enterprise-grade virtual operations hub designed for local businesses (demonstrated for **BrightSmile Dental**). It functions as an autonomous front-desk, marketing, and operational team by unifying real-time chat, lead qualification, email triage, optical document audit, voice AI, and multi-channel workflows.

```mermaid
graph TD
    User["👤 Patients & Customers"] -->|Chat / Web / Voice| Web["🖥️ Next.js Web Dashboard & Widget"]
    User -->|Voice Calls| Vapi["🎙️ Vapi Voice AI Agent"]
    User -->|Orders| Shopify["🛍️ Shopify Store"]
    User -->|Inquiries| Gmail["📧 Gmail / Inbound Email"]

    Web -->|Internal Proxy| AIService["⚡ Python FastAPI AI Service"]
    Vapi -->|Webhook| AIService
    Shopify -->|HMAC Webhook| AIService
    n8n["🔄 n8n Orchestrator (LP-W1 to LP-W8)"] <-->|REST API + X-API-Key| AIService

    AIService -->|LangGraph State Machine| Agent["🤖 Autonomous Agent & Tools"]
    Agent -->|Hybrid RRF Search| PG[("🐘 PostgreSQL 16 + pgvector")]
    Agent -->|Deterministic / Gemini| LLM["🧠 LLM Layer (Gemini / Claude / Mock)"]

    AIService -->|Mock / Real Adapters| Integrations["🔌 Integration Hub"]
    Integrations --> HubSpot["CRM (HubSpot)"]
    Integrations --> Slack["Alerts (Slack Block Kit)"]
    Integrations --> Telegram["Bot (Telegram)"]
    Integrations --> Sheets["Spreadsheets (Google Sheets)"]
    Integrations --> Outbox[("📦 Mock Outbox Table")]
```

---

## 2. Sequence Diagrams for Core Scenarios

### Scenario A: Grounded Support Chat with RAG & Scope Handoff

```mermaid
sequenceDiagram
    autonumber
    actor Patient
    participant Web as Next.js Dashboard / Widget
    participant Fast as FastAPI (/v1/chat)
    participant Agent as LangGraph Agent
    participant DB as pgvector & Full-Text Search
    participant Slack as Front-Desk Slack Channel

    Patient->>Web: "How much is teeth whitening and do you do weekend appointments?"
    Web->>Fast: POST /v1/chat (X-API-Key)
    Fast->>Agent: StateGraph.run()
    Agent->>Agent: Node 2: Guardrails & PII Masking
    Agent->>Agent: Node 3: Intent Classification (faq)
    Agent->>DB: Node 4: Hybrid Search (Vector + BM25 RRF)
    DB-->>Agent: Returns top chunks (pricing.md: $299, opening_hours.md: Sat 9-14)
    Agent->>Agent: Node 5: Generate Answer citing [Source: pricing.md]
    Agent->>DB: Node 7: Persist conversation turn
    Fast-->>Web: ChatResponse (answer, citations, handoff=false)
    Web-->>Patient: Displays answer with interactive source chips

    opt Scope Boundary Query ("Do you treat horses?")
        Patient->>Web: "Do you treat horses?"
        Web->>Fast: POST /v1/chat
        Fast->>Agent: StateGraph.run()
        Agent->>Agent: Scope Check detects veterinary query
        Agent->>Slack: Trigger Human Handoff Alert (#front-desk-alerts)
        Fast-->>Web: ChatResponse (decline politely, handoff=true)
    end
```

### Scenario B: Lead Qualification, Scoring, and CRM Sync

```mermaid
sequenceDiagram
    autonumber
    actor Visitor
    participant Agent as LangGraph Agent
    participant Hub as HubSpot CRM Adapter
    participant Slack as Sales Slack Channel
    participant Outbox as Mock Outbox Table

    Visitor->>Agent: "I'm interested in Invisalign, my name is Priya Nair, priya@example.com, start next month, budget 4000."
    Agent->>Agent: capture_lead tool call
    Agent->>Agent: Rubric: Contact + Specific Interest + Near Timeline (30d) -> HOT
    Agent->>Hub: Upsert Contact (email, name, score: 'hot', interest: 'Invisalign')
    alt Real Mode
        Hub->>HubSpot API: POST /crm/v3/objects/contacts
    else Mock Mode
        Hub->>Outbox: Record simulated contact payload
    end
    Agent->>Slack: Post Hot Lead Alert to #sales-leads
    Agent->>Outbox: Record personalized follow-up email draft
    Agent-->>Visitor: "Thank you Priya! I've recorded your interest in Invisalign..."
```

### Scenario G: Workflow Failure Handling & Automatic Retries

```mermaid
sequenceDiagram
    autonumber
    participant App as AI Service / n8n Workflow
    participant Queue as failed_jobs Queue
    participant Slack as Ops Alert Channel
    participant Admin as Admin Dashboard (/v1/admin/failed-jobs)

    App->>App: External CRM call times out (500 Server Error)
    App->>App: retry_with_backoff (Attempts 1, 2, 3 exhausted)
    App->>Queue: INSERT INTO failed_jobs (job_type='crm_sync', payload, error)
    App->>Slack: Post Failure Notification with Retry URL
    Admin->>Queue: GET /v1/admin/failed-jobs (Status: 'failed')
    Admin->>App: Operator clicks "Retry Job" (POST /v1/admin/failed-jobs/{id}/retry)
    App->>App: Re-executes registered handler (handle_crm_sync_retry)
    App->>Queue: UPDATE failed_jobs SET status='resolved', attempts=attempts+1
    App-->>Admin: Returns { status: "resolved" }
```

---

## 3. Data Model

```mermaid
erDiagram
    TENANTS ||--o{ KB_DOCUMENTS : owns
    TENANTS ||--o{ CONVERSATIONS : participates
    TENANTS ||--o{ LEADS : captures
    TENANTS ||--o{ EMAILS : triages
    TENANTS ||--o{ EXTRACTED_DOCUMENTS : audits
    TENANTS ||--o{ ORDERS : records
    TENANTS ||--o{ CALL_LOGS : logs

    KB_DOCUMENTS ||--|{ KB_CHUNKS : splits_into
    CONVERSATIONS ||--|{ MESSAGES : contains
    LEADS }o--|| CONVERSATIONS : references

    TENANTS {
        uuid id PK
        string name
        string slug
        jsonb settings
    }
    KB_CHUNKS {
        uuid id PK
        uuid document_id FK
        text content
        vector embedding
        tsvector tsv
        jsonb metadata
    }
    LEADS {
        uuid id PK
        uuid tenant_id FK
        string name
        string email
        string phone
        string interest
        string score
        string score_reason
        string crm_id
    }
    EMAILS {
        uuid id PK
        string message_id
        string category
        string priority
        text draft_reply
        string action
    }
    FAILED_JOBS {
        uuid id PK
        string job_type
        jsonb payload
        text error
        int attempts
        string status
    }
```

---

## 4. Design Decisions & Trade-Offs

| Decision | Rationale | Alternatives Considered |
|---|---|---|
| **n8n + Python Hybrid** | Python excels at mathematical validation, vector search, and agent state machines. n8n provides visual orchestration, cron schedules, and webhooks that business clients can understand. | Pure Python (lacks visual UI) or pure n8n (weak native vector and agent control). |
| **pgvector + SQLite Fallback** | PostgreSQL 16 + pgvector is standard for Supabase and production cloud. The dual SQLite/Postgres async driver allows developers to test zero-dependency offline without Docker running. | Chroma / Pinecone (requires cloud network or heavy binaries). |
| **Mock-First Architecture** | Every external integration has an active toggle (`REAL` vs `MOCK`). This prevents tests from ever breaking due to missing third-party API keys or rate limits. | Stubs in unit tests only (leaves end-to-end stack untested). |
| **Reciprocal Rank Fusion (RRF)** | Fusing vector cosine similarity with lexical BM25 matching overcomes vector blindspots on specific numeric pricing ($299) and exact terms. | Dense vector search alone (prone to hallucinating exact pricing). |

---

## 5. Security & Threat Mitigation

| Threat | Risk Level | Mitigation in LeadPilot AI |
|---|:---:|---|
| **Prompt Injection** | High | User content placed in clear data blocks; system prompt enforces strict clinical scope; guardrails block injection phrases. |
| **Webhook Spoofing** | High | Shopify HMAC-SHA256 signature checked using constant-time comparison (`secrets.compare_digest`); Vapi secret header verified. |
| **PII & Card Leakage** | High | Pre-storage regex scrubbing masks credit cards (13-19 digits) and SSNs before messages are saved to database. |
| **Tenant Data Leakage** | High | All queries strictly filter by `tenant_id` at the database index layer. |
| **Secret Exposure** | High | API keys restricted to backend proxy; Next.js server proxy forwards requests; `.env` is git-ignored. |
