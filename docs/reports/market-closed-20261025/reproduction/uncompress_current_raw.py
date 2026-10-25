"""Transparent NTFS storage control; never rewrite journal contents or EA inputs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess

root=Path('C:/Users/11/TraderLabLongHistory/POLMCFIX2510-0669ccf6').resolve()
raw=next((root/'terminal/Tester/Agent-127.0.0.1-3096/MQL5/Files').glob('POLMCFIX*.jsonl')).resolve()
assert raw.is_relative_to(root)
record=root/'ntfs-storage-control.json'
assert not record.exists()
size=raw.stat().st_size
length=size-64*1024*1024 # exclude the concurrently advancing writer tail
assert length>0 and shutil.disk_usage(root).free>size+20*1024**3
def prefix_hash():
    h=hashlib.sha256();remaining=length
    with raw.open('rb') as file:
        while remaining:
            data=file.read(min(8*1024*1024,remaining))
            if not data:raise ValueError('The append-only prefix shortened')
            h.update(data);remaining-=len(data)
    return h.hexdigest()
r=dict(started_utc=datetime.now(timezone.utc).isoformat(),file=str(raw),initial_size=size,
       stable_prefix_bytes=length,compressed_before=bool(raw.stat().st_file_attributes&stat.FILE_ATTRIBUTE_COMPRESSED),
       operation='compact.exe /U /Q on only the current-run raw JSONL; no source/old archives',
       native_agent_not_suspended=True,native_not_restarted=True,ea_or_strategy_inputs_changed=False,
       reason='Reuse the previously verified transparent NTFS storage control on this isolated regression output before the first baseline trade; no strategy or execution-input change',
       documentation=['https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/compact',
                      'https://learn.microsoft.com/en-us/windows/desktop/api/winioctl/ni-winioctl-fsctl_set_compression'])
r['prefix_before_sha256']=prefix_hash()
record.write_text(json.dumps(r,indent=2)+'\n')
done=subprocess.run(['compact.exe','/U','/Q',str(raw)],capture_output=True,text=True)
r.update(command_exit_code=done.returncode,command_stdout=done.stdout,command_stderr=done.stderr,
         prefix_after_sha256=prefix_hash(),compressed_after=bool(raw.stat().st_file_attributes&stat.FILE_ATTRIBUTE_COMPRESSED),
         completed_utc=datetime.now(timezone.utc).isoformat())
r['stable_prefix_unchanged']=r['prefix_before_sha256']==r['prefix_after_sha256']
record.write_text(json.dumps(r,indent=2)+'\n')
assert r['stable_prefix_unchanged'],'Invalidate result and inspect: stable append-only prefix changed'
print(json.dumps(r,indent=2))
