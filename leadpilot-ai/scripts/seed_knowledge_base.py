import asyncio
import sys
from pathlib import Path

# Add services/ai to sys.path so app modules import directly
ai_service_path = Path(__file__).resolve().parent.parent / "services" / "ai"
sys.path.insert(0, str(ai_service_path))

from app.db import init_db
from app.rag.ingest import ingest_knowledge_base_directory


async def main():
    print("=== Seeding BrightSmile Dental Knowledge Base ===")
    await init_db()
    kb_dir = Path(__file__).resolve().parent.parent / "knowledge_base"
    results = await ingest_knowledge_base_directory(str(kb_dir))
    for r in results:
        print(f"Ingested doc: {r}")
    print("=== Knowledge Base Seeding Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
