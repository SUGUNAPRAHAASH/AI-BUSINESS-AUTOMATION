import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.db import insert_mock_outbox
from app.utils.logging import logger


class AirtableAdapter:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or settings.AIRTABLE_MODE
        self.api_key = settings.AIRTABLE_API_KEY
        self.base_id = settings.AIRTABLE_BASE_ID
        self.table_name = settings.AIRTABLE_TABLE_NAME or "tbl3krL8HajZx6jxQ"

    async def create_record(self, table_name: Optional[str] = None, fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        target_table = table_name or self.table_name
        data_fields = fields or {}
        payload = {"table": target_table, "fields": data_fields}

        if self.mode == "real" and self.api_key and self.base_id:
            try:
                url = f"https://api.airtable.com/v0/{self.base_id}/{target_table}"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                body = {
                    "records": [{"fields": data_fields}],
                    "typecast": True
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(url, json=body, headers=headers)
                    if res.status_code in (200, 201):
                        record_id = res.json().get("records", [{}])[0].get("id")
                        logger.info(f"Real Airtable record created: {record_id}")
                        await insert_mock_outbox("airtable", "create_record", payload)
                        return {"status": "created", "airtable_id": record_id}
                    else:
                        logger.warning(f"Airtable API error {res.status_code}: {res.text}")
            except Exception as e:
                logger.error(f"Failed to post to Airtable: {e}")

        outbox_id = await insert_mock_outbox("airtable", "create_record", payload)
        return {"status": "mock_created", "outbox_id": outbox_id}
