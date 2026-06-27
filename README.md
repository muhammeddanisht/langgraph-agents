## 🚀 Live Demo
👉 [Click here to use the agent](https://danish-ai-agent.streamlit.app)

# LangGraph Agent Series — V1 to V7

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1.9-FF6B35?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.4.2-00C7B7?style=flat-square)](https://github.com/jlowin/fastmcp)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-F55036?style=flat-square)](https://groq.com)
[![HuggingFace](https://img.shields.io/badge/Live_Demo-HuggingFace-FFD21F?style=flat-square&logo=huggingface&logoColor=black)](https://huggingface.co/spaces/danish811/rag-chatbot-v3)
[![Open In Colab](https://img.shields.io/badge/Open%20in-Colab-F9AB00?style=flat-square&logo=googlecolab&logoColor=white)](https://colab.research.google.com)

A 7-notebook series building a production AI agent from scratch — starting with zero code knowledge and ending with a complete agent that has real tools, dual-layer memory, and live API integrations. Each notebook adds exactly one new concept. Everything runs free on Google Colab.

---

## Live Demo

| Project | Link | Stack |
|---|---|---|
| RAG Chatbot v3 | [Try it live](https://huggingface.co/spaces/danish811/rag-chatbot-v3) | Streamlit · LangChain · FAISS · Groq |

---

## The Series at a Glance

| Notebook | Title | What it adds | Tests passed |
|---|---|---|---|
| V1 | Graph Basics | Nodes, edges, state, compile | Text transforms through chained nodes |
| V2 | LLM Node + Memory | Real LLM in graph, short-term memory | Agent recalls previous question in same thread |
| V3 | Tool Calling | @tool, ToolNode, ReAct loop | Calculator + weather both called correctly |
| V4 | Conditional Routing | Classifier, multi-agent, custom router | 3 paths routed correctly by topic |
| V5 | Dual Memory | Short-term + long-term memory | Facts recalled across separate threads |
| V6 | MCP Tools | FastMCP server, real API calls | Live math + live weather via MCP protocol |
| **V7** | **Complete Agent** | **All combined: memory + MCP** | **Memory + tools working together** |

---

## V1 — Graph Basics

**What it teaches:** How LangGraph graphs actually work — before any LLM or tools. Pure graph mechanics.

**The concept:** A graph is a factory. You define rooms (nodes), roads between rooms (edges), and a bag the robot carries through the factory (state). The robot starts at `START`, visits rooms in order, and exits at `END`.

**Architecture:**
```
START → greet_user → shout → END

State: { user_question: str }
greet_user: prepends "Hello! You asked: " to the text
shout:      converts full string to UPPERCASE
```

**Key code:**
```python
class State(TypedDict):
    user_question: str              # one pocket in the bag

graph = StateGraph(State)
graph.add_node("greet_user", greet_user)
graph.add_node("shout", shout)
graph.add_edge(START, "greet_user")
graph.add_edge("greet_user", "shout")
graph.add_edge("shout", END)
app = graph.compile()
```

**Test result:**
```
Input:  "Book ticket to talkies"
Output: "HELLO! YOU ASKED: BOOK TICKET TO TALKIES"
```

**What you learn:** `StateGraph`, `TypedDict`, `add_node`, `add_edge`, `compile`, `invoke`, how state flows through nodes.

---

## V2 — LLM Node + Short-Term Memory

**What it teaches:** How to plug a real LLM into a graph node, and how short-term memory (same conversation) works via `MemorySaver`.

**The concept:** V1's graph had no brain — just text transformations. V2 adds Groq's LLM as the node's engine. `MessagesState` replaces the basic `TypedDict` — it holds a full conversation list, not just one string. `MemorySaver` saves the full state after each node runs, scoped to a `thread_id`. Same thread = same memory locker.

**Architecture:**
```
START → thinking_node → END

State: MessagesState (full chat history list)
thinking_node: sends full chat history to LLM, appends reply
MemorySaver: saves state per thread_id after every run
```

**Key code:**
```python
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

def thinking_node(state: MessagesState):
    response = llm.invoke(state["messages"])  # send full history to LLM
    return {"messages": response}             # append reply to history

memory = MemorySaver()
app = graph.compile(checkpointer=memory)

# thread_id = which conversation locker
config = {"configurable": {"thread_id": "chat1"}}
```

**Tests passed:**
```
Turn 1 — "What is AI?" → LLM gives full answer
Turn 2 — "What did I just ask you?" → "You just asked me 'What is AI?'"
(Proof: agent remembers across turns in same thread)
```

**What you learn:** `MessagesState`, `ChatGroq`, `HumanMessage`, `MemorySaver`, `thread_id`, how conversation history is stored and replayed.

---

## V3 — Tool Calling

**What it teaches:** How to give the LLM tools it can call — and how the agent loop (think → call tool → get result → think again) works.

**The concept:** The LLM alone can only generate text. Tools give it the ability to act. `bind_tools()` tells the LLM "these workers exist, you can request them." When LLM responds with a tool call instead of text, `ToolNode` intercepts it, runs the actual function, and returns the result. `tools_condition` is the prebuilt traffic signal — routes to `ToolNode` if there's a tool call, routes to `END` if there isn't.

**Architecture:**
```
START → agent → [tools_condition?] → tools → agent (loop)
                        |
                        → END (when LLM gives final answer)

Tools: calculator (a, b, operation) + get_weather (city)
ToolNode: executes whichever tool LLM requests
tools_condition: prebuilt router — checks last message for tool_calls
```

**Key code:**
```python
@tool
def calculator(a: float, b: float, operation: str) -> float:
    """Do math. operation must be: add, subtract, multiply, divide."""
    if operation == "multiply": return a * b
    # ... other operations

llm_with_tools = llm.bind_tools(tools)   # LLM now knows about tools
tool_node = ToolNode(tools, handle_tool_errors=True)

graph.add_conditional_edges("agent", tools_condition)  # prebuilt router
graph.add_edge("tools", "agent")                       # loop back after tool use
```

**Tests passed:**
```
"What is 25 multiplied by 4?" → calculator called → 100
"What is the weather in Kerala?"  → get_weather called → "32 degrees C sunny"
```

**What you learn:** `@tool`, `bind_tools`, `ToolNode`, `tools_condition`, `handle_tool_errors`, the ReAct agent loop pattern.

---

## V4 — Conditional Routing (Multi-Agent)

**What it teaches:** How to build a classifier that reads the user's intent and routes them to different specialist agents — each expert in one domain.

**The concept:** A single agent handles everything in V3. In V4, we add a `classifier_node` that reads the message first, tags it with a category (`math`, `weather`, `general`), then a custom router function sends it to the right specialist. Each specialist only handles its domain. This is the foundation of multi-agent systems.

**Architecture:**
```
START
  → classifier (reads message, sets category field)
  → router (reads category, picks road)
      ├── "math"    → math_agent    → [tools?] → tools → math_agent
      ├── "weather" → weather_agent → [tools?] → tools → weather_agent
      └── "general" → general_agent → END

State: AgentState (extends MessagesState + adds category: str field)
```

**Key code:**
```python
class AgentState(MessagesState):
    category: str    # extra pocket: which specialist handles this?

def classifier_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1].content.lower()
    if any(w in last_msg for w in ["multiply", "calculate", "times"]):
        return {"category": "math"}
    elif any(w in last_msg for w in ["weather", "temperature"]):
        return {"category": "weather"}
    return {"category": "general"}

def router(state: AgentState) -> str:
    return state["category"]   # returns node name to route to

graph.add_conditional_edges("classifier", router, {
    "math":    "math_agent",
    "weather": "weather_agent",
    "general": "general_agent"
})
```

**Tests passed:**
```
"What is 25 multiplied by 4?"   → routed to math_agent    → 100
"What is the weather in Kerala?" → routed to weather_agent → weather answer
"Who is Virat Kohli?"            → routed to general_agent → cricket legend
```

**What you learn:** Custom state fields, `add_conditional_edges` with dict mapping, classifier nodes, specialist agents, `route_after_tools` pattern for returning to the right specialist after tool execution.

---

## V5 — Dual Memory Agent

**What it teaches:** The difference between short-term memory (within one conversation) and long-term memory (across all conversations) — and how to extract and store facts about a user permanently.

**The concept:** `MemorySaver` from V2 only remembers within one thread. Close the chat, open a new one — it forgets everything. `InMemoryStore` is different: facts are stored under a `(namespace, user_id)` key, persist across all threads, and can be read at the start of any future conversation. The agent uses an LLM to extract facts from the conversation ("what did the user tell me that's worth remembering?") and saves them.

**Architecture:**
```
START → call_model → [custom router]
                          |
          tool_call? → tools → call_model (loop)
                          |
          final answer? → save_memory → END

InMemorySaver: saves conversation per thread_id (short-term)
InMemoryStore: saves user facts per user_id namespace (long-term)
save_memory: LLM extracts facts → dict merge → store.put()
```

**Key code:**
```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

checkpointer = InMemorySaver()    # short-term: per thread_id
store = InMemoryStore()           # long-term: per user_id

# Read facts for this user
namespace = ("memories", user_id)
memories = store.search(namespace)

# Save new facts (dict merge = deduplication)
old_facts = existing.value if existing else {}
merged = {**old_facts, **new_facts}    # same key overwrites, no duplicates
store.put(namespace, "profile", merged)

# Compile with both memory layers
app = graph.compile(checkpointer=checkpointer, store=store)
```

**Tests passed:**
```
Thread 1 — "My name is Danish and I want an AI job"
          → save_memory extracts: {name: "Danish", goal: "AI job"}

Thread 2 (new thread, short-term memory reset) —
          → load_memory reads: {name: "Danish", goal: "AI job"}
          → "What is my name?" → "Your name is Danish"
(Proof: long-term memory survives thread change)
```

**What you learn:** `InMemoryStore`, `store.put/search/get`, namespace design, LLM-based fact extraction, dict merge deduplication strategy, custom router that separates tool calls from memory-save calls.

---

## V6 — MCP Agent (Real Tools via Model Context Protocol)

**What it teaches:** How to connect a LangGraph agent to tools running on a real MCP server — the open industry standard for AI tool integration.

**The concept:** V3's tools were Python functions in the same file as the agent. MCP (Model Context Protocol) separates tools into their own server. The agent connects to the server over HTTP, discovers available tools, and calls them through a standardized JSON-RPC 2.0 protocol. This is how production AI systems are built — tools can be on different machines, different languages, different teams.

**Architecture:**
```
FastMCP Server (localhost:8000/mcp) ← daemon thread
      |
      | streamable-http transport
      |
MultiServerMCPClient (connects, discovers tools)
      |
create_agent (ReAct loop with MCP tools)
      |
Groq LLM (llama-3.3-70b-versatile)

Tools:
- calculator  → AST-safe evaluator (no eval())
- get_weather → wttr.in live API (real data, no API key)
```

**Key code:**
```python
# Start FastMCP server in background thread (Colab-compatible)
def run_server():
    mcp.run(transport="streamable-http")   # NOT stdio (breaks Colab)

threading.Thread(target=run_server, daemon=True).start()
time.sleep(2)

# Connect and get tools
client = MultiServerMCPClient({
    "my_tools": {"transport": "http", "url": "http://localhost:8000/mcp"}
})
tools = await client.get_tools()

# Safe calculator — rejects any non-math input
def safe_eval(expression: str):
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)   # walks AST, rejects non-math nodes
```

**Tests passed:**
```
"What is 347 multiplied by 28?"  → calculator called → 9716 (real AST math)
"What is the weather in Tokyo?"  → get_weather called → live wttr.in data
"What is the weather in Kozhikode?" → get_weather called → live wttr.in data
Server logs confirm: full MCP JSON-RPC 2.0 handshake (POST/GET/POST/DELETE)
```

**What you learn:** FastMCP, Model Context Protocol, streamable-http transport, `MultiServerMCPClient`, `nest_asyncio` for Colab async fix, daemon threading, AST-based safe math evaluation.

---

## V7 — Complete Production Agent (Capstone)

**What it teaches:** How to combine everything — dual memory from V5 and real MCP tools from V6 — into one complete, production-grade agent using a custom `StateGraph` with four explicit nodes.

**The concept:** V5 had brain (memory) but no hands. V6 had hands (tools) but no memory. V7 is the full system. A custom 4-node graph controls the entire lifecycle: load facts at start, think and act in the middle, save new facts at the end. `ToolNode` handles MCP tool execution. A custom router decides whether to loop back for more tool calls or proceed to memory saving.

**Architecture:**
```
State: { messages, user_id, memory_context }

START
  |
  v
load_memories  -- reads InMemoryStore for this user_id
  |                puts facts into memory_context field
  v
agent          -- LLM sees: memory_context + chat history + tools
  |
  |-- has tool_calls? --YES--> tools (ToolNode: MCP calculator/weather)
  |                                    |
  |                             loops back to agent
  |
  |-- no tool_calls ---------> save_memories
                                    |
                                    |-- LLM extracts new facts
                                    |-- 2-layer dedup check
                                    |-- store.put() for each new fact
                                    v
                                   END

Memory layer 1: InMemorySaver  -- thread_id scoped  (short-term)
Memory layer 2: InMemoryStore  -- user_id scoped    (long-term)
MCP server:     FastMCP 3.4.2  -- calculator + live weather
```

**Key code:**
```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    memory_context: str

# 4 explicit nodes
builder.add_node("load_memories", load_memories)
builder.add_node("agent", call_agent)
builder.add_node("tools", ToolNode(mcp_tools))
builder.add_node("save_memories", save_memories)

# Custom router: tools or save?
def should_continue(state):
    if state["messages"][-1].tool_calls:
        return "tools"
    return "save_memories"

# Compile with both memory layers
agent = builder.compile(checkpointer=InMemorySaver(), store=InMemoryStore())
```

**Tests passed:**
```
Test 1: "What is 347 multiplied by 28?" → MCP calculator → 9716
Test 2: "What is the weather in Kozhikode?" → MCP weather → live wttr.in data
Test 3: Thread 1: "My name is Dani and I am learning AI engineering"
           → saved: "user's name is Dani", "user is learning AI engineering"
        Thread 2 (new thread): "What is my name and what am I learning?"
           → recalled both facts from InMemoryStore across thread boundary
```

---

## Key Engineering Decisions

### 1. AST-based calculator — no eval()
All calculator tools use `ast.parse()` + a whitelist of allowed operators. Python's `eval()` executes any code passed to it — a user could pass a shell command disguised as a math expression and compromise the system. The AST approach parses input as a syntax tree, walks each node, and rejects anything that is not a number or an allowed math operator (`+`, `-`, `*`, `/`, `**`, `%`, `//`). Anything else raises an error before execution.

### 2. Two-layer memory deduplication
V5 uses fixed-key dict merge (`{**old, **new}`) — same key overwrites rather than appending, so duplicates are structurally impossible. V7 uses UUID-keyed rows — each fact gets a unique key, so explicit dedup is required. Two layers: first the LLM extraction prompt includes existing facts ("do not repeat these"), then a Python set check catches any exact-string repeats before `store.put()` is called.

### 3. MCP transport: streamable-http only
`stdio` transport (the MCP default) blocks Colab's main event loop and crashes the runtime. `streamable-http` runs the FastMCP server in a daemon thread on `localhost:8000`, completely decoupled from the notebook's event loop. `nest_asyncio.apply()` allows `asyncio.run()` to nest inside Colab's existing event loop.

### 4. StateGraph over create_agent in V7
`create_agent` handles the ReAct loop internally — suitable for V6 where only tool calling is needed. V7 requires custom nodes (`load_memories`, `save_memories`) that run before and after the agent loop. These cannot be injected into `create_agent`. A manual `StateGraph` gives full control over node sequencing and state management.

### 5. Dual memory: two different scopes
`InMemorySaver` is scoped to `thread_id` — it resets when a new conversation starts. `InMemoryStore` is scoped to `(namespace, user_id)` — it persists across all conversations for the same user. They solve different problems and are both needed. Using only `InMemorySaver` means the agent forgets you exist every new session.

---

## Stack

| Layer | Tool | Used from |
|---|---|---|
| Agent framework | LangGraph 1.1.9 | V1 |
| LLM | Groq - llama-3.3-70b-versatile | V2 |
| Short-term memory | InMemorySaver | V2 |
| Tool interface | @tool, ToolNode, tools_condition | V3 |
| Conditional routing | add_conditional_edges, custom router | V4 |
| Long-term memory | InMemoryStore | V5 |
| MCP server | FastMCP 3.4.2 | V6 |
| MCP client | langchain-mcp-adapters 0.3.0 | V6 |
| Live weather API | wttr.in (free, no API key) | V6 |
| Safe math | ast, operator (Python built-in) | V6 |
| Async in Colab | nest_asyncio | V6 |
| Tool execution node | ToolNode (from langgraph.prebuilt) | V7 |
| RAG retrieval | FAISS + all-MiniLM-L6-v2 | RAG Chatbot |
| RAG UI | Streamlit | RAG Chatbot |

---

## Also Built

| Project | Description | Link |
|---|---|---|
| Transformer from scratch | Full attention mechanism in PyTorch — no shortcuts | GitHub |
| DistilBERT spam classifier | Fine-tuned, 99%+ accuracy | HuggingFace |
| RAG Chatbot v3 | PDF upload, FAISS retrieval, conversational memory, Groq LLM | [Live](https://huggingface.co/spaces/danish811/rag-chatbot-v3) |

---

## How to Run

All notebooks run on Google Colab — no local setup, no paid APIs required.

1. Click any notebook in this repo
2. Open in Colab (File > Open in Colab, or use the badge at top)
3. Add Groq API key to Colab Secrets as `GROQ_API_KEY`
   - Left sidebar in Colab > key icon > New secret
   - Free key at: console.groq.com
4. Runtime > Run all

V6 and V7 require no additional setup beyond the `!pip install` cell already in the notebook.

---

## Contact

**Muhammad Danisht**
- GitHub: [github.com/muhammeddanisht](https://github.com/muhammeddanisht)
- HuggingFace: [huggingface.co/Danisht](https://huggingface.co/Danisht)
- Open to: AI/ML engineering roles, remote friendly

---

*All notebooks run entirely free. Groq free tier for LLM. wttr.in free API for weather. Google Colab for compute. HuggingFace Spaces for deployment. Zero paid services.*
