"""Bronze -> silver -> order-level tables, mirroring the SQL views.

load_raw()            ~ bronze.auto_sales_raw
build_order_lines()   ~ silver.order_lines       (one row per order line)
build_order_summary() ~ gold.order_summary       (one row per order)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import RAW_CSV, REGION_MAP, STATUS_MAP

FLAG_COLS = ["is_fulfilled", "is_open", "is_at_risk", "is_lost", "is_failed", "had_issue"]


def load_raw(path=RAW_CSV) -> pd.DataFrame:
    """Read the raw CSV exactly as delivered (bronze)."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def build_order_lines(raw: pd.DataFrame) -> pd.DataFrame:
    """Type, trim and standardise the raw data (silver).

    Personal data (phone, street address, postcode) is deliberately dropped.
    """
    s = raw.apply(lambda col: col.str.strip())
    df = pd.DataFrame(
        {
            "order_number": pd.to_numeric(s["ORDERNUMBER"], errors="coerce").astype("Int64"),
            "order_line_number": pd.to_numeric(s["ORDERLINENUMBER"], errors="coerce").astype("Int64"),
            "order_date": pd.to_datetime(s["ORDERDATE"], format="%d/%m/%Y", errors="coerce"),
            "customer_name": s["CUSTOMERNAME"],
            "contact_name": s["CONTACTFIRSTNAME"] + " " + s["CONTACTLASTNAME"],
            "city": s["CITY"],
            "country": s["COUNTRY"],
            "product_code": s["PRODUCTCODE"],
            "product_line": s["PRODUCTLINE"],
            "deal_size": s["DEALSIZE"],
            "status": s["STATUS"].str.upper(),
            "quantity": pd.to_numeric(s["QUANTITYORDERED"], errors="coerce"),
            "price_each": pd.to_numeric(s["PRICEEACH"], errors="coerce"),
            "msrp": pd.to_numeric(s["MSRP"], errors="coerce"),
            "sales": pd.to_numeric(s["SALES"], errors="coerce"),
        }
    )
    df["order_month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()

    status = pd.DataFrame.from_dict(STATUS_MAP, orient="index")
    status = status.rename(
        columns={
            "group": "status_group",
            "fulfilled": "is_fulfilled",
            "open": "is_open",
            "at_risk": "is_at_risk",
            "lost": "is_lost",
            "failed": "is_failed",
            "issue": "had_issue",
        }
    )
    df = df.merge(status, left_on="status", right_index=True, how="left")

    df["region"] = df["country"].map(REGION_MAP).fillna("EMEA")
    df["list_value"] = (df["msrp"] * df["quantity"]).round(2)
    df["price_vs_msrp_pct"] = np.where(df["msrp"] > 0, df["price_each"] / df["msrp"] - 1, np.nan)
    df["sales_reconciles"] = ((df["sales"] - df["price_each"] * df["quantity"]).abs() <= 0.10).astype(int)
    return df


def build_order_summary(lines: pd.DataFrame) -> pd.DataFrame:
    """Collapse order lines to one row per order (gold.order_summary).

    Status, customer, country and date are constant within an order
    (checked in tests), so taking the first value is safe.
    """
    first_cols = ["order_date", "order_month", "customer_name", "country", "region", "status", "status_group"]
    agg = {c: "first" for c in first_cols}
    agg.update({c: "max" for c in FLAG_COLS})
    agg.update(
        {
            "order_line_number": "count",
            "product_line": "nunique",
            "quantity": "sum",
            "sales": "sum",
            "list_value": "sum",
        }
    )
    orders = lines.groupby("order_number", as_index=False).agg(agg)
    return orders.rename(
        columns={
            "order_line_number": "n_lines",
            "product_line": "n_product_lines",
            "quantity": "units",
            "sales": "order_revenue",
            "list_value": "order_list_value",
        }
    )


def analysis_date(lines: pd.DataFrame) -> pd.Timestamp:
    """Reference date for recency: the day after the last order (2020-06-01)."""
    return lines["order_date"].max() + pd.Timedelta(days=1)


def build_customer_features(lines: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    """One row per customer with the behavioural features used downstream."""
    ref = analysis_date(lines)
    cust = lines.groupby("customer_name").agg(
        last_order=("order_date", "max"),
        first_order=("order_date", "min"),
        monetary=("sales", "sum"),
        n_unique_products=("product_code", "nunique"),
        country=("country", "first"),
        region=("region", "first"),
        city=("city", "first"),
        main_product_line=("product_line", lambda x: x.mode().iat[0]),
    )
    order_stats = orders.groupby("customer_name").agg(
        frequency=("order_number", "nunique"),
        open_orders=("is_open", "sum"),
        issue_orders=("had_issue", "sum"),
        at_risk_orders=("is_at_risk", "sum"),
        lost_orders=("is_lost", "sum"),
        fulfilled_orders=("is_fulfilled", "sum"),
    )
    cust = cust.join(order_stats)
    cust["recency_days"] = (ref - cust["last_order"]).dt.days
    cust["tenure_days"] = (cust["last_order"] - cust["first_order"]).dt.days
    cust["avg_order_value"] = cust["monetary"] / cust["frequency"]
    closed = cust["frequency"] - cust["open_orders"]
    cust["fulfilment_rate"] = np.where(closed > 0, cust["fulfilled_orders"] / closed, np.nan)

    # Event-based fulfilment experience (replaces v1's arbitrary % buckets).
    cust["fulfilment_experience"] = np.select(
        [cust["at_risk_orders"] + cust["lost_orders"] > 0, cust["issue_orders"] > 0],
        ["Order at risk / lost", "Issue resolved"],
        default="Clean record",
    )
    return cust.reset_index()
