import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime

# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------
st.set_page_config(page_title="RBI Macro Dashboard", layout="wide", page_icon="🏦")

st.markdown("<h1 style='text-align:center;color:#0B63A8;'>RBI Macro Economic Dashboard</h1>", unsafe_allow_html=True)
st.markdown("### A professional dashboard for Inflation • Riskometer • Monetary Policy • Liquidity (India + US)")

# Sidebar Navigation
menu = st.sidebar.radio("Navigation", [
    "Inflation (India + US)",
    "Riskometer",
    "Monetary Policy Impact",
    "Liquidity Data (India + US)",
    "PDF Report"
])

# ******************************************************************************************
# 1️⃣  LIVE US CPI DATA (FRED API)
# ******************************************************************************************

FRED_API_KEY = "INSERT_YOUR_FRED_API_KEY_HERE"   # <<<--- Replace this

def get_fred(series_id):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json"
    }
    r = requests.get(url, params=params)
    data = r.json()["observations"]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df[["date", "value"]]

# ******************************************************************************************
# 2️⃣  INDIA CPI (WORLD BANK API)
# ******************************************************************************************

def india_cpi():
    url = "https://api.worldbank.org/v2/country/IN/indicator/FP.CPI.TOTL?format=json&per_page=500"
    r = requests.get(url)
    data = r.json()[1]
    df = pd.DataFrame(data)
    df = df[["date", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df

# ******************************************************************************************
# PAGE 1 — INFLATION
# ******************************************************************************************

if menu == "Inflation (India + US)":
    st.header("📌 Inflation Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🇺🇸 US CPI (Live FRED)")
        try:
            us_df = get_fred("CPIAUCSL")
            st.line_chart(us_df.set_index("date"))
            st.metric("Latest US CPI", us_df["value"].iloc[-1])
        except:
            st.error("⚠ Unable to fetch US CPI. Check FRED API Key.")

    with col2:
        st.subheader("🇮🇳 India CPI (World Bank)")
        try:
            ind_df = india_cpi()
            st.line_chart(ind_df.set_index("date"))
            st.metric("Latest India CPI", ind_df["value"].iloc[-1])
        except:
            st.error("⚠ Unable to fetch India CPI.")

    st.subheader("🧮 Inflation Calculator")
    initial = st.number_input("Initial Price", value=100)
    inflation = st.number_input("Inflation Rate (%)", value=6.0)
    years = st.number_input("Years", value=5)

    future_price = initial * ((1 + inflation/100) ** years)
    st.success(f"Future Price after {years} years → ₹{future_price:.2f}")

# ******************************************************************************************
# PAGE 2 — RISKOMETER
# ******************************************************************************************

if menu == "Riskometer":
    st.header("📌 Portfolio Riskometer")

    eq = st.slider("Equity %", 0, 100, 40)
    debt = st.slider("Debt %", 0, 100, 40)
    gold = st.slider("Gold %", 0, 100, 20)

    risk_score = eq*0.7 + gold*0.2 + debt*0.1

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        title={"text": "Portfolio Risk Score"},
        gauge={"axis": {"range": [0, 100]}}
    ))

    st.plotly_chart(fig, use_container_width=True)

    if risk_score < 30:
        st.success("LOW RISK — Stable portfolio.")
    elif risk_score < 60:
        st.warning("MODERATE RISK — Balanced portfolio.")
    else:
        st.error("HIGH RISK — Risky portfolio for volatile markets.")

# ******************************************************************************************
# PAGE 3 — MONETARY POLICY IMPACT
# ******************************************************************************************

if menu == "Monetary Policy Impact":
    st.header("📌 Monetary Policy Risk Analysis")

    st.subheader("📈 Risks when Interest Rates Increase")
    st.write("""
    - Borrowing cost increases  
    - GDP growth slows  
    - Bond prices fall  
    - Stock market correction  
    - EM currency depreciation  
    """)

    st.subheader("💧 Risks when Liquidity Increases")
    st.write("""
    - Inflation rises  
    - Asset bubble risk  
    - Currency weakens  
    - Excessive credit growth  
    """)

    st.subheader("🔥 Risks when Inflation Rises")
    st.write("""
    - Purchasing power falls  
    - Corporate margins shrink  
    - Monetary tightening expected  
    """)

    st.subheader("🇺🇸 Risks when US CPI Rises")
    st.write("""
    - USD strengthens  
    - FPI outflows from India  
    - RBI may be forced to hike  
    """)

# ******************************************************************************************
# PAGE 4 — LIQUIDITY PAGE
# ******************************************************************************************

if menu == "Liquidity Data (India + US)":
    st.header("📌 Liquidity (India + US)")

    st.subheader("🇺🇸 US Federal Reserve Balance Sheet (FRED WALCL)")
    try:
        fed_df = get_fred("WALCL")
        st.line_chart(fed_df.set_index("date"))
        st.metric("Latest US Liquidity", fed_df["value"].iloc[-1])
    except:
        st.error("⚠ Cannot fetch US liquidity.")

    st.subheader("🇮🇳 India Liquidity — Upload CSV (LAF / Net Liquidity)")
    file = st.file_uploader("Upload India Liquidity CSV", type=['csv'])
    if file:
        df = pd.read_csv(file)
        try:
            df['date'] = pd.to_datetime(df['date'])
            st.line_chart(df.set_index("date"))
        except:
            st.error("Invalid CSV format")

# ******************************************************************************************
# PAGE 5 — PDF EXPORT
# ******************************************************************************************

if menu == "PDF Report":
    st.header("📄 Generate PDF Report")

    st.write("Click button to download report")

    import pdfkit
    from io import BytesIO

    if st.button("Generate PDF Report"):
        html = """
        <h1>RBI Macro Dashboard Report</h1>
        <p>This report includes inflation, monetary policy risks, and liquidity indicators.</p>
        <p>Prepared for RBI Summer Internship.</p>
        """
        pdf = pdfkit.from_string(html, False)
        st.download_button("Download PDF", data=pdf, file_name="rbi_report.pdf")
