from typing import Dict, Any, Optional
from app.config import settings
from app.db import insert_mock_outbox


class TelegramAdapter:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or settings.TELEGRAM_MODE
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID

    async def send_message(self, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"text": text, "chat_id": self.chat_id, "reply_markup": reply_markup}
        outbox_id = await insert_mock_outbox("telegram", "send_message", payload)
        return {"status": "mock_sent", "outbox_id": outbox_id}
