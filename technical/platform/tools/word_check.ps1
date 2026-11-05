<#
.SYNOPSIS
  Opens Word documents in real Word (via COM) and reports problems.

.DESCRIPTION
  Used to prove the generated guides open cleanly: no repair prompt, a real page count, and the text
  they should contain. Needs Microsoft Word on Windows. Prints one JSON object per document.

.EXAMPLE
  powershell -File tools/word_check.ps1 ../../non-technical/ready-to-use/*.docx
#>
param([Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)][string[]]$Paths)

$files = foreach ($p in $Paths) { Get-ChildItem -Path $p -File | ForEach-Object { $_.FullName } }
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$exit = 0
try {
    foreach ($f in $files) {
        $result = [ordered]@{ file = (Split-Path $f -Leaf); opened = $false; pages = 0; words = 0; tables = 0; links = 0; error = $null }
        try {
            $doc = $word.Documents.Open($f, $false, $true)
            $result.opened = $true
            $result.pages = $doc.ComputeStatistics(2)
            $result.words = $doc.ComputeStatistics(0)
            $result.tables = $doc.Tables.Count
            $result.links = $doc.Hyperlinks.Count
            $doc.Close(0)
        } catch {
            $result.error = $_.Exception.Message
        }
        if (-not $result.opened -or $result.pages -lt 1) { $exit = 1 }
        $result | ConvertTo-Json -Compress
    }
} finally {
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
exit $exit
