# Sovereign source reader: 03-guards, part 1

Derived reading aid; original file bytes and rights are authoritative. No functions or file sections have been omitted from the listed files. Cite `original/path:line` using the numbered column. Read at the exact review commit supplied in the user message.

## ai-architect/ruleforge.py

Original bytes: 4843; SHA256: `62816e3f23ea260ae5ab7d0baaf44b15e9a60902ee03631342fe82d12928ca47`. Original source line numbers follow.

````text
    1 | """Natural-language templates and a validated, versioned plugin boundary."""
    2 | from copy import deepcopy
    3 | import hashlib
    4 | import json
    5 | import re
    6 |
    7 | from contracts import canonical, identifier, keys, number, text
    8 | from sandbox import check_source
    9 | from unified_tick import apply_operations
   10 |
   11 |
   12 | def validate_rule(rule):
   13 |     keys(rule,['schema','id','format','operations','source','assumptions','origin'],['schema','id','format','assumptions','origin'])
   14 |     if rule['schema']!='sovereign.rule.v1' or rule['format'] not in {'json','python'}: raise ValueError('RULE_SCHEMA_UNSUPPORTED')
   15 |     identifier(rule['id'])
   16 |     if rule['origin'] not in {'offline-template','llm','operator'}: raise ValueError('UNKNOWN_RULE_ORIGIN')
   17 |     if not isinstance(rule['assumptions'],list) or len(rule['assumptions'])>8: raise ValueError('INVALID_ASSUMPTIONS')
   18 |     for value in rule['assumptions']: text(value,300)
   19 |     if rule['format']=='python':
   20 |         if 'operations' in rule or 'source' not in rule: raise ValueError('INVALID_PYTHON_RULE')
   21 |         check_source(rule['source'])
   22 |     elif 'source' in rule or not isinstance(rule.get('operations'),list): raise ValueError('INVALID_JSON_RULE')
   23 |     canonical(rule)
   24 |     return dict(deepcopy(rule),sha256=hashlib.sha256(canonical(rule).encode()).hexdigest())
   25 |
   26 |
   27 | def compile_offline(prompt, format='json', template_params=None):
   28 |     prompt=text(prompt,2000)
   29 |     if format not in {'json','python'}: raise ValueError('UNKNOWN_RULE_FORMAT')
   30 |     lowered=prompt.casefold()
   31 |     id='rule-'+hashlib.sha256(prompt.encode()).hexdigest()[:16]
   32 |     assumptions=['Synthetic scenario; no actual income, diagnosis, or causal sales prediction.']
   33 |     params=keys(template_params if template_params is not None else {},['setup_cents','auto_deduct_setup'])
   34 |     if any(word in lowered for word in ('бот','bot','башт','tower')):
   35 |         operations=[dict(op='add_node',id='bot-'+id[5:],title='AI Bot / нова башта',kind='tower')]
   36 |         if params:
   37 |             auto=params.get('auto_deduct_setup',False)
   38 |             if type(auto) is not bool: raise ValueError('INVALID_BOOLEAN')
   39 |             operations[0].update(setup_cents=number(params.get('setup_cents',0),'SETUP',0,100000000,True),auto_deduct_setup=auto)
   40 |         assumptions+=['Revenue defaults to zero until explicit scenario parameters are supplied.']
   41 |     elif any(word in lowered for word in ('імплан','имплан','implant','стомат')):
   42 |         match=re.search(r'(\d{1,7}(?:[.,]\d{1,2})?)\s*(?:chf|франк)',lowered)
   43 |         if not match: raise ValueError('OFFLINE_TEMPLATE_NEEDS_EXPLICIT_CHF_AMOUNT')
   44 |         from decimal import Decimal
   45 |         amount=int(Decimal(match.group(1).replace(',','.'))*100)
   46 |         operations=[dict(op='expense',amount_cents=amount)]
   47 |         assumptions+=['Confidence and B2B uplift stay unchanged; compare explicit user-supplied hypotheses in parameters.']
   48 |     elif any(word in lowered for word in ('клієн','клиент','client','mirofish','npc')):
   49 |         operations=[dict(op='add_node',id='client-'+id[5:],title='Клієнт / сценарний агент',kind='agent')]
   50 |         assumptions+=['MiroFish-style local placeholder; upstream MiroFish is NOT_CONNECTED.']
   51 |     else:
   52 |         raise ValueError('OFFLINE_UNSUPPORTED: supported templates are bot tower, explicit CHF expense, and client agent')
   53 |     if params and operations[0]['op']!='add_node': raise ValueError('TOWER_TEMPLATE_PARAMS_REQUIRED')
   54 |     if params and operations[0].get('kind')!='tower': raise ValueError('TOWER_TEMPLATE_PARAMS_REQUIRED')
   55 |     rule=dict(schema='sovereign.rule.v1',id=id,format=format,assumptions=assumptions,origin='offline-template')
   56 |     if format=='python': rule['source']='def evaluate(state, params, seed):\n    return '+repr(operations)+'\n'
   57 |     else: rule['operations']=operations
   58 |     return validate_rule(rule)
   59 |
   60 |
   61 | def evaluate(rule, state, sandbox):
   62 |     operations=(sandbox.evaluate(rule['source'],dict(tick=state['life']['tick'],cash_cents=state['life']['balance_cents']),state['seed'])
   63 |                 if rule['format']=='python' else deepcopy(rule['operations']))
   64 |     apply_operations(state,operations,rule['id'],charge=rule['sha256'] not in state['rules'].get(rule['id'],{}).get('applied',[]))
   65 |     return operations
   66 |
   67 |
   68 | def stage(state, rule, sandbox):
   69 |     # Caller persists the accepted artifact before committing this candidate state.
   70 |     raw={k:v for k,v in rule.items() if k!='sha256'}
   71 |     verified=validate_rule(raw)
   72 |     if verified['sha256']!=rule.get('sha256'): raise ValueError('RULE_HASH_MISMATCH')
   73 |     evaluate(verified,state,sandbox)
   74 |     result=deepcopy(state)
   75 |     entry=result['rules'].setdefault(rule['id'],dict(active=None,pending=None,history=[],applied=[]))
   76 |     if entry['pending'] and entry['pending']['sha256']!=rule['sha256']: raise ValueError('RULE_ALREADY_PENDING')
   77 |     entry['pending']=verified
   78 |     return result
