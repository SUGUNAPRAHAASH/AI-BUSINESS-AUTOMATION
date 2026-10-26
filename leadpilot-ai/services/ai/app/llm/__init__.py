from app.config import settings
from app.llm.base import LLMClient, LLMResult, ToolCall, CircuitBreaker
from app.llm.mock import MockLLMClient
from app.llm.gemini import GeminiClient
from app.llm.anthropic import AnthropicClient
from app.llm.openai import OpenAIClient

_circuit_breaker = CircuitBreaker(failure_threshold=3, reset_timeout_sec=60.0)


def get_llm_client() -> LLMClient:
    provider = settings.LLM_PROVIDER.lower()
    if settings.GEMINI_MODE == "mock" or provider == "mock":
        return MockLLMClient(embedding_dim=settings.EMBEDDING_DIM)
    if provider == "gemini":
        return GeminiClient()
    if provider == "anthropic":
        return AnthropicClient()
    if provider == "openai":
        return OpenAIClient()
    return MockLLMClient(embedding_dim=settings.EMBEDDING_DIM)
