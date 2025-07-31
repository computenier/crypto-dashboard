import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(layout="wide", page_title="Crypto Global Dashboard", page_icon="📊")

# --- Fetch Global Stats ---
@st.cache_data(ttl=600)
def get_global_data():
    url = "https://api.coingecko.com/api/v3/global"
    response = requests.get(url).json()
    return response['data']

@st.cache_data(ttl=600)
def get_btc_market_cap(days=7):
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
    response = requests.get(url).json()
    return response['market_caps']

# --- Format numbers ---
def format_number(n):
    if n >= 1e12:
        return f"${n / 1e12:.2f}T"
    elif n >= 1e9:
        return f"${n / 1e9:.2f}B"
    else:
        return f"${n:,.2f}"

# --- Main App ---
st.title("📊 Global Crypto Dashboard")

data = get_global_data()
market_cap = data['total_market_cap']['usd']
volume = data['total_volume']['usd']
btc_dominance = data['market_cap_percentage']['btc']
eth_dominance = data['market_cap_percentage']['eth']
others = 100 - btc_dominance - eth_dominance

col1, col2, col3 = st.columns(3)
col1.metric("🌐 Global Market Cap", format_number(market_cap))
col2.metric("💸 24H Volume", format_number(volume))
col3.metric("📈 BTC Dominance", f"{btc_dominance:.2f}%")

# --- Chart: Bitcoin Market Cap Trend ---
st.subheader("📈 Bitcoin Market Cap (Last 7 Days)")
btc_chart = get_btc_market_cap(days=7)
df_btc = pd.DataFrame(btc_chart, columns=["timestamp", "market_cap"])
df_btc["timestamp"] = pd.to_datetime(df_btc["timestamp"], unit="ms")
df_btc.set_index("timestamp", inplace=True)
st.line_chart(df_btc["market_cap"])

# --- Chart: Market Dominance ---
st.subheader("📊 Market Dominance")

# Filter options
filter_option = st.selectbox("Select filter", [
    "BTC vs ETH vs Others",
    "BTC vs Altcoins (excluding top 5)"
])

if filter_option == "BTC vs ETH vs Others":
    labels = ["BTC", "ETH", "Others"]
    values = [btc_dominance, eth_dominance, others]
else:
    top_5_ids = ["bitcoin", "ethereum", "tether", "bnb", "solana"]
    coin_data = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
    ).json()

    altcoins = [c for c in coin_data if c['id'] not in top_5_ids]
    alt_dominance = sum(c['market_cap'] for c in altcoins) / market_cap * 100
    labels = ["BTC", "Altcoins (excl. Top 5)"]
    values = [btc_dominance, alt_dominance]

fig, ax = plt.subplots()
ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
ax.axis('equal')
st.pyplot(fig)
