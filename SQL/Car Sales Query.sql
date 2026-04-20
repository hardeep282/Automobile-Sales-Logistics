
---- ==================================================
-- Automobile Sales Analytics 
-- Hardeep Bamrah
-- ====================================================


------------------------------------------------------
-- 1. Raw Data Exploration
-- Purpose: Inspect the base automobile sales dataset
------------------------------------------------------




USE autosales_DB;
GO

--- EXEC sp_rename 'dbo.[Auto Sales data]', 'autosales_raw';


SELECT * FROM dbo.autosales_raw;
GO


SELECT TOP 10 * FROM dbo.autosales_raw;
GO



-- Bronze_autosales table created

IF OBJECT_ID('dbo.bronze_autosales','U') IS NOT NULL
    DROP TABLE dbo.bronze_autosales;

SELECT *
INTO dbo.bronze_autosales
FROM dbo.autosales_raw;   
GO



SELECT COUNT(*) AS bronze_rows FROM dbo.bronze_autosales;
GO


SELECT TOP 20 ORDERDATE
FROM dbo.bronze_autosales
WHERE ORDERDATE IS NOT NULL;
GO



SELECT 
    COUNT(*) AS rows_total,
    SUM(
        CASE 
            WHEN COALESCE(
                TRY_CONVERT(date, ORDERDATE, 103),
                TRY_CONVERT(date, ORDERDATE, 101),
                TRY_CONVERT(date, ORDERDATE)
            ) IS NULL 
            THEN 1 
            ELSE 0 
        END
    ) AS bad_orderdate_rows
FROM dbo.bronze_autosales;
GO


  

-- Checking if any odd or negative values 
SELECT 
    SUM(CASE WHEN SALES IS NULL OR SALES <= 0 THEN 1 ELSE 0 END) AS bad_sales_rows,
    SUM(CASE WHEN PRICEEACH IS NULL OR PRICEEACH <= 0 THEN 1 ELSE 0 END) AS bad_price_rows,
    SUM(CASE WHEN MSRP IS NULL OR MSRP <= 0 THEN 1 ELSE 0 END) AS bad_msrp_rows
FROM dbo.bronze_autosales;



------------------------------------------------------
-- 2. Silver Layer
-- Purpose: Clean and prepare the dataset for analysis
------------------------------------------------------

-- Silver Table Autosales



-- Drop view if exists 
IF OBJECT_ID('dbo.silver_auto_sales', 'V') IS NOT NULL
    DROP VIEW dbo.silver_auto_sales;
GO


-- Create Silver View
CREATE VIEW dbo.silver_auto_sales AS
SELECT
    ORDERNUMBER,
    ORDERLINENUMBER,
    QUANTITYORDERED,
    PRICEEACH,
    SALES,

    -- Convert ORDERDATE to DATE 
    TRY_CONVERT(date, ORDERDATE, 103) AS order_date,

    -- Order Month (YYYY-MM-01)
    DATEFROMPARTS(
        YEAR(TRY_CONVERT(date, ORDERDATE, 103)),
        MONTH(TRY_CONVERT(date, ORDERDATE, 103)),
        1
    ) AS order_month,

    DAYS_SINCE_LASTORDER,

    UPPER(LTRIM(RTRIM(STATUS))) AS status,
    LTRIM(RTRIM(PRODUCTLINE)) AS productline,
    MSRP,
    LTRIM(RTRIM(PRODUCTCODE)) AS productcode,
    LTRIM(RTRIM(CUSTOMERNAME)) AS customername,
    LTRIM(RTRIM(COUNTRY)) AS country,
    LTRIM(RTRIM(DEALSIZE)) AS deal_size,

    /* Calculating Discount % */
    CASE 
        WHEN MSRP IS NULL OR MSRP = 0 THEN NULL
        ELSE ROUND(1 - ( PRICEEACH / MSRP), 4)  --We have considered MSRP
    END AS discount_pct,                      -- as listed price

    /* Calculating Profit Proxy per line */
    CASE
        WHEN MSRP IS NULL THEN NULL
        ELSE ROUND(( MSRP - PRICEEACH) * QUANTITYORDERED, 2)
    END AS pricing_gap

FROM dbo.bronze_autosales;
GO




SELECT  *
FROM dbo.silver_auto_sales;



SELECT COUNT(DISTINCT ordernumber) AS unique_orders
FROM dbo.silver_auto_sales;



