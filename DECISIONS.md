# Architecture Decision Records — LangGraph Agent Series V1-V8

All decisions documented using MADR 4.0.0 format.
Each ADR records one specific design choice — what was decided,
what alternatives were considered, and why.

Stored in the repository alongside the code so decisions remain
in sync with the implementation.

---

## ADR-0001: AST-Based Safe Evaluator Over eval() for Calculator Tool

- **Status:** Accepted
- **Applies from:** V6
- **Carried forward in:** V7, V8

### Context and Problem Statement

The calculator tool receives math expressions as text strings from user
input via the LLM. A function must evaluate these strings and return
numeric results. The simplest approach is Python's built-in `eval()`.

### Decision Drivers

- User input must never be trusted as safe code
- eval() executes any valid Python — not just math
- A deployed public app (V8) increases the attack surface

### Considered Options

**Option 1: eval(expression)**
- Pro: one line of code, handles all math
- Con: executes any Python code — `os.system("rm -rf /")` is valid input
- Con: serious security vulnerability in any internet-facing app

**Option 2: ast.parse() + SAFE_OPERATORS whitelist**
- Pro: reads the expression into a tree, never executes it directly
- Pro: whitelist of 4 operations only (add, subtract, multiply, divide)
- Pro: anything outside the whitelist raises ValueError immediately
- Con: more code to write

### Decision Outcome

**Chosen: Option 2 — AST-based safe evaluator**

Whitelist approach means only 4 operations are possible. Any attempt
to inject code (function calls, imports, attribute access) hits the
`else: raise ValueError` branch and stops immediately.

### Consequences

- Good: zero code injection risk from math expressions
- Good: explicit whitelist is easy to audit and extend
- Good: interview talking point — shows security awareness
- Bad: cannot handle advanced math (exponents, functions) without
  extending the whitelist deliberately

---

## ADR-0002: streamable-http Over stdio or SSE for MCP Transport

- **Status:** Accepted
- **Applies from:** V6
- **Carried forward in:** V7

### Context and Problem Statement

FastMCP 3.4.2 supports three transport options for connecting the MCP
server to the agent client: stdio, SSE (Server-Sent Events), and
streamable-http. The agent runs in Google Colab alongside the server.

### Decision Drivers

- Must work reliably inside Google Colab runtime
- Must support bidirectional communication for tool results
- Must not require external infrastructure

### Considered Options

**Option 1: stdio**
- Requires subprocess management
- Colab subprocess handling is unreliable
- Hard to debug when connections drop

**Option 2: SSE (Server-Sent Events)**
- One-directional by design (server to client only)
- Requires workaround for client-to-server messages
- Connection reliability issues observed in testing

**Option 3: streamable-http**
- HTTP-based — reliable in any Python environment
- Bidirectional — supports full tool call and result cycle
- FastMCP runs as a background thread on localhost:8000
- Standard HTTP means no special runtime support needed

### Decision Outcome

**Chosen: Option 3 — streamable-http**

Runs on `http://127.0.0.1:8000/mcp`. Background thread started with
`threading.Thread(target=run_server, daemon=True)`. Client connects
via `MultiServerMCPClient` using `"transport": "http"`.

### Consequences

- Good: reliable in Colab, no subprocess issues
- Good: standard HTTP — easy to debug with any HTTP tool
- Good: daemon=True means server dies when notebook stops
- Neutral: requires `nest_asyncio.apply()` in Colab for async compat

---

## ADR-0003: StateGraph Over create_agent for V7 Production Agent

- **Status:** Accepted
- **Applies from:** V7

### Context and Problem Statement

V7 combines V5 dual memory with V6 MCP tools. Two approaches exist for
building the agent loop: the prebuilt `create_react_agent` shortcut
from langgraph.prebuilt, or a hand-built `StateGraph` with explicit
nodes and edges.

### Decision Drivers

- V7 needs custom nodes: load_memories and save_memories
- Memory nodes require store and config parameters injected by LangGraph
- The progression of the series should show graph-level control

### Considered Options

**Option 1: create_react_agent from langgraph.prebuilt**
- Pro: fewer lines of code
- Con: no control over what nodes exist or their order
- Con: cannot inject load_memories before agent and save_memories after
- Con: marked deprecated in LangGraph 1.1.x

**Option 2: Hand-built StateGraph with explicit 4 nodes**
- Pro: full control — load_memories -> agent -> tools -> save_memories
- Pro: custom should_continue router
- Pro: compatible with store injection into node function signatures
- Con: more code

