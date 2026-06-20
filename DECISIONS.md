# Architecture Decision Records

This file documents every significant technical decision made across the V1-V7 LangGraph
agent series. Format: MADR 4.0.0 (Markdown Architectural Decision Records), the current
industry standard as of 2026.

Each record answers three questions: What was the problem? What options existed?
Why was this one chosen?

---

## Index

| ID | Decision | Status | Notebook |
|---|---|---|---|
| ADR-001 | Use AST-based evaluator instead of eval() for math | Accepted | V6, V7 |
| ADR-002 | Use streamable-http transport instead of stdio or SSE | Accepted | V6, V7 |
| ADR-003 | Use StateGraph instead of create_agent for V7 | Accepted | V7 |
| ADR-004 | Use dual memory layers: InMemorySaver + InMemoryStore | Accepted | V5, V7 |
| ADR-005 | Use UUID-keyed facts with two-layer dedup in V7 | Accepted | V7 |
| ADR-006 | Use Groq free tier over other LLM providers | Accepted | V2-V7 |
| ADR-007 | Use FastMCP over other MCP server frameworks | Accepted | V6, V7 |
| ADR-008 | Use wttr.in over paid weather APIs | Accepted | V6, V7 |
| ADR-009 | Use ToolNode instead of manual tool execution | Accepted | V7 |
| ADR-010 | Use progressive notebook series instead of one large project | Accepted | V1-V7 |

---

## ADR-001: Use AST-based evaluator instead of eval() for math tools

**Status:** Accepted
**Notebook:** V6 (first introduced), V7 (carried forward)
**Date:** June 2026

### Context

The calculator tool needs to evaluate math expressions that users type as strings,
such as `"347 * 28"` or `"100 / 4 + 50"`. The simplest Python approach is `eval(expression)`,
which evaluates any string as Python code and returns the result.

### Decision Drivers

- The calculator is exposed as an MCP tool — any user of the deployed agent can provide input
- Input from users cannot be trusted — it may be intentionally malicious or accidentally harmful
- The portfolio is intended for public deployment on HuggingFace Spaces in V8
- Technical interviewers specifically look for `eval()` on user input as a red flag

### Considered Options

**Option A: Python eval()**

```python
result = eval(expression)
```

Pros:
- One line of code
- Handles any valid Python math expression
- Supports complex expressions automatically

Cons:
- Executes ANY Python code, not just math
- A user typing `__import__('os').system('rm -rf /')` would run a shell command
- A user typing `open('/etc/passwd').read()` would read system files
- Known as one of the most dangerous patterns in Python security

**Option B: AST-based whitelist evaluator**

```python
SAFE_OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}

def safe_eval(expression: str):
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)

def _eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numbers allowed")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Operator not allowed: {op_type.__name__}")
        return SAFE_OPERATORS[op_type](_eval_node(node.left), _eval_node(node.right))
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Operator not allowed: {op_type.__name__}")
        return SAFE_OPERATORS[op_type](_eval_node(node.operand))
    else:
        raise ValueError(f"Not allowed: {type(node).__name__}")
```

Pros:
- Parses input as a syntax tree — never executes arbitrary code
- Any non-math node (function calls, imports, attribute access) is rejected at the AST level
- Attack input like `__import__('os')` becomes an `ast.Call` node, which hits the `else` branch and raises ValueError before anything runs
- Shows security awareness in a portfolio context

Cons:
- More code than eval()
- Does not support functions like sqrt(), sin(), log() — only basic arithmetic operators
- Complex nested expressions require careful recursive handling

**Option C: Third-party safe math library (e.g., asteval, numexpr)**

Pros:
- Handles more complex expressions
- Well-tested edge cases

Cons:
- Adds an external dependency
- Requires `pip install` — unnecessary for basic math
- Overkill for calculator + weather tool agent

### Decision Outcome

**Chosen: Option B — AST-based whitelist evaluator**

