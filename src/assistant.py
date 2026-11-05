import json
import os

import openai
from dotenv import load_dotenv

from src.tools import TOOLS, run_tool

load_dotenv()

MAX_STEPS = 6
MAX_TOOL_CHARS = 3000

SYSTEM_PROMPT = """You are Stock Helper, an educational assistant for beginner investors.

Rules:
- Every price, ratio, indicator value, or headline you mention MUST come from a tool result in this conversation. Never use memorized or guessed numbers.
- If the user gives a company name, call search_company first to find the ticker, then use the other tools.
- If a tool returns an error or no data, say so plainly. Do not fill the gap.
- Never tell the user to buy, sell, or hold, and never promise or predict returns. Explain what the data shows and what it does not show.
- Explain indicators like RSI and MACD in simple language, and mention the currency of prices when relevant.
- Keep answers short and clear. End with a one-line reminder that this is educational, not financial advice, when you discuss a specific stock.
"""


def to_openai_tools(tools: list) -> list:
    """Convert our tool definitions to the OpenAI-compatible format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in tools
    ]


OPENAI_TOOLS = to_openai_tools(TOOLS)


def get_model() -> str:
    return os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")


def get_client(api_key: str | None = None) -> openai.OpenAI:
    key = api_key or os.environ.get("LLM_API_KEY")
    if not key:
        raise ValueError("No API key found. Set LLM_API_KEY in your .env file.")
    base_url = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    return openai.OpenAI(api_key=key, base_url=base_url)


def chat(client, history: list, user_message: str):
    """Send a message, let the model call tools, and return the final answer.

    Returns (answer_text, updated_history, tool_calls) where tool_calls is a
    list of (tool_name, tool_input) pairs the model used.
    """
    messages = history + [{"role": "user", "content": user_message}]
    calls = []
    for _ in range(MAX_STEPS):
        try:
            response = client.chat.completions.create(
                model=get_model(),
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                tools=OPENAI_TOOLS,
                max_tokens=1024,
            )
        except openai.RateLimitError:
            return (
                "The free AI service is rate-limited right now. "
                "Please wait a minute and try again.",
                history,
                calls,
            )
        except openai.APIError as exc:
            return f"The AI service had a problem: {exc}", history, calls

        msg = response.choices[0].message
        entry = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        messages.append(entry)

        if not msg.tool_calls:
            return msg.content or "", messages, calls

        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            calls.append((tc.function.name, args))
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": run_tool(tc.function.name, args)[:MAX_TOOL_CHARS],
                }
            )
    return "Sorry, I couldn't finish that. Please try a simpler question.", messages, calls