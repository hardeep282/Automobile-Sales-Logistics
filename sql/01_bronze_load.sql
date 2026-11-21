/* =====================================================================
   01_bronze_load.sql  —  BRONZE (raw landing)
   ---------------------------------------------------------------------
   Lands data/raw/auto_sales_data.csv into bronze.auto_sales_raw.
   Every source column is stored as NVARCHAR so the load can never fail
   on a bad value; typing happens in silver. Two audit columns record
   when and from where each row arrived.

   >>> EDIT @csv_path BELOW to the full path of the CSV on your machine.
       The SQL Server service account must be able to read that folder
       (for SQL Express a path such as C:\Projects\... normally works).

   Industry equivalent: Fivetran / Airbyte / ADF copy activity landing
   raw files into a "raw" or "landing" schema.
   ===================================================================== */

USE autosales_DB;
GO

DROP TABLE IF EXISTS bronze.auto_sales_raw;
GO

CREATE TABLE bronze.auto_sales_raw (
    ORDERNUMBER          NVARCHAR(50)  NULL,
    QUANTITYORDERED      NVARCHAR(50)  NULL,
    PRICEEACH            NVARCHAR(50)  NULL,
    ORDERLINENUMBER      NVARCHAR(50)  NULL,
    SALES                NVARCHAR(50)  NULL,
    ORDERDATE            NVARCHAR(50)  NULL,
    DAYS_SINCE_LASTORDER NVARCHAR(50)  NULL,
    STATUS               NVARCHAR(50)  NULL,
    PRODUCTLINE          NVARCHAR(100) NULL,
    MSRP                 NVARCHAR(50)  NULL,
    PRODUCTCODE          NVARCHAR(50)  NULL,
    CUSTOMERNAME         NVARCHAR(200) NULL,
    PHONE                NVARCHAR(100) NULL,
    ADDRESSLINE1         NVARCHAR(200) NULL,
    CITY                 NVARCHAR(100) NULL,
    POSTALCODE           NVARCHAR(50)  NULL,
    COUNTRY              NVARCHAR(100) NULL,
    CONTACTLASTNAME      NVARCHAR(100) NULL,
    CONTACTFIRSTNAME     NVARCHAR(100) NULL,
    DEALSIZE             NVARCHAR(50)  NULL,
    -- audit columns
    _source_file         NVARCHAR(400) NULL,
    _loaded_at           DATETIME2(0)  NOT NULL
        CONSTRAINT DF_auto_sales_raw_loaded_at DEFAULT (SYSUTCDATETIME())
);
GO

-- BULK INSERT needs the column list to match the file exactly, so we load
-- through a view that exposes only the 20 source columns.
CREATE OR ALTER VIEW bronze.v_auto_sales_raw_load AS
SELECT ORDERNUMBER, QUANTITYORDERED, PRICEEACH, ORDERLINENUMBER, SALES,
       ORDERDATE, DAYS_SINCE_LASTORDER, STATUS, PRODUCTLINE, MSRP,
       PRODUCTCODE, CUSTOMERNAME, PHONE, ADDRESSLINE1, CITY, POSTALCODE,
       COUNTRY, CONTACTLASTNAME, CONTACTFIRSTNAME, DEALSIZE
FROM bronze.auto_sales_raw;
GO

/* ---------------------------------------------------------------------
   OPTION A (recommended): load straight from the CSV
   --------------------------------------------------------------------- */
DECLARE @csv_path NVARCHAR(400) =
    N'C:\Projects\Automobile-Sales-Logistics\data\raw\auto_sales_data.csv';

DECLARE @sql NVARCHAR(MAX) = N'
BULK INSERT bronze.v_auto_sales_raw_load
FROM ''' + REPLACE(@csv_path, '''', '''''') + N'''
WITH (
    FORMAT          = ''CSV'',      -- handles quoted fields such as "AV Stores, Co."
    FIRSTROW        = 2,            -- skip header
    FIELDTERMINATOR = '','',
    ROWTERMINATOR   = ''0x0a'',     -- file uses LF line endings
    CODEPAGE        = ''65001'',    -- UTF-8
    TABLOCK
);';

EXEC sys.sp_executesql @sql;

UPDATE bronze.auto_sales_raw
SET    _source_file = @csv_path
WHERE  _source_file IS NULL;
GO

/* ---------------------------------------------------------------------
   OPTION B: you already imported the CSV with the SSMS Import Wizard
   into dbo.autosales_raw (the original v1 approach). Comment out
   OPTION A above and run this instead.
   ---------------------------------------------------------------------
INSERT INTO bronze.v_auto_sales_raw_load
SELECT CAST(ORDERNUMBER AS NVARCHAR(50)),  CAST(QUANTITYORDERED AS NVARCHAR(50)),
       CAST(PRICEEACH AS NVARCHAR(50)),    CAST(ORDERLINENUMBER AS NVARCHAR(50)),
       CAST(SALES AS NVARCHAR(50)),        CONVERT(NVARCHAR(50), ORDERDATE, 103),
       CAST(DAYS_SINCE_LASTORDER AS NVARCHAR(50)), STATUS, PRODUCTLINE,
       CAST(MSRP AS NVARCHAR(50)), PRODUCTCODE, CUSTOMERNAME, PHONE, ADDRESSLINE1,
       CITY, CAST(POSTALCODE AS NVARCHAR(50)), COUNTRY, CONTACTLASTNAME,
       CONTACTFIRSTNAME, DEALSIZE
FROM dbo.autosales_raw;
UPDATE bronze.auto_sales_raw SET _source_file = N'dbo.autosales_raw' WHERE _source_file IS NULL;
*/

-- Expect 2,747 rows
SELECT COUNT(*) AS bronze_rows, MIN(_loaded_at) AS loaded_at
FROM bronze.auto_sales_raw;
GO
