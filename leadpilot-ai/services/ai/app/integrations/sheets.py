from typing import Dict, Any, List, Optional
from app.config import settings
from app.db import insert_mock_outbox


class GoogleSheetsAdapter:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or settings.SHEETS_MODE

    async def append_row(self, sheet_name: str, values: List[Any]) -> Dict[str, Any]:
        payload = {"sheet_name": sheet_name, "values": values}
        outbox_id = await insert_mock_outbox("sheets", "append_row", payload)
        return {"status": "mock_appended" if self.mode != "real" else "appended", "outbox_id": outbox_id}
