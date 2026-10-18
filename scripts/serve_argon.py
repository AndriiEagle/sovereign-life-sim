"""Loopback-only Argon adventure. No model, payment, or shell execution routes."""
import argparse
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
from pathlib import Path
import secrets
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'argon-game'))
from game import Game

STATIC = {'/':'index.html', '/app.mjs':'app.mjs', '/client.mjs':'client.mjs', '/styles.css':'styles.css'}
ART_NAMES = {'sky.png':'L0_zurich_twilight_sky.png', 'station.png':'L1_stadelhofen_calatrava_arches.png',
             'train.png':'L2_swiss_sbb_train_parallax.png'}


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_): pass

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; connect-src 'self'; img-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        super().end_headers()

    def valid_origin(self):
        host = f'127.0.0.1:{self.server.server_port}'
        return self.headers.get('Host') == host and self.headers.get('Origin') in {None,'http://'+host} and self.headers.get('Sec-Fetch-Site') != 'cross-site'

    def authenticated(self):
        return hmac.compare_digest(self.headers.get('Authorization','').removeprefix('Bearer '), self.server.token)

    def send_data(self, status, data, content_type='application/json; charset=utf-8', cookie=False):
        if not isinstance(data,bytes): data=json.dumps(data,ensure_ascii=False,allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(data)))
        if cookie: self.send_header('Set-Cookie',f'argon={self.server.token}; HttpOnly; SameSite=Strict; Path=/api')
        self.end_headers()
        if self.command != 'HEAD': self.wfile.write(data)

    def do_HEAD(self): self.do_GET()

    def do_GET(self):
        if not self.valid_origin(): self.send_data(403,{'error':'ORIGIN_REJECTED'}); return
        path=urlsplit(self.path).path
        if path == '/api/session': self.send_data(200,{'token':self.server.token},cookie=True); return
        if path == '/api/state':
            cookie=SimpleCookie()
            try: cookie.load(self.headers.get('Cookie',''))
            except Exception: pass
            valid_cookie = 'argon' in cookie and hmac.compare_digest(cookie['argon'].value,self.server.token)
            if not self.authenticated() and not valid_cookie: self.send_data(401,{'error':'AUTH_REQUIRED'}); return
            with self.server.game.store.lock: self.send_data(200,self.server.game.view())
            return
        if path in STATIC:
            file=ROOT/'argon-game'/STATIC[path]
            self.send_data(200,file.read_bytes(),{'.html':'text/html; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}[file.suffix]); return
        if path=='/mcp-bridge/command-queue.mjs':
            self.send_data(200,(ROOT/'mcp-bridge/command-queue.mjs').read_bytes(),'text/javascript; charset=utf-8'); return
        if path.startswith('/art/') and path[5:] in ART_NAMES and self.server.art_dir:
            file=self.server.art_dir/ART_NAMES[path[5:]]
            if file.is_file(): self.send_data(200,file.read_bytes(),'image/png'); return
        self.send_data(404,{'error':'NOT_FOUND'})

    def do_POST(self):
        if not self.valid_origin(): self.send_data(403,{'error':'ORIGIN_REJECTED'}); return
        if not self.authenticated(): self.send_data(401,{'error':'AUTH_REQUIRED'}); return
        if self.path != '/api/action': self.send_data(404,{'error':'NOT_FOUND'}); return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 8192 or self.headers.get('Content-Type','').split(';')[0] != 'application/json': raise ValueError('JSON_REQUIRED')
            body=json.loads(self.rfile.read(length))
            if not isinstance(body,dict) or set(body) not in ({'action','payload','request_id'}, {'action','payload','request_id','expected_revision'}): raise ValueError('INVALID_REQUEST')
            with self.server.game.store.lock:
                result=self.server.game.command(body['action'],body['payload'],body['request_id'],body.get('expected_revision'))
                self.send_data(200,{'result':result,**self.server.game.view()})
        except (ValueError,TypeError,KeyError) as error:
            if str(error)=='REVISION_CONFLICT':
                with self.server.game.store.lock: self.send_data(409,{'error':'REVISION_CONFLICT',**self.server.game.view()})
            else:self.send_data(400,{'error':str(error)})
        except OSError: self.send_data(503,{'error':'Збереження недоступне. Дію не підтверджено.'})


class Server(ThreadingHTTPServer):
    daemon_threads=True

    def __init__(self,port=4532,directory=None,art_dir=None):
        self.token=secrets.token_urlsafe(32)
        self.art_dir=Path(art_dir).resolve() if art_dir else None
        self.game=Game(directory or ROOT/'.runtime/argon')
        try: super().__init__(('127.0.0.1',port),Handler)
        except Exception: self.game.close(); raise

    def server_close(self):
        super().server_close(); self.game.close()


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=4532)
    parser.add_argument('--state-dir',type=Path)
    parser.add_argument('--art-dir',type=Path)
    args=parser.parse_args()
    server=Server(args.port,args.state_dir,args.art_dir)
    print(f'Argon: http://127.0.0.1:{server.server_port}/',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
