param(
 [ValidateSet('FinalDataInventory','FinalGapProbe')]
 [string]$ScriptName='FinalDataInventory',
 [string]$ReportName='native-data-inventory.json',
 [string]$ArchiveParent='D:\TraderLabFinalEvaluation',
 [string]$SourceTerminal='D:\TraderLabTesterArchives\POLBODY2110-86b0dd17\holdout-BODY80_AGE120\terminal',
 [string]$TerminalExe='C:\Program Files\MetaTrader 5\terminal64.exe',
 [int]$TimeoutSeconds=360
)
$ErrorActionPreference='Stop'
$repo=Split-Path -Parent $PSScriptRoot
$run=Join-Path $ArchiveParent ('PF20261023-INVENTORY-'+[guid]::NewGuid().ToString('N').Substring(0,8))
$scripts=Join-Path $run 'MQL5\Scripts\TraderLab'
[IO.Directory]::CreateDirectory($scripts)|Out-Null
[IO.Directory]::CreateDirectory((Join-Path $run 'config'))|Out-Null
Copy-Item -LiteralPath $TerminalExe -Destination (Join-Path $run 'terminal64.exe')
Copy-Item -LiteralPath (Join-Path $repo ('mt5\'+$ScriptName+'.ex5')) -Destination $scripts
foreach($name in @('accounts.dat','servers.dat','common.ini')) {
 Copy-Item -LiteralPath (Join-Path $SourceTerminal ('config\'+$name)) -Destination (Join-Path $run 'config')
}
Copy-Item -LiteralPath (Join-Path $SourceTerminal 'bases') -Destination (Join-Path $run 'bases') -Recurse
$ini=Join-Path $run 'inventory.ini'
$configuration=@'
[Common]
Login=91496222
Server=LiteFinance-MT5-Demo
[Experts]
Enabled=1
AllowLiveTrading=0
AllowDllImport=0
[StartUp]
Script=TraderLab\FinalDataInventory.ex5
Symbol=XAUUSD_o
Period=M1
'@
$configuration.Replace('FinalDataInventory.ex5',$ScriptName+'.ex5') | Set-Content -LiteralPath $ini -Encoding Unicode
$work=Join-Path $repo 'work\final-profitability-20261023'
$pointer=if($ScriptName -eq 'FinalGapProbe') {'gap-root.txt'}else{'inventory-root.txt'}
[IO.File]::WriteAllText((Join-Path $work $pointer),$run)
Write-Output "INVENTORY $run"
$exe=[IO.Path]::GetFullPath((Join-Path $run 'terminal64.exe'))
$initial=Start-Process -FilePath $exe -ArgumentList @('/portable',('/config:"'+$ini+'"')) -WindowStyle Hidden -PassThru
$result=Join-Path $run 'MQL5\Files\FinalDataInventory-result.json'
$deadline=[DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
while([DateTime]::UtcNow -lt $deadline -and -not (Test-Path -LiteralPath $result)) { Start-Sleep -Seconds 2 }
# Stop only this isolated read-only terminal, including a replacement launcher PID.
foreach($native in @(Get-Process terminal64 -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $exe})) {
 if($native.Path -ne $exe) {throw 'Unexpected inventory process path'}
 $native.Kill();$native.WaitForExit()
}
if(-not (Test-Path -LiteralPath $result)) {throw "Inventory did not finish; retained logs at $run"}
$out=Join-Path $repo 'docs\reports\final-profitability-20261023'
Copy-Item -LiteralPath $result -Destination (Join-Path $out $ReportName)
Get-Content -LiteralPath $result -Raw
