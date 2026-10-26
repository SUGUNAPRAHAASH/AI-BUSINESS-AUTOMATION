# LeadPilot AI — Credentials & Third-Party Integration Setup Guide

LeadPilot AI is built to run 100% offline out-of-the-box using built-in mock adapters. When transitioning to real client operations, follow this step-by-step guide to connect production services.

---

## 1. Google Gemini API Key (`GEMINI_API_KEY`)
1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Sign in with any Google account.
3. Click **Get API key** in the left navigation sidebar.
4. Click **Create API key in new project**.
5. Copy the generated key string (starts with `AIzaSy...`).
6. Paste into your `.env` file:
   ```env
   GEMINI_API_KEY=AIzaSy...
   GEMINI_MODE=real
   ```

---

## 2. Telegram Bot Token (`TELEGRAM_BOT_TOKEN`)
1. Open the Telegram app and search for the official **@BotFather**.
2. Send the message `/newbot`.
3. Follow the prompts: choose a display name (e.g., `BrightSmile Assistant`) and a username ending in `bot` (e.g., `BrightSmileOpsBot`).
4. BotFather will provide an HTTP API token (format `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).
5. To find your Chat ID: message **@userinfobot** on Telegram.
6. Set in `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdef...
   TELEGRAM_CHAT_ID=987654321
   TELEGRAM_MODE=real
   ```

---

## 3. Slack Incoming Webhook (`SLACK_WEBHOOK_URL`)
1. Go to [Slack API: Your Apps](https://api.slack.com/apps).
2. Click **Create New App** → **From scratch**.
3. Name it `LeadPilot Ops` and select your Slack workspace.
4. Under **Add features and functionality**, click **Incoming Webhooks**.
5. Toggle **Activate Incoming Webhooks** to **On**.
6. Click **Add New Webhook to Workspace** at the bottom.
7. Select your target channel (e.g., `#sales-leads` or `#ops-alerts`) and click **Allow**.
8. Copy the Webhook URL:
   ```env
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00/B00/XXXXX
   SLACK_MODE=real
   ```

---

## 4. HubSpot Private App Token (`HUBSPOT_TOKEN`)
1. Log into your free [HubSpot](https://app.hubspot.com/) account.
2. Click the **Settings (gear icon)** in the top navigation bar.
3. In the left sidebar, navigate to **Integrations** → **Private Apps**.
4. Click **Create a private app**.
5. Name it `LeadPilot Automation`.
6. On the **Scopes** tab, enable the following permissions:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
7. Click **Create app** in the top right.
8. Click **Continue creating** and copy the personal access token (starts with `pat-na1-...`).
9. Set in `.env`:
   ```env
   HUBSPOT_TOKEN=pat-na1-...
   HUBSPOT_MODE=real
   ```

---

## 5. Google Workspace / Gmail OAuth (Optional)
If using the Gmail API instead of local Mailpit SMTP:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project named `LeadPilot Business Automation`.
3. Go to **APIs & Services** → **OAuth consent screen** → Select **External** → Save.
4. Go to **Credentials** → **Create Credentials** → **OAuth client ID**.
5. Application type: **Web application**.
6. Authorized redirect URIs: Add your n8n OAuth redirect URL (`http://localhost:5678/rest/oauth2-credential/callback`).
7. Save client ID and secret in n8n's Google credential manager.