### Decision Outcome

**Chosen: Option 2 — hand-built StateGraph**

The 4-node graph gives explicit control:
```
START -> load_memories -> agent -> tools -> agent -> save_memories -> END
```

Memory nodes only work correctly when LangGraph can inject `store` and
`config` as function parameters — this only works with explicit nodes.

### Consequences

- Good: full architectural control
- Good: memory injection works correctly
- Good: shows senior-level LangGraph knowledge (not just shortcuts)
- Good: create_react_agent deprecation avoided

---

## ADR-0004: create_agent from langchain.agents Over Deprecated create_react_agent

- **Status:** Accepted
- **Applies from:** V6

### Context and Problem Statement

V6 builds an MCP agent using tools discovered at runtime from the MCP
server. An agent runner must be chosen to bind the LLM and tools
together. LangGraph's prebuilt `create_react_agent` from
`langgraph.prebuilt` was the historical choice but is deprecated.

### Decision Drivers

- Must not use deprecated APIs in portfolio code
- HR and technical reviewers check imports for freshness signals
- Must work with tools loaded dynamically from MCP at runtime

### Considered Options

**Option 1: create_react_agent from langgraph.prebuilt**
- Deprecated in LangGraph 1.1.x
- Still functional but throws deprecation warnings
- Wrong signal to send in portfolio code

**Option 2: create_agent from langchain.agents**
- Current, non-deprecated API
- Takes model and tools as parameters
- Works with dynamically loaded MCP tools

### Decision Outcome

**Chosen: Option 2 — create_agent from langchain.agents**

Import: `from langchain.agents import create_agent`

### Consequences

- Good: no deprecation warnings in output
- Good: correct signal to employers — using current APIs
- Good: works with MCP tools loaded at runtime

---

## ADR-0005: Dual Memory Scopes — InMemorySaver and InMemoryStore

- **Status:** Accepted
- **Applies from:** V5
- **Carried forward in:** V7, V8

### Context and Problem Statement

An agent that only remembers the current conversation is limited.
Users benefit from agents that also remember facts across different
sessions. Two separate memory problems exist: conversation continuity
(short-term) and user profile persistence (long-term).

### Decision Drivers

- Short-term: agent must recall earlier messages in the same chat
- Long-term: agent must recall user facts (name, city, goals) across chats
- Must use different keys to scope each memory correctly

### Considered Options

**Option 1: InMemorySaver only**
- Handles conversation continuity via thread_id
- Cannot store structured user facts across threads
- Memory lost when thread changes

**Option 2: InMemoryStore only**
- Can store arbitrary facts
- Does not handle conversation message continuity natively

**Option 3: Both InMemorySaver + InMemoryStore**
- InMemorySaver scoped by thread_id (one conversation)
- InMemoryStore scoped by user_id (one person across all conversations)
- Each scope handles exactly what it is designed for

### Decision Outcome

**Chosen: Option 3 — both memory systems**

```python
app = graph.compile(
    checkpointer=InMemorySaver(),  # conversation history
    store=InMemoryStore()          # user facts
)
```

Config carries both IDs:
```python
config = {"configurable": {
    "thread_id": "chat_1",    # which conversation
    "user_id":   "danish"     # which person
}}
```

### Consequences

- Good: clean separation of concerns — each memory has one job
- Good: conversation continuity works independently of fact storage
- Good: user facts survive new conversations (different thread_id)
- Good: strong portfolio signal — dual memory is a senior design pattern

---

## ADR-0006: UUID Append-Style Memory Deduplication for V7

- **Status:** Accepted
- **Applies from:** V7

### Context and Problem Statement

V5 used a fixed-key dict merge (`{**old, **new}`) for memory storage.
V7 switches to an append-style UUID-keyed approach for each memory
entry. This requires a different deduplication strategy since multiple
entries can now exist for the same user.

### Decision Drivers

- Append-style allows individual memory entries, not one merged blob
- Must prevent saving duplicate facts on every message
- Deduplication must handle LLM's tendency to re-extract known facts

### Considered Options

**Option 1: Skip dedup entirely**
- Fast to implement
- Results in hundreds of duplicate memory entries over time
- Degrades retrieval quality

**Option 2: Single-layer dedup (code only)**
- Compare new fact against existing entries
- Misses cases where LLM rephrases a known fact

**Option 3: Two-layer dedup (LLM prompt + code)**
- Layer 1: Feed existing facts into extraction prompt — LLM avoids
  re-extracting what it already knows
