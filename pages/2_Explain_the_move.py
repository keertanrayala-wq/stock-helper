from datetime import date, timedelta

import plotly.graph_objects as go
import streamlit as st

from src.move import get_move_evidence
from src.search import format_option, search_companies

st.set_page_config(page_title="Explain the move", layout="wide")
st.title("Explain the move")
st.caption(
    "See what coincided with a stock's move on a past trading day. "
    "Educational only. This is not financial advice."
)

LABEL_TEXT = {
    "mostly market-wide": "The stock moved with the broad market.",
    "mostly sector-wide": (
        "The stock moved together with its sector, and the broad market "
        "does not explain it."
    ),
    "mostly stock-specific": (
        "Neither the market nor the sector moved the same way by a similar "
        "amount, so company news is worth checking."
    ),
    "small move": "The move was small.",
}


@st.cache_data(ttl=3600)
def find_companies(query: str):
    return search_companies(query)


@st.cache_data(ttl=1800, show_spinner="Gathering the evidence...")
def load_evidence(ticker: str, day: date):
    return get_move_evidence(ticker, day)


def pct(value):
    return "n/a" if value is None else f"{value:+.2f}%"


col_a, col_b = st.columns([2, 1])
query = col_a.text_input(
    "Search a company name or ticker", "Tata Consultancy Services"
).strip()
day = col_b.date_input(
    "Trading day", value=date.today() - timedelta(days=1), max_value=date.today()
)

ticker = ""
if query:
    matches = find_companies(query)
    if matches:
        labels = {format_option(m): m["symbol"] for m in matches}
        choice = st.selectbox("Pick the company", list(labels))
        ticker = labels[choice]
    else:
        ticker = query.upper().replace(" ", "")
        st.caption(f"No search matches, trying '{ticker}' as a ticker.")

if ticker and st.button("Explain the move"):
    try:
        ev = load_evidence(ticker, day)
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    st.subheader(ev["classification"].capitalize())
    st.write(LABEL_TEXT.get(ev["classification"], "There is not enough data to compare."))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(ticker, pct(ev["change_pct"]))
    c2.metric(f'Market ({ev["benchmark"] or "none"})', pct(ev["benchmark_change_pct"]))
    c3.metric(f'Sector ({ev["sector_index"] or "none"})', pct(ev["sector_change_pct"]))
    vr = ev["volume_ratio"]
    c4.metric("Volume vs 20-day average", "n/a" if vr is None else f"{vr:.2f}x")

    names, values = ["Stock"], [ev["change_pct"]]
    if ev["benchmark_change_pct"] is not None:
        names.append("Market")
        values.append(ev["benchmark_change_pct"])
    if ev["sector_change_pct"] is not None:
        names.append("Sector")
        values.append(ev["sector_change_pct"])
    fig = go.Figure(go.Bar(x=names, y=values, text=[f"{v:+.2f}%" for v in values]))
    fig.update_layout(yaxis_title="Change on the day (%)", height=320)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Headlines around that day")
    if ev["headlines"]:
        for h in ev["headlines"]:
            title = h["title"].replace("[", "(").replace("]", ")").replace("$", "\\$")
            st.markdown(f"- [{title}]({h['link']})")
    else:
        st.write("No headlines found for that window.")
    st.caption(
        "Headlines come from a short window around the date and may be unrelated "
        "to the move. What coincided with a move is not proof of what caused it."
    )