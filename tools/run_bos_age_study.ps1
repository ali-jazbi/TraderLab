param(
 [string]$HistoryBase='D:\Codex\POLDISC1810-13be7b1c\M7\terminal\bases',
 [string]$ArchiveParent="$env:LOCALAPPDATA\TraderLabTesterArchives",
 [int]$Parallel=3,
 [int]$FirstPort=3100
)
$ErrorActionPreference='Stop'
if($Parallel -lt 1 -or $Parallel -gt 3) { throw 'Use1–3 independent portable Tester instances' }
$repo=Split-Path -Parent $PSScriptRoot
$drive=[IO.DriveInfo]::new([IO.Path]::GetPathRoot([IO.Path]::GetFullPath($ArchiveParent)))
if($drive.AvailableFreeSpace -lt 35GB) { throw 'Six full-history archives require35GiB free; choose ArchiveParent before starting' }
$data='C:\Users\mehdi\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075'
$batch='POLAGE1910-'+[guid]::NewGuid().ToString('N').Substring(0,8)
$root=Join-Path $ArchiveParent $batch
[IO.Directory]::CreateDirectory($root)|Out-Null
# Lossless NTFS compression inherited by NEW archives; original history is read-only.
& compact.exe /C /I /Q $root | Out-Null
[IO.File]::WriteAllText((Join-Path $repo 'work\auto-core\current-age-batch.txt'),$root)
Write-Output "ARCHIVE $root"
$jobs=@(); $number=0
foreach($window in @('training','holdout')) {
 foreach($age in @(0,60,120)) {
  $number++; $name=$window+'-AGE'+$age; $run=$batch+'-'+$name
  $out=Join-Path $root $name; $portable=Join-Path $out 'terminal'
  [IO.Directory]::CreateDirectory($portable)|Out-Null
  foreach($exe in @('terminal64.exe','metatester64.exe')) { Copy-Item -LiteralPath (Join-Path 'C:\Program Files\MetaTrader 5' $exe) -Destination $portable }
  [IO.Directory]::CreateDirectory((Join-Path $portable 'config'))|Out-Null
  foreach($file in @('accounts.dat','servers.dat','common.ini')) { Copy-Item -LiteralPath (Join-Path $data ('config\'+$file)) -Destination (Join-Path $portable 'config') }
  Copy-Item -LiteralPath $HistoryBase -Destination (Join-Path $portable 'bases') -Recurse
  foreach($dir in @('MQL5\Experts\TraderLab','MQL5\Files','MQL5\Profiles\Tester')) { [IO.Directory]::CreateDirectory((Join-Path $portable $dir))|Out-Null }
  Copy-Item -LiteralPath (Join-Path $repo 'mt5\AUTO_CORE_DEMO.ex5') -Destination (Join-Path $portable ('MQL5\Experts\TraderLab\'+$run+'.ex5'))
  Copy-Item -LiteralPath (Join-Path $repo 'mt5\AUTO_CORE_DEMO.ex5') -Destination (Join-Path $out 'tested.ex5')
  Copy-Item -LiteralPath (Join-Path $repo 'work\auto-core\DISC-OOS-calendar-20261018.calendar.csv') -Destination (Join-Path $portable 'MQL5\Files\TraderLab-auto-tester-calendar.csv')
  $old=if($window -eq 'training') {'POLDISC1810-5e62a5fc-M7'} else {'POLDISC1810-13be7b1c-M7'}
  $report=Join-Path $repo ('docs\reports\auto-core-discovery-20261018\final-'+$window+'\'+$old)
  $preset=(Get-Content -LiteralPath (Join-Path $report ($old+'.set')) -Raw).Replace($old,$run)+"`r`nInpExperimentalM1MaxAgeMinutes=$age`r`n"
  [IO.File]::WriteAllText((Join-Path $out ($run+'.set')),$preset,[Text.Encoding]::Unicode)
  Copy-Item -LiteralPath (Join-Path $out ($run+'.set')) -Destination (Join-Path $portable ('MQL5\Profiles\Tester\'+$run+'.set'))
  $ini=(Get-Content -LiteralPath (Join-Path $report ($old+'.ini')) -Raw).Replace($old,$run)
  $ini=$ini -replace 'Port=\d+',('Port='+($FirstPort+$number))
  [IO.File]::WriteAllText((Join-Path $out ($run+'.ini')),$ini,[Text.Encoding]::Unicode)
  $jobs+=@{name=$name;run=$run;out=$out;portable=$portable;process=$null;done=$false}
 }
}
while(($jobs | Where-Object { -not $_.done }).Count -gt 0) {
 foreach($job in $jobs) {
  if($job.done) {continue}
  if($null -eq $job.process) {
   $running=@($jobs | Where-Object {$null -ne $_.process -and -not $_.done}).Count
   if($running -ge $Parallel) {continue}
   $job.process=Start-Process (Join-Path $job.portable 'terminal64.exe') -ArgumentList @('/portable',('/config:"'+(Join-Path $job.out ($job.run+'.ini'))+'"')) -WindowStyle Hidden -PassThru
   Write-Output ("START "+$job.name+" pid="+$job.process.Id)
  }
  elseif($job.process.HasExited) {
   $raw=Get-ChildItem -LiteralPath $job.portable -Filter ($job.run+'*.jsonl') -File -Recurse | Select-Object -First 1
   if(-not $raw) {throw ("No native capture; preserve failed archive: "+$job.out)}
   # Closed-run snapshot: same-volume hardlinks avoid fragile directory junctions.
   $snapshot=Join-Path $job.out 'native-files'
   [IO.Directory]::CreateDirectory($snapshot)|Out-Null
   foreach($file in (Get-ChildItem -LiteralPath $raw.DirectoryName -File)) {
    New-Item -ItemType HardLink -Path (Join-Path $snapshot $file.Name) -Target $file.FullName | Out-Null
   }
   foreach($file in (Get-ChildItem -LiteralPath $job.portable -Filter ($job.run+'*') -File -Recurse | Where-Object {$_.Extension -in '.html','.png'})) { Copy-Item -LiteralPath $file.FullName -Destination $job.out }
   $job.done=$true
   Write-Output ("DONE "+$job.name+" raw="+$raw.Length)
  }
 }
 Start-Sleep -Seconds 2
}
Write-Output "COMPLETE $root"
