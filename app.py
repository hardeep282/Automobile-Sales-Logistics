"""Automobile Sales & Logistics: Streamlit dashboard (v2).

Run locally:  streamlit run app.py
Data:         KPIs are computed live from data/raw with the same tested code
              as the pipeline; customer segments / clusters / model results
              come from data/processed (regenerate: python scripts/run_pipeline.py).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from autosales import kpis  # noqa: E402
from autosales.config import COLOURS, LOW_SAMPLE_ORDERS, PROCESSED_DIR, STATUS_GROUP_ORDER  # noqa: E402
from autosales.data import build_order_lines, build_order_summary, load_raw  # noqa: E402
from autosales.segmentation import SEGMENT_ACTIONS  # noqa: E402

st.set_page_config(page_title="Automobile Sales & Logistics", page_icon="🚗", layout="wide")

PLOT_CFG = {"displayModeBar": False}
STATUS_COLOURS = {k: COLOURS[k] for k in STATUS_GROUP_ORDER}


# ----------------------------------------------------------------- data
@st.cache_data
def load_lines() -> pd.DataFrame:
    return build_order_lines(load_raw())


@st.cache_data
def load_processed(name: str) -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / name)


def gbp(v: float) -> str:
    return f"£{v / 1e6:,.2f}M" if abs(v) >= 1e6 else f"£{v / 1e3:,.0f}k"


def style(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=40, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), title_font_size=15)
    return fig


lines_all = load_lines()

# ----------------------------------------------------------------- sidebar filters
st.sidebar.header("Filters")
years = sorted(lines_all["order_date"].dt.year.unique())
sel_years = st.sidebar.multiselect("Year", years, default=years)
regions = sorted(lines_all["region"].unique())
sel_regions = st.sidebar.multiselect("Region", regions, default=regions)
plines = sorted(lines_all["product_line"].unique())
sel_plines = st.sidebar.multiselect("Product line", plines, default=plines)
st.sidebar.caption("Filters apply to the operational tabs. Customer segments are scored on the full customer base.")

lines = lines_all[
    lines_all["order_date"].dt.year.isin(sel_years)
    & lines_all["region"].isin(sel_regions)
    & lines_all["product_line"].isin(sel_plines)
]
if lines.empty:
    st.warning("No data for this filter combination.")
    st.stop()
orders = build_order_summary(lines)
head = kpis.headline(orders)

# ----------------------------------------------------------------- header
st.title("🚗 Automobile Sales & Logistics Analytics")
st.caption(
    f"{lines['order_date'].min():%d %b %Y} – {lines['order_date'].max():%d %b %Y} · "
    f"{head['total_orders']} orders · {lines['customer_name'].nunique()} customers · "
    "2020 is a partial year (to 31 May)"
)

c = st.columns(6)
c[0].metric("Total revenue", gbp(head["total_revenue"]))
c[1].metric("Orders", f"{head['total_orders']:,}")
c[2].metric("Avg order value", gbp(head["avg_order_value"]))
c[3].metric("Fulfilment rate", f"{head['fulfilment_rate']:.1%}", help="Fulfilled ÷ closed orders (open orders excluded)")
c[4].metric("Revenue at risk", gbp(head["revenue_at_risk"]), help="On hold + disputed orders: still recoverable")
c[5].metric("Revenue lost", gbp(head["revenue_lost"]), help="Cancelled orders")

tab_over, tab_ful, tab_country, tab_prod, tab_cust, tab_method = st.tabs(
    ["📈 Overview", "🚚 Fulfilment", "🌍 Country risk", "📦 Product lines", "👥 Customers", "🧪 Methodology"]
)

# ----------------------------------------------------------------- overview
with tab_over:
    monthly = kpis.monthly(orders)
    fig = px.bar(monthly, x="order_month", y="total_revenue", title="Monthly revenue",
                 labels={"order_month": "", "total_revenue": "Revenue (£)"}, color_discrete_sequence=[COLOURS["primary"]])
    st.plotly_chart(style(fig), width="stretch", config=PLOT_CFG)
    st.caption("November is roughly 3× an average month in both full years. Plan stock and fulfilment capacity for Q4.")

    left, right = st.columns(2)
    sg = orders.groupby("status_group", as_index=False).agg(orders=("order_number", "count"), revenue=("order_revenue", "sum"))
    fig = px.bar(sg, x="revenue", y="status_group", orientation="h", color="status_group", title="Revenue by order outcome",
                 category_orders={"status_group": STATUS_GROUP_ORDER}, color_discrete_map=STATUS_COLOURS,
                 labels={"revenue": "Revenue (£)", "status_group": ""}, text=sg["orders"].astype(str) + " orders")
    left.plotly_chart(style(fig).update_layout(showlegend=False), width="stretch", config=PLOT_CFG)

    ytd = monthly[monthly["order_month"].dt.month <= 5].groupby(monthly["order_month"].dt.year)["total_revenue"].sum()
    ytd = ytd.reset_index().rename(columns={"order_month": "year"})
    ytd["year"] = ytd["year"].astype(str)
    fig = px.bar(ytd, x="year", y="total_revenue", title="Like-for-like: Jan–May revenue by year", text_auto=".3s",
                 labels={"year": "", "total_revenue": "Revenue (£)"}, color_discrete_sequence=[COLOURS["primary"]])
    right.plotly_chart(style(fig), width="stretch", config=PLOT_CFG)

# ----------------------------------------------------------------- fulfilment
with tab_ful:
    st.markdown(
        "**Status groups:** Fulfilled = Shipped / Resolved · Open = In Process (all dated in the last 3 days of the data, "
        "so normal pipeline) · At Risk = On Hold / Disputed · Lost = Cancelled."
    )
    k = st.columns(4)
    k[0].metric("Failure rate", f"{head['failure_rate']:.1%}", help="(Cancelled + Disputed) ÷ all orders")
    k[1].metric("Issue rate", f"{head['issue_rate']:.1%}", help="Orders with any issue ÷ closed orders")
    k[2].metric("Open orders", head["open_orders"])
    k[3].metric("Open pipeline", gbp(head["open_pipeline_revenue"]))

    mo = orders.groupby(["order_month", "status_group"], as_index=False)["order_number"].count()
    fig = px.bar(mo, x="order_month", y="order_number", color="status_group", title="Orders per month by outcome",
                 category_orders={"status_group": STATUS_GROUP_ORDER}, color_discrete_map=STATUS_COLOURS,
                 labels={"order_month": "", "order_number": "Orders", "status_group": ""})
    st.plotly_chart(style(fig), width="stretch", config=PLOT_CFG)

    attention = orders[orders["status_group"].isin(["At Risk", "Lost"])].sort_values("order_revenue", ascending=False)
    st.subheader(f"Orders needing attention ({len(attention)})")
    st.dataframe(
        attention[["order_number", "order_date", "customer_name", "country", "status", "status_group", "order_revenue"]],
        hide_index=True, width="stretch",
        column_config={"order_revenue": st.column_config.NumberColumn("Revenue", format="£%.0f"),
                       "order_date": st.column_config.DateColumn("Order date", format="DD MMM YYYY")},
    )

# ----------------------------------------------------------------- country risk
with tab_country:
    country = kpis.by_country(orders)
    country["failed_of_total"] = country["failed_orders"].astype(int).astype(str) + " / " + country["total_orders"].astype(int).astype(str)
    country["sample"] = country["low_sample_flag"].map({1: f"< {LOW_SAMPLE_ORDERS} orders (low sample)", 0: f"≥ {LOW_SAMPLE_ORDERS} orders"})
    fig = px.scatter(country, x="total_revenue", y="failure_rate", size="total_orders", color="sample",
                     hover_name="country", text="country", title="Failure rate vs revenue (bubble = orders)",
                     hover_data={"failed_of_total": True, "sample": False, "total_orders": True},
                     color_discrete_sequence=[COLOURS["primary"], COLOURS["muted"]],
                     labels={"total_revenue": "Revenue (£)", "failure_rate": "Failure rate", "sample": ""})
    fig.update_traces(textposition="top center", textfont_size=10)
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(style(fig, 420), width="stretch", config=PLOT_CFG)
    st.info(
        "Sweden and Denmark show the highest failure rate (14.3%), but each is **1 failed order out of 7**. "
        f"Countries with fewer than {LOW_SAMPLE_ORDERS} orders are flagged instead of ranked."
    )
    st.dataframe(
        country[["country", "region", "total_orders", "total_revenue", "failed_of_total", "failure_rate",
                 "fulfilment_rate", "revenue_at_risk", "revenue_lost", "sample"]],
        hide_index=True, width="stretch",
        column_config={
            "total_revenue": st.column_config.NumberColumn("Revenue", format="£%.0f"),
            "failure_rate": st.column_config.NumberColumn("Failure rate", format="percent"),
            "fulfilment_rate": st.column_config.NumberColumn("Fulfilment rate", format="percent"),
            "revenue_at_risk": st.column_config.NumberColumn("Revenue at risk", format="£%.0f"),
            "revenue_lost": st.column_config.NumberColumn("Revenue lost", format="£%.0f"),
            "failed_of_total": "Failed / total",
        },
    )

# ----------------------------------------------------------------- product lines
with tab_prod:
    pl_month = kpis.by_product_line_month(lines)
    pl = kpis.product_line_summary(pl_month, lines)
    left, right = st.columns(2)
    fig = px.bar(pl.sort_values("revenue"), x="revenue", y="product_line", orientation="h", title="Revenue by product line",
                 text=pl.sort_values("revenue")["revenue_share"].map("{:.0%}".format),
                 labels={"revenue": "Revenue (£)", "product_line": ""}, color_discrete_sequence=[COLOURS["primary"]])
    left.plotly_chart(style(fig, 380), width="stretch", config=PLOT_CFG)
    exp = pl.melt(id_vars="product_line", value_vars=["revenue_at_risk_pct", "revenue_lost_pct"], var_name="metric", value_name="pct")
    exp["metric"] = exp["metric"].map({"revenue_at_risk_pct": "At risk", "revenue_lost_pct": "Lost"})
    fig = px.bar(exp, x="pct", y="product_line", color="metric", barmode="group", orientation="h",
                 title="Exposure: % of product-line revenue", color_discrete_map={"At risk": COLOURS["At Risk"], "Lost": COLOURS["Lost"]},
                 labels={"pct": "", "product_line": "", "metric": ""})
    fig.update_xaxes(tickformat=".0%")
    right.plotly_chart(style(fig, 380), width="stretch", config=PLOT_CFG)

    with st.expander("Why these numbers differ from v1 (allocation fix)"):
        fix = load_processed("product_line_v1_vs_v2.csv")
        st.markdown(
            "v1 split each **order's** revenue equally across the product lines in that order (weight = 1/n). "
            "Every order line already has its own sales value, so v2 simply sums line-level sales. "
            "Figures below are for the full dataset."
        )
        st.dataframe(fix, hide_index=True, width="stretch", column_config={
            "v2_exact": st.column_config.NumberColumn("v2 exact", format="£%.0f"),
            "v1_equal_split": st.column_config.NumberColumn("v1 equal split", format="£%.0f"),
            "v1_error_pct": st.column_config.NumberColumn("v1 error", format="percent"),
        })

# ----------------------------------------------------------------- customers
with tab_cust:
    cust = load_processed("customer_segments.csv")
    st.caption("Scored on the full customer base (89 customers); sidebar filters do not apply here.")
    tiers = ["High Value", "Mid Value", "Low Value"]
    t = cust.groupby("value_tier").agg(customers=("customer_name", "count"), revenue=("monetary", "sum")).reindex(tiers)
    t["customer_share"] = t["customers"] / t["customers"].sum()
    t["revenue_share"] = t["revenue"] / t["revenue"].sum()
    m = st.columns(3)
    for col, tier in zip(m, tiers, strict=True):
        col.metric(tier, f"{t.loc[tier, 'revenue_share']:.0%} of revenue", f"{int(t.loc[tier, 'customers'])} customers", delta_color="off")

    left, right = st.columns(2)
    seg = cust.groupby("rfm_segment", as_index=False).agg(customers=("customer_name", "count"), revenue=("monetary", "sum"))
    fig = px.bar(seg.sort_values("revenue"), x="revenue", y="rfm_segment", orientation="h", title="Revenue by RFM segment",
                 text=seg.sort_values("revenue")["customers"].astype(str) + " customers",
                 labels={"revenue": "Revenue (£)", "rfm_segment": ""}, color_discrete_sequence=[COLOURS["primary"]])
    left.plotly_chart(style(fig), width="stretch", config=PLOT_CFG)
    fig = px.scatter(cust, x="frequency", y="monetary", color="cluster_label", log_x=True, log_y=True,
                     hover_name="customer_name", title="K-Means clusters (k chosen by silhouette)",
                     hover_data={"recency_days": True, "value_tier": True},
                     labels={"frequency": "Orders (log)", "monetary": "Revenue £ (log)", "cluster_label": ""})
    right.plotly_chart(style(fig), width="stretch", config=PLOT_CFG)

    st.subheader("What to do with each segment")
    st.dataframe(pd.DataFrame({"Segment": SEGMENT_ACTIONS.keys(), "Action": SEGMENT_ACTIONS.values()}),
                 hide_index=True, width="stretch")

    st.subheader("Customer list")
    pick = st.multiselect("RFM segment", sorted(cust["rfm_segment"].unique()))
    view = cust[cust["rfm_segment"].isin(pick)] if pick else cust
    st.dataframe(
        view.sort_values("monetary", ascending=False)[
            ["customer_name", "country", "frequency", "monetary", "recency_days", "R_score", "F_score", "M_score",
             "value_tier", "rfm_segment", "cluster_label", "fulfilment_experience"]],
        hide_index=True, width="stretch",
        column_config={"monetary": st.column_config.NumberColumn("Revenue", format="£%.0f"),
                       "frequency": "Orders", "recency_days": "Days since last order"},
    )

# ----------------------------------------------------------------- methodology
with tab_method:
    meta = json.loads((PROCESSED_DIR / "kpi_headline.json").read_text())
    st.markdown(
        """
