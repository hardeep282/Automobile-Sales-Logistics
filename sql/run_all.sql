/* =====================================================================
   run_all.sql  —  run the whole SQL pipeline with ONE Execute in SSMS
   ---------------------------------------------------------------------
   1. In SSMS: Query menu -> SQLCMD Mode  (must be ticked)
   2. Check the SqlDir path below points at this repo's sql folder
   3. Press Execute (F5)

   Runs 00 -> 01 -> 02 -> 03 -> 05 in order and stops at the first error.
   (Prefer PowerShell? scripts\run_sql_pipeline.ps1 does the same thing
    and also handles the CSV-folder permission problem automatically.)
   ===================================================================== */

:on error exit
:setvar SqlDir "C:\Projects\Automobile-Sales-Logistics\sql"

:r $(SqlDir)\00_setup_database.sql
:r $(SqlDir)\01_bronze_load.sql
:r $(SqlDir)\02_silver_transform.sql
:r $(SqlDir)\03_gold_model.sql
:r $(SqlDir)\05_data_quality_tests.sql