SELECT TOP 10 *
FROM dbo.silver_auto_sales
ORDER BY order_date;



SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN order_date IS NULL THEN 1 ELSE 0 END) AS bad_date_rows
FROM dbo.silver_auto_sales;



------------------------------------------------------
-- 3. Gold Layer
-- Purpose: Create analytical tables used for reporting
------------------------------------------------------

-- Gold Table Autosales



-- Drop view if exists 
IF OBJECT_ID('dbo.gold_orders', 'V') IS NOT NULL
    DROP VIEW dbo.gold_orders;
GO


-- Create view 
CREATE VIEW dbo.gold_orders AS
SELECT
    ordernumber,
    MIN(order_date)  AS order_date,     -- earliest line date for that order
    MIN(order_month) AS order_month,
    MAX(country)     AS country,
    MAX(deal_size)   AS deal_size,

    SUM(sales)        AS order_revenue,
    SUM(pricing_gap) AS order_pricing_gap,

    /* Flags */
    MAX(CASE WHEN status IN ('CANCELLED','DISPUTED') THEN 1 ELSE 0 END) AS failure_flag,
    MAX(CASE WHEN status IN ('CANCELLED','DISPUTED','ON HOLD') THEN 1 ELSE 0 END) AS high_risk_flag,

    /* High discount flag (if any line item has >=20% discount) */
    MAX(CASE WHEN discount_pct >= 0.20 THEN 1 ELSE 0 END) AS high_discount_flag
FROM dbo.silver_auto_sales
GROUP BY ordernumber;
GO

SELECT * 
FROM dbo.gold_orders;




SELECT
    ordernumber,
    MAX(CASE WHEN status IN ('CANCELLED','DISPUTED') THEN 1 ELSE 0 END) AS failure_flag
FROM dbo.silver_auto_sales
GROUP BY ordernumber
HAVING MAX(CASE WHEN status IN ('CANCELLED','DISPUTED') THEN 1 ELSE 0 END) = 1;
GO



SELECT * 
FROM dbo.gold_orders
WHERE high_risk_flag = 1;

SELECT * 
FROM dbo.gold_orders
WHERE high_discount_flag = 1;

SELECT * 
FROM dbo.gold_orders
WHERE failure_flag = 1;


-- Calculating shipping order percentage that had some issues or were cancelled
SELECT
  ROUND(
    SUM(CAST(failure_flag AS float)) / NULLIF(COUNT(*), 0) * 100,
    2
  ) AS failure_rate_pct
FROM dbo.gold_orders;




SELECT *
FROM dbo.gold_orders;



SELECT * FROM dbo.silver_auto_sales;


--- Total rows in different layers

SELECT 'raw'   AS layer, COUNT(*) AS rows FROM dbo.autosales_raw
UNION ALL
SELECT 'bronze'AS layer, COUNT(*) AS rows FROM dbo.bronze_autosales
UNION ALL
SELECT 'silver'AS layer, COUNT(*) AS rows FROM dbo.silver_auto_sales
UNION ALL
SELECT 'gold_orders' AS layer, COUNT(*) AS rows FROM dbo.gold_orders;
GO


-- Verifying gold output table with the silver table to understand distinct value

SELECT
  (SELECT COUNT(*) FROM dbo.gold_orders) AS gold_rows,
  (SELECT COUNT(DISTINCT ORDERNUMBER) FROM dbo.silver_auto_sales) AS distinct_orders_in_silver;
  GO

 SELECT @@VERSION;


-- Revenue month wise (check)
SELECT 
    order_month,
    SUM(sales) AS check_revenue
FROM dbo.silver_auto_sales
GROUP BY order_month
ORDER BY order_month;



--- Monthly revenue and Monthly profit proxy
IF OBJECT_ID('dbo.gold_monthly_revenue', 'V') IS NOT NULL
    DROP VIEW dbo.gold_monthly_revenue;
GO

CREATE VIEW dbo.gold_monthly_revenue AS
SELECT
    order_month,
    SUM(sales) AS revenue,
    COUNT(DISTINCT ordernumber) AS orders,
    SUM(pricing_gap) AS pricing_gap
FROM dbo.silver_auto_sales
GROUP BY order_month;
GO

SELECT * FROM dbo.gold_monthly_revenue;


EXEC sp_helptext 'dbo.gold_monthly_revenue';


