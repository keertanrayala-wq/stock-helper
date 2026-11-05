from src.data import get_price_history
from src.indicators import rsi, sma

df = get_price_history("TCS.NS")
df["SMA50"] = sma(df["Close"], 50)
df["RSI"] = rsi(df["Close"])
print(df.tail())
