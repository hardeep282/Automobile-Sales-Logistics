"""RFM scoring, value tiers and named RFM segments.

v1 bug (fixed here): F and M were ranked with ascending=False and then
labelled 1..4 in qcut, so the BIGGEST customers received the LOWEST score.
Euro Shopping Channel (26 orders, the top customer) came out "Low Value".
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def quartile_score(values: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """Score 1 (worst) .. 4 (best) from percentile rank.

    Uses method="average" so customers with the same value always get the
    same score (v1 used method="first", which broke ties arbitrarily by row
    order). With heavy ties (many customers have exactly 3 orders) some
    scores can end up empty - that is a property of the data, not a bug.
    """
    ranked = values if higher_is_better else -values
    pct = ranked.rank(pct=True, method="average")
    return np.clip(np.ceil(pct * 4), 1, 4).astype(int)


def add_rfm(cust: pd.DataFrame) -> pd.DataFrame:
    out = cust.copy()
    out["R_score"] = quartile_score(out["recency_days"], higher_is_better=False)  # recent = good
    out["F_score"] = quartile_score(out["frequency"])
    out["M_score"] = quartile_score(out["monetary"])
    out["RFM_score"] = out[["R_score", "F_score", "M_score"]].sum(axis=1)  # 3..12

    out["value_tier"] = np.select(
        [out["RFM_score"] >= 10, out["RFM_score"] >= 7], ["High Value", "Mid Value"], default="Low Value"
    )

    # Classic R x FM grid -> four actionable segments
    fm = (out["F_score"] + out["M_score"]) / 2
    recent = out["R_score"] >= 3
    valuable = fm >= 3
    out["rfm_segment"] = np.select(
        [recent & valuable, recent & ~valuable, ~recent & valuable],
        ["Champions", "Potential Loyalists", "At Risk – High Value"],
        default="Hibernating",
    )
    return out


def legacy_v1_value_tier(cust: pd.DataFrame) -> pd.Series:
    """Reproduces the v1 (inverted) scoring, kept only to document the fix."""
    r = pd.qcut(cust["recency_days"].rank(method="first", ascending=True), 4, labels=[4, 3, 2, 1]).astype(int)
    f = pd.qcut(cust["frequency"].rank(method="first", ascending=False), 4, labels=[1, 2, 3, 4]).astype(int)
    m = pd.qcut(cust["monetary"].rank(method="first", ascending=False), 4, labels=[1, 2, 3, 4]).astype(int)
    score = r + f + m
    return pd.Series(
        np.select([score >= 9, score.between(6, 8)], ["High Value", "Mid Value"], default="Low Value"),
        index=cust.index,
    )


SEGMENT_ACTIONS = {
    "Champions": "Protect: account management, priority fulfilment, early access to new lines.",
    "Potential Loyalists": "Grow: cross-sell adjacent product lines to raise order frequency.",
    "At Risk – High Value": "Win back: proactive outreach before they lapse; review any service issues.",
    "Hibernating": "Low-cost reactivation (email / catalogue); do not over-invest.",
}
