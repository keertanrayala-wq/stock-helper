import os

import streamlit as st

from src.assistant import chat, get_client

st.set_page_config(page_title="Ask Stock Helper", layout="wide")
st.title("Ask Stock Helper")
st.caption("Educational only. This is not financial advice.")

env_key = os.environ.get("LLM_API_KEY")

STARTERS = [
    "What is RSI, in simple words?",
    "Is Infosys overbought right now?",
    "Why did TCS fall on 4 November 2026?",
    "What does a candlestick chart show?",
]

if "history" not in st.session_state:
    st.session_state.history = []
    st.session_state.display = []


def clear_chat():
    st.session_state.history = []
    st.session_state.display = []


def pick(text: str):
    st.session_state.pending = text


with st.sidebar:
    user_key = st.text_input(
        "Your Groq API key",
        type="password",
        help="Free at console.groq.com. Used only for your session and not saved by the app.",
    ).strip()
    beginner = st.toggle("Explain like I'm new to investing", value=True)
    st.button("Clear chat", on_click=clear_chat)

key = user_key or env_key
if not key:
    st.info(
        "To chat, paste your free Groq API key in the sidebar. "
        "You can create one at console.groq.com."
    )
    st.stop()


def show(text: str) -> None:
    # Escape dollar signs so prices are not rendered as math
    st.markdown(text.replace("$", "\\$"))


for m in st.session_state.display:
    with st.chat_message(m["role"]):
        show(m["content"])
        if m.get("tools"):
            st.caption("Data used: " + "; ".join(m["tools"]))

pending = st.session_state.pop("pending", None)
prompt = st.chat_input("Ask about a stock, or what a term means") or pending

if not st.session_state.display and not prompt:
    st.write("New to investing? Try one of these:")
    cols = st.columns(len(STARTERS))
    for i, (col, text) in enumerate(zip(cols, STARTERS)):
        col.button(text, key=f"starter_{i}", on_click=pick, args=(text,))

if prompt:
    st.session_state.display.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        show(prompt)

    level = "beginner" if beginner else "standard"
    with st.chat_message("assistant"):
        with st.spinner("Checking the data..."):
            try:
                client = get_client(key)
                text, st.session_state.history, calls = chat(
                    client, st.session_state.history, prompt, level
                )
            except Exception as exc:
                text, calls = f"Something went wrong: {exc}", []
        show(text)
        tools = [
            f"{name}({', '.join(str(v) for v in args.values())})"
            for name, args in calls
        ]
        if tools:
            st.caption("Data used: " + "; ".join(tools))

    st.session_state.display.append(
        {"role": "assistant", "content": text, "tools": tools}
    )