import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime
import fpdf
from io import BytesIO
import numpy as np # Added for robust data handling

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
# Load API key securely from Streamlit secrets
FRED_API_KEY = st.secrets.get("fred_api_key")

def get_fred(series_id):
    """Fetches data from the FRED API using the specified series ID."""
    
    # Check if the API key is missing (None) or a placeholder string.
    if not FRED_API_KEY or FRED_API_KEY == "YOUR_FRED_API_KEY_PLACEHOLDER":
        st.error(f"⚠️ FRED API Key Required: Cannot fetch live data for {series_id}. Please set your FRED API key as `fred_api_key` in Streamlit secrets.")
        return pd.DataFrame(columns=["date", "value"])

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json"
    }
    
    try:
        r = requests.get(url, params=params)
        r.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        
        # Process the data
        data = r.json()["observations"]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        # Convert '.' (used for missing data in FRED) to NaN, then coerce to numeric
        df["value"] = pd.to_numeric(df["value"], errors="coerce") 
        df = df.dropna(subset=['value'])
        return df[["date", "value"]]
    except requests.exceptions.RequestException as e:
        # Catch network errors, connection problems, or the specific 400 error
        st.error(f"Error fetching {series_id}: Request Failed. Check API key validity or network. Details: {e}")
        return pd.DataFrame(columns=["date", "value"])
    except Exception as e:
        # Catch unexpected errors like JSON parsing failure
        st.error(f"Error fetching {series_id}: Unexpected error ({e})")
        return pd.DataFrame(columns=["date", "value"])

# -------------------- India CPI --------------------
def india_cpi():
    """Fetches India CPI data from the World Bank API."""
    try:
        # Adjusted URL to be more robust, requesting JSON directly
        url = "https://api.worldbank.org/v2/country/IN/indicator/FP.CPI.TOTL?format=json&per_page=500"
        r = requests.get(url)
        r.raise_for_status()
        
        # World Bank API returns metadata as the first element [0] and data as the second [1]
        data = r.json()[1]
        
        # Check if data is not empty or None
        if not data:
             st.warning("World Bank API returned no data for India CPI.")
             return pd.DataFrame(columns=["date", "value"])

        df = pd.DataFrame(data)
        df = df.rename(columns={'date': 'date_str', 'value': 'value'})
        df['date'] = pd.to_datetime(df['date_str'], format='%Y')
        df = df.sort_values("date")
        df = df.dropna(subset=['value'])
        
        # Keep only the columns needed for the chart
        return df[['date', 'value']]
    except Exception as e:
        st.error(f"Error fetching India CPI: {e}")
        return pd.DataFrame(columns=["date", "value"])

# -------------------- PAGE 1: INFLATION --------------------
if menu == "Inflation (India + US)":
    st.header("📌 Inflation Dashboard")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🇺🇸 US CPI (Live FRED)")
        # CPIAUCSL: Consumer Price Index for All Urban Consumers: All Items in U.S. City Average, Seasonally Adjusted
        us_df = get_fred("CPIAUCSL") 
        if not us_df.empty:
            st.line_chart(us_df.set_index("date"))
            st.metric("Latest US CPI (Index)", f"{us_df['value'].iloc[-1]:.2f}")
    
    with col2:
        st.subheader("🇮🇳 India CPI (World Bank)")
        ind_df = india_cpi()
        if not ind_df.empty:
            st.line_chart(ind_df.set_index("date"))
            st.metric("Latest India CPI (Index)", f"{ind_df['value'].iloc[-1]:.2f}")

    st.subheader("🧮 Inflation Calculator")
    initial = st.number_input("Initial Price", value=100.0)
    inflation = st.number_input("Inflation Rate (%)", value=6.0)
    years = st.number_input("Years", value=5, min_value=1)
    
    # Calculation with better precision handling
    future_price = initial * ((1 + inflation/100) ** years)
    st.success(f"Future Price after {years} years → ₹{future_price:.2f}")

