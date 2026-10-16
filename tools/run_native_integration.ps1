param(
    [ValidateSet('AutoCoreIntegrationChecks','AutoCoreProcessRestartChecks')]
    [string]$ScriptName = 'AutoCoreIntegrationChecks',
    [string]$TerminalExe = 'C:\Program Files\MetaTrader 5\terminal64.exe',
    [string]$SymbolCache = 'C:\Users\11\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\bases\Default\Symbols',
    [int]$TimeoutSeconds = 45
)
$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
$runPath = Join-Path $repoPath ('work\offline-native\' + [guid]::NewGuid().ToString('N'))
$scriptPath = Join-Path $runPath 'MQL5\Scripts\TraderLab'
[IO.Directory]::CreateDirectory($scriptPath) | Out-Null
Copy-Item -LiteralPath $TerminalExe -Destination (Join-Path $runPath 'terminal64.exe')
Copy-Item -LiteralPath (Join-Path $repoPath ('mt5\' + $ScriptName + '.ex5')) -Destination $scriptPath
$cachePath = Join-Path $runPath 'bases\Default\Symbols'
[IO.Directory]::CreateDirectory($cachePath) | Out-Null
Get-ChildItem -LiteralPath $SymbolCache -File | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $cachePath }
$configuration = @'
[Common]
Login=0
Server=127.0.0.1:1
KeepPrivate=0
NewsEnable=0
[Experts]
Enabled=1
AllowLiveTrading=0
AllowDllImport=0
[StartUp]
Script=TraderLab\AutoCoreIntegrationChecks.ex5
Symbol=EURUSD
Period=M1
'@
$configurationPath = Join-Path $runPath 'offline.ini'
$configuration = $configuration.Replace('AutoCoreIntegrationChecks.ex5', $ScriptName + '.ex5')
[IO.File]::WriteAllText($configurationPath,$configuration,[Text.Encoding]::Unicode)
$phases = 1
if ($ScriptName -eq 'AutoCoreProcessRestartChecks') { $phases = 4 }
for ($phase = 1; $phase -le $phases; $phase++) {
$nativeProcess = Start-Process -FilePath (Join-Path $runPath 'terminal64.exe') -ArgumentList @('/portable','/config:' + $configurationPath) -WindowStyle Hidden -PassThru
$resultPath = Join-Path $runPath 'MQL5\Files\AutoCoreIntegrationChecks-result.json'
if ($phases -eq 4) { $resultPath = Join-Path $runPath ('MQL5\Files\AutoCoreProcessRestartChecks-phase' + $phase + '.json') }
$deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
while ([DateTime]::UtcNow -lt $deadline -and -not (Test-Path -LiteralPath $resultPath) -and -not $nativeProcess.HasExited) {
    Start-Sleep -Milliseconds 250
}
if (-not $nativeProcess.HasExited) {
    # This is only the process launched from the verified isolated workspace path.
    $expectedExe = [IO.Path]::GetFullPath((Join-Path $runPath 'terminal64.exe'))
    if ($nativeProcess.Path -ne $expectedExe) { throw 'Refusing to stop a different terminal process' }
    if (-not $nativeProcess.WaitForExit(2000)) { $nativeProcess.Kill(); $nativeProcess.WaitForExit() }
}
Write-Output ('Native run directory: ' + $runPath)
if (-not (Test-Path -LiteralPath $resultPath)) { throw 'Native runtime result unavailable; inspect retained isolated logs' }
$result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
Get-Content -LiteralPath $resultPath
if ($result.failures -ne 0) { exit 1 }
}
