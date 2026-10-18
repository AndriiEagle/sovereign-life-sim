# Sovereign source reader: 05-transport-ui, part 1

Derived reading aid; original file bytes and rights are authoritative. No functions or file sections have been omitted from the listed files. Cite `original/path:line` using the numbered column. Read at the exact review commit supplied in the user message.

## scripts/serve.py

Original bytes: 9974; SHA256: `892c7cd48170365b6b9694eef79d8908aeea41660d201d5907ffd9ee4fa00eda`. Original source line numbers follow.

````text
    1 | """Authenticated loopback app; no repository browsing or arbitrary commands."""
    2 | from http.cookies import SimpleCookie
    3 | from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    4 | from pathlib import Path
    5 | from urllib.parse import parse_qs, unquote, urlsplit
    6 | import argparse
    7 | import hmac
    8 | import json
    9 | import re
   10 | import secrets
   11 | import sys
   12 |
   13 | ROOT=Path(__file__).resolve().parents[1]
   14 | for directory in ('simulation-core','ai-architect'):sys.path.insert(0,str(ROOT/directory))
   15 | from contracts import canonical, keys
   16 | from persistence import atomic_write
   17 | from runtime import Runtime
   18 |
   19 | ALLOWED={'/engine-isometric-ui/index.html','/engine-isometric-ui/styles.css','/engine-isometric-ui/app.mjs',
   20 |  '/engine-isometric-ui/emberglass.mjs','/engine-isometric-ui/atlas.svg','/engine-isometric-ui/scenario-forms.mjs','/mcp-bridge/command-queue.mjs',
   21 |  '/engine-isometric-ui/assets/visual/sovereign-island-v1.png',
   22 |  '/engine-isometric-ui/reference-source/iso-kit-renderer.js','/simulation-core/model.mjs','/mcp-bridge/events.mjs'}
   23 |
   24 |
   25 | def allowed_path(raw):
   26 |     path=unquote(urlsplit(raw).path)
   27 |     if path in {'/','/engine-isometric-ui/'}:path='/engine-isometric-ui/index.html'
   28 |     return path if path in ALLOWED else None
   29 |
   30 |
   31 | class Handler(SimpleHTTPRequestHandler):
   32 |     protocol_version='HTTP/1.1'
   33 |     extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript','.js':'text/javascript','.svg':'image/svg+xml','.css':'text/css'}
   34 |     def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
   35 |     def setup(self):super().setup();self.connection.settimeout(5)
   36 |     def log_message(self,*args):pass
   37 |     def end_headers(self):
   38 |         self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
   39 |         self.send_header('Referrer-Policy','no-referrer')
   40 |         self.send_header('Content-Security-Policy',"default-src 'self'; connect-src 'self'; img-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
   41 |         super().end_headers()
   42 |     def valid_origin(self):
   43 |         host=f'127.0.0.1:{self.server.server_port}'
   44 |         return self.headers.get('Host')==host and self.headers.get('Origin') in {None,'http://'+host} and self.headers.get('Sec-Fetch-Site')!='cross-site'
   45 |     def authenticated(self,mutating=False):
   46 |         if hmac.compare_digest(self.headers.get('Authorization','').removeprefix('Bearer '),self.server.token):return True
   47 |         if mutating:return False
   48 |         try:
   49 |             cookie=SimpleCookie(self.headers.get('Cookie',''))
   50 |             return 'sovereign' in cookie and hmac.compare_digest(cookie['sovereign'].value,self.server.token)
   51 |         except Exception:return False
   52 |     def send_json(self,status,value,cookie=False):
   53 |         data=canonical(value).encode();self.send_response(status)
   54 |         self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)))
   55 |         if cookie:self.send_header('Set-Cookie',f'sovereign={self.server.token}; HttpOnly; SameSite=Strict; Path=/api')
   56 |         self.end_headers()
   57 |         if self.command!='HEAD':self.wfile.write(data)
   58 |     def do_HEAD(self):self.do_GET()
   59 |     def do_GET(self):
   60 |         if not self.valid_origin():self.send_json(403,{'error':'ORIGIN_OR_HOST_REJECTED'});return
   61 |         parsed=urlsplit(self.path);path=parsed.path
   62 |         if path=='/api/session':self.send_json(200,{'token':self.server.token},cookie=True);return
   63 |         if path.startswith('/api/'):
   64 |             if not self.authenticated():self.send_json(401,{'error':'AUTH_REQUIRED'});return
   65 |             if path=='/api/state':self.send_json(200,self.server.app.get());return
   66 |             if path=='/api/events':
   67 |                 try:
   68 |                     after=int(parse_qs(parsed.query).get('after',['0'])[0])
   69 |                     if after<0:raise ValueError()
   70 |                 except ValueError:self.send_json(400,{'error':'INVALID_EVENT_CURSOR'});return
   71 |                 self.send_json(200,{'events':self.server.app.store.events(after)});return
   72 |             if path=='/api/mcp/stream':self.stream(parsed.query);return
   73 |             if re.fullmatch(r'/api/assets/[a-f0-9]{64}\.(svg|png|webp)',path):
   74 |                 if not any(a['url']==path for a in self.server.app.store.get()['assets'].values()):self.send_error(404);return
   75 |                 file=self.server.app.assets.directory/path.rsplit('/',1)[1]
   76 |                 if not file.is_file():self.send_error(404);return
   77 |                 data=file.read_bytes();extension=file.suffix[1:]
   78 |                 self.send_response(200);self.send_header('Content-Type',{'svg':'image/svg+xml','png':'image/png','webp':'image/webp'}[extension])
   79 |                 self.send_header('Content-Length',str(len(data)));self.end_headers()
   80 |                 if self.command!='HEAD':self.wfile.write(data)
   81 |                 return
   82 |             self.send_error(404);return
   83 |         static=allowed_path(self.path)
   84 |         if static is None:self.send_error(404);return
   85 |         self.path=static
   86 |         if self.command=='HEAD':super().do_HEAD()
   87 |         else:super().do_GET()
   88 |     def stream(self,query):
   89 |         try:
   90 |             after=int(self.headers.get('Last-Event-ID') or parse_qs(query).get('after',['0'])[0])
   91 |             if not 0<=after<=self.server.app.store.get()['revision']:raise ValueError()
   92 |         except ValueError:self.send_json(400,{'error':'INVALID_EVENT_CURSOR'});return
   93 |         self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Connection','close')
   94 |         self.end_headers();self.close_connection=True
   95 |         if self.command=='HEAD':return
   96 |         self.wfile.write(b': connected\nretry: 1000\n\n');self.wfile.flush()
   97 |         try:
   98 |             while not self.server.stopping:
   99 |                 rows=self.server.app.store.events(after)
  100 |                 for row in rows:
  101 |                     self.wfile.write(f'id: {row["seq"]}\nevent: state\ndata: {canonical(row)}\n\n'.encode());self.wfile.flush();after=row['seq']
  102 |                 with self.server.app.store.changed:self.server.app.store.changed.wait(timeout=2)
  103 |                 if not rows:self.wfile.write(b': heartbeat\n\n');self.wfile.flush()
  104 |         except (BrokenPipeError,ConnectionError,OSError):pass
  105 |     def do_POST(self):
  106 |         if not self.valid_origin():self.send_json(403,{'error':'ORIGIN_OR_HOST_REJECTED'});return
  107 |         if not self.authenticated(mutating=True):self.send_json(401,{'error':'AUTH_REQUIRED'});return
  108 |         rpc=False;rpc_id=None
  109 |         try:
  110 |             if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('JSON_REQUIRED')
  111 |             size=int(self.headers.get('Content-Length','0'))
  112 |             if not 0<size<=65536:raise ValueError('INVALID_BODY_SIZE')
  113 |             body=json.loads(self.rfile.read(size),parse_constant=lambda _:(_ for _ in ()).throw(ValueError('NONFINITE_JSON')))
  114 |             path=urlsplit(self.path).path
  115 |             if path=='/api/mcp':
  116 |                 rpc=True;keys(body,['jsonrpc','id','method','params'],['jsonrpc','id','method']);rpc_id=body['id']
  117 |                 if body['jsonrpc']!='2.0' or type(rpc_id) not in (str,int):raise ValueError('INVALID_RPC')
  118 |                 name=body['method'];params=keys(body.get('params',{}),['payload','request_id'])
  119 |                 if name=='get_state':self.send_json(200,dict(jsonrpc='2.0',id=rpc_id,result=self.server.app.get()));return
  120 |                 payload=params.get('payload',{});request_id=params.get('request_id');source='mcp'
  121 |             elif path=='/api/tick':
  122 |                 name='tick';payload=dict(body);request_id=payload.pop('request_id',None);source='ui'
  123 |             elif path=='/api/command':
  124 |                 keys(body,['command','payload','request_id'],['command','payload','request_id'])
  125 |                 name=body['command'];payload=body['payload'];request_id=body['request_id'];source='ui'
  126 |             else:self.send_error(404);return
  127 |             if not isinstance(name,str):raise ValueError('INVALID_METHOD')
  128 |             result=self.server.app.execute(name,payload,request_id,source)
  129 |             response={'result':result,'state':self.server.app.get()}
  130 |             self.send_json(200,dict(jsonrpc='2.0',id=rpc_id,result=response) if rpc else response)
  131 |         except (ValueError,TypeError,KeyError) as error:
  132 |             message=str(error) if isinstance(error,ValueError) else 'INVALID_REQUEST'
  133 |             self.send_json(400,dict(jsonrpc='2.0',id=rpc_id,error={'code':-32602,'message':message}) if rpc else {'error':message})
  134 |         except Exception:self.send_json(500,{'error':'INTERNAL_ERROR_NO_CHANGE_ACKNOWLEDGED'})
  135 |
  136 |
  137 | class SimulationServer(ThreadingHTTPServer):
  138 |     daemon_threads=True
  139 |     def __init__(self,port=4530,directory=None):
  140 |         self.stopping=False;self.token=secrets.token_urlsafe(32)
  141 |         directory=Path(directory) if directory else ROOT/'.runtime/simulator'
  142 |         self.app=Runtime(ROOT,directory,
  143 |             generated=ROOT/'engine-isometric-ui/assets/generated' if directory==ROOT/'.runtime/simulator' else None,
  144 |             plugins=ROOT/'simulation-core/plugins/generated' if directory==ROOT/'.runtime/simulator' else None)
  145 |         try:
  146 |             super().__init__(('127.0.0.1',port),Handler)
  147 |             atomic_write(directory/'session.json',canonical({'url':f'http://127.0.0.1:{self.server_port}','token':self.token}).encode())
  148 |         except Exception:self.app.close();raise
  149 |     def server_close(self):
  150 |         self.stopping=True
  151 |         with self.app.store.changed:self.app.store.changed.notify_all()
  152 |         super().server_close();self.app.close()
  153 |
  154 |
  155 | def main():
  156 |     parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=4530);parser.add_argument('--state-dir',type=Path)
  157 |     args=parser.parse_args();server=SimulationServer(args.port,args.state_dir)
  158 |     print(f'SYNTHETIC local simulator: http://127.0.0.1:{server.server_port}/',flush=True)
  159 |     try:server.serve_forever()
  160 |     except KeyboardInterrupt:pass
  161 |     finally:server.server_close()
  162 |
  163 | if __name__=='__main__':main()
