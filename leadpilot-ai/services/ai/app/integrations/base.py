from typing import Protocol, Dict, Any, Optional
from app.db import insert_mock_outbox


class IntegrationError(Exception):
    def __init__(self, message: str, integration: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.integration = integration
        self.status_code = status_code