# -------------------- PAGE 2: RISKOMETER --------------------
if menu == "Riskometer":
    st.header("📌 Portfolio Riskometer")
    
    st.markdown("Use the sliders below to determine the risk score based on your asset allocation.")
    
    eq = st.slider("Equity (%)", 0, 100, 40)
    debt = st.slider("Debt (%)", 0, 100, 40)
    gold = st.slider("Gold/Commodities (%)", 0, 100, 20)
    
    total = eq + debt + gold
    if total != 100:
        st.error(f"Allocation must sum to 100%. Current sum: {total}%")
        risk_score = 0
    else:
        # Risk weights: Equity (0.7), Gold (0.2), Debt (0.1) - based on original code logic
        risk_score = eq*0.7 + gold*0.2 + debt*0.1

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        title={"text": "Portfolio Risk Score (out of 100)"},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkblue"},
            "bar": {"color": "darkblue"},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "gray",
            "steps": [
                {"range": [0, 30], "color": "lightgreen"},
                {"range": [30, 60], "color": "yellow"},
                {"range": [60, 100], "color": "red"}
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": risk_score
            }
        }
    ))
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Interpretation")
    if risk_score < 30:
        st.success(f"Score: {risk_score:.1f} → **LOW RISK**. Stable portfolio, aiming for capital preservation.")
    elif risk_score < 60:
        st.warning(f"Score: {risk_score:.1f} → **MODERATE RISK**. Balanced portfolio, suitable for moderate growth and stability.")
    else:
        st.error(f"Score: {risk_score:.1f} → **HIGH RISK**. Risky portfolio, sensitive to market volatility, but with higher potential returns.")

# -------------------- PAGE 3: MONETARY POLICY IMPACT --------------------
if menu == "Monetary Policy Impact":
    st.header("📌 Monetary Policy Risk Analysis")
    
    st.markdown("This section summarizes the macroeconomic risks associated with key policy changes.")
    
    st.subheader("📈 Risks when Interest Rates Increase (Tightening Cycle)")
    st.markdown("""
    - **Borrowing cost increases:** Higher EMI for loans, dampening consumption and corporate investment.
    - **GDP growth slows:** Economic activity contracts due to higher cost of capital.
    - **Bond prices fall:** (Inverse relationship) Existing bond yields look less attractive.
    - **Stock market correction:** Higher discount rate reduces the present value of future earnings.
    - **EM currency depreciation (India perspective):** If US rates rise faster than India's, FPI outflows strengthen the USD.
    """)
    st.subheader("💧 Risks when Liquidity Increases (Easing Cycle)")
    st.markdown("""
    - **Inflation rises:** Too much money chasing too few goods leads to demand-pull inflation.
    - **Asset bubble risk:** Excess liquidity flows into equity and real estate, inflating prices unsustainably.
    - **Currency weakens:** Higher money supply puts downward pressure on the domestic currency's value.
    - **Excessive credit growth:** Banks lend aggressively, potentially leading to future Non-Performing Assets (NPAs).
    """)
    st.subheader("🔥 Risks when Inflation Rises (Cost of Living Crisis)")
    st.markdown("""
    - **Purchasing power falls:** The primary impact on consumers and real wages.
    - **Corporate margins shrink:** If companies cannot pass on rising input costs to consumers.
    - **Monetary tightening expected:** Central Banks are forced to raise interest rates, potentially leading to recession.
    """)
    st.subheader("🇺🇸 Risks when US CPI Rises (Fed Tightening)")
    st.markdown("""
    - **USD strengthens:** Global demand for safe-haven US assets increases.
    - **FPI outflows from India:** Foreign Portfolio Investors withdraw capital from emerging markets for safer, higher-yielding US assets.
    - **RBI may be forced to hike:** To protect the Rupee and maintain interest rate differentials.
    """)

