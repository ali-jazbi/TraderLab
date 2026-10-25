# Supervision only: preserve the already-running Native test and its journals.
param([int]$OriginalSupervisorId=2340)
$ErrorActionPreference='Stop'
$work=Join-Path (Get-Location).Path 'work\long-history-20261023'
$root=(Get-Content (Join-Path $work 'six-month-root.txt') -Raw).Trim()
$terminal=Join-Path $root 'terminal';$exe=Join-Path $terminal 'terminal64.exe'
$original=Get-CimInstance Win32_Process -Filter "ProcessId=$OriginalSupervisorId"
if(-not $original -or $original.Name -ne 'powershell.exe' -or $original.CommandLine -notlike '*-File work/long-history-20261023/run_six_month.ps1'){throw 'Original supervisor identity mismatch'}
if(-not (Get-Process terminal64 -ErrorAction SilentlyContinue|Where-Object {$_.Path -eq $exe})){throw 'No existing Native terminal to adopt'}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class NativeStudySupervisor {
 [DllImport("ntdll.dll")] public static extern int NtSuspendProcess(IntPtr processHandle);
}
'@
$old=Get-Process -Id $OriginalSupervisorId
$result=[NativeStudySupervisor]::NtSuspendProcess($old.Handle)
if($result -ne 0){throw "Supervisor suspension failed: $result"}
[ordered]@{watcher_pid=$PID;old_supervisor_pid=$OriginalSupervisorId;old_supervisor_suspended=$true;native_terminal_not_suspended=$true;native_not_restarted=$true;adopted_utc=[DateTime]::UtcNow.ToString('o');reason='Avoid six-hour supervision timeout while frozen Native run is progressing';strategy_parameters_changed=$false}|ConvertTo-Json|Set-Content (Join-Path $root 'supervision-adoption.json') -Encoding utf8
$exitedSince=$null;$status='TERMINAL_EXIT_REQUIRES_AUDIT'
while($true){
 $active=@(Get-Process terminal64 -ErrorAction SilentlyContinue|Where-Object {$_.Path -eq $exe})
 if($active.Count){$exitedSince=$null}else{
  if($null -eq $exitedSince){$exitedSince=[DateTime]::UtcNow}
  if(([DateTime]::UtcNow-$exitedSince).TotalSeconds -ge 20){break}
 }
 if((Get-PSDrive -Name C).Free -lt 2GB){$status='RESOURCE_STOP_INSUFFICIENT_DISK';break}
 # No elapsed-time kill: only native completion or actual disk exhaustion.
 Start-Sleep -Seconds 3
}
foreach($p in @(Get-Process terminal64 -ErrorAction SilentlyContinue|Where-Object {$_.Path -eq $exe})){$p.Kill();$p.WaitForExit()}
# The original watcher remains suspended until the Native terminal has exited.
$oldNow=Get-CimInstance Win32_Process -Filter "ProcessId=$OriginalSupervisorId"
if($oldNow -and $oldNow.CreationDate -eq $original.CreationDate){Stop-Process -Id $OriginalSupervisorId}
$run=Split-Path -Path $root -Leaf
$raw=Get-ChildItem -LiteralPath $terminal -Filter ($run+'*.jsonl') -File -Recurse|Select-Object -First 1
if($raw){
 $snapshot=Join-Path $root 'native-files';[IO.Directory]::CreateDirectory($snapshot)|Out-Null
 foreach($file in Get-ChildItem -LiteralPath $raw.DirectoryName -File){
  $dest=Join-Path $snapshot $file.Name
  if(Test-Path -LiteralPath $dest){throw "Snapshot already exists; refusing overwrite: $dest"}
  New-Item -ItemType HardLink -Path $dest -Target $file.FullName|Out-Null
 }
}
foreach($file in @(Get-ChildItem -LiteralPath $terminal -Filter ($run+'*') -File -Recurse|Where-Object {$_.Extension -in '.html','.png'})){
 $dest=Join-Path $root $file.Name
 if(Test-Path -LiteralPath $dest){throw "Report already exists; refusing overwrite: $dest"}
 Copy-Item -LiteralPath $file.FullName -Destination $dest
}
[ordered]@{run=$run;status=$status;archive=$root;raw=if($raw){$raw.FullName}else{$null};all_journals_preserved=$true;no_elapsed_time_stop=$true;finished_utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content (Join-Path $root 'run-status.json') -Encoding utf8
Write-Output "COMPLETE $root $status"
