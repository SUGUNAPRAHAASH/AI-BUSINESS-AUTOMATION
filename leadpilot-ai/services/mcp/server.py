import os
import sys
import json
import inspect
from typing import Optional, List, Dict, Any, Callable
import httpx

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8000")
AI_SERVICE_API_KEY = os.getenv("AI_SERVICE_API_KEY", "lp_secret_key_demo_2026")


def _get_headers() -> Dict[str, str]:
    return {
        "X-API-Key": AI_SERVICE_API_KEY,
        "Content-Type": "application/json"
    }


# Attempt to import official FastMCP, or provide compliant built-in MCP engine
try:
    from mcp.server.fastmcp import FastMCP as _SDKFastMCP
    HAS_OFFICIAL_MCP = True
except Exception:
    HAS_OFFICIAL_MCP = False


class BuiltinFastMCP:
    """Production-grade MCP server implementation adhering to MCP standard protocols."""

    def __init__(self, name: str = "LeadPilot-AI-Hub"):
        self.name = name
        self.tools: Dict[str, Callable] = {}
        self.tool_descriptions: Dict[str, str] = {}
        self.prompts: Dict[str, Callable] = {}

    def tool(self):
        def decorator(fn: Callable):
            name = fn.__name__
            self.tools[name] = fn
            self.tool_descriptions[name] = (fn.__doc__ or "").strip()
            return fn
        return decorator

    def prompt(self):
        def decorator(fn: Callable):
            name = fn.__name__
            self.prompts[name] = fn
            return fn
        return decorator

    def list_tools(self) -> List[Dict[str, Any]]:
        result = []
        for name, fn in self.tools.items():
            result.append({
                "name": name,
                "description": self.tool_descriptions.get(name, ""),
                "parameters": {
                    "type": "object",
                    "properties": {
                        param: {"type": "string"}
                        for param in inspect.signature(fn).parameters
                    }
                }
            })
        return result

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        fn = self.tools[name]
        return fn(**arguments)

    def run(self, transport: str = "stdio", port: int = 8765):
        if transport == "stdio":
            # JSON-RPC stdio loop
            print(f"LeadPilot MCP Server '{self.name}' running on stdio transport.", file=sys.stderr)
            for line in sys.stdin:
                try:
                    req = json.loads(line)
                    req_id = req.get("id")
                    method = req.get("method")
                    if method == "tools/list":
                        resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": self.list_tools()}}
                    elif method == "tools/call":
                        params = req.get("params", {})
                        t_name = params.get("name")
                        t_args = params.get("arguments", {})
                        t_res = self.call_tool(t_name, t_args)
                        resp = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": str(t_res)}]}}
                    else:
                        resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
                except Exception as e:
                    err_resp = {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}
                    sys.stdout.write(json.dumps(err_resp) + "\n")
                    sys.stdout.flush()


# Initialize instance
mcp = _SDKFastMCP("LeadPilot-AI-Hub") if HAS_OFFICIAL_MCP else BuiltinFastMCP("LeadPilot-AI-Hub")


@mcp.tool()
def search_knowledge_base(query: str, k: int = 5) -> str:
    """
    Search the BrightSmile Dental clinical knowledge base using hybrid vector and keyword search.
    Returns treatment procedures, pricing, opening hours, insurance, and clinic policies.
    """
    url = f"{AI_SERVICE_URL}/v1/kb/search"
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, params={"q": query}, headers=_get_headers())
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                if not results:
                    return f"No matching documents found for query: '{query}'"
                formatted = []
                for idx, r in enumerate(results, 1):
                    formatted.append(f"{idx}. [{r['title']} - {r['source']}] (Score: {r['score']})\n{r['content']}\n")
                return "\n".join(formatted)
            return f"Error searching knowledge base: HTTP {res.status_code}"
    except Exception as e:
        return f"Connection error to LeadPilot AI service: {str(e)}"


@mcp.tool()
def list_recent_leads(limit: int = 10, score: Optional[str] = None) -> str:
    """
    List recent patient inquiries and qualified leads captured by the AI agent.
    Filterable by score: 'hot', 'warm', 'cold'.
    """
    url = f"{AI_SERVICE_URL}/v1/leads"
    params = {"limit": limit}
    if score:
        params["score"] = score
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, params=params, headers=_get_headers())
            if res.status_code == 200:
                leads = res.json().get("leads", [])
                if not leads:
                    return "No leads found."
                out = [f"Found {len(leads)} leads:"]
                for l in leads:
                    out.append(f"- [{l['score'].upper()}] {l.get('name') or 'Anonymous'} ({l.get('email') or 'No email'}) - {l.get('interest') or 'General'} | {l.get('summary')}")
                return "\n".join(out)
            return f"Error listing leads: HTTP {res.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"


@mcp.tool()
def lookup_lead(email_or_id: str) -> str:
    """
    Lookup a specific lead record by email address or lead UUID.
    """
    url = f"{AI_SERVICE_URL}/v1/leads"
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=_get_headers())
            if res.status_code == 200:
                leads = res.json().get("leads", [])
                for l in leads:
                    if l.get("id") == email_or_id or (l.get("email") and l.get("email").lower() == email_or_id.lower()):
                        return json.dumps(l, indent=2)
                return f"Lead '{email_or_id}' not found."
            return f"Error: HTTP {res.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"


@mcp.tool()
def create_lead(name: str, email: str, phone: Optional[str] = None, interest: Optional[str] = None) -> str:
    """
    Manually register a new qualified prospective patient lead into LeadPilot AI and sync to CRM.
    """
    url = f"{AI_SERVICE_URL}/v1/chat"
    text = f"My name is {name}, email: {email}"
    if phone:
        text += f", phone: {phone}"
    if interest:
        text += f", interested in {interest}"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.post(url, json={"message": text, "channel": "mcp"}, headers=_get_headers())
            if res.status_code == 200:
                lead = res.json().get("lead_captured")
                return f"Lead created successfully:\n{json.dumps(lead, indent=2)}"
            return f"Error creating lead: HTTP {res.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"


@mcp.tool()
def get_dashboard_stats() -> str:
    """
    Retrieve real-time operational statistics: total leads, hot leads today, emails triaged, and failed jobs.
    """
    url = f"{AI_SERVICE_URL}/v1/admin/stats"
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=_get_headers())
            if res.status_code == 200:
                return json.dumps(res.json(), indent=2)
            return f"Error: HTTP {res.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"


@mcp.prompt()
def lead_followup_email(patient_name: str, treatment_interest: str) -> str:
    """Generate a high-converting follow-up email template for a patient consultation."""
    return f"""Please draft a warm, professional, high-converting follow-up email for:
Patient Name: {patient_name}
Treatment Interest: {treatment_interest}
Clinic: BrightSmile Dental

Tone: Friendly, medical excellence, clear invitation for a complimentary 3D digital scan. Include a 24-hour response window."""


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    port = int(os.getenv("MCP_PORT", "8765"))
    mcp.run(transport=transport, port=port)
