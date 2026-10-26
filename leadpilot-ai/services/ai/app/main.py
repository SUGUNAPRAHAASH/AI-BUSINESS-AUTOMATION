import time
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import init_db
from app.rag.ingest import ingest_knowledge_base_directory
from app.routers import (
    health_router,
    chat_router,
    leads_router,
    emails_router,
    documents_router,
    webhooks_router,
    reports_router,
    admin_router,
)
from app.utils.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables and seed knowledge base
    logger.info("Initializing LeadPilot AI Service...")
    await init_db()
    # Ingest default knowledge base documents
    kb_dir = Path(__file__).resolve().parent.parent.parent.parent / "knowledge_base"
    if kb_dir.exists():
        await ingest_knowledge_base_directory(str(kb_dir))
    logger.info("LeadPilot AI Service startup complete.")
    yield
    logger.info("LeadPilot AI Service shutting down.")


app = FastAPI(
    title="LeadPilot AI — Business Automation Service",
    description="Virtual AI operations team & automation hub for small businesses",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
origins = [
    settings.CORS_ORIGIN,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5678",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID Middleware & Structured Access Logging
@app.middleware("http")
async def request_id_and_logging_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = req_id

    start_time = time.time()
    try:
        response = await call_next(request)
        latency_ms = int((time.time() - start_time) * 1000)
        response.headers["X-Request-ID"] = req_id
        if request.url.path != "/health":
            logger.info(
                f"{request.method} {request.url.path} -> {response.status_code} ({latency_ms}ms)",
                extra={"request_id": req_id, "latency_ms": latency_ms}
            )
        return response
    except Exception as exc:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {exc}",
            exc_info=True,
            extra={"request_id": req_id, "latency_ms": latency_ms}
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred.",
                    "request_id": req_id
                }
            }
        )


# Global Exception Handler for consistent error shape
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    if isinstance(exc.detail, dict):
        code = exc.detail.get("code", "ERROR")
        message = exc.detail.get("message", "An error occurred")
    else:
        code = "HTTP_ERROR"
        message = str(exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": req_id
            }
        }
    )


# Register all routers
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(leads_router)
app.include_router(emails_router)
app.include_router(documents_router)
app.include_router(webhooks_router)
app.include_router(reports_router)
app.include_router(admin_router)
