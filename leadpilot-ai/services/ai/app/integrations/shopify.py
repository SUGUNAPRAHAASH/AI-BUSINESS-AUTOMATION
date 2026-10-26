import json
from typing import Dict, Any, Optional
from app.config import settings
from app.db import execute, fetch_one, insert_mock_outbox
from app.utils.logging import logger


class ShopifyAdapter:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or settings.SHOPIFY_MODE

    async def process_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        order_id = str(order_data.get("id", order_data.get("order_number", "unknown")))
        customer_email = order_data.get("email") or order_data.get("customer", {}).get("email")
        total_price = float(order_data.get("total_price", 0.0))
        currency = order_data.get("currency", "USD")
        line_items = order_data.get("line_items", [])

        # Store order
        await execute(
            "INSERT INTO orders (id, tenant_id, external_id, customer_email, total, currency, line_items, raw, created_at) "
            "VALUES (lower(hex(randomblob(16))), 'a0000000-0000-0000-0000-000000000001', ?, ?, ?, ?, ?, ?, datetime('now'))",
            (order_id, customer_email, total_price, currency, json.dumps(line_items), json.dumps(order_data))
        )

        # Check inventory and deduct
        low_stock_alerts = []
        for item in line_items:
            sku = item.get("sku")
            qty = int(item.get("quantity", 1))
            if sku:
                inv = await fetch_one("SELECT stock, low_stock_threshold, name FROM inventory WHERE sku = ?", (sku,))
                if inv:
                    new_stock = max(0, inv["stock"] - qty)
                    await execute("UPDATE inventory SET stock = ? WHERE sku = ?", (new_stock, sku))
                    if new_stock <= inv["low_stock_threshold"]:
                        low_stock_alerts.append({"sku": sku, "name": inv["name"], "remaining": new_stock})

        # Post Slack alert for low stock if needed
        for alert in low_stock_alerts:
            await insert_mock_outbox("slack", "low_stock_alert", {
                "channel": "#inventory-alerts",
                "message": f"LOW STOCK WARNING: {alert['name']} ({alert['sku']}) has only {alert['remaining']} units left!"
            })

        # Thank you email outbox
        if customer_email:
            await insert_mock_outbox("gmail", "order_confirmation_email", {
                "to": customer_email,
                "subject": f"Thank you for your BrightSmile Dental order #{order_id}",
                "total": total_price
            })

        return {
            "order_id": order_id,
            "status": "processed",
            "low_stock_alerts": low_stock_alerts
        }
