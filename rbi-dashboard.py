import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime

# PAGE CONFIG
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

# -------------------- FRED API --------------------
FRED_API_KEY = "YOUR_FRED_API_KEY"  # Replace this

def get_fred(series_id):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json"
    }
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()["observations"]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=['value'])
        return df[["date", "value"]]
    except Exception as e:
        st.error(f"Error fetching {series_id}: {e}")
        return pd.DataFrame(columns=["date","value"])

# -------------------- India CPI --------------------
def india_cpi():
    try:
        url = "https://api.worldbank.org/v2/country/IN/indicator/FP.CPI.TOTL?format=json&per_page=500"
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()[1]
        df = pd.DataFrame(data)
        df = df[["date", "value"]]
        df["date"] = pd.to_datetime(df["date"], format='%Y')
        df = df.sort_values("date")
        df = df.dropna(subset=['value'])
        return df
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
            st.metric("Latest US CPI", us_df["value"].iloc[-1])
    
    with col2:
        st.subheader("🇮🇳 India CPI (World Bank)")
        ind_df = india_cpi()
        if not ind_df.empty:
            st.line_chart(ind_df.set_index("date"))
            st.metric("Latest India CPI", ind_df["value"].iloc[-1])

    st.subheader("🧮 Inflation Calculator")
    initial = st.number_input("Initial Price", value=100)
    inflation = st.number_input("Inflation Rate (%)", value=6.0)
    years = st.number_input("Years", value=5)
    future_price = initial * ((1 + inflation/100) ** years)
    st.success(f"Future Price after {years} years → ₹{future_price:.2f}")

# -------------------- PAGE 2: RISKOMETER --------------------
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

# -------------------- PAGE 3: MONETARY POLICY IMPACT --------------------
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

# -------------------- PAGE 4: LIQUIDITY --------------------
if menu == "Liquidity Data (India + US)":
    st.header("📌 Liquidity (India + US)")
    st.subheader("🇺🇸 US Federal Reserve Balance Sheet (FRED WALCL)")
    fed_df = get_fred("WALCL")
    if not fed_df.empty:
        st.line_chart(fed_df.set_index("date"))
        st.metric("Latest US Liquidity", fed_df["value"].iloc[-1])

    st.subheader("🇮🇳 India Liquidity — Upload CSV (LAF / Net Liquidity)")
    file = st.file_uploader("Upload India Liquidity CSV", type=['csv'])
    if file:
        df = pd.read_csv(file)
        try:
            df['date'] = pd.to_datetime(df['date'])
            st.line_chart(df.set_index("date"))
        except Exception as e:
            st.error(f"Invalid CSV format: {e}")

# -------------------- PAGE 5: PDF --------------------
if menu == "PDF Report":
    st.header("📄 Generate PDF Report")
    st.write("Click button to download report")
    import fpdf
    from io import BytesIO

    if st.button("Generate PDF Report"):
        pdf = fpdf.FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="RBI Macro Dashboard Report", ln=True, align="C")
        pdf.ln(10)
        pdf.multi_cell(0, 10, txt="This report includes inflation, monetary policy risks, and liquidity indicators.\nPrepared for RBI Summer Internship.")
        pdf_output = BytesIO()
        pdf.output(pdf_output)
        st.download_button("Download PDF", data=pdf_output.getvalue(), file_name="rbi_report.pdf")

