# LeadPilot AI — 5-Minute Client Loom Demo Script

Use this exact timed script to record a polished walkthrough video for a prospective client or hiring manager.

---

### [0:00 - 0:30] Introduction & The Problem
**Visual:** LeadPilot AI Overview Dashboard (`http://localhost:3000`)
> *"Hi there! If you run a local medical or service business, your front desk loses hours every week answering repetitive questions, playing phone tag for leads, sorting through supplier invoices, and triaging emails.
>
> Today, I'm excited to walk you through **LeadPilot AI**—an autonomous virtual AI operations hub built for BrightSmile Dental. It unifies a grounded clinical chatbot, automated lead qualification, email triage, optical invoice auditing, and voice AI into one cohesive, production-grade system."*

---

### [0:30 - 1:30] Support Chat with Grounded RAG & Safety Guardrails
**Visual:** Switch to `/chat` page.
> *"Let's start with patient support. Notice our knowledge base has 6 clinical documents covering pricing, Saturday hours, and HIPAA policies. Let's ask a multi-part question:"*
>
> **Action:** Type into chat:
> ```
> How much is teeth whitening and do you do weekend appointments?
> ```
>
> *"Within milliseconds, the agent retrieves exact pricing from `pricing.md` and our Saturday hours from `opening_hours.md`, citing both sources transparently. It never hallucinates prices.
>
> Now watch what happens when someone tests the clinical boundary:"*
>
> **Action:** Type into chat:
> ```
> Do you treat horses?
> ```
>
> *"The agent politely declines because it is strictly a human dental practice, and triggers an autonomous escalation alert to the front-desk Slack channel."*

---

### [1:30 - 2:30] Lead Capture, Scoring Rubric & CRM Sync
**Visual:** Still on `/chat`, then navigate to `/leads` and `/outbox`.
> *"Now let's test lead generation. A prospective patient reaches out with buying intent:"*
>
> **Action:** Type into chat:
> ```
> I'm interested in Invisalign, my name is Priya Nair, priya@example.com, I'd like to start next month, budget around 4000.
> ```
>
> *"Notice the badge: **Lead Qualified: HOT**. Our LangGraph state machine detected contact info, a specific procedure, and a 30-day timeline.
>
> When we jump over to our **Patient Leads CRM** tab, Priya's record is immediately saved with her score reason and recommended next action. In the **Mock Outbox Inspector**, you can see the payload dispatched to HubSpot CRM and the immediate Slack alert sent to the sales team."*

---

### [2:30 - 3:15] Email Triage & Human-in-the-Loop Approval
**Visual:** Switch to `/emails` page.
> *"Next is incoming email triage. In the left panel, every inbound message is classified into categories like appointments, sales, billing, or spam.
>
> For sensitive emails—like patient rescheduling or billing questions—the AI drafts an empathetic, context-aware reply and queues it for approval. With one click on **Approve & Send Draft**, the front-desk confirms the dispatch without typing from scratch."*

---

### [3:15 - 3:45] Optical Document Extraction & Math Auditing
**Visual:** Switch to `/documents` page.
> *"Handling supplier invoices is traditionally tedious. Watch how LeadPilot audits incoming PDFs:"*
>
> **Action:** Upload `samples/invoices/invoice_01_supplies.pdf`.
>
> *"The system parses vendor details, line items, and quantities. Crucially, it performs mathematical cross-checks: verifying that the sum of line items matches the subtotal and that subtotal plus tax equals the grand total. If a vendor miscalculates by even a cent, it flags a discrepancy alert and reduces the confidence rating before appending to Google Sheets."*

---

### [3:45 - 4:15] Reliability: Dead-Letter Queue & Retries
**Visual:** Switch to `/failed-jobs` page.
> *"In production, external APIs fail—HubSpot might return a 500 error or a webhook might time out. LeadPilot implements an exponential backoff retry policy. If all retries fail, it writes to this **Failed Jobs** dead-letter queue.
>
> An operator can review the error payload and simply click **Retry Job** to re-dispatch the handler without losing data."*

---

### [4:15 - 4:45] Model Context Protocol (MCP) in Claude Desktop
**Visual:** Show MCP tool configuration or terminal test.
> *"LeadPilot also runs a native **Model Context Protocol (MCP)** server. This allows AI tools like Claude Desktop or Cursor to connect directly to the clinic's database, searching the knowledge base or looking up patient records using natural language."*

---

### [4:45 - 5:00] Wrap-up & Call to Action
**Visual:** Return to `/` (Overview Dashboard).
> *"Everything you saw runs mock-first out-of-the-box, backed by an automated 48-test verification suite and Docker Compose orchestration.
>
> If you're looking to automate your business operations with reliable, production-ready AI systems, let's talk. Thank you!"*