````

## mcp-bridge/client.py

Original bytes: 3120; SHA256: `170832ae1c5ec95134e526a65a67bce3f919df0f4f411a527059c2a969173187`. Original source line numbers follow.

````text
    1 | """Authenticated loopback client. Session tokens never enter URLs or stdout."""
    2 | import json
    3 | from pathlib import Path
    4 | import threading
    5 | from urllib.parse import urlsplit
    6 | import urllib.request
    7 | import uuid
    8 |
    9 |
   10 | class LocalClient:
   11 |     def __init__(self,session_file):
   12 |         self.session_file=Path(session_file)
   13 |         self._connection_lock=threading.RLock()
   14 |         self._connected_session=None
   15 |         self._receipt=None
   16 |     def session(self):
   17 |         data=json.loads(self.session_file.read_text(encoding='utf-8'))
   18 |         parsed=urlsplit(data['url'])
   19 |         if parsed.scheme!='http' or parsed.hostname!='127.0.0.1' or not parsed.port or parsed.path or parsed.query or parsed.fragment or parsed.username:
   20 |             raise ValueError('LOOPBACK_SESSION_REQUIRED')
   21 |         return data
   22 |     def connect(self):
   23 |         """Confirm this adapter once per server token; restart requires a fresh SSE/ack."""
   24 |         with self._connection_lock:
   25 |             session=self.session()
   26 |             identity=(session['url'],session['token'])
   27 |             if self._connected_session!=identity:
   28 |                 receipt=self.probe()
   29 |                 if receipt['status']!='LIVE_LOCAL_BRIDGE':raise ValueError('ROUNDTRIP_NOT_CONFIRMED')
   30 |                 current=self.session()
   31 |                 if identity!=(current['url'],current['token']):raise ValueError('BRIDGE_SESSION_CHANGED_RETRY')
   32 |                 self._connected_session=identity;self._receipt=receipt
   33 |             return dict(self._receipt)
   34 |     def call(self,name,payload=None,request_id=None):
   35 |         session=self.session()
   36 |         body=dict(jsonrpc='2.0',id=uuid.uuid4().hex,method=name,params=dict(payload=payload or {},request_id=request_id or uuid.uuid4().hex))
   37 |         req=urllib.request.Request(session['url']+'/api/mcp',data=json.dumps(body).encode(),
   38 |             headers={'Authorization':'Bearer '+session['token'],'Content-Type':'application/json'},method='POST')
   39 |         with urllib.request.urlopen(req,timeout=15) as response:result=json.load(response)
   40 |         if 'error' in result:raise ValueError(result['error']['message'])
   41 |         return result['result']
   42 |     def probe(self):
   43 |         before=self.call('get_state')
   44 |         result=self.call('select_node',{'node_id':before['selected']})
   45 |         event_id=result['result']['event_id'];session=self.session()
   46 |         req=urllib.request.Request(session['url']+'/api/mcp/stream?after='+str(event_id-1),headers={'Authorization':'Bearer '+session['token']})
   47 |         observed=False
   48 |         with urllib.request.urlopen(req,timeout=6) as response:
   49 |             for _ in range(100):
   50 |                 line=response.readline(16384).decode()
   51 |                 if line.startswith('data: '):
   52 |                     event=json.loads(line[6:])
   53 |                     if event['seq']==event_id and event['source']=='mcp':observed=True;break
   54 |         if not observed:raise ValueError('SSE_ROUNDTRIP_NOT_OBSERVED')
   55 |         accepted=self.call('ack_event',{'event_id':event_id})
   56 |         return dict(status=accepted['state']['bridge']['status'],event_id=event_id,transport='MCP stdio → authenticated HTTP JSON-RPC → SSE → ack',providers='NOT_CONNECTED')
