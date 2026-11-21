<#
.SYNOPSIS
    Runs the SQL medallion pipeline against SQL Server in one go:
    00 setup -> 01 bronze -> 02 silver -> 03 gold -> 05 data-quality tests.

.DESCRIPTION
    - Splits each script on its GO lines and runs the batches in order,
      exactly as SSMS would.
    - Points 01_bronze_load.sql at this repo's CSV automatically.
    - If SQL Server cannot read the CSV folder (the common
      "Operating system error 5 / Access is denied"), it loads the CSV
      from PowerShell instead (SqlBulkCopy) into the same bronze table.
    - Prints the headline KPIs and the PASS/FAIL table from 05, and writes
      everything to logs\sql_pipeline_last_run.txt.

    Uses only Windows PowerShell 5.1 + .NET (System.Data.SqlClient):
    no sqlcmd or extra modules needed.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\run_sql_pipeline.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\run_sql_pipeline.ps1 -Server "localhost\SQLEXPRESS" -IncludeAnalysis
#>
param(
    [string]$Server = ".\SQLEXPRESS",
    [string]$Database = "autosales_DB",
    [switch]$IncludeAnalysis   # also run 04_kpi_analysis.sql (read-only)
)

$ErrorActionPreference = "Stop"
$Repo   = Split-Path -Parent $PSScriptRoot
$SqlDir = Join-Path $Repo "sql"
$Csv    = Join-Path $Repo "data\raw\auto_sales_data.csv"
$LogDir = Join-Path $Repo "logs"
$Log    = Join-Path $LogDir "sql_pipeline_last_run.txt"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Content -Path $Log -Value "" -Encoding UTF8

function Write-Log([string]$Message) {
    Write-Output $Message
    Add-Content -Path $Log -Value $Message -Encoding UTF8
}

function Get-Batches([string]$Path) {
    $text = [System.IO.File]::ReadAllText($Path)
    return [regex]::Split($text, '(?im)^\s*GO\s*$') | Where-Object { $_.Trim() -ne "" }
}

function Invoke-Batch($Connection, [string]$Sql) {
    $cmd = $Connection.CreateCommand()
    $cmd.CommandText = $Sql
    $cmd.CommandTimeout = 600
    $adapter = New-Object System.Data.SqlClient.SqlDataAdapter($cmd)
    $dataSet = New-Object System.Data.DataSet
    [void]$adapter.Fill($dataSet)
    return ,$dataSet
}

function Write-Tables($DataSet) {
    foreach ($table in $DataSet.Tables) {
        $text = ($table | Format-Table -AutoSize | Out-String -Width 220).TrimEnd()
        if ($text) { Write-Log $text }
    }
}

function Import-CsvToBronze($Connection) {
    Write-Log "   -> SQL Server could not read the CSV folder; loading it from PowerShell instead (SqlBulkCopy)."
    $Connection.ChangeDatabase($Database)
    [void](Invoke-Batch $Connection "TRUNCATE TABLE bronze.auto_sales_raw;")
    $rows = Import-Csv -Path $Csv -Encoding UTF8
    $columns = $rows[0].PSObject.Properties.Name
    $table = New-Object System.Data.DataTable
    foreach ($c in $columns) { [void]$table.Columns.Add($c, [string]) }
    foreach ($r in $rows) {
        $dr = $table.NewRow()
        foreach ($c in $columns) { $dr[$c] = $r.$c }
        $table.Rows.Add($dr)
    }
    $bulk = New-Object System.Data.SqlClient.SqlBulkCopy($Connection)
    $bulk.DestinationTableName = "bronze.auto_sales_raw"
    foreach ($c in $columns) { [void]$bulk.ColumnMappings.Add($c, $c) }
    $bulk.WriteToServer($table)
    $safePath = $Csv.Replace("'", "''")
    [void](Invoke-Batch $Connection "UPDATE bronze.auto_sales_raw SET _source_file = N'$safePath (PowerShell SqlBulkCopy)' WHERE _source_file IS NULL;")
    Write-Log ("   -> loaded {0} rows" -f $table.Rows.Count)
}

$scripts = @("00_setup_database.sql", "01_bronze_load.sql", "02_silver_transform.sql", "03_gold_model.sql")
if ($IncludeAnalysis) { $scripts += "04_kpi_analysis.sql" }
$scripts += "05_data_quality_tests.sql"

Write-Log ("SQL pipeline run  {0}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
Write-Log ("Server: {0}   Database: {1}" -f $Server, $Database)
Write-Log ("CSV:    {0}" -f $Csv)
Write-Log ""

$exitCode = 0
$testTable = $null
try {
    $conn = New-Object System.Data.SqlClient.SqlConnection("Server=$Server;Database=master;Integrated Security=True;TrustServerCertificate=True;Connect Timeout=20")
    $conn.Open()

    foreach ($name in $scripts) {
        $path = Join-Path $SqlDir $name
        Write-Log ("=== {0} ===" -f $name)
        $batchNo = 0
        foreach ($batch in Get-Batches $path) {
            $batchNo++
            $sql = $batch
            if ($name -eq "01_bronze_load.sql") {
                $sql = $sql.Replace("C:\Projects\Automobile-Sales-Logistics\data\raw\auto_sales_data.csv", $Csv)
            }
            try {
                $result = Invoke-Batch $conn $sql
            }
            catch {
                $msg = $_.Exception.InnerException.Message
                if (-not $msg) { $msg = $_.Exception.Message }
                if ($name -eq "01_bronze_load.sql" -and $sql -match "BULK INSERT") {
                    Write-Log ("   BULK INSERT failed: {0}" -f $msg)
                    Import-CsvToBronze $conn
                    continue
                }
                throw ("{0}, batch {1}: {2}" -f $name, $batchNo, $msg)
            }
            if ($name -ne "02_silver_transform.sql") { Write-Tables $result }   # skip the 10-row preview
            if ($name -eq "05_data_quality_tests.sql" -and $result.Tables.Count -gt 0) { $testTable = $result.Tables[0] }
        }
        Write-Log ""
    }

    if (-not $testTable) { throw "05_data_quality_tests.sql returned no result table." }
    $failed = @($testTable.Rows | Where-Object { $_.result -ne "PASS" })
    if ($failed.Count -eq 0) {
        Write-Log ("RESULT: all {0} data-quality tests PASSED. Power BI can now be refreshed." -f $testTable.Rows.Count)
    }
    else {
        Write-Log ("RESULT: {0} data-quality test(s) FAILED - see the table above." -f $failed.Count)
        $exitCode = 2
    }
    $conn.Close()
}
catch {
    Write-Log ("ERROR: {0}" -f $_)
    Write-Log "Check that SQL Server is running and the -Server name is right (default .\SQLEXPRESS)."
    $exitCode = 1
}

Write-Log ("Log saved to {0}" -f $Log)
exit $exitCode
