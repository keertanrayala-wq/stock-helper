import streamlit as st

from src.charts import candlestick_chart
from src.data import get_price_history
from src.explain import explain_macd, explain_rsi, explain_trend
from src.summary import summarize

st.set_page_config(page_title="Stock Helper", layout="wide")
st.title("Stock Helper")
st.caption("Educational only. This is not financial advice.")


@st.cache_data(ttl=900)
def load(ticker: str, period: str):
    return get_price_history(ticker, period)


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