The cost of a security vulnerability in a public deployment outweighs the cost of writing
30 more lines of code. `eval()` on user input is explicitly listed in OWASP secure coding
guidelines as dangerous. For the scope of this calculator (arithmetic only), the AST
approach covers 100% of legitimate use cases. No third-party library needed.

### Consequences

Positive:
- Calculator is safe to expose publicly in V8 Streamlit deployment
- Demonstrates security awareness to technical interviewers
- No new dependencies required

Negative:
- Does not support math functions (sqrt, sin, cos) — acceptable for this use case
- Slightly more complex code than eval()

---

## ADR-002: Use streamable-http transport instead of stdio or SSE for MCP

**Status:** Accepted
**Notebook:** V6 (first introduced), V7 (carried forward)
**Date:** June 2026

### Context

FastMCP supports three transport options for communication between the MCP server and
the agent client: stdio, SSE (Server-Sent Events), and streamable-http. The environment
is Google Colab, which has specific constraints around process management and event loops.

### Decision Drivers

- All notebooks run on Google Colab — no local server environment available
- Colab runs a Jupyter kernel with its own event loop already active
- The MCP server must run simultaneously with the agent in the same notebook session
- Transport must support bidirectional communication for tool calls

### Considered Options

**Option A: stdio transport**

The MCP server communicates via standard input/output streams of a subprocess.

Pros:
- The original MCP transport — maximum compatibility
- No network port required
- Works in most standard environments

Cons:
- Requires launching the server as a separate subprocess
- In Colab, starting a subprocess that reads from stdin blocks the main kernel process
- Confirmed broken in Colab: the notebook hangs when stdio server is started
- No workaround available without changing the runtime environment

**Option B: SSE (Server-Sent Events)**

The MCP server sends events over an HTTP connection using the SSE protocol.

Pros:
- HTTP-based — works with threading
- Supported in older versions of langchain-mcp-adapters

Cons:
- Deprecated in FastMCP 3.x in favour of streamable-http
- langchain-mcp-adapters 0.2.0+ removed SSE support
- Would require pinning to older versions of both libraries — creates dependency conflicts

**Option C: streamable-http**

The MCP server runs as an HTTP server (via Uvicorn) on localhost:8000. The client
connects via HTTP requests. The server runs in a daemon thread.

```python
def run_server():
    mcp.run(transport="streamable-http")

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(2)
```

Pros:
- HTTP server decoupled from Colab's main event loop — no blocking
- Daemon thread means server stops automatically when notebook session ends
- Confirmed working: full JSON-RPC 2.0 handshake verified via Uvicorn logs
- Current recommended transport in FastMCP 3.4.2 documentation
- Supported by langchain-mcp-adapters 0.3.0

Cons:
- Occupies localhost port 8000 — conflicts if another service uses same port
- Requires 2-second sleep after thread start to let Uvicorn initialize
- Slightly more setup code than stdio

### Decision Outcome

**Chosen: Option C — streamable-http**

Options A and B are not viable in Colab. Option A blocks the kernel; Option B is deprecated.
streamable-http is the current standard transport in FastMCP 3.x and works reliably in Colab
via daemon threading. The port conflict risk is negligible in a notebook environment.

### Consequences

Positive:
- MCP server runs reliably alongside the agent in the same Colab session
- Uses current recommended transport — no deprecated patterns
- Full MCP JSON-RPC 2.0 protocol confirmed working

Negative:
- Port 8000 must be free — if another process uses it, server fails to bind
- Requires nest_asyncio.apply() to allow asyncio.run() nesting in Colab's event loop
- 2-second cold start wait required before client can connect

---

## ADR-003: Use custom StateGraph instead of create_agent for V7

**Status:** Accepted
**Notebook:** V7
**Date:** June 2026

### Context

V6 used `create_agent` from `langchain.agents` to build a simple ReAct agent with MCP
tools. V7 needs to add custom nodes for memory management (loading facts before the LLM
runs, saving facts after the LLM responds). The question is whether to extend the
existing `create_agent` approach or build a custom `StateGraph`.

