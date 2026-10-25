"""Independent semantic checks and preimage rejection in a disposable copy."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASE = '7e1b314f010c114fdde6d8cd387601442652f76c'
SOURCES = ['ai-architect/runtime.py', 'simulation-core/unified_tick.py',
           'simulation-core/persistence.py', 'engine-isometric-ui/app.mjs']
COMMANDS = [[sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_returned_repairs.py', '-q'],
            [shutil.which('node'), '--test', 'tests/retry-ack.test.mjs']]


def run(root, command):
    result = subprocess.run(command, cwd=root, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=60)
    return {'command': [Path(command[0]).name, *command[1:]], 'exit_code': result.returncode,
            'output': (result.stdout + result.stderr).replace(str(root), '<subject>')}


def main():
    rows = []
    for command in COMMANDS:
        result = {'mode': 'current', **run(ROOT, command)}
        result['accepted'] = result['exit_code'] == 0
        rows.append(result)
    with tempfile.TemporaryDirectory(prefix='sovereign-preimage-', dir=ROOT.parent) as temporary:
        subject = Path(temporary) / 'subject'
        shutil.copytree(ROOT, subject, ignore=shutil.ignore_patterns('.git', '.runtime', 'local-*', '__pycache__', 'node_modules'))
        for source in SOURCES:
            data = subprocess.check_output(['git', 'show', BASE + ':' + source], cwd=ROOT)
            (subject / source).write_bytes(data)
        for command in COMMANDS:
            result = {'mode': 'preimage', **run(subject, command)}
            result['accepted'] = result['exit_code'] != 0 and 'AssertionError' in result['output'] and not any(
                text in result['output'] for text in ('ModuleNotFoundError', 'SyntaxError', 'ENOENT'))
            rows.append(result)
    files = SOURCES + ['tests/test_returned_repairs.py', 'tests/retry-ack.test.mjs', 'scripts/verify.py']
    report = {'status': 'PASS' if all(r['accepted'] for r in rows) else 'FAIL',
              'observed_utc': datetime.now(timezone.utc).isoformat(), 'base': BASE,
              'fingerprints': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files},
              'checks': rows, 'limits': 'Synthetic state and stubbed DOM/HTTP; no live browser, provider or Linux durability acceptance.'}
    target = ROOT / 'audit/local-recovered-guards.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'checks': len(rows), 'report': str(target.relative_to(ROOT))}))
    return int(report['status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())
