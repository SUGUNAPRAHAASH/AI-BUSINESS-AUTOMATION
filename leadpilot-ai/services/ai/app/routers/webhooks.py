import json
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from app.config import settings
from app.models import CallSummaryRequest, CallSummaryResponse
from app.features.call_summary import process_call_transcript
from app.integrations.shopify import ShopifyAdapter
from app.integrations.vapi import VapiAdapter
from app.security import verify_api_key, verify_shopify_hmac, verify_vapi_secret
from app.db import execute, fetch_one
from app.utils.idempotency import generate_idempotency_key
from app.utils.logging import logger

router = APIRouter(tags=["Webhooks & Voice"])


@router.post("/v1/calls/summarize", response_model=CallSummaryResponse, dependencies=[Depends(verify_api_key)])
async def summarize_call_endpoint(req: CallSummaryRequest):
    """Summarize call transcript and extract appointment intent."""
    result = await process_call_transcript(
        tenant_id="a0000000-0000-0000-0000-000000000001",
        external_call_id=req.external_call_id,
        transcript=req.transcript
    )
    return CallSummaryResponse(**result)


@router.post("/webhooks/shopify")
async def shopify_webhook_endpoint(
    request: Request,
    x_shopify_hmac_sha256: str = Header(None),
    x_shopify_order_id: str = Header(None)
):
    """
    Shopify orders/create webhook handler with HMAC-SHA256 signature verification
    and idempotent deduplication.
    """
    raw_body = await request.body()

    # HMAC Verification
    if settings.SHOPIFY_MODE == "real" or x_shopify_hmac_sha256:
        is_valid = verify_shopify_hmac(raw_body, x_shopify_hmac_sha256 or "", settings.SHOPIFY_WEBHOOK_SECRET)
        if not is_valid and x_shopify_hmac_sha256:
            logger.warning("Shopify HMAC signature verification failed.")
            raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Invalid HMAC signature"})

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail={"code": "BAD_REQUEST", "message": "Invalid JSON body"})

    # Idempotency check
    order_id = str(payload.get("id", payload.get("order_number", x_shopify_order_id or "default_order")))
    idempotency_key = f"shopify_order_{order_id}"

    existing = await fetch_one("SELECT id FROM webhook_events WHERE source = 'shopify' AND idempotency_key = ?", (idempotency_key,))
    if existing:
        logger.info(f"Duplicate Shopify webhook delivery detected for order {order_id}. Skipping processing.")
        return {"status": "duplicate", "order_id": order_id}

    # Record event
    await execute(
        "INSERT INTO webhook_events (id, source, idempotency_key, payload, status, created_at) "
        "VALUES (lower(hex(randomblob(16))), 'shopify', ?, ?, 'processed', datetime('now'))",
        (idempotency_key, json.dumps(payload))
    )

    shopify_adapter = ShopifyAdapter()
    result = await shopify_adapter.process_order(payload)
    return result


@router.post("/webhooks/vapi")
async def vapi_webhook_endpoint(
    request: Request,
    x_vapi_secret: str = Header(None)
):
    """
    Vapi voice agent webhook handler with secret verification and idempotency.
    Handles 'end-of-call-report' and function tool calls.
    """
    if settings.VAPI_MODE == "real" or x_vapi_secret:
        if not verify_vapi_secret(x_vapi_secret or "", settings.VAPI_WEBHOOK_SECRET) and x_vapi_secret:
            logger.warning("Vapi webhook secret verification failed.")
            raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Invalid Vapi secret header"})

    raw_body = await request.body()
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail={"code": "BAD_REQUEST", "message": "Invalid JSON body"})

    call_id = str(payload.get("message", {}).get("call", {}).get("id", payload.get("call_id", "vapi_123")))
    idempotency_key = f"vapi_call_{call_id}"

    existing = await fetch_one("SELECT id FROM webhook_events WHERE source = 'vapi' AND idempotency_key = ?", (idempotency_key,))
    if existing:
        return {"status": "duplicate", "call_id": call_id}

    await execute(
        "INSERT INTO webhook_events (id, source, idempotency_key, payload, status, created_at) "
        "VALUES (lower(hex(randomblob(16))), 'vapi', ?, ?, 'processed', datetime('now'))",
        (idempotency_key, json.dumps(payload))
    )

    vapi_adapter = VapiAdapter()
    result = await vapi_adapter.handle_end_of_call(payload)
    return result
