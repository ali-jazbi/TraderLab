param(
    [Parameter(Mandatory=$true)][string]$TerminalData,
    [Parameter(Mandatory=$true)][int]$MaxAgeSeconds,
    [Parameter(Mandatory=$true)][int]$RefreshSeconds
)
$ErrorActionPreference = 'Stop'
if ($RefreshSeconds -lt 1 -or $RefreshSeconds -ge $MaxAgeSeconds -or $MaxAgeSeconds -gt 3600) {
    throw 'Require 1 <= refresh < maximum source age <=3600 seconds'
}
$rootPath = Split-Path -Parent $PSScriptRoot
$filesPath = Join-Path ([IO.Path]::GetFullPath($TerminalData)) 'MQL5\Files'
if (-not (Test-Path -LiteralPath $filesPath -PathType Container)) { throw 'Explicit MT5 data folder with MQL5\Files required' }
$pythonPath = (Get-Command python -ErrorAction Stop).Source
$logPath = Join-Path $rootPath ('work\calendar-service\' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($logPath) | Out-Null
$arguments = @('-B', ('"'+(Join-Path $PSScriptRoot 'refresh_core_calendar.py')+'"'),
    '--profile', ('"'+(Join-Path $rootPath 'configs\core-calendar.sources-20261016.json')+'"'),
    '--out', ('"'+(Join-Path $filesPath 'AUTO_CORE_DEMO-forward.csv')+'"'),
    '--max-age-seconds', $MaxAgeSeconds, '--refresh-seconds', $RefreshSeconds)
$serviceProcess = Start-Process -FilePath $pythonPath -ArgumentList $arguments -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $logPath 'stdout.jsonl') -RedirectStandardError (Join-Path $logPath 'stderr.log')
@{ pid=$serviceProcess.Id; output=(Join-Path $filesPath 'AUTO_CORE_DEMO-forward.csv'); logs=$logPath;
   broker_orders_enabled=$false; automatic_demo_ready=$false } | ConvertTo-Json