### Decision Drivers

- V7 requires a `load_memories` node that runs before the LLM sees any message
- V7 requires a `save_memories` node that runs after the LLM gives its final answer
- These nodes must have access to the InMemoryStore at runtime
- The graph must be inspectable and explainable for portfolio purposes

### Considered Options

**Option A: create_agent with store and checkpointer parameters**

```python
from langchain.agents import create_agent

agent = create_agent(
    model=llm,
    tools=mcp_tools,
    checkpointer=InMemorySaver(),
    store=store,
)
```

Pros:
- Less code — internal ReAct loop handled automatically
- Both `checkpointer=` and `store=` parameters are supported directly
- Simpler for tool-only agents

Cons:
- Cannot inject custom nodes before or after the internal loop
- `load_memories` and `save_memories` cannot be added as explicit graph nodes
- Memory access pattern inside the agent is implicit — harder to explain and debug
- Less educational — hides the graph structure that V1-V6 built up progressively

**Option B: Custom StateGraph with explicit nodes**

```python
builder = StateGraph(AgentState)
builder.add_node("load_memories", load_memories)
builder.add_node("agent", call_agent)
builder.add_node("tools", ToolNode(mcp_tools))
builder.add_node("save_memories", save_memories)

builder.add_edge(START, "load_memories")
builder.add_edge("load_memories", "agent")
builder.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    "save_memories": "save_memories"
})
builder.add_edge("tools", "agent")
builder.add_edge("save_memories", END)

agent = builder.compile(checkpointer=InMemorySaver(), store=store)
```

Pros:
- Full control over node sequencing — memory nodes run exactly when intended
- Every node is explicit, named, and inspectable
- Builds directly on V5 (custom graph) and V4 (conditional routing) — pedagogical continuity
- Interviewer can see the exact execution order from the graph definition
- Easier to extend with additional nodes in future versions

Cons:
- More code than create_agent
- Must manually handle the agent loop (tools → agent → tools cycle)
- Must write a custom router function instead of using the prebuilt tools_condition

### Decision Outcome

**Chosen: Option B — custom StateGraph**

V7 is a capstone notebook. The goal is to demonstrate full understanding of graph
construction, not to use the shortest possible code path. `create_agent` hides the
internals that V1-V6 progressively taught. A custom StateGraph makes every decision
visible and explainable. The additional code is worth the transparency.

### Consequences

Positive:
- Memory lifecycle is fully explicit: load → think/act → save
- Graph structure can be drawn, explained, and extended
- Demonstrates progression from V1 basics to V7 production pattern
- Every node is independently testable

Negative:
- More code than create_agent approach
- Custom router required instead of prebuilt tools_condition
- Agent node must be defined inside the async build_agent function
  (because it needs the bound LLM, which needs the MCP tools, which require async)

---

## ADR-004: Use dual memory layers: InMemorySaver and InMemoryStore

**Status:** Accepted
**Notebook:** V5 (first introduced), V7 (carried forward)
**Date:** June 2026

### Context

The agent needs to remember two distinct things: what was said in the current conversation
(so it can maintain context across multiple turns), and what is known about the user
from all past conversations (so it can personalize responses across sessions).

### Decision Drivers

- Short-term context (same session) resets naturally when a new conversation begins
- Long-term user facts should survive indefinitely across all sessions
- Both are needed simultaneously — one does not replace the other
- All infrastructure must be free-tier

### Considered Options

**Option A: MemorySaver (InMemorySaver) only**

Uses conversation checkpointing scoped to `thread_id`. Each thread gets its own
conversation snapshot.

Pros:
- Built into LangGraph — no extra setup
- Handles multi-turn conversation automatically via message accumulation

Cons:
- Scoped only to thread_id — starts fresh every new conversation
- No cross-session user knowledge — agent forgets the user completely between chats
- Insufficient for a personalized assistant

