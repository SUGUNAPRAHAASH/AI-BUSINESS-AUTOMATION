import asyncio
import asyncpg
from pathlib import Path

async def setup():
    print("Connecting to Supabase PostgreSQL...")
    conn = await asyncpg.connect(
        user="postgres.yojrrumkuzrzltrqrpqj",
        password="Leadpilot@624001",
        host="aws-0-ap-northeast-1.pooler.supabase.com",
        port=5432,
        database="postgres",
        timeout=30.0
    )
    print("Enabling extensions (vector, pgcrypto, pg_trgm)...")
    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    schema_file = Path("leadpilot-ai/db/init/002_schema.sql")
    if schema_file.exists():
        print("Executing 002_schema.sql...")
        content = schema_file.read_text(encoding="utf-8")
        clean_lines = [l for l in content.splitlines() if not l.strip().lower().startswith("create extension")]
        await conn.execute("\n".join(clean_lines))
        print("Schema tables successfully created!")

    seed_file = Path("leadpilot-ai/db/seed/seed.sql")
    if seed_file.exists():
        print("Executing seed.sql...")
        seed_content = seed_file.read_text(encoding="utf-8")
        await conn.execute(seed_content)
        print("Seed data successfully inserted!")

    rows = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
    tables = [r["table_name"] for r in rows]
    print(f"Total tables created in Supabase: {len(tables)}")
    print("Tables:", tables)

    await conn.close()
    print("Supabase database setup COMPLETE!")

if __name__ == "__main__":
    asyncio.run(setup())
