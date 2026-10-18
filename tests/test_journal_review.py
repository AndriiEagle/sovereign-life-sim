"""Additional disposable-state checks for the external journal audit.

These exercise the public Runtime entry point and real filesystem/process effects.
They do not call providers, load personal state, or change the installed app.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
for directory in ('simulation-core', 'ai-architect'):
    sys.path.insert(0, str(ROOT / directory))
from persistence import Store
from runtime import Runtime


def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


class JournalReviewTests(unittest.TestCase):
    def make_committed_journal(self, directory):
        app = Runtime(ROOT, directory)
        try:
            app.execute('tick', {'hours': 1}, 'journal-review-0001')
            return app.get()
        finally:
            app.close()

    def test_corrupt_complete_row_is_rejected_without_truncation(self):
        for damage in ('state_checksum', 'sequence', 'previous_hash', 'invalid_json_with_cr'):
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                self.make_committed_journal(directory)
                path = directory / 'events.jsonl'
                lines = path.read_bytes().splitlines(keepends=True)
                row = json.loads(lines[-1])
                if damage == 'state_checksum':
                    row['state']['life']['balance_cents'] += 1
                elif damage == 'sequence':
                    row['seq'] += 1
                elif damage == 'previous_hash':
                    row['previous'] = '1' * 64
                if damage in ('sequence', 'previous_hash'):
                    unsigned = {key: value for key, value in row.items() if key != 'sha256'}
                    row['sha256'] = hashlib.sha256(canonical_bytes(unsigned)).hexdigest()
                lines[-1] = canonical_bytes(row) + b'\n'
                if damage == 'invalid_json_with_cr':
                    # Still a complete LF-terminated record, not an interrupted EOF tail.
                    lines[-1] = b'BROKEN\r' + lines[-1]
                damaged = b''.join(lines)
                path.write_bytes(damaged)
                with self.assertRaises(ValueError):
                    unexpected = Runtime(ROOT, directory)
                    unexpected.close()
                self.assertEqual(path.read_bytes(), damaged)

    def test_interrupted_eof_tail_preserved_exactly_with_unicode_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            expected = self.make_committed_journal(directory)
            path = directory / 'events.jsonl'
            committed = path.read_bytes()
            tail = '{"interrupted":"Україна'.encode('utf-8') + b'\xe2'
            path.write_bytes(committed + tail)
            (directory / 'state.json').write_bytes(b'not a snapshot')
            app = Runtime(ROOT, directory)
            try:
                self.assertEqual(app.get(), expected)
                self.assertEqual(path.read_bytes(), committed)
                self.assertEqual([p.read_bytes() for p in directory.glob('interrupted-*.bin')], [tail])
            finally:
                app.close()

    def test_committed_crlf_records_recover_without_loss(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            expected = self.make_committed_journal(directory)
            path = directory / 'events.jsonl'
            crlf = path.read_bytes().replace(b'\n', b'\r\n')
            path.write_bytes(crlf)
            app = Runtime(ROOT, directory)
            try:
                self.assertEqual(app.get(), expected)
                self.assertEqual(path.read_bytes(), crlf)
                self.assertEqual(list(directory.glob('interrupted-*.bin')), [])
            finally:
                app.close()

    def test_real_process_lease_blocks_then_releases(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            # Store's minimum actual commit contract includes sim_time.
            initial = {'sim_time': '2026-10-18T00:00:00Z', 'revision': 0}
            store = Store(directory, deepcopy(initial))
            child = (
                'import json,sys; from pathlib import Path; '
                'sys.path.insert(0,sys.argv[1]); from persistence import Store; '
                '\ntry:\n s=Store(Path(sys.argv[2]),json.loads(sys.argv[3]))'
                '\nexcept ValueError as e:\n print(str(e))'
                '\nelse:\n s.close(); print("OPENED")\n'
            )
            command = [sys.executable, '-B', '-c', child, str(ROOT / 'simulation-core'),
                       str(directory), json.dumps(initial)]
            before = (directory / 'events.jsonl').read_bytes()
            try:
                blocked = subprocess.run(command, capture_output=True, text=True, timeout=15)
                self.assertEqual(blocked.returncode, 0, blocked.stderr)
                self.assertEqual(blocked.stdout.strip(), 'STORE_ALREADY_IN_USE')
                self.assertEqual((directory / 'events.jsonl').read_bytes(), before)
            finally:
                store.close()
            opened = subprocess.run(command, capture_output=True, text=True, timeout=15)
            self.assertEqual(opened.returncode, 0, opened.stderr)
            self.assertEqual(opened.stdout.strip(), 'OPENED')
            self.assertEqual((directory / 'events.jsonl').read_bytes(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
