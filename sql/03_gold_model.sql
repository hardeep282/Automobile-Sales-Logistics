/* =====================================================================
   03_gold_model.sql  —  GOLD (business-ready)
   ---------------------------------------------------------------------
   Two kinds of objects:

   1) STAR SCHEMA consumed by Power BI
        gold.fact_order_lines   grain: one order line   (2,747 rows)
        gold.dim_customer       grain: one customer     (89)
        gold.dim_product        grain: one product code (109)
        gold.dim_country        grain: one country      (19)
        gold.dim_status         grain: one status       (6)
      (the date dimension is built inside Power BI and marked as a
       date table — see powerbi/ README)

   2) ANALYSIS VIEWS for SQL-side reporting and reconciliation
        gold.order_summary            grain: one order (298)
        gold.kpi_headline             one row of headline KPIs
        gold.kpi_monthly              one row per calendar month
        gold.kpi_country              one row per country
        gold.kpi_product_line_monthly one row per product line per month

   v1 -> v2 fixes made here
   - Product-line revenue now comes from the line-level SALES column.
     v1 split each ORDER's revenue equally across its product lines
     (alloc_weight = 1/n). Line revenue already exists, so no
     allocation is needed: the equal split overstated Trains by ~138%
     and understated Planes by ~25%.
   - One status definition (silver.ref_order_status) instead of two
     different "high risk" definitions in two views.
   - Objects are created in dependency order with CREATE OR ALTER, so
     the script runs cleanly top-to-bottom on a fresh database
     (v1 created a view that referenced the bridge before the bridge
     existed, then replaced it with the double-counting version).

   KPI DEFINITIONS (identical in SQL, Python and DAX)
     total_orders         COUNT(DISTINCT order_number)
     total_revenue        SUM(sales)
     avg_order_value      total_revenue / total_orders
     closed_orders        total_orders - open_orders
     fulfilment_rate      fulfilled_orders / closed_orders
     issue_rate           orders_with_issue / closed_orders
     failure_rate         failed_orders (CANCELLED + DISPUTED) / total_orders
     revenue_at_risk      revenue on ON HOLD + DISPUTED orders
     revenue_lost         revenue on CANCELLED orders
     open_pipeline        revenue on IN PROCESS orders

   Industry equivalent: dbt "marts" (fct_ / dim_ models) with the KPI
   definitions held once in a semantic layer (dbt Semantic Layer /
   MetricFlow, Cube, LookML).
   ===================================================================== */

USE autosales_DB;
GO

/* =====================================================================
   1) STAR SCHEMA
   ===================================================================== */

CREATE OR ALTER VIEW gold.dim_status AS
SELECT status, status_group, status_sort,
       CASE status_group WHEN N'Fulfilled' THEN 1 WHEN N'Open' THEN 2
                         WHEN N'At Risk'   THEN 3 ELSE 4 END AS status_group_sort,
       is_fulfilled, is_open, is_at_risk, is_lost, is_failed, had_issue
FROM silver.ref_order_status;
GO

CREATE OR ALTER VIEW gold.dim_country AS
SELECT DISTINCT
    country,
    CASE
        WHEN country IN (N'USA', N'Canada')                                   THEN N'North America'
        WHEN country IN (N'Australia', N'Japan', N'Philippines', N'Singapore') THEN N'APAC'
        ELSE N'EMEA'
    END AS region
FROM silver.order_lines
WHERE country IS NOT NULL;
GO

CREATE OR ALTER VIEW gold.dim_customer AS
SELECT
    customer_name,
    MAX(contact_name) AS contact_name,
    MAX(city)         AS city,
    MAX(country)      AS country
FROM silver.order_lines
WHERE customer_name IS NOT NULL
GROUP BY customer_name;      -- tested: one city / country / contact per customer
GO

CREATE OR ALTER VIEW gold.dim_product AS
SELECT
    product_code,
    MAX(product_line) AS product_line,
    MAX(msrp)         AS msrp
FROM silver.order_lines
WHERE product_code IS NOT NULL
GROUP BY product_code;       -- tested: one product line / MSRP per product
GO

