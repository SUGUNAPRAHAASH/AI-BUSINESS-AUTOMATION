import json
import pytest
from app.security import verify_shopify_hmac, verify_vapi_secret
from scripts.make_shopify_hmac import compute_shopify_hmac
from app.utils.idempotency import generate_idempotency_key


def test_shopify_hmac_valid():
    secret = "test_shopify_secret_123"
    body = b'{"id": 12345, "total": "299.00"}'
    valid_hmac = compute_shopify_hmac(secret, body)
    assert verify_shopify_hmac(body, valid_hmac, secret) is True


def test_shopify_hmac_tampered_body():
    secret = "test_shopify_secret_123"
    body = b'{"id": 12345, "total": "299.00"}'
    tampered_body = b'{"id": 12345, "total": "0.01"}'
    valid_hmac = compute_shopify_hmac(secret, body)
    assert verify_shopify_hmac(tampered_body, valid_hmac, secret) is False


def test_shopify_hmac_invalid_secret():
    secret = "test_shopify_secret_123"
    body = b'{"id": 12345, "total": "299.00"}'
    valid_hmac = compute_shopify_hmac(secret, body)
    assert verify_shopify_hmac(body, valid_hmac, "wrong_secret") is False


def test_vapi_secret_verification():
    secret = "vapi_secret_abc"
    assert verify_vapi_secret("vapi_secret_abc", secret) is True
    assert verify_vapi_secret("wrong_secret", secret) is False
    assert verify_vapi_secret("", secret) is False


def test_idempotency_key_deterministic():
    payload = {"order_id": 999, "customer": "test@example.com"}
    key1 = generate_idempotency_key("shopify", payload)
    key2 = generate_idempotency_key("shopify", payload)
    assert key1 == key2
