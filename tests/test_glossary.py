import json

from src.glossary import GLOSSARY, lookup_term


def test_lookup_known_term():
    result = json.loads(lookup_term("RSI"))
    assert result["term"] == "RSI"
    assert "0 to 100" in result["definition"]


def test_aliases_and_case():
    assert json.loads(lookup_term("SMA"))["term"] == "Moving average"
    assert json.loads(lookup_term("  Overbought "))["term"] == "Overbought and oversold"
    assert json.loads(lookup_term("p/e"))["term"] == "P/E ratio"


def test_unknown_term_lists_available():
    result = json.loads(lookup_term("zzz"))
    assert "error" in result
    assert "RSI" in result["available_terms"]


def test_every_term_has_a_definition():
    assert all(len(text) > 40 for text in GLOSSARY.values())