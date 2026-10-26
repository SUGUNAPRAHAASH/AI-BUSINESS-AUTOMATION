import json
import math
import re
from typing import List, Dict, Any, Optional
from app.db import fetch_all, fetch_one
from app.rag.embedder import generate_embeddings
from app.utils.logging import logger


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two unit-normalized or non-normalized vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


def compute_rrf(vector_ranks: Dict[str, int], keyword_ranks: Dict[str, int], k: int = 60) -> Dict[str, float]:
    """Reciprocal Rank Fusion (RRF) formula: score(d) = sum(1 / (k + rank))."""
    scores: Dict[str, float] = {}
    all_doc_ids = set(vector_ranks.keys()).union(set(keyword_ranks.keys()))

    for doc_id in all_doc_ids:
        score = 0.0
        if doc_id in vector_ranks:
            score += 1.0 / (k + vector_ranks[doc_id])
        if doc_id in keyword_ranks:
            score += 1.0 / (k + keyword_ranks[doc_id])
        scores[doc_id] = score

    return scores


class HybridRetriever:
    def __init__(self, tenant_id: str = "a0000000-0000-0000-0000-000000000001", min_score_threshold: float = 0.005):
        self.tenant_id = tenant_id
        self.min_score_threshold = min_score_threshold

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not query.strip():
            return []

        # 1. Fetch chunks for tenant
        rows = await fetch_all(
            "SELECT c.id, c.document_id, c.content, c.metadata, c.embedding, d.title, d.source "
            "FROM kb_chunks c "
            "JOIN kb_documents d ON c.document_id = d.id "
            "WHERE c.tenant_id = ?",
            (self.tenant_id,)
        )
        if not rows:
            return []

        # 2. Vector search rank
        query_embeddings = await generate_embeddings([query])
        query_vec = query_embeddings[0] if query_embeddings else []

        vector_scores: List[tuple] = []
        for r in rows:
            emb_str = r.get("embedding")
            if emb_str:
                try:
                    vec = json.loads(emb_str)
                    sim = cosine_similarity(query_vec, vec)
                    vector_scores.append((r["id"], sim))
                except Exception:
                    pass

        vector_scores.sort(key=lambda x: x[1], reverse=True)
        vector_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(vector_scores)}

        # 3. Keyword / BM25-style match rank
        query_tokens = set(re.findall(r'\b\w+\b', query.lower()))
        keyword_scores: List[tuple] = []
        for r in rows:
            content_lower = r["content"].lower()
            title_lower = r["title"].lower()
            # Match score with title bonus
            token_matches = sum(1 for t in query_tokens if t in content_lower)
            title_matches = sum(2 for t in query_tokens if t in title_lower)
            total_k_score = token_matches + title_matches
            if total_k_score > 0:
                keyword_scores.append((r["id"], total_k_score))

        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        keyword_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(keyword_scores)}

        # 4. Fuse using RRF
        rrf_scores = compute_rrf(vector_ranks, keyword_ranks, k=60)

        # 5. Build results
        doc_lookup = {r["id"]: r for r in rows}
        sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        results: List[Dict[str, Any]] = []
        for doc_id, score in sorted_rrf[:top_k]:
            if score < self.min_score_threshold:
                continue
            item = doc_lookup[doc_id]
            meta = json.loads(item["metadata"]) if isinstance(item["metadata"], str) else item["metadata"]
            results.append({
                "id": doc_id,
                "title": item["title"],
                "source": item["source"],
                "content": item["content"],
                "score": round(score, 5),
                "metadata": meta
            })

        return results
