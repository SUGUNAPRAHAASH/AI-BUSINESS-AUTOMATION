from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
import uuid


# Standard API Error Response
class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


# Health & Integration Status
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str
    embedding_dim: int
    modes: Dict[str, str]
    last_llm_call: Optional[str] = None


# Chat & RAG
class Citation(BaseModel):
    title: str
    source: str
    score: float


class ChatRequest(BaseModel):
    tenant: str = "brightsmile"
    channel: str = "web"
    external_id: Optional[str] = None
    conversation_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    lead_captured: Optional[Dict[str, Any]] = None
    handoff: bool = False
    conversation_id: str
    scheduling_card: Optional[Dict[str, Any]] = None


# Knowledge Base
class KBChunk(BaseModel):
    id: str
    title: str
    source: str
    content: str
    score: float
    metadata: Dict[str, Any] = {}


class KBSearchResponse(BaseModel):
    query: str
    results: List[KBChunk]
    count: int


# Lead Scoring & CRM
class LeadQualifyRequest(BaseModel):
    text: Optional[str] = None
    conversation_id: Optional[str] = None
    tenant: str = "brightsmile"


class LeadResponse(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    interest: Optional[str] = None
    budget_text: Optional[str] = None
    timeline_text: Optional[str] = None
    score: str = Field(..., pattern="^(hot|warm|cold)$")
    score_reason: str = Field(..., max_length=200)
    summary: str = Field(..., max_length=300)
    next_best_action: Optional[str] = "Follow up with patient"
    crm_id: Optional[str] = None
    crm_synced_at: Optional[str] = None
    status: str = "new"
    created_at: Optional[str] = None


class LeadListResponse(BaseModel):
    leads: List[LeadResponse]
    total: int


# Email Triage
class EmailTriageRequest(BaseModel):
    tenant: str = "brightsmile"
    message_id: str
    from_addr: str
    subject: str
    body: str


class EmailTriageResponse(BaseModel):
    id: Optional[str] = None
    category: str = Field(..., pattern="^(support|sales|appointment|billing|spam|other)$")
    priority: str = Field(..., pattern="^(low|normal|high)$")
    entities: Dict[str, Any] = {}
    sentiment: str = "neutral"
    draft_reply: str
    needs_human: bool = False
    reason: str
    action: str = "needs_approval"


# Document Extraction
class InvoiceLineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float


class InvoiceExtractionResponse(BaseModel):
    id: Optional[str] = None
    vendor_name: str
    vendor_address: Optional[str] = None
    invoice_number: str
    invoice_date: str
    due_date: Optional[str] = None
    currency: str = "USD"
    line_items: List[InvoiceLineItem] = []
    subtotal: float
    tax: float
    total: float
    confidence: float
    validation_errors: List[str] = []


# Call Summary
class CallSummaryRequest(BaseModel):
    tenant: str = "brightsmile"
    external_call_id: str
    transcript: str


class CallSummaryResponse(BaseModel):
    id: Optional[str] = None
    external_call_id: str
    summary: str
    caller_name: Optional[str] = None
    phone: Optional[str] = None
    intent: Optional[str] = None
    appointment_request: Optional[Dict[str, Any]] = None
    sentiment: str = "neutral"
    follow_up_needed: bool = False


# Admin & Observability
class FailedJobResponse(BaseModel):
    id: str
    job_type: str
    payload: Dict[str, Any]
    error: str
    attempts: int
    status: str
    created_at: str
    last_attempt_at: Optional[str] = None


class MockOutboxItem(BaseModel):
    id: str
    integration: str
    action: str
    payload: Dict[str, Any]
    created_at: str


class AdminStatsResponse(BaseModel):
    total_leads: int
    hot_leads_today: int
    total_conversations: int
    emails_triaged: int
    documents_extracted: int
    failed_jobs: int
    recent_lead_velocity: List[Dict[str, Any]] = []
    integration_modes: Dict[str, str] = {}
