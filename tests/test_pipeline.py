"""Unit tests for the Python analytics. Each test pins a bug found in v1."""

import numpy as np
import pandas as pd
import pytest

from autosales import kpis, modelling, segmentation
from autosales.config import STATUS_MAP


# ---------------------------------------------------------------- data layer
def test_row_and_order_counts(lines, orders):
    assert len(lines) == 2747
    assert len(orders) == 298
    assert lines["customer_name"].nunique() == 89


def test_no_unparsed_values(lines):
    assert lines[["order_date", "quantity", "price_each", "sales", "msrp", "status_group"]].notna().all().all()


def test_every_status_is_mapped(lines):
    assert set(lines["status"]) <= set(STATUS_MAP)


def test_status_constant_within_order(lines):
    assert lines.groupby("order_number")["status"].nunique().max() == 1


def test_pii_not_carried_forward(lines):
    assert not {"PHONE", "ADDRESSLINE1", "POSTALCODE", "phone", "address"} & set(lines.columns)


# ---------------------------------------------------------------- KPIs
def test_headline_kpis(orders):
    h = kpis.headline(orders)
    assert h["total_orders"] == 298
    assert h["total_revenue"] == pytest.approx(9_760_221.71, abs=0.01)
    assert h["failure_rate"] == pytest.approx(7 / 298)
    assert h["open_orders"] == 6
    assert h["fulfilment_rate"] == pytest.approx(281 / 292)
    assert h["revenue_at_risk"] == pytest.approx(251_192.05, abs=0.01)
    assert h["revenue_lost"] == pytest.approx(194_487.48, abs=0.01)


def test_in_process_orders_are_open_not_risk(lines):
    """v1 counted IN PROCESS as stuck. They are the last 3 days of data."""
    ip = lines[lines["status"] == "IN PROCESS"]
    assert ip["order_date"].min() >= pd.Timestamp("2020-05-29")
    assert (ip["status_group"] == "Open").all() and (ip["is_at_risk"] == 0).all()


def test_product_line_revenue_reconciles(lines, orders):
    """v1 split order revenue 1/n across product lines. v2 must reconcile exactly."""
    pl = kpis.by_product_line_month(lines)
    assert pl["revenue"].sum() == pytest.approx(lines["sales"].sum(), abs=0.01)
    exact = pl.groupby("product_line")["revenue"].sum()
    assert exact["Trains"] == pytest.approx(lines.loc[lines.product_line == "Trains", "sales"].sum())


def test_v1_allocation_error_is_documented(lines, orders):
    cmp = kpis.equal_split_product_revenue(lines, orders).set_index("product_line")
    assert cmp.loc["Trains", "v1_error_pct"] > 1.0      # overstated by >100%
    assert cmp.loc["Planes", "v1_error_pct"] < -0.2     # understated by >20%


def test_monthly_spine_has_every_month(orders):
    m = kpis.monthly(orders)
    assert len(m) == 29  # Jan 2018 .. May 2020
    assert m["total_revenue"].sum() == pytest.approx(orders["order_revenue"].sum())


def test_country_low_sample_flag(orders):
    c = kpis.by_country(orders).set_index("country")
    assert c.loc["Sweden", "low_sample_flag"] == 1 and c.loc["Sweden", "total_orders"] == 7
    assert c.loc["USA", "low_sample_flag"] == 0
    assert c["total_revenue"].sum() == pytest.approx(orders["order_revenue"].sum())


# ---------------------------------------------------------------- RFM
def test_rfm_scores_point_the_right_way(customers):
    """v1 bug: the biggest customers got F = M = 1."""
    top = customers.sort_values("monetary", ascending=False).iloc[0]
    assert top["customer_name"] == "Euro Shopping Channel"
    assert top["M_score"] == 4 and top["F_score"] == 4
    assert top["value_tier"] == "High Value"


def test_rfm_scores_monotonic(customers):
    assert customers.groupby("M_score")["monetary"].mean().is_monotonic_increasing
    assert customers.groupby("R_score")["recency_days"].mean().is_monotonic_decreasing


def test_value_tiers_ordered_by_revenue(customers):
    avg = customers.groupby("value_tier")["monetary"].mean()
    assert avg["High Value"] > avg["Mid Value"] > avg["Low Value"]


def test_tied_values_share_a_score(customers):
    assert customers.groupby("frequency")["F_score"].nunique().max() == 1


def test_legacy_v1_tiers_were_inverted(customers):
    v1 = segmentation.legacy_v1_value_tier(customers)
    avg = customers.groupby(v1)["monetary"].mean()
    assert avg["Low Value"] > avg["High Value"]


# ---------------------------------------------------------------- clustering
def test_cluster_labels_match_profiles(customers):
    """v1 named the 2-day-recency, £784k cluster 'Dormant'. Labels must follow the data."""
    prof = customers.groupby("cluster_label").agg(rec=("recency_days", "median"), mon=("monetary", "median"))
    for label, row in prof.iterrows():
        if "Active" in label:
            assert row["rec"] <= 90
        if "Lapsed" in label:
            assert row["rec"] > 270
    assert customers["cluster_label"].nunique() == customers["cluster"].nunique()


# ---------------------------------------------------------------- model
def test_model_is_honest(customers):
    res = modelling.run(customers)
    ols = res["ols_full"].set_index("term")
    lo, hi = ols.loc["log_frequency", ["ci_low", "ci_high"]]
    assert lo < 1 < hi                                       # ~proportional to order count
    assert ols.loc["had_order_at_risk_or_lost", "p_value"] > 0.05   # no evidence of effect
    cv = res["cv"].set_index("model")["cv_r2_mean"]
    assert cv.iloc[1] <= cv.iloc[0] + 0.05                    # extra features add nothing out of sample
    assert np.isfinite(cv).all()