### How the numbers are built
**SQL Server medallion** (`sql/`): bronze (raw text) → silver (typed, one row per order line) → gold (star schema + KPI views),
with 23 automated data-quality tests. The **same KPI definitions** are used in SQL, in this app (Python) and in the Power BI measures,
and CI checks that SQL and Python agree.

| KPI | Definition |
|---|---|
| Fulfilment rate | Fulfilled orders ÷ closed orders (open orders excluded) |
| Failure rate | (Cancelled + Disputed) ÷ all orders |
| Revenue at risk | Revenue on On Hold + Disputed orders (still recoverable) |
| Revenue lost | Revenue on Cancelled orders |

### Fixes made in v2 (an audit of v1)
1. **RFM scores were inverted** for frequency and monetary, so the top customer was labelled *Low Value*. Fixed and unit-tested.
2. **Product-line revenue** was an equal 1/n split of order revenue (Trains +138%, Planes −25%). It now uses exact line-level sales.
3. **IN PROCESS orders** (last 3 days of data) were counted as *stuck*. They're now *Open* and excluded from rates.
4. **K-Means**: k is now chosen by silhouette score, and labels are generated from each cluster's profile (v1 called the most active cluster "Dormant").
5. **Revenue model**: v1's R² = 0.971 mostly reflected arithmetic (revenue = orders × order value), tested on 18 customers. v2 uses log-log OLS with robust
   standard errors and repeated cross-validation.