CREATE OR ALTER VIEW gold.fact_order_lines AS
SELECT
    order_number,
    order_line_number,
    order_date,
    customer_name,           -- FK -> dim_customer
    product_code,            -- FK -> dim_product
    country,                 -- FK -> dim_country (kept on the fact for a clean star)
    status,                  -- FK -> dim_status
    deal_size,               -- line-level attribute in the source (based on line value)
    quantity,
    price_each,
    msrp,
    sales,
    list_value,
    price_vs_msrp_pct
FROM silver.order_lines;
GO

/* =====================================================================
   2) ANALYSIS VIEWS
   ===================================================================== */

-- One row per order. Status / customer / country / date are constant
-- within an order (enforced by tests in 05_data_quality_tests.sql), so
-- MAX() simply picks that single value.
CREATE OR ALTER VIEW gold.order_summary AS
SELECT
    order_number,
    MAX(order_date)                   AS order_date,
    MAX(order_month)                  AS order_month,
    MAX(customer_name)                AS customer_name,
    MAX(country)                      AS country,
    MAX(status)                       AS status,
    MAX(status_group)                 AS status_group,
    MAX(is_fulfilled)                 AS is_fulfilled,
    MAX(is_open)                      AS is_open,
    MAX(is_at_risk)                   AS is_at_risk,
    MAX(is_lost)                      AS is_lost,
    MAX(is_failed)                    AS is_failed,
    MAX(had_issue)                    AS had_issue,
    COUNT(*)                          AS n_lines,
    COUNT(DISTINCT product_line)      AS n_product_lines,
    SUM(quantity)                     AS units,
    SUM(sales)                        AS order_revenue,
    SUM(list_value)                   AS order_list_value
FROM silver.order_lines
GROUP BY order_number;
GO

-- The KPI arithmetic below is repeated per grain (headline / month /
-- country) to keep each view readable on its own. If you change a
-- definition, change it in all three and in the header above.

CREATE OR ALTER VIEW gold.kpi_headline AS
SELECT
    COUNT(*)                                                         AS total_orders,
    SUM(order_revenue)                                               AS total_revenue,
    CAST(SUM(order_revenue) / NULLIF(COUNT(*), 0) AS DECIMAL(12,2))  AS avg_order_value,
    SUM(is_fulfilled)                                                AS fulfilled_orders,
    SUM(is_open)                                                     AS open_orders,
    SUM(is_at_risk)                                                  AS at_risk_orders,
    SUM(is_lost)                                                     AS lost_orders,
    SUM(is_failed)                                                   AS failed_orders,
    CAST(1.0 * SUM(is_fulfilled) / NULLIF(COUNT(*) - SUM(is_open), 0) AS DECIMAL(9,4)) AS fulfilment_rate,
    CAST(1.0 * SUM(had_issue)    / NULLIF(COUNT(*) - SUM(is_open), 0) AS DECIMAL(9,4)) AS issue_rate,
    CAST(1.0 * SUM(is_failed)    / NULLIF(COUNT(*), 0)                AS DECIMAL(9,4)) AS failure_rate,
    SUM(CASE WHEN is_at_risk = 1 THEN order_revenue ELSE 0 END)      AS revenue_at_risk,
    CAST(SUM(CASE WHEN is_at_risk = 1 THEN order_revenue ELSE 0 END)
         / NULLIF(SUM(order_revenue), 0) AS DECIMAL(9,4))            AS revenue_at_risk_pct,
    SUM(CASE WHEN is_lost = 1 THEN order_revenue ELSE 0 END)         AS revenue_lost,
    SUM(CASE WHEN is_open = 1 THEN order_revenue ELSE 0 END)         AS open_pipeline_revenue
FROM gold.order_summary;
GO

