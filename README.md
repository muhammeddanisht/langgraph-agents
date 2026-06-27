# 🤖 LangGraph Agent Series — V1 to V8

> Self-taught AI engineer. Zero coding background. Built 8 production-grade
> LangGraph agents from scratch — deployed, documented, and decision-recorded.

## 🚀 Live Demo
👉 **[Use the agent live — no setup needed](https://danish-ai-agent.streamlit.app)**

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://danish-ai-agent.streamlit.app)
[![HuggingFace RAG](https://img.shields.io/badge/HuggingFace-RAG%20Chatbot-yellow)](https://huggingface.co/spaces/danish811/rag-chatbot-v3)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1.9-orange)]()
[![Python](https://img.shields.io/badge/Python-3.10+-blue)]()

---

## What This Is

8 LangGraph agents built in progression. Each version builds on the last.
Not a course project. Built to prove production AI engineering skills to employers.

**V8 is live** — personal AI agent with:
- 🧮 Safe math via AST-based calculator (no eval() — security by design)
- 🌤️ Live weather via wttr.in (real data, no fake responses)
- 🧠 Dual memory — short-term per conversation + long-term across sessions
- 👤 UUID per visitor — memory never leaks between public users

---

## The Series

| # | What It Builds | Key Concept |
|---|---------------|-------------|
| V1 | Pure graph — no LLM | StateGraph, nodes, edges, TypedDict |
| V2 | LLM + conversation memory | MessagesState, InMemorySaver, thread_id |
| V3 | Tool calling | @tool, ToolNode, tools_condition, bind_tools |
| V4 | Multi-agent routing | Conditional edges, classifier node, Literal router |
| V5 | Dual memory | InMemorySaver (short-term) + InMemoryStore (long-term) |
| V6 | MCP agent | FastMCP 3.4.2, langchain-mcp-adapters, streamable-http |
| V7 | Production agent | V5 dual memory + V6 MCP tools combined |
| **V8** | **Deployed web app** | **Streamlit, UUID session isolation, st.cache_resource** |

---

## V8 — Architecture
Visitor opens link

↓

Streamlit (UUID per visitor via st.session_state)

↓

load_memories  →  reads user facts from InMemoryStore

↓

agent  →  llama-3.3-70b-versatile, temperature=0

↓  tool needed?

tools  →  AST calculator OR wttr.in live weather

↓

agent  →  final answer with tool result

↓

save_memories  →  extracts facts, writes to InMemoryStore

↓

Streamlit (live progress via st.status)
Each visitor gets their own UUID on first load.
`thread_id` = short-term memory scope.
`user_id` = long-term memory scope.
Memory never crosses between visitors.

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Agent framework | LangGraph | 1.1.9 |
| LLM | Groq llama-3.3-70b-versatile | temperature=0 |
| Short-term memory | LangGraph InMemorySaver | — |
| Long-term memory | LangGraph InMemoryStore | — |
| MCP server (V6, V7) | FastMCP | 3.4.2 |
| MCP client (V6, V7) | langchain-mcp-adapters | 0.3.0 |
| Embeddings (RAG v3) | all-MiniLM-L6-v2 | 384-dim |
| Web UI | Streamlit | — |
| Deployment | Streamlit Community Cloud | free tier |

---

## Architecture Decisions

Every significant design choice is documented in
[DECISIONS.md](DECISIONS.md) using MADR 4.0.0 format.

11 decisions documented including:
- AST over eval() for calculator security
- streamable-http over stdio/SSE for Colab stability
- InMemorySaver + InMemoryStore for dual memory scopes
- UUID per session for public multi-user isolation (V8)
- Direct tool calls over MCP server for V8 deployment reliability

---

## Other Portfolio Projects

| Project | Description | Link |
|---------|-------------|------|
| RAG Chatbot v3 | LangChain + FAISS + Groq. PDF upload up to 200MB. | [Live on HuggingFace](https://huggingface.co/spaces/danish811/rag-chatbot-v3) |
| DistilBERT Spam Classifier | Fine-tuned transformer. 99.19% accuracy. | [HuggingFace Hub](https://huggingface.co/danish811/spam-detector-distilbert) |

---

## Run Locally

```bash
git clone https://github.com/muhammeddanisht/langgraph-agents
cd langgraph-agents
pip install -r requirements.txt
```

Add your key to `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your_key_here"
```

Run:
```bash
python -m streamlit run app.py
```

---

## Contact

**Muhammed Danish T.** — AI Engineer (Open to Work)

[![GitHub](https://img.shields.io/badge/GitHub-muhammeddanisht-black)](https://github.com/muhammeddanisht)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-muhammeddanisht-blue)](https://linkedin.com/in/muhammeddanisht)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-danish811-yellow)](https://huggingface.co/danish811)
