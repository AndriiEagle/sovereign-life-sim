"""Finite audit checks and reversible mutations, without installs or hosted calls.

The report goes to an ignored path. Mutations happen only in disposable copies.
Run from any directory: python -B audit/repeat-journal-20261018/run_checks.py
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def run(root, arguments):
    started = time.monotonic()
    result = subprocess.run([sys.executable, '-B', '-X', 'utf8', *arguments],
                            cwd=root, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=60)
    output = (result.stdout + result.stderr).replace(str(root), '<subject>')
    return {'command': ['python', '-B', '-X', 'utf8', *arguments],
            'exit_code': result.returncode,
            'elapsed_seconds': round(time.monotonic() - started, 3),
            'output': output}


def main():
    cases = []
    supplemental = ['-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_journal_review.py', '-q']
    concurrent = ['-m', 'unittest', 'discover', '-s', 'tests', '-p',
                  'test_phase2.py', '-k', 'concurrent_retry', '-q']
    root_suite = ['-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-q']
    for name, arguments in [('candidate_journal_checks', supplemental),
                            ('candidate_root_python_suite', root_suite),
                            ('candidate_concurrent_retry', concurrent)]:
        row = {'case': name, **run(ROOT, arguments)}
        row['accepted'] = row['exit_code'] == 0
        cases.append(row)
        print(json.dumps({'case': name, 'accepted': row['accepted']}), flush=True)

    with tempfile.TemporaryDirectory(prefix='sovereign-journal-review-') as temporary:
        subject = Path(temporary) / 'subject'
        shutil.copytree(ROOT, subject, ignore=shutil.ignore_patterns(
            '.git', '.runtime', '.venv', 'node_modules', '__pycache__', 'local-*'))
        mutations = [
            ('preimage_cr_splits_complete_record', 'simulation-core/persistence.py',
             'for line in io.BytesIO(data):', 'for line in data.splitlines(keepends=True):', supplemental),
            ('duplicate_guard_removed', 'ai-architect/runtime.py',
             'previous=self.store.duplicate(request_id,fingerprint)', 'previous=None', concurrent),
        ]
        for name, relative, before, after, arguments in mutations:
            target = subject / relative
            original = target.read_bytes()
            text = original.decode('utf-8')
            if text.count(before) != 1:
                raise ValueError('MUTATION_TARGET_NOT_UNIQUE: ' + relative)
            target.write_bytes(text.replace(before, after).encode('utf-8'))
            try:
                row = {'case': name, 'mutation_path': relative, **run(subject, arguments)}
                row['accepted'] = row['exit_code'] != 0 and 'AssertionError' in row['output']
                cases.append(row)
                print(json.dumps({'case': name, 'accepted': row['accepted']}), flush=True)
            finally:
                target.write_bytes(original)

    paths = ['simulation-core/persistence.py', 'ai-architect/runtime.py',
             'tests/test_phase2.py', 'tests/test_journal_review.py',
             'audit/repeat-journal-20261018/run_checks.py']
    report = {
        'schema': 'sovereign.journal-review.v1',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'status': 'PASS' if all(row['accepted'] for row in cases) else 'FAIL',
        'platform': sys.platform, 'python': sys.version.split()[0],
        'source_base': '5963e7d1dc54057db73f61159171f1bb94f94604',
        'fingerprints': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths},
        'checks': cases,
        'effects': 'Disposable synthetic state and temporary mutations only. No provider calls.',
        'limits': ['No physical power-loss or disk-controller durability test',
                   'No Linux filesystem/lock run', 'No hosted providers, real customer data or live Synera',
                   'No new visual, official SDK or rootless-sandbox acceptance'],
    }
    target = ROOT / 'audit/local-journal-focused.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'report': target.relative_to(ROOT).as_posix()}))
    return int(report['status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())