- Layer 2: Exact-string set check in code before store.put()
- Both layers must pass before a memory is saved

### Decision Outcome

**Chosen: Option 3 — two-layer deduplication**

Layer 1 (prompt-level): existing facts included in EXTRACT_PROMPT
context so LLM knows what is already stored.

Layer 2 (code-level): new fact string checked against set of all
existing fact strings. Skip if exact match found.

Log output: `"Skipped duplicate"` confirms dedup working.

### Consequences

- Good: clean memory store even after 100+ conversations
- Good: LLM extraction improves because it sees existing context
- Good: interview talking point — shows systems thinking
- Neutral: slight overhead from two-pass check
- Bad: two-layer complexity overkill for simple use cases

---

## ADR-0007: Groq llama-3.3-70b-versatile at temperature=0 Across All Notebooks

- **Status:** Accepted
- **Applies from:** V5
- **Carried forward in:** V6, V7, V8

### Context and Problem Statement

Different notebooks could use different LLM providers or models.
A consistent choice across the series affects reproducibility,
comparison across versions, and portfolio coherence.

### Decision Drivers

- Groq free tier available — no cost during portfolio development
- Consistent model across series = consistent quality baseline
- temperature=0 required for predictable agent behavior in demos
- Portfolio must be reproducible by anyone who clones the repo

### Considered Options

**Option 1: Different models per notebook based on task**
- Allows optimization per use case
- Makes cross-notebook comparison meaningless
- Confuses employers reviewing the series

**Option 2: OpenAI GPT-4o**
- High quality but requires paid API key
- Not reproducible for free-tier developers

**Option 3: Groq llama-3.3-70b-versatile at temperature=0**
- Free tier with high throughput
- Consistent across all notebooks from V5 onwards
- temperature=0 = deterministic = reliable demos

### Decision Outcome

**Chosen: Option 3 — Groq llama-3.3-70b-versatile, temperature=0**

Applied from V5 onwards. V1-V4 used llama-3.1-8b-instant as an
earlier choice before this standard was established.

### Consequences

- Good: free for anyone reproducing the portfolio
- Good: consistent quality baseline across V5-V8
- Good: temperature=0 means demos always produce same output
- Neutral: not the most powerful model available
- Bad: smaller context window than GPT-4o class models

---

## ADR-0008: FastMCP 3.4.2 as MCP Server Framework

- **Status:** Accepted
- **Applies from:** V6
- **Carried forward in:** V7

### Context and Problem Statement

Model Context Protocol requires a server-side framework to host tools
and expose them over a transport. Multiple Python MCP server libraries
exist. One must be chosen for the V6/V7 MCP architecture.

### Decision Drivers

- Must support streamable-http transport
- Must be actively maintained as of June 2026
- Must use @mcp.tool() decorator pattern for clean tool registration
- Must work inside Google Colab background thread

### Considered Options

**Option 1: Official MCP Python SDK (mcp package)**
- Lower-level — requires more boilerplate
- Less ergonomic tool registration
- Smaller ecosystem in June 2026

**Option 2: FastMCP 3.4.2**
- High-level framework built on top of official MCP Python SDK
- @mcp.tool() decorator for clean tool registration
- Built-in streamable-http transport support
- 9.9k GitHub stars at launch (March 2026)
- Actively maintained by the community

### Decision Outcome

**Chosen: Option 2 — FastMCP 3.4.2**

Installation: `pip install fastmcp==3.4.2`
Server creation: `mcp = FastMCP("my_tools")`
Tool registration: `@mcp.tool()`
Server start: `mcp.run(transport="streamable-http")`

### Consequences

- Good: clean @mcp.tool() decorator pattern
- Good: built-in streamable-http with no extra configuration
- Good: strong signal — MCP is fastest-growing skill in AI jobs 2026
- Neutral: pinned to 3.4.2 for reproducibility

---

## ADR-0009: wttr.in for Weather Data — No API Key Required

- **Status:** Accepted
- **Applies from:** V6
- **Carried forward in:** V7, V8

### Context and Problem Statement

V3 used a fake weather dictionary for pedagogical reasons. From V6
onwards, all tool data must be real and live. A weather data source
must be chosen that works in a portfolio context with zero cost.

### Decision Drivers

- Must require no API key — repo must be reproducible immediately
- Must return live data for any city in the world
- Must work from any Python environment via HTTP
- No rate limiting issues for demo-level traffic

### Considered Options

