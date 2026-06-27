# ── SECTION 1: IMPORTS ────────────────────────────────────────

# Standard Python tools
import os
import uuid
import ast
import operator
import requests
import json
from typing import Literal

# Streamlit — the web framework
import streamlit as st

# LangChain messages
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_groq import ChatGroq

# LangGraph — same as V7
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore
# ── SECTION 2: API KEY SETUP ──────────────────────────────────

# st.secrets reads from .streamlit/secrets.toml on your computer
# On Streamlit Cloud it reads from the secrets panel in the dashboard
# Either way — the key never appears in your code or on GitHub
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
# os.environ = the system's key-value storage
# We put the key here so ChatGroq can find it automatically
# ── SECTION 3: TOOLS ──────────────────────────────────────────

# SAFE OPERATORS MAP
# Links math symbols to actual Python math functions
# ast.Add means the + symbol was found in the expression
SAFE_OPERATORS = {
    ast.Add:  operator.add,       # + symbol  →  add
    ast.Sub:  operator.sub,       # - symbol  →  subtract
    ast.Mult: operator.mul,       # * symbol  →  multiply
    ast.Div:  operator.truediv,   # / symbol  →  divide
}

def safe_eval(node):
    # node = one piece of the math expression
    # This function processes each piece safely
    if isinstance(node, ast.Constant):
        # ast.Constant = a plain number like 25 or 4
        return node.value
    elif isinstance(node, ast.BinOp):
        # ast.BinOp = a math operation like 25 * 4
        # BinOp has three parts: left number, operator, right number
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsafe operation blocked: {op_type}")
        left  = safe_eval(node.left)    # process left side
        right = safe_eval(node.right)   # process right side
        return SAFE_OPERATORS[op_type](left, right)  # do the math
    else:
        raise ValueError(f"Not allowed: {node}")

@tool
def calculator(expression: str) -> str:
    """Calculate a math expression. Example: '25 * 4' or '100 / 5' or '10 + 3'"""
    # expression = the math problem as text, like "25 * 4"
    try:
        tree = ast.parse(expression, mode="eval")
        # ast.parse = read the expression and break it into pieces
        # mode="eval" = tells ast this is a math expression, not full code
        result = safe_eval(tree.body)
        # tree.body = the actual math part after parsing
        # safe_eval = processes each piece and calculates the answer
        return f"Result of {expression} = {result}"
    except Exception as e:
        return f"Math error: {str(e)}"

@tool
def get_weather(city: str) -> str:
    """Get real current weather for any city. Example: 'London' or 'Kozhikode'"""
    try:
        url = f"https://wttr.in/{city}?format=3"
        # wttr.in = free weather website, no API key needed
        # ?format=3 = gives short output like "Kozhikode: 25C, Rain"
        response = requests.get(url, timeout=5)
        # requests.get = visit that URL and get the response
        # timeout=5 = if no response in 5 seconds, stop waiting
        if response.status_code == 200:
            # status_code 200 = success (website responded correctly)
            return f"Current weather: {response.text.strip()}"
            # .text = the text content of the response
            # .strip() = removes extra spaces/newlines
        else:
            return f"Could not fetch weather for {city}"
    except Exception as e:
        return f"Weather error: {str(e)}"

# List of ALL tools the LLM can use
tools = [calculator, get_weather]
# ── SECTION 4: BUILD GRAPH ────────────────────────────────────