````

## mcp-bridge/command-queue.mjs

Original bytes: 1708; SHA256: `b7af5360a43411d774d048882a48c19df15438562faf98741b43efde2981f952`. Original source line numbers follow.

````text
    1 | // Durable request IDs shared by the simulator and Argon. Persist before sending.
    2 | export function createDurableQueue({send,storage,key,acknowledged,uuid=()=>crypto.randomUUID()}){
    3 |   let pending=null;
    4 |   const stored=storage.getItem(key);
    5 |   if(stored){
    6 |     try{
    7 |       const value=JSON.parse(stored);
    8 |       if(typeof value.action!=='string'||typeof value.payload!=='object'||value.payload===null||
    9 |          typeof value.request_id!=='string'||!Number.isInteger(value.expected_revision))throw Error();
   10 |       pending=value;
   11 |     }catch{storage.removeItem(key);}
   12 |   }
   13 |   function clear(){pending=null;try{storage.removeItem(key);}catch{/* A persisted ID remains safe to replay. */}}
   14 |   async function transmit(){
   15 |     if(!pending)throw Error('Немає непідтвердженої дії');
   16 |     let response;
   17 |     try{
   18 |       try{response=await send(pending);}catch(error){if(error instanceof TypeError)response=await send(pending);else throw error;}
   19 |     }catch(error){
   20 |       if(error.status===400||(error.status===409&&error.stateView?.state))clear();
   21 |       throw error;
   22 |     }
   23 |     if(!acknowledged(response,pending))throw Error('Підтвердження дії не отримано. Повтори підтвердження.');
   24 |     clear();return response;
   25 |   }
   26 |   return {
   27 |     hasPending:()=>pending!==null,
   28 |     async execute(action,payload,revision){
   29 |       if(pending)throw Error('Спершу повтори підтвердження попередньої дії.');
   30 |       const next={action,payload:JSON.parse(JSON.stringify(payload)),request_id:uuid(),expected_revision:revision};
   31 |       storage.setItem(key,JSON.stringify(next));pending=next;
   32 |       return transmit();
   33 |     },
   34 |     retry:()=>transmit()
   35 |   };
   36 | }
````

## engine-isometric-ui/app.mjs

Original bytes: 14171; SHA256: `10c6c5888d35d0fa540aa086114e6b3413c3d2d53746b6d82470dc782596c7b8`. Original source line numbers follow.