# -------------------- PAGE 4: LIQUIDITY --------------------
if menu == "Liquidity Data (India + US)":
    st.header("📌 Liquidity (India + US)")
    
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("🇺🇸 US Federal Reserve Balance Sheet (FRED WALCL)")
        # WALCL: Assets, Total: All: Wednesday Level
        fed_df = get_fred("WALCL")
        if not fed_df.empty:
            st.line_chart(fed_df.set_index("date"))
            # Format in trillions for readability
            latest_val = fed_df["value"].iloc[-1] / 1000000 
            st.metric("Latest Fed Balance Sheet (Trillion $)", f"${latest_val:.2f}")

    with col4:
        st.subheader("🇮🇳 India Liquidity — Upload CSV (LAF / Net Liquidity)")
        file = st.file_uploader("Upload India Liquidity CSV", type=['csv'], help="Expected CSV columns: 'date' (YYYY-MM-DD format) and 'value' (Liquidity data)")
        if file:
            try:
                df = pd.read_csv(file)
                df.columns = [col.lower() for col in df.columns]
                
                if 'date' in df.columns and 'value' in df.columns:
                    # FIX: Explicitly convert columns to handle non-numeric data and ensure proper date type
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    df['value'] = pd.to_numeric(df['value'], errors='coerce') 
                    
                    # Drop any rows where conversion failed or data is missing
                    df = df.dropna(subset=['date', 'value'])

                    if df.empty:
                        st.error("CSV uploaded, but no valid date and value pairs were found after cleaning. Check for non-numeric values or invalid dates.")
                    else:
                        st.success("CSV Uploaded and Parsed Successfully!")
                        st.line_chart(df.set_index("date"))
                        st.metric("Latest India Liquidity Value", f"₹{df['value'].iloc[-1]:,.2f}")
                else:
                    st.error("CSV must contain 'date' and 'value' columns.")

            except Exception as e:
                # Catch general parsing errors
                st.error(f"Invalid CSV format or parsing error: {e}")

# -------------------- PAGE 5: PDF (FIXED) --------------------
if menu == "PDF Report":
    st.header("📄 Generate PDF Report")
    st.write("Click the button below to generate and download a simple report summarizing the dashboard.")
    
    if st.button("Generate PDF Report"):
        try:
            pdf = fpdf.FPDF()
            pdf.add_page()
            
            # Title
            pdf.set_font("Arial", "B", size=16)
            pdf.cell(0, 10, txt="RBI Macro Dashboard Report", ln=True, align="C")
            pdf.ln(5)
            
            # Metadata
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, txt=f"Report Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="L")
            pdf.ln(5)
            
            # Content
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 8, txt="This report provides a snapshot of the key macroeconomic indicators tracked by the RBI Macro Economic Dashboard, including Inflation, Liquidity, and Risk assessment tools. This analysis is suitable for academic or professional review of the current economic environment (India & US).")
            pdf.ln(10)
            
            # Summary of FRED Status
            pdf.set_font("Arial", "B", size=14)
            pdf.cell(0, 10, txt="Data Source Status", ln=True, align="L")
            pdf.set_font("Arial", size=12)
            
            # Check if the API key is missing (None)
            if not FRED_API_KEY:
                pdf.multi_cell(0, 8, txt="FRED API Connection: UNAVAILABLE. The API key is missing from Streamlit secrets, preventing the retrieval of live US CPI and Fed Balance Sheet data.")
            else:
                pdf.multi_cell(0, 8, txt="FRED API Connection: ACTIVE. Live US economic data is being fetched.")
            
            # FIX: Use dest='S' to get the raw bytes string, which resolves the 'BytesIO' error.
            pdf_data = pdf.output(dest='S')
            
            st.download_button(
                label="Download PDF", 
                data=pdf_data,  # Pass the raw bytes string
                file_name="rbi_macro_report.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Could not generate PDF. Ensure the 'fpdf' library is installed. Error: {e}")
