<#
.SYNOPSIS
  Opens workbooks in real Excel (via COM), recalculates them and reports problems.

.DESCRIPTION
  Used to prove that files written by the ADLC engine open cleanly in Excel: no repair
  prompt, formulas calculate, and no cell shows an error such as #REF! or #NAME?.
  Needs Microsoft Excel installed on Windows. Prints one JSON object per workbook.

.EXAMPLE
  powershell -File tools/excel_check.ps1 ../../non-technical/ready-to-use/templates/*.xlsx
#>
param([Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)][string[]]$Paths)

$files = foreach ($p in $Paths) { Get-ChildItem -Path $p -File | ForEach-Object { $_.FullName } }
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$exit = 0
try {
    foreach ($f in $files) {
        $result = [ordered]@{ file = (Split-Path $f -Leaf); opened = $false; repaired = $false; errors = @(); tables = @(); charts = 0 }
        try {
            $wb = $xl.Workbooks.Open($f, 0, $true)
            $result.opened = $true
            $result.repaired = ($wb.Name -match 'Repaired') -or ($xl.Caption -match 'Repaired')
            $xl.CalculateFull()
            foreach ($ws in $wb.Worksheets) {
                foreach ($lo in $ws.ListObjects) {
                    $rows = if ($lo.DataBodyRange) { $lo.DataBodyRange.Rows.Count } else { 0 }
                    $result.tables += "$($ws.Name)!$($lo.Name) ($rows rows)"
                }
                $result.charts += $ws.ChartObjects().Count
                $used = $ws.UsedRange
                foreach ($cell in $used.Cells) {
                    if ($cell.HasFormula -and ($cell.Text -match '^#(REF!|NAME\?|VALUE!|DIV/0!|N/A|NUM!|NULL!|SPILL!|CALC!)')) {
                        $result.errors += "$($ws.Name)!$($cell.Address($false, $false)) = $($cell.Text)"
                    }
                }
            }
            $wb.Close($false)
        } catch {
            $result.errors += "Could not open: $($_.Exception.Message)"
        }
        if (-not $result.opened -or $result.repaired -or $result.errors.Count -gt 0) { $exit = 1 }
        $result | ConvertTo-Json -Compress -Depth 4
    }
} finally {
    $xl.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl)
}
exit $exit