SELECT 
    c.name AS column_name,
    t.name AS data_type,
    c.max_length,
    c.is_nullable
FROM sys.columns c
JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID('dbo.gold_monthly_revenue')
ORDER BY c.column_id;

--- Monthly revenue all
SELECT * 
FROM dbo.gold_monthly_revenue
ORDER BY order_month;


---Monthly revenue selective
SELECT order_month, revenue
FROM dbo.gold_monthly_revenue
ORDER BY order_month;

SELECT * FROM dbo.gold_orders;




--- Monthly Revenue based on Productline

IF OBJECT_ID('dbo.gold_product_monthly', 'V') IS NOT NULL
    DROP VIEW dbo.gold_product_monthly;
GO

CREATE VIEW dbo.gold_product_monthly AS
SELECT 
    productline,
    order_month,
    SUM(sales) AS revenue,
    SUM(pricing_gap) AS pricing_gap,
    COUNT(DISTINCT ordernumber) AS orders
FROM dbo.silver_auto_sales
GROUP BY productline, order_month;
GO

SELECT * 
FROM dbo.gold_product_monthly
ORDER BY productline, order_month;




------------------------------------------------------
-- 4. KPI Calculations
-- Purpose: Calculate business performance metrics
------------------------------------------------------

-- KPI List




--- KPI 1  Total Revenue, Total Orders, Revenue per Order
SELECT 
    SUM(order_revenue) AS total_revenue,
    COUNT(*) AS total_orders,
    ROUND(SUM(order_revenue) / NULLIF(COUNT(*), 0), 2) AS revenue_per_order
FROM dbo.gold_orders;




--- KPI 2: Gross Pricing Gap + Pricing Margin % Proxy
SELECT 
    ROUND(SUM(order_pricing_gap), 2) AS gross_pricing_gap,
    ROUND(
        SUM(order_pricing_gap) / NULLIF(SUM(order_revenue), 0) * 100,
        2
    ) AS pricing_margin_pct_proxy
FROM dbo.gold_orders;



--- KPI 3: High Discount Revenue %
SELECT 
    ROUND(
        SUM(CASE WHEN high_discount_flag = 1 THEN order_revenue ELSE 0 END) 
        / NULLIF(SUM(order_revenue), 0) * 100,
        2
    ) AS high_discount_revenue_pct
FROM dbo.gold_orders;


