import os
import time
import json
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings
from app.llm.base import LLMResult, ToolCall
from app.llm.mock import MockLLMClient
from app.utils.logging import logger


class GeminiClient:
    """Gemini client using Google Gemini API with fallback to MockLLMClient."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.LLM_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL
        self.mock = MockLLMClient(embedding_dim=settings.EMBEDDING_DIM)

    async def generate(
        self,
        system: str,
        messages: List[Dict[str, str]],
        *,
        json_schema: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> LLMResult:
        if not self.api_key or settings.GEMINI_MODE == "mock":
            return await self.mock.generate(system, messages, json_schema=json_schema, tools=tools, temperature=temperature)

        start_time = time.time()
        candidate_models = [self.model]
        for alt in ["gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-3.5-flash-lite"]:
            if alt not in candidate_models:
                candidate_models.append(alt)

        contents = []
        for msg in messages:
            role = "model" if msg.get("role") in ("assistant", "model") else "user"
            contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}]
            })

        payload: Dict[str, Any] = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system}]},
            "generationConfig": {
                "temperature": temperature,
            }
        }
        if json_schema:
            payload["generationConfig"]["responseMimeType"] = "application/json"
            payload["generationConfig"]["responseSchema"] = json_schema

        async with httpx.AsyncClient(timeout=25.0) as client:
            for model_name in candidate_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
                try:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        content = ""
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            content = "".join([p.get("text", "") for p in parts])
                        usage = data.get("usageMetadata", {})
                        latency = int((time.time() - start_time) * 1000)
                        return LLMResult(
                            content=content,
                            prompt_tokens=usage.get("promptTokenCount", 0),
                            completion_tokens=usage.get("candidatesTokenCount", 0),
                            latency_ms=latency,
                            model=model_name,
                            provider="gemini"
                        )
                    elif res.status_code in (429, 503, 404):
                        logger.warning(f"Gemini model '{model_name}' returned {res.status_code}. Trying next candidate model...")
                        continue
                    else:
                        logger.warning(f"Gemini API returned {res.status_code}: {res.text}. Trying next candidate model...")
                        continue
                except Exception as e:
                    logger.warning(f"Error calling Gemini model '{model_name}': {e}. Trying next candidate...")
                    continue

        logger.error("All Gemini candidate models failed or unavailable. Falling back to intelligent mock.")
        return await self.mock.generate(system, messages, json_schema=json_schema, tools=tools, temperature=temperature)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key or settings.GEMINI_MODE == "mock":
            return await self.mock.embed(texts)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.embedding_model}:batchEmbedContents?key={self.api_key}"
        requests_list = [{"model": f"models/{self.embedding_model}", "content": {"parts": [{"text": t}]}} for t in texts]
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json={"requests": requests_list})
                if res.status_code == 200:
                    embeddings_data = res.json().get("embeddings", [])
                    return [e.get("values", []) for e in embeddings_data]
                else:
                    logger.warning(f"Gemini embed returned {res.status_code}. Falling back to mock embedder.")
                    return await self.mock.embed(texts)
        except Exception as e:
            logger.error(f"Error calling Gemini embed: {e}. Falling back to mock embedder.")
            return await self.mock.embed(texts)
