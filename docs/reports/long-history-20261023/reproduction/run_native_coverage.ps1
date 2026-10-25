param([int]$TimeoutSeconds=3600)
$ErrorActionPreference='Stop'
$repo=(Get-Location).Path
$work=Join-Path $repo 'work\long-history-20261023'
$source='C:\Users\11\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075'
$root=Join-Path 'C:\Users\11\TraderLabLongHistory' ('DATA-AUDIT-20261024-'+[guid]::NewGuid().ToString('N').Substring(0,8))
$terminal=Join-Path $root 'terminal'
foreach($path in @('config','MQL5\Experts\TraderLab')) {[IO.Directory]::CreateDirectory((Join-Path $terminal $path))|Out-Null}
foreach($exe in @('terminal64.exe','metatester64.exe')) {Copy-Item -LiteralPath (Join-Path 'C:\Program Files\MetaTrader 5' $exe) -Destination $terminal}
foreach($name in @('accounts.dat','servers.dat','common.ini')) {Copy-Item -LiteralPath (Join-Path $source ('config\'+$name)) -Destination (Join-Path $terminal 'config')}
Copy-Item -LiteralPath (Join-Path $source 'bases') -Destination (Join-Path $terminal 'bases') -Recurse
Copy-Item -LiteralPath (Join-Path $work 'NativeCoverageAudit.ex5') -Destination (Join-Path $terminal 'MQL5\Experts\TraderLab')
$ini=Join-Path $root 'native-coverage.ini'
@'
[Common]
Login=91496222
Server=LiteFinance-MT5-Demo
[Experts]
AllowLiveTrading=0
AllowDllImport=0
[Tester]
Expert=TraderLab\NativeCoverageAudit.ex5
Symbol=XAUUSD_o
Period=M1
Model=4
ExecutionMode=0
FromDate=2025.10.01
ToDate=2026.10.24
Optimization=0
Report=NativeCoverageAudit.html
ReplaceReport=0
ShutdownTerminal=1
Deposit=1000
Currency=USD
Leverage=1:200
UseLocal=1
UseRemote=0
UseCloud=0
Visual=0
'@ | Set-Content -LiteralPath $ini -Encoding Unicode
[IO.File]::WriteAllText((Join-Path $work 'native-root.txt'),$root)
Write-Output "NATIVE_DATA_AUDIT $root"
$exe=Join-Path $terminal 'terminal64.exe'
Start-Process -FilePath $exe -ArgumentList @('/portable',('/config:"'+$ini+'"')) -WindowStyle Hidden | Out-Null
$deadline=[DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
$done=$false
while([DateTime]::UtcNow -lt $deadline) {
 $logs=@(Get-ChildItem -LiteralPath (Join-Path $terminal 'Tester') -Filter '*.log' -Recurse -ErrorAction SilentlyContinue | Where-Object {$_.FullName -match 'Agent-.*\\logs\\'})
 foreach($log in $logs) { if(Select-String -LiteralPath $log.FullName -SimpleMatch 'DATA_AUDIT_COMPLETE' -Quiet) {$done=$true} }
 if($done) {break}
 Start-Sleep -Seconds 3
}
if(-not $done) {throw "Data audit did not finish; retained all logs at $root"}
Write-Output 'DATA_AUDIT_COMPLETE; never treat zero orders or HTML profit as strategy results'
