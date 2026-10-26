import os
import uuid
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.db import execute, fetch_one, init_db
from app.rag.chunking import split_markdown_by_headings, chunk_text
from app.rag.embedder import generate_embeddings
from app.utils.logging import logger


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def ingest_document(
    tenant_id: str,
    title: str,
    source: str,
    content: str,
    force: bool = False
) -> Dict[str, Any]:
    """Ingest a single document into kb_documents and kb_chunks idempotently."""
    await init_db()
    content_hash = compute_content_hash(content)

    existing = await fetch_one(
        "SELECT id, content_hash FROM kb_documents WHERE tenant_id = ? AND source = ?",
        (tenant_id, source)
    )

    if existing and existing["content_hash"] == content_hash and not force:
        logger.info(f"Document '{title}' ({source}) unchanged. Skipping ingestion.")
        return {"status": "skipped", "document_id": existing["id"], "reason": "unchanged"}

    doc_id = existing["id"] if existing else str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    if existing:
        await execute(
            "UPDATE kb_documents SET title = ?, content_hash = ?, created_at = ? WHERE id = ?",
            (title, content_hash, now_iso, doc_id)
        )
        await execute("DELETE FROM kb_chunks WHERE document_id = ?", (doc_id,))
    else:
        await execute(
            "INSERT INTO kb_documents (id, tenant_id, title, source, content_hash, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (doc_id, tenant_id, title, source, content_hash, now_iso)
        )

    # Chunk content
    sections = split_markdown_by_headings(content)
    chunks = chunk_text(sections, chunk_size=800, chunk_overlap=100)

    # Embed chunks
    texts = [c["content"] for c in chunks]
    embeddings = await generate_embeddings(texts)

    # Insert chunks
    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        chunk_id = str(uuid.uuid4())
        meta = {
            "heading": chunk["heading"],
            "chunk_index": idx,
            "source": source
        }
        await execute(
            "INSERT INTO kb_chunks (id, document_id, tenant_id, chunk_index, content, metadata, embedding, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (chunk_id, doc_id, tenant_id, idx, chunk["content"], json.dumps(meta), json.dumps(emb), now_iso)
        )

    logger.info(f"Ingested '{title}': created {len(chunks)} chunks.")
    return {"status": "ingested", "document_id": doc_id, "chunks_count": len(chunks)}


async def ingest_knowledge_base_directory(
    directory_path: str,
    tenant_id: str = "a0000000-0000-0000-0000-000000000001"
) -> List[Dict[str, Any]]:
    """Scan and ingest all .md files in knowledge_base directory."""
    path = Path(directory_path)
    if not path.exists():
        logger.warning(f"Directory {directory_path} does not exist.")
        return []

    results = []
    for file in sorted(path.glob("*.md")):
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
        title = file.stem.replace("_", " ").title()
        res = await ingest_document(tenant_id, title, file.name, content)
        results.append(res)

    return results
