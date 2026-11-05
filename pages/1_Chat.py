import os

import streamlit as st

from src.assistant import chat, get_client

st.set_page_config(page_title="Ask Stock Helper", layout="wide")
st.title("Ask Stock Helper")
st.caption("Educational only. This is not financial advice.")

env_key = os.environ.get("LLM_API_KEY")

with st.sidebar:
    user_key = st.text_input(
        "Your Groq API key",
        type="password",
        help="Free at console.groq.com. Used only for your session and not saved by the app.",
    ).strip()
    if st.button("Clear chat"):
        st.session_state.history = []
        st.session_state.display = []

key = user_key or env_key
if not key:
    st.info(
        "To chat, paste your free Groq API key in the sidebar. "
        "You can create one at console.groq.com."
    )
    st.stop()

if "history" not in st.session_state:
    st.session_state.history = []
    st.session_state.display = []


def show(text: str) -> None:
    # Escape dollar signs so prices are not rendered as math
    st.markdown(text.replace("$", "\\$"))


for m in st.session_state.display:
    with st.chat_message(m["role"]):
        show(m["content"])
        if m.get("tools"):
            st.caption("Data used: " + "; ".join(m["tools"]))

prompt = st.chat_input("Ask about a stock, e.g. Is Infosys overbought right now?")
if prompt:
    st.session_state.display.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        show(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Checking the data..."):
            try:
                client = get_client(key)
                text, st.session_state.history, calls = chat(
                    client, st.session_state.history, prompt
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