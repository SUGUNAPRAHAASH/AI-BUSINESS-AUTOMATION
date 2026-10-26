import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.db import insert_mock_outbox
from app.utils.logging import logger


class TelegramAdapter:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or settings.TELEGRAM_MODE
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID

    async def send_message(self, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"text": text, "chat_id": self.chat_id, "reply_markup": reply_markup}
        
        if self.mode == "real" and self.token and self.chat_id:
            try:
                url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                body: Dict[str, Any] = {
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }
                if reply_markup:
                    body["reply_markup"] = reply_markup
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(url, json=body)
                    if res.status_code == 200:
                        logger.info(f"Telegram real alert sent to chat {self.chat_id}")
                        await insert_mock_outbox("telegram", "send_message", payload)
                        return {"status": "sent", "telegram_response": res.json()}
                    else:
                        logger.warning(f"Telegram API error {res.status_code}: {res.text}")
            except Exception as e:
                logger.error(f"Failed to dispatch Telegram message: {e}")

        outbox_id = await insert_mock_outbox("telegram", "send_message", payload)
        return {"status": "mock_sent", "outbox_id": outbox_id}
