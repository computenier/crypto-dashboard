import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime

st.set_page_config(layout="wide", page_title="Crypto Global Dashboard", page_icon="📊")

# ------------------- API Functions -------------------

@st.cache_data(ttl=600)
def get_global_data():
    return requests.get("https://api.coingecko.com/api/v3/global").json()["data"]

@st.cache_data(ttl=600)
def get_btc_market_cap(days="7"):
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
    return requests.get(url).json()["market_caps"]

@st.cache_data(ttl=600)
def get_top_market_data():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
    return requests.get(url).json()

@st.cache_data(ttl=300)
def get_fear_greed_index():
    url = "https://api.alternative.me/fng/"
    return requests.get(url).json()["data"][0]

# ------------------- Helpers -------------------

def format_number(n):
    if n >= 1e12:
        return f"${n / 1e12:.2f}T"
    elif n >= 1e9:
        return f"${n / 1e9:.2f}B"
    else:
        return f"${n:,.2f}"

def get_fg_color(label):
    return {
        "Extreme Fear": "red",
        "Fear": "orange",
        "Neutral": "gray",
        "Greed": "lightgreen",
        "Extreme Greed": "green"
    }.get(label, "gray")

# ------------------- Load Data -------------------

global_data = get_global_data()
market_cap = global_data["total_market_cap"]["usd"]
volume = global_data["total_volume"]["usd"]
btc_dominance = global_data["market_cap_percentage"]["btc"]
eth_dominance = global_data["market_cap_percentage"]["eth"]
others = 100 - btc_dominance - eth_dominance

fear_data = get_fear_greed_index()
fg_value = int(fear_data["value"])
fg_label = fear_data["value_classification"]
fg_color = get_fg_color(fg_label)

# ------------------- Header Section -------------------

st.title("📊 Global Crypto Dashboard")

col1, col2, col3, col4 = st.columns(4)
col1.metric("🌐 Global Market Cap", format_number(market_cap))
col2.metric("💸 24H Volume", format_number(volume))
col3.metric("📈 BTC Dominance", f"{btc_dominance:.2f}%")
col4.markdown(f"""
### 🧠 Fear & Greed Index  
<span style='font-size:32px; color:{fg_color}; font-weight:bold'>{fg_value} – {fg_label}</span>
""", unsafe_allow_html=True)

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
global_caps = [[t, btc / btc_dominance_fraction] for t, btc in btc_caps]
df_global = pd.DataFrame(global_caps, columns=["timestamp", "global_market_cap"])
df_global["timestamp"] = pd.to_datetime(df_global["timestamp"], unit="ms")
df_global.set_index("timestamp", inplace=True)

# Plot using matplotlib with fixed Y-axis from $2.5T to $5T
fig, ax = plt.subplots()
ax.plot(df_global.index, df_global["global_market_cap"], color='royalblue', linewidth=2)
ax.set_title("Estimated Global Market Cap", fontsize=14)
ax.set_ylabel("USD")
ax.set_ylim(2.5e12, 5e12)
formatter = ticker.FuncFormatter(lambda x, _: f"${x/1e12:.1f}T")
ax.yaxis.set_major_formatter(formatter)
ax.grid(True, linestyle='--', alpha=0.4)
fig.autofmt_xdate()
st.pyplot(fig)

st.caption("🧮 Global market cap is estimated from BTC market cap and BTC dominance.")

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