**Option B: InMemoryStore only**

Uses a key-value store with namespace-based organization for persistent facts.

Pros:
- Persists across all conversations
- User-scoped via namespace tuple (namespace, user_id)

Cons:
- Does not handle conversation turn management — must manually track messages
- No automatic checkpointing — if agent crashes mid-conversation, state is lost
- Would need to rebuild message history management from scratch

**Option C: InMemorySaver + InMemoryStore (dual memory)**

```python
checkpointer = InMemorySaver()   # short-term: per thread_id
store = InMemoryStore()          # long-term: per user_id namespace

app = graph.compile(checkpointer=checkpointer, store=store)
```

Pros:
- InMemorySaver handles within-conversation turn management automatically
- InMemoryStore handles cross-conversation user fact persistence
- Each solves a different scope problem — they complement, not overlap
- LangGraph's compile() accepts both simultaneously with no conflicts

Cons:
- Two systems to understand and maintain
- Must be careful not to confuse thread_id scope with user_id scope
- Both store data in RAM — data is lost when the Colab runtime restarts

### Decision Outcome

**Chosen: Option C — dual memory with InMemorySaver + InMemoryStore**

Short-term and long-term memory solve fundamentally different problems. Using only one
means either losing cross-session knowledge (Option A) or rebuilding conversation
management from scratch (Option B). LangGraph is designed to support both simultaneously.
RAM-only storage is acceptable for a portfolio/demo context — production would use
persistent backends (PostgreSQL, Redis).

### Consequences

Positive:
- Agent maintains context within a conversation (InMemorySaver)
- Agent recalls user facts across separate conversations (InMemoryStore)
- Proven by Test 3 in V7: facts from thread_1 recalled in thread_2

Negative:
- All data is in-process RAM — Colab runtime restart clears all memory
- Two different scoping concepts (thread_id vs user_id) must be explained clearly
- Production upgrade path requires replacing both with persistent backends

---

## ADR-005: Use UUID-keyed facts with two-layer dedup for V7 long-term memory

**Status:** Accepted
**Notebook:** V7
**Date:** June 2026

### Context

V5 stores long-term facts as a single dict per user under one fixed key ("profile"),
using dict merge for deduplication: `{**old_facts, **new_facts}`. V7 uses
InMemoryStore differently — each fact is stored as a separate item with its own key.
This raises the question of how to prevent duplicate facts from accumulating across
multiple conversations.

### Decision Drivers

- V7 extracts multiple individual facts per conversation (not one fixed schema)
- Facts must survive across sessions but not duplicate across turns
- The save_memories node runs every turn — without dedup, same facts would multiply
- Observed in testing: without dedup, "user's name is Dani" saved twice in two turns

### Considered Options

**Option A: Fixed-key dict merge (V5 approach)**

```python
namespace = ("memories", user_id)
existing = store.get(namespace, "profile")
old_facts = existing.value if existing else {}
merged = {**old_facts, **extracted_facts}
store.put(namespace, "profile", merged)
```

Pros:
- Simple — one dict per user, same key always overwrites
- Dedup is structurally guaranteed — same key cannot exist twice
- Works well for a fixed schema (name, goal, location, etc.)

Cons:
- Requires a fixed schema — extracted facts must have consistent key names
- LLM does not always return consistent key names across extractions
- Free-form fact extraction ("user likes Python") does not map to a fixed key naturally

**Option B: UUID-keyed append with no dedup**

```python
fact_key = f"fact_{uuid.uuid4().hex[:8]}"
store.put(namespace, fact_key, {"fact": fact_text})
```

Pros:
- Flexible — any fact can be stored without a fixed schema
- Simple to implement

Cons:
- Each turn saves facts blindly — duplicates accumulate rapidly
- After 10 conversations: 10 copies of "user's name is Dani"
- Agent's system prompt grows with duplicate facts — wastes tokens, confuses LLM

