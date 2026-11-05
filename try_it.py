from src.charts import candlestick_chart
from src.data import get_price_history
from src.summary import get_stock_summary

print(get_stock_summary("TCS.NS"))

df = get_price_history("TCS.NS")
candlestick_chart(df, "TCS.NS").show()
