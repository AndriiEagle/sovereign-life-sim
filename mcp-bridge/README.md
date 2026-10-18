# Local MCP transport

`client.py` forwards authenticated loopback JSON-RPC and observes the durable SSE journal. HTTP, UI and the official SDK stdio adapter use one Runtime/Store. `events.mjs` is only a compatibility helper for the archived Phase 1 DTO; `command-queue.mjs` is the durable browser request queue shared with Argon.

Run the app, prepare the pinned SDK environment and register this checkout:

```powershell
python -B scripts/serve.py
# Separate terminal:
python -B scripts/configure_mcp.py
.runtime/bridge-venv/Scripts/python.exe -B scripts/verify_mcp.py --project-config
```

For first-time SDK installation see the root README. The registrar writes only ignored `.codex/config.toml` inside this repository, using absolute paths to this checkout's venv interpreter and `scripts/mcp_server.py`. Existing unrelated settings are preserved; conflicting `sovereign_local` settings are rejected without rewriting them. Global/account configuration and secrets are never copied. Re-run after moving the checkout. [Official Codex MCP project configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) is loaded for trusted projects on the next client startup/reconnect. Registration does not hot-load tools into an existing chat.

For a custom app state directory, supply `--session-file .runtime/<state>/session.json`
to registration and SDK verification. The file must remain under this checkout's
private `.runtime`; the client accepts only an authenticated IPv4 loopback URL.

On startup, and before a tool call after server-token rotation, the adapter performs a harmless `select_node` of the already selected node, observes its real SSE event, then acknowledges it. Only that successful exchange sets `LIVE_LOCAL_BRIDGE`. A server restart invalidates freshness; the next adapter exchange restores it. An unavailable server leaves the adapter callable for a later retry; it never invents a live status. Concurrent tool starts share the connection lock. Tokens are read from ignored local session files, never URLs/stdout/Git.

Tools: `get_state`, `command`, `probe_bridge`. The adapter allowlists local scenario commands. Model/provider sessions stay `NOT_CONNECTED`; SDK transport acceptance is not evidence that Claude/Codex used a tool. No inference is requested by registration or health verification. Historical DTO notes: `audit/phase1-mcp-notes.md`.
