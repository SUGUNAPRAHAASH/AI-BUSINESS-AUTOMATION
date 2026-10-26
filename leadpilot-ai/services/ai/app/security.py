import hmac
import hashlib
import base64
import re
import secrets
from fastapi import Request, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Card masking regex: sequences of 13 to 19 digits possibly separated by spaces or hyphens
CARD_REGEX = re.compile(r'\b(?:\d[ -]*?){13,19}\b')
# SSN masking regex: 3 digits - 2 digits - 4 digits
SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')


def mask_pii(text: str) -> str:
    """Mask credit card numbers and SSNs to protect sensitive patient/client data."""
    if not text:
        return text

    def mask_card(match: re.Match) -> str:
        s = match.group(0)
        digits = [c for c in s if c.isdigit()]
        if len(digits) >= 13:
            # Mask all but the last 4 digits
            masked_digits = '*' * (len(digits) - 4) + ''.join(digits[-4:])
            return f"[MASKED_CARD: {masked_digits}]"
        return s

    masked = CARD_REGEX.sub(mask_card, text)
    masked = SSN_REGEX.sub("[MASKED_SSN]", masked)
    return masked


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Enforce constant-time comparison for API key authentication."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Missing required X-API-Key header"}
        )
    if not secrets.compare_digest(api_key, settings.AI_SERVICE_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "FORBIDDEN", "message": "Invalid API Key provided"}
        )
    return api_key


def verify_shopify_hmac(raw_body: bytes, hmac_header: str, secret: str) -> bool:
    """Verify Shopify HMAC-SHA256 signature using constant-time comparison."""
    if not hmac_header or not secret:
        return False
    digest = hmac.new(
        secret.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).digest()
    computed_hmac = base64.b64encode(digest).decode('utf-8')
    return secrets.compare_digest(computed_hmac, hmac_header)


def verify_vapi_secret(secret_header: str, expected_secret: str) -> bool:
    """Verify Vapi secret header using constant-time comparison."""
    if not secret_header or not expected_secret:
        return False
    return secrets.compare_digest(secret_header, expected_secret)
