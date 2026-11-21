"""Run the full Python pipeline end to end.

    python scripts/run_pipeline.py

raw CSV -> order lines -> orders -> KPI tables -> customer features
-> RFM -> clusters -> revenue-driver model -> data/processed + reports/figures

Everything the Streamlit app and README use is regenerated from the raw
file, so the numbers can always be reproduced.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autosales import clustering, kpis, modelling, plots, segmentation  # noqa: E402
from autosales.config import FIGURES_DIR, PROCESSED_DIR  # noqa: E402
from autosales.data import (  # noqa: E402
    build_customer_features,
    build_order_lines,
    build_order_summary,
    load_raw,
)


def main() -> dict:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    lines = build_order_lines(load_raw())
    orders = build_order_summary(lines)

    head = kpis.headline(orders)
    monthly = kpis.monthly(orders)
    country = kpis.by_country(orders)
    pl_month = kpis.by_product_line_month(lines)
    pl_summary = kpis.product_line_summary(pl_month, lines)
    pl_fix = kpis.equal_split_product_revenue(lines, orders)

    cust = build_customer_features(lines, orders)
    cust = segmentation.add_rfm(cust)
    cust["v1_value_tier"] = segmentation.legacy_v1_value_tier(cust)
    cust, cluster_profile, k_table = clustering.fit_clusters(cust)
    model = modelling.run(cust)

    # ---- processed outputs (consumed by the app) ----
    orders.to_csv(PROCESSED_DIR / "order_summary.csv", index=False)
    monthly.to_csv(PROCESSED_DIR / "kpi_monthly.csv", index=False)
    country.to_csv(PROCESSED_DIR / "kpi_country.csv", index=False)
    pl_month.to_csv(PROCESSED_DIR / "kpi_product_line_monthly.csv", index=False)
    pl_summary.to_csv(PROCESSED_DIR / "kpi_product_line.csv", index=False)
    pl_fix.to_csv(PROCESSED_DIR / "product_line_v1_vs_v2.csv", index=False)
    cust.drop(columns=["last_order", "first_order"]).to_csv(PROCESSED_DIR / "customer_segments.csv", index=False)
    cluster_profile.to_csv(PROCESSED_DIR / "cluster_profile.csv", index=False)
    k_table.to_csv(PROCESSED_DIR / "cluster_k_selection.csv", index=False)
    model["ols_full"].to_csv(PROCESSED_DIR / "model_ols.csv", index=False)
    model["ols_without_two_largest"].to_csv(PROCESSED_DIR / "model_ols_without_two_largest.csv", index=False)
    model["cv"].to_csv(PROCESSED_DIR / "model_cv.csv", index=False)
    meta = {
        "headline": {k: round(v, 6) if isinstance(v, float) else v for k, v in head.items()},
        "date_range": [str(lines["order_date"].min().date()), str(lines["order_date"].max().date())],
        "n_customers": int(cust.shape[0]),
        "customers_with_order_at_risk_or_lost": model["customers_with_issue"],
    }
    (PROCESSED_DIR / "kpi_headline.json").write_text(json.dumps(meta, indent=2))

    # ---- figures (README / notebooks) ----
    plots.status_mix(orders, FIGURES_DIR / "01_status_mix.png")
    plots.monthly_revenue(monthly, FIGURES_DIR / "02_monthly_revenue.png")
    plots.country_risk(country, FIGURES_DIR / "03_country_risk.png")
    plots.product_line_fix(pl_fix, FIGURES_DIR / "04_product_line_v1_vs_v2.png")
    plots.rfm_fix(cust, FIGURES_DIR / "05_rfm_v1_vs_v2.png")
    plots.tier_share(cust, FIGURES_DIR / "06_value_tier_share.png")
    plots.k_selection(k_table, FIGURES_DIR / "07_cluster_k_selection.png")
    plots.clusters(cust, FIGURES_DIR / "08_customer_clusters.png")
    plots.revenue_drivers(model["ols_full"], FIGURES_DIR / "09_revenue_drivers.png")

    return meta


if __name__ == "__main__":
    out = main()
    print(json.dumps(out, indent=2))
