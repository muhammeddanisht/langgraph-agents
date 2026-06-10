# DECISIONS.md — LangGraph Agents (v1 → v8)
> Architecture Decision Records for every major choice made
> across the full LangGraph learning and building journey.

---

## ADR-001: Why LangGraph over plain LangChain LCEL?

**Status:** Accepted  
**Version:** v1  

**Context:**  
LangChain LCEL chains are linear — input flows one direction.
Real agents need branching: "did the tool fail? retry. 
did user ask code? route to code agent."
Linear chains can't do this without hacks.

**Decision:**  
Use LangGraph. Models agent logic as a graph.
Nodes = functions. Edges = decisions.
State persists across nodes automatically.

**Alternatives considered:**  
| Option | Why rejected |
|---|---|
| Plain LCEL chain | No branching, no state, no loops |
| CrewAI | Higher abstraction, less control |
| AutoGen | Microsoft-specific, less LangChain native |
| **LangGraph** ✅ | Full control, official LangChain recommendation |

**Consequences:**  
More setup than LCEL. Worth it — production agents
at Notion, Linear use this exact pattern.

---

## ADR-002: Why TypedDict for AgentState over plain dict?

**Status:** Accepted  
**Version:** v2  

**Context:**  
Agent state passed between every node.
If one node adds wrong key, silent bug — crashes 3 nodes later.
Hard to debug.

**Decision:**  
```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    route: str
```
TypedDict enforces structure at definition time.
`add_messages` reducer appends instead of overwrites —
critical for conversation history.

**Consequences:**  
Type errors caught early. Code self-documents.
Any new developer reads state = understands entire agent.

---

## ADR-003: Why Groq over OpenAI for inference?

**Status:** Accepted  
**Version:** v2  

**Context:**  
Agent loops call LLM multiple times per request.
4-node graph × 2 sec/call = 8 sec response time.
Unacceptable for demos and recruiter walkthroughs.

**Decision:**  
Use Groq (llama-3.1-8b-instant).

**Benchmark tested:**  
| Provider | Avg response | Cost |
|---|---|---|
| OpenAI GPT-4o | ~2000ms | Paid |
| OpenAI GPT-3.5 | ~800ms | Paid |
| **Groq llama-3.1-8b** ✅ | ~300ms | Free tier |

Same graph = 1.2 sec end-to-end on Groq vs 8 sec OpenAI.
6× faster. Free. Obvious choice for portfolio projects.

**Consequences:**  
Model less capable than GPT-4. Acceptable for
agent routing and tool use tasks in this project.

---

## ADR-004: Why handle_tool_errors=True in ToolNode?

**Status:** Accepted  
**Version:** v3  

**Context:**  
Without error handling, one bad API call or malformed
tool input crashes entire graph. No recovery.

**Decision:**  
```python
ToolNode(tools, handle_tool_errors=True)
```
Error caught → passed back as message → agent decides next step.

**Consequences:**  
Difference between demo and production system.
Agent can retry, reroute, or explain failure gracefully.

---

## ADR-005: Why Literal type for router return?

**Status:** Accepted  
**Version:** v4  

**Context:**  
LangGraph builds conditional edge map at compile time.
Without explicit types, it doesn't know which edges are valid.
Runtime error instead of compile-time error.

**Decision:**  
```python
def router(state) -> Literal["code", "rag", "general"]:
```
Literal forces all valid routes declared upfront.
Also documents all possible paths in one place.

**Consequences:**  
Adding new route = update Literal + add edge.
Impossible to route to undefined node accidentally.

---

## ADR-006: Why 3 specialist agents over 1 general agent?

**Status:** Accepted  
**Version:** v4  

**Context:**  
Tested single agent with all instructions in one system prompt.
Code questions answered with RAG reasoning.
RAG questions answered with code formatting.
Confused outputs. Inconsistent.

**Decision:**  
3 separate specialist system prompts:
- Code Agent: thinks only about code
- RAG Agent: thinks only about retrieval
- General Agent: everything else

This = "mixture of experts" at prompt level.

**Alternatives considered:**  
| Option | Problem |
|---|---|
| 1 massive system prompt | Context confusion, inconsistent output |
| 2 agents | Not granular enough |
| **3 specialist agents** ✅ | Clean separation, predictable outputs |

---

## ADR-007: [v5 — Memory + MCP] — IN PROGRESS

**Status:** Proposed  

**Context:**  
v4 agent has no memory across sessions.
Each conversation starts fresh — no continuity.
MCP tools not yet integrated.

**Decision:** (pending)  
Evaluating: LangGraph checkpointers (MemorySaver vs PostgresSaver)
and MCP tool integration approach.

**Will update after v5 complete.**

---

## What I'd do differently in production

- PostgreSQL checkpointer instead of MemorySaver (persistent)
- LangSmith tracing on every node (debug which node failed)
- RAGAS evaluation on RAG node answer quality
- Rate limiting per user session
- Streaming token output (not wait for full response)
- Docker containerization for deployment
