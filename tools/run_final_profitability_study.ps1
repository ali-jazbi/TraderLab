param([int]$TimeoutSeconds=7200,[int]$FirstPort=3500,[string]$ArchiveParent='D:\TraderLabFinalEvaluation')
$ErrorActionPreference='Stop'
$repo=Split-Path -Parent $PSScriptRoot
$evidence=Join-Path $repo 'docs\reports\final-profitability-20261023'
$work=Join-Path $repo 'work\final-profitability-20261023'
$frozen=Get-Content -LiteralPath (Join-Path $evidence 'frozen-version.json') -Raw | ConvertFrom-Json
$binary=Join-Path $work 'frozen\AUTO_CORE_DEMO.ex5'
if((Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLower() -ne $frozen.tested_binary_sha256) {throw 'Frozen binary hash mismatch'}
$presetSource=Join-Path $work 'frozen\original.set'
if((Get-FileHash -LiteralPath $presetSource -Algorithm SHA256).Hash.ToLower() -ne $frozen.original_preset_sha256) {throw 'Frozen preset hash mismatch'}
foreach($property in $frozen.source_sha256.PSObject.Properties) {
 if((Get-FileHash -LiteralPath (Join-Path $repo $property.Name) -Algorithm SHA256).Hash.ToLower() -ne $property.Value) {throw "Frozen source changed: $($property.Name)"}
}
$inventory=Get-Content -LiteralPath (Join-Path $work 'inventory-root.txt') -Raw
$batch='POLFINAL2310-'+[guid]::NewGuid().ToString('N').Substring(0,8)
$root=Join-Path $ArchiveParent $batch
if(Test-Path -LiteralPath $root) {throw 'Fresh archive required'}
[IO.Directory]::CreateDirectory($root)|Out-Null
& compact.exe /C /I /Q $root | Out-Null
[IO.File]::WriteAllText((Join-Path $work 'current-batch.txt'),$root)
Write-Output "ARCHIVE $root"
$old=$frozen.parameters.InpLogFile
$oldIni=Join-Path $repo ('docs\reports\body80-20261021\native\holdout-BODY80_AGE120\'+$old+'.ini')
$cases=@(@{name='W1_20261019_20';from='2026.10.19';until='2026.10.21'},@{name='W2_20261021_22';from='2026.10.21';until='2026.10.23'})
$jobs=@();$number=0
foreach($case in $cases) {
 $number++;$run=$batch+'-'+$case.name;$out=Join-Path $root $case.name;$terminal=Join-Path $out 'terminal'
 [IO.Directory]::CreateDirectory($terminal)|Out-Null
 foreach($exe in @('terminal64.exe','metatester64.exe')) {Copy-Item -LiteralPath (Join-Path 'C:\Program Files\MetaTrader 5' $exe) -Destination $terminal}
 [IO.Directory]::CreateDirectory((Join-Path $terminal 'config'))|Out-Null
 foreach($file in @('accounts.dat','servers.dat','common.ini')) {Copy-Item -LiteralPath (Join-Path $inventory ('config\'+$file)) -Destination (Join-Path $terminal 'config')}
 Copy-Item -LiteralPath (Join-Path $inventory 'bases') -Destination (Join-Path $terminal 'bases') -Recurse
 foreach($dir in @('MQL5\Experts\TraderLab','MQL5\Files','MQL5\Profiles\Tester')) {[IO.Directory]::CreateDirectory((Join-Path $terminal $dir))|Out-Null}
 Copy-Item -LiteralPath $binary -Destination (Join-Path $terminal ('MQL5\Experts\TraderLab\'+$run+'.ex5'))
 Copy-Item -LiteralPath $binary -Destination (Join-Path $out 'tested.ex5')
 Copy-Item -LiteralPath (Join-Path $evidence 'candidate-calendar.csv') -Destination (Join-Path $terminal 'MQL5\Files\TraderLab-auto-tester-calendar.csv')
 $preset=(Get-Content -LiteralPath $presetSource -Raw).Replace($old,$run)
 $preset=$preset -replace '(?m)^InpTesterCoreExecutionFromServer=.*$',('InpTesterCoreExecutionFromServer='+$case.from+' 00:00:00')
 [IO.File]::WriteAllText((Join-Path $out ($run+'.set')),$preset,[Text.Encoding]::Unicode)
 Copy-Item -LiteralPath (Join-Path $out ($run+'.set')) -Destination (Join-Path $terminal ('MQL5\Profiles\Tester\'+$run+'.set'))
 $ini=(Get-Content -LiteralPath $oldIni -Raw).Replace($old,$run)
 $ini=$ini -replace '(?m)^ToDate=.*$',('ToDate='+$case.until)
 $ini=$ini -replace '(?m)^Port=\d+\s*$',('Port='+($FirstPort+$number))
 $iniPath=Join-Path $out ($run+'.ini');[IO.File]::WriteAllText($iniPath,$ini,[Text.Encoding]::Unicode)
 $jobs+=@{name=$case.name;run=$run;out=$out;terminal=$terminal;ini=$iniPath;done=$false;launched=$false;exited_since=$null}
}
foreach($job in $jobs) {
 $job.process=Start-Process -FilePath (Join-Path $job.terminal 'terminal64.exe') -ArgumentList @('/portable',('/config:"'+$job.ini+'"')) -WindowStyle Hidden -PassThru
 $job.deadline=[DateTime]::UtcNow.AddSeconds($TimeoutSeconds);$job.launched=$true
 Write-Output "START $($job.name) pid=$($job.process.Id)"
}
while(@($jobs|Where-Object {-not $_.done}).Count -gt 0) {
 foreach($job in $jobs) {
  if($job.done) {continue}
  $exe=[IO.Path]::GetFullPath((Join-Path $job.terminal 'terminal64.exe'))
  $replacement=Get-Process terminal64 -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $exe} | Select-Object -First 1
  if($replacement) {$job.process=$replacement;$job.exited_since=$null}
  if(-not $job.process.HasExited -and [DateTime]::UtcNow -lt $job.deadline) {continue}
  if($job.process.HasExited) {
   if($null -eq $job.exited_since) {$job.exited_since=[DateTime]::UtcNow}
   if(([DateTime]::UtcNow-$job.exited_since).TotalSeconds -lt 20) {continue}
  } else {
   if($job.process.Path -ne $exe) {throw 'Unexpected process path'}
   $job.process.Kill();$job.process.WaitForExit()
  }
  $raw=Get-ChildItem -LiteralPath $job.terminal -Filter ($job.run+'*.jsonl') -File -Recurse | Select-Object -First 1
  $snapshot=Join-Path $job.out 'native-files';[IO.Directory]::CreateDirectory($snapshot)|Out-Null
  if($raw) {foreach($file in (Get-ChildItem -LiteralPath $raw.DirectoryName -File)) {New-Item -ItemType HardLink -Path (Join-Path $snapshot $file.Name) -Target $file.FullName|Out-Null}}
  foreach($file in (Get-ChildItem -LiteralPath $job.terminal -Filter ($job.run+'*') -File -Recurse | Where-Object {$_.Extension -in '.html','.png'})) {Copy-Item -LiteralPath $file.FullName -Destination $job.out}
  [ordered]@{case=$job.name;status=if($raw){'CAPTURE_AVAILABLE_REQUIRES_AUDIT'}else{'NO_NATIVE_CAPTURE'};archive=$job.out;raw=if($raw){$raw.FullName}else{$null}}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $job.out 'run-status.json') -Encoding utf8
  Write-Output "DONE $($job.name)";$job.done=$true
 }
 Start-Sleep -Seconds 2
}
Write-Output "COMPLETE $root"
