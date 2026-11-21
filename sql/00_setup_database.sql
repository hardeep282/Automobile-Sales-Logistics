/* =====================================================================
   00_setup_database.sql
   Automobile Sales & Logistics Analytics  |  Author: Hardeep Bamrah
   ---------------------------------------------------------------------
   Creates the database and the three medallion schemas.
   Safe to re-run (idempotent).

   Run order:  00 -> 01 -> 02 -> 03 -> 04 (analysis) -> 05 (tests)
   Target:     SQL Server 2017+ (tested syntax for SQL Server Express)
   ===================================================================== */

IF DB_ID(N'autosales_DB') IS NULL
    CREATE DATABASE autosales_DB;
GO

USE autosales_DB;
GO

-- bronze = raw landing, everything stored as text exactly as received
IF SCHEMA_ID(N'bronze') IS NULL EXEC (N'CREATE SCHEMA bronze');
GO
-- silver = typed, trimmed, standardised, one row per order line
IF SCHEMA_ID(N'silver') IS NULL EXEC (N'CREATE SCHEMA silver');
GO
-- gold   = business-ready star schema + KPI views consumed by Power BI
IF SCHEMA_ID(N'gold') IS NULL EXEC (N'CREATE SCHEMA gold');
GO