--- KPI 4: Order Failure Rate
SELECT
    ROUND(
        SUM(CAST(failure_flag AS float)) / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS order_failure_rate_pct
FROM dbo.gold_orders;


--- KPI 5: High-Risk Order %
SELECT
    ROUND(
        SUM(CAST(high_risk_flag AS float)) / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS high_risk_order_pct
FROM dbo.gold_orders;



--- KPI 6: Revenue Concentration Ratio (Top 20% products) – NTILE 
WITH prod AS (
    SELECT
        productcode,
        SUM(sales) AS revenue
    FROM dbo.silver_auto_sales
    GROUP BY productcode
),
ranked AS (
    SELECT
        productcode,
        revenue,
        NTILE(5) OVER (ORDER BY revenue DESC) AS quintile
    FROM prod
)
SELECT
    ROUND(
        SUM(CASE WHEN quintile = 1 THEN revenue ELSE 0 END) 
        / NULLIF(SUM(revenue), 0) * 100,
        2
    ) AS top20_products_revenue_share_pct
FROM ranked;

--- KPI 7: Volatility Index (Monthly Revenue Std Dev)

SELECT
    ROUND(STDEV(revenue), 2) AS monthly_revenue_stddev,
    ROUND(AVG(revenue), 2) AS avg_monthly_revenue,
    ROUND(STDEV(revenue) / NULLIF(AVG(revenue), 0), 4) AS revenue_volatility_cv
FROM dbo.gold_monthly_revenue;



-- Below small table clearly indicates the reason for volatility
-- as there can be seen difference in orders


SELECT TOP 5 * 
FROM dbo.gold_monthly_revenue
ORDER BY revenue DESC;

SELECT TOP 5 *
FROM dbo.gold_monthly_revenue
ORDER BY revenue ASC;


-- KPI 8.1 Seasonality Index 

WITH monthly_avg AS (
    SELECT
        MONTH(order_month) AS month_no,
        AVG(revenue) AS avg_month_revenue
    FROM dbo.gold_monthly_revenue
    GROUP BY MONTH(order_month)
),
overall_avg AS (
    SELECT AVG(revenue) AS overall_avg_revenue
    FROM dbo.gold_monthly_revenue
)
SELECT
    m.month_no,
    ROUND(m.avg_month_revenue,2) AS avg_month_revenue,
    ROUND(m.avg_month_revenue / o.overall_avg_revenue,2) AS seasonality_index
FROM monthly_avg m
CROSS JOIN overall_avg o
ORDER BY m.month_no;




--- KPI 9: Product Growth Rate (MoM) + Decline Index
WITH g AS (
    SELECT
        productline,
        order_month,
        revenue,
        LAG(revenue) OVER (PARTITION BY productline ORDER BY order_month) AS prev_revenue
    FROM dbo.gold_product_monthly
),
calc AS (
    SELECT
        productline,
        order_month,
        revenue,
        prev_revenue,
        CASE 
            WHEN prev_revenue IS NULL OR prev_revenue = 0 THEN NULL
            ELSE (revenue - prev_revenue) / prev_revenue
        END AS mom_growth
    FROM g
)
SELECT
    productline,
    ROUND(AVG(mom_growth) * 100, 2) AS avg_mom_growth_pct,
    SUM(CASE WHEN mom_growth < 0 THEN 1 ELSE 0 END) AS negative_growth_months
FROM calc
GROUP BY productline
ORDER BY avg_mom_growth_pct DESC;






------------------------------------------------------
-- 5. Logistics KPI Analysis
-- Purpose: Monitor fulfilment reliability and risk
------------------------------------------------------

-- Logistics KPIs



---- Logistics relevant KPI's


DROP VIEW IF EXISTS dbo.gold_order_ops_fact;
GO

CREATE VIEW dbo.gold_order_ops_fact AS
WITH order_rollup AS (
    SELECT
        ordernumber,

        MIN(CAST(order_date AS date)) AS order_date,
        MIN(order_month)              AS order_month,

        MAX(country)                  AS country,
        SUM(CAST(sales AS decimal(18,2))) AS order_revenue,

        /* Status flags (order-level) */
        MAX(CASE WHEN status = 'SHIPPED' THEN 1 ELSE 0 END) AS shipped_flag,
        MAX(CASE WHEN status IN ('ON HOLD','IN PROCESS') THEN 1 ELSE 0 END) AS stuck_flag,
        MAX(CASE WHEN status IN ('CANCELLED','DISPUTED') THEN 1 ELSE 0 END) AS failure_flag
    FROM dbo.silver_auto_sales
    GROUP BY ordernumber
),
final AS (
    SELECT
        ordernumber,
        order_date,
        order_month,
        country,
        order_revenue,

        shipped_flag,
        stuck_flag,
        failure_flag,

        --// high risk flag is created because there could be a possibility that one 
        -- order number could have different shipping statuses and in that case because 
        -- of max case there could be a possibility of getting both orders.
        -- So high risk flag is just a confirmation for stuck flag and failure flag
        -- If we check status also by month wise then high risk flag can be helpful.//


        CASE WHEN (stuck_flag = 1 OR failure_flag = 1) THEN 1 ELSE 0 END AS high_risk_flag
    FROM order_rollup
)
SELECT * FROM final;
GO

SELECT * FROM dbo.gold_order_ops_fact;



-- Operational KPI's country wise

DROP VIEW IF EXISTS dbo.gold_ops_country_kpis;
GO

CREATE VIEW dbo.gold_ops_country_kpis AS
SELECT
    country,
    COUNT(*) AS total_orders,
    SUM(order_revenue) AS total_revenue,

    SUM(shipped_flag)  AS shipped_orders,
    SUM(stuck_flag)    AS stuck_orders,
    SUM(failure_flag)  AS failed_orders,
    SUM(high_risk_flag) AS high_risk_orders,

    CAST(100.0 * SUM(shipped_flag)   / NULLIF(COUNT(*),0) AS decimal(10,2)) AS shipped_pct,
    CAST(100.0 * SUM(stuck_flag)     / NULLIF(COUNT(*),0) AS decimal(10,2)) AS stuck_pct,
    CAST(100.0 * SUM(failure_flag)   / NULLIF(COUNT(*),0) AS decimal(10,2)) AS failure_pct,
    CAST(100.0 * SUM(high_risk_flag) / NULLIF(COUNT(*),0) AS decimal(10,2)) AS high_risk_pct,

    CAST(100.0 * (1 - (SUM(high_risk_flag) * 1.0 / NULLIF(COUNT(*),0))) AS decimal(10,2))
      AS shipping_reliability_score_pct,

    CAST(100.0 * SUM(CASE WHEN high_risk_flag = 1 THEN order_revenue ELSE 0 END)
         / NULLIF(SUM(order_revenue),0) AS decimal(10,2)) AS revenue_at_risk_pct
FROM dbo.gold_order_ops_fact
GROUP BY country;
GO

SELECT * FROM dbo.gold_ops_country_kpis;





DROP VIEW IF EXISTS dbo.gold_ops_country_month_kpis;
GO

CREATE VIEW dbo.gold_ops_country_month_kpis AS
SELECT
    order_month,
    country,
    COUNT(*) AS total_orders,
    SUM(order_revenue) AS total_revenue,

    SUM(shipped_flag)  AS shipped_orders,
    SUM(stuck_flag)    AS stuck_orders,
    SUM(failure_flag)  AS failed_orders,
    SUM(high_risk_flag) AS high_risk_orders,

    CAST(100.0 * SUM(shipped_flag)   / NULLIF(COUNT(*),0) AS decimal(10,2)) AS shipped_pct,
    CAST(100.0 * SUM(stuck_flag)     / NULLIF(COUNT(*),0) AS decimal(10,2)) AS stuck_pct,
    CAST(100.0 * SUM(failure_flag)   / NULLIF(COUNT(*),0) AS decimal(10,2)) AS failure_pct,
    CAST(100.0 * SUM(high_risk_flag) / NULLIF(COUNT(*),0) AS decimal(10,2)) AS high_risk_pct,

    CAST(100.0 * (1 - (SUM(high_risk_flag) * 1.0 / NULLIF(COUNT(*),0))) AS decimal(10,2))
      AS shipping_reliability_score_pct,

    CAST(100.0 * SUM(CASE WHEN high_risk_flag = 1 THEN order_revenue ELSE 0 END)
         / NULLIF(SUM(order_revenue),0) AS decimal(10,2)) AS revenue_at_risk_pct,

    /* Composite Country Risk Index */
    CAST(
        (0.4 * (100.0 * SUM(failure_flag) / NULLIF(COUNT(*),0))) +
        (0.3 * (100.0 * SUM(stuck_flag)   / NULLIF(COUNT(*),0))) +
        (0.3 * (100.0 * SUM(high_risk_flag) / NULLIF(COUNT(*),0)))
        AS decimal(10,2)
    ) AS country_risk_index
FROM dbo.gold_order_ops_fact
GROUP BY order_month, country;
GO

SELECT * FROM dbo.gold_ops_country_month_kpis;



-- Shipping Status based on order_month and country

DROP VIEW IF EXISTS dbo.gold_status_distribution_month;
GO

CREATE VIEW dbo.gold_status_distribution_month AS
SELECT
    order_month,
    country,
    status,
    COUNT(DISTINCT ordernumber) AS orders_count
FROM dbo.silver_auto_sales
GROUP BY order_month, country, status;
GO

SELECT * FROM dbo.gold_status_distribution_month;



-- // Correct format and calculation of total revenue based on productlines
-- in each order number.//

DROP VIEW IF EXISTS dbo.gold_ops_productline_month;
GO

CREATE VIEW dbo.gold_ops_productline_month AS
WITH pl_orders AS (
    SELECT DISTINCT
        s.order_month,
        s.ordernumber,
        s.productline
    FROM dbo.silver_auto_sales s
    WHERE s.ordernumber IS NOT NULL
      AND s.productline IS NOT NULL
      AND s.order_month IS NOT NULL
),
joined AS (
    SELECT
        p.order_month,
        p.productline,
        f.ordernumber,
        f.order_revenue,
        f.high_risk_flag,
        f.failure_flag,
        f.stuck_flag,
        b.alloc_weight
    FROM pl_orders p
    JOIN dbo.gold_order_ops_fact f
      ON f.ordernumber = p.ordernumber
    JOIN dbo.bridge_order_productline b
      ON b.ordernumber = p.ordernumber
     AND b.productline = p.productline
)
SELECT
    order_month,
    productline,

    COUNT(DISTINCT ordernumber) AS total_orders,

    -- allocated revenue (prevents double counting). This helped preventing 
    -- adding up revenue double time.
   CAST(SUM(order_revenue * alloc_weight) AS decimal(18,2)) AS total_revenue,

    SUM(high_risk_flag) AS high_risk_orders,
    SUM(failure_flag)   AS failed_orders,
    SUM(stuck_flag)     AS stuck_orders,

    CAST(100.0 * SUM(high_risk_flag) / NULLIF(COUNT(*),0) AS decimal(10,2)) AS high_risk_pct,
    CAST(100.0 * SUM(failure_flag)   / NULLIF(COUNT(*),0) AS decimal(10,2)) AS failure_pct,
    CAST(100.0 * SUM(stuck_flag)     / NULLIF(COUNT(*),0) AS decimal(10,2)) AS stuck_pct,

    CAST(
      100.0 * SUM(CASE WHEN high_risk_flag=1 THEN (order_revenue * alloc_weight) ELSE 0 END)
      / NULLIF(SUM(order_revenue * alloc_weight),0)
      AS decimal(10,2)
    ) AS revenue_at_risk_pct
FROM joined
GROUP BY order_month, productline;
GO


SELECT * FROM dbo.gold_ops_productline_month;


-- // After carefully analysing it was also found that one order has multiple productlines,
-- so it was necessary to claculate productline in every ordernu,ber and then calculate,
-- accordingly, to avoid multiple addition of order revenue.
-- Below is the table which was duplicating total revenue //



DROP VIEW IF EXISTS dbo.gold_ops_productline_month;
GO

CREATE VIEW dbo.gold_ops_productline_month AS
WITH pl_orders AS (
    SELECT
        s.order_month,
        s.productline,
        s.ordernumber
    FROM dbo.silver_auto_sales s
    GROUP BY s.order_month, s.productline, s.ordernumber
),
joined AS (
    SELECT
        p.order_month,
        p.productline,
        f.ordernumber,
        f.order_revenue,
        f.high_risk_flag,
        f.failure_flag,
        f.stuck_flag
    FROM pl_orders p
    JOIN dbo.gold_order_ops_fact f
      ON f.ordernumber = p.ordernumber
)
SELECT
    order_month,
    productline,

    COUNT(*) AS total_orders,
    SUM(order_revenue) AS total_revenue,

    SUM(high_risk_flag) AS high_risk_orders,
    SUM(failure_flag)   AS failed_orders,
    SUM(stuck_flag)     AS stuck_orders,

    CAST(100.0 * SUM(high_risk_flag) / NULLIF(COUNT(*),0) AS decimal(10,2)) AS high_risk_pct,
    CAST(100.0 * SUM(failure_flag)   / NULLIF(COUNT(*),0) AS decimal(10,2)) AS failure_pct,
    CAST(100.0 * SUM(stuck_flag)     / NULLIF(COUNT(*),0) AS decimal(10,2)) AS stuck_pct,

    CAST(100.0 * SUM(CASE WHEN high_risk_flag=1 THEN order_revenue ELSE 0 END)
         / NULLIF(SUM(order_revenue),0) AS decimal(10,2)) AS revenue_at_risk_pct
FROM joined
GROUP BY order_month, productline;
GO





-- Understanding Productline and Order Distribution in Order Numbers

DROP VIEW IF EXISTS dbo.bridge_order_productline;
GO

CREATE VIEW dbo.bridge_order_productline AS
WITH distinct_pairs AS (
    SELECT DISTINCT
        ordernumber,
        productline
    FROM dbo.silver_auto_sales
    WHERE ordernumber IS NOT NULL
      AND productline IS NOT NULL
),
counts AS (
    SELECT
        ordernumber,
        COUNT(*) AS productline_cnt
    FROM distinct_pairs
    GROUP BY ordernumber
)
SELECT
    p.ordernumber,
    p.productline,
    c.productline_cnt,
    CAST(1.0 / NULLIF(c.productline_cnt, 0) AS decimal(18,6)) AS alloc_weight
FROM distinct_pairs p
JOIN counts c
  ON c.ordernumber = p.ordernumber;
GO


SELECT * FROM dbo.bridge_order_productline;



-- Query to check unique counts of productlines

DROP VIEW IF EXISTS dbo.dim_productline;
GO

CREATE VIEW dbo.dim_productline AS
SELECT 
   DISTINCT productline
FROM dbo.silver_auto_sales
WHERE productline IS NOT NULL;
GO

SELECT * FROM dbo.dim_productline;












