from typing import Dict, Any, Optional
from app.config import settings
from app.db import insert_mock_outbox


class AirtableAdapter:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or settings.AIRTABLE_MODE

    async def create_record(self, table_name: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"table": table_name, "fields": fields}
        outbox_id = await insert_mock_outbox("airtable", "create_record", payload)
        return {"status": "mock_created", "outbox_id": outbox_id}