````

## ai-architect/assetforge.py

Original bytes: 3269; SHA256: `cc95c14d303fcc2665c0a3ee9704cb87f336dd969095cd59d923e79b3921d36e`. Original source line numbers follow.

````text
    1 | """Original, deterministic SVG sprites. AI replacements never remove the fallback."""
    2 | import hashlib
    3 | import html
    4 | import io
    5 | from pathlib import Path
    6 |
    7 | from contracts import canonical, identifier, number
    8 | from persistence import atomic_write
    9 |
   10 | STYLE='emberglass-sovereign-v1'
   11 |
   12 |
   13 | class AssetForge:
   14 |     def __init__(self,directory):
   15 |         self.directory=Path(directory)
   16 |
   17 |     def fallback(self,node,variant=0):
   18 |         identifier(node['id']); number(variant,'VARIANT',0,1000000,True)
   19 |         spec=dict(id=node['id'],kind=node['kind'],style=STYLE,size=[128,160],variant=variant)
   20 |         key=hashlib.sha256(canonical(spec).encode()).hexdigest()
   21 |         path=self.directory/(key+'.svg')
   22 |         if not path.is_file():
   23 |             palette=['#d3e7aa','#d4ad77','#87c2be','#b1a9dc']
   24 |             glow=palette[int(key[:8],16)%len(palette)]
   25 |             height=50 if node['kind']=='mine' else 88 if node['kind']=='tower' else 65
   26 |             top=120-height
   27 |             label=html.escape(node['title'][:1].upper())
   28 |             svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="128" height="160" viewBox="0 0 128 160">
   29 | <path d="M8 128 64 100 120 128 64 156Z" fill="#102321" opacity=".7"/>
   30 | <path d="M24 {top+16} 64 {top+36} 64 132 24 112Z" fill="#3f6159" stroke="#83a38b"/>
   31 | <path d="M64 {top+36} 104 {top+16} 104 112 64 132Z" fill="#233e39" stroke="#547d6a"/>
   32 | <path d="M24 {top+16} 64 {top-4} 104 {top+16} 64 {top+36}Z" fill="#78947a" stroke="{glow}"/>
   33 | <path d="M34 99 54 109 M75 109 94 99 M34 89 54 99 M75 99 94 89" stroke="{glow}" stroke-width="4"/>
   34 | <path d="M64 {top+16}V{max(4,top-20)}" stroke="{glow}" stroke-width="2"/>
   35 | <circle cx="64" cy="{max(4,top-20)}" r="4" fill="{glow}"/>
   36 | <text x="64" y="{top+64}" fill="{glow}" text-anchor="middle" font-size="14" font-family="sans-serif">{label}</text></svg>'''
   37 |             atomic_write(path,svg.encode('utf-8'))
   38 |         data=path.read_bytes()
   39 |         return dict(key=key,sha256=hashlib.sha256(data).hexdigest(),format='svg',origin='offline-template',
   40 |                     style=STYLE,variant=variant,status='READY',url='/api/assets/'+key+'.svg')
   41 |
   42 |     def accept_image(self,node,data,variant=0):
   43 |         if len(data)>8*1024*1024: raise ValueError('IMAGE_TOO_LARGE')
   44 |         from PIL import Image
   45 |         with Image.open(io.BytesIO(data)) as image:
   46 |             if image.format not in {'PNG','WEBP'} or not (32<=image.width<=2048 and 32<=image.height<=2048):
   47 |                 raise ValueError('UNSUPPORTED_IMAGE')
   48 |             image.load()
   49 |             if 'A' not in image.getbands() or image.getextrema()[image.getbands().index('A')][0]==255:
   50 |                 raise ValueError('TRANSPARENT_SPRITE_REQUIRED')
   51 |             ext='png' if image.format=='PNG' else 'webp'
   52 |         checksum=hashlib.sha256(data).hexdigest()
   53 |         atomic_write(self.directory/(checksum+'.'+ext),data)
   54 |         return dict(key=checksum,sha256=checksum,format=ext,origin='ai-provider',style=STYLE,
   55 |                     variant=variant,status='READY',url='/api/assets/'+checksum+'.'+ext)
   56 |
   57 |     def prompt(self,node):
   58 |         return f'Original {node["kind"]} sprite for {node["title"]}. Dark sci-fi Emberglass RTS isometric style, 2:1 isometry, muted green metal, warm emissive details, single centered object, transparent background, no text, no logos, no copied game art.'
````

## ai-architect/sandbox.py

Original bytes: 7198; SHA256: `e56a48eaab19d8485bbc45e4a329ccf5e98c5e5778491c1ecaaba0f6c1398493`. Original source line numbers follow.

````text
    1 | """Generated Python runs only in a rootless, resource-checked OCI container."""
    2 | import ast
    3 | import json
    4 | from pathlib import Path
    5 | import re
    6 | import shutil
    7 | import subprocess
    8 | import threading
    9 | import time
   10 | import uuid
   11 |
   12 |
   13 | def check_source(source):
   14 |     if not isinstance(source,str) or len(source)>16000: raise ValueError('INVALID_PYTHON_SIZE')
   15 |     try:tree=ast.parse(source)
   16 |     except SyntaxError:raise ValueError('PYTHON_SYNTAX_REJECTED') from None
   17 |     if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef) or tree.body[0].name!='evaluate':
   18 |         raise ValueError('EXPECTED_EVALUATE_FUNCTION')
   19 |     fn=tree.body[0]
   20 |     if [a.arg for a in fn.args.args]!=['state','params','seed'] or fn.decorator_list or fn.args.defaults or fn.args.kwarg or fn.args.vararg:
   21 |         raise ValueError('INVALID_EVALUATE_SIGNATURE')
   22 |     for item in ast.walk(tree):
   23 |         if isinstance(item,(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal,ast.ClassDef,ast.AsyncFunctionDef)):
   24 |             raise ValueError('PYTHON_POLICY_REJECTED')
   25 |         if isinstance(item,ast.Attribute) and item.attr.startswith('_'):
   26 |             raise ValueError('PYTHON_POLICY_REJECTED')
   27 |         if isinstance(item,ast.Name) and (item.id.startswith('__') or item.id in {'open','eval','exec','compile','getattr','setattr','globals','locals','input','breakpoint'}):
   28 |             raise ValueError('PYTHON_POLICY_REJECTED')
   29 |     return tree
   30 |
   31 |
   32 | RUNNER = r'''
   33 | import json, sys, os, pathlib, resource, math
   34 | cg=pathlib.Path('/sys/fs/cgroup')
   35 | memory=(cg/'memory.max').read_text().strip()
   36 | quota,period=(cg/'cpu.max').read_text().split()
   37 | status=pathlib.Path('/proc/self/status').read_text()
   38 | mounts=pathlib.Path('/proc/mounts').read_text().splitlines()
   39 | checks={
   40 |  'nonroot':os.getuid()==65534,
   41 |  'memory':memory!='max' and int(memory)<=268435456,
   42 |  'cpu':quota!='max' and int(quota)/int(period)<=.5,
   43 |  'network':set(os.listdir('/sys/class/net'))<=set(['lo']),
   44 |  'capabilities':any(line.startswith('CapEff:') and int(line.split()[1],16)==0 for line in status.splitlines()),
   45 |  'no_new_privileges':'NoNewPrivs:\t1' in status,
   46 |  'readonly_root':any(line.split()[1]=='/' and 'ro' in line.split()[3].split(',') for line in mounts),
   47 |  'no_gpu':not pathlib.Path('/dev/nvidia0').exists() and not pathlib.Path('/dev/dri').exists(),
   48 | }
   49 | if not all(checks.values()): raise RuntimeError('ISOLATION_NOT_ENFORCED')
   50 | os.environ.clear()
   51 | resource.setrlimit(resource.RLIMIT_CORE,(0,0))
   52 | resource.setrlimit(resource.RLIMIT_CPU,(4,4))
   53 | request=json.loads(sys.stdin.read(262145))
   54 | safe={k:__builtins__.__dict__[k] for k in ['abs','min','max','sum','range','len','enumerate','round','list','dict','int','float','str','bool','any','all','zip','sorted']}
   55 | scope={'__builtins__':safe,'math':math}
   56 | exec(compile(request['source'],'<isolated-rule>','exec'),scope)
   57 | ops=scope['evaluate'](request['state'],request.get('params',{}),request['seed'])
   58 | print(json.dumps({'operations':ops,'isolation':checks},allow_nan=False))
   59 | '''
   60 |
   61 |
   62 | class Sandbox:
   63 |     def __init__(self, config_path):
   64 |         self.status='BLOCKED_SANDBOX'; self.reason='Rootless OCI runtime and pinned image are required.'
   65 |         self.runtime=None; self.image=None
   66 |         path=Path(config_path)
   67 |         if not path.is_file(): return
   68 |         try:
   69 |             cfg=json.loads(path.read_text(encoding='utf-8'))
   70 |             if set(cfg)!={'runtime','image'} or cfg['runtime'] not in {'podman','docker'}: return
   71 |             self.runtime=shutil.which(cfg['runtime']); self.image=cfg['image']
   72 |             if not self.runtime or not re.fullmatch(r'[a-zA-Z0-9./_-]+@sha256:[a-f0-9]{64}',self.image): return
   73 |             p=subprocess.run([self.runtime,'info','--format','json' if cfg['runtime']=='podman' else '{{json .}}'],capture_output=True,timeout=4,text=True)
   74 |             info=json.loads(p.stdout)
   75 |             host=info.get('host',{})
   76 |             rootless=(host.get('security',{}).get('rootless') is True if cfg['runtime']=='podman'
   77 |                       else any('rootless' in item for item in info.get('SecurityOptions',[])))
   78 |             cgroup=host.get('cgroupVersion') if cfg['runtime']=='podman' else info.get('CgroupVersion')
   79 |             if not rootless or str(cgroup) not in {'2','v2'}: return
   80 |             self.status='PROBING'
   81 |             self.evaluate('def evaluate(state, params, seed):\n    return []\n',{},42)
   82 |             self.status='READY'; self.reason='Rootless OCI isolation and resource controls observed in a real worker.'
   83 |         except Exception:
   84 |             self.status='BLOCKED_SANDBOX'; self.reason='Runtime, pinned local image, or enforced isolation probe failed.'
   85 |
   86 |     def evaluate(self, source, state, seed):
   87 |         check_source(source)
   88 |         if self.status not in {'READY','PROBING'}: raise ValueError('BLOCKED_SANDBOX')
   89 |         name='sovereign-rule-'+uuid.uuid4().hex
   90 |         argv=[self.runtime,'run','--rm','--pull=never','--name',name,'--network=none','--read-only',
   91 |               '--cap-drop=ALL','--security-opt=no-new-privileges','--user=65534:65534',
   92 |               '--cpus=0.5','--memory=256m','--memory-swap=256m','--pids-limit=16',
   93 |               '--tmpfs=/tmp:rw,noexec,nosuid,size=8m','--workdir=/tmp','--entrypoint=python','-i',
   94 |               self.image,'-I','-S','-c',RUNNER]
   95 |         data=json.dumps(dict(source=source,state=state,params={},seed=seed),allow_nan=False).encode()
   96 |         if len(data)>262144: raise ValueError('SANDBOX_INPUT_TOO_LARGE')
   97 |         proc=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   98 |         buffers=[bytearray(),bytearray()]; overflow=threading.Event()
   99 |         def read(pipe, output):
  100 |             while True:
  101 |                 chunk=pipe.read(4096)
  102 |                 if not chunk: return
  103 |                 if len(output)+len(chunk)>65536: overflow.set(); return
  104 |                 output.extend(chunk)
  105 |         threads=[threading.Thread(target=read,args=(pipe,buffers[i]),daemon=True) for i,pipe in enumerate((proc.stdout,proc.stderr))]
  106 |         for t in threads:t.start()
  107 |         def write_input():
  108 |             try:proc.stdin.write(data);proc.stdin.close()
  109 |             except (BrokenPipeError,OSError,ValueError):pass
  110 |         writer=threading.Thread(target=write_input,daemon=True)
  111 |         try:
  112 |             writer.start()
  113 |             deadline=time.monotonic()+5
  114 |             while proc.poll() is None and not overflow.is_set() and time.monotonic()<deadline:
  115 |                 time.sleep(.02)
  116 |             if proc.poll() is None or overflow.is_set():
  117 |                 proc.kill()
  118 |                 raise ValueError('SANDBOX_TIMEOUT_OR_OUTPUT_LIMIT')
  119 |             for t in threads:t.join(timeout=.5)
  120 |             if proc.returncode or overflow.is_set(): raise ValueError('SANDBOX_RULE_FAILED')
  121 |             response=json.loads(buffers[0])
  122 |             if not response.get('isolation') or not all(response['isolation'].values()): raise ValueError('SANDBOX_ISOLATION_FAILED')
  123 |             return response['operations']
  124 |         finally:
  125 |             if proc.poll() is None: proc.kill()
  126 |             proc.wait(timeout=2)
  127 |             for pipe in (proc.stdout,proc.stderr):pipe.close()
  128 |             subprocess.run([self.runtime,'rm','--force',name],capture_output=True,timeout=3)
  129 |
  130 |     def report(self):
  131 |         return dict(status=self.status,reason=self.reason)
````

## ai-architect/providers.py

Original bytes: 5871; SHA256: `6fed93786dd76d148b93f1c28122f0d17c79deafc829963b1d6b69d52ed77938`. Original source line numbers follow.

````text
    1 | """Opt-in provider adapter. No approved policy means no external process or call."""
    2 | import base64
    3 | from datetime import datetime, timezone, date
    4 | from decimal import Decimal
    5 | import json
    6 | from pathlib import Path
    7 | import subprocess
    8 | import sys
    9 | import threading
   10 | import uuid
   11 |
   12 | from contracts import canonical, number, text
   13 | from persistence import atomic_write
   14 |
   15 |
   16 | class ProviderGateway:
   17 |     def __init__(self,root,directory):
   18 |         self.root=Path(root);self.directory=Path(directory);self.lock=threading.Lock()
   19 |         path=self.directory/'providers.json'
   20 |         self.policy=json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
   21 |         self.governor=Path(self.policy.get('governor',str(Path.home()/'Desktop/KI/andrey-os/gradual_ai_launcher.py')))
   22 |
   23 |     def check(self,kind):
   24 |         p=self.policy
   25 |         if p.get('enabled') is not True or p.get('allow_paid') is not True:raise ValueError('BLOCKED_PROVIDER_NO_APPROVED_BUDGET')
   26 |         if p.get('provider') not in {'openai','openrouter'} or kind not in {'rule','image'}:raise ValueError('BLOCKED_PROVIDER')
   27 |         if kind=='image' and p['provider']!='openai':raise ValueError('BLOCKED_IMAGE_ADAPTER')
   28 |         if not self.governor.is_file() or not (self.governor.parent/'harness/power_governor.py').is_file():raise ValueError('BLOCKED_GOVERNOR')
   29 |         for key in ('task_cap_usd','day_cap_usd','max_call_usd'):
   30 |             number(p.get(key),key,.000001,100)
   31 |         verified=date.fromisoformat(p.get('pricing_verified_on','1900-01-01'))
   32 |         if not 0<=(datetime.now(timezone.utc).date()-verified).days<=1:raise ValueError('BLOCKED_STALE_PRICING')
   33 |         text(p.get(kind+'_model'),120)
   34 |         number(p.get('max_output_tokens',1024),'MAX_OUTPUT_TOKENS',64,4096,True)
   35 |         for key in (('image_usd',) if kind=='image' else ('input_usd_per_million','output_usd_per_million')):
   36 |             number(p.get(key),key,0,10000)
   37 |
   38 |     def report(self):
   39 |         try:self.check('rule');status='CONFIGURED_NOT_LIVE_VERIFIED'
   40 |         except (ValueError,TypeError):status='OFFLINE'
   41 |         ledger=self._ledger()
   42 |         return dict(status=status,provider=self.policy.get('provider') if status!='OFFLINE' else None,
   43 |                     calls=sum(bool(r.get('attempted')) for r in ledger),
   44 |                     receipts_known_usd=str(sum(Decimal(str(r.get('reported_cost_usd') or 0)) for r in ledger)),
   45 |                     unknown_cost_calls=sum(bool(r.get('attempted')) and r.get('reported_cost_usd') is None for r in ledger))
   46 |
   47 |     def _ledger(self):
   48 |         path=self.directory/'provider-ledger.json'
   49 |         return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else []
   50 |
   51 |     def generate(self,kind,prompt,format='json'):
   52 |         self.check(kind);text(prompt,4000)
   53 |         if format not in {'json','python'}:raise ValueError('UNKNOWN_RULE_FORMAT')
   54 |         with self.lock:
   55 |             p=self.policy;now=datetime.now(timezone.utc);day=now.date().isoformat()
   56 |             ledger=self._ledger();cap=Decimal(str(p['max_call_usd']))
   57 |             used=sum(Decimal(str(r['reservation_usd'])) for r in ledger)
   58 |             daily=sum(Decimal(str(r['reservation_usd'])) for r in ledger if r['utc_day']==day)
   59 |             if used+cap>Decimal(str(p['task_cap_usd'])) or daily+cap>Decimal(str(p['day_cap_usd'])):raise ValueError('BLOCKED_BUDGET_CAP')
   60 |             # Conservative byte-based input bound, including protocol/schema overhead.
   61 |             estimate=(Decimal(str(p['image_usd'])) if kind=='image' else
   62 |                 Decimal(len(prompt.encode())+8192)*Decimal(str(p['input_usd_per_million']))/1000000+
   63 |                 Decimal(p.get('max_output_tokens',1024))*Decimal(str(p['output_usd_per_million']))/1000000)
   64 |             if estimate>cap:raise ValueError('BLOCKED_CALL_PRICE_BOUND')
   65 |             id=uuid.uuid4().hex;folder=self.directory/'provider-jobs'/id;folder.mkdir(parents=True)
   66 |             request=folder/'request.json';response=folder/'response.json'
   67 |             atomic_write(request,canonical(dict(kind=kind,prompt=prompt,format=format,provider=p['provider'],model=p[kind+'_model'],
   68 |                 max_output_tokens=p.get('max_output_tokens',1024),env_file=str(self.root/'.env'))).encode())
   69 |             row=dict(id=id,utc_day=day,kind=kind,reservation_usd=str(cap),attempted=None,status='RESERVED',reported_cost_usd=None)
   70 |             ledger.append(row);atomic_write(self.directory/'provider-ledger.json',canonical(ledger).encode())
   71 |             argv=[sys.executable,'-B',str(self.governor),'--governor','--report',str(folder/'governor.json'),'--',
   72 |                   sys.executable,'-I','-B',str(self.root/'ai-architect/provider_worker.py'),str(request),str(response)]
   73 |             try:
   74 |                 with (folder/'process.log').open('wb') as log:
   75 |                     process=subprocess.run(argv,cwd=folder,stdout=log,stderr=log,timeout=120)
   76 |                 if process.returncode or not response.is_file() or response.stat().st_size>12*1024*1024:raise ValueError('PROVIDER_WORKER_FAILED')
   77 |                 result=json.loads(response.read_text(encoding='utf-8'))
   78 |                 row.update(status=result['status'],attempted=result.get('attempted'),usage=result.get('usage'),
   79 |                            reported_cost_usd=result.get('usage',{}).get('cost'))
   80 |                 if result.get('attempted') is False:row['reservation_usd']='0'
   81 |                 atomic_write(self.directory/'provider-ledger.json',canonical(ledger).encode())
   82 |                 if result['status']!='PASS':raise ValueError('PROVIDER_REQUEST_FAILED')
   83 |                 return base64.b64decode(result['data'],validate=True) if kind=='image' else result['data']
   84 |             except Exception:
   85 |                 if row['status']=='RESERVED':
   86 |                     row.update(status='UNKNOWN_REQUIRES_RECONCILIATION',attempted=True)
   87 |                     atomic_write(self.directory/'provider-ledger.json',canonical(ledger).encode())
   88 |                 raise
````

## ai-architect/provider_worker.py

Original bytes: 3111; SHA256: `8b0605f49fa03053500f7f7b62dd7c0fa839f40f58b3cd921fffda3d8d99ec8d`. Original source line numbers follow.

````text
    1 | """Trusted bounded API worker; invoked ONLY by the governor adapter. No retries."""
    2 | import json
    3 | import os
    4 | from pathlib import Path
    5 | import sys
    6 | import urllib.request
    7 |
    8 |
    9 | def run(request):
   10 |     key_name='OPENAI_API_KEY' if request['provider']=='openai' else 'OPENROUTER_API_KEY'
   11 |     key=os.environ.get(key_name)
   12 |     env=Path(request['env_file'])
   13 |     if not key and env.is_file():
   14 |         for line in env.read_text(encoding='utf-8-sig').splitlines():
   15 |             name,separator,value=line.strip().partition('=')
   16 |             if separator and name==key_name:key=value.strip().strip('"').strip("'")
   17 |     if not key:return dict(status='BLOCKED_KEY',attempted=False,usage={})
   18 |     if request['kind']=='image':
   19 |         url='https://api.openai.com/v1/images/generations'
   20 |         body=dict(model=request['model'],prompt=request['prompt'],n=1,size='1024x1024',quality='low',background='transparent',output_format='png')
   21 |     else:
   22 |         url=('https://api.openai.com/v1/chat/completions' if request['provider']=='openai' else 'https://openrouter.ai/api/v1/chat/completions')
   23 |         instruction='Return only a JSON rule with schema="sovereign.rule.v1", id (lowercase safe ID), format="'+request['format']+'", origin="llm", assumptions (list). '
   24 |         instruction+='For json include operations: at most 8 add_node {op,id,title,kind:tower|mine|agent,revenue_day_cents,cost_day_cents,setup_cents}, expense {op,amount_cents}, or set_modifier {op,name:confidence_assumption|b2b_uplift_assumption,value:0..100}. '
   25 |         instruction+='For python include source defining only evaluate(state, params, seed), returning the same operations. No imports or external effects. All finances are synthetic, no invented actual revenue or health effects.'
   26 |         body=dict(model=request['model'],messages=[dict(role='system',content=instruction),dict(role='user',content=request['prompt'])],
   27 |                   max_tokens=request['max_output_tokens'],response_format={'type':'json_object'})
   28 |         if request['provider']=='openrouter':body['provider']={'allow_fallbacks':False}
   29 |     req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
   30 |     try:
   31 |         with urllib.request.urlopen(req,timeout=70) as response:
   32 |             data=response.read(12*1024*1024+1)
   33 |         if len(data)>12*1024*1024:raise ValueError('PROVIDER_RESPONSE_TOO_LARGE')
   34 |         result=json.loads(data)
   35 |         output=result['data'][0]['b64_json'] if request['kind']=='image' else json.loads(result['choices'][0]['message']['content'])
   36 |         return dict(status='PASS',attempted=True,data=output,usage=result.get('usage',{}))
   37 |     except Exception:return dict(status='PROVIDER_FAILED',attempted=True,usage={})
   38 |
   39 |
   40 | if __name__=='__main__':
   41 |     request=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
   42 |     result=run(request)
   43 |     target=Path(sys.argv[2]);temporary=target.with_suffix('.tmp')
   44 |     with temporary.open('wb') as handle:
   45 |         handle.write(json.dumps(result,allow_nan=False).encode());handle.flush();os.fsync(handle.fileno())
   46 |     os.replace(temporary,target)
````
