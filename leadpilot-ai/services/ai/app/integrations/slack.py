from typing import Dict, Any, Optional
import httpx
from app.config import settings
from app.db import insert_mock_outbox
from app.utils.logging import logger


class SlackAdapter:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or settings.SLACK_MODE
        self.webhook_url = settings.SLACK_WEBHOOK_URL

    async def send_message(self, text: str, blocks: Optional[list] = None, channel: str = "#leads-and-alerts") -> Dict[str, Any]:
        payload = {"text": text, "channel": channel}
        if blocks:
            payload["blocks"] = blocks

        if self.mode != "real" or not self.webhook_url:
            outbox_id = await insert_mock_outbox("slack", "send_message", payload)
            return {"status": "mock_delivered", "outbox_id": outbox_id, "payload": payload}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(self.webhook_url, json=payload)
                if res.status_code == 200:
                    return {"status": "delivered", "response": res.text}
                else:
                    logger.warning(f"Slack webhook returned {res.status_code}. Logging to mock outbox.")
                    outbox_id = await insert_mock_outbox("slack", "send_message", payload)
                    return {"status": "fallback_mock", "outbox_id": outbox_id}
        except Exception as e:
            logger.error(f"Slack delivery error: {e}. Falling back to mock.")
            outbox_id = await insert_mock_outbox("slack", "send_message", payload)
            return {"status": "fallback_mock", "outbox_id": outbox_id}