**Option C: UUID-keyed append with two-layer dedup**

```python
# Layer 1: feed existing facts into extraction prompt (LLM-level soft filter)
existing_memories = store.search(namespace)
existing_facts_text = "\n".join([m.value.get("fact", "") for m in existing_memories])

extraction_prompt = f"""Extract NEW personal facts. Do NOT repeat:
{existing_facts_text}
Return only genuinely new facts as JSON."""

# Layer 2: exact string match in code (hard filter)
existing_set = {m.value.get("fact", "").lower().strip() for m in existing_memories}

for fact_obj in extracted_facts:
    fact_text = fact_obj.get("fact", "")
    if fact_text and fact_text.lower().strip() not in existing_set:
        store.put(namespace, f"fact_{uuid.uuid4().hex[:8]}", {"fact": fact_text})
```

Pros:
- Flexible schema — any free-form fact can be stored
- Layer 1 (LLM prompt) catches semantic duplicates: "user is Dani" vs "name is Dani"
- Layer 2 (code) catches exact repeats that Layer 1 misses
- Prevents token waste and LLM confusion from repeated facts

Cons:
- More code than Option A or B
- Layer 1 is a soft filter — LLM may still occasionally miss a paraphrase duplicate
- Embedding-based similarity (the production-grade approach) would be more robust,
  but requires a vector index — out of scope for this notebook

### Decision Outcome

**Chosen: Option C — UUID-keyed with two-layer dedup**

V7 uses free-form fact extraction where the LLM decides what to save. This rules out
Option A's fixed-key approach. Option B is demonstrably broken — confirmed in testing
where two identical facts were saved across two conversation turns. Option C catches
both exact duplicates (code layer) and semantic near-duplicates (LLM layer), with
acceptable complexity for a portfolio project.

### Consequences

Positive:
- Flexible fact storage without a fixed schema
- Duplicate facts confirmed eliminated in testing (⏭️ Skipped duplicate: shown in output)
- LLM receives clean, non-redundant context on every turn

Negative:
- Semantic dedup is imperfect — LLM may miss paraphrased duplicates
- Production upgrade: replace Layer 1 with embedding similarity search
  (e.g., cosine similarity on all-MiniLM-L6-v2 vectors)

---

## ADR-006: Use Groq free tier over other LLM providers

**Status:** Accepted
**Notebook:** V2-V7
**Date:** June 2026

### Context

Every notebook in this series requires a capable LLM for reasoning, tool calling, and
fact extraction. The constraint is zero budget — no paid API access.

### Decision Drivers

- Zero budget: no paid APIs allowed at any stage
- LLM must support tool calling (required from V3 onward)
- LLM must handle JSON instruction following for fact extraction (V5, V7)
- Consistent model across all notebooks for portfolio coherence

### Considered Options

**Option A: Groq free tier (llama-3.3-70b-versatile)**

Pros:
- Free tier with generous rate limits
- llama-3.3-70b-versatile: 70 billion parameters — strong instruction following
- Supports tool calling natively via LangChain integration
- `langchain-groq` provides first-class LangChain compatibility
- temperature=0 gives deterministic, consistent outputs

Cons:
- Rate limits on free tier — heavy testing can hit limits
- Hosted inference — data leaves local machine (acceptable for demo data)
- Model may be deprecated eventually — would require updating one line

**Option B: OpenAI GPT-4o / GPT-4o-mini**

Pros:
- Industry-standard model — widely recognized in interviews
- Excellent tool calling reliability

Cons:
- Paid API — violates the zero-budget constraint
- Cannot be used

**Option C: Ollama (local models)**

Pros:
- Completely free — runs on local hardware
- Data never leaves the machine

Cons:
- Colab's free GPU tier does not support running a separate Ollama server
- Would require Colab Pro (paid) or local machine with sufficient VRAM
- Violates the Colab-only constraint

**Option D: HuggingFace Inference API (free tier)**

