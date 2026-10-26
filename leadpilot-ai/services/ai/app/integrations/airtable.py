import httpx
from typing import Dict, Any, Optional, List
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

    async def fetch_records(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all records from Airtable table."""
        target_table = table_name or self.table_name
        if not self.api_key or not self.base_id:
            logger.warning("Airtable API key or Base ID not configured, cannot fetch records.")
            return []
        try:
            url = f"https://api.airtable.com/v0/{self.base_id}/{target_table}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            records = []
            offset = None
            async with httpx.AsyncClient(timeout=15.0) as client:
                while True:
                    params = {}
                    if offset:
                        params["offset"] = offset
                    res = await client.get(url, headers=headers, params=params)
                    if res.status_code == 200:
                        data = res.json()
                        records.extend(data.get("records", []))
                        offset = data.get("offset")
                        if not offset:
                            break
                    else:
                        logger.warning(f"Failed to fetch Airtable records: {res.status_code} {res.text}")
                        break
            return records
        except Exception as e:
            logger.error(f"Error fetching Airtable records: {e}")
            return []

    async def sync_to_sqlite(self) -> int:
        """Sync leads from Airtable into local SQLite so leads persist across Render redeployments."""
        import re
        import uuid
        from datetime import datetime, timezone
        from app.db import execute, fetch_one

        records = await self.fetch_records()
        if not records:
            return 0

        synced_count = 0
        for rec in records:
            rec_id = rec.get("id")
            if not rec_id:
                continue
            fields = rec.get("fields", {})
            raw_name = fields.get("Name", "")
            notes = fields.get("Notes", "")
            if not raw_name and not notes:
                continue

            # Parse lead attributes
            name_clean = re.sub(r'\s*\([^)]*\)', '', raw_name).strip() or "Visitor"
            score_match = re.search(r'Score:\s*(HOT|WARM|COLD)', raw_name, re.I) or re.search(r'Score:\s*(HOT|WARM|COLD)', notes, re.I)
            score = score_match.group(1).lower() if score_match else "warm"

            email_m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', notes)
            email = email_m.group(0) if email_m else None

            phone_m = re.search(r'Phone:\s*([^|\n]+)', notes)
            phone = phone_m.group(1).strip() if (phone_m and phone_m.group(1).strip() != "N/A") else None

            interest_m = re.search(r'Interest:\s*([^|\n]+)', notes)
            interest = interest_m.group(1).strip() if (interest_m and interest_m.group(1).strip() != "N/A") else "General Dental Care"

            budget_m = re.search(r'Budget:\s*([^,\n]+)', notes)
            budget_text = budget_m.group(1).strip() if budget_m else None

            timeline_m = re.search(r'Timeline:\s*([^)\n]+)', notes)
            timeline_text = timeline_m.group(1).strip() if timeline_m else "Upcoming"

            summary = notes or f"Lead from Airtable: {name_clean}"
            created_at = rec.get("createdTime") or datetime.now(timezone.utc).isoformat()
            lead_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, rec_id))

            # Check if this lead already exists by ID, email, or name
            existing = await fetch_one("SELECT id FROM leads WHERE id = ?", (lead_uuid,))
            if not existing and email:
                existing = await fetch_one("SELECT id FROM leads WHERE lower(email) = lower(?)", (email,))

            if existing:
                await execute(
                    "UPDATE leads SET name = COALESCE(?, name), email = COALESCE(?, email), phone = COALESCE(?, phone), "
                    "interest = COALESCE(?, interest), score = ?, summary = ?, updated_at = ? WHERE id = ?",
                    (name_clean, email, phone, interest, score, summary[:300], created_at, existing["id"])
                )
            else:
                await execute(
                    "INSERT INTO leads (id, tenant_id, conversation_id, name, email, phone, interest, budget_text, "
                    "timeline_text, score, score_reason, summary, source, crm_id, status, created_at, updated_at) "
                    "VALUES (?, 'brightsmile', NULL, ?, ?, ?, ?, ?, ?, ?, 'Synced from Airtable CRM', ?, 'airtable', ?, 'qualified', ?, ?)",
                    (lead_uuid, name_clean, email, phone, interest, budget_text, timeline_text, score, summary[:300], rec_id, created_at, created_at)
                )
            synced_count += 1

        logger.info(f"Successfully synced {synced_count} leads from Airtable into SQLite.")
        return synced_count

