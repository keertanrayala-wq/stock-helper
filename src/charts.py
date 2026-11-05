import pandas as pd
import plotly.graph_objects as go

from src.indicators import sma


def candlestick_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Candlestick chart with 50 and 200-day moving averages."""
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
        )
    )
    fig.add_trace(go.Scatter(x=df.index, y=sma(df["Close"], 50), name="SMA 50"))
    fig.add_trace(go.Scatter(x=df.index, y=sma(df["Close"], 200), name="SMA 200"))
    fig.update_layout(
        title=f"{ticker} price",
        xaxis_rangeslider_visible=False,
        yaxis_title="Price",
    )
    return fig
