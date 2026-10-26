# LeadPilot AI — Known Limitations & Architectural Caveats

In the spirit of honest, transparent software engineering, this document details intentional design boundaries, known edge cases, and current limitations in LeadPilot AI.

## 1. Integrations & Third-Party APIs
- **Mock-First Defaults:** To prevent test suite disruption and guarantee 100% offline functionality, all adapters default to `MOCK` mode unless explicit production API keys are provided in `.env`.
- **HubSpot Conflict Resolution:** When creating a contact that already exists in HubSpot (HTTP 409 conflict), the adapter logs a conflict resolution notice and updates the contact rather than failing.
- **Gmail OAuth Flow:** Direct SMTP via Mailpit is used for local email catching. Full Google Workspace OAuth2 requires completing the Google Cloud Consent screen and obtaining refresh tokens as detailed in `CREDENTIALS_SETUP.md`.

## 2. RAG & Retrieval Scope
- **Chunk Window Size:** Document chunks are budgeted between 600 and 900 characters with 100-character overlap. Inquiries spanning multiple disconnected treatment sections simultaneously may retrieve top 5 chunks that capture the primary 2-3 topics.
- **Lexical/Semantic Ranking:** Extremely short single-word queries without clinical context (e.g. "hi", "dental") receive lower vector density scores than detailed natural language questions ("How much is teeth whitening?").

## 3. Optical Document Extraction
- **PDF Text vs Vision:** In mock/local mode, the service relies on `pypdf` text stream parsing and regex extraction. Scanned bitmap PDFs without OCR text layers require Gemini 2.5 Vision mode (`GEMINI_MODE=real` with active API key).
- **Mathematical Tolerance:** The validation engine allows a tolerance of $0.05 on subtotal and tax calculations to account for fractional rounding across international currencies.

## 4. Voice AI Webhooks
- **Vapi Protocol Assumptions:** Webhook payload parsing supports Vapi's standard `end-of-call-report` format (`message.call.transcript`). Other providers (Retell, Bland, Twilio) require format normalization as documented in `VOICE_SETUP.md`.
