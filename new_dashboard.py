# Save this as banknifty_dashboard.py

import yfinance as yf
import pandas as pd
import streamlit as st
import ta
from datetime import datetime, timedelta

# --------- Parameters ---------
symbol = "^NSEBANK"  # Bank Nifty Index
timeframes = {"5m": "5m", "15m": "15m", "1h": "60m"}
lookback_period = "7d"

# --------- Functions ---------
@st.cache_data(ttl=3600)
def get_data(interval):
    data = yf.download(symbol, period=lookback_period, interval=interval)
    return data.dropna()

def add_technical_indicators(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
    df["macd"] = ta.trend.MACD(df["Close"]).macd_diff()
    df["ema_20"] = ta.trend.EMAIndicator(df["Close"], window=20).ema_indicator().values.flatten()
    df["ema_signal"] = df["Close"] > df["ema_20"]
    return df

def generate_signal(row):
    if row["rsi"] < 30 and row["macd"] > 0 and row["ema_signal"]:
        return "Buy"
    elif row["rsi"] > 70 and row["macd"] < 0 and not row["ema_signal"]:
        return "Sell"
    else:
        return "Hold"

def dummy_fundamental_sentiment_score():
    # Placeholder: 1 means bullish, -1 bearish
    return 1  # Assume bullish based on simple FII/DII or global cues

def accuracy_tracking(df):
    df["Signal"] = df.apply(generate_signal, axis=1)
    df["Future Close"] = df["Close"].shift(-2)
    df["Accuracy"] = ((df["Signal"] == "Buy") & (df["Future Close"] > df["Close"])) | \
                     ((df["Signal"] == "Sell") & (df["Future Close"] < df["Close"]))
    acc = df["Accuracy"].mean()
    return df, round(acc * 100, 2)

# --------- Streamlit UI ---------
st.set_page_config("Bank Nifty Signal Dashboard", layout="wide")
st.title("📊 Bank Nifty Signal Dashboard")

for label, interval in timeframes.items():
    st.subheader(f"⏱ Timeframe: {label}")
    data = get_data(interval)
    data = add_technical_indicators(data)
    score = dummy_fundamental_sentiment_score()
    
    # Adjust signal based on sentiment
    data["Signal"] = data.apply(generate_signal, axis=1)
    if score == 1:
        data.loc[data["Signal"] == "Hold", "Signal"] = "Buy"
    elif score == -1:
        data.loc[data["Signal"] == "Hold", "Signal"] = "Sell"

    # Signal & accuracy
    data, acc = accuracy_tracking(data)
    
    # Display
    st.write(f"✅ Signal Accuracy (historical): **{acc}%**")
    st.dataframe(data[["Close", "rsi", "macd", "Signal"]].tail(10))
