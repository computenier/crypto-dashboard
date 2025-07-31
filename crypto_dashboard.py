import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(layout="wide", page_title="Crypto Global Dashboard", page_icon="📊")

# ------------------- API Functions -------------------

@st.cache_data(ttl=600)
def get_global_data():
    url = "https://api.coingecko.com/api/v3/global"
    return requests.get(url).json()["data"]

@st.cache_data(ttl=600)
def get_btc_market_cap(days="7"):
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
    response = requests.get(url).json()
    return response["market_caps"]

@st.cache_data(ttl=600)
def get_top_market_data():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
    return requests.get(url).json()

# ------------------- Helpers -------------------

def format_number(n):
    if n >= 1e12:
        return f"${n / 1e12:.2f}T"
    elif n >= 1e9:
        return f"${n / 1e9:.2f}B"
    else:
        return f"${n:,.2f}"

# ------------------- Load Data -------------------

global_data = get_global_data()
market_cap = global_data["total_market_cap"]["usd"]
volume = global_data["total_volume"]["usd"]
btc_dominance = global_data["market_cap_percentage"]["btc"]
eth_dominance = global_data["market_cap_percentage"]["eth"]
others = 100 - btc_dominance - eth_dominance

# ------------------- Header Stats -------------------

st.title("📊 Global Crypto Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("🌐 Global Market Cap", format_number(market_cap))
col2.metric("💸 24H Volume", format_number(volume))
col3.metric("📈 BTC Dominance", f"{btc_dominance:.2f}%")

# ------------------- Global Market Cap Chart -------------------

st.subheader("📈 Estimated Global Market Cap Over Time")

time_ranges = {
    "24H": "1",
    "7D": "7",
    "14D": "14",
    "1M": "30",
    "3M": "90",
    "1Y": "365",
    "All": "max"
}
selected_range = st.selectbox("Select time range:", list(time_ranges.keys()))
days = time_ranges[selected_range]

btc_caps = get_btc_market_cap(days)
btc_dominance_fraction = btc_dominance / 100

# Estimate global market cap using BTC dominance
global_caps = [[t, btc / btc_dominance_fraction] for t, btc in btc_caps]
df_global = pd.DataFrame(global_caps, columns=["timestamp", "global_market_cap"])
df_global["timestamp"] = pd.to_datetime(df_global["timestamp"], unit="ms")
df_global.set_index("timestamp", inplace=True)

# Show chart with grid from $2T to $5T
st.line_chart(df_global["global_market_cap"])

st.caption("🧮 Global market cap is estimated from BTC market cap and current BTC dominance.")

# ------------------- Market Dominance Pie Chart -------------------

st.subheader("📊 Market Dominance Breakdown")

filter_option = st.selectbox("Select filter", [
    "BTC vs ETH vs Others",
    "BTC vs Altcoins (excluding top 5)"
])

if filter_option == "BTC vs ETH vs Others":
    labels = ["BTC", "ETH", "Others"]
    values = [btc_dominance, eth_dominance, others]
else:
    top_5_ids = ["bitcoin", "ethereum", "tether", "bnb", "solana"]
    coin_data = get_top_market_data()
    altcoins = [c for c in coin_data if c["id"] not in top_5_ids]
    alt_dominance = sum(c["market_cap"] for c in altcoins) / market_cap * 100
    labels = ["BTC", "Altcoins (excl. Top 5)"]
    values = [btc_dominance, alt_dominance]

fig, ax = plt.subplots()
ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
ax.axis("equal")
st.pyplot(fig)