Pros:
- Free tier available
- Large model selection

Cons:
- Free tier has very low rate limits — impractical for interactive testing
- Smaller models on free tier do not reliably support tool calling
- No `langchain-huggingface` equivalent for tool calling that matches Groq's reliability

### Decision Outcome

**Chosen: Option A — Groq free tier with llama-3.3-70b-versatile**

Groq is the only free provider that combines reliable tool calling, JSON instruction
following, and a model large enough (70B) to perform well on all tasks across V2-V7.
Model consistency across all notebooks presents a coherent portfolio. All notebooks use
`llama-3.3-70b-versatile` at `temperature=0`.

Note: V1-V4 were initially built with `llama-3.1-8b-instant`. These have been upgraded
to `llama-3.3-70b-versatile` during the June 2026 audit for consistency.

### Consequences

Positive:
- Zero cost across all 7 notebooks
- Consistent model makes cross-notebook comparisons valid
- temperature=0 ensures deterministic outputs for testing

Negative:
- Free tier rate limits can interrupt rapid testing sessions
- Hosted inference — cannot be used for sensitive/private data
- Dependency on Groq's service availability

---

## ADR-007: Use FastMCP over other MCP server frameworks

**Status:** Accepted
**Notebook:** V6 (first introduced), V7 (carried forward)
**Date:** June 2026

### Context

V6 introduces MCP (Model Context Protocol) tool integration. An MCP server is needed
to host the calculator and weather tools. Several Python MCP server frameworks exist.

### Decision Drivers

- Framework must support streamable-http transport (required for Colab — see ADR-002)
- Framework must integrate cleanly with langchain-mcp-adapters
- Must be actively maintained as of June 2026
- Must be installable via pip with no complex setup

### Considered Options

**Option A: FastMCP**

```python
from fastmcp import FastMCP

mcp = FastMCP("my_tools")

@mcp.tool()
def calculator(expression: str) -> str:
    """Calculate a math expression."""
    return str(safe_eval(expression))

mcp.run(transport="streamable-http")
```

Pros:
- Decorator-based API — extremely clean tool definition
- Version 3.4.2 (June 2026) — actively maintained
- First-class streamable-http support
- Confirmed working with langchain-mcp-adapters 0.3.0
- Tool docstrings automatically become MCP tool descriptions

Cons:
- Separate project from the official MCP Python SDK
- Version history is shorter than the official SDK

**Option B: Official MCP Python SDK (mcp library)**

Pros:
- Official Anthropic/MCP Foundation maintained package
- Reference implementation of the protocol

Cons:
- Lower-level API — requires more boilerplate per tool
- FastMCP was originally built on top of this SDK to simplify it
- Less ergonomic for quick tool definition in notebooks

**Option C: Custom HTTP server (Flask/FastAPI)**

Pros:
- Full control over request handling
- No MCP dependency

Cons:
- Does not implement MCP protocol — not compatible with langchain-mcp-adapters
- Would require implementing JSON-RPC 2.0 from scratch
- Defeats the purpose of demonstrating MCP in the portfolio

### Decision Outcome

**Chosen: Option A — FastMCP 3.4.2**

FastMCP's decorator-based API is the cleanest way to define MCP tools in a notebook
context. It handles the protocol details automatically, supports streamable-http natively,
and works reliably with langchain-mcp-adapters. The @mcp.tool() pattern is identical in
concept to @tool from LangChain — easier to explain to an interviewer as a progression.

### Consequences

Positive:
- Tool definition is one decorator + one function — minimal boilerplate
- Full MCP JSON-RPC 2.0 compliance confirmed via server logs
- Docstrings serve as tool descriptions automatically

Negative:
- Third-party library — not the official MCP SDK
- Version 3.x has breaking changes from 2.x — must pin or specify minimum version

---

## ADR-008: Use wttr.in over paid weather APIs

**Status:** Accepted
**Notebook:** V6 (first introduced), V7 (carried forward)
**Date:** June 2026