-- Calendar spine so months with no orders still appear (v1 used LAG over
-- existing rows only, which silently compared non-adjacent months).
CREATE OR ALTER VIEW gold.kpi_monthly AS
WITH bounds AS (
    SELECT MIN(order_month) AS first_month, MAX(order_month) AS last_month
    FROM gold.order_summary
),
months AS (
    SELECT first_month AS month_start, last_month FROM bounds
    UNION ALL
    SELECT DATEADD(MONTH, 1, month_start), last_month
    FROM months
    WHERE month_start < last_month
)
SELECT
    m.month_start                                                    AS order_month,
    COUNT(o.order_number)                                            AS total_orders,
    COALESCE(SUM(o.order_revenue), 0)                                AS total_revenue,
    COALESCE(SUM(o.is_open), 0)                                      AS open_orders,
    COALESCE(SUM(o.is_failed), 0)                                    AS failed_orders,
    CAST(1.0 * SUM(o.is_fulfilled)
         / NULLIF(COUNT(o.order_number) - SUM(o.is_open), 0) AS DECIMAL(9,4)) AS fulfilment_rate,
    CAST(1.0 * SUM(o.is_failed) / NULLIF(COUNT(o.order_number), 0) AS DECIMAL(9,4)) AS failure_rate,
    COALESCE(SUM(CASE WHEN o.is_at_risk = 1 THEN o.order_revenue END), 0) AS revenue_at_risk,
    COALESCE(SUM(CASE WHEN o.is_lost    = 1 THEN o.order_revenue END), 0) AS revenue_lost
FROM months AS m
LEFT JOIN gold.order_summary AS o
       ON o.order_month = m.month_start
GROUP BY m.month_start;
GO

CREATE OR ALTER VIEW gold.kpi_country AS
SELECT
    o.country,
    c.region,
    COUNT(*)                                                         AS total_orders,
    SUM(o.order_revenue)                                             AS total_revenue,
    SUM(o.is_failed)                                                 AS failed_orders,
    SUM(o.is_at_risk)                                                AS at_risk_orders,
    CAST(1.0 * SUM(o.is_fulfilled) / NULLIF(COUNT(*) - SUM(o.is_open), 0) AS DECIMAL(9,4)) AS fulfilment_rate,
    CAST(1.0 * SUM(o.is_failed)    / NULLIF(COUNT(*), 0)                  AS DECIMAL(9,4)) AS failure_rate,
    SUM(CASE WHEN o.is_at_risk = 1 THEN o.order_revenue ELSE 0 END)  AS revenue_at_risk,
    CAST(SUM(CASE WHEN o.is_at_risk = 1 THEN o.order_revenue ELSE 0 END)
         / NULLIF(SUM(o.order_revenue), 0) AS DECIMAL(9,4))          AS revenue_at_risk_pct,
    SUM(CASE WHEN o.is_lost = 1 THEN o.order_revenue ELSE 0 END)     AS revenue_lost,
    -- with fewer than 10 orders a single bad order moves the rate by 10+
    -- points (Sweden / Denmark: 1 failed order out of 7 = 14.3%)
    CASE WHEN COUNT(*) < 10 THEN 1 ELSE 0 END                        AS low_sample_flag
FROM gold.order_summary AS o
LEFT JOIN gold.dim_country AS c
       ON c.country = o.country
GROUP BY o.country, c.region;
GO

-- Exact product-line revenue from line-level sales: no allocation needed.
CREATE OR ALTER VIEW gold.kpi_product_line_monthly AS
WITH bounds AS (
    SELECT MIN(order_month) AS first_month, MAX(order_month) AS last_month
    FROM silver.order_lines
),
months AS (
    SELECT first_month AS month_start, last_month FROM bounds
    UNION ALL
    SELECT DATEADD(MONTH, 1, month_start), last_month
    FROM months
    WHERE month_start < last_month
),
spine AS (
    SELECT m.month_start, p.product_line
    FROM months AS m
    CROSS JOIN (SELECT DISTINCT product_line FROM silver.order_lines) AS p
)
SELECT
    s.month_start                                                     AS order_month,
    s.product_line,
    COUNT(DISTINCT l.order_number)                                    AS orders,
    COALESCE(SUM(l.quantity), 0)                                      AS units,
    COALESCE(SUM(l.sales), 0)                                         AS revenue,
    COALESCE(SUM(CASE WHEN l.is_at_risk = 1 THEN l.sales END), 0)     AS revenue_at_risk,
    COALESCE(SUM(CASE WHEN l.is_lost    = 1 THEN l.sales END), 0)     AS revenue_lost,
    COUNT(DISTINCT CASE WHEN l.is_failed = 1 THEN l.order_number END) AS failed_orders
FROM spine AS s
LEFT JOIN silver.order_lines AS l
       ON l.order_month  = s.month_start
      AND l.product_line = s.product_line
GROUP BY s.month_start, s.product_line;
GO

-- Expected headline (v2 definitions): 298 orders, 9,760,221.71 revenue
SELECT * FROM gold.kpi_headline;
GO
