import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('demo_server', Path(__file__).resolve().parents[1] / 'scripts/serve.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class ServerPrivacyTests(unittest.TestCase):
    def test_entrypoint_is_demo(self):
        self.assertEqual(server.allowed_path('/'), '/engine-isometric-ui/index.html')

    def test_private_paths_and_encoded_traversal_are_rejected(self):
        for path in ['/.git/config', '/USER_DIGITAL_TWIN_SEED.json', '/CONTEXT_MANIFEST.json',
                     '/audit/source-copies.json', '/engine-isometric-ui/../USER_DIGITAL_TWIN_SEED.json',
                     '/engine-isometric-ui/%2e%2e/USER_DIGITAL_TWIN_SEED.json', '/%252e%252e/.env']:
            with self.subTest(path=path):
                self.assertIsNone(server.allowed_path(path))