### Context

The weather tool needs real, live weather data for any city. Using hardcoded fake data
(as in V3/V4) is a portfolio quality problem — if an interviewer tests it with an
unlisted city, it returns "Weather not found." A real API is required.

### Decision Drivers

- Zero budget — no paid API keys
- Must return real, current weather data for any city worldwide
- Must require zero setup (no account creation, no API key)
- Must be reliable enough for demo purposes

### Considered Options

**Option A: OpenWeatherMap API**

Pros:
- Industry-standard weather API
- Comprehensive data (temperature, humidity, wind, forecast)
- Widely recognized in job interviews

Cons:
- Requires account creation and API key even for free tier
- Free tier requires storing another secret alongside Groq key
- Adds setup friction for anyone trying to run the notebook

**Option B: WeatherAPI.com**

Pros:
- Generous free tier
- Good data quality

Cons:
- Requires API key — same problem as Option A
- One more credential to manage and expose risk

**Option C: wttr.in (no key required)**

```python
url = f"https://wttr.in/{city}?format=3"
response = requests.get(url, timeout=5)
# format=3 returns: "Kozhikode: ⛅ +31°C"
```

Pros:
- Completely free, no account, no API key
- Returns real current weather for any city worldwide
- `?format=3` gives compact single-line output — perfect for LLM consumption
- timeout=5 prevents hanging if service is slow
- status_code==200 check ensures clean error handling

Cons:
- No SLA — service could be down without notice
- Less data than paid APIs (temperature + condition only, not full forecast)
- Not appropriate for production use — demo/portfolio only

**Option D: Hardcoded fake data (V3/V4 approach)**

```python
weather = {"kerala": "32°C sunny", "delhi": "41°C hot", "mumbai": "28°C humid"}
return weather.get(city.lower(), "Weather not found for that city")
```

Pros:
- No network call needed
- Always returns instantly

Cons:
- Only 3 cities work — everything else returns "Weather not found"
- Clearly fake to any interviewer who tests it
- Violates the real data rule established from V6 onward

### Decision Outcome

**Chosen: Option C — wttr.in**

wttr.in is the only option that provides real weather data with zero API key requirement
and zero account setup. The data quality is sufficient for a demo agent — temperature
and condition are enough for the weather tool's purpose. The lack of SLA is acceptable
in a portfolio context. Any notebook user can run it immediately without setup.

### Consequences

Positive:
- Real live weather data for any city — confirmed working for Tokyo, Kozhikode
- Zero setup friction — notebook runs without any additional secrets
- Permanent data rule satisfied: zero hardcoded responses in MCP tools

Negative:
- wttr.in has no uptime guarantee — occasional failures possible
- timeout=5 means network issues cause tool to fail after 5 seconds
- Not suitable for production — would require a paid API with SLA

---

## ADR-009: Use prebuilt ToolNode instead of manual tool execution

**Status:** Accepted
**Notebook:** V7
**Date:** June 2026

### Context

When the LLM in V7's agent node returns a response with tool_calls, something must
execute those tool calls and return the results as ToolMessages. This can be done
manually or using LangGraph's prebuilt ToolNode.

### Decision Drivers

- Tool execution must handle both sync and async tools correctly
- Error handling for failed tool calls must be graceful
- Code should be minimal and maintainable

### Considered Options

**Option A: Manual tool execution**

```python
def execute_tools(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    tool_results = []
    for tool_call in last_message.tool_calls:
        tool = next(t for t in tools if t.name == tool_call["name"])
        result = tool.invoke(tool_call["args"])
        tool_results.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
    return {"messages": tool_results}
```

Pros:
- Full control over execution logic
- Can add custom pre/post processing per tool call

Cons:
- Must manually match tool names to tool objects
- Must manually construct ToolMessage with correct tool_call_id
- Must handle async tools separately
- Error handling must be written manually — easy to get wrong

