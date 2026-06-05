#  LangGraph Agents — Building AI Agents Step by Step

> **AI/ML Engineer in progress** | LangGraph · LangChain · Groq · Python

Building a production-grade AI agent from scratch — version by version.
Each notebook = one new concept. Each version = more powerful agent.

---

##  Live Notebooks

| Version | What It Does | Open |
|---------|-------------|------|
| v1 — Basic Graph | State + Nodes + Edges | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://github.com/muhammeddanisht/langgraph-agents/blob/main/langgraph_v1_basics.ipynb) |
| v2 — LLM Node | Groq LLM + Memory + Conversation | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://github.com/muhammeddanisht/langgraph-agents/blob/main/langgraph_v2_llm_node.ipynb) |
| v3 — Tool Calling | @tool + ToolNode + Agent Loop | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://github.com/muhammeddanisht/langgraph-agents/blob/main/langgraph_v3_tools.ipynb) |

---

##  What Is This?

A step-by-step build of a LangGraph AI agent using:
- **Groq LLM** (llama-3.1-8b-instant) as the brain
- **@tool decorator** to give agent real capabilities
- **ToolNode + tools_condition** for the agent loop
- **MemorySaver** for persistent conversation memory

---

##  Agent Architecture (v3)

User Input
↓
[Agent Node] — Groq LLM decides
↓
tools_condition (traffic signal)
↓ tool needed          ↓ no tool
[Tool Node]              END
↓
back to Agent

---

---

##  Stack

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-1.1.9-green)
![Groq](https://img.shields.io/badge/Groq-LLaMA3-orange)
![LangChain](https://img.shields.io/badge/LangChain-latest-yellow)

---

##  Versions Roadmap

| Version | Concept | Status |
|---------|---------|--------|
| v1 | Basic graph — State, Nodes, Edges | ✅ Done |
| v2 | Groq LLM + MessagesState + Memory | ✅ Done |
| v3 | @tool + ToolNode + Agent Loop | ✅ Done |
| v4 | Conditional edges + Context Engineering | 🔄 Building |
| v5 | MCP Integration (Gmail/Calendar) | ⬜ Soon |
| v6 | ReAct Pattern | ⬜ Soon |
| v7 | Multi-Agent + A2A | ⬜ Soon |
| v8 | Final Deploy — Streamlit on HuggingFace | ⬜ Soon |

---

##  Author

**Muhammed Danish T** — AI/ML Engineer
[GitHub](https://github.com/muhammeddanisht) · [HuggingFace](https://huggingface.co/danish811)
 
