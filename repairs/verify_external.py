"""Independent semantic regression tests. Never calls a real provider or payment API."""
import argparse
import ast
import asyncio
import copy
import hashlib
import http.client
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
import urllib.error

DEFAULT_Q = Path(r'C:\Users\Andrii\Desktop\Desktop_2026_August\02_Scripts_and_Tools\YouTube_Shorts_Arsenal_2026\Quantum_Trinity')
DEFAULT_SENTINEL = Path(r'C:\Users\Andrii\Desktop\KI\token-monster\global_sanity_sentinel.py')


def load(path, name, database=None):
    # Redirect the module's default DB before evaluating it, including the old baseline.
    tree = ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    if database is not None:
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'DB_PATH' for t in node.targets):
                node.value = ast.parse('Path(' + repr(str(database)) + ')', mode='eval').body
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader=None))
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(ast.fix_missing_locations(tree), str(path), 'exec'), module.__dict__)
    return module


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='argon-contracts-')
        cls.directory = Path(cls.temp.name)
        cls.codec = load(SENTINEL, 'audit_sentinel').BidirectionalJymovaCodec
        cls.proxy = load(Q / 'quantum_omni_router.py', 'audit_proxy')
        cls.payment = load(Q / 'MicroSaaS_MVP_01/app_server.py', 'audit_payment', cls.directory / 'only-test.sqlite')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_codec_roundtrips_exact_source_and_literals(self):
        samples = ['configuration = "function"\r\n', 'Please note that this exact phrase is test data.',
                   'fn cfg impl @JYMOVA_DICT[$S00=literal]\n', 'Привіт 🌧 Zürich\r\n\r\n',
                   'a_really_long_identifier_name = "a_really_long_identifier_name"\n' * 40,
                   '[CCR x3]: this is a literal log line\n\n\n']
        for source in samples:
            with self.subTest(source=source[:50]):
                dense, symbols, _ = self.codec.encode_text_or_code(source)
                self.assertEqual(self.codec.decode_frontier_output(dense, symbols), source)

    def test_quantum_codec_roundtrip_with_full_package(self):
        for mode, source in [('prompt', 'Please note that configuration means configuration.\n'),
                             ('code', 'configuration = "function"\r\n\r\n'),
                             ('log', '[CCR x3]: literal\r\nINFO test\r\n' * 10)]:
            with self.subTest(mode=mode):
                packet = self.proxy.QuantumCodec.compress(source, mode)
                self.assertEqual(self.proxy.QuantumCodec.decompress(packet), source)

    def post_proxy(self, payload, upstream):
        server = ThreadingHTTPServer(('127.0.0.1', 0), self.proxy.QuantumProxyHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(os.environ, {'QUANTUM_UPSTREAM_URL': 'http://127.0.0.1:9'}, clear=True):
                target = (self.proxy, 'open_upstream') if hasattr(self.proxy, 'open_upstream') else (self.proxy.urllib.request, 'urlopen')
                with patch.object(*target, upstream):
                    client = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
                    client.request('POST', '/v1/chat/completions', json.dumps(payload), {'Content-Type': 'application/json'})
                    response = client.getresponse()
                    status, body = response.status, json.loads(response.read())
                    client.close()
                    return status, body
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_proxy_offline_is_failure_without_completion_or_fake_usage(self):
        def unavailable(*_args, **_kwargs):
            raise urllib.error.URLError('synthetic offline test')
        status, body = self.post_proxy({'model': 'synthetic-test', 'messages': [{'role': 'user', 'content': 'test'}]}, unavailable)
        self.assertIn(status, (502, 503, 504))
        self.assertIn('error', body)
        self.assertNotIn('choices', body)
        self.assertNotIn('usage', body)

    def test_proxy_preserves_entire_protocol_payload(self):
        body = {'model': 'synthetic-test', 'messages': [{'role': 'assistant', 'content': 'cached', 'signature': 'synthetic'},
                {'role': 'user', 'content': 'Please note that configuration is literal.'}],
                'tools': [{'type': 'function', 'function': {'name': 'configuration', 'parameters': {'type': 'object'}}}],
                'temperature': 0}
        seen = []
        class Response(io.BytesIO):
            status = 200
            def getheaders(self): return [('Content-Type', 'application/json')]
        def upstream(request, **_):
            seen.append(json.loads(request.data))
            return Response(b'{"choices":[]}')
        self.assertEqual(self.post_proxy(copy.deepcopy(body), upstream)[0], 200)
        self.assertEqual(seen, [body])

    def test_paid_checkout_cannot_issue_key_without_payment(self):
        ledger = self.payment.DatabaseLedger(self.directory / 'unpaid.sqlite')
        with ledger._get_connection() as conn:
            before = conn.execute('SELECT count(*) FROM api_keys').fetchone()[0]
        with self.assertRaises(ValueError):
            ledger.record_checkout('synthetic@example.invalid', 'pro', 29.0, 'stripe')
        with ledger._get_connection() as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM api_keys').fetchone()[0], before)
            self.assertEqual(conn.execute('SELECT count(*) FROM checkout_transactions').fetchone()[0], 0)

    def test_http_checkout_without_configuration_is_unavailable(self):
        import httpx
        async def request():
            with patch.dict(os.environ, {}, clear=True):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.payment.app), base_url='http://testserver') as client:
                    return await client.post('/api/v1/billing/checkout', json={'customer_email':'synthetic@example.invalid', 'tier':'pro', 'payment_method':'stripe'})
        response = asyncio.run(request())
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('api_key', response.json())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=DEFAULT_Q)
    parser.add_argument('--sentinel', type=Path, default=DEFAULT_SENTINEL)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    Q, SENTINEL = args.root, args.sentinel
    sys.path.insert(0, str(Q))
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contracts)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'passed':result.wasSuccessful(), 'tests':result.testsRun,
              'failures':len(result.failures), 'errors':len(result.errors),
              'oracle_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SENTINEL, Q/'quantum_omni_router.py', Q/'MicroSaaS_MVP_01/app_server.py']},
              'boundary':'Loopback synthetic upstream and isolated temporary database. Real provider calls=0; real payments=0.'}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))
    raise SystemExit(not result.wasSuccessful())
