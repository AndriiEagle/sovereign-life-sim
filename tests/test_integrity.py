from pathlib import Path
import hashlib
import importlib.util
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('package_verify', Path(__file__).resolve().parents[1] / 'scripts/verify.py')
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class SourceIntegrityTests(unittest.TestCase):
    def test_missing_package_manifest_cannot_be_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in verify.REQUIRED:
                if name == 'PACKAGE_MANIFEST.json':
                    continue
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('{}', encoding='utf-8')
            (root / 'audit/source-copies.json').write_text('{"copies":[]}', encoding='utf-8')
            (root / 'CONTEXT_MANIFEST.json').write_text('{"projects":[]}', encoding='utf-8')
            (root / 'USER_DIGITAL_TWIN_SEED.json').write_text('{"unknowns":{}}', encoding='utf-8')
            (root / 'automation-nodes/catalog.json').write_text('{"nodes":[]}', encoding='utf-8')
            (root / 'SYNERA_LAUNCH_CHECKLIST.md').write_text('\n'.join(f'{i}. **action**' for i in range(1, 6)), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'MISSING_REQUIRED_FILE: PACKAGE_MANIFEST.json'):
                verify.contract_checks(root)

    def test_exact_copy_accepted_then_changed_copy_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'source.py'
            path.write_bytes(b'original')
            rows = [{'target': 'source.py', 'sha256': hashlib.sha256(b'original').hexdigest()}]
            verify.check_copies(root, rows)
            path.write_bytes(b'altered')
            with self.assertRaisesRegex(ValueError, 'SNAPSHOT_MISSING_OR_CHANGED'):
                verify.check_copies(root, rows)

    def test_foreign_path_and_missing_dependency_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ['../source.py', '/outside.py', 'C:/secret', '..\\secret']:
                with self.subTest(path=name), self.assertRaises(ValueError):
                    verify.safe_target(root, name)
            with self.assertRaisesRegex(ValueError, 'SNAPSHOT_MISSING_OR_CHANGED'):
                verify.check_copies(root, [{'target': 'missing.py', 'sha256': '0' * 64}])
