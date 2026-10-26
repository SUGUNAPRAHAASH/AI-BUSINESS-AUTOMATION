import hmac
import hashlib
import base64
import json
import sys


def compute_shopify_hmac(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


if __name__ == "__main__":
    secret = sys.argv[1] if len(sys.argv) > 1 else "shopify_test_secret_key_12345"
    sample_payload = {
        "id": 892341209,
        "email": "sarah.buyer@example.com",
        "total_price": "299.00"
    }
    raw_body = json.dumps(sample_payload).encode("utf-8")
    sig = compute_shopify_hmac(secret, raw_body)
    print(f"Shopify HMAC Signature for test payload:\n{sig}")
