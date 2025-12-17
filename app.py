import streamlit as st
import pandas as pd

DEBUG = False
if DEBUG:
    import os
    st.write("RUNNING FILE:", __file__)
    st.write("WORKDIR:", os.getcwd())


from src.charts import (
    chart1_value_tier_count,
    chart2_value_tier_revenue,
    chart3_shipping_bucket_count,
    chart4_value_vs_shipping_heatmap
)

from pathlib import Path

st.set_page_config(page_title="Automobile Sales Dashboard", layout="wide")
st.title("🚗 Automobile Sales Analytics Dashboard")

DATA_PATH = Path(r"data/Cleaned-Data/rfm_output.csv")

@st.cache_data
def load_rfm(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

if not DATA_PATH.exists():
    st.error(f"File not found: {DATA_PATH}")
    st.stop()

rfm = load_rfm(DATA_PATH)

# Sidebar filters
st.sidebar.header("Filters")
countries = ["All"] + sorted(rfm["main_country"].dropna().unique().tolist()) if "main_country" in rfm.columns else ["All"]
country = st.sidebar.selectbox("Main Country", countries, index=0)

tiers = ["All", "High Value", "Mid Value", "Low Value"] if "value_tier" in rfm.columns else ["All"]
tier = st.sidebar.selectbox("Value Tier", tiers, index=0)

ship_buckets = ["All"] + sorted(rfm["ship_bucket"].dropna().unique().tolist()) if "ship_bucket" in rfm.columns else ["All"]
ship_bucket = st.sidebar.selectbox("Shipping Bucket", ship_buckets, index=0)

save_charts = st.sidebar.checkbox("Save charts to assets/screenshots", value=False)

# Apply filters
df = rfm.copy()
if country != "All" and "main_country" in df.columns:
    df = df[df["main_country"] == country]
if tier != "All" and "value_tier" in df.columns:
    df = df[df["value_tier"] == tier]
if ship_bucket != "All" and "ship_bucket" in df.columns:
    df = df[df["ship_bucket"] == ship_bucket]

# Metrics + preview
col1, col2, col3 = st.columns(3)
col1.metric("Rows", f"{len(df):,}")
col2.metric("Columns", f"{df.shape[1]:,}")
col3.metric("Missing cells", f"{int(df.isna().sum().sum()):,}")

with st.expander("🔍 Data Preview", expanded=False):
    st.dataframe(df.head(25), use_container_width=True)

# Save paths
out_dir = Path("assets/screenshots")
p1 = out_dir / "01_customer_distribution_by_value_tier.png" if save_charts else None
p2 = out_dir / "02_revenue_by_value_tier.png" if save_charts else None
p3 = out_dir / "03_customer_distribution_by_shipping.png" if save_charts else None
p4 = out_dir / "04_value_tier_x_shipping_heatmap.png" if save_charts else None

# ---- Charts ----
st.markdown("## 📊 Customer Value Overview")
st.markdown(
    "This section highlights how customers are distributed across RFM value tiers "
    "and how much revenue each tier contributes."
)

st.subheader("Chart 1 — Customer Distribution by RFM Value Tier")
if "value_tier" in df.columns:
    st.pyplot(chart1_value_tier_count(df, save_path=p1))
else:
    st.warning("Missing column: value_tier")

st.subheader("Chart 2 — Total Revenue Contribution by RFM Value Tier")
need2 = {"value_tier", "monetary_sales"}
if need2.issubset(df.columns):
    st.pyplot(chart2_value_tier_revenue(df, save_path=p2))
else:
    st.warning("Missing columns: value_tier and/or monetary_sales")


st.markdown("## 🚚 Logistics Risk & Reliability")
st.markdown(
    "This section shows how customers are distributed across shipping reliability buckets, "
    "helping identify operational risk."
)

st.subheader("Chart 3 — Customer Distribution by Shipping Reliability")
if "ship_bucket" in df.columns:
    st.pyplot(chart3_shipping_bucket_count(df, save_path=p3))
else:
    st.warning("Missing column: ship_bucket")


st.markdown("## 🔀 Value × Logistics Interaction")
st.markdown(
    "This heatmap shows how customer value tiers intersect with shipping reliability, "
    "revealing high-value customers at operational risk."
)

st.subheader("Chart 4 — Value Tier × Shipping Reliability Heatmap (%)")
need4 = {"value_tier", "ship_bucket"}
if need4.issubset(df.columns):
    st.pyplot(chart4_value_vs_shipping_heatmap(df, save_path=p4))
else:
    st.warning("Missing columns: value_tier and/or ship_bucket")
