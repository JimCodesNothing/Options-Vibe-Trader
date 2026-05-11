import streamlit as st
import yfinance as yf
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
import pandas as pd
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Options Vibe Trader", layout="wide")
st.title("🚀 Options Vibe Trader")
st.markdown("**Yahoo Finance + Alpaca Paper Trading**")

# Sidebar
ticker = st.sidebar.text_input("Stock Ticker", value="AAPL").upper()
st.sidebar.warning("📌 Running in Paper Trading Mode")

# Alpaca Client
@st.cache_resource
def get_trading_client():
    return TradingClient(
        os.getenv("ALPACA_API_KEY"),
        os.getenv("ALPACA_SECRET_KEY"),
        paper=True
    )

trading_client = get_trading_client()

# Fetch Data
@st.cache_data(ttl=30)
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    return stock, stock.info, stock.history(period="1mo"), stock.options

stock, info, hist, options_dates = get_stock_data(ticker)

# Dashboard
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Current Price", f"${info.get('currentPrice', 'N/A')}")
with col2:
    st.metric("Change %", f"{info.get('regularMarketChangePercent', 0):.2f}%")
with col3:
    st.metric("Volume", f"{info.get('volume', 0):,}")

# Price Chart
fig = go.Figure(data=[go.Candlestick(x=hist.index,
                open=hist['Open'], high=hist['High'],
                low=hist['Low'], close=hist['Close'])])
st.plotly_chart(fig, use_container_width=True)

# Options Chain
if options_dates:
    expiry = st.selectbox("Select Expiration", options_dates)
    chain = stock.option_chain(expiry)
    
    tab1, tab2 = st.tabs(["📈 Calls", "📉 Puts"])
    with tab1:
        st.dataframe(chain.calls[['contractSymbol', 'strike', 'lastPrice', 'bid', 'ask', 
                                 'volume', 'openInterest', 'impliedVolatility']].head(20), 
                    use_container_width=True)
    with tab2:
        st.dataframe(chain.puts[['contractSymbol', 'strike', 'lastPrice', 'bid', 'ask', 
                                'volume', 'openInterest', 'impliedVolatility']].head(20), 
                    use_container_width=True)

# Quick Trade
st.subheader("Quick Option Trade")
contract = st.text_input("Option Contract Symbol (e.g. AAPL250516C00250000)")
side = st.radio("Side", ["Buy", "Sell"])
qty = st.number_input("Quantity", min_value=1, value=1)

if st.button("🚀 Place Market Order", type="primary"):
    if contract and os.getenv("ALPACA_API_KEY"):
        try:
            order = MarketOrderRequest(
                symbol=contract,
                qty=qty,
                side=OrderSide.BUY if side == "Buy" else OrderSide.SELL,
                type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY
            )
            submitted = trading_client.submit_order(order)
            st.success(f"✅ Order Submitted! ID: {submitted.id}")
        except Exception as e:
            st.error(f"❌ Order Failed: {e}")
    else:
        st.warning("Enter contract symbol and make sure API keys are set")
