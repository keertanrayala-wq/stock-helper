from functools import lru_cache


@lru_cache(maxsize=1)
def _get_pipeline():
    from transformers import pipeline

    return pipeline("sentiment-analysis", model="ProsusAI/finbert")


def signed_score(label: str, score: float) -> float:
    """Positive -> +score, negative -> -score, neutral -> 0."""
    label = label.lower()
    if label == "positive":
        return score
    if label == "negative":
        return -score
    return 0.0


def score_headlines(titles: list[str]) -> list[dict]:
    """Run FinBERT on headlines and return label plus a signed score."""
    if not titles:
        return []
    results = _get_pipeline()(titles, truncation=True)
    return [
        {
            "title": t,
            "label": r["label"].lower(),
            "confidence": round(r["score"], 3),
            "score": round(signed_score(r["label"], r["score"]), 3),
        }
        for t, r in zip(titles, results)
    ]


def aggregate_sentiment(scored: list[dict]) -> dict:
    """Combine per-headline scores into one summary."""
    if not scored:
        return {"count": 0, "mean_score": None, "positive": 0, "negative": 0, "neutral": 0}
    return {
        "count": len(scored),
        "mean_score": round(sum(s["score"] for s in scored) / len(scored), 3),
        "positive": sum(s["label"] == "positive" for s in scored),
        "negative": sum(s["label"] == "negative" for s in scored),
        "neutral": sum(s["label"] == "neutral" for s in scored),
    }


MIN_HEADLINES = 5


def describe_sentiment(summary: dict) -> str:
    """Turn an aggregate summary into a short label for the user."""
    if summary["count"] < MIN_HEADLINES or summary["mean_score"] is None:
        return "Not enough recent news to score"
    mean = summary["mean_score"]
    if mean >= 0.15:
        return "Mostly positive"
    if mean <= -0.15:
        return "Mostly negative"
    return "Mixed or neutral"
