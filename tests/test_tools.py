import json

from src.tools import TOOLS, run_tool


def test_unknown_tool_returns_error():
    assert "error" in json.loads(run_tool("nope", {}))


def test_tool_names():
    assert {t["name"] for t in TOOLS} == {
        "search_company",
        "get_stock_summary",
        "get_news_sentiment",
    }


def test_openai_tool_conversion():
    from src.assistant import OPENAI_TOOLS

    assert len(OPENAI_TOOLS) == 3
    assert OPENAI_TOOLS[0]["type"] == "function"
    assert "parameters" in OPENAI_TOOLS[0]["function"]