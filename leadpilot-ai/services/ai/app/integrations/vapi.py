from typing import Dict, Any, Optional
from app.config import settings
from app.db import insert_mock_outbox
from app.features.call_summary import process_call_transcript


class VapiAdapter:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or settings.VAPI_MODE

    async def handle_end_of_call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        message = payload.get("message", payload)
        call = message.get("call", {})
        call_id = str(call.get("id", message.get("call_id", "vapi_call_default")))
        transcript = message.get("transcript", "") or call.get("transcript", "")

        result = await process_call_transcript(
            tenant_id="a0000000-0000-0000-0000-000000000001",
            external_call_id=call_id,
            transcript=transcript
        )

        outbox_id = await insert_mock_outbox("vapi", "end_of_call_processed", {
            "call_id": call_id,
            "caller": result["caller_name"],
            "summary": result["summary"]
        })
        result["outbox_id"] = outbox_id
        return result
