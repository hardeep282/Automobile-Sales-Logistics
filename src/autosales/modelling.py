"""Revenue-driver analysis done honestly.

v1 regressed total customer revenue on order count (frequency), product
breadth and shipping reliability, reported R² = 0.971 on an 18-customer
test split, and read the unscaled coefficients as "drivers".

Problems:
- Revenue = frequency x average order value, so a high R² from frequency
  is close to arithmetic, not insight.
- n_unique_products rises mechanically with the number of orders.
- One 80/20 split of 89 customers leaves 18 test rows: R² is unstable.
- Unscaled coefficients are in different units, so their sizes cannot be
  compared as "impact".

v2 approach:
1. Log-log OLS with robust (HC3) standard errors: the coefficient on
   log(frequency) is an elasticity, and every coefficient gets a 95% CI
   and p-value.
2. Repeated 5-fold cross-validation (20 repeats = 100 fits) to compare a
   frequency-only baseline with the full model. If adding recency and
   fulfilment issues does not improve out-of-sample R², they add nothing.
3. Sensitivity check without the two very large accounts.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import RepeatedKFold, cross_val_score

from .config import RANDOM_STATE


def model_frame(cust: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_name": cust["customer_name"],
            "log_revenue": np.log(cust["monetary"]),
            "log_frequency": np.log(cust["frequency"]),
            "recency_days": cust["recency_days"],
            "had_order_at_risk_or_lost": ((cust["at_risk_orders"] + cust["lost_orders"]) > 0).astype(int),
            "frequency": cust["frequency"],
        }
    )


FULL = ["log_frequency", "recency_days", "had_order_at_risk_or_lost"]
BASELINE = ["log_frequency"]


def ols(frame: pd.DataFrame, features=FULL) -> pd.DataFrame:
    X = sm.add_constant(frame[features])
    fit = sm.OLS(frame["log_revenue"], X).fit(cov_type="HC3")
    ci = fit.conf_int()
    return pd.DataFrame(
        {
            "coef": fit.params,
            "ci_low": ci[0],
            "ci_high": ci[1],
            "p_value": fit.pvalues,
        }
    ).assign(r2=fit.rsquared, n=int(fit.nobs)).reset_index(names="term")


def cv_compare(frame: pd.DataFrame) -> pd.DataFrame:
    cv = RepeatedKFold(n_splits=5, n_repeats=20, random_state=RANDOM_STATE)
    rows = []
    for name, feats in [("Baseline: order count only", BASELINE), ("Full: + recency + fulfilment issue", FULL)]:
        s = cross_val_score(LinearRegression(), frame[feats], frame["log_revenue"], cv=cv, scoring="r2")
        rows.append({"model": name, "cv_r2_mean": s.mean(), "cv_r2_std": s.std(), "n_fits": len(s)})
    return pd.DataFrame(rows)


def run(cust: pd.DataFrame) -> dict:
    frame = model_frame(cust)
    full = ols(frame)
    no_whales = ols(frame[frame["frequency"] < 10])
    return {
        "n_customers": int(len(frame)),
        "customers_with_issue": int(frame["had_order_at_risk_or_lost"].sum()),
        "ols_full": full,
        "ols_without_two_largest": no_whales,
        "cv": cv_compare(frame),
    }
