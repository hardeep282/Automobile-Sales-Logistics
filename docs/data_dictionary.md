# Data dictionary

**Source:** `data/raw/auto_sales_data.csv`, the Kaggle "Automobile Sales data" (a variant of the classic *sample sales data* set of scale-model vehicles). 2,747 order lines, 20 columns, UTF-8, LF line endings, dates in `dd/mm/yyyy`. Coverage: 06 Jan 2018 – 31 May 2020.

> Provenance note: this is a public teaching dataset, not real company data. A few customer names carry encoding artefacts from the original file (e.g. `Mart¡n`). They're kept as-is so the data stays faithful to the source.

## Raw columns → silver (`silver.order_lines` / `build_order_lines()`)

| Raw column | Silver column | Type | Notes |
|---|---|---|---|
| ORDERNUMBER | order_number | int | 298 distinct orders |
| ORDERLINENUMBER | order_line_number | int | (order_number, order_line_number) is unique |
| ORDERDATE | order_date, order_month | date | style 103 (`dd/mm/yyyy`) |
| QUANTITYORDERED | quantity | int | 6–97 |
| PRICEEACH | price_each | decimal | unit price actually charged |
| SALES | sales | decimal | = price × qty (rounded to 1 dp; 5 lines differ by £0.02) |
| MSRP | msrp | decimal | list price; constant per product |
| STATUS | status, status_group, is_* flags | text | see `kpi_definitions.md` |
| PRODUCTLINE | product_line | text | 7 lines |
| PRODUCTCODE | product_code | text | 109 products |
| CUSTOMERNAME | customer_name | text | 89 customers, one country/city each |
| CONTACTFIRSTNAME + CONTACTLASTNAME | contact_name | text | |
| CITY, COUNTRY | city, country (+ region) | text | 19 countries → EMEA / North America / APAC |
| DEALSIZE | deal_size | text | Small / Medium / Large, assigned **per line** from line value |
| DAYS_SINCE_LASTORDER | *(not used)* | | meaning undocumented in the source; recency is recomputed from dates |
| PHONE, ADDRESSLINE1, POSTALCODE | *(dropped)* | | personal data; not needed downstream |

Derived in silver: `list_value` = MSRP × qty · `price_vs_msrp_pct` = price ÷ MSRP − 1 · `sales_reconciles` flag.

> **MSRP is not a price ceiling here:** 51% of lines are sold *above* MSRP. v1 labelled `(MSRP − price) × qty` a "profit proxy". There's no cost data, so v2 calls it what it is: price realisation against list price.

## Gold

| Object | Grain | Rows |
|---|---|---|
| gold.fact_order_lines | order line | 2,747 |
| gold.dim_customer | customer | 89 |
| gold.dim_product | product | 109 |
| gold.dim_country | country | 19 |
| gold.dim_status | status | 6 |
| gold.order_summary | order | 298 |
| gold.kpi_headline | – | 1 |
| gold.kpi_monthly | calendar month | 29 |
| gold.kpi_country | country | 19 |
| gold.kpi_product_line_monthly | product line × month | 203 |

## Processed files (`data/processed/`, written by `scripts/run_pipeline.py`)

| File | Content |
|---|---|
| order_summary.csv | one row per order with status flags |
| kpi_*.csv / kpi_headline.json | KPI tables (match the SQL gold views) |
| customer_segments.csv | customer features, RFM scores, tier, segment, cluster |
| cluster_profile.csv, cluster_k_selection.csv | cluster medians/labels; silhouette by k |
| model_*.csv | OLS coefficients with CIs, cross-validation results |
| product_line_v1_vs_v2.csv | the v1 allocation error, kept for documentation |
