import pytest
from services.mcp.server import mcp


def test_mcp_tools_registered():
    """Verify all 5 tools are properly decorated and registered."""
    if hasattr(mcp, "list_tools"):
        tools = mcp.list_tools()
        tool_names = [t["name"] for t in tools]
    else:
        tools = mcp._tool_manager.list_tools()
        tool_names = [t.name for t in tools]

    expected = [
        "search_knowledge_base",
        "list_recent_leads",
        "lookup_lead",
        "create_lead",
        "get_dashboard_stats"
    ]
    for exp in expected:
        assert exp in tool_names, f"Expected MCP tool '{exp}' not registered!"
