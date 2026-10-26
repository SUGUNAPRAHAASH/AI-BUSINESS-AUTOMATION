from typing import List
from app.llm import get_llm_client


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Batch embed a list of texts using the configured LLM client."""
    client = get_llm_client()
    return await client.embed(texts)
