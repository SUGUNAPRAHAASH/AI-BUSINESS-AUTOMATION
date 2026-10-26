from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    tenant: str
    tenant_id: str
    channel: str
    external_id: Optional[str]
    conversation_id: str
    messages: List[Dict[str, Any]]
    current_input: str
    intent: str
    retrieved_context: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    lead_draft: Optional[Dict[str, Any]]
    lead_captured: Optional[Dict[str, Any]]
    handoff: bool
    handoff_reason: Optional[str]
    final_answer: str
    errors: List[str]
