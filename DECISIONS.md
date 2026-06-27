## ADR-0011: Direct Tool Calls Over MCP Server for V8 Streamlit Deployment

- **Status:** Accepted
- **Date:** 2026-06-27

### Context and Problem Statement

V8 is a public Streamlit deployment of the V7 agent.
V6 and V7 used FastMCP 3.4.2 with streamable-http transport
running as a background thread in Google Colab.

In a public Streamlit Community Cloud deployment, background
threads are unreliable and the MCP server startup adds latency
on every cold start. The free tier has a 1GB RAM cap.

### Decision Drivers

- Public demo must work reliably for recruiters on first open
- Cold start time must be minimized on free tier hosting
- V6 and V7 already prove MCP mastery — V8 has a different mission
- Demo reliability matters more than demonstrating additional skills

### Considered Options

**Option 1: Keep MCP server (FastMCP background thread)**
- Same architecture as V6/V7
- Pro: Demonstrates MCP in deployment context
- Con: Background thread unreliable on Streamlit Cloud
- Con: Adds ~2 second cold start latency
- Con: Port 8000 dependency adds failure point

**Option 2: Direct tool calls via @tool decorator**
- Simplified architecture — no server process
- Pro: Zero startup latency, no port dependency
- Pro: Works reliably on Streamlit Cloud free tier
- Pro: Cleaner code — easier for employers to read
- Con: MCP not demonstrated in V8 (but proven in V6/V7)

### Decision Outcome

**Chosen: Option 2 — direct tool calls**

MCP mastery is already proven in V6 and V7, which live in the
same repository. V8's mission is public demo reliability for
recruiters and hiring managers — not additional skill demonstration.

Running FastMCP as a background thread in Streamlit Community Cloud
introduces startup race conditions and is an unnecessary complexity
for a public demo.

This is a deliberate senior engineering judgment: use the right
tool for the mission, not the most impressive-looking tool.

### Consequences

- Good: Zero MCP server startup time
- Good: No localhost port dependency
- Good: Works reliably on Streamlit Community Cloud free tier
- Good: Simpler codebase — faster for employers to review
- Good: Shorter cold start time improves recruiter first impression
- Neutral: MCP capability not shown in V8 — shown in V6/V7 same repo
- Bad: None for V8's stated mission
