# KPI definitions

One definition per KPI, implemented three times. CI checks that the SQL and Python versions agree.

| Where | File |
|---|---|
| SQL | `sql/03_gold_model.sql` (`gold.kpi_*` views) |
| Python | `src/autosales/kpis.py` |
| Power BI | `_Measures` table in `powerbi/…SemanticModel/definition/tables/_Measures.tmdl` |

## Order status → status group

| Source status | Group | Fulfilled | Open | At risk | Lost | Failed | Had issue |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|
| SHIPPED | Fulfilled | 1 | | | | | |
| RESOLVED | Fulfilled | 1 | | | | | 1 |
| IN PROCESS | Open | | 1 | | | | |
| ON HOLD | At Risk | | | 1 | | | 1 |
| DISPUTED | At Risk | | | 1 | | 1 | 1 |
| CANCELLED | Lost | | | | 1 | 1 | 1 |

Why IN PROCESS is *Open*: every IN PROCESS line is dated 29–31 May 2020, the last three days in the data, so these orders are simply still in the pipeline. v1 counted them as "stuck".

## KPIs

| KPI | Formula | Value (all data) |
|---|---|---|
| Total revenue | Σ line `sales` | £9,760,221.71 |
| Total orders | distinct `order_number` | 298 |
| Avg order value | revenue ÷ orders | £32,752 |
| Closed orders | orders − open orders | 292 |
| **Fulfilment rate** | fulfilled ÷ closed | 96.2% (281 / 292) |
| Issue rate | orders with issue ÷ closed | 5.1% (15 / 292) |
| **Failure rate** | (cancelled + disputed) ÷ all orders | 2.35% (7 / 298) |
| **Revenue at risk** | revenue on ON HOLD + DISPUTED | £251,192 (2.6%) |
| **Revenue lost** | revenue on CANCELLED | £194,487 (2.0%) |
| Open pipeline | revenue on IN PROCESS | £144,730 |
| Revenue vs list | Σ sales ÷ Σ (MSRP × qty) − 1 | positive = sold above MSRP |
| Low-sample flag | country with < 10 orders | 14 of 19 countries |

## Customer metrics (Python)

| Metric | Definition |
|---|---|
| Recency | days from last order to 01 Jun 2020 (the day after the last order) |
| Frequency | distinct orders |
| Monetary | Σ sales |
| R / F / M score | 1–4 from percentile rank (`method="average"`, so ties share a score); higher is better |
| Value tier | RFM score 10–12 High · 7–9 Mid · 3–6 Low |
| RFM segment | R ≥ 3 and (F+M)/2 ≥ 3 → Champions · R ≥ 3 only → Potential Loyalists · (F+M)/2 ≥ 3 only → At Risk – High Value · neither → Hibernating |
| Fulfilment experience | any order at risk or lost → "Order at risk / lost" · any other issue → "Issue resolved" · else "Clean record" |
