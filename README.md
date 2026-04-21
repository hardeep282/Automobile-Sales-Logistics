# Automobile Sales \& Logistics — Customer Intelligence Platform

> \\\*\\\*End-to-end commercial analytics project\\\*\\\* | SQL Server · Python · Power BI  
> Built to answer a single business question: \\\*which customers are worth protecting, and which represent a hidden commercial or operational risk?\\\*

\---

## Project Overview

This project analyses a transactional automobile sales dataset of **2,747 order records across 89 customers**, spanning multiple product lines, countries, and deal sizes. The goal was not to build a model for its own sake — it was to produce a set of commercial insights that a Sales or Account Management team could act on immediately.

The pipeline runs end-to-end: raw data ingestion and cleaning in SQL Server, customer-level feature engineering and machine learning in Python, and a Power BI dashboard for stakeholder reporting.

\---

## Business Questions Addressed

* Which customers generate the most revenue — and which of those are at operational risk?
* What drives customer revenue, and where should commercial effort be focused?
* How do customers segment by purchasing behaviour and shipping reliability?
* Where are the fulfilment risks concentrated, and what is the revenue exposure?

\---

## Tech Stack

|Layer|Tools Used|
|-|-|
|Data Architecture|SQL Server Express (SSMS)|
|Data Cleaning \& EDA|Python — Pandas, NumPy|
|Machine Learning|Scikit-learn — K-Means, Linear Regression, PCA|
|Visualisation|Matplotlib, Seaborn, Plotly, Power BI|
|Environment|Jupyter Notebook, Virtual Environment (.venv)|

\---

## Data Architecture — Bronze · Silver · Gold

The project follows a layered SQL architecture to separate raw data from clean data from analytical outputs. This keeps the pipeline auditable and rebuilding any layer does not require re-ingesting source data.

```
Raw Source
    │
    ▼
Bronze Layer  ──  dbo.bronze\\\_autosales
                  Exact copy of source data. No transformations.
                  Purpose: Auditability and reprocessing baseline.
    │
    ▼
Silver Layer  ──  dbo.silver\\\_auto\\\_sales (VIEW)
                  Cleaned and standardised.
                  Key transformations:
                  · Date parsing with TRY\\\_CONVERT (handles mixed formats)
                  · Derived: pricing\\\_gap = (MSRP − PRICEEACH) × QUANTITYORDERED
                  · Derived: discount\\\_pct = 1 − (PRICEEACH / MSRP)
                  · Status normalised → binary: Shipped / Not Shipped
                  · String trimming and case standardisation
    │
    ▼
Gold Layer    ──  dbo.gold\\\_orders (VIEW)
                  dbo.gold\\\_monthly\\\_revenue (VIEW)
                  Aggregated for business reporting.
                  Key features:
                  · Order-level risk flags: failure\\\_flag, high\\\_risk\\\_flag, high\\\_discount\\\_flag
                  · Monthly revenue and order counts
                  · Pricing gap aggregated per order
```

**Data quality checks at Bronze layer confirmed:**

* 2,747 rows, 20 features — zero nulls, zero duplicates
* Sales range: £483 – £14,082 per line item
* MSRP per unit: £33 – £214
* Quantity ordered: 6 – 97 units

\---

## Feature Engineering — Customer-Level Aggregation

Transaction data was aggregated from order-line level to **89 unique customers**, each described by six analytical features:

|Feature|Description|How Calculated|
|-|-|-|
|`recency\\\_days`|Days since last order|Analysis date (2020-06-01) minus max order date|
|`frequency\\\_orders`|Number of unique orders|COUNT DISTINCT of order numbers|
|`monetary\\\_sales`|Total revenue|SUM of sales|
|`avg\\\_totalmsrp`|Average MSRP exposure per order|MEAN of (MSRP × Quantity)|
|`n\\\_unique\\\_products`|Product breadth|COUNT DISTINCT of product codes|
|`shipping\\\_reliability`|% of orders successfully shipped|MEAN of binary shipped flag|

\---

## RFM Segmentation

Customers were scored on Recency, Frequency, and Monetary dimensions using quartile-based ranking. Scores were summed into an RFM composite, then banded into three value tiers:

|Value Tier|Customers|Total Revenue|Avg Revenue per Customer|
|-|-|-|-|
|**High Value**|27|£1,682,711|£62,323|
|**Mid Value**|51|£6,417,403|£125,831|
|**Low Value**|11|£1,660,107|£150,919|

A fourth dimension — **Shipping Reliability** — was overlaid to identify fulfilment risk within each tier, producing a composite segment (e.g. *High Value – Fulfilment Risk*, *Mid Value – Growth Potential*):

|Segment|Customers|
|-|-|
|Mid Value – Growth Potential|43|
|High Value – Stable VIP|21|
|Low Value – Stable (Upsell Test)|10|
|Mid Value – Fulfilment Risk|8|
|High Value – Fulfilment Risk|6|
|Low Value – High Risk|1|

> \\\*\\\*Key finding:\\\*\\\* 6 High Value customers carry active fulfilment risk. These are the highest-priority accounts for an SLA review — they are commercially significant and operationally exposed simultaneously.

