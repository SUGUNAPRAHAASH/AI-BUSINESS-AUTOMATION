from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException
from app.models import ChatRequest, ChatResponse, KBSearchResponse, KBChunk
from app.agent.graph import agent_instance
from app.rag.retriever import HybridRetriever
from app.rag.ingest import ingest_knowledge_base_directory
from app.security import verify_api_key

router = APIRouter(prefix="/v1", tags=["Chat & Knowledge Base"])


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
async def chat_endpoint(req: ChatRequest):
    """
    RAG support chat and lead capture agent endpoint.
    Retrieves grounded business facts and captures prospective patient leads.
    """
    tenant_id = "a0000000-0000-0000-0000-000000000001"
    res = await agent_instance.run(
        tenant_id=tenant_id,
        message=req.message,
        channel=req.channel,
        external_id=req.external_id,
        conversation_id=req.conversation_id
    )
    return ChatResponse(
        answer=res["answer"],
        citations=res["citations"],
        lead_captured=res["lead_captured"],
        handoff=res["handoff"],
        conversation_id=res["conversation_id"]
    )


@router.post("/kb/ingest", dependencies=[Depends(verify_api_key)])
async def ingest_kb():
    """Ingest markdown files from knowledge_base directory into vector database."""
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    kb_path = base_dir / "knowledge_base"
    results = await ingest_knowledge_base_directory(str(kb_path))
    return {"status": "success", "ingested": results}


@router.get("/kb/search", response_model=KBSearchResponse, dependencies=[Depends(verify_api_key)])
async def search_kb(q: str = Query(..., min_length=1)):
    """Hybrid search across the knowledge base for debugging and MCP."""
    tenant_id = "a0000000-0000-0000-0000-000000000001"
    retriever = HybridRetriever(tenant_id=tenant_id)
    chunks = await retriever.search(q, top_k=5)
    parsed_chunks = [
        KBChunk(
            id=c["id"],
            title=c["title"],
            source=c["source"],
            content=c["content"],
            score=c["score"],
            metadata=c["metadata"]
        )
        for c in chunks
    ]
    return KBSearchResponse(query=q, results=parsed_chunks, count=len(parsed_chunks))
