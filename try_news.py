from src.news import fetch_headlines
from src.sentiment import aggregate_sentiment, score_headlines

items = fetch_headlines("TCS.NS")
print(f"Fetched {len(items)} headlines")

scored = score_headlines([i["title"] for i in items])
for s in scored:
    print(f'{s["label"]:>8}  {s["score"]:+.2f}  {s["title"]}')

print(aggregate_sentiment(scored))
