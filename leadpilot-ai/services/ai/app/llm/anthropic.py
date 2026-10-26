from typing import List, Dict, Any, Optional
from app.llm.base import LLMResult
from app.llm.mock import MockLLMClient
from app.config import settings


class AnthropicClient:
    def __init__(self):
        self.mock = MockLLMClient(embedding_dim=settings.EMBEDDING_DIM)

    async def generate(self, system: str, messages: List[Dict[str, str]], *, json_schema: Optional[Dict[str, Any]] = None, tools: Optional[List[Dict[str, Any]]] = None, temperature: float = 0.2) -> LLMResult:
        return await self.mock.generate(system, messages, json_schema=json_schema, tools=tools, temperature=temperature)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        return await self.mock.embed(texts)