````text
    1 | import {createMap,titleFor,syncProjectButtons} from './emberglass.mjs';
    2 | import {cents,expenseRule,towerParams} from './scenario-forms.mjs';
    3 | import {createDurableQueue} from '../mcp-bridge/command-queue.mjs';
    4 | const $=id=>document.getElementById(id);let state,token,map,stream,reconnectTimer,busy=false;
    5 | let commandBusy=false;
    6 | const commandQueue=createDurableQueue({storage:sessionStorage,key:'sovereign.pending.v1',
    7 |   send:request=>api('/api/command',{command:request.action,payload:request.payload,request_id:request.request_id}),
    8 |   acknowledged:(response,pending)=>response?.result?.request_id===pending.request_id&&Number.isInteger(response.result.event_id)});
    9 | let messageTimer;const eventIds=new Set();
   10 | function notice(message){$('notice').textContent=message;$('notice').hidden=false;clearTimeout(messageTimer);messageTimer=setTimeout(()=>$('notice').hidden=true,6000);}
   11 | async function session(){const response=await fetch('/api/session');if(!response.ok)throw Error('LOCAL_SESSION_UNAVAILABLE');token=(await response.json()).token;}
   12 | async function api(path,body,retry=true){
   13 |   const response=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json','Authorization':'Bearer '+token}:{},body:body?JSON.stringify(body):undefined});
   14 |   if(response.status===401&&retry){await session();return api(path,body,false);}
   15 |   const data=await response.json();if(!response.ok)throw Object.assign(Error(data.error||'REQUEST_FAILED'),{status:response.status});return data;
   16 | }
   17 | async function act(command,payload={},retry=false){
   18 |   if(commandBusy)throw Error('Попередня дія ще виконується.');
   19 |   commandBusy=true;
   20 |   try{
   21 |     const data=await (retry?commandQueue.retry():commandQueue.execute(command,payload,state.revision));
   22 |     state=data.state;render();return data.result;
   23 |   }finally{commandBusy=false;$('retry-command').hidden=!commandQueue.hasPending();}
   24 | }
   25 | async function activateRule(payload){
   26 |   const result=await act('forge_rule',payload);
   27 |   if(result.status==='PENDING_TICK'){
   28 |     const activation=await act('tick',{steps:1,action:'rest'});
   29 |     if(activation.rule_errors?.[result.rule_id])throw Error(activation.rule_errors[result.rule_id]);
   30 |     if(state.rules[result.rule_id]?.active!==result.sha256)throw Error('RULE_NOT_ACTIVE');
   31 |   }
   32 |   return result;
   33 | }
   34 | function button(label,handler,className){const b=document.createElement('button');b.textContent=label;if(className)b.className=className;b.addEventListener('click',()=>Promise.resolve(handler()).catch(e=>notice(e.message)));return b;}
   35 | function theory(){
   36 |   const chart=$('theory-chart');chart.replaceChildren();$('theory-legend').replaceChildren();
   37 |   const colors=['#d6b783','#9fbe91','#91bec1'],names=['Рятівник','Tit-for-Tat','Вихід після порушення'];
   38 |   const values=state.game_theory.flatMap(s=>s.history.map(r=>r.cumulative[0]));const max=Math.max(1,...values),min=Math.min(0,...values);
   39 |   state.game_theory.forEach((s,i)=>{
   40 |     const points=s.history.map(r=>`${20+(r.round-1)/19*560},${140-(r.cumulative[0]-min)/(max-min)*120}`).join(' ');
   41 |     const path=document.createElementNS('http://www.w3.org/2000/svg','polyline');path.setAttribute('points',points);path.setAttribute('fill','none');path.setAttribute('stroke',colors[i]);path.setAttribute('stroke-width','3');chart.append(path);
   42 |     const dot=document.createElementNS('http://www.w3.org/2000/svg','circle');const last=points.split(' ').at(-1).split(',');dot.setAttribute('cx',last[0]);dot.setAttribute('cy',last[1]);dot.setAttribute('r','4');dot.setAttribute('fill',colors[i]);chart.append(dot);
   43 |     const span=document.createElement('span');span.style.borderColor=colors[i];span.textContent=`${names[i]}: ${s.cumulative[0]} · енергія −${s.energy[0]} · експл. ${(s.exploitation_rate[0]*100).toFixed(0)}% (${s.completed_rounds} р.)`;$('theory-legend').append(span);
   44 |   });
   45 | }
   46 | function render(){
   47 |   if(!state)return;map?.update(state);$('cash').textContent=`CHF ${(state.economy.cash_cents/100).toLocaleString('de-CH',{minimumFractionDigits:2,maximumFractionDigits:2})}`;
   48 |   $('day').textContent=`ДЕНЬ ${Math.floor(state.life.tick/96)+1}`;$('energy').textContent=`${state.bio.Bio_RAM.toFixed(1)} / 100`;$('energy-bar').style.width=state.bio.Bio_RAM+'%';
   49 |   $('sim-time').textContent=new Date(state.sim_time).toLocaleString('uk-UA',{timeZone:'Europe/Zurich'});$('revision').textContent=`REV ${state.revision} · SYNTHETIC`;
   50 |   $('runway').textContent=`Ігровий запас · runway ${state.economy.runway_days??'∞'} днів · фактичні гроші невідомі`;
   51 |   $('trust').textContent=state.economy.gilbert_trust_index.toFixed(1);$('trust').title=state.economy.trust_formula;
   52 |   $('quest').textContent=state.quest.hours_remaining===null?'Не активований':`${state.quest.hours_remaining.toFixed(2)} год`;$('activate-quest').disabled=state.quest.start_step!==null;
   53 |   $('gemeinde').textContent=state.economy.gemeinde_status==='UNCONFIGURED'?'Не налаштовано':`${state.economy.gemeinde_days_remaining} днів`;
   54 |   $('bridge-state').textContent=state.bridge.status;$('sandbox-status').textContent=`Python: ${state.capabilities.python.status}`;
   55 |   $('retry-command').hidden=!commandQueue.hasPending();
   56 |   $('scenario-multiplier').textContent=`Надходження ×${state.config.revenue_multiplier??1} · явне сценарне припущення`;
   57 |   $('use-provider').disabled=state.capabilities.provider.status!=='CONFIGURED_NOT_LIVE_VERIFIED';if($('use-provider').disabled)$('use-provider').checked=false;
   58 |   const focus=state.nodes.find(n=>n.id===state.selected);$('focus-name').textContent=focus?titleFor(focus):'Обери вузол';$('focus-status').textContent=focus?`ХВИЛЯ ${focus.wave} · ${focus.status}`:'—';
   59 |   $('focus-description').textContent=focus?`Наступний крок: ${focus.status==='Queued'?'дочекайся вільного слота у фокусі':focus.status==='FOCUSED'?'виділи годину на роботу або заверши етап':focus.status==='SHIPPED'?'задай припущення для cashflow':'переглянь параметри сценарію'}.`:'';
   60 |   $('focus-source-status').textContent=focus?.source_status||'Джерело не вказано';
   61 |   $('focus-progress').textContent=focus?`${focus.progress.toFixed(1)}%`:'—';
   62 |   $('focus-progress-bar').style.width=(focus?.progress||0)+'%';
   63 |   $('work').disabled=focus?.status!=='FOCUSED';$('ship').disabled=focus?.status!=='FOCUSED';$('cashflow').disabled=focus?.status!=='SHIPPED';
   64 |   const asset=focus&&state.assets[focus.id];if(asset){$('asset-preview').src=asset.url;$('asset-origin').textContent=`${asset.origin}\n${asset.status} · SHA ${asset.sha256.slice(0,10)}`;}
   65 |   $('node-economics').textContent=focus?`База CHF/день: +${focus.revenue_day_cents/100} / −${focus.cost_day_cents/100}. Старт списано: CHF ${(focus.setup_paid_cents??0)/100}. ROI після списання: ${state.economy.ROI[focus.id]??'базу не задано'}.`:'';
   66 |   if(focus&&document.activeElement?.tagName!=='INPUT'){
   67 |     for(const [id,key]of[['daily-income','revenue_day_cents'],['daily-cost','cost_day_cents'],['roi-base','setup_cents']])$(id).value=(focus[key]/100).toFixed(2);
   68 |     $('auto-deduct-setup').checked=focus.auto_deduct_setup??false;
   69 |   }
   70 |   $('node-count').textContent=`${state.nodes.length} вузлів · ${state.nodes.filter(n=>n.status==='FOCUSED').length}/2 у фокусі`;
   71 |   syncProjectButtons($('nodes'),state.nodes,state.selected,id=>act('select_node',{node_id:id}).catch(e=>notice(e.message)));
   72 |   $('rules').replaceChildren(...Object.values(state.rules).map(r=>{const div=document.createElement('div');div.textContent=`${r.id} · ${r.pending?'PENDING_TICK':r.active?'ACTIVE':'DISABLED'} · ${r.format||'—'}`;div.append(button('Відкотити',()=>act('rollback_rule',{rule_id:r.id})));return div;}));
   73 |   $('recovery').textContent=state.bio.debuff_active?`${state.bio.debuff_reason}: будівництво ×0.6 до тіку ${state.bio.debuff_until_step}. Одна дія: ${state.bio.recovery}.`:'Дебаф не активний. Параметри — добровільна самооцінка сценарію.';
   74 |   if(document.activeElement?.tagName!=='INPUT'){
   75 |     $('bio-ram').value=state.bio.Bio_RAM.toFixed(1);$('sleep-sync').value=state.bio.Sleep_Sync_Index.toFixed(1);$('weather').value=state.bio.Swiss_Grey_Weather_Modifier;$('reduced-fog').checked=state.bio.reduced_fog;
   76 |   }
   77 |   theory();
   78 | }
   79 | function record(event){if(eventIds.has(event.seq))return;eventIds.add(event.seq);const li=document.createElement('li');li.textContent=`#${event.seq} · ${event.type} · ${event.source}`;$('events').prepend(li);while($('events').children.length>10)$('events').lastChild.remove();}
   80 | function connect(){
   81 |   stream?.close();clearTimeout(reconnectTimer);stream=new EventSource('/api/mcp/stream?after='+state.revision);
   82 |   stream.onopen=()=>{$('connection').textContent='● ЛОКАЛЬНО · ЗБЕРЕЖЕНО';};
   83 |   stream.addEventListener('state',async e=>{record(JSON.parse(e.data));try{state=await api('/api/state');render();}catch(error){notice(error.message);}});
   84 |   stream.onerror=()=>{stream.close();$('connection').textContent='Відновлення зв’язку…';reconnectTimer=setTimeout(async()=>{try{await session();state=await api('/api/state');render();connect();}catch{connect();}},1500);};
   85 | }
   86 | for(const [id,name,payload]of[['work','tick',{hours:1,action:'work'}],['rest','tick',{hours:1,action:'rest'}],['next-day','tick',{days:1,action:'rest'}],['activate-quest','activate_quest',{}]])$(id).addEventListener('click',()=>act(name,payload).catch(e=>notice(e.message)));
   87 | for(const [id,status]of[['ship','SHIPPED'],['cashflow','ACTIVE_CASHFLOW']])$(id).addEventListener('click',()=>act('node_status',{node_id:state.selected,status}).catch(e=>notice(e.message)));
   88 | $('regenerate').addEventListener('click',()=>act('regenerate_asset',{node_id:state.selected,use_provider:$('use-provider').checked}).catch(e=>notice(e.message)));
   89 | $('economics-form').addEventListener('submit',async e=>{e.preventDefault();try{await act('configure_node',{node_id:state.selected,revenue_day_cents:cents($('daily-income').value),cost_day_cents:cents($('daily-cost').value),...towerParams($('roi-base').value,$('auto-deduct-setup').checked)});}catch(error){notice(error.message);}});
   90 | $('zoom-in').addEventListener('click',()=>map?.zoom(.1));$('zoom-out').addEventListener('click',()=>map?.zoom(-.1));
   91 | $('example-bot').addEventListener('click',()=>$('prompt').value='Додай нову башту доходу на базі нового бота');$('example-client').addEventListener('click',()=>$('prompt').value='Додай клієнта з агентною поведінкою в стилі MiroFish');
   92 | $('bio-form').addEventListener('submit',async e=>{e.preventDefault();try{const bio={Bio_RAM:Number($('bio-ram').value),Sleep_Sync_Index:Number($('sleep-sync').value),Swiss_Grey_Weather_Modifier:Number($('weather').value),reduced_fog:$('reduced-fog').checked};if($('debuff-hours').value!=='')bio.debuff_hours=Number($('debuff-hours').value);await act('update_params',{bio});}catch(error){notice(error.message);}});
   93 | $('architect-form').addEventListener('submit',async e=>{
   94 |   e.preventDefault();if(busy)return;busy=true;$('forge').disabled=true;
   95 |   try{
   96 |     const params=towerParams($('new-tower-setup').value,$('new-tower-deduct').checked);
   97 |     const payload={prompt:$('prompt').value,format:$('rule-format').value,use_provider:$('use-provider').checked};
   98 |     if(params.setup_cents||params.auto_deduct_setup)payload.template_params=params;
   99 |     const result=await activateRule(payload);
  100 |     $('architect-status').textContent=result.status==='QUEUED'?`Генерація: ${result.job_id}`:`Правило ${result.rule_id} перевірено.`;
  101 |     if(result.status==='PENDING_TICK')$('architect-status').textContent='Правило активовано. Вузол і візуал збережено.';
  102 |   }catch(error){$('architect-status').textContent=error.message;notice(error.message);}finally{busy=false;$('forge').disabled=false;}
  103 | });
  104 | $('expense-form').addEventListener('submit',async e=>{
  105 |   e.preventDefault();if(busy)return;busy=true;$('expense-submit').disabled=true;
  106 |   try{
  107 |     const rule=expenseRule({id:'expense-'+crypto.randomUUID(),title:$('expense-title').value,amount:$('expense-amount').value,multiplier:$('expense-multiplier').value,bio:$('expense-bio').value});
  108 |     await activateRule({rule});$('expense-status').textContent='Витрату й задані припущення застосовано та збережено.';
  109 |     $('expense-form').reset();
  110 |   }catch(error){$('expense-status').textContent=error.message;notice(error.message);}
  111 |   finally{busy=false;$('expense-submit').disabled=false;}
  112 | });
  113 | $('retry-command').addEventListener('click',async()=>{
  114 |   try{
  115 |     const result=await act(undefined,{},true);
  116 |     if(result.status==='PENDING_TICK'){
  117 |       const activation=await act('tick',{steps:1,action:'rest'});
  118 |       if(activation.rule_errors?.[result.rule_id])throw Error(activation.rule_errors[result.rule_id]);
  119 |     }
  120 |     $('expense-form').reset();notice('Дію підтверджено. Повторного списання немає.');
  121 |   }catch(error){notice(error.message);}
  122 | });
  123 | $('export').addEventListener('click',async()=>{try{const data=await api('/api/events');const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='sovereign-local-events.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){notice(error.message);}});
  124 | try{await session();state=await api('/api/state');try{map=await createMap($('map'),id=>act('select_node',{node_id:id}).catch(e=>notice(e.message)));}catch(error){$('renderer-state').textContent='Помилка рендерера';notice(error.message);}render();for(const event of (await api('/api/events')).events.slice(-10))record(event);connect();}catch(error){$('connection').textContent='Сервер недоступний';notice(error.message);}
````

## engine-isometric-ui/emberglass.mjs

Original bytes: 8938; SHA256: `ca777a16762b41106c0273e98921c4e803c55d40dd12686f305cb4f510749700`. Original source line numbers follow.

````text
    1 | // Adapter over the byte-preserved Emberglass renderer: owned atlas + live project DTOs.
    2 | const shortNames = {'game-forge':'Game Forge','brand-social-os':'Instagram','creator-income-os':'Creator OS','revenue-defense':'Revenue Defense','visual-voice-lab':'Voice Lab','agency-backlog':'Agency Lab','coiffeur-site':'Coiffeur','lego-godot':'LEGO / Godot','arcanum-card':'Card Forge','control-room':'Control Room','conductor':'Conductor','fiverr':'Fiverr / B2B','mirofish':'MiroFish','synera':'Synera','living-arcanum':'Living Arcanum','memento':'Memento'};
    3 | export const titleFor = node => shortNames[node.id] || node.title;
    4 | export const labelFor = node => titleFor(node).slice(0,22);
    5 | export function syncProjectButtons(container,nodes,selected,onSelect) {
    6 |   const existing=new Map([...container.children].map(b=>[b.dataset.nodeId,b]));
    7 |   for(const [index,n] of nodes.entries()){
    8 |     let b=existing.get(n.id);
    9 |     if(!b){
   10 |       b=container.ownerDocument.createElement('button');
   11 |       b.type='button';b.dataset.nodeId=n.id;
   12 |       b.append(container.ownerDocument.createTextNode(''),container.ownerDocument.createElement('span'));
   13 |       b.addEventListener('click',()=>onSelect(n.id));
   14 |     }
   15 |     b.className=`project ${n.status.toLowerCase()} ${n.id===selected?'selected':''}`;
   16 |     b.setAttribute('aria-pressed',String(n.id===selected));
   17 |     b.title=n.title;
   18 |     b.childNodes[0].nodeValue=labelFor(n);b.children[0].textContent=`W${n.wave} · ${n.status}`;
   19 |     // Leave existing elements in place: removing or re-appending them loses focus.
   20 |     if(container.children[index]!==b)container.insertBefore(b,container.children[index]||null);
   21 |     existing.delete(n.id);
   22 |   }
   23 |   for(const b of existing.values())b.remove();
   24 | }
   25 | export function positions(nodes) {
   26 |   const primary = Array.from({length:16},(_,i)=>({x:1+3*(i%4),y:1+3*Math.floor(i/4)}));
   27 |   const rest=[];
   28 |   for(let y=0;y<12;y++)for(let x=0;x<12;x++)if(!primary.some(p=>p.x===x&&p.y===y))rest.push({x,y});
   29 |   return nodes.map((n,i)=>({...n,...[...primary,...rest][i],z:0,zBias:0}));
   30 | }
   31 | export function viewportFor(width,zoom=1) {
   32 |   const height=Math.round(width*2/3);
   33 |   return {width,height,scale:width/2450*zoom,origin:{x:width/2,y:height*.205}};
   34 | }
   35 | export function pickProject(items,x,y,scale) {
   36 |   const front=[...items].reverse();
   37 |   return front.find(n=>n.labelBox&&x>=n.labelBox.x&&x<=n.labelBox.x+n.labelBox.w&&y>=n.labelBox.y&&y<=n.labelBox.y+n.labelBox.h)
   38 |     ||front.find(n=>Math.abs(x-n.screen.x)<60*scale&&y>n.screen.y-128*scale&&y<n.screen.y+25*scale);
   39 | }
   40 | export function layoutLabels(items,selected,hovered,scale,measure) {
   41 |   const priority=n=>(n.id===selected?4:0)+(n.id===hovered?2:0)+(n.status==='FOCUSED'?1:0);
   42 |   const labels=[];
   43 |   for(const n of [...items].sort((a,b)=>priority(b)-priority(a))){
   44 |     if(items.length>24&&n.id!==selected&&n.id!==hovered)continue;
   45 |     const w=Math.min(140,Math.max(78,measure(labelFor(n))+20)),h=scale<.33?27:30;
   46 |     const box={x:n.screen.x-w/2,y:n.screen.y+14*scale,w,h};
   47 |     if(labels.some(({box:b})=>box.x<b.x+b.w&&box.x+box.w>b.x&&box.y<b.y+b.h&&box.y+box.h>b.y))continue;
   48 |     labels.push({node:n,box});
   49 |   }
   50 |   return labels;
   51 | }
   52 | export async function createMap(canvas,onSelect) {
   53 |   const iso=window.EmberIsoKitRenderer;
   54 |   if(!iso)throw new Error('Emberglass renderer unavailable');
   55 |   const ids=['sovereign_tile','sovereign_mine','sovereign_tower','sovereign_agent'];
   56 |   await iso.init({kitVersion:'emberglass-iso-kit-v1',atlas:{file:'atlas.svg'},
   57 |     promotedAssets:ids.map(assetId=>({assetId,qaStatus:'promoted',artStatus:'original-owned-geometric',pivot:{x:64,y:assetId==='sovereign_tile'?96:128}})),
   58 |     runtimeAssets:ids.map((assetId,i)=>({assetId,frame:{x:i*128,y:0,w:128,h:160}}))},'/engine-isometric-ui');
   59 |   const ctx=canvas.getContext('2d');let state=null,view=null,items=[],zoom=1,hovered=null,mobileCentered=false;
   60 |   const backdrop=new Image();backdrop.onload=draw;backdrop.onerror=()=>draw();
   61 |   backdrop.src='/engine-isometric-ui/assets/visual/sovereign-island-v1.png';
   62 |   const images=new Map();
   63 |   function image(url) {
   64 |     if(!images.has(url)){
   65 |       const img=new Image();img.onload=draw;img.onerror=()=>{img.failed=true;draw();};img.src=url;images.set(url,img);
   66 |     }
   67 |     return images.get(url);
   68 |   }
   69 |   function draw(){
   70 |     if(!state)return;
   71 |     view=viewportFor(Math.max(320,Math.round(canvas.clientWidth||1100)),zoom);
   72 |     const {width,height,scale,origin}=view;
   73 |     const stage=canvas.parentElement;
   74 |     if(stage&&stage.clientWidth<width&&!mobileCentered){stage.scrollLeft=(width-stage.clientWidth)/2;mobileCentered=true;}
   75 |     else if(stage&&stage.clientWidth>=width)mobileCentered=false;
   76 |     const density=Math.max(1,Math.min(2,window.devicePixelRatio||1));
   77 |     canvas.width=Math.round(width*density);canvas.height=Math.round(height*density);
   78 |     ctx.setTransform(density,0,0,density,0,0);ctx.imageSmoothingEnabled=true;
   79 |     ctx.fillStyle='#122d32';ctx.fillRect(0,0,width,height);
   80 |     const hasArt=backdrop.complete&&backdrop.naturalWidth;
   81 |     canvas.dataset.artStatus=hasArt?'ready':'fallback';
   82 |     if(hasArt)ctx.drawImage(backdrop,0,0,width,height);
   83 |     // Reuse the frozen kit's world projection and sprite renderer. The active
   84 |     // adapter owns the art and grid; no archived renderer bytes are changed.
   85 |     for(let y=0;y<12;y++)for(let x=0;x<12;x++){
   86 |       const p=iso.worldToScreen(x,y,0,scale,origin);
   87 |       ctx.beginPath();ctx.moveTo(p.x,p.y-32*scale);ctx.lineTo(p.x+64*scale,p.y);
   88 |       ctx.lineTo(p.x,p.y+32*scale);ctx.lineTo(p.x-64*scale,p.y);ctx.closePath();
   89 |       if(!hasArt){ctx.fillStyle=(x+y)%2?'#304940':'#385247';ctx.fill();}
   90 |       ctx.strokeStyle=hasArt?'rgba(225,232,191,.09)':'rgba(195,218,177,.2)';ctx.lineWidth=.7;ctx.stroke();
   91 |     }
   92 |     items=positions(state.nodes).sort((a,b)=>a.x+a.y-b.x-b.y||a.id.localeCompare(b.id));
   93 |     for(const n of items){
   94 |       const point=iso.worldToScreen(n.x,n.y,0,scale,origin);
   95 |       const asset=state.assets[n.id];const img=asset&&image(asset.url);
   96 |       const selected=n.id===state.selected,focused=n.status==='FOCUSED',cashflow=n.status==='ACTIVE_CASHFLOW';
   97 |       ctx.fillStyle=selected?'rgba(249,217,149,.4)':focused?'rgba(218,237,156,.25)':cashflow?'rgba(121,200,193,.3)':'rgba(8,30,29,.3)';
   98 |       ctx.beginPath();ctx.ellipse(point.x,point.y+5*scale,60*scale,28*scale,0,0,Math.PI*2);ctx.fill();
   99 |       if(selected||focused||cashflow){
  100 |         ctx.strokeStyle=selected?'#f7dc9f':cashflow?'#79c8c1':'#d2e49f';ctx.lineWidth=selected?2:1;
  101 |         ctx.beginPath();ctx.ellipse(point.x,point.y+5*scale,60*scale,28*scale,0,0,Math.PI*2);ctx.stroke();
  102 |       }
  103 |       ctx.globalAlpha=n.status==='Queued'?.78:n.status==='DISABLED'?.35:1;
  104 |       if(img?.complete&&img.naturalWidth&&!img.failed)ctx.drawImage(img,point.x-64*scale,point.y-128*scale,128*scale,160*scale);
  105 |       else iso.drawAsset(ctx,'sovereign_'+(n.kind==='agent'?'agent':n.status==='Queued'?'mine':'tower'),point,scale,ctx.globalAlpha);
  106 |       ctx.globalAlpha=1;
  107 |       n.screen=point;
  108 |     }
  109 |     if(state.bio.fog){ctx.fillStyle=`rgba(13,24,23,${state.bio.fog})`;ctx.fillRect(0,0,width,height);}
  110 |     ctx.font='500 11px system-ui';
  111 |     for(const {node:n,box} of layoutLabels(items,state.selected,hovered,scale,text=>ctx.measureText(text).width)){
  112 |       const selected=n.id===state.selected,focused=n.status==='FOCUSED',cashflow=n.status==='ACTIVE_CASHFLOW',p=n.screen;
  113 |       ctx.font='500 11px system-ui';ctx.textAlign='center';
  114 |       n.labelBox=box;const {w,h}=box;
  115 |       ctx.fillStyle=selected?'rgba(21,42,35,.97)':'rgba(12,31,30,.87)';
  116 |       ctx.strokeStyle=selected?'#e5c58b':focused?'rgba(210,228,159,.65)':cashflow?'#79c8c1':'rgba(205,218,191,.17)';ctx.lineWidth=1;
  117 |       ctx.beginPath();ctx.roundRect(box.x,box.y,w,h,5);ctx.fill();ctx.stroke();
  118 |       ctx.fillStyle=selected?'#f5deae':'#e4ebd8';ctx.fillText(labelFor(n),p.x,box.y+13,w-12);
  119 |       ctx.font='9px system-ui';ctx.fillStyle=focused?'#d2e49f':cashflow?'#79c8c1':'#afc3b6';
  120 |       ctx.fillText(`W${n.wave} · ${n.status}`,p.x,box.y+23);
  121 |     }
  122 |   }
  123 |   function target(event){
  124 |     if(!view)return;const bounds=canvas.getBoundingClientRect();
  125 |     const x=(event.clientX-bounds.left)*view.width/bounds.width,y=(event.clientY-bounds.top)*view.height/bounds.height;
  126 |     const hit=pickProject(items,x,y,view.scale);
  127 |     const tile=iso.clickTarget(x,y,{heights:Array.from({length:12},()=>Array(12).fill(0))},view.scale,view.origin);
  128 |     return hit||items.find(n=>tile&&n.x===tile.x&&n.y===tile.y);
  129 |   }
  130 |   canvas.addEventListener('click',event=>{const n=target(event);if(n)onSelect(n.id);});
  131 |   canvas.addEventListener('pointermove',event=>{const node=target(event),id=node?.id||null;if(id!==hovered){hovered=id;canvas.style.cursor=id?'pointer':'default';canvas.title=node?labelFor(node):'';draw();}});
  132 |   canvas.addEventListener('pointerleave',()=>{hovered=null;canvas.style.cursor='default';canvas.title='';draw();});
  133 |   new ResizeObserver(draw).observe(canvas);
  134 |   return {update(next){state=next;draw();},zoom(delta){zoom=Math.max(.65,Math.min(1.4,zoom+delta));draw();}};
  135 | }
````

## engine-isometric-ui/scenario-forms.mjs

Original bytes: 1396; SHA256: `22aa5f049d9f5658004fa1e2cd7d7deeda14b80913c989fa293669f25b4f7a50`. Original source line numbers follow.

````text
    1 | function numeric(value,name,low,high){
    2 |   if(typeof value!=='string'||!value.trim())throw Error(`Потрібне значення: ${name}`);
    3 |   const result=Number(value);
    4 |   if(!Number.isFinite(result)||result<low||result>high)throw Error(`Недопустиме значення: ${name}`);
    5 |   return result;
    6 | }
    7 | export function cents(value){
    8 |   const amount=numeric(value,'CHF',0,1000000);
    9 |   if(Math.abs(amount*100-Math.round(amount*100))>.00001)throw Error('CHF: не більше двох знаків після коми');
   10 |   return Math.round(amount*100);
   11 | }
   12 | export function towerParams(setup,auto){
   13 |   if(typeof auto!=='boolean')throw Error('INVALID_BOOLEAN');
   14 |   return {setup_cents:cents(setup),auto_deduct_setup:auto};
   15 | }
   16 | export function expenseRule({id,title,amount,multiplier='',bio=''}){
   17 |   if(typeof title!=='string'||!title.trim()||title.length>160)throw Error('Вкажи назву витрати (до 160 символів)');
   18 |   const modifiers={};
   19 |   if(multiplier.trim())modifiers.revenue_multiplier=numeric(multiplier,'множник доходу',0,5);
   20 |   if(bio.trim())modifiers.Bio_RAM=numeric(bio,'Bio_RAM',0,100);
   21 |   return {schema:'sovereign.rule.v1',id,format:'json',origin:'operator',
   22 |     assumptions:['Synthetic scenario; operator-entered values are not a causal prediction.',title.trim()],
   23 |     operations:[{op:'expense',amount_cents:cents(amount),kpi_modifiers:modifiers}]};
   24 | }
````
