from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass, field
import time
from app.db import record_llm_usage
from app.utils.logging import logger


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None


@dataclass
class LLMResult:
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    model: str = "mock"
    provider: str = "mock"


class LLMClient(Protocol):
    async def generate(
        self,
        system: str,
        messages: List[Dict[str, str]],
        *,
        json_schema: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> LLMResult:
        ...

    async def embed(self, texts: List[str]) -> List[List[float]]:
        ...


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout_sec: float = 60.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout_sec = reset_timeout_sec
        self.consecutive_failures = 0
        self.last_failure_time = 0.0

    def record_success(self):
        self.consecutive_failures = 0

    def record_failure(self):
        self.consecutive_failures += 1
        self.last_failure_time = time.time()

    def is_open(self) -> bool:
        if self.consecutive_failures >= self.failure_threshold:
            if time.time() - self.last_failure_time > self.reset_timeout_sec:
                # Half-open test
                return False
            return True
        return False