@st.cache_resource
def build_graph():
    # @st.cache_resource = build this ONCE, reuse forever
    # Without this, every message would rebuild the entire agent
    # That would be slow and wasteful

    # ── LLM SETUP ─────────────────────────────────────────────
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    # Same LLM as V5/V6/V7
    # temperature=0 = always gives consistent answers, no randomness

    llm_with_tools = llm.bind_tools(tools)
    # bind_tools = give LLM the list of tools it can call
    # Now LLM knows calculator and get_weather exist

    # ── SYSTEM PROMPTS ────────────────────────────────────────
    AGENT_PROMPT = """You are a helpful personal assistant with memory.
You remember important facts about the user across conversations.

Here is what you know about this user:
{memories}

You have two tools available:
- calculator: for any math calculations
- get_weather: for real current weather of any city

Use tools when needed. Personalize responses using memory."""

    EXTRACT_PROMPT = """Read this conversation and extract ONLY important facts about the user.
Important facts = name, age, city, goals, job, skills, preferences.
Ignore: greetings, tool results, math questions, weather questions, small talk.
Return ONLY a JSON object. No explanation. No extra text.
Example: {{"name": "Danish", "goal": "AI job", "city": "Mattannur"}}
If nothing important found, return: {{}}"""

    # ── NODE 1: LOAD MEMORIES ─────────────────────────────────
    def load_memories(
        state: MessagesState,
        config: RunnableConfig,
        store: BaseStore
    ) -> dict:
        # Runs FIRST before agent sees the message
        # Reads long-term facts about this user from InMemoryStore

        user_id = config["configurable"].get("user_id", "default")
        # Get this visitor's unique ID from the config
        # "default" is fallback if no ID provided

        namespace = ("user_facts", user_id)
        # namespace = the folder in the facts book for THIS user
        # ("user_facts", "abc123") = facts/abc123 folder
        # Every visitor has their OWN folder

        memories = store.search(namespace)
        # Open that folder and read everything inside

        if memories:
            facts = memories[0].value
            memory_text = " | ".join(
                [f"{k}: {v}" for k, v in facts.items()]
            )
            # Turn {"name":"Danish","city":"Mattannur"}
            # into "name: Danish | city: Mattannur"
        else:
            memory_text = "No information about this user yet."

        filled_prompt = AGENT_PROMPT.format(memories=memory_text)
        # Replace {memories} placeholder with actual facts text

        return {"messages": [SystemMessage(content=filled_prompt)]}
        # Inject the system prompt WITH memories into message list
        # Agent will see this as its first instruction

    # ── NODE 2: AGENT ─────────────────────────────────────────
    def agent(state: MessagesState) -> dict:
        # The thinking node
        # Reads all messages + system prompt + decides what to do

        response = llm_with_tools.invoke(state["messages"])
        # Send full message history to LLM
        # LLM decides: answer directly OR call a tool

        return {"messages": [response]}

    # ── NODE 3: SAVE MEMORIES ─────────────────────────────────
    def save_memories(
        state: MessagesState,
        config: RunnableConfig,
        store: BaseStore
    ) -> dict:
        # Runs LAST after agent answered
        # Extracts important facts and saves them

        user_id = config["configurable"].get("user_id", "default")
        namespace = ("user_facts", user_id)

        # Get last two messages: user question + agent reply
        recent = state["messages"][-2:]
        conversation_text = ""
        for msg in recent:
            if isinstance(msg, HumanMessage):
                conversation_text += f"Human: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                conversation_text += f"Assistant: {msg.content}\n"

        # Ask LLM to extract important facts from conversation
        extract_response = llm.invoke([
            SystemMessage(content=EXTRACT_PROMPT),
            HumanMessage(content=conversation_text)
        ])

        # Parse the JSON response
        try:
            extracted = json.loads(extract_response.content)
        except Exception:
            extracted = {}
        # If LLM returned invalid JSON, just use empty dict
        # App never crashes because of bad extraction

        if extracted:
            # Read existing facts first so we dont lose old ones
            existing = store.search(namespace)
            old_facts = existing[0].value if existing else {}

            # Merge old facts + new facts together
            merged = {**old_facts, **extracted}
            # {**old, **new} = combine two dicts
            # If same key exists, new value wins (updates old info)

            store.put(namespace, "profile", merged)
            # Save merged facts back to this user's folder

        return {}
        # save_memories never changes messages
        # Returns empty dict = no state update needed

    # ── ROUTER ────────────────────────────────────────────────
    def should_continue(state: MessagesState) -> Literal["tools", END]:
        # After agent node runs, where do we go?
        # Check if agent wants to call a tool

        last_message = state["messages"][-1]
        # Get agent's most recent reply

        if last_message.tool_calls:
            return "tools"
            # Agent said "use calculator" or "use get_weather"
            # Go to tools node
        return END
        # Agent gave final answer
        # Conversation complete

    # ── TOOL NODE ─────────────────────────────────────────────
    tool_node = ToolNode(tools, handle_tool_errors=True)
    # Same as V6/V7
    # This is the room where tools actually execute
    # handle_tool_errors=True = if tool crashes, handle gracefully

    # ── WIRE THE GRAPH ────────────────────────────────────────
    graph = StateGraph(MessagesState)

    # Add all nodes (rooms)
    graph.add_node("load_memories", load_memories)
    graph.add_node("agent", agent)
    graph.add_node("tools", tool_node)
    graph.add_node("save_memories", save_memories)

    # Add edges (roads between rooms)
    graph.add_edge(START, "load_memories")
    # Entry door always goes to load_memories first

    graph.add_edge("load_memories", "agent")
    # After loading memories, go to agent

    graph.add_conditional_edges("agent", should_continue)
    # After agent: router decides tools or END

    graph.add_edge("tools", "agent")
    # After tools run, go back to agent with results

    graph.add_edge("agent", "save_memories")
    # After agent gives final answer, save memories

    graph.add_edge("save_memories", END)
    # After saving, conversation complete

    # ── COMPILE ───────────────────────────────────────────────
    checkpointer = InMemorySaver()
    store = InMemoryStore()

    app = graph.compile(
        checkpointer=checkpointer,
        store=store
    )
    # checkpointer = short-term memory (per thread_id)
    # store = long-term memory (per user_id)

    return app
    # Return the compiled agent
    # @st.cache_resource stores this and reuses it every time


