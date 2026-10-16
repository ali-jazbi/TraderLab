"""Package a compiled, locked review candidate. Never install or activate an EA."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root, output):
    root, output = Path(root), Path(output)
    validation_path = root / 'docs/reports/auto-core-engineering-20261016.json'
    if not validation_path.exists():
        validation_path = root / 'docs/reports/auto-core-validation-20261016.json'
    validation = json.loads(validation_path.read_text(encoding='utf-8'))
    if validation['automatic_demo_ready'] is not False:
        raise ValueError('This packager is only for the locked candidate')
    for relative, expected in validation['validated_source_sha256'].items():
        content = (root / relative).read_bytes()
        if validation.get('source_hash_mode') == 'LF_NORMALIZED_TEXT':
            content = content.replace(b'\r\n', b'\n')
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError('Source changed after validation: ' + relative)
    binary = root / 'mt5/AUTO_CORE_DEMO.ex5'
    if sha(binary) != validation['compiled_binary_sha256']['AUTO_CORE_DEMO']:
        raise ValueError('Candidate binary differs from compiler evidence')
    for name, expected in validation['compiled_binary_sha256'].items():
        if sha(root / 'mt5' / (name + '.ex5')) != expected:
            raise ValueError('Compiled binary changed: ' + name)
    members = [root / p for p in validation['validated_source_sha256']]
    members += [root / p for p in ('mt5/AUTO_CORE_DEMO.mq5', 'mt5/TraderLab.mq5',
        'mt5/activation/AUTO_CORE_DEMO.locked.set', 'docs/AUTO_CORE_AUDIT_20261016.md',
        'tools/audit_auto_core.py',
        'configs/core-calendar.sources-20261016.json',
        'configs/TraderLab-core-calendar-20261019.csv',
        'configs/TraderLab-core-calendar-20261019.manifest.json')]
    engineering = root/'docs/AUTO_CORE_ENGINEERING_20261016.md'
    if engineering.exists():
        members.append(engineering)
    if (root/'mt5/AutoCoreIntegrationChecks.ex5').exists():
        members.append(root/'mt5/AutoCoreIntegrationChecks.ex5')
    if (root/'mt5/AutoCoreProcessRestartChecks.ex5').exists():
        members.append(root/'mt5/AutoCoreProcessRestartChecks.ex5')
    members += [binary, validation_path]
    members = sorted(set(members))
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    manifest = {'name': 'AUTO_CORE_DEMO-EXPERIMENTAL-equal-level-v1-LOCKED',
        'source_commit': commit, 'automatic_demo_ready': False,
        'install_or_enable_live': False, 'tester_runtime_verified': False,
        'native_synthetic_integration': validation.get('native_synthetic_integration'),
        'physical_terminal_restart': validation.get('physical_terminal_restart'),
        'policy': 'same_frame_earliest_qualified_equal_level_v1',
        'real_broker_orders_submitted_this_validation': 0,
        'historical_tester_orders_this_validation': 0,
        'fresh_real_tick_backtest': 'UNAVAILABLE_MISSING_EXISTING_HISTORY',
        'files': {p.relative_to(root).as_posix(): sha(p) for p in sorted(members)}}
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation preserves every prior delivery archive.
    with output.open('xb') as stream, ZipFile(stream, 'w', ZIP_DEFLATED) as archive:
        for path in sorted(members):
            archive.write(path, path.relative_to(root).as_posix())
        archive.writestr('manifest.json', json.dumps(manifest, indent=2) + '\n')
    return {'archive': str(output), 'sha256': sha(output), 'source_commit': commit,
            'automatic_demo_ready': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(Path(__file__).resolve().parents[1], args.out), indent=2))