**Option 1: OpenWeatherMap API**
- Real data but requires API key registration
- Free tier available but adds setup friction for anyone reproducing

**Option 2: wttr.in**
- Free public weather service
- No API key required — HTTP GET only
- `?format=3` returns compact one-line output: `City: emoji temp`
- Works for any city globally
- Reliable uptime for portfolio traffic levels

### Decision Outcome

**Chosen: Option 2 — wttr.in**

Implementation:
```python
url = f"https://wttr.in/{city}?format=3"
response = requests.get(url, timeout=5)
```

### Consequences

- Good: zero setup for anyone reproducing the portfolio
- Good: real live data — not fake or hardcoded
- Good: timeout=5 prevents app hanging on slow network
- Bad: dependent on third-party free service — can go down
- Neutral: limited output format options with ?format=3

---

## ADR-0010: ToolNode Over Manual Tool Execution

- **Status:** Accepted
- **Applies from:** V3
- **Carried forward in:** V4, V5, V6, V7, V8

### Context and Problem Statement

When the agent LLM decides to call a tool, something must execute the
actual function and return the result. This can be done manually
(parse the tool_calls, call the function, format the result) or using
LangGraph's prebuilt ToolNode.

### Decision Drivers

- Manual execution requires error-prone parsing of tool_calls structure
- Must handle ToolMessage formatting correctly for LangGraph state
- Must handle errors gracefully so app does not crash

### Considered Options

**Option 1: Manual tool execution**
- Extract tool name and args from message.tool_calls
- Call function manually
- Format result as ToolMessage and append to state
- Handle errors manually

**Option 2: ToolNode from langgraph.prebuilt**
- Handles all parsing, execution, formatting automatically
- `handle_tool_errors=True` catches errors gracefully
- Single line: `tool_node = ToolNode(tools, handle_tool_errors=True)`

### Decision Outcome

**Chosen: Option 2 — ToolNode**

Used from V3 onwards consistently.

### Consequences

- Good: zero boilerplate for tool execution
- Good: handle_tool_errors=True means one bad input does not crash app
- Good: correct ToolMessage formatting guaranteed
- Good: consistent with LangGraph best practices

---

## ADR-0011: Direct Tool Calls Over MCP Server for V8 Streamlit Deployment

- **Status:** Accepted
- **Applies from:** V8

### Context and Problem Statement

V8 deploys the V7 agent as a public web application on Streamlit
Community Cloud. V6 and V7 used FastMCP 3.4.2 with streamable-http
running as a background thread in Google Colab. In a public Streamlit
Community Cloud deployment, background threads are unreliable and the
MCP server startup adds latency on cold starts. The free tier has a
1GB RAM cap and shared infrastructure.

### Decision Drivers

- Public demo must work reliably on first open for recruiters
- Cold start time must be minimized on free tier hosting
- V6 and V7 already prove MCP mastery — V8 has a different mission
- Demo reliability matters more than demonstrating an additional pattern

### Considered Options

**Option 1: Keep MCP server (FastMCP background thread)**
- Same architecture as V6/V7
- Pro: demonstrates MCP in a deployment context
- Con: background thread unreliable on Streamlit Community Cloud
- Con: adds 2+ second cold start latency minimum
- Con: port 8000 localhost dependency adds a failure point
- Con: MCP already proven in V6/V7 — no new signal added

**Option 2: Direct tool calls via @tool decorator**
- Simplified architecture — no server process required
- Pro: zero startup latency, no port dependency
- Pro: works reliably on Streamlit Community Cloud free tier
- Pro: cleaner codebase — easier for employers to read
- Con: MCP not demonstrated in V8 (mitigated: proven in V6/V7)

### Decision Outcome

**Chosen: Option 2 — direct tool calls**

MCP mastery is proven in V6 and V7, which live in the same repository.
V8's mission is public demo reliability for recruiters and hiring
managers — not additional skill demonstration.

Running FastMCP as a background thread in Streamlit Community Cloud
introduces startup race conditions and is an unnecessary complexity
for a public demo.

This is a deliberate senior engineering judgment: use the right tool
for the mission, not the most impressive-looking tool.

### Consequences

- Good: zero MCP server startup time
- Good: no localhost port dependency
- Good: works reliably on Streamlit Community Cloud free tier
- Good: simpler codebase — faster for employers to read in portfolio review
- Good: shorter cold start time improves recruiter first impression
- Neutral: MCP capability not shown in V8 — shown in V6/V7 same repo
- Bad: none for V8's stated mission