# Build the agent ONCE when app starts
app = build_graph()
# ── SECTION 5: PAGE CONFIG ────────────────────────────────────

st.set_page_config(
    page_title="LangGraph AI Agent",
    page_icon="🤖",
    layout="centered"
)
# set_page_config = settings for the browser tab
# page_title = text shown on browser tab (like a window title)
# page_icon = emoji shown on browser tab
# layout="centered" = content in middle of screen, not full width
# IMPORTANT: this must be the FIRST st command in the file

# ── SIDEBAR ───────────────────────────────────────────────────

with st.sidebar:
    # st.sidebar = the left panel that slides out
    # "with" = everything indented inside goes INTO the sidebar

    st.title("🤖 LangGraph Agent")
    st.caption("V8 — Streamlit Deployment")
    # st.title = big heading text
    # st.caption = small grey text below

    st.divider()
    # st.divider = draws a horizontal line (just visual separation)

    st.markdown("### What I can do")
    # st.markdown = lets you write formatted text
    # ### = makes it a heading (like bold title)

    st.markdown("""
- 🧮 **Calculate** anything  
- 🌤️ **Live weather** for any city  
- 🧠 **Remember** facts about you  
- 💬 **Chat** naturally  
""")
    # This is a bullet point list
    # ** text ** = bold text
    # Each line with - becomes a bullet point

    st.divider()

    st.markdown("### Your Session")
    # This section will show the user their session info

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()
    # st.button = clickable button
    # if st.button(...): = runs the indented code when clicked
    # Clears chat history + generates new thread_id
    # st.rerun() = tells Streamlit to restart the script immediately

    st.divider()

    st.caption("Built with LangGraph + Groq + Streamlit")
    # ── SECTION 6: SESSION STATE INITIALIZATION ───────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
# Check if messages list exists in session_state
# If NOT exists = first time this visitor opened the app
# Create empty list to store chat history
# If EXISTS = visitor already chatting, dont reset it

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
# Check if this visitor has a thread_id yet
# If NOT exists = brand new visitor
# Generate unique ID for their conversation
# If EXISTS = same visitor, keep their existing ID

if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
# Same pattern for user_id
# user_id = identity for long-term memory store
# thread_id = identity for short-term conversation memory
# Two different IDs, two different jobs
# ── SECTION 7: CHAT HISTORY DISPLAY ──────────────────────────

st.title("🤖 LangGraph AI Agent")
st.caption("Powered by Groq + LangGraph + Streamlit")
# Main page title - different from sidebar title
# This appears in the CENTER of the page, not sidebar

st.divider()

