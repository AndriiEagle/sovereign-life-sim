"""Authenticated loopback app; no repository browsing or arbitrary commands."""
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
import argparse
import hmac
import json
import re
import secrets
import sys

ROOT=Path(__file__).resolve().parents[1]
for directory in ('simulation-core','ai-architect'):sys.path.insert(0,str(ROOT/directory))
from contracts import canonical, keys
from persistence import atomic_write
from runtime import Runtime

ALLOWED={'/engine-isometric-ui/index.html','/engine-isometric-ui/styles.css','/engine-isometric-ui/app.mjs',
 '/engine-isometric-ui/emberglass.mjs','/engine-isometric-ui/atlas.svg','/engine-isometric-ui/scenario-forms.mjs','/mcp-bridge/command-queue.mjs',
 '/engine-isometric-ui/reference-source/iso-kit-renderer.js','/simulation-core/model.mjs','/mcp-bridge/events.mjs'}


def allowed_path(raw):
    path=unquote(urlsplit(raw).path)
    if path in {'/','/engine-isometric-ui/'}:path='/engine-isometric-ui/index.html'
    return path if path in ALLOWED else None


class Handler(SimpleHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript','.js':'text/javascript','.svg':'image/svg+xml','.css':'text/css'}
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def setup(self):super().setup();self.connection.settimeout(5)
    def log_message(self,*args):pass
    def end_headers(self):
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; connect-src 'self'; img-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        super().end_headers()
    def valid_origin(self):
        host=f'127.0.0.1:{self.server.server_port}'
        return self.headers.get('Host')==host and self.headers.get('Origin') in {None,'http://'+host} and self.headers.get('Sec-Fetch-Site')!='cross-site'
    def authenticated(self,mutating=False):
        if hmac.compare_digest(self.headers.get('Authorization','').removeprefix('Bearer '),self.server.token):return True
        if mutating:return False
        try:
            cookie=SimpleCookie(self.headers.get('Cookie',''))
            return 'sovereign' in cookie and hmac.compare_digest(cookie['sovereign'].value,self.server.token)
        except Exception:return False
    def send_json(self,status,value,cookie=False):
        data=canonical(value).encode();self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)))
        if cookie:self.send_header('Set-Cookie',f'sovereign={self.server.token}; HttpOnly; SameSite=Strict; Path=/api')
        self.end_headers()
        if self.command!='HEAD':self.wfile.write(data)
    def do_HEAD(self):self.do_GET()
    def do_GET(self):
        if not self.valid_origin():self.send_json(403,{'error':'ORIGIN_OR_HOST_REJECTED'});return
        parsed=urlsplit(self.path);path=parsed.path
        if path=='/api/session':self.send_json(200,{'token':self.server.token},cookie=True);return
        if path.startswith('/api/'):
            if not self.authenticated():self.send_json(401,{'error':'AUTH_REQUIRED'});return
            if path=='/api/state':self.send_json(200,self.server.app.get());return
            if path=='/api/events':
                try:
                    after=int(parse_qs(parsed.query).get('after',['0'])[0])
                    if after<0:raise ValueError()
                except ValueError:self.send_json(400,{'error':'INVALID_EVENT_CURSOR'});return
                self.send_json(200,{'events':self.server.app.store.events(after)});return
            if path=='/api/mcp/stream':self.stream(parsed.query);return
            if re.fullmatch(r'/api/assets/[a-f0-9]{64}\.(svg|png|webp)',path):
                if not any(a['url']==path for a in self.server.app.store.get()['assets'].values()):self.send_error(404);return
                file=self.server.app.assets.directory/path.rsplit('/',1)[1]
                if not file.is_file():self.send_error(404);return
                data=file.read_bytes();extension=file.suffix[1:]
                self.send_response(200);self.send_header('Content-Type',{'svg':'image/svg+xml','png':'image/png','webp':'image/webp'}[extension])
                self.send_header('Content-Length',str(len(data)));self.end_headers()
                if self.command!='HEAD':self.wfile.write(data)
                return
            self.send_error(404);return
        static=allowed_path(self.path)
        if static is None:self.send_error(404);return
        self.path=static
        if self.command=='HEAD':super().do_HEAD()
        else:super().do_GET()
    def stream(self,query):
        try:
            after=int(self.headers.get('Last-Event-ID') or parse_qs(query).get('after',['0'])[0])
            if not 0<=after<=self.server.app.store.get()['revision']:raise ValueError()
        except ValueError:self.send_json(400,{'error':'INVALID_EVENT_CURSOR'});return
        self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Connection','close')
        self.end_headers();self.close_connection=True
        if self.command=='HEAD':return
        self.wfile.write(b': connected\nretry: 1000\n\n');self.wfile.flush()
        try:
            while not self.server.stopping:
                rows=self.server.app.store.events(after)
                for row in rows:
                    self.wfile.write(f'id: {row["seq"]}\nevent: state\ndata: {canonical(row)}\n\n'.encode());self.wfile.flush();after=row['seq']
                with self.server.app.store.changed:self.server.app.store.changed.wait(timeout=2)
                if not rows:self.wfile.write(b': heartbeat\n\n');self.wfile.flush()
        except (BrokenPipeError,ConnectionError,OSError):pass
    def do_POST(self):
        if not self.valid_origin():self.send_json(403,{'error':'ORIGIN_OR_HOST_REJECTED'});return
        if not self.authenticated(mutating=True):self.send_json(401,{'error':'AUTH_REQUIRED'});return
        rpc=False;rpc_id=None
        try:
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('JSON_REQUIRED')
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=65536:raise ValueError('INVALID_BODY_SIZE')
            body=json.loads(self.rfile.read(size),parse_constant=lambda _:(_ for _ in ()).throw(ValueError('NONFINITE_JSON')))
            path=urlsplit(self.path).path
            if path=='/api/mcp':
                rpc=True;keys(body,['jsonrpc','id','method','params'],['jsonrpc','id','method']);rpc_id=body['id']
                if body['jsonrpc']!='2.0' or type(rpc_id) not in (str,int):raise ValueError('INVALID_RPC')
                name=body['method'];params=keys(body.get('params',{}),['payload','request_id'])
                if name=='get_state':self.send_json(200,dict(jsonrpc='2.0',id=rpc_id,result=self.server.app.get()));return
                payload=params.get('payload',{});request_id=params.get('request_id');source='mcp'
            elif path=='/api/tick':
                name='tick';payload=dict(body);request_id=payload.pop('request_id',None);source='ui'
            elif path=='/api/command':
                keys(body,['command','payload','request_id'],['command','payload','request_id'])
                name=body['command'];payload=body['payload'];request_id=body['request_id'];source='ui'
            else:self.send_error(404);return
            if not isinstance(name,str):raise ValueError('INVALID_METHOD')
            result=self.server.app.execute(name,payload,request_id,source)
            response={'result':result,'state':self.server.app.get()}
            self.send_json(200,dict(jsonrpc='2.0',id=rpc_id,result=response) if rpc else response)
        except (ValueError,TypeError,KeyError) as error:
            message=str(error) if isinstance(error,ValueError) else 'INVALID_REQUEST'
            self.send_json(400,dict(jsonrpc='2.0',id=rpc_id,error={'code':-32602,'message':message}) if rpc else {'error':message})
        except Exception:self.send_json(500,{'error':'INTERNAL_ERROR_NO_CHANGE_ACKNOWLEDGED'})


class SimulationServer(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,port=4530,directory=None):
        self.stopping=False;self.token=secrets.token_urlsafe(32)
        directory=Path(directory) if directory else ROOT/'.runtime/simulator'
        self.app=Runtime(ROOT,directory,
            generated=ROOT/'engine-isometric-ui/assets/generated' if directory==ROOT/'.runtime/simulator' else None,
            plugins=ROOT/'simulation-core/plugins/generated' if directory==ROOT/'.runtime/simulator' else None)
        try:
            super().__init__(('127.0.0.1',port),Handler)
            atomic_write(directory/'session.json',canonical({'url':f'http://127.0.0.1:{self.server_port}','token':self.token}).encode())
        except Exception:self.app.close();raise
    def server_close(self):
        self.stopping=True
        with self.app.store.changed:self.app.store.changed.notify_all()
        super().server_close();self.app.close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=4530);parser.add_argument('--state-dir',type=Path)
    args=parser.parse_args();server=SimulationServer(args.port,args.state_dir)
    print(f'SYNTHETIC local simulator: http://127.0.0.1:{server.server_port}/',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()
