"""Portable source/contract acceptance, independent of Sol's original project paths."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ('PACKAGE_MANIFEST.json', 'audit/git-base.json', 'CONTEXT_MANIFEST.json', 'USER_DIGITAL_TWIN_SEED.json', 'SYNERA_LAUNCH_CHECKLIST.md',
            'HANDOFF.md', 'TASKS.md', 'EXTERNAL_PROMPT.md', 'RIGHTS.md', 'audit/source-copies.json',
            'engine-isometric-ui/index.html', 'simulation-core/game-forge/sim/core.py',
            'simulation-core/revenue_lab/core.py', 'automation-nodes/catalog.json', 'mcp-bridge/events.mjs')


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def safe_target(root, relative):
    rel = PurePosixPath(relative)
    if not relative or '\\' in relative or ':' in relative or rel.is_absolute() or '..' in rel.parts:
        raise ValueError('UNSAFE_SNAPSHOT_PATH')
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('SNAPSHOT_OUTSIDE_ROOT')
    return path


def check_copies(root, rows):
    for row in rows:
        path = safe_target(root, row['target'])
        if not path.is_file() or sha(path) != row['sha256']:
            raise ValueError('SNAPSHOT_MISSING_OR_CHANGED: ' + row['target'])


def contract_checks(root):
    for name in REQUIRED:
        if not (root / name).is_file():
            raise ValueError('MISSING_REQUIRED_FILE: ' + name)
    copies = json.loads((root / 'audit/source-copies.json').read_text(encoding='utf-8'))['copies']
    check_copies(root, copies)
    manifest = json.loads((root / 'CONTEXT_MANIFEST.json').read_text(encoding='utf-8'))
    for project in manifest['projects']:
        if project['readiness_percent'] is not None:
            raise ValueError('UNSUPPORTED_READINESS_PERCENT')
    seed = json.loads((root / 'USER_DIGITAL_TWIN_SEED.json').read_text(encoding='utf-8'))
    if any(value is not None for value in seed['unknowns'].values()):
        raise ValueError('UNVERIFIED_PERSONAL_PARAMETER')
    catalog = json.loads((root / 'automation-nodes/catalog.json').read_text(encoding='utf-8'))
    if any(node['enabled'] or not node['dry_run'] or node['external_effects'] for node in catalog['nodes']):
        raise ValueError('EXTERNAL_NODE_ENABLED')
    checklist = (root / 'SYNERA_LAUNCH_CHECKLIST.md').read_text(encoding='utf-8')
    if len(re.findall(r'^\d\. \*\*', checklist, re.M)) != 5:
        raise ValueError('CHECKLIST_MUST_HAVE_FIVE_ACTIONS')
    lock = root / 'PACKAGE_MANIFEST.json'
    rows = json.loads(lock.read_text(encoding='utf-8'))['files']
    names = [row['path'] for row in rows]
    if len(names) != len(set(names)) or not set(REQUIRED[1:]).issubset(names):
        raise ValueError('PACKAGE_COVERAGE_MISSING_OR_DUPLICATED')
    for row in rows:
        path = safe_target(root, row['path'])
        if not path.is_file() or sha(path) != row['sha256']:
            raise ValueError('PACKAGE_CHANGED: ' + row['path'])
    return {'source_copies': len(copies), 'projects': len(manifest['projects']), 'seed_unknowns_preserved': True}


def run(command, cwd):
    start = time.monotonic()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return {'command': command, 'cwd': str(cwd.relative_to(ROOT)), 'exit_code': result.returncode,
            'elapsed_seconds': round(time.monotonic() - start, 3),
            'summary': (result.stdout + result.stderr)[-1800:]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--integrity-only', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        facts = contract_checks(ROOT)
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({'status': 'FAIL', 'error': str(error)}))
        return 1
    runs = []
    if not args.integrity_only:
        node = shutil.which('node')
        if not node:
            print(json.dumps({'status': 'HOLD', 'error': 'NODE_NOT_FOUND_IN_CHECKED_PATH'}))
            return 1
        commands = [
            ([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'upstream-tests', '-q'], ROOT / 'simulation-core'),
            ([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'sim/tests', '-t', '.', '-q'], ROOT / 'simulation-core/game-forge'),
            ([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-q'], ROOT),
            ([node, '--test', 'tests/model.test.mjs', 'tests/events.test.mjs'], ROOT),
            ([sys.executable, '-B', 'scripts/scenario.py', '--ticks', '96', '--action', 'rest', '--seed', '42'], ROOT),
        ]
        for command, cwd in commands:
            row = run(command, cwd)
            runs.append(row)
            print(json.dumps({'check': len(runs), 'exit_code': row['exit_code'], 'seconds': row['elapsed_seconds']}), flush=True)
            if row['exit_code']:
                break
    success = all(row['exit_code'] == 0 for row in runs)
    report = {'status': 'PASS' if success else 'FAIL', 'facts': facts, 'runs': runs,
              'boundary': 'Portable component/source acceptance only. Browser, native engines, live Synera, real MCP transport and customers require separate observed evidence.'}
    if args.report:
        target = safe_target(ROOT, args.report.as_posix())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], **facts, 'commands': len(runs)}))
    if not success:
        print(runs[-1]['summary'])
    return int(not success)


if __name__ == '__main__':
    raise SystemExit(main())
