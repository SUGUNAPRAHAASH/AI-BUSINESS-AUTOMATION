import hashlib
import json
from typing import Any, Tuple
from app.utils.logging import logger


def generate_idempotency_key(source: str, payload: Any) -> str:
    """Generate a deterministic sha256 hash from source and payload."""
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(f"{source}:{serialized}".encode("utf-8")).hexdigest()