# Loop through every message saved in session_state
# Display each one as a chat bubble
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # st.chat_message = creates a chat bubble
        # message["role"] = "user" or "assistant"
        # "user" role    = bubble on right, person icon
        # "assistant" role = bubble on left, robot icon
        st.write(message["content"])
        # st.write = display the text inside the bubble
# ── SECTION 8: INPUT + AGENT RESPONSE ────────────────────────

prompt = st.chat_input("Ask me anything...")
# st.chat_input = the text box at bottom of screen
# User types here and presses Enter
# When user submits → prompt = their message text
# When nothing submitted → prompt = None

if prompt:
    # Only runs when user actually sent a message
    # If prompt is None (nothing typed) → skip everything below

    # ── SAVE USER MESSAGE ─────────────────────────────────────
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    # append = add new item to end of list
    # Save user's message to session_state
    # So it survives the next rerun

    # ── DISPLAY USER BUBBLE ───────────────────────────────────
    with st.chat_message("user"):
        st.write(prompt)
    # Show user's message as a chat bubble immediately
    # Dont wait for agent - show it right away

    # ── GET AGENT RESPONSE ────────────────────────────────────
    with st.chat_message("assistant"):
        # Open assistant chat bubble
        # Everything inside appears in that bubble

        with st.status("Agent thinking...", expanded=True) as status:
            # st.status = live progress box
            # Shows what the agent is doing step by step
            # expanded=True = open by default so user sees progress

            final_response = ""
            # Empty string to collect agent's answer

            config = {
                "configurable": {
                    "thread_id": st.session_state.thread_id,
                    "user_id":   st.session_state.user_id
                }
            }
            # config = the delivery envelope
            # Carries this visitor's IDs into the graph nodes
            # thread_id → InMemorySaver (short-term memory)
            # user_id   → InMemoryStore (long-term memory)

            input_data = {
                "messages": [HumanMessage(content=prompt)]
            }
            # input_data = what we send into the graph
            # Wrap user's text in HumanMessage format
            # LangGraph expects this exact format

            # ── STREAM THE GRAPH ──────────────────────────────
            for update in app.stream(
                input_data,
                config=config,
                stream_mode="updates"
            ):
                # app.stream = run the graph and get updates
                # stream_mode="updates" = tells us what each
                # node returned after it finished running
                # update = one node's output at a time

                for node_name, node_output in update.items():
                    # update is a dictionary like:
                    # {"agent": {"messages": [AIMessage(...)]}}
                    # node_name  = which room just finished
                    # node_output = what that room returned

                    if node_name == "load_memories":
                        status.update(
                            label="Loading your memories..."
                        )
                        # load_memories room finished
                        # Update the progress box text

                    elif node_name == "agent":
                        status.update(
                            label="Agent thinking..."
                        )
                        msgs = node_output.get("messages", [])
                        # Get messages from agent's output
                        # .get("messages", []) = safely get
                        # messages key, use [] if not found

                        for msg in msgs:
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                tool_name = msg.tool_calls[0]["name"]
                                status.update(
                                    label=f"Using tool: {tool_name}..."
                                )
                                # hasattr checks if tool_calls exists
                                # If agent wants to use a tool
                                # Show which tool is being called

                            elif hasattr(msg, "content") and msg.content:
                                if isinstance(msg.content, str):
                                    final_response = msg.content
                                    # Agent gave final text answer
                                    # Save it to final_response

                    elif node_name == "tools":
                        status.update(
                            label="Tool running..."
                        )
                        # Tools node finished running
                        # Calculator or weather just executed

                    elif node_name == "save_memories":
                        status.update(
                            label="Saving to memory..."
                        )
                        # save_memories room finished
                        # Facts extracted and saved

            status.update(
                label="Done!",
                state="complete"
            )
            # After all nodes finished
            # Mark status box as complete
            # state="complete" = turns the box green with checkmark

        # ── DISPLAY FINAL RESPONSE ────────────────────────────
        st.write(final_response)
        # Show agent's final answer below the status box

    # ── SAVE AGENT MESSAGE ────────────────────────────────────
    st.session_state.messages.append({
        "role": "assistant",
        "content": final_response
    })
    # Save agent's reply to session_state
    # So it appears in chat history on next rerun

