"""Adversarial checks separate from the paired six-test baseline oracle."""
import asyncio
import hashlib
import http.client
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import verify_external as core

core.Q,core.SENTINEL=core.DEFAULT_Q,core.DEFAULT_SENTINEL
sys.path.insert(0,str(core.Q))
import lossless_codec as codec


class EdgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.proxy=core.load(core.Q/'quantum_omni_router.py','edge_proxy')
        cls.payment=core.load(core.Q/'MicroSaaS_MVP_01/app_server.py','edge_payment',Path(cls.temp.name)/'synthetic.sqlite')

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_roundtrip_fuzz_and_reserved_framing(self):
        rng=random.Random(530)
        alphabet=['configuration','function','fn','cfg','\\path\\long-long-file-name.py','⟦literal:0⟧','🌧','é','中文','\r\n','\n',' ','$S00','Please note that']
        for _ in range(250):
            source=''.join(rng.choice(alphabet) for _ in range(rng.randrange(0,150)))
            dense,symbols=codec.encode(source)
            self.assertEqual(codec.decode(dense,symbols),source)
        source=codec.PREFIX+'{"symbols":{},"sha256":"literal"}\nraw literal'
        self.assertEqual(codec.decode(codec.encode(source)[0]),source)

    def test_compression_packet_counts_header_and_rejects_corruption_and_bombs(self):
        source='a_very_long_exact_identifier_that_must_remain_unchanged_0123456789\r\n'*100
        dense,symbols=codec.encode(source)
        self.assertTrue(symbols)
        self.assertLess(len(dense.encode()),len(source.encode()))
        with self.assertRaises(ValueError):codec.decode(dense+'changed')
        marker='⟦0123456789ab:0⟧'
        packet=codec.PREFIX+json.dumps({'symbols':{marker:'a'*10000},'sha256':'0'*64})+'\n'+marker*1000
        with self.assertRaises(ValueError):codec.decode(packet)
        with self.assertRaises(ValueError):codec.decode('legacy $S00',{'$S00':'unverified'})

    def test_upstream_http_errors_are_preserved(self):
        for code in (401,429,500):
            def unavailable(*_args,**_kwargs):raise urllib.error.HTTPError('http://synthetic.invalid',code,'synthetic',{},None)
            status,body=core.Contracts.post_proxy(self,{'model':'synthetic','messages':[]},unavailable)
            self.assertEqual(status,code);self.assertNotIn('choices',body)

    def test_unconfigured_upstream_does_not_try_any_provider(self):
        with patch.dict(os.environ,{},clear=True),patch.object(self.proxy.urllib.request,'urlopen',side_effect=AssertionError('network forbidden')):
            server=core.ThreadingHTTPServer(('127.0.0.1',0),self.proxy.QuantumProxyHandler)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                client=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
                client.request('POST','/v1/chat/completions',json.dumps({'model':'synthetic','messages':[]}),{'Content-Type':'application/json','X-Upstream-URL':'https://untrusted.invalid'})
                response=client.getresponse();self.assertEqual(response.status,400);response.read();client.close()
            finally:server.shutdown();server.server_close();thread.join()

    def test_redirect_cannot_escape_explicit_upstream_or_forward_credentials(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        seen=[]
        class Sink(BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append(self.headers.get('Authorization'));self.send_response(200);self.end_headers();self.wfile.write(b'{}')
            def log_message(self,*_):pass
        sink=ThreadingHTTPServer(('127.0.0.1',0),Sink)
        class Redirect(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(302);self.send_header('Location',f'http://127.0.0.1:{sink.server_port}/sink');self.end_headers()
            def log_message(self,*_):pass
        origin=ThreadingHTTPServer(('127.0.0.1',0),Redirect)
        servers=[sink,origin];threads=[threading.Thread(target=s.serve_forever,daemon=True) for s in servers]
        for thread in threads:thread.start()
        try:
            request=self.proxy.urllib.request.Request(f'http://127.0.0.1:{origin.server_port}/',data=b'{}',headers={'Authorization':'Bearer synthetic-non-secret'})
            with self.assertRaises(urllib.error.HTTPError):self.proxy.open_upstream(request,timeout=2)
            self.assertEqual(seen,[])
        finally:
            for server in servers:server.shutdown();server.server_close()
            for thread in threads:thread.join()

    def test_saas_roundtrip_corrupt_packet_and_forged_payment(self):
        import httpx
        async def exercise():
            with patch.dict(os.environ,{},clear=True):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.payment.app),base_url='http://testserver') as client:
                    for source in ['', 'configuration = "function"\r\n'*30, 'an_extremely_long_identifier_0123456789_abcdefgh\n'*40]:
                        encoded=await client.post('/api/v1/compress',json={'text':source,'mode':'all'})
                        if source == '':
                            self.assertEqual(encoded.status_code,400)  # Existing HTTP input contract.
                            continue
                        self.assertEqual(encoded.status_code,200)
                        packet=encoded.json()
                        decoded=await client.post('/api/v1/decompress',json={'compressed_text':packet['compressed_text'],'symbol_table':packet['symbol_table']})
                        self.assertEqual(decoded.status_code,200)
                        self.assertEqual(decoded.json()['restored_text'],source)
                    corrupted=await client.post('/api/v1/decompress',json={'compressed_text':codec.PREFIX+'invalid\nraw','symbol_table':{}})
                    self.assertEqual(corrupted.status_code,400)
                    for tier,method in [('pro','stripe'),('team','crypto'),('enterprise','credits'),('starter','stripe')]:
                        response=await client.post('/api/v1/billing/checkout',json={'tier':tier,'payment_method':method,'customer_email':'synthetic@example.invalid','payment_verified':True,'status':'paid'})
                        self.assertEqual(response.status_code,503)
                        self.assertNotIn('api_key',response.json())
        asyncio.run(exercise())

    def test_native_wrapper_does_not_rewrite_code_or_call_proxy(self):
        wrapper=core.load(core.Q/'quantum_cli_wrapper.py','edge_wrapper')
        source='Please note that configuration = "function"\r\n'
        with patch.object(wrapper,'is_proxy_alive',side_effect=AssertionError('must stay native')):
            self.assertEqual(wrapper.compress_text(source)[0],source)


if __name__=='__main__':unittest.main(verbosity=2)
