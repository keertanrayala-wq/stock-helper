import pandas as pd
import streamlit as st

from src.charts import candlestick_chart
from src.data import get_price_history
from src.explain import explain_macd, explain_rsi, explain_trend
from src.news import clean_headlines, fetch_headlines, get_company_name
from src.sentiment import (
    aggregate_sentiment,
    describe_sentiment,
    is_available,
    score_headlines,
)
from src.summary import summarize

st.set_page_config(page_title="Stock Helper", layout="wide")
st.title("Stock Helper")
st.caption("Educational only. This is not financial advice.")


@st.cache_data(ttl=900)
def load(ticker: str, period: str):
    return get_price_history(ticker, period)


@st.cache_data(ttl=1800, show_spinner="Reading the news...")
def load_news(ticker: str):
    items = clean_headlines(fetch_headlines(ticker))
    scored = None
    if items and is_available():
        scored = score_headlines([i["title"] for i in items])
    return items, scored


def fmt(value, prefix=""):
    return "n/a" if value is None else f"{prefix}{value:,.2f}"


col_a, col_b = st.columns([2, 1])
ticker = col_a.text_input(
    "Ticker (e.g. TCS.NS, INFY.NS, RELIANCE.NS, AAPL)", "TCS.NS"
).strip().upper()
period = col_b.selectbox("Time range", ["3mo", "6mo", "1y", "2y", "5y"], index=2)

if ticker:
    try:
        df = load(ticker, period)
    except Exception:
        st.error(f"Could not find data for '{ticker}'. Check the ticker and try again.")
        st.stop()

    s = summarize(df.tail(252), ticker)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Last close", fmt(s["last_close"]), f'{fmt(s["change_1d_pct"])}% today')
    m2.metric("52-week high", fmt(s["high_52w"]))
    m3.metric("52-week low", fmt(s["low_52w"]))
    m4.metric("RSI (14)", fmt(s["rsi_14"]))

    st.plotly_chart(candlestick_chart(df, ticker), use_container_width=True)

    st.subheader("What the indicators say")
    st.write(explain_rsi(s["rsi_14"]))
    st.write(explain_macd(s["macd"], s["macd_signal"]))
    st.write(explain_trend(s["last_close"], s["sma_50"], s["sma_200"]))

    st.subheader("Recent news")
    name = get_company_name(ticker)
    if name:
        st.caption(f"Searching news for: {name}")

    items, scored = load_news(ticker)
    if not items:
        st.info("No recent headlines found for this stock.")
    else:
        if scored is not None:
            summary_s = aggregate_sentiment(scored)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("News sentiment", describe_sentiment(summary_s))
            c2.metric("Positive", summary_s["positive"])
            c3.metric("Neutral", summary_s["neutral"])
            c4.metric("Negative", summary_s["negative"])
            rows = [
                {
                    "Sentiment": sc["label"],
                    "Score": sc["score"],
                    "Headline": it["title"],
                    "Source": it["source"],
                }
                for it, sc in zip(items, scored)
            ]
            st.caption(
                "Scores come from FinBERT, a financial-text model. "
                "They are noisy and are not a prediction."
            )
        else:
            rows = [{"Headline": it["title"], "Source": it["source"]} for it in items]
            st.caption(
                "Sentiment scoring is not available in this deployment, "
                "so only headlines are shown."
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
