"""Behavioural K-Means clustering with an evidence-based choice of k and
labels generated from the cluster profiles.

v1 issues fixed here:
- k=4 was hard-coded with no justification -> now chosen by silhouette
  score over k = 2..8 (elbow / inertia also reported).
- Cluster names were typed by hand and did not match the clusters (the
  2-day-recency, £784k cluster was called "Dormant / At Risk"), and two
  notebooks used two different name maps -> labels are now generated from
  each cluster's own profile, so they cannot drift.
- Heavily skewed features (two customers hold 16% of revenue) dominated
  MinMax scaling -> log-transform frequency and monetary, then standardise.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from .config import RANDOM_STATE

FEATURES = ["recency_days", "frequency", "monetary"]


def feature_matrix(cust: pd.DataFrame) -> np.ndarray:
    X = pd.DataFrame(
        {
            "recency_days": cust["recency_days"],
            "log_frequency": np.log1p(cust["frequency"]),
            "log_monetary": np.log1p(cust["monetary"]),
        }
    )
    return StandardScaler().fit_transform(X)


def select_k(X: np.ndarray, k_range=range(2, 9)) -> pd.DataFrame:
    rows = []
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE).fit(X)
        rows.append({"k": k, "silhouette": silhouette_score(X, km.labels_), "inertia": km.inertia_})
    return pd.DataFrame(rows)


def _label(row: pd.Series, med: pd.Series) -> str:
    value = ("High-value" if row["monetary"] > 1.5 * med["monetary"]
             else "Low-value" if row["monetary"] < 0.75 * med["monetary"] else "Mid-value")
    activity = ("Active" if row["recency_days"] <= 90
                else "Cooling" if row["recency_days"] <= 270 else "Lapsed")
    return f"{value} · {activity}"


def fit_clusters(cust: pd.DataFrame, k: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (customers with cluster + label, cluster profile, k-selection table)."""
    X = feature_matrix(cust)
    selection = select_k(X)
    if k is None:
        k = int(selection.loc[selection["silhouette"].idxmax(), "k"])
    km = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE).fit(X)

    out = cust.copy()
    out["cluster"] = km.labels_
    profile = out.groupby("cluster").agg(
        customers=("customer_name", "count"),
        recency_days=("recency_days", "median"),
        frequency=("frequency", "median"),
        monetary=("monetary", "median"),
        avg_order_value=("avg_order_value", "median"),
        total_revenue=("monetary", "sum"),
    )
    med = out[FEATURES].median()
    profile["label"] = profile.apply(_label, axis=1, med=med)
    # make labels unique if two clusters share a description
    dup = profile["label"].duplicated(keep=False)
    profile.loc[dup, "label"] = profile.loc[dup, "label"] + " (" + profile.loc[dup, "frequency"].astype(int).astype(str) + " orders)"
    profile["revenue_share"] = profile["total_revenue"] / profile["total_revenue"].sum()
    profile = profile.sort_values("total_revenue", ascending=False)

    out["cluster_label"] = out["cluster"].map(profile["label"])
    selection["chosen"] = selection["k"] == k
    return out, profile.reset_index(), selection
