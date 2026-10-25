param(
 [Parameter(Mandatory=$true)][string]$TerminalRoot,
 [switch]$RequestActivation
)
$ErrorActionPreference='Stop'
$repo=Split-Path -Parent $PSScriptRoot
$root=[IO.Path]::GetFullPath($TerminalRoot)
$expected=Join-Path $env:USERPROFILE 'TraderLabDemoForward\BODY80-AGE120-20261025'
if($root -ne $expected){throw 'Unexpected isolated Demo deployment path'}
$exe=Join-Path $root 'terminal64.exe'
if(Get-Process terminal64 -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $exe}){
 throw 'Deployment terminal is already running; preserve its journals and current EA state'
}
$files=Join-Path $root 'MQL5\Files'
$evidence=Get-Content (Join-Path $repo 'docs\reports\demo-forward-20261025.json') -Raw|ConvertFrom-Json
if($evidence.python.failures-ne 0 -or $evidence.native_integration.failures-ne 0 -or
   $evidence.compilation.forward.errors-ne 0 -or
   (Get-FileHash (Join-Path $repo 'mt5\AUTO_CORE_DEMO_FORWARD.ex5') -Algorithm SHA256).Hash.ToLower()-ne $evidence.artifacts.forward_binary_sha256 -or
   (Get-FileHash (Join-Path $repo 'mt5\activation\Body80Age120.demo-forward.set') -Algorithm SHA256).Hash.ToLower()-ne $evidence.artifacts.forward_profile_sha256){
 throw 'Tested binary/profile evidence mismatch; no activation'
}
$preflightPath=Join-Path $files 'TraderLab-forward-preflight.json'
$probeStart=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$p=Start-Process $exe -ArgumentList @('/portable',('/config:"'+(Join-Path $root 'preflight.ini')+'"')) -WindowStyle Hidden -PassThru
$deadline=[DateTime]::UtcNow.AddSeconds(45)
$probe=$null
do {
 if(Test-Path -LiteralPath $preflightPath){
  try {$candidate=Get-Content -LiteralPath $preflightPath -Raw|ConvertFrom-Json
   if($candidate.utc-ge $probeStart){$probe=$candidate}
  } catch { $probe=$null }
 }
 $running=@(Get-Process terminal64 -ErrorAction SilentlyContinue | Where-Object {$_.Path-eq $exe})
 if($null-ne $probe -and $running.Count-eq 0){break}
 Start-Sleep -Milliseconds 250
} while([DateTime]::UtcNow-lt $deadline)
if($null-eq $probe -or $running.Count-ne 0){throw 'Read-only native account verification did not complete; no activation'}
if(!$probe.demo_verified -or $probe.login-ne 91496222 -or $probe.server-ne 'LiteFinance-MT5-Demo' -or
   $probe.utc-lt $probeStart -or !$probe.clock_verified -or !$probe.hedging -or $probe.currency-ne 'USD' -or !$probe.five_frames_history){
 throw 'Fresh account/clock/history verification failed; no activation'
}
# The application never transforms an Investor credential into trading authority.
$activate=$RequestActivation -and $probe.trade_allowed -and $probe.expert_allowed
if($RequestActivation -and !$activate){Write-Warning 'ACCOUNT_TRADE_ALLOWED=false: Investor/read-only authentication; Algo stays OFF'}
$presetSource=Join-Path $repo 'mt5\activation\Body80Age120.demo-forward.set'
Copy-Item -LiteralPath $presetSource -Destination (Join-Path $root 'MQL5\Presets\Body80Age120.demo-forward.set')
Copy-Item -LiteralPath (Join-Path $repo 'mt5\AUTO_CORE_DEMO_FORWARD.ex5') -Destination (Join-Path $root 'MQL5\Experts\TraderLab\AUTO_CORE_DEMO_FORWARD.ex5')
$python=(Get-Command python.exe -ErrorAction Stop).Source
$existing=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
 $_.CommandLine -and $_.CommandLine.Contains('traderlab.forward_calendar') -and $_.CommandLine.Contains($files)
})
# Windows venv launchers can have a real interpreter child with the same command.
# Count independent process trees, not the wrapper/interpreter pair twice.
$publisherIds=@($existing | ForEach-Object {$_.ProcessId})
$trees=@($existing | Where-Object {$publisherIds -notcontains $_.ParentProcessId})
if($trees.Count-gt 1){throw 'More than one independent calendar publisher; refuse activation'}
if($trees.Count-eq 1){$publisher=Get-Process -Id $trees[0].ProcessId}
else {$publisher=Start-Process $python -ArgumentList @('-m','traderlab.forward_calendar','--files',('"'+$files+'"')) -WorkingDirectory $repo -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $root 'calendar-publisher.log') -RedirectStandardError (Join-Path $root 'calendar-publisher-errors.log')}
$allowed=if($activate){'1'}else{'0'}
$ini=@"
[Common]
Login=91496222
Server=LiteFinance-MT5-Demo
KeepPrivate=1
NewsEnable=0
[Experts]
Enabled=$allowed
AllowLiveTrading=$allowed
AllowDllImport=0
Account=1
Profile=1
[StartUp]
Expert=TraderLab\AUTO_CORE_DEMO_FORWARD.ex5
ExpertParameters=Body80Age120.demo-forward.set
Symbol=XAUUSD_o
Period=M1
"@
$iniPath=Join-Path $root 'forward.ini';[IO.File]::WriteAllText($iniPath,$ini,[Text.Encoding]::Unicode)
$terminal=Start-Process $exe -ArgumentList @('/portable',('/config:"'+$iniPath+'"')) -WindowStyle Hidden -PassThru
[ordered]@{demo_identity_verified=$true;activation_requested=[bool]$RequestActivation;algo_enabled=[bool]$activate;investor_blocked=(!$probe.trade_allowed);
 terminal_pid=$terminal.Id;publisher_pid=$publisher.Id;terminal_root=$root;started_utc=[DateTime]::UtcNow.ToString('o')}|
 ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'deployment.json') -Encoding utf8
Write-Output "Demo engine installed/running; Algo=$allowed; terminal PID=$($terminal.Id); calendar PID=$($publisher.Id)"
