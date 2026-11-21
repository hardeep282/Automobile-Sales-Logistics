/* =====================================================================
   04_kpi_analysis.sql  —  Business questions answered in SQL
   ---------------------------------------------------------------------
   Read-only analysis on top of the gold layer. Each block answers one
   question; expected results (v2) are noted so you can check your run.
   Data covers 06 Jan 2018 – 31 May 2020 (2020 is a PARTIAL year).
   ===================================================================== */

USE autosales_DB;
GO

/* Q1. Headline KPIs
   Expect: 298 orders | 9,760,221.71 revenue | failure 2.35% */
SELECT * FROM gold.kpi_headline;
GO

/* Q2. Where do orders end up? (order-level status mix) */
SELECT status_group, status,
       COUNT(*)                                  AS orders,
       SUM(order_revenue)                        AS revenue,
       CAST(100.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS DECIMAL(5,2)) AS pct_orders
FROM gold.order_summary
GROUP BY status_group, status
ORDER BY MIN(CASE status_group WHEN N'Fulfilled' THEN 1 WHEN N'Open' THEN 2
                               WHEN N'At Risk' THEN 3 ELSE 4 END), orders DESC;
GO

/* Q3. Country risk — read low_sample_flag before ranking!
   Sweden and Denmark show 14.3% failure = 1 failed order out of 7. */
SELECT country, region, total_orders, total_revenue,
       failure_rate, fulfilment_rate, revenue_at_risk, revenue_at_risk_pct,
       revenue_lost, low_sample_flag
FROM gold.kpi_country
ORDER BY total_revenue DESC;
GO

/* Q4. Product-line revenue and exposure (exact, line-level) */
SELECT product_line,
       SUM(revenue)                                                   AS revenue,
       CAST(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER () AS DECIMAL(5,2)) AS revenue_share_pct,
       SUM(revenue_at_risk)                                           AS revenue_at_risk,
       CAST(100.0 * SUM(revenue_at_risk) / NULLIF(SUM(revenue), 0) AS DECIMAL(5,2)) AS revenue_at_risk_pct,
       SUM(revenue_lost)                                              AS revenue_lost
FROM gold.kpi_product_line_monthly
GROUP BY product_line
ORDER BY revenue DESC;
GO

/* Q5. Revenue concentration
   a) share of revenue from the top 20% of products (NTILE quintiles)
   b) share of revenue from the top 10 customers                       */
WITH prod AS (
    SELECT product_code, SUM(sales) AS revenue
    FROM gold.fact_order_lines GROUP BY product_code
), ranked AS (
    SELECT revenue, NTILE(5) OVER (ORDER BY revenue DESC) AS quintile FROM prod
)
SELECT CAST(100.0 * SUM(CASE WHEN quintile = 1 THEN revenue END) / SUM(revenue)
            AS DECIMAL(5,2)) AS top20pct_products_revenue_share
FROM ranked;

WITH cust AS (
    SELECT customer_name, SUM(sales) AS revenue,
           ROW_NUMBER() OVER (ORDER BY SUM(sales) DESC) AS rn
    FROM gold.fact_order_lines GROUP BY customer_name
)
SELECT CAST(100.0 * SUM(CASE WHEN rn <= 10 THEN revenue END) / SUM(revenue)
            AS DECIMAL(5,2)) AS top10_customers_revenue_share,
       CAST(100.0 * SUM(CASE WHEN rn <= 2 THEN revenue END) / SUM(revenue)
            AS DECIMAL(5,2)) AS top2_customers_revenue_share
FROM cust;
GO

/* Q6. Monthly volatility — coefficient of variation of monthly revenue
   (all 29 months; the calendar spine keeps any empty month as 0) */
SELECT CAST(STDEV(total_revenue) AS DECIMAL(14,2))                          AS monthly_revenue_stdev,
       CAST(AVG(total_revenue)   AS DECIMAL(14,2))                          AS avg_monthly_revenue,
       CAST(STDEV(total_revenue) / NULLIF(AVG(total_revenue), 0) AS DECIMAL(6,3)) AS cv
FROM gold.kpi_monthly;
GO

/* Q7. Seasonality index — FULL years only (2018, 2019).
   Index = average revenue for that calendar month / average month.
   Only two observations per month, so treat as indicative. */
WITH full_years AS (
    SELECT * FROM gold.kpi_monthly WHERE YEAR(order_month) IN (2018, 2019)
)
SELECT MONTH(order_month)                                                   AS month_no,
       DATENAME(MONTH, MIN(order_month))                                    AS month_name,
       CAST(AVG(total_revenue) AS DECIMAL(14,2))                            AS avg_revenue,
       CAST(AVG(total_revenue) / (SELECT AVG(total_revenue) FROM full_years) AS DECIMAL(5,2)) AS seasonality_index
FROM full_years
GROUP BY MONTH(order_month)
ORDER BY month_no;
GO

/* Q8. Year-over-year on comparable periods (Jan–May each year) */
SELECT YEAR(order_month)  AS yr,
       SUM(total_revenue) AS jan_to_may_revenue,
       SUM(total_orders)  AS jan_to_may_orders
FROM gold.kpi_monthly
WHERE MONTH(order_month) BETWEEN 1 AND 5
GROUP BY YEAR(order_month)
ORDER BY yr;
GO

/* Q9. Product-line month-over-month growth on a calendar spine.
   Months with zero revenue break the % (division by zero) -> NULL. */
WITH g AS (
    SELECT product_line, order_month, revenue,
           LAG(revenue) OVER (PARTITION BY product_line ORDER BY order_month) AS prev_revenue
    FROM gold.kpi_product_line_monthly
)
SELECT product_line,
       CAST(100 * AVG(CASE WHEN prev_revenue > 0 THEN (revenue - prev_revenue) / prev_revenue END)
            AS DECIMAL(8,2))                                        AS avg_mom_growth_pct,
       SUM(CASE WHEN prev_revenue > 0 AND revenue < prev_revenue THEN 1 ELSE 0 END) AS declining_months,
       SUM(CASE WHEN revenue = 0 THEN 1 ELSE 0 END)                 AS zero_revenue_months
FROM g
GROUP BY product_line
ORDER BY avg_mom_growth_pct DESC;
GO

/* Q10. Price realisation vs list price (MSRP) by product line.
   > 0 means products sell ABOVE MSRP on average — i.e. MSRP in this
   dataset is not a ceiling, so "discount" analysis is limited. */
SELECT p.product_line,
       CAST(100 * AVG(f.price_vs_msrp_pct) AS DECIMAL(6,2))                       AS avg_price_vs_msrp_pct,
       CAST(100.0 * SUM(CASE WHEN f.price_vs_msrp_pct > 0 THEN 1 ELSE 0 END) / COUNT(*) AS DECIMAL(5,2)) AS pct_lines_above_msrp,
       CAST(100 * (SUM(f.sales) / NULLIF(SUM(f.list_value), 0) - 1) AS DECIMAL(6,2)) AS revenue_vs_list_pct
FROM gold.fact_order_lines AS f
JOIN gold.dim_product      AS p ON p.product_code = f.product_code
GROUP BY p.product_line
ORDER BY avg_price_vs_msrp_pct DESC;
GO

/* Q11. Deal-size mix (deal size is assigned per LINE in the source) */
SELECT deal_size,
       COUNT(*)   AS lines,
       SUM(sales) AS revenue,
       CAST(100.0 * SUM(sales) / SUM(SUM(sales)) OVER () AS DECIMAL(5,2)) AS revenue_share_pct
FROM gold.fact_order_lines
GROUP BY deal_size
ORDER BY revenue DESC;
GO