**Option B: Prebuilt ToolNode**

```python
from langgraph.prebuilt import ToolNode

tools_node = ToolNode(tools)
builder.add_node("tools", tools_node)
```

Pros:
- One line to create
- Automatically reads tool_calls from last AI message
- Automatically constructs ToolMessage with correct ID
- Handles both sync and async tools
- handle_tool_errors parameter provides built-in error handling
- Same component used in official LangGraph documentation and examples

Cons:
- Less visible — tool execution is a black box
- Cannot easily add custom logic per tool call without subclassing

### Decision Outcome

**Chosen: Option B — prebuilt ToolNode**

The manual approach requires correctly implementing the ToolMessage ID matching and
async handling — both of which ToolNode already does correctly. In a notebook context
with MCP tools (which are async under the hood), ToolNode's async handling is important.
The transparency trade-off is acceptable because the router (should_continue) and the
nodes before/after are all fully visible.

### Consequences

Positive:
- Tool execution is correct out of the box
- Handles MCP tools' async nature automatically
- Consistent with official LangGraph documentation patterns

Negative:
- Tool execution internals are not visible in the notebook
- Cannot easily inspect what happens between tool call and tool result without logging

---

## ADR-010: Use progressive notebook series instead of one large project

**Status:** Accepted
**Notebook:** V1-V7 (series design decision)
**Date:** June 2026

### Context

The portfolio could have been structured as one large, comprehensive notebook containing
all features (graph basics, LLM node, tools, routing, memory, MCP). Alternatively, it
could be built as a progressive series where each notebook adds exactly one new concept.

### Decision Drivers

- Portfolio must be explainable to both HR (non-technical) and engineers (technical)
- Each concept should be demonstrable independently — debugging is easier in isolation
- The learning process itself is part of the portfolio story

### Considered Options

**Option A: One large notebook with all features**

Pros:
- Single file to share or demo
- All code in one place

Cons:
- Any bug affects the entire system — harder to isolate
- An HR reviewer sees a 500-line notebook with no context for what each part does
- New concepts cannot be introduced incrementally — everything is presented at once
- Harder to explain in an interview: "where does the memory start?" has no clean answer

**Option B: Progressive notebook series (V1-V7)**

Each notebook builds on the previous one by adding exactly one concept:
- V1: graph mechanics (no LLM)
- V2: adds LLM + short-term memory
- V3: adds tool calling
- V4: adds conditional routing
- V5: adds long-term memory
- V6: adds MCP (replaces local tools with server-based tools)
- V7: combines everything into one production agent

Pros:
- Each notebook is independently runnable and testable
- Concept isolation makes debugging straightforward
- Reviewers can open any notebook and understand exactly what it demonstrates
- Tells a clear progression story: "I built from zero to production in 7 steps"
- Cell 0 in each notebook explains what that specific notebook teaches

Cons:
- More files to maintain — changes to a shared pattern (e.g., LLM upgrade) must be
  applied across all notebooks
- Some code is repeated across notebooks (LLM setup, API key loading)

### Decision Outcome

**Chosen: Option B — progressive series**

A portfolio that tells a story is more memorable and easier to evaluate than one large
file. The ability to say "here is the exact moment I added memory, here is the exact
moment I added MCP tools" is a demonstration of controlled engineering, not just working
code. The maintenance overhead (applying changes across notebooks) is real but manageable.

### Consequences

Positive:
- Clear narrative from V1 to V7 — easy to walk an interviewer through
- Each notebook independently demonstrates one concept
- Bugs are isolated to the notebook where the concept lives

Negative:
- LLM model upgrade (llama-3.1-8b-instant → llama-3.3-70b-versatile) had to be
  applied across V2-V4 during June 2026 audit — multi-file maintenance cost confirmed
- Cell 0 intro markdown had to be added to all notebooks after the rule was established

---

*Format: MADR 4.0.0 — Markdown Architectural Decision Records*
*Last updated: June 2026*
