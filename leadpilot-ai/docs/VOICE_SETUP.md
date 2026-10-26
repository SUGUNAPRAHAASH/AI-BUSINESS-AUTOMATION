# LeadPilot AI — Voice AI (Vapi / Retell / Twilio) Integration Guide

LeadPilot AI natively supports bidirectional voice assistant webhooks. This guide details how to configure a free-trial **Vapi** voice assistant for BrightSmile Dental and route end-of-call summaries into the LeadPilot operations pipeline.

---

## 1. Creating a Vapi Assistant

1. Sign up for a free account at [Vapi.ai](https://vapi.ai/).
2. In the dashboard, click **Create Assistant** → Choose a blank template.
3. Configure the assistant persona:
   - **Name:** `BrightSmile Receptionist`
   - **Voice:** Choose a warm, professional voice (e.g. `Sarah` or `Ellie`).
   - **Model:** `gemini-1.5-flash` or `gpt-4o-mini`.

4. **System Prompt to Paste:**
```text
You are the virtual receptionist for BrightSmile Dental.
Your goal is to warmly greet callers, answer basic questions regarding dental cleanings, whitening, and Invisalign, and capture their appointment booking requests.

When a caller wants to book:
1. Ask for their full name.
2. Ask for their preferred appointment day and time (morning or afternoon).
3. Ask for their best callback phone number.
4. Confirm their details before saying goodbye.

Do not give medical treatment advice or prescribe drugs. If someone has acute pain or trauma, advise them to visit the clinic emergency room or call our emergency line at (555) 019-9000.
```

---

## 2. Exposing the Local Stack via Tunnel

To let Vapi reach your local Docker Compose or FastAPI instance during development, create a temporary secure tunnel using **cloudflared** or **ngrok**:

### Using Cloudflared (Free, no account needed):
```bash
cloudflared tunnel --url http://localhost:8000
```
*Cloudflared will output a public HTTPS URL like `https://random-words.trycloudflare.com`.*

### Setting Server URL in Vapi:
1. In your Vapi Assistant settings, navigate to the **Server URL** section.
2. Enter your endpoint:
   ```
   https://random-words.trycloudflare.com/webhooks/vapi
   ```
3. Set the **Server Secret** to match `VAPI_WEBHOOK_SECRET` in `.env` (`vapi_test_secret_key_12345`).
4. Ensure the **End of Call Report** event is checked.

---

## 3. Alternative Providers: Retell AI & Twilio

LeadPilot AI's call processing pipeline (`/v1/calls/summarize`) is completely provider-agnostic:

| Voice Provider | Integration Strategy |
|---|---|
| **Retell AI** | Configure Retell's post-call webhook to send the JSON transcript to `/v1/calls/summarize`. Retell provides pre-calculated call durations. |
| **Twilio Media Streams** | Ingest raw telephony via Twilio Studio or websocket audio streams. Use Whisper or Deepgram for real-time transcription, then forward the final transcript to `/v1/calls/summarize`. |
| **Bland AI** | Set Bland's `webhook` parameter in outbound dispatch calls pointing to LeadPilot AI. |
