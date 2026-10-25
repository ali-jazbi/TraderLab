param([int]$TimeoutSeconds=7200)
$ErrorActionPreference='Stop'
$repo=(Get-Location).Path
$work=Join-Path $repo 'work\market-closed-20261025'
$evidence=Join-Path $repo 'docs\reports\long-history-20261023'
$frozen=Get-Content (Join-Path $evidence 'frozen-candidate.json') -Raw | ConvertFrom-Json
$calendarManifest=Get-Content (Join-Path $evidence 'six-month-calendar.manifest.json') -Raw | ConvertFrom-Json
$binary=Join-Path $repo 'mt5\AUTO_CORE_DEMO.ex5'
if(!(Test-Path $binary)){throw 'Compile candidate first'}
foreach($p in $frozen.source_sha256.PSObject.Properties){if($p.Name -in @('mt5/Include/TraderLab/DemoGateway.mqh','mt5/Include/TraderLab/CoreLifecycle.mqh','mt5/AutoCoreIntegrationChecks.mq5','mt5/Checks/OfflineBroker.mqh')){continue};if((Get-FileHash (Join-Path $repo $p.Name) -Algorithm SHA256).Hash.ToLower() -ne $p.Value){throw "Frozen source changed: $($p.Name)"}}
$calendar=Join-Path $evidence 'six-month-calendar.csv'
if((Get-FileHash $calendar -Algorithm SHA256).Hash.ToLower() -ne $calendarManifest.sha256){throw 'Calendar changed'}
$sourceRoot=(Get-Content (Join-Path $repo 'work\long-history-20261023\native-root.txt') -Raw).Trim()
$source=Join-Path $sourceRoot 'terminal'
$sourceExe=Join-Path $source 'terminal64.exe'
if(@(Get-Process terminal64 -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $sourceExe}).Count){throw 'Close completed data audit before copying its cache'}
$run='POLMCFIX2510-'+[guid]::NewGuid().ToString('N').Substring(0,8)
$root=Join-Path 'C:\Users\11\TraderLabLongHistory' $run
$terminal=Join-Path $root 'terminal'
if(Test-Path $root){throw 'A fresh study directory is required'}
[IO.Directory]::CreateDirectory($root)|Out-Null
& compact.exe /C /I /Q $root | Out-Null
foreach($dir in @('config','MQL5\Experts\TraderLab','MQL5\Files','MQL5\Profiles\Tester')){[IO.Directory]::CreateDirectory((Join-Path $terminal $dir))|Out-Null}
foreach($exe in @('terminal64.exe','metatester64.exe')){Copy-Item -LiteralPath (Join-Path 'C:\Program Files\MetaTrader 5' $exe) -Destination $terminal}
foreach($name in @('accounts.dat','servers.dat','common.ini')){Copy-Item -LiteralPath (Join-Path $source ('config\'+$name)) -Destination (Join-Path $terminal 'config')}
Copy-Item -LiteralPath (Join-Path $source 'bases') -Destination (Join-Path $terminal 'bases') -Recurse
Copy-Item -LiteralPath $binary -Destination (Join-Path $terminal ('MQL5\Experts\TraderLab\'+$run+'.ex5'))
Copy-Item -LiteralPath $binary -Destination (Join-Path $root 'tested.ex5')
Copy-Item -LiteralPath $calendar -Destination (Join-Path $terminal 'MQL5\Files\TraderLab-auto-tester-calendar.csv')
$presetSource=Join-Path $repo 'work\final-profitability-20261023\frozen\original.set'
if((Get-FileHash $presetSource -Algorithm SHA256).Hash.ToLower() -ne $frozen.original_preset_sha256){throw 'Frozen original preset changed'}
$preset=(Get-Content $presetSource -Raw).Replace($frozen.parameters.InpLogFile,$run)
$preset=$preset -replace '(?m)^InpTesterCoreExecutionFromServer=.*$','InpTesterCoreExecutionFromServer=2026.04.24 00:00:00'
$set=Join-Path $root ($run+'.set');[IO.File]::WriteAllText($set,$preset,[Text.Encoding]::Unicode)
Copy-Item -LiteralPath $set -Destination (Join-Path $terminal ('MQL5\Profiles\Tester\'+$run+'.set'))
$ini=Join-Path $root ($run+'.ini')
$configuration=@'
[Common]
Login=91496222
Server=LiteFinance-MT5-Demo
[Experts]
AllowLiveTrading=0
AllowDllImport=0
[Tester]
Expert=TraderLab\RUN_NAME.ex5
ExpertParameters=RUN_NAME.set
Symbol=XAUUSD_o
Period=M1
Model=4
ExecutionMode=0
FromDate=2026.04.07
ToDate=2026.05.16
Optimization=0
Report=RUN_NAME.html
ReplaceReport=0
ShutdownTerminal=1
Deposit=1000
Currency=USD
Leverage=1:200
UseLocal=1
UseRemote=0
UseCloud=0
Visual=0
'@
[IO.File]::WriteAllText($ini,$configuration.Replace('RUN_NAME',$run),[Text.Encoding]::Unicode)
$hashes=[ordered]@{}
foreach($p in @($set,$ini,(Join-Path $root 'tested.ex5'),(Join-Path $terminal 'MQL5\Files\TraderLab-auto-tester-calendar.csv'))){$hashes[[IO.Path]::GetFileName($p)]=(Get-FileHash $p -Algorithm SHA256).Hash.ToLower()}
[ordered]@{run=$run;archive=$root;frozen_binary=$frozen.tested_binary_sha256;hashes=$hashes;measurement_from='2026-04-24';measurement_until_exclusive='2026-05-16';warmup_from='2026-04-07';timeframes=@('M1','M5','M15','H1','H4');strategy_changed=$false;execution_error_handling_changed=$true;live_trading=$false;started_utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json -Depth 6|Set-Content (Join-Path $repo 'docs\reports\market-closed-20261025\native-run-protocol.json') -Encoding utf8
[IO.File]::WriteAllText((Join-Path $work 'native-root.txt'),$root)
Write-Output "LIMITED_NATIVE_MARKET_CLOSED_REGRESSION $root"
$exe=Join-Path $terminal 'terminal64.exe'
Start-Process -FilePath $exe -ArgumentList @('/portable',('/config:"'+$ini+'"')) -WindowStyle Hidden|Out-Null
$deadline=[DateTime]::UtcNow.AddSeconds($TimeoutSeconds);$exitedSince=$null;$status='TERMINAL_EXIT_REQUIRES_AUDIT'
while([DateTime]::UtcNow -lt $deadline){
 $p=Get-Process terminal64 -ErrorAction SilentlyContinue|Where-Object {$_.Path -eq $exe}|Select-Object -First 1
 if($p){$exitedSince=$null}else{if($null -eq $exitedSince){$exitedSince=[DateTime]::UtcNow};if(([DateTime]::UtcNow-$exitedSince).TotalSeconds -ge 20){break}}
 if((Get-PSDrive -Name C).Free -lt 2GB){$status='RESOURCE_STOP_INSUFFICIENT_DISK';break}
 Start-Sleep -Seconds 3
}
if([DateTime]::UtcNow -ge $deadline){$status='TIMEOUT_REQUIRES_INCOMPLETE_RESULT'}
foreach($p in @(Get-Process terminal64 -ErrorAction SilentlyContinue|Where-Object {$_.Path -eq $exe})){$p.Kill();$p.WaitForExit()}
$raw=Get-ChildItem -LiteralPath $terminal -Filter ($run+'*.jsonl') -File -Recurse|Select-Object -First 1
if($raw){$snapshot=Join-Path $root 'native-files';[IO.Directory]::CreateDirectory($snapshot)|Out-Null;foreach($file in Get-ChildItem -LiteralPath $raw.DirectoryName -File){New-Item -ItemType HardLink -Path (Join-Path $snapshot $file.Name) -Target $file.FullName|Out-Null}}
foreach($file in @(Get-ChildItem -LiteralPath $terminal -Filter ($run+'*') -File -Recurse|Where-Object {$_.Extension -in '.html','.png'})){Copy-Item -LiteralPath $file.FullName -Destination $root}
[ordered]@{run=$run;status=$status;archive=$root;raw=if($raw){$raw.FullName}else{$null};all_journals_preserved=$true;finished_utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content (Join-Path $root 'run-status.json') -Encoding utf8
Write-Output "COMPLETE $root $status"
