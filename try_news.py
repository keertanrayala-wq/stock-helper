import sys

from src.news import clean_headlines, fetch_headlines, get_company_name
from src.sentiment import aggregate_sentiment, describe_sentiment, score_headlines

ticker = sys.argv[1] if len(sys.argv) > 1 else "TCS.NS"
print(f"Company: {get_company_name(ticker)}")

items = clean_headlines(fetch_headlines(ticker))
print(f"{ticker}: {len(items)} headlines after cleaning")

scored = score_headlines([i["title"] for i in items])
for s in scored:
    print(f'{s["label"]:>8}  {s["score"]:+.2f}  {s["title"]}')

summary = aggregate_sentiment(scored)
print(summary)
print(describe_sentiment(summary))