\---

## K-Means Clustering

K-Means was applied across all five customer features (MinMax scaled) to validate and extend the RFM segmentation with a data-driven grouping. k=4 was selected using the elbow method and silhouette scoring.

|Cluster|Label|Customers|Avg Recency|Avg Orders|Avg Revenue|Avg Unique Products|Shipping Reliability|
|-|-|-|-|-|-|-|-|
|2|**Ultra VIP Heavy Buyers**|2|2 days|21.5|£783,576|91.5 products|0.90|
|1|**Core Stable Buyers**|14|69 days|3.5|£113,691|29.5 products|0.60|
|0|**VIP High Spenders**|62|165 days|3.0|£94,612|24.2 products|1.00|
|3|**Dormant / At Risk**|11|444 days|2.1|£66,862|18.1 products|1.00|

PCA (2 components) was applied for visual cluster separation and confirmed clean boundaries between the Ultra VIP and Dormant segments.

> \\\*\\\*Commercial interpretation:\\\*\\\* The Ultra VIP cluster (Cluster 2) represents 2 customers generating nearly £800K average revenue each. Despite the small count, this group warrants dedicated account management — any churn here has disproportionate revenue impact.

\---

## Revenue Driver Analysis — Linear Regression

A Linear Regression model was built on the 89-customer dataset to identify which features drive total customer revenue. The model was trained on an 80/20 train-test split.

**Model performance:**

* R² Score: 0.971
* RMSE: £23,200

**Coefficient interpretation (unscaled — revenue impact per 1 unit increase):**

|Feature|Revenue Impact|
|-|-|
|`frequency\\\_orders`|+£23,686 per additional order|
|`n\\\_unique\\\_products`|+£3,267 per additional unique product|
|`shipping\\\_reliability`|+£2,981 per 1% improvement|
|`recency\\\_days`|+£67 per additional day|
|`avg\\\_totalmsrp`|+£16 per £1 MSRP increase|

> \\\*\\\*Commercial interpretation:\\\*\\\* Order frequency is the dominant revenue driver by a significant margin. A strategy focused on increasing purchase frequency — through relationship management, promotional timing, or product range expansion — has the highest expected revenue return per unit of effort.

\---

## Key Findings Summary

|Finding|Detail|
|-|-|
|Total customers analysed|89|
|Total revenue in dataset|£9,760,222|
|High Value customers at fulfilment risk|6 (22% of High Value base)|
|Dominant revenue driver|Order frequency (+£23,686 per order)|
|Dormant / At Risk customers|11 (444 days avg since last order)|
|Ultra VIP avg revenue|£783,576 per customer|
|82% of customers|Reliable shipping (≥95% shipped)|
|18% of customers|Shipping issues requiring SLA review|

\---

## Repository Structure

```
Automobile-Sales-Logistics/
│
├── Data/
│   ├── Raw-Data/
│   │   └── Auto Sales data.csv
│   └── Cleaned-Data/
│       ├── cust\\\_output.csv          # Customer-level aggregated features
│       └── rfm\\\_output.csv           # RFM scores + segments + cluster labels
│
├── SQL/
│   └── Car\\\_Sales\\\_Query.sql          # Full Bronze–Silver–Gold pipeline
│
├── Python/
│   └── Notebooks/
│       ├── Automobile-Sales-Logistics.ipynb     # EDA + feature engineering
│       ├── Auto\\\_logistics\\\_rfm.ipynb             # RFM scoring + segmentation
│       ├── Auto\\\_logistics\\\_cluster\\\_analysis.ipynb # K-Means clustering
│       ├── Auto\\\_logistics\\\_reg.ipynb             # Linear regression
│       └── Auto\\\_logistics\\\_visuals.ipynb         # Visualisations
│
├── Output/
│   └── Visuals\\\_Plots/               # Exported charts (300 DPI)
│
└── README.md
```

\---

## How to Run

**Prerequisites**

* Python 3.9+
* SQL Server Express (free) with SSMS
* Required Python packages:

```bash
pip install pandas numpy scikit-learn matplotlib seaborn plotly yellowbrick tabulate
```

**Steps**

1. Load `Auto Sales data.csv` into SQL Server as `dbo.autosales\\\_raw`
2. Run `Car\\\_Sales\\\_Query.sql` in order — this builds Bronze, Silver, and Gold layers
3. Run notebooks in sequence: `Automobile-Sales-Logistics` → `rfm` → `cluster\\\_analysis` → `reg` → `visuals`
4. Cleaned outputs (`cust\\\_output.csv`, `rfm\\\_output.csv`) are generated automatically

\---

## About

Built by **Hardeep Bamrah** as part of a commercial analytics portfolio demonstrating end-to-end analytical capability — from raw data architecture through machine learning to business insight.

**MSc Management with Business Analytics** — Bournemouth University  
[linkedin.com/in/hardeep-bamrah-479810234](https://linkedin.com/in/hardeep-bamrah-479810234)

\---

*This project was built on a publicly available automobile sales dataset. All analysis, architecture decisions, and commercial interpretations are original work.*

