param(
 [string]$ArchiveParent="$env:LOCALAPPDATA\TraderLabTesterArchives",
 [string]$HistoryBase='',
 [int]$TimeoutSeconds=1800,
 [int]$Parallel=2,
 [string]$ResumeRoot='',
 [switch]$NewModesOnly,
 [int]$FirstPort=3200,
 [string]$TerminalData=(Join-Path $env:APPDATA 'MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075'),
 [string]$TerminalInstall='C:\Program Files\MetaTrader 5',
 [string]$CalendarFile=''
)
$ErrorActionPreference='Stop'
$repo=Split-Path -Parent $PSScriptRoot
$data=$TerminalData
if(-not $HistoryBase) {$HistoryBase=Join-Path $data 'bases'}
if(-not $CalendarFile) {$CalendarFile=Join-Path $repo 'docs\reports\auto-core-discovery-20261018\holdout-calendar.csv'}
foreach($required in @($HistoryBase,$CalendarFile,(Join-Path $TerminalInstall 'terminal64.exe'),(Join-Path $TerminalInstall 'metatester64.exe'))) {
 if(-not (Test-Path -LiteralPath $required)) {throw "Missing study prerequisite: $required"}
}
foreach($file in @('accounts.dat','servers.dat','common.ini')) {
 if(-not (Test-Path -LiteralPath (Join-Path $data ('config\'+$file)))) {throw "Missing terminal config: $file"}
}
foreach($binary in $(if($NewModesOnly) {@('mt5\AUTO_CORE_DEMO.ex5')} else {@('mt5\AUTO_CORE_DEMO.ex5','work\body80-baseline\mt5\AUTO_CORE_DEMO.ex5')})) {
 if(-not (Test-Path -LiteralPath (Join-Path $repo $binary))) {throw "Compile the study binary first: $binary"}
}
$batch=if($ResumeRoot) {Split-Path -Leaf $ResumeRoot} else {'POLBODY2110-'+[guid]::NewGuid().ToString('N').Substring(0,8)}
$root=Join-Path $ArchiveParent $batch
if($ResumeRoot -and [IO.Path]::GetFullPath($ResumeRoot) -ne [IO.Path]::GetFullPath($root)) {throw 'Resume must use the original archive parent'}
if($Parallel -lt 1 -or $Parallel -gt 3) {throw 'Use 1 to 3 isolated local agents'}
[IO.Directory]::CreateDirectory($root)|Out-Null
[IO.Directory]::CreateDirectory((Join-Path $repo 'work\auto-core'))|Out-Null
& compact.exe /C /I /Q $root | Out-Null
[IO.File]::WriteAllText((Join-Path $repo 'work\auto-core\current-body80-batch.txt'),$root)
Write-Output "ARCHIVE $root"
$number=0;$jobs=@()
foreach($window in @('training','holdout')) {
 $modes=if($NewModesOnly) {@('BODY80','BODY80_AGE120')} else {@('BASELINE','BODY80','BODY80_AGE120')}
 foreach($mode in $modes) {
  $number++;$run=$batch+'-'+$window+'-'+$mode
  $out=Join-Path $root ($window+'-'+$mode);$portable=Join-Path $out 'terminal'
  $iniPath=Join-Path $out ($run+'.ini')
  if(-not (Test-Path -LiteralPath $iniPath)) {
  [IO.Directory]::CreateDirectory($portable)|Out-Null
  foreach($exe in @('terminal64.exe','metatester64.exe')) {Copy-Item -LiteralPath (Join-Path $TerminalInstall $exe) -Destination $portable}
  [IO.Directory]::CreateDirectory((Join-Path $portable 'config'))|Out-Null
  foreach($file in @('accounts.dat','servers.dat','common.ini')) {Copy-Item -LiteralPath (Join-Path $data ('config\'+$file)) -Destination (Join-Path $portable 'config')}
  Copy-Item -LiteralPath $HistoryBase -Destination (Join-Path $portable 'bases') -Recurse
  foreach($dir in @('MQL5\Experts\TraderLab','MQL5\Files','MQL5\Profiles\Tester')) {[IO.Directory]::CreateDirectory((Join-Path $portable $dir))|Out-Null}
  $binary=if($mode -eq 'BASELINE') {'work\body80-baseline\mt5\AUTO_CORE_DEMO.ex5'} else {'mt5\AUTO_CORE_DEMO.ex5'}
  Copy-Item -LiteralPath (Join-Path $repo $binary) -Destination (Join-Path $portable ('MQL5\Experts\TraderLab\'+$run+'.ex5'))
  Copy-Item -LiteralPath (Join-Path $repo $binary) -Destination (Join-Path $out 'tested.ex5')
  Copy-Item -LiteralPath $CalendarFile -Destination (Join-Path $portable 'MQL5\Files\TraderLab-auto-tester-calendar.csv')
  $old=if($window -eq 'training') {'POLDISC1810-5e62a5fc-M7'} else {'POLDISC1810-13be7b1c-M7'}
  $report=Join-Path $repo ('docs\reports\auto-core-discovery-20261018\final-'+$window+'\'+$old)
  $age=if($mode -eq 'BODY80_AGE120') {120} else {0}
  $preset=(Get-Content -LiteralPath (Join-Path $report ($old+'.set')) -Raw).Replace($old,$run)+"`r`nInpExperimentalM1MaxAgeMinutes=$age`r`n"
  [IO.File]::WriteAllText((Join-Path $out ($run+'.set')),$preset,[Text.Encoding]::Unicode)
  Copy-Item -LiteralPath (Join-Path $out ($run+'.set')) -Destination (Join-Path $portable ('MQL5\Profiles\Tester\'+$run+'.set'))
  $ini=(Get-Content -LiteralPath (Join-Path $report ($old+'.ini')) -Raw).Replace($old,$run)
  $ini=$ini -replace '(?m)^Port=\d+\s*$',('Port='+($FirstPort+$number))
  [IO.File]::WriteAllText((Join-Path $out ($run+'.ini')),$ini,[Text.Encoding]::Unicode)
  }
  $existing=Get-Process terminal64 -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq (Join-Path $portable 'terminal64.exe')} | Select-Object -First 1
  $jobs+=@{window=$window;mode=$mode;run=$run;out=$out;portable=$portable;ini=$iniPath;process=$existing;done=((Test-Path -LiteralPath (Join-Path $out 'run-status.json')) -and $null -eq $existing);exited_since=$null;deadline=if($existing){$existing.StartTime.ToUniversalTime().AddSeconds($TimeoutSeconds)}else{$null}}
 }
}
while(@($jobs | Where-Object {-not $_.done}).Count -gt 0) {
 foreach($job in $jobs) {
  if($job.done) {continue}
  $window=$job.window;$mode=$job.mode;$run=$job.run;$out=$job.out;$portable=$job.portable
  # Terminal LiveUpdate can replace the launching PID. Follow only the exact
  # isolated executable path; never mistake a launcher exit for test completion.
  $replacement=Get-Process terminal64 -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq (Join-Path $portable 'terminal64.exe')} | Select-Object -First 1
  if($replacement) {$job.process=$replacement;$job.exited_since=$null}
  if($null -eq $job.process) {
   if(@($jobs | Where-Object {$null -ne $_.process -and -not $_.done}).Count -ge $Parallel) {continue}
   $job.process=Start-Process (Join-Path $portable 'terminal64.exe') -ArgumentList @('/portable',('/config:"'+$job.ini+'"')) -WindowStyle Hidden -PassThru
   $job.deadline=[DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
   Write-Output "START $window $mode pid=$($job.process.Id)"
  }
  $process=$job.process;$failed=$false
  if($process.HasExited -and -not (Test-Path -LiteralPath (Join-Path $out ($run+'.html')))) {
   if($null -eq $job.exited_since) {$job.exited_since=[DateTime]::UtcNow}
   if(([DateTime]::UtcNow-$job.exited_since).TotalSeconds -lt 20) {continue}
  }
  if(-not $process.HasExited) {
   # A prior synchronization error may be followed by a successful automatic
   # reconnect. Do not terminate a running test because of an old log line.
   if([DateTime]::UtcNow -lt $job.deadline) {continue}
  }
  if(-not $process.HasExited) {
   if($process.Path -ne [IO.Path]::GetFullPath((Join-Path $portable 'terminal64.exe'))) {throw 'Unexpected process path'}
   $process.Kill();$process.WaitForExit()
  }
  $raw=Get-ChildItem -LiteralPath $portable -Filter ($run+'*.jsonl') -File -Recurse | Select-Object -First 1
  $logs=Get-ChildItem -LiteralPath (Join-Path $portable 'logs') -Filter '*.log' -ErrorAction SilentlyContinue
  $failed=[bool]($logs | Select-String -SimpleMatch 'terminal is not synchronized with the trade server before start automatic testing' -Quiet)
  $status=if($raw) {'CAPTURE_AVAILABLE_REQUIRES_AUDIT'} elseif($failed) {'SERVER_NOT_SYNCHRONIZED'} else {'NO_NATIVE_CAPTURE'}
  if($raw) {
   $snapshot=Join-Path $out 'native-files';[IO.Directory]::CreateDirectory($snapshot)|Out-Null
   foreach($file in (Get-ChildItem -LiteralPath $raw.DirectoryName -File)) {New-Item -ItemType HardLink -Path (Join-Path $snapshot $file.Name) -Target $file.FullName | Out-Null}
  }
  foreach($file in (Get-ChildItem -LiteralPath $portable -Filter ($run+'*') -File -Recurse | Where-Object {$_.Extension -in '.html','.png'})) {Copy-Item -LiteralPath $file.FullName -Destination $out}
  [ordered]@{window=$window;mode=$mode;status=$status;archive=$out;raw=if($raw){$raw.FullName}else{$null}} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'run-status.json') -Encoding utf8
  Write-Output "DONE $window $mode $status"
  $job.done=$true
 }
 Start-Sleep -Seconds 2
}
Write-Output "COMPLETE $root"
