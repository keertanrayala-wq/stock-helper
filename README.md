# Stock Helper

A beginner-friendly stock assistant that shows price charts, technical indicators, and plain-English explanations of what they mean.

**Live demo:** https://why-did-it-move.streamlit.app

> Educational only. This is not financial advice.

## Features
- Candlestick charts with 50 and 200-day moving averages
- RSI, MACD, and trend indicators with plain-English explanations
- Works with Indian (NSE, e.g. `TCS.NS`) and global tickers

## Run locally
    git clone https://github.com/keertanrayala-wq/stock-helper.git
    cd stock-helper
    python3.12 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    streamlit run app.py

## Roadmap
- News headlines and sentiment analysis (FinBERT)
- AI chat assistant that answers questions using real data
- "Explain the move" feature
- Accuracy scoreboard for the sentiment signals