6. **Power BI**: the date table was disconnected, so time slicers did nothing. The model is rebuilt as a star schema in PBIP/TMDL.
"""
    )
    ols = load_processed("model_ols.csv")
    cv = load_processed("model_cv.csv")
    lf = ols.set_index("term").loc["log_frequency"]
    iss = ols.set_index("term").loc["had_order_at_risk_or_lost"]
    st.markdown(
        f"""
### Revenue drivers: result
- Revenue elasticity to order count: **{lf['coef']:.2f}** (95% CI {lf['ci_low']:.2f}–{lf['ci_high']:.2f}). Revenue grows roughly in proportion to orders.
- Having an order at risk or lost: coefficient {iss['coef']:+.2f}, **p = {iss['p_value']:.2f}**. No evidence of an effect, but only
  {meta['customers_with_order_at_risk_or_lost']} of {meta['n_customers']} customers were affected, so the test has little power.
- Cross-validated R²: baseline {cv.loc[0, 'cv_r2_mean']:.2f} vs full model {cv.loc[1, 'cv_r2_mean']:.2f}. The extra features add nothing out of sample.
"""
    )
    st.caption("Source: Kaggle 'Automobile Sales data' (2,747 order lines). Code: github.com/hardeep282/Automobile-Sales-Logistics")
