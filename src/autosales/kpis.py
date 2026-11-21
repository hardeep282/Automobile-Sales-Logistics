"""KPI tables. Definitions are identical to sql/03_gold_model.sql and the
Power BI measures (see docs/kpi_definitions.md)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import LOW_SAMPLE_ORDERS


def _kpis(g: pd.DataFrame) -> pd.Series:
    """KPI arithmetic for any group of orders (one row per order)."""
    n = len(g)
    closed = n - g["is_open"].sum()
    rev = g["order_revenue"].sum()
    at_risk_rev = g.loc[g["is_at_risk"] == 1, "order_revenue"].sum()
    return pd.Series(
        {
            "total_orders": n,
            "total_revenue": rev,
            "avg_order_value": rev / n if n else np.nan,
            "fulfilled_orders": g["is_fulfilled"].sum(),
            "open_orders": g["is_open"].sum(),
            "at_risk_orders": g["is_at_risk"].sum(),
            "lost_orders": g["is_lost"].sum(),
            "failed_orders": g["is_failed"].sum(),
            "fulfilment_rate": g["is_fulfilled"].sum() / closed if closed else np.nan,
            "issue_rate": g["had_issue"].sum() / closed if closed else np.nan,
            "failure_rate": g["is_failed"].sum() / n if n else np.nan,
            "revenue_at_risk": at_risk_rev,
            "revenue_at_risk_pct": at_risk_rev / rev if rev else np.nan,
            "revenue_lost": g.loc[g["is_lost"] == 1, "order_revenue"].sum(),
            "open_pipeline_revenue": g.loc[g["is_open"] == 1, "order_revenue"].sum(),
        }
    )


def headline(orders: pd.DataFrame) -> dict:
    out = {}
    for k, v in _kpis(orders).items():
        out[k] = int(v) if k.endswith("orders") else float(v)
    return out


def monthly(orders: pd.DataFrame) -> pd.DataFrame:
    """One row per calendar month, including any month with no orders."""
    months = pd.date_range(orders["order_month"].min(), orders["order_month"].max(), freq="MS")
    out = orders.groupby("order_month").apply(_kpis, include_groups=False).reindex(months)
    out.index.name = "order_month"
    zero_cols = [c for c in out.columns if c.endswith(("orders", "revenue", "risk", "lost"))]
    out[zero_cols] = out[zero_cols].fillna(0)
    return out.reset_index()


def by_country(orders: pd.DataFrame) -> pd.DataFrame:
    out = (
        orders.groupby(["country", "region"]).apply(_kpis, include_groups=False).reset_index()
        .sort_values("total_revenue", ascending=False)
    )
    out["low_sample_flag"] = (out["total_orders"] < LOW_SAMPLE_ORDERS).astype(int)
    return out.reset_index(drop=True)


def by_product_line_month(lines: pd.DataFrame) -> pd.DataFrame:
    """Exact product-line revenue from line-level sales (no allocation)."""
    months = pd.date_range(lines["order_month"].min(), lines["order_month"].max(), freq="MS")
    spine = pd.MultiIndex.from_product([months, sorted(lines["product_line"].unique())],
                                       names=["order_month", "product_line"])
    l = lines.assign(
        rev_at_risk=lines["sales"].where(lines["is_at_risk"] == 1, 0),
        rev_lost=lines["sales"].where(lines["is_lost"] == 1, 0),
        failed_order=lines["order_number"].where(lines["is_failed"] == 1),
    )
    g = l.groupby(["order_month", "product_line"]).agg(
        orders=("order_number", "nunique"),
        units=("quantity", "sum"),
        revenue=("sales", "sum"),
        revenue_at_risk=("rev_at_risk", "sum"),
        revenue_lost=("rev_lost", "sum"),
        failed_orders=("failed_order", "nunique"),
    )
    return g.reindex(spine, fill_value=0).reset_index()


def product_line_summary(pl_month: pd.DataFrame, lines: pd.DataFrame) -> pd.DataFrame:
    s = pl_month.groupby("product_line")[["revenue", "revenue_at_risk", "revenue_lost", "units"]].sum()
    s["orders"] = lines.groupby("product_line")["order_number"].nunique()
    s["revenue_share"] = s["revenue"] / s["revenue"].sum()
    s["revenue_at_risk_pct"] = s["revenue_at_risk"] / s["revenue"]
    s["revenue_lost_pct"] = s["revenue_lost"] / s["revenue"]
    return s.sort_values("revenue", ascending=False).reset_index()


def equal_split_product_revenue(lines: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    """Reproduces the v1 (wrong) 1/n allocation, kept only to document the fix."""
    pairs = lines[["order_number", "product_line"]].drop_duplicates()
    pairs = pairs.merge(orders[["order_number", "order_revenue", "n_product_lines"]], on="order_number")
    pairs["allocated"] = pairs["order_revenue"] / pairs["n_product_lines"]
    v1 = pairs.groupby("product_line")["allocated"].sum().rename("v1_equal_split")
    exact = lines.groupby("product_line")["sales"].sum().rename("v2_exact")
    out = pd.concat([exact, v1], axis=1)
    out["v1_error_pct"] = out["v1_equal_split"] / out["v2_exact"] - 1
    return out.sort_values("v2_exact", ascending=False).reset_index()
