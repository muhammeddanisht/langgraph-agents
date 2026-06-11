# 🤖 LangGraph Agents — From Zero to Production

> A progressive series of AI agent notebooks built with **LangGraph**, 
> **Groq LLM**, and production memory patterns.  
> Each version adds one real skill. V1 → V5 = zero to memory-enabled agent.

![LangGraph](https://img.shields.io/badge/LangGraph-1.1.9-blue?style=flat-square)
![LangChain](https://img.shields.io/badge/LangChain_Core-1.3.1-green?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-llama--3.1--8b-orange?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)

---

## 🎯 What This Repository Is

Most AI tutorials teach concepts in isolation.

This repo builds one agent — version by version — adding one real skill 
at a time. By V5, the agent remembers users across conversations, 
routes intelligently, uses tools, and applies context engineering.

Every concept taught here maps directly to what production AI teams 
build in 2026.

---

## 📚 Version Roadmap

| Version | Notebook | Core Skill | Key Concepts | Run |
|---|---|---|---|---|
| V1 | `langgraph_v1_basics.ipynb` | Graph fundamentals | StateGraph, Nodes, Edges, START, END | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/muhammeddanisht/langgraph-agents/blob/main/langgraph_v1_basics.ipynb) |
| V2 | `langgraph_v2_llm_node.ipynb` | LLM integration | ChatGroq, MessagesState, MemorySaver, thread_id | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/muhammeddanisht/langgraph-agents/blob/main/langgraph_v2_llm_node.ipynb) |
| V3 | `langgraph_v3_tools.ipynb` | Tool use + agent loop | @tool, ToolNode, tools_condition, ReAct loop | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/muhammeddanisht/langgraph-agents/blob/main/langgraph_v3_tools.ipynb) |
| V4 | `langgraph_v4_conditional_edges.ipynb` | Routing + Context Engineering | Conditional edges, classifier node, system prompts | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/muhammeddanisht/langgraph-agents/blob/main/langgraph_v4_conditional_edges.ipynb) |
| V5 | `langgraph_v5_memory.ipynb` | Dual memory architecture | MemorySaver, InMemoryStore, LLM fact extraction | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)]([YOUR_V5_LINK](https://colab.research.google.com/drive/1DHSCnH5_v5P0rIURVeOZGsTdQQ07i1R5)) |

---

## 🏗️ V5 Architecture — Dual Memory Agent
User Message
↓
┌─────────────┐     reads facts    ┌──────────────────┐
│  call_model │◄───────────────────│  InMemoryStore   │
│             │                    │  (Long-term)     │
└──────┬──────┘                    └──────────────────┘
│                                    ▲
│ tool needed?                       │ writes facts
│                           ┌────────┴──────┐
YES ─┼─→ tools ──────────────┐   │  save_memory  │
│        loop back      │   └───────────────┘
NO ──┼─────────────────────► │
│                       └──→ call_model
│
└──→ save_memory ──→ END
Short-term: MemorySaver (thread_id scoped — this conversation)
Long-term:  InMemoryStore (user_id scoped — all conversations)

---

## 🧠 What V5 Proves

| Test | Input | Expected | Result |
|---|---|---|---|
| Test 1 | "My name is Danish. Multiply 12×8" | Tool runs + facts saved | ✅ |
| Test 2 | New thread, same user: "What's my name?" | Agent recalls name | ✅ |
| Test 3 | Same thread: "What was my result?" | Agent recalls 96 | ✅ |

---

## 🔑 Skills Demonstrated Across V1–V5

Agent Architecture          LangGraph StateGraph, compiled graphs
State Management            MessagesState, custom AgentState, state fields
LLM Integration             ChatGroq, llama-3.1-8b-instant, bind_tools
Tool Use                    @tool decorator, ToolNode, tools_condition
Conditional Routing         add_conditional_edges, Literal type hints
Context Engineering         Specialist system prompts, dynamic prompt filling
Short-term Memory           MemorySaver checkpointer, thread_id scoping
Long-term Memory            InMemoryStore, namespace isolation, store.put/search
Fact Extraction             LLM-based extraction, JSON parsing, dict merging
Production Patterns         MemorySaver→PostgresSaver migration path
Config Management           RunnableConfig, thread_id + user_id in configurable

---

## 🛠️ Tech Stack

---

## 🚀 Quick Start

**No local setup needed. Everything runs in Google Colab.**

1. Click any Colab badge in the table above
2. Go to `Runtime → Run all`
3. Add `GROQ_API_KEY` to Colab Secrets (left sidebar 🔑)
4. Watch the agent run

**Get free Groq API key:** [console.groq.com](https://console.groq.com) — 
no credit card, generous free tier.

---

## 📖 Learning Path

Each version is a standalone notebook with:
- ✅ Concept explanation before any code
- ✅ Every line commented
- ✅ Test cases with expected outputs
- ✅ Builds directly on previous version

**Recommended order:** V1 → V2 → V3 → V4 → V5

---

## 🗺️ Coming Next

| Version | Topic | Status |
|---|---|---|
| V6 | MCP — Model Context Protocol | 🔄 Building |
| V7 | Multi-Agent + A2A Communication | ⬜ Planned |
| V8 | Streamlit Deployment — Full App | ⬜ Planned |

---

## 👨‍💻 Author

**Muhammed Danish T.**  
BBA Graduate → AI/ML Engineer  
Building production AI agents from scratch.

[![GitHub](https://img.shields.io/badge/GitHub-muhammeddanisht-black?style=flat-square&logo=github)](https://github.com/muhammeddanisht)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-danish811-yellow?style=flat-square)](https://huggingface.co/danish811)

---

## ⭐ If this helped you learn LangGraph — star the repo.
