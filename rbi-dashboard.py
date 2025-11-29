# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime
from io import BytesIO
import fpdf

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="RBI Macro Dashboard", layout="wide", page_icon="🏦")
st.markdown("<h1 style='text-align:center;color:#0B63A8;'>RBI Macro Economic Dashboard</h1>", unsafe_allow_html=True)
st.markdown("### A professional dashboard for Inflation • Riskometer • Monetary Policy • Liquidity (India + US)")

# -------------------- SIDEBAR NAVIGATION --------------------
menu = st.sidebar.radio("Navigation", [
    "Inflation (India + US)",
    "Riskometer",
    "Monetary Policy Impact",
    "Liquidity Data (India + US)",
    "PDF Report"
])

# -------------------- FRED API --------------------
FRED_API_KEY = st.secrets.get("fred_api_key")  # Must be set in Streamlit secrets

def get_fred(series_id):
    """Fetch data from FRED API safely"""
    if not FRED_API_KEY:
        st.error("⚠ FRED API key missing. Set `fred_api_key` in Streamlit secrets.")
        return pd.DataFrame(columns=["date","value"])
    
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {"series_id": series_id, "api_key": FRED_API_KEY, "file_type":"json"}
    
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()["observations"]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        return df[["date","value"]]
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Error fetching {series_id}: {e}")
        return pd.DataFrame(columns=["date","value"])
    except Exception as e:
        st.error(f"Unexpected error fetching {series_id}: {e}")
        return pd.DataFrame(columns=["date","value"])

# -------------------- INDIA CPI --------------------
def india_cpi():
    try:
        url = "https://api.worldbank.org/v2/country/IN/indicator/FP.CPI.TOTL?format=json&per_page=500"
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()[1]
        if not data:
            st.warning("No India CPI data returned.")
            return pd.DataFrame(columns=["date","value"])
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"], format="%Y", errors="coerce")
        df = df.dropna(subset=["value","date"]).sort_values("date")
        return df[["date","value"]]
    except Exception as e:
        st.error(f"Error fetching India CPI: {e}")
        return pd.DataFrame(columns=["date","value"])

# -------------------- PAGE 1: INFLATION --------------------
if menu == "Inflation (India + US)":
    st.header("📌 Inflation Dashboard")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🇺🇸 US CPI (Live FRED)")
        us_df = get_fred("CPIAUCSL")
        if not us_df.empty:
            st.line_chart(us_df.set_index("date"))
            st.metric("Latest US CPI", f"{us_df['value'].iloc[-1]:.2f}")

    with col2:
        st.subheader("🇮🇳 India CPI (World Bank)")
        ind_df = india_cpi()
        if not ind_df.empty:
            st.line_chart(ind_df.set_index("date"))
            st.metric("Latest India CPI", f"{ind_df['value'].iloc[-1]:.2f}")

    st.subheader("🧮 Inflation Calculator")
    initial = st.number_input("Initial Price", value=100.0)
    inflation = st.number_input("Inflation Rate (%)", value=6.0)
    years = st.number_input("Years", value=5, min_value=1)
    future_price = initial * ((1 + inflation/100) ** years)
    st.success(f"Future Price after {years} years → ₹{future_price:.2f}")

# -------------------- PAGE 2: RISKOMETER --------------------
if menu == "Riskometer":
    st.header("📌 Portfolio Riskometer")
    eq = st.slider("Equity (%)", 0, 100, 40)
    debt = st.slider("Debt (%)", 0, 100, 40)
    gold = st.slider("Gold/Commodities (%)", 0, 100, 20)

    total = eq + debt + gold
    if total != 100:
        st.error(f"Allocation must sum to 100%. Current sum: {total}%")
        risk_score = 0
    else:
        risk_score = eq*0.7 + gold*0.2 + debt*0.1

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        title={"text":"Portfolio Risk Score (0-100)"},
        gauge={
            "axis":{"range":[0,100]},
            "steps":[{"range":[0,30],"color":"lightgreen"},{"range":[30,60],"color":"yellow"},{"range":[60,100],"color":"red"}],
            "bar":{"color":"darkblue"},
            "threshold":{"value":risk_score,"line":{"color":"red","width":4}}
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

    if risk_score < 30:
        st.success(f"Score: {risk_score:.1f} → LOW RISK")
    elif risk_score < 60:
        st.warning(f"Score: {risk_score:.1f} → MODERATE RISK")
    else:
        st.error(f"Score: {risk_score:.1f} → HIGH RISK")

# -------------------- PAGE 3: MONETARY POLICY IMPACT --------------------
if menu == "Monetary Policy Impact":
    st.header("📌 Monetary Policy Risk Analysis")
    st.subheader("📈 Risks when Interest Rates Increase")
    st.write("- Borrowing cost rises\n- GDP growth slows\n- Bond prices fall\n- Stock market correction\n- EM currency depreciation")
    st.subheader("💧 Risks when Liquidity Increases")
    st.write("- Inflation rises\n- Asset bubble risk\n- Currency weakens\n- Excessive credit growth")
    st.subheader("🔥 Risks when Inflation Rises")
    st.write("- Purchasing power falls\n- Corporate margins shrink\n- Monetary tightening expected")
    st.subheader("🇺🇸 Risks when US CPI Rises")
    st.write("- USD strengthens\n- FPI outflows from India\n- RBI may be forced to hike")

# -------------------- PAGE 4: LIQUIDITY --------------------
if menu == "Liquidity Data (India + US)":
    st.header("📌 Liquidity (India + US)")
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("🇺🇸 US Fed Balance Sheet (WALCL)")
        fed_df = get_fred("WALCL")
        if not fed_df.empty:
            st.line_chart(fed_df.set_index("date"))
            latest_val = fed_df["value"].iloc[-1]/1e6
            st.metric("Latest Fed Balance Sheet (Trillion $)", f"${latest_val:.2f}")

    with col4:
        st.subheader("🇮🇳 India Liquidity — Upload CSV")
        file = st.file_uploader("Upload CSV with 'date' & 'value' columns", type=['csv'])
        if file:
            try:
                df = pd.read_csv(file)
                df.columns = [c.lower() for c in df.columns]
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                df = df.dropna(subset=['date','value'])
                st.line_chart(df.set_index("date"))
                st.metric("Latest India Liquidity", f"₹{df['value'].iloc[-1]:,.2f}")
            except Exception as e:
                st.error(f"CSV parsing error: {e}")

