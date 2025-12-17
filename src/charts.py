from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


# ----------------------------
# Shared orders + palettes (exactly like your notebook)
# ----------------------------
ORDER_VT = ['High Value', 'Mid Value', 'Low Value']

PALETTE_VT = [
    "#1B5E20",  # Executive Green (High Value)
    "#F9A825",  # Business Yellow (Mid Value)
    "#B71C1C"   # Strategic Red (Low Value)
]

ORDER_SHIP = ['Critical', 'Unreliable', 'Minor Issues', 'Reliable']

PALETTE_SHIP = [
    "#B71C1C",  # Strategic Red (Critical)
    "#E65100",  # Deep Orange (Unreliable)
    "#F9A825",  # Business Yellow (Minor Issues)
    "#1B5E20"   # Executive Green (Reliable)
]


def _save_fig(fig, save_path: str | Path | None):
    if not save_path:
        return
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=300, bbox_inches="tight")


# ----------------------------
# Chart 1: Customer Distribution by RFM Value Tier (COUNT + %)
# ----------------------------
def chart1_value_tier_count(rfm: pd.DataFrame, save_path: str | Path | None = None):
    fig = plt.figure(figsize=(10, 5))

    ax = sns.countplot(
        data=rfm,
        x='value_tier',
        order=ORDER_VT,
        palette=PALETTE_VT,
        edgecolor='black',
        linewidth=0.6
    )

    plt.title(
        "Customer Distribution by RFM Value Tier",
        fontsize=14,
        fontweight='bold',
        pad=20
    )
    plt.xlabel("Value Tier (RFM-Based)", fontsize=11, labelpad=10)
    plt.ylabel("Number of Customers", fontsize=11, labelpad=10)

    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.3)

    total = len(rfm)
    for p in ax.patches:
        count = p.get_height()
        percent = (count / total) * 100 if total else 0
        x = p.get_x() + p.get_width() / 2
        y = p.get_height()
        ax.text(
            x,
            y + (total * 0.005 if total else 0.5),
            f"{percent:.1f}%",
            ha='center',
            va='bottom',
            fontsize=9,
            fontweight='bold'
        )

    ax.margins(y=0.12)
    plt.tight_layout()

    _save_fig(fig, save_path)
    return fig


# ----------------------------
# Chart 2: Total Revenue Contribution by RFM Value Tier (BAR + £ labels)
# ----------------------------
def chart2_value_tier_revenue(rfm: pd.DataFrame, save_path: str | Path | None = None):
    fig = plt.figure(figsize=(10, 5))

    value_revenue_plot = (
        rfm.groupby('value_tier')['monetary_sales']
           .sum()
           .reindex(ORDER_VT)
           .reset_index()
    )

    ax = sns.barplot(
        data=value_revenue_plot,
        x='value_tier',
        y='monetary_sales',
        order=ORDER_VT,
        palette=PALETTE_VT,
        edgecolor='black',
        linewidth=0.6
    )

    plt.title(
        "Total Revenue Contribution by RFM Value Tier",
        fontsize=14,
        fontweight='bold',
        pad=20
    )
    plt.xlabel("Value Tier (RFM-Based)", fontsize=11, labelpad=10)
    plt.ylabel("Total Revenue", fontsize=11, labelpad=10)

    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.3)

    max_val = value_revenue_plot['monetary_sales'].max() if len(value_revenue_plot) else 0
    for p in ax.patches:
        value = p.get_height()
        x = p.get_x() + p.get_width() / 2
        y = p.get_height()
        ax.text(
            x,
            y + (max_val * 0.015 if max_val else 0.5),
            f"£{value:,.0f}",
            ha='center',
            va='bottom',
            fontsize=9,
            fontweight='bold'
        )

    ax.margins(y=0.18)
    plt.tight_layout()

    _save_fig(fig, save_path)
    return fig


# ----------------------------
# Chart 3: Customer Distribution by Shipping Reliability (COUNT + %)
# ----------------------------
def chart3_shipping_bucket_count(rfm: pd.DataFrame, save_path: str | Path | None = None):
    fig = plt.figure(figsize=(10, 5))

    ax = sns.countplot(
        data=rfm,
        x='ship_bucket',
        order=ORDER_SHIP,
        palette=PALETTE_SHIP,
        edgecolor='black',
        linewidth=0.6
    )

    plt.title(
        "Customer Distribution by Shipping Reliability",
        fontsize=14,
        fontweight='bold',
        pad=20
    )
    plt.xlabel("Shipping Reliability Bucket", fontsize=11, labelpad=10)
    plt.ylabel("Number of Customers", fontsize=11, labelpad=10)

    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.3)

    total = len(rfm)
    for p in ax.patches:
        count = p.get_height()
        percent = (count / total) * 100 if total else 0
        x = p.get_x() + p.get_width() / 2
        y = p.get_height()
        ax.text(
            x,
            y + (total * 0.005 if total else 0.5),
            f"{percent:.1f}%",
            ha='center',
            va='bottom',
            fontsize=9,
            fontweight='bold'
        )

    ax.margins(y=0.14)
    plt.tight_layout()

    _save_fig(fig, save_path)
    return fig


# ----------------------------
# Chart 4: Heatmap Value Tier × Shipping Reliability (%)
# ----------------------------
def chart4_value_vs_shipping_heatmap(rfm: pd.DataFrame, save_path: str | Path | None = None):
    # Cross-tab & row-wise %
    cross_tab = pd.crosstab(rfm['value_tier'], rfm['ship_bucket'])
    cross_percent = cross_tab.div(cross_tab.sum(axis=1), axis=0) * 100

    plot_data = cross_percent.loc[ORDER_VT, ORDER_SHIP]
    annot_labels = plot_data.round(1).astype(str) + "%"

    fig = plt.figure(figsize=(8, 5))
    ax = sns.heatmap(
        plot_data,
        annot=annot_labels,
        fmt="",
        cmap="YlGnBu",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "% of Customers in Value Tier"}
    )

    plt.title(
        "Value Tier × Shipping Reliability (%)",
        fontsize=14,
        fontweight='bold',
        pad=15
    )
    plt.xlabel("Shipping Reliability Bucket", fontsize=11, labelpad=10)
    plt.ylabel("Value Tier (RFM-Based)", fontsize=11, labelpad=10)

    plt.xticks(rotation=0, fontsize=10)
    plt.yticks(rotation=0, fontsize=10)

    plt.tight_layout()

    _save_fig(fig, save_path)
    return fig
