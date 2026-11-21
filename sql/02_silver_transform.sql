/* =====================================================================
   02_silver_transform.sql  —  SILVER (clean, typed, standardised)
   ---------------------------------------------------------------------
   Grain: one row per order line (ORDERNUMBER + ORDERLINENUMBER).

   What happens here
   - text -> proper types with TRY_CONVERT (bad values become NULL and
     are caught by the tests in 05_data_quality_tests.sql)
   - trimming / upper-casing of status, consistent column names
   - ORDERDATE is dd/mm/yyyy in the source, so style 103 is used
   - status is mapped ONCE, through silver.ref_order_status, so every
     downstream view uses the same business definition
   - personal data (phone, street address, postcode) is NOT carried
     forward: nothing downstream needs it

   Industry equivalent: dbt "staging" models (stg_*), with the status
   mapping held as a dbt seed.
   ===================================================================== */

USE autosales_DB;
GO

/* ---------------------------------------------------------------------
   Reference: order status -> business status group
   ---------------------------------------------------------------------
   v1 counted IN PROCESS as "stuck". Every IN PROCESS row is dated
   29–31 May 2020 — the last three days of the data — so these are
   simply orders still moving through the pipeline. v2 treats them as
   OPEN and excludes them from reliability rates.

   status_group   meaning                                     statuses
   Fulfilled      delivered (Resolved = delivered after an     SHIPPED, RESOLVED
                  issue was raised and closed)
   Open           still in the normal pipeline                 IN PROCESS
   At Risk        revenue not yet secured, could still be lost ON HOLD, DISPUTED
   Lost           revenue already lost                         CANCELLED
   --------------------------------------------------------------------- */
CREATE OR ALTER VIEW silver.ref_order_status AS
SELECT status, status_group, status_sort,
       is_fulfilled, is_open, is_at_risk, is_lost, is_failed, had_issue
FROM (VALUES
    --  status       group        sort fulfilled open at_risk lost failed issue
    (N'SHIPPED',    N'Fulfilled',  1,   1,        0,   0,      0,   0,     0),
    (N'RESOLVED',   N'Fulfilled',  2,   1,        0,   0,      0,   0,     1),
    (N'IN PROCESS', N'Open',       3,   0,        1,   0,      0,   0,     0),
    (N'ON HOLD',    N'At Risk',    4,   0,        0,   1,      0,   0,     1),
    (N'DISPUTED',   N'At Risk',    5,   0,        0,   1,      0,   1,     1),
    (N'CANCELLED',  N'Lost',       6,   0,        0,   0,      1,   1,     1)
) AS s (status, status_group, status_sort,
        is_fulfilled, is_open, is_at_risk, is_lost, is_failed, had_issue);
GO

/* ---------------------------------------------------------------------
   silver.order_lines
   --------------------------------------------------------------------- */
CREATE OR ALTER VIEW silver.order_lines AS
WITH typed AS (
    SELECT
        TRY_CONVERT(INT,           LTRIM(RTRIM(ORDERNUMBER)))        AS order_number,
        TRY_CONVERT(INT,           LTRIM(RTRIM(ORDERLINENUMBER)))    AS order_line_number,
        TRY_CONVERT(DATE,          LTRIM(RTRIM(ORDERDATE)), 103)     AS order_date,
        TRY_CONVERT(INT,           LTRIM(RTRIM(QUANTITYORDERED)))    AS quantity,
        TRY_CONVERT(DECIMAL(10,2), LTRIM(RTRIM(PRICEEACH)))          AS price_each,
        TRY_CONVERT(DECIMAL(12,2), LTRIM(RTRIM(SALES)))              AS sales,
        TRY_CONVERT(DECIMAL(10,2), LTRIM(RTRIM(MSRP)))               AS msrp,
        UPPER(LTRIM(RTRIM(STATUS)))                                  AS status,
        LTRIM(RTRIM(PRODUCTLINE))                                    AS product_line,
        LTRIM(RTRIM(PRODUCTCODE))                                    AS product_code,
        LTRIM(RTRIM(CUSTOMERNAME))                                   AS customer_name,
        CONCAT(LTRIM(RTRIM(CONTACTFIRSTNAME)), N' ',
               LTRIM(RTRIM(CONTACTLASTNAME)))                        AS contact_name,   -- NULL-safe
        LTRIM(RTRIM(CITY))                                           AS city,
        LTRIM(RTRIM(COUNTRY))                                        AS country,
        LTRIM(RTRIM(DEALSIZE))                                       AS deal_size
    FROM bronze.auto_sales_raw
)
SELECT
    t.order_number,
    t.order_line_number,
    t.order_date,
    DATEFROMPARTS(YEAR(t.order_date), MONTH(t.order_date), 1)  AS order_month,
    t.customer_name,
    t.contact_name,
    t.city,
    t.country,
    t.product_code,
    t.product_line,
    t.deal_size,
    t.status,
    s.status_group,
    s.is_fulfilled, s.is_open, s.is_at_risk, s.is_lost, s.is_failed, s.had_issue,
    t.quantity,
    t.price_each,
    t.msrp,
    t.sales,
    -- list value = what the line would be worth at MSRP (list price)
    CAST(t.msrp * t.quantity AS DECIMAL(12,2))                 AS list_value,
    -- price realisation vs list: +0.05 = sold 5% ABOVE MSRP, -0.10 = 10% discount.
    -- (v1 called the inverse of this a "profit proxy"; there is no cost data,
    --  so it is a pricing signal, not profit.)
    CAST(CASE WHEN t.msrp > 0 THEN t.price_each / t.msrp - 1 END AS DECIMAL(9,4))
                                                               AS price_vs_msrp_pct,
    -- source SALES is rounded to 1 dp, so allow a small tolerance
    CASE WHEN ABS(t.sales - t.price_each * t.quantity) <= 0.10 THEN 1 ELSE 0 END
                                                               AS sales_reconciles
FROM typed AS t
LEFT JOIN silver.ref_order_status AS s
       ON s.status = t.status;
GO

-- quick look
SELECT TOP (10) * FROM silver.order_lines ORDER BY order_date, order_number, order_line_number;
GO
