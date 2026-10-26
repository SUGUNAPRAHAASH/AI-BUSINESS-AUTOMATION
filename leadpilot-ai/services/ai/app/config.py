import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Find .env in current or parent directories
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseModel):
    # Core & Security
    AI_SERVICE_API_KEY: str = os.getenv("AI_SERVICE_API_KEY", "lp_secret_key_demo_2026")
    CORS_ORIGIN: str = os.getenv("CORS_ORIGIN", "http://localhost:3000")
    PORT: int = int(os.getenv("PORT", "8000"))
    AUTO_REPLY_ENABLED: bool = os.getenv("AUTO_REPLY_ENABLED", "false").lower() in ("true", "1")
    TENANT_DEFAULT_SLUG: str = os.getenv("TENANT_DEFAULT_SLUG", "brightsmile")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///leadpilot.db")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))

    # LLM & Embeddings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-3.5-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "3072"))

    # Provider Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Mode Switches (Mock vs Real)
    GEMINI_MODE: str = os.getenv("GEMINI_MODE", "mock").lower()
    HUBSPOT_MODE: str = os.getenv("HUBSPOT_MODE", "mock").lower()
    SLACK_MODE: str = os.getenv("SLACK_MODE", "mock").lower()
    GMAIL_MODE: str = os.getenv("GMAIL_MODE", "mock").lower()
    SHEETS_MODE: str = os.getenv("SHEETS_MODE", "mock").lower()
    AIRTABLE_MODE: str = os.getenv("AIRTABLE_MODE", "mock").lower()
    TELEGRAM_MODE: str = os.getenv("TELEGRAM_MODE", "mock").lower()
    SHOPIFY_MODE: str = os.getenv("SHOPIFY_MODE", "mock").lower()
    VAPI_MODE: str = os.getenv("VAPI_MODE", "mock").lower()

    # Integration Credentials
    HUBSPOT_TOKEN: str = os.getenv("HUBSPOT_TOKEN", "")
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    AIRTABLE_API_KEY: str = os.getenv("AIRTABLE_API_KEY", "")
    AIRTABLE_BASE_ID: str = os.getenv("AIRTABLE_BASE_ID", "")
    AIRTABLE_TABLE_NAME: str = os.getenv("AIRTABLE_TABLE_NAME", "Leads")
    SHOPIFY_WEBHOOK_SECRET: str = os.getenv("SHOPIFY_WEBHOOK_SECRET", "shopify_test_secret_key_12345")
    VAPI_WEBHOOK_SECRET: str = os.getenv("VAPI_WEBHOOK_SECRET", "vapi_test_secret_key_12345")

    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "1025"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "BrightSmile Dental <hello@brightsmile.example.com>")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")


settings = Settings()
