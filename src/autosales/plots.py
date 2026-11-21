"""Static matplotlib figures for the README and notebooks (reports/figures).

The Streamlit app builds its own interactive Plotly charts.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

if "ipykernel" not in sys.modules:  # headless (pipeline / CI); notebooks keep inline plots
    matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .config import COLOURS, STATUS_GROUP_ORDER, TIER_COLOURS  # noqa: E402

plt.rcParams.update(
    {
        "figure.dpi": 110,
        "savefig.dpi": 160,
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "axes.titlesize": 12,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--",
    }
)

money = mtick.FuncFormatter(lambda x, _: f"£{x / 1e6:.1f}M" if abs(x) >= 1e6 else f"£{x / 1e3:.0f}k")


def _save(fig, path: Path | None):
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, bbox_inches="tight", facecolor="white")
    return fig


def status_mix(orders: pd.DataFrame, path=None):
    g = orders.groupby("status_group").agg(orders=("order_number", "count"), revenue=("order_revenue", "sum"))
    g = g.reindex(STATUS_GROUP_ORDER)
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    for ax, col, title in [(axes[0], "orders", "Orders by outcome"), (axes[1], "revenue", "Revenue by outcome")]:
        bars = ax.barh(g.index[::-1], g[col][::-1], color=[COLOURS[s] for s in g.index[::-1]])
        ax.set_title(title)
        ax.grid(axis="y", visible=False)
        for b, v in zip(bars, g[col][::-1], strict=True):
            label = f"{int(v)}" if col == "orders" else money(v)
            ax.text(b.get_width(), b.get_y() + b.get_height() / 2, f"  {label}", va="center", fontsize=9)
        if col == "revenue":
            ax.xaxis.set_major_formatter(money)
        ax.margins(x=0.18)
    closed = g["orders"].sum() - g.loc["Open", "orders"]
    fulfilled = g.loc["Fulfilled", "orders"] / closed
    fig.suptitle(f"{fulfilled:.0%} of closed orders fulfilled; {money(g.loc['At Risk', 'revenue'])} sits in "
                 "on-hold / disputed orders",
                 x=0.01, ha="left", fontsize=11, color="#333")
    fig.tight_layout()
    return _save(fig, path)


def monthly_revenue(monthly: pd.DataFrame, path=None):
    fig, ax = plt.subplots(figsize=(11, 3.8))
    ax.bar(monthly["order_month"], monthly["total_revenue"], width=20, color=COLOURS["primary"])
    nov = monthly[monthly["order_month"].dt.month == 11]
    ax.bar(nov["order_month"], nov["total_revenue"], width=20, color=COLOURS["accent"], label="November")
    ax.yaxis.set_major_formatter(money)
    full = monthly[monthly["order_month"].dt.year.isin([2018, 2019])]
    ratio = full.loc[full["order_month"].dt.month == 11, "total_revenue"].mean() / full["total_revenue"].mean()
    ax.set_title(f"Monthly revenue — a strong Q4 peak every year (Nov ≈ {ratio:.1f}× an average month in 2018–19)")
    ax.legend(frameon=False)
    fig.tight_layout()
    return _save(fig, path)


def country_risk(country: pd.DataFrame, path=None):
    fig, ax = plt.subplots(figsize=(9, 5))
    ok = country["low_sample_flag"] == 0
    for mask, kw in [(ok, dict(color=COLOURS["primary"], label="≥ 10 orders")),
                     (~ok, dict(facecolors="none", edgecolors=COLOURS["muted"], label="< 10 orders (low sample)"))]:
        d = country[mask]
        ax.scatter(d["total_revenue"], d["failure_rate"], s=d["total_orders"] * 6 + 20, linewidths=1.2, **kw)
    seen: dict[float, int] = {}
    for _, r in country.sort_values("total_revenue").iterrows():
        if r["failure_rate"] > 0 or r["total_revenue"] > 1e6:
            key = round(r["failure_rate"], 3)
            n = seen.get(key, 0)
            seen[key] = n + 1
            ax.annotate(f"{r['country']} ({int(r['failed_orders'])}/{int(r['total_orders'])})",
                        (r["total_revenue"], r["failure_rate"]), xytext=(8, 4 - 13 * n),
                        textcoords="offset points", fontsize=8.5)
    ax.xaxis.set_major_formatter(money)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_xlabel("Revenue")
    ax.set_ylabel("Failure rate (cancelled + disputed / orders)")
    ax.set_title("Country failure rate vs revenue — labels show failed / total orders")
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    return _save(fig, path)


def product_line_fix(comparison: pd.DataFrame, path=None):
    d = comparison.sort_values("v2_exact")
    y = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.barh(y - 0.2, d["v1_equal_split"], height=0.4, color=COLOURS["muted"], label="v1: order revenue split 1/n")
    ax.barh(y + 0.2, d["v2_exact"], height=0.4, color=COLOURS["primary"], label="v2: exact line-level sales")
    for i, (_, r) in enumerate(d.iterrows()):
        ax.text(max(r["v1_equal_split"], r["v2_exact"]), i, f"  v1 error {r['v1_error_pct']:+.0%}", va="center", fontsize=8.5)
    ax.set_yticks(y, d["product_line"])
    ax.xaxis.set_major_formatter(money)
    ax.grid(axis="y", visible=False)
    ax.margins(x=0.22)
    ax.set_title("Product-line revenue: the v1 allocation misstated every line")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    return _save(fig, path)


def rfm_fix(cust: pd.DataFrame, path=None):
    order = ["High Value", "Mid Value", "Low Value"]
    v1 = cust.groupby("v1_value_tier")["monetary"].mean().reindex(order)
    v2 = cust.groupby("value_tier")["monetary"].mean().reindex(order)
    x = np.arange(3)
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.bar(x - 0.2, v1, 0.4, color=COLOURS["muted"], label="v1 (F & M scores inverted)")
    ax.bar(x + 0.2, v2, 0.4, color=[TIER_COLOURS[t] for t in order], label="v2 (fixed)")
    ax.set_xticks(x, order)
    ax.yaxis.set_major_formatter(money)
    ax.set_title("Average revenue per customer by RFM tier — v1 ranked the best customers lowest")
    ax.legend(frameon=False)
    fig.tight_layout()
    return _save(fig, path)


def tier_share(cust: pd.DataFrame, path=None):
    order = ["High Value", "Mid Value", "Low Value"]
    g = cust.groupby("value_tier").agg(customers=("customer_name", "count"), revenue=("monetary", "sum")).reindex(order)
    share = pd.DataFrame({"Customers": g["customers"] / g["customers"].sum(), "Revenue": g["revenue"] / g["revenue"].sum()})
    fig, ax = plt.subplots(figsize=(8, 2.8))
    left = np.zeros(2)
    for tier in order:
        vals = share.loc[tier].values
        ax.barh(share.columns, vals, left=left, color=TIER_COLOURS[tier], label=tier)
        for i, v in enumerate(vals):
            ax.text(left[i] + v / 2, i, f"{v:.0%}", ha="center", va="center", color="white", fontweight="bold")
        left += vals
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(False)
    ax.set_title(f"High-value customers: {share.loc['High Value', 'Customers']:.0%} of the base, "
                 f"{share.loc['High Value', 'Revenue']:.0%} of revenue")
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.15))
    fig.tight_layout()
    return _save(fig, path)


def k_selection(selection: pd.DataFrame, path=None):
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.plot(selection["k"], selection["silhouette"], marker="o", color=COLOURS["primary"])
    best = selection[selection["chosen"]].iloc[0]
    ax.scatter([best["k"]], [best["silhouette"]], s=160, facecolors="none", edgecolors=COLOURS["accent"], linewidths=2)
    ax.annotate(f"chosen k = {int(best['k'])}", (best["k"], best["silhouette"]), xytext=(10, -14), textcoords="offset points")
    ax.set_xlabel("number of clusters k")
    ax.set_ylabel("silhouette score")
    ax.set_title("Choosing k: highest silhouette score")
    fig.tight_layout()
    return _save(fig, path)


def clusters(cust: pd.DataFrame, path=None):
    fig, ax = plt.subplots(figsize=(9, 5))
    palette = ["#4C78A8", "#2E7D5B", "#E69F00", "#C0392B", "#8E6BB8", "#9AA5B1", "#17BECF", "#7F7F7F"]
    for i, (label, d) in enumerate(cust.groupby("cluster_label")):
        ax.scatter(d["frequency"], d["monetary"], s=60, alpha=0.85, color=palette[i % len(palette)],
                   edgecolor="white", linewidths=0.6, label=f"{label} (n={len(d)})")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(money)
    ax.set_xticks([1, 2, 3, 5, 10, 20], ["1", "2", "3", "5", "10", "20"])
    ax.xaxis.set_minor_formatter(mtick.NullFormatter())
    ax.set_xlabel("orders (log scale)")
    ax.set_ylabel("revenue (log scale)")
    ax.set_title("Customer clusters (K-Means on recency, log-frequency, log-revenue)")
    ax.legend(frameon=False, fontsize=8.5)
    fig.tight_layout()
    return _save(fig, path)


def revenue_drivers(ols: pd.DataFrame, path=None):
    d = ols[ols["term"] != "const"].copy()
    nice = {
        "log_frequency": "log(order count)\n[elasticity]",
        "recency_days": "recency (days)",
        "had_order_at_risk_or_lost": "had order at risk / lost",
    }
    d["label"] = d["term"].map(nice)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    y = np.arange(len(d))
    ax.errorbar(d["coef"], y, xerr=[d["coef"] - d["ci_low"], d["ci_high"] - d["coef"]], fmt="o",
                color=COLOURS["primary"], ecolor=COLOURS["muted"], capsize=4)
    ax.axvline(0, color="#333", lw=1)
    ax.set_yticks(y, d["label"])
    for i, (_, r) in enumerate(d.iterrows()):
        p_txt = "p<0.001" if r["p_value"] < 0.001 else f"p={r['p_value']:.2f}"
        ax.text(r["ci_high"], i, f"  β={r['coef']:.3g}, {p_txt}", va="center", fontsize=8.5)
    ax.margins(x=0.35)
    ax.grid(axis="y", visible=False)
    ax.set_title("What explains customer revenue? (log-revenue OLS, 95% CI, robust SE)")
    fig.tight_layout()
    return _save(fig, path)
