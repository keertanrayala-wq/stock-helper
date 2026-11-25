import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Does news sentiment predict returns?", layout="wide")
st.title("Does news sentiment predict returns?")
st.caption("Educational only. This is not financial advice.")

RESULTS = Path("results/scoreboard_v2.json")
if not RESULTS.exists():
    st.error("Results file not found. Run analyze_v2.py to create it.")
    st.stop()

r = json.loads(RESULTS.read_text())
ic = r["daily_ic"]["ex_1d"]
ic5 = r["daily_ic"]["ex_5d"]
perm = r.get("permutation_ex_1d")
if perm is None or ic["mean_ic"] is None:
    st.warning("The results file does not contain a complete test. Re-run analyze_v2.py.")
    st.stop()

st.write(
    "Does the mood of a company's news headlines tell us which stocks will do "
    "better than the market the next day? This page shows how we tested that, "
    "and what we found."
)

if perm["p_value"] < 0.05:
    st.warning(
        "The test found a pattern that is unlikely to be pure chance. Treat it "
        "with caution until it is confirmed on new data."
    )
else:
    st.success(
        "No detectable relationship. In this sample, news mood did not tell us "
        f"which stocks would beat the market the next day. The result "
        f"({ic['mean_ic']:+.3f}) sits inside the range that random shuffling produces."
    )

a, b, c, d = st.columns(4)
a.metric("Companies", r["companies"])
b.metric("Company-days", f"{r['observations']:,}")
c.metric("Trading dates", r["dates"])
d.metric("Data through", r["data_through"])

e, f, g, h = st.columns(4)
e.metric("Average daily correlation", f"{ic['mean_ic']:+.3f}")
f.metric(
    "Expected by chance",
    f"{perm['null_mean']:+.3f} \u00b1 {perm['null_sd']:.3f}",
)
g.metric("Chance of seeing this by luck", f"{perm['p_value']:.2f}")
h.metric("Days the signal pointed the right way", f"{ic['positive_days']} of {ic['days']}")

lim = max(0.1, 3 * perm["null_sd"], abs(perm["observed"]) * 1.5)
fig = go.Figure(
    go.Scatter(x=[0], y=[0], mode="markers", marker=dict(opacity=0),
               showlegend=False, hoverinfo="skip")
)
fig.add_vrect(
    x0=perm["null_mean"] - 2 * perm["null_sd"],
    x1=perm["null_mean"] + 2 * perm["null_sd"],
    fillcolor="rgba(150,150,150,0.35)",
    line_width=0,
    annotation_text="Range expected by chance",
    annotation_position="top left",
)
fig.add_vline(
    x=perm["observed"],
    line_width=3,
    line_color="crimson",
    annotation_text=f"Observed {perm['observed']:+.3f}",
    annotation_position="top right",
)
fig.update_layout(
    xaxis=dict(range=[-lim, lim], title="Average daily correlation (1 = perfect, 0 = none)"),
    yaxis=dict(visible=False),
    height=260,
    margin=dict(l=10, r=10, t=30, b=10),
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("In plain English")
st.write(
    f"Each day, we ranked {r['companies']} large Indian companies by the mood of "
    "their news headlines, then checked whether the more upbeat ones beat the "
    f"market (the Nifty 50) the next trading day. A score of 1.0 would mean the "
    f"ranking was perfect and 0 means no relationship. Ours averaged "
    f"{ic['mean_ic']:+.3f} over {ic['days']} days."
)
st.write(
    "To judge whether that is real, we shuffled the sentiment scores between "
    "companies many times and recomputed the same number. Shuffled data has no "
    f"real signal, and it averaged {perm['null_mean']:+.3f} with a spread of "
    f"{perm['null_sd']:.3f}. Our real result falls inside that range."
)
st.write(
    f"With this much data, a relationship stronger than roughly "
    f"{2 * perm['null_sd']:.2f} would probably have stood out. Weaker ones could "
    f"still be hidden. Over five trading days the average was "
    f"{ic5['mean_ic']:+.3f}, which is also close to zero."
)

with st.expander("How the test works"):
    st.markdown(
        "- **Headlines** come from Google News, scored by FinBERT (a model trained "
        "on financial text) as positive, negative, or neutral.\n"
        "- **Timing:** a headline published before the market close counts toward "
        "that day's signal, and one published after the close counts toward the "
        "next trading day. Returns are measured from the close, so no headline "
        "can know the outcome.\n"
        "- **Market-adjusted:** each stock's return has the Nifty 50's return "
        "subtracted, so we measure beating the market, not just rising with it.\n"
        "- **Main number:** the average, across days, of the rank correlation "
        "between companies' sentiment and their next-day market-adjusted return.\n"
        "- **Rules were fixed before we looked at any result.**"
    )

with st.expander("What this does not show"):
    st.markdown(
        "- About two months of data from one period.\n"
        "- Only 60 large, well-covered companies. Small or thinly covered stocks "
        "were not tested.\n"
        "- Stocks move together on any given day, so the company-days are not "
        "fully independent evidence.\n"
        "- The sentiment model misreads some headlines, and Google News is an "
        "incomplete source.\n"
        "- Only next-day and five-day horizons were tested.\n"
        "- Not finding a relationship is not proof that none exists."
    )

with st.expander("The first version of this test was wrong"):
    st.write(
        "Our first run looked impressive, with an average correlation of about "
        "0.11. We did not trust it, because five-day results showed nothing and "
        "real effects of that size are unusual. We checked the data and found that "
        "headlines from the next day were leaking into each day's sentiment, so "
        "the headlines were describing the very move we were trying to predict. "
        "After assigning each headline to the first market close after it was "
        "published, the result fell to the figures above. Checking for this kind "
        "of leak is a key step in testing any signal."
    )