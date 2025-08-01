import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime
import random
from pytrends.request import TrendReq
import numpy as np

st.set_page_config(page_title="Crypto Dashboard", layout="wide")

# CSS Styling
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-family: "-apple-system", "system-ui", "Segoe UI", Roboto, sans-serif;
    }
    .metric-container {
        padding: 1.5rem;
        background: #f8f9fa;
        border-radius: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        text-align: center;
    }
    .section-header {
        font-size: 1.4rem;
        font-weight: 600;
        padding: 1rem 0 0.5rem;
        color: #222;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------- Data Functions -------------------
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

def get_flex_sentiment():
    flex_levels = [
        {"label": "Low Flex", "emoji": "🧢", "color": "gray"},
        {"label": "Mild Flex", "emoji": "🕶️", "color": "blue"},
        {"label": "Crypto Bros Warming Up", "emoji": "⌚", "color": "orange"},
        {"label": "Lambo Watch Out", "emoji": "🚗", "color": "red"},
        {"label": "Full Degens Activated", "emoji": "🛥️", "color": "purple"},
    ]
    return random.choice(flex_levels)

# ------------------- Format Helpers -------------------
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

fg_data = get_fear_greed_index()
fg_value = int(fg_data["value"])
fg_label = fg_data["value_classification"]
fg_color = get_fg_color(fg_label)

flex = get_flex_sentiment()

# ------------------- Header Section -------------------
st.markdown("<h1 style='margin-bottom: 1rem;'>🌐 Crypto Market Overview</h1>", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)
col1.markdown(f"""
    <div class='metric-container'>
    <h3>Market Cap</h3><p>{format_number(market_cap)}</p>
    </div>
""", unsafe_allow_html=True)

col2.markdown(f"""
    <div class='metric-container'>
    <h3>24H Volume</h3><p>{format_number(volume)}</p>
    </div>
""", unsafe_allow_html=True)

col3.markdown(f"""
    <div class='metric-container'>
    <h3>BTC Dominance</h3><p>{btc_dominance:.2f}%</p>
    </div>
""", unsafe_allow_html=True)

col4.markdown(f"""
    <div class='metric-container'>
    <h3>Fear & Greed</h3><p style='color:{fg_color}; font-weight:bold'>{fg_value} – {fg_label}</p>
    </div>
""", unsafe_allow_html=True)

col5.markdown(f"""
    <div class='metric-container'>
    <h3>Flex Meter</h3><p style='color:{flex['color']}; font-weight:bold'>{flex['emoji']} {flex['label']}</p>
    </div>
""", unsafe_allow_html=True)

# ------------------- Global Market Cap Chart -------------------
st.markdown("<div class='section-header'>📈 Estimated Global Market Cap</div>", unsafe_allow_html=True)
time_ranges = {
    "24H": "1", "7D": "7", "14D": "14", "1M": "30", "3M": "90", "1Y": "365", "All": "max"
}
days = time_ranges[st.selectbox("Time range:", list(time_ranges.keys()), index=1)]

btc_caps = get_btc_market_cap(days)
btc_dominance_fraction = btc_dominance / 100
global_caps = [[t, btc / btc_dominance_fraction] for t, btc in btc_caps]
df_global = pd.DataFrame(global_caps, columns=["timestamp", "global_market_cap"])
df_global["timestamp"] = pd.to_datetime(df_global["timestamp"], unit="ms")
df_global.set_index("timestamp", inplace=True)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(df_global.index, df_global["global_market_cap"], color='#007aff', linewidth=2.5)
ax.set_title("Estimated Global Market Cap", fontsize=16, fontweight='bold')
ax.set_ylabel("USD")

# Dynamic range based on data, not starting from 0
y_min = max(2e12, df_global["global_market_cap"].min() * 0.95)
y_max = df_global["global_market_cap"].max() * 1.05
ax.set_ylim(y_min, y_max)

formatter = ticker.FuncFormatter(lambda x, _: f"${x/1e12:.1f}T")
ax.yaxis.set_major_formatter(formatter)
ax.grid(True, linestyle='--', alpha=0.3)
fig.autofmt_xdate()
st.pyplot(fig)

# ------------------- Rolex Google Trends -------------------
st.markdown("<div class='section-header'>💎 Rolex Crypto (Google Trends)</div>", unsafe_allow_html=True)
try:
    pytrends = TrendReq(hl='en-US', tz=360)
    pytrends.build_payload(["Rolex Crypto"], timeframe='now 7-d')
    df_trend = pytrends.interest_over_time().drop(columns=['isPartial'])
    st.line_chart(df_trend)
except Exception as e:
    st.warning("⚠️ Could not fetch Google Trends data.")
    st.text(str(e))

# ------------------- Market Dominance Pie Chart -------------------
st.markdown("<div class='section-header'>📊 Market Dominance Comparison</div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**BTC vs ETH vs Others**")
    labels_1 = ["BTC", "ETH", "Others"]
    values_1 = [btc_dominance, eth_dominance, others]
    fig1, ax1 = plt.subplots()
    ax1.pie(values_1, labels=labels_1, autopct="%1.1f%%", startangle=90)
    ax1.axis("equal")
    st.pyplot(fig1)

with col2:
    st.markdown("**BTC vs Altcoins (excluding Top 5)**")
    top_5_ids = ["bitcoin", "ethereum", "tether", "bnb", "solana"]
    coin_data = get_top_market_data()
    altcoins = [c for c in coin_data if c["id"] not in top_5_ids]
    alt_dominance = sum(c["market_cap"] for c in altcoins) / market_cap * 100
    labels_2 = ["BTC", "Altcoins (excl. Top 5)"]
    values_2 = [btc_dominance, alt_dominance]
    fig2, ax2 = plt.subplots()
    ax2.pie(values_2, labels=labels_2, autopct="%1.1f%%", startangle=90)
    ax2.axis("equal")
    st.pyplot(fig2)

# ------------------- Technical Indicator Gauge + Sentiment -------------------

import streamlit as st
import requests
import matplotlib.pyplot as plt
import pandas as pd
from tradingview_ta import TA_Handler, Interval
from collections import Counter

st.markdown("<div class='section-header'>📉 TradingView Technical Sentiment</div>", unsafe_allow_html=True)

# Map human labels to TradingView TA interval enums
interval_map = {
    "1h": Interval.INTERVAL_1_HOUR,
    "4h": Interval.INTERVAL_4_HOURS,
    "1d": Interval.INTERVAL_1_DAY,
    "7d": Interval.INTERVAL_1_WEEK,
    "1mo": Interval.INTERVAL_1_MONTH
}

# Timeframe selection (sorted from short to long)
ordered_intervals = ["1h", "4h", "1d", "7d", "1mo"]
selected_interval = st.selectbox("Select timeframe", ordered_intervals, index=2)
selected_tv_interval = interval_map[selected_interval]

@st.cache_data(ttl=600)
def get_sentiment(symbol, exchange, interval):
    handler = TA_Handler(
        symbol=symbol,
        screener="crypto",
        exchange=exchange,
        interval=interval
    )
    try:
        analysis = handler.get_analysis()
        return {
            "summary": analysis.summary["RECOMMENDATION"],
            "oscillators": analysis.oscillators["RECOMMENDATION"],
            "ma": analysis.moving_averages["RECOMMENDATION"]
        }
    except Exception as e:
        return {
            "summary": "N/A",
            "oscillators": "N/A",
            "ma": "N/A"
        }

@st.cache_data(ttl=600)
def get_average_sentiment(symbol, exchange):
    votes = []
    for intv in ordered_intervals:
        tv_intv = interval_map[intv]
        s = get_sentiment(symbol, exchange, tv_intv)["summary"]
        if s != "N/A":
            votes.append(s)
    if votes:
        most_common = Counter(votes).most_common(1)[0][0]
        return most_common
    return "N/A"

# Binance Long/Short Sentiment
@st.cache_data(ttl=600)
def get_binance_long_short_ratio(symbol="BTCUSDT"):
    url = f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol={symbol}&period=5m&limit=1"
    try:
        response = requests.get(url).json()
        if response:
            long_ratio = float(response[0]["longAccountRatio"])
            short_ratio = float(response[0]["shortAccountRatio"])
            return long_ratio, short_ratio
    except:
        return None, None

# Define coins and exchange
assets = [
    {"label": "BTC/USD", "symbol": "BTCUSD", "exchange": "COINBASE"},
    {"label": "ETH/USD", "symbol": "ETHUSD", "exchange": "COINBASE"},
    {"label": "SOL/USD", "symbol": "SOLUSD", "exchange": "COINBASE"},
    {"label": "XRP/USD", "symbol": "XRPUSD", "exchange": "COINBASE"}
]

# Gauge rendering function
def draw_gauge(title, value):
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.text(5, 6.5, title, ha="center", fontsize=12, weight="bold")
    color = "red" if value == "SELL" or value == "STRONG_SELL" else ("green" if value == "BUY" or value == "STRONG_BUY" else "orange")
    ax.text(5, 5, value.replace("_", " "), ha="center", fontsize=16, color=color)
    ax.add_patch(plt.Circle((5, 2), 1.5, color=color, alpha=0.2))
    return fig

# Display gauges per asset
for asset in assets:
    st.subheader(f"📊 {asset['label']} ({selected_interval})")
    sentiment = get_sentiment(asset["symbol"], asset["exchange"], selected_tv_interval)
    avg_signal = get_average_sentiment(asset["symbol"], asset["exchange"])
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.pyplot(draw_gauge("Summary", sentiment["summary"]))
    with col2:
        st.pyplot(draw_gauge("Oscillators", sentiment["oscillators"]))
    with col3:
        st.pyplot(draw_gauge("Moving Averages", sentiment["ma"]))
    with col4:
        st.pyplot(draw_gauge("Avg Signal", avg_signal))

# Binance Long/Short Sentiment Card
st.markdown("<div class='section-header'>🧭 Binance Trader Sentiment</div>", unsafe_allow_html=True)
long_ratio, short_ratio = get_binance_long_short_ratio()
if long_ratio is not None:
    st.metric("📈 Long Ratio", f"{long_ratio*100:.1f}%")
    st.metric("📉 Short Ratio", f"{short_ratio*100:.1f}%")
else:
    st.warning("Unable to fetch Binance sentiment ratio.")
