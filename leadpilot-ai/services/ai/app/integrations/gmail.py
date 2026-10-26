import smtplib
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
        self.smtp_from = settings.SMTP_FROM

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

        if self.mode != "real":
            outbox_id = await insert_mock_outbox("gmail", "send_email", payload)
            return {"status": "mock_sent", "outbox_id": outbox_id, "payload": payload}

        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_from
            msg['To'] = to_addr
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

            server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=5)
            server.send_message(msg)
            server.quit()
            logger.info(f"Email sent via SMTP ({self.smtp_host}:{self.smtp_port}) to {to_addr}")
            return {"status": "sent", "transport": "smtp"}
        except Exception as e:
            logger.warning(f"SMTP send failed ({e}). Falling back to mock outbox.")
            outbox_id = await insert_mock_outbox("gmail", "send_email", payload)
            return {"status": "fallback_mock", "outbox_id": outbox_id}
