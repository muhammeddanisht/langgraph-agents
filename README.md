# LangGraph Agent Series — V1 to V8

> Self-taught AI engineer. Zero coding background. BBA graduate.
> Built 8 production-grade LangGraph agents from scratch — each one
> more advanced than the last. This repository is proof of that journey.

---

## Live Demos

| Project | Link | Status |
|---------|------|--------|
| LangGraph Agent V8 | [danish-ai-agent.streamlit.app](https://danish-ai-agent.streamlit.app) | Live |

---

## What This Repository Is

A progressive series of 8 LangGraph agents — each notebook building
on the previous one. Designed to show real skill growth to employers,
not just completed exercises.

Every major design decision is documented in
[DECISIONS.md](DECISIONS.md) using MADR 4.0.0 format. Every notebook
opens with a Cell 0 markdown explaining what it is, its architecture,
and how it relates to the other notebooks.

---

## The Series at a Glance

| Version | File | What It Builds | Key Concepts |
|---------|------|---------------|--------------|
| V1 | `langgraph_v1_basics.ipynb` | Pure graph — no LLM | StateGraph, TypedDict state, nodes, edges, START, END |
| V2 | `langgraph_v2_llm_node.ipynb` | LLM node + conversation memory | MessagesState, ChatGroq, InMemorySaver, thread_id |
| V3 | `langgraph_v3_tools.ipynb` | Tool calling agent | @tool decorator, ToolNode, tools_condition, bind_tools |
| V4 | `langgraph_v4_conditional_edges.ipynb` | Multi-agent routing | Conditional edges, classifier node, specialist agents, Literal router |
| V5 | `langgraph_v5_memory.ipynb` | Dual memory system | InMemorySaver (short-term) + InMemoryStore (long-term), user_id |
| V6 | `langgraph_v6_mcp.ipynb` | MCP agent | FastMCP 3.4.2, langchain-mcp-adapters 0.3.0, streamable-http transport |
| V7 | `langgraph_v7_production.ipynb` | Production agent | V5 dual memory + V6 MCP tools combined in one StateGraph |
| **V8** | `app.py` | **Deployed web app** | **Streamlit, st.cache_resource, UUID session isolation, public deployment** |

---

## V1 — Graph Basics

**What it does:** Demonstrates pure LangGraph graph mechanics with
no LLM involved. Two chained nodes: `greet_user` then `shout`.

**Architecture:**
```
START -> greet_user -> shout -> END
```

**Key concept:** State as a shared bag that every node reads and updates.
The robot carries a TypedDict state dict through every room.

**Notebook:** `langgraph_v1_basics.ipynb`

---

## V2 — LLM Node + Memory

**What it does:** Adds a real LLM brain (Groq llama) and conversation
memory using InMemorySaver. Multi-turn recall confirmed — the agent
remembers what was said earlier in the same thread.

**Architecture:**
```
START -> thinking_node -> END
         (ChatGroq + InMemorySaver)
```

**Key concept:** thread_id as conversation locker. Same thread_id =
same memory. Different thread_id = fresh conversation.

**Notebook:** `langgraph_v2_llm_node.ipynb`

---

## V3 — Tool Calling

**What it does:** Adds two tools — a calculator and a weather lookup.
The agent decides on its own when to call a tool vs answer directly.

**Architecture:**
```
START -> agent -> tools -> agent -> END
              (conditional: tool call?)
```

**Key concept:** tools_condition prebuilt router — checks if the LLM's
last message contains tool_calls. If yes, go to tools. If no, go to END.

**Note:** Weather data in V3 uses a fake dictionary intentionally — V3
is a pedagogical stepping stone. Real data arrives in V6 via MCP.

**Notebook:** `langgraph_v3_tools.ipynb`

---

## V4 — Multi-Agent Routing

**What it does:** A classifier node reads the user message, categorizes
it (math / weather / general), then routes to one of three specialist
agents via conditional edges.

**Architecture:**
```
START -> classifier -> math_agent    -> tools -> math_agent    -> END
                    -> weather_agent -> tools -> weather_agent -> END
                    -> general_agent                           -> END
```

**Key concept:** add_conditional_edges with a path map. Each specialist
gets its own system prompt — context engineering for each use case.

**New state field:** `category: str` added to AgentState via
MessagesState subclass.

**Notebook:** `langgraph_v4_conditional_edges.ipynb`

---

## V5 — Dual Memory System

**What it does:** Two layers of memory in one agent. Short-term memory
(InMemorySaver) tracks the conversation thread. Long-term memory
(InMemoryStore) stores user facts across different sessions.

**Architecture:**
```
START -> call_model -> tools    -> call_model -> save_memory -> END
                    -> save_memory (if no tool call)         -> END
```

**Memory scopes:**
```
InMemorySaver  ->  keyed by thread_id  ->  conversation history
InMemoryStore  ->  keyed by user_id    ->  user facts (name, city, goal)
```

**Key concept:** Fixed-key dict merge for deduplication:
`{**old_facts, **new_facts}` — new value wins on same key, old facts
preserved on different keys.

**LLM upgraded:** llama-3.3-70b-versatile at temperature=0 from V5
onwards. Consistent across all remaining notebooks.

**Notebook:** `langgraph_v5_memory.ipynb`

---

## V6 — MCP Agent

**What it does:** Demonstrates Model Context Protocol — tools now live
on a separate FastMCP server, not hardcoded in the agent. The agent
connects to the server, discovers tools at runtime, and uses them.

**Architecture:**
```
FastMCP Server (background thread, port 8000)
    - calculator tool (AST-based, no eval)
    - get_weather tool (wttr.in, real live data)

LangGraph Agent
    -> MultiServerMCPClient (connects via streamable-http)
    -> gets tools list at runtime
    -> invokes tools over HTTP
```

**Transport:** streamable-http chosen over stdio/SSE for Colab
stability. stdio requires subprocess management. SSE had connection
reliability issues in testing.

**Security decision:** eval() replaced with AST-based safe evaluator.
SAFE_OPERATORS whitelist — only add, subtract, multiply, divide allowed.
Anything else raises ValueError immediately.

**Notebook:** `langgraph_v6_mcp.ipynb`

---

## V7 — Production Agent

**What it does:** Combines V5 dual memory with V6 MCP tools into one
production-grade StateGraph. The most complete notebook in the series —
4 nodes, two memory scopes, real tool data, and memory deduplication.

**Architecture:**
```
START
  -> load_memories  (reads InMemoryStore for this user_id)
  -> agent          (llm_with_tools, decides action)
  -> tools          (MCP tools via ToolNode)    [if tool call]
  -> agent          (processes tool result)
  -> save_memories  (extracts facts, writes to InMemoryStore)
  -> END
```

**Key decisions:**
- StateGraph over create_agent — full control over node flow
- create_agent from langchain.agents — NOT deprecated create_react_agent
- UUID-keyed append for memory entries (not fixed-key)
- Two-layer dedup: LLM prompt-level + code-level exact-string set check
- nest_asyncio.apply() for Colab async compatibility

**Verified tests:** calculator (real math), live weather, cross-thread
long-term memory recall — all 3 passed.

**Notebook:** `langgraph_v7_production.ipynb`

---

## V8 — Streamlit Deployment

**What it does:** Takes the V7 agent and deploys it as a public web
application on Streamlit Community Cloud. Anyone with the link can use
it immediately — no setup required.

**Live demo:** [danish-ai-agent.streamlit.app](https://danish-ai-agent.streamlit.app)

**Architecture:**
```
Browser visitor (any device, any location)
      |
      v
Streamlit Community Cloud (free tier, GitHub-connected)
      |
      v
app.py (st.cache_resource builds agent ONCE per server instance)
      |
      v
UUID per session (st.session_state — prevents memory leakage)
      |
      v
4-node StateGraph (same as V7):
  load_memories -> agent -> tools -> save_memories
      |
      v
st.status (live tool call progress shown to user)
      |
      v
st.write (final response displayed in chat bubble)
```

**Key engineering decisions for V8:**
- Direct tool calls instead of MCP server (demo reliability > skill-flex)
- st.cache_resource — builds LangGraph agent once per server, not per request
- UUID per visitor in st.session_state — each visitor gets isolated memory namespace
- .streamlit/secrets.toml locally, Streamlit Cloud secrets panel in production

**Files:**
```
app.py              - entire Streamlit application
requirements.txt    - dependencies for Streamlit Cloud
.gitignore          - excludes secrets.toml from GitHub
```

---

## V8 Full Tech Stack

| Layer | Technology | Version / Detail |
|-------|-----------|-----------------|
| Agent framework | LangGraph | 1.1.9 |
| LLM | ChatGroq llama-3.3-70b-versatile | temperature=0 |
| Short-term memory | LangGraph InMemorySaver | per thread_id |
| Long-term memory | LangGraph InMemoryStore | per user_id (UUID) |
| MCP server (V6/V7) | FastMCP | 3.4.2 |
| MCP client (V6/V7) | langchain-mcp-adapters | 0.3.0 |
| Calculator security | Python ast module | AST + SAFE_OPERATORS whitelist |
| Weather data | wttr.in | free, no API key required |
| Web framework | Streamlit | latest |
| Deployment | Streamlit Community Cloud | free tier |
| Session isolation | Python uuid module | uuid4 per visitor |

---

## Architecture Decisions

All major design choices are documented in
[DECISIONS.md](DECISIONS.md) using MADR 4.0.0 format.

11 ADRs covering:
- Security (AST over eval)
- Transport (streamable-http over stdio/SSE)
- Memory (dual scope design)
- Deduplication strategy
- LLM consistency across series
- MCP framework choice
- Weather data source
- Tool execution approach
- Graph architecture
- Deployment simplification

---

## Run V8 Locally

```bash
git clone https://github.com/muhammeddanisht/langgraph-agents
cd langgraph-agents
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

Run:
```bash
python -m streamlit run app.py
```

Get a free Groq API key at [console.groq.com](https://console.groq.com)

---

## Run Notebooks (V1-V7)

All notebooks run in Google Colab. Open any `.ipynb` file in GitHub
and click `Open in Colab`. Add your Groq API key to Colab Secrets
under the name `GROQ_API_KEY`.

---

## Contact

**Muhammed Danish T.** — AI Engineer

Self-taught. BBA background. Building production AI systems.
Targeting AI Engineer, AI Automation Engineer, and Agentic GenAI
Engineer roles.

- GitHub: [github.com/muhammeddanisht](https://github.com/muhammeddanisht)
- LinkedIn: [linkedin.com/in/muhammeddanisht](https://linkedin.com/in/muhammeddanisht)
- HuggingFace: [huggingface.co/danish811](https://huggingface.co/danish811)
- Live Agent: [danish-ai-agent.streamlit.app](https://danish-ai-agent.streamlit.app)
