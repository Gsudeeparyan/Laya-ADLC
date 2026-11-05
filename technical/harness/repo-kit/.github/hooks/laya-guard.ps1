# Laya guard: stops an agent's most damaging commands and writes before they run.
# Reads the tool call as JSON on stdin. Prints a deny decision, or nothing to allow it.
# A crash denies the call (Copilot treats a non-zero exit as a denial); a timeout does not.
$ErrorActionPreference = 'Stop'

$payload = [Console]::In.ReadToEnd() -replace '\\[nrt]', ' '
$shellTool = [regex]::IsMatch($payload, '"(toolName|tool_name)" *: *"(bash|sh|powershell|pwsh|shell|execute|run_in_terminal|runInTerminal|terminal)"', 'IgnoreCase')

foreach ($line in [IO.File]::ReadAllLines((Join-Path $PSScriptRoot 'laya-guard-patterns.txt'))) {
    if (-not $line -or $line.StartsWith('#')) { continue }
    $scope, $flags, $regex, $reason = $line -split "`t", 4
    if ($scope -eq 'shell' -and -not $shellTool) { continue }
    $options = 'Multiline'
    if ($flags -eq 'i') { $options = 'Multiline, IgnoreCase' }
    if ([regex]::IsMatch($payload, $regex, $options)) {
        @{ permissionDecision = 'deny'; permissionDecisionReason = $reason } | ConvertTo-Json -Compress
        exit 0
    }
}
exit 0
