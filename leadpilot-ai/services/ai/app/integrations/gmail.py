import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from app.config import settings
from app.db import insert_mock_outbox
from app.utils.logging import logger


class EmailAdapter:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or settings.GMAIL_MODE
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM
        self.resend_api_key = settings.RESEND_API_KEY

    async def send_email(
        self,
        to_addr: str,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> Dict[str, Any]:
        payload = {
            "from": self.smtp_from,
            "to": to_addr,
            "subject": subject,
            "body": body
        }

        # 1. Try Resend API if API key provided
        if self.resend_api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.resend_api_key}",
                    "Content-Type": "application/json"
                }
                resend_payload = {
                    "from": "BrightSmile Dental <onboarding@resend.dev>",
                    "to": [to_addr],
                    "subject": subject,
                    "html" if is_html else "text": body
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post("https://api.resend.com/emails", headers=headers, json=resend_payload)
                    if resp.status_code in (200, 201):
                        logger.info(f"Live email delivered via Resend API to {to_addr}")
                        return {"status": "sent", "transport": "resend", "data": resp.json()}
                    elif resp.status_code == 403 and to_addr != "prahaashnms18@gmail.com":
                        logger.warning(f"Resend sandbox requires delivery to account owner prahaashnms18@gmail.com. Routing copy.")
                        resend_payload["to"] = ["prahaashnms18@gmail.com"]
                        resend_payload["subject"] = subject
                        retry_resp = await client.post("https://api.resend.com/emails", headers=headers, json=resend_payload)
                        if retry_resp.status_code in (200, 201):
                            logger.info(f"Delivered sandbox copy to prahaashnms18@gmail.com (for {to_addr})")
                            return {"status": "sent_sandbox_owner", "transport": "resend", "data": retry_resp.json()}
                    else:
                        logger.warning(f"Resend API error ({resp.status_code}): {resp.text}")
            except Exception as e:
                logger.error(f"Resend dispatch error: {e}")

        # 2. Try SMTP if real mode or credentials configured
        if self.mode == "real" or self.smtp_user:
            try:
                msg = MIMEMultipart()
                msg['From'] = self.smtp_from
                msg['To'] = to_addr
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=8)
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                server.quit()
                logger.info(f"Email sent via SMTP ({self.smtp_host}:{self.smtp_port}) to {to_addr}")
                return {"status": "sent", "transport": "smtp"}
            except Exception as e:
                logger.warning(f"SMTP send failed ({e}). Falling back to mock outbox.")

        # 3. Fallback to mock outbox
        outbox_id = await insert_mock_outbox("gmail", "send_email", payload)
        return {"status": "mock_sent", "outbox_id": outbox_id, "payload": payload}
