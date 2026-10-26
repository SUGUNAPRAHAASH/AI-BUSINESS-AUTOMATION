# LeadPilot AI — Model Context Protocol (MCP) Server

The LeadPilot AI MCP server exposes our clinical automation capabilities directly to external AI agents and desktop clients such as **Claude Desktop**, **Cursor**, and the **MCP Inspector**.

## Available Tools

| Tool Name | Parameters | Description |
|---|---|---|
| `search_knowledge_base` | `query: str`, `k: int = 5` | Hybrid semantic vector + BM25 keyword search across dental procedures, fees, and clinic policies. |
| `list_recent_leads` | `limit: int = 10`, `score: str = None` | Fetch patient inquiries categorized by intent (`hot`, `warm`, `cold`). |
| `lookup_lead` | `email_or_id: str` | Retrieve full lead details and conversation history by email address or UUID. |
| `create_lead` | `name: str`, `email: str`, `phone?: str`, `interest?: str` | Manually capture and qualify a new patient lead with instant CRM sync. |
| `get_dashboard_stats` | None | Fetch real-time operational statistics and health metrics. |

---

## Connecting Claude Desktop

To connect Claude Desktop to the local LeadPilot MCP server:

1. Open your Claude Desktop configuration file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the `leadpilot` MCP server configuration:

```json
{
  "mcpServers": {
    "leadpilot": {
      "command": "python",
      "args": [
        "d:/AI-BUSINESS-AUTOMATION/leadpilot-ai/services/mcp/server.py"
      ],
      "env": {
        "AI_SERVICE_URL": "http://localhost:8000",
        "AI_SERVICE_API_KEY": "lp_secret_key_demo_2026",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

3. Restart Claude Desktop. The hammer icon will appear in the input bar showing the 5 LeadPilot AI tools.

---

## Testing with MCP Inspector

You can test the MCP server interactively in your browser using the official Anthropic MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python services/mcp/server.py
```
