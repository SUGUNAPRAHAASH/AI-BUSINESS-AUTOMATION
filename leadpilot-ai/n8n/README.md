# LeadPilot AI — n8n Orchestration Layer

LeadPilot AI leverages self-hosted **n8n** as its visual workflow orchestrator, bridging triggers, branching, notifications, retries, and human-in-the-loop approvals with the core Python FastAPI AI service.

## Workflows Catalog

| Workflow ID | Name | Trigger | Actions |
|---|---|---|---|
| **LP-W1** | `LP-W1-chat-gateway` | Webhook / Telegram | Normalizes payload, calls `/v1/chat`, verifies human handoff, and dispatches responses. |
| **LP-W2** | `LP-W2-lead-processing` | Webhook / Event | Routes by `score`, triggers personalized follow-up emails, and posts hot lead alerts. |
| **LP-W3** | `LP-W3-email-intake-triage` | Webhook / Gmail | Triages incoming email, evaluates `needs_human`, generates approval links for Slack/Telegram. |
| **LP-W4** | `LP-W4-document-extraction` | Webhook (file) | Calls `/v1/documents/extract`, checks confidence threshold, alerts on discrepancy. |
| **LP-W5** | `LP-W5-voice-call-results` | Webhook (Vapi) | Processes voice call transcripts, extracts appointments, and requests callbacks. |
| **LP-W6** | `LP-W6-ecommerce-orders` | Webhook (Shopify) | Validates orders, decrements inventory, flags low-stock items (<5). |
| **LP-W7** | `LP-W7-scheduled-reports` | Cron (daily 18:00) | Generates executive daily KPI summaries and broadcasts via Slack and Email. |
| **LP-W8** | `LP-W8-error-handler-retries` | Error Trigger & 15m Cron | Catches failures, inserts into `failed_jobs`, alerts Slack, and retries failed jobs. |

---

## Importing Workflows into n8n

### Automated Import (Inside Docker Container):
```bash
docker compose exec n8n bash /data/workflows/../import.sh
```

### Manual Import via UI:
1. Open n8n at `http://localhost:5678`.
2. Go to **Workflows** → Click `+` or **Import from File**.
3. Select any workflow file from `n8n/workflows/*.json`.
4. Click **Activate** in the top right toggle.
