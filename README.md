# 🤖 LangGraph Agent Series — V1 to V8

> Self-taught AI engineer building production-grade LangGraph agents
> from scratch. 8 notebooks showing progressive skill growth —
> from graph basics to a live deployed web app.

## 🚀 Live Demo
👉 **[Click to use the agent — no setup required](https://danish-ai-agent.streamlit.app)**

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://danish-ai-agent.streamlit.app)
[![HuggingFace RAG](https://img.shields.io/badge/HuggingFace-RAG%20Chatbot-yellow)](https://huggingface.co/spaces/danish811/rag-chatbot-v3)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)]()
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1.9-orange)]()

---

## What This Is

A series of 8 LangGraph agents — each one building on the last.
Built to prove production AI engineering skills, not just to learn.

**V8 (live now)** — personal AI agent with:
- 🧮 Real math via AST-safe calculator (no eval() — security by design)
- 🌤️ Live weather from wttr.in (real data, no fake responses)
- 🧠 Dual memory — short-term per conversation + long-term across sessions
- 👤 UUID session isolation — each visitor gets their own memory namespace

---

## The Series

| Version | What It Builds | Key Concept Demonstrated |
|---------|---------------|--------------------------|
| V1 | Pure graph — no LLM | StateGraph, nodes, edges, TypedDict state |
| V2 | LLM + conversation memory | MessagesState, InMemorySaver, thread_id |
| V3 | Tool calling agent | @tool decorator, ToolNode, bind_tools |
| V4 | Multi-agent routing | Conditional edges, classifier node, Literal router |
| V5 | Dual memory system | InMemorySaver (short) + InMemoryStore (long) |
| V6 | MCP agent | FastMCP 3.4.2, langchain-mcp-adapters, streamable-http |
| V7 | Production agent | V5 dual memory + V6 MCP tools combined |
| **V8** | **Streamlit deployment** | **Public web app, UUID session isolation, caching** |

---

## V8 Architecture
Browser visitor

↓

[Streamlit UI — st.cache_resource, UUID per session]

↓

load_memories — reads facts from InMemoryStore

↓

agent — llama-3.3-70b-versatile, temperature=0

↓  (if tool needed)

tools — AST calculator OR wttr.in live weather

↓

agent — final answer

↓

save_memories — extracts facts, writes back to store

↓

[Browser — st.status shows live tool call progress]
Browser visitor

↓

[Streamlit UI — st.cache_resource, UUID per session]

↓

load_memories — reads facts from InMemoryStore

↓

agent — llama-3.3-70b-versatile, temperature=0

↓  (if tool needed)

tools — AST calculator OR wttr.in live weather

↓

agent — final answer

↓

save_memories — extracts facts, writes back to store

↓

[Browser — st.status shows live tool call progress]
