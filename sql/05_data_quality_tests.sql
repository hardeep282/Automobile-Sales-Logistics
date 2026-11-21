/* =====================================================================
   05_data_quality_tests.sql  —  Automated data tests
   ---------------------------------------------------------------------
   Each test counts the rows that BREAK a rule. A healthy pipeline
   returns failures = 0 for every test. Run after 01–03.

   Industry equivalent: dbt tests (unique, not_null, relationships,
   accepted_values, dbt_utils.equal_rowcount), Great Expectations,
   Soda.
   ===================================================================== */

USE autosales_DB;
GO

WITH tests AS (

    /* ---------- completeness / row counts ---------- */
    SELECT N'bronze row count = 2747' AS test_name,
           CASE WHEN (SELECT COUNT(*) FROM bronze.auto_sales_raw) = 2747 THEN 0 ELSE 1 END AS failures
    UNION ALL
    SELECT N'silver keeps every bronze row',
           ABS((SELECT COUNT(*) FROM bronze.auto_sales_raw) - (SELECT COUNT(*) FROM silver.order_lines))

    /* ---------- typing: nothing silently became NULL ---------- */
    UNION ALL
    SELECT N'no unparseable order dates',  COUNT(*) FROM silver.order_lines WHERE order_date IS NULL
    UNION ALL
    SELECT N'no unparseable numbers',      COUNT(*) FROM silver.order_lines
           WHERE order_number IS NULL OR quantity IS NULL OR price_each IS NULL OR sales IS NULL OR msrp IS NULL
    UNION ALL
    SELECT N'every status is mapped (accepted values)', COUNT(*) FROM silver.order_lines WHERE status_group IS NULL

    /* ---------- validity ---------- */
    UNION ALL
    SELECT N'quantity, price, sales, msrp > 0', COUNT(*) FROM silver.order_lines
           WHERE quantity <= 0 OR price_each <= 0 OR sales <= 0 OR msrp <= 0
    UNION ALL
    SELECT N'sales = price_each x quantity (±0.10)', COUNT(*) FROM silver.order_lines WHERE sales_reconciles = 0

    /* ---------- uniqueness (primary keys) ---------- */
    UNION ALL
    SELECT N'order line key is unique', COUNT(*) FROM (
           SELECT order_number, order_line_number FROM silver.order_lines
           GROUP BY order_number, order_line_number HAVING COUNT(*) > 1) d
    UNION ALL
    SELECT N'dim_customer key unique', COUNT(*) - COUNT(DISTINCT customer_name) FROM gold.dim_customer
    UNION ALL
    SELECT N'dim_product key unique',  COUNT(*) - COUNT(DISTINCT product_code)  FROM gold.dim_product

    /* ---------- grain assumptions the gold layer relies on ---------- */
    UNION ALL
    SELECT N'one status per order', COUNT(*) FROM (
           SELECT order_number FROM silver.order_lines GROUP BY order_number HAVING COUNT(DISTINCT status) > 1) d
    UNION ALL
    SELECT N'one customer / country / date per order', COUNT(*) FROM (
           SELECT order_number FROM silver.order_lines GROUP BY order_number
           HAVING COUNT(DISTINCT customer_name) > 1 OR COUNT(DISTINCT country) > 1
               OR COUNT(DISTINCT order_date) > 1) d
    UNION ALL
    SELECT N'one city / country per customer', COUNT(*) FROM (
           SELECT customer_name FROM silver.order_lines GROUP BY customer_name
           HAVING COUNT(DISTINCT city) > 1 OR COUNT(DISTINCT country) > 1) d
    UNION ALL
    SELECT N'one product line / MSRP per product', COUNT(*) FROM (
           SELECT product_code FROM silver.order_lines GROUP BY product_code
           HAVING COUNT(DISTINCT product_line) > 1 OR COUNT(DISTINCT msrp) > 1) d

    /* ---------- referential integrity (fact -> dims) ---------- */
    UNION ALL
    SELECT N'fact -> dim_customer', COUNT(*) FROM gold.fact_order_lines f
           WHERE NOT EXISTS (SELECT 1 FROM gold.dim_customer d WHERE d.customer_name = f.customer_name)
    UNION ALL
    SELECT N'fact -> dim_product', COUNT(*) FROM gold.fact_order_lines f
           WHERE NOT EXISTS (SELECT 1 FROM gold.dim_product d WHERE d.product_code = f.product_code)
    UNION ALL
    SELECT N'fact -> dim_country', COUNT(*) FROM gold.fact_order_lines f
           WHERE NOT EXISTS (SELECT 1 FROM gold.dim_country d WHERE d.country = f.country)
    UNION ALL
    SELECT N'fact -> dim_status', COUNT(*) FROM gold.fact_order_lines f
           WHERE NOT EXISTS (SELECT 1 FROM gold.dim_status d WHERE d.status = f.status)

    /* ---------- reconciliation: revenue is identical at every layer ---------- */
    UNION ALL
    SELECT N'revenue: silver = order_summary',
           CASE WHEN ABS((SELECT SUM(sales) FROM silver.order_lines)
                       - (SELECT SUM(order_revenue) FROM gold.order_summary)) < 0.01 THEN 0 ELSE 1 END
    UNION ALL
    SELECT N'revenue: silver = product-line view (no double counting)',
           CASE WHEN ABS((SELECT SUM(sales) FROM silver.order_lines)
                       - (SELECT SUM(revenue) FROM gold.kpi_product_line_monthly)) < 0.01 THEN 0 ELSE 1 END
    UNION ALL
    SELECT N'revenue: silver = monthly view',
           CASE WHEN ABS((SELECT SUM(sales) FROM silver.order_lines)
                       - (SELECT SUM(total_revenue) FROM gold.kpi_monthly)) < 0.01 THEN 0 ELSE 1 END
    UNION ALL
    SELECT N'revenue: silver = country view',
           CASE WHEN ABS((SELECT SUM(sales) FROM silver.order_lines)
                       - (SELECT SUM(total_revenue) FROM gold.kpi_country)) < 0.01 THEN 0 ELSE 1 END
    UNION ALL
    SELECT N'orders: headline = distinct orders in silver',
           ABS((SELECT total_orders FROM gold.kpi_headline)
             - (SELECT COUNT(DISTINCT order_number) FROM silver.order_lines))
)
SELECT test_name,
       failures,
       CASE WHEN failures = 0 THEN N'PASS' ELSE N'FAIL' END AS result
FROM tests
ORDER BY CASE WHEN failures = 0 THEN 1 ELSE 0 END, test_name;
GO
