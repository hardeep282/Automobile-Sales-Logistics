"""Paths and business constants shared by the pipeline, notebooks and app."""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (always relative to the repo root, so the code runs on any machine)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = REPO_ROOT / "data" / "raw" / "auto_sales_data.csv"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
FIGURES_DIR = REPO_ROOT / "reports" / "figures"

RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Order status -> business status group.
# Single source of truth; mirrors silver.ref_order_status in SQL.
#
# IN PROCESS rows are all dated 29–31 May 2020 (the last 3 days of the data),
# so they are normal pipeline orders -> "Open", not "stuck".
# ---------------------------------------------------------------------------
STATUS_MAP: dict[str, dict] = {
    #  status         group        fulfilled open at_risk lost failed issue
    "SHIPPED":    dict(group="Fulfilled", fulfilled=1, open=0, at_risk=0, lost=0, failed=0, issue=0),
    "RESOLVED":   dict(group="Fulfilled", fulfilled=1, open=0, at_risk=0, lost=0, failed=0, issue=1),
    "IN PROCESS": dict(group="Open",      fulfilled=0, open=1, at_risk=0, lost=0, failed=0, issue=0),
    "ON HOLD":    dict(group="At Risk",   fulfilled=0, open=0, at_risk=1, lost=0, failed=0, issue=1),
    "DISPUTED":   dict(group="At Risk",   fulfilled=0, open=0, at_risk=1, lost=0, failed=1, issue=1),
    "CANCELLED":  dict(group="Lost",      fulfilled=0, open=0, at_risk=0, lost=1, failed=1, issue=1),
}
STATUS_GROUP_ORDER = ["Fulfilled", "Open", "At Risk", "Lost"]

REGION_MAP = {
    "USA": "North America", "Canada": "North America",
    "Australia": "APAC", "Japan": "APAC", "Philippines": "APAC", "Singapore": "APAC",
}  # everything else -> EMEA

# A country with fewer orders than this gets a low-sample warning: one bad
# order moves its rate by more than 10 percentage points.
LOW_SAMPLE_ORDERS = 10

# ---------------------------------------------------------------------------
# Colours (colour-blind-safe, consistent across app, figures and Power BI)
# ---------------------------------------------------------------------------
COLOURS = {
    "Fulfilled": "#2E7D5B",
    "Open": "#4C78A8",
    "At Risk": "#E69F00",
    "Lost": "#C0392B",
    "primary": "#4C78A8",
    "accent": "#E69F00",
    "muted": "#9AA5B1",
}
TIER_COLOURS = {"High Value": "#2E7D5B", "Mid Value": "#4C78A8", "Low Value": "#9AA5B1"}
