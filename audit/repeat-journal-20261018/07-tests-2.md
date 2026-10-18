# Sovereign source reader: 07-tests, part 2

Derived reading aid; original file bytes and rights are authoritative. No functions or file sections have been omitted from the listed files. Cite `original/path:line` using the numbered column. Read at the exact review commit supplied in the user message.

## tests/test_journal_review.py

Original bytes: 5854; SHA256: `9c028b48bb2b9a5eec1a50f0fff5e135bdf618c45ef0117425534a200abdff6e`. Original source line numbers follow.

````text
    1 | """Additional disposable-state checks for the external journal audit.
    2 |
    3 | These exercise the public Runtime entry point and real filesystem/process effects.
    4 | They do not call providers, load personal state, or change the installed app.
    5 | """
    6 | from copy import deepcopy
    7 | import hashlib
    8 | import json
    9 | from pathlib import Path
   10 | import subprocess
   11 | import sys
   12 | import tempfile
   13 | import unittest
   14 |
   15 | ROOT = Path(__file__).resolve().parents[1]
   16 | for directory in ('simulation-core', 'ai-architect'):
   17 |     sys.path.insert(0, str(ROOT / directory))
   18 | from persistence import Store
   19 | from runtime import Runtime
   20 |
   21 |
   22 | def canonical_bytes(value):
   23 |     return json.dumps(value, ensure_ascii=False, sort_keys=True,
   24 |                       separators=(',', ':'), allow_nan=False).encode('utf-8')
   25 |
   26 |
   27 | class JournalReviewTests(unittest.TestCase):
   28 |     def make_committed_journal(self, directory):
   29 |         app = Runtime(ROOT, directory)
   30 |         try:
   31 |             app.execute('tick', {'hours': 1}, 'journal-review-0001')
   32 |             return app.get()
   33 |         finally:
   34 |             app.close()
   35 |
   36 |     def test_corrupt_complete_row_is_rejected_without_truncation(self):
   37 |         for damage in ('state_checksum', 'sequence', 'previous_hash', 'invalid_json_with_cr'):
   38 |             with self.subTest(damage=damage), tempfile.TemporaryDirectory() as temporary:
   39 |                 directory = Path(temporary)
   40 |                 self.make_committed_journal(directory)
   41 |                 path = directory / 'events.jsonl'
   42 |                 lines = path.read_bytes().splitlines(keepends=True)
   43 |                 row = json.loads(lines[-1])
   44 |                 if damage == 'state_checksum':
   45 |                     row['state']['life']['balance_cents'] += 1
   46 |                 elif damage == 'sequence':
   47 |                     row['seq'] += 1
   48 |                 elif damage == 'previous_hash':
   49 |                     row['previous'] = '1' * 64
   50 |                 if damage in ('sequence', 'previous_hash'):
   51 |                     unsigned = {key: value for key, value in row.items() if key != 'sha256'}
   52 |                     row['sha256'] = hashlib.sha256(canonical_bytes(unsigned)).hexdigest()
   53 |                 lines[-1] = canonical_bytes(row) + b'\n'
   54 |                 if damage == 'invalid_json_with_cr':
   55 |                     # Still a complete LF-terminated record, not an interrupted EOF tail.
   56 |                     lines[-1] = b'BROKEN\r' + lines[-1]
   57 |                 damaged = b''.join(lines)
   58 |                 path.write_bytes(damaged)
   59 |                 with self.assertRaises(ValueError):
   60 |                     unexpected = Runtime(ROOT, directory)
   61 |                     unexpected.close()
   62 |                 self.assertEqual(path.read_bytes(), damaged)
   63 |
   64 |     def test_interrupted_eof_tail_preserved_exactly_with_unicode_state(self):
   65 |         with tempfile.TemporaryDirectory() as temporary:
   66 |             directory = Path(temporary)
   67 |             expected = self.make_committed_journal(directory)
   68 |             path = directory / 'events.jsonl'
   69 |             committed = path.read_bytes()
   70 |             tail = '{"interrupted":"Україна'.encode('utf-8') + b'\xe2'
   71 |             path.write_bytes(committed + tail)
   72 |             (directory / 'state.json').write_bytes(b'not a snapshot')
   73 |             app = Runtime(ROOT, directory)
   74 |             try:
   75 |                 self.assertEqual(app.get(), expected)
   76 |                 self.assertEqual(path.read_bytes(), committed)
   77 |                 self.assertEqual([p.read_bytes() for p in directory.glob('interrupted-*.bin')], [tail])
   78 |             finally:
   79 |                 app.close()
   80 |
   81 |     def test_committed_crlf_records_recover_without_loss(self):
   82 |         with tempfile.TemporaryDirectory() as temporary:
   83 |             directory = Path(temporary)
   84 |             expected = self.make_committed_journal(directory)
   85 |             path = directory / 'events.jsonl'
   86 |             crlf = path.read_bytes().replace(b'\n', b'\r\n')
   87 |             path.write_bytes(crlf)
   88 |             app = Runtime(ROOT, directory)
   89 |             try:
   90 |                 self.assertEqual(app.get(), expected)
   91 |                 self.assertEqual(path.read_bytes(), crlf)
   92 |                 self.assertEqual(list(directory.glob('interrupted-*.bin')), [])
   93 |             finally:
   94 |                 app.close()
   95 |
   96 |     def test_real_process_lease_blocks_then_releases(self):
   97 |         with tempfile.TemporaryDirectory() as temporary:
   98 |             directory = Path(temporary)
   99 |             # Store's minimum actual commit contract includes sim_time.
  100 |             initial = {'sim_time': '2026-10-18T00:00:00Z', 'revision': 0}
  101 |             store = Store(directory, deepcopy(initial))
  102 |             child = (
  103 |                 'import json,sys; from pathlib import Path; '
  104 |                 'sys.path.insert(0,sys.argv[1]); from persistence import Store; '
  105 |                 '\ntry:\n s=Store(Path(sys.argv[2]),json.loads(sys.argv[3]))'
  106 |                 '\nexcept ValueError as e:\n print(str(e))'
  107 |                 '\nelse:\n s.close(); print("OPENED")\n'
  108 |             )
  109 |             command = [sys.executable, '-B', '-c', child, str(ROOT / 'simulation-core'),
  110 |                        str(directory), json.dumps(initial)]
  111 |             before = (directory / 'events.jsonl').read_bytes()
  112 |             try:
  113 |                 blocked = subprocess.run(command, capture_output=True, text=True, timeout=15)
  114 |                 self.assertEqual(blocked.returncode, 0, blocked.stderr)
  115 |                 self.assertEqual(blocked.stdout.strip(), 'STORE_ALREADY_IN_USE')
  116 |                 self.assertEqual((directory / 'events.jsonl').read_bytes(), before)
  117 |             finally:
  118 |                 store.close()
  119 |             opened = subprocess.run(command, capture_output=True, text=True, timeout=15)
  120 |             self.assertEqual(opened.returncode, 0, opened.stderr)
  121 |             self.assertEqual(opened.stdout.strip(), 'OPENED')
  122 |             self.assertEqual((directory / 'events.jsonl').read_bytes(), before)
  123 |
  124 |
  125 | if __name__ == '__main__':
  126 |     unittest.main(verbosity=2)
````

## tests/test_integrity.py

Original bytes: 2536; SHA256: `75b913e579e900c4a27c5ef93069cd5b2e74e4845faad4212dfe0aedc6dc1b2a`. Original source line numbers follow.

````text
    1 | from pathlib import Path
    2 | import hashlib
    3 | import importlib.util
    4 | import tempfile
    5 | import unittest
    6 |
    7 | spec = importlib.util.spec_from_file_location('package_verify', Path(__file__).resolve().parents[1] / 'scripts/verify.py')
    8 | verify = importlib.util.module_from_spec(spec)
    9 | spec.loader.exec_module(verify)
   10 |
   11 |
   12 | class SourceIntegrityTests(unittest.TestCase):
   13 |     def test_missing_package_manifest_cannot_be_accepted(self):
   14 |         with tempfile.TemporaryDirectory() as directory:
   15 |             root = Path(directory)
   16 |             for name in verify.REQUIRED:
   17 |                 if name == 'PACKAGE_MANIFEST.json':
   18 |                     continue
   19 |                 path = root / name
   20 |                 path.parent.mkdir(parents=True, exist_ok=True)
   21 |                 path.write_text('{}', encoding='utf-8')
   22 |             (root / 'audit/source-copies.json').write_text('{"copies":[]}', encoding='utf-8')
   23 |             (root / 'CONTEXT_MANIFEST.json').write_text('{"projects":[]}', encoding='utf-8')
   24 |             (root / 'USER_DIGITAL_TWIN_SEED.json').write_text('{"unknowns":{}}', encoding='utf-8')
   25 |             (root / 'automation-nodes/catalog.json').write_text('{"nodes":[]}', encoding='utf-8')
   26 |             (root / 'SYNERA_LAUNCH_CHECKLIST.md').write_text('\n'.join(f'{i}. **action**' for i in range(1, 6)), encoding='utf-8')
   27 |             with self.assertRaisesRegex(ValueError, 'MISSING_REQUIRED_FILE: PACKAGE_MANIFEST.json'):
   28 |                 verify.contract_checks(root)
   29 |
   30 |     def test_exact_copy_accepted_then_changed_copy_rejected(self):
   31 |         with tempfile.TemporaryDirectory() as directory:
   32 |             root = Path(directory)
   33 |             path = root / 'source.py'
   34 |             path.write_bytes(b'original')
   35 |             rows = [{'target': 'source.py', 'sha256': hashlib.sha256(b'original').hexdigest()}]
   36 |             verify.check_copies(root, rows)
   37 |             path.write_bytes(b'altered')
   38 |             with self.assertRaisesRegex(ValueError, 'SNAPSHOT_MISSING_OR_CHANGED'):
   39 |                 verify.check_copies(root, rows)
   40 |
   41 |     def test_foreign_path_and_missing_dependency_rejected(self):
   42 |         with tempfile.TemporaryDirectory() as directory:
   43 |             root = Path(directory)
   44 |             for name in ['../source.py', '/outside.py', 'C:/secret', '..\\secret']:
   45 |                 with self.subTest(path=name), self.assertRaises(ValueError):
   46 |                     verify.safe_target(root, name)
   47 |             with self.assertRaisesRegex(ValueError, 'SNAPSHOT_MISSING_OR_CHANGED'):
   48 |                 verify.check_copies(root, [{'target': 'missing.py', 'sha256': '0' * 64}])
````

## tests/test_server.py

Original bytes: 1331; SHA256: `0c5f8cf59cdfaac813e9afd9377991351bf7729f711721f110ef979e18fdc69b`. Original source line numbers follow.

````text
    1 | import importlib.util
    2 | from pathlib import Path
    3 | import unittest
    4 |
    5 | spec = importlib.util.spec_from_file_location('demo_server', Path(__file__).resolve().parents[1] / 'scripts/serve.py')
    6 | server = importlib.util.module_from_spec(spec)
    7 | spec.loader.exec_module(server)
    8 |
    9 |
   10 | class ServerPrivacyTests(unittest.TestCase):
   11 |     def test_entrypoint_is_demo(self):
   12 |         self.assertEqual(server.allowed_path('/'), '/engine-isometric-ui/index.html')
   13 |
   14 |     def test_only_the_reviewed_visual_asset_is_public(self):
   15 |         path = '/engine-isometric-ui/assets/visual/sovereign-island-v1.png'
   16 |         self.assertEqual(server.allowed_path(path), path)
   17 |         for private in ['/engine-isometric-ui/assets/visual/ART_DIRECTION.md',
   18 |                         '/engine-isometric-ui/assets/visual/../generated/private.png']:
   19 |             self.assertIsNone(server.allowed_path(private))
   20 |
   21 |     def test_private_paths_and_encoded_traversal_are_rejected(self):
   22 |         for path in ['/.git/config', '/USER_DIGITAL_TWIN_SEED.json', '/CONTEXT_MANIFEST.json',
   23 |                      '/audit/source-copies.json', '/engine-isometric-ui/../USER_DIGITAL_TWIN_SEED.json',
   24 |                      '/engine-isometric-ui/%2e%2e/USER_DIGITAL_TWIN_SEED.json', '/%252e%252e/.env']:
   25 |             with self.subTest(path=path):
   26 |                 self.assertIsNone(server.allowed_path(path))
````

## tests/scenario-forms.test.mjs

Original bytes: 3190; SHA256: `54f8a04eca95142cd79d75164898a7e39ebe60403dc3be7b4e19704b6e579afd`. Original source line numbers follow.

````text
    1 | import test from 'node:test';
    2 | import assert from 'node:assert/strict';
    3 | import fs from 'node:fs';
    4 | import vm from 'node:vm';
    5 | import {cents,expenseRule,towerParams} from '../engine-isometric-ui/scenario-forms.mjs';
    6 | import {createDurableQueue} from '../mcp-bridge/command-queue.mjs';
    7 |
    8 | test('UI expresses explicit synthetic modifiers and exact cents; plain expense infers none',()=>{
    9 |   assert.equal(cents('20.01'),2001);
   10 |   assert.deepEqual(towerParams('20',true),{setup_cents:2000,auto_deduct_setup:true});
   11 |   const input={id:'expense-test',title:'Implants',amount:'20'};
   12 |   assert.deepEqual(expenseRule(input).operations,[{op:'expense',amount_cents:2000,kpi_modifiers:{}}]);
   13 |   assert.deepEqual(expenseRule({...input,multiplier:'1.5',bio:'60'}).operations[0].kpi_modifiers,{revenue_multiplier:1.5,Bio_RAM:60});
   14 |   for(const value of ['','NaN','Infinity','-1','1000001','1.001'])assert.throws(()=>cents(value));
   15 |   for(const multiplier of ['5.01','-1','NaN'])assert.throws(()=>expenseRule({...input,multiplier}));
   16 | });
   17 |
   18 | test('simulator lost-ack retry after reload reuses one request and one expense',async()=>{
   19 |   const values=new Map(),storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};
   20 |   let debits=0,calls=0;const seen=new Set();
   21 |   const options={storage,key:'sovereign.pending.v1',uuid:()=> 'one-expense-id',
   22 |     acknowledged:(response,pending)=>response.result.request_id===pending.request_id,
   23 |     async send(request){
   24 |       if(!seen.has(request.request_id)){seen.add(request.request_id);debits++;}
   25 |       if(++calls<=2)throw new TypeError('lost ack');
   26 |       return {result:{event_id:2,request_id:request.request_id}};
   27 |     }};
   28 |   let queue=createDurableQueue(options);
   29 |   await assert.rejects(queue.execute('forge_rule',{rule:expenseRule({id:'one-rule',title:'Test',amount:'20'})},1));
   30 |   queue=createDurableQueue(options);
   31 |   await queue.retry();assert.equal(debits,1);assert(!queue.hasPending());
   32 | });
   33 |
   34 | test('actual simulator UI retries the durable command rather than creating a new request',async()=>{
   35 |   const source=fs.readFileSync(new URL('../engine-isometric-ui/app.mjs',import.meta.url),'utf8');
   36 |   const first=source.indexOf('async function act('),last=source.indexOf('\nasync function activateRule',first);
   37 |   assert(first>=0&&last>first);
   38 |   const values=new Map(),storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};
   39 |   let calls=0,debits=0;const seen=new Set();
   40 |   const commandQueue=createDurableQueue({storage,key:'sovereign.pending.v1',uuid:()=> 'one-stable-ui-id',
   41 |     acknowledged:(r,p)=>r.result.request_id===p.request_id,
   42 |     async send(request){
   43 |       if(!seen.has(request.request_id)){seen.add(request.request_id);debits++;}
   44 |       if(++calls<=2)throw new TypeError('lost ack');
   45 |       return {result:{request_id:request.request_id,event_id:3},state:{revision:3}};
   46 |     }});
   47 |   const context={commandBusy:false,commandQueue,state:{revision:1},render(){},$:()=>({hidden:false}),Error};
   48 |   vm.createContext(context);vm.runInContext(source.slice(first,last),context);
   49 |   await assert.rejects(context.act('tick',{steps:1}));
   50 |   await context.act(undefined,{},true);assert.equal(debits,1);
   51 | });
````

## tests/argon-client.test.mjs

Original bytes: 5018; SHA256: `e236f8edd2e49c82b26f90f06529791e551095ee736edb84c245326e7308e109`. Original source line numbers follow.

````text
    1 | import test from 'node:test';
    2 | import assert from 'node:assert/strict';
    3 | import fs from 'node:fs';
    4 | import vm from 'node:vm';
    5 | import {createCommandQueue,wasDemoShown} from '../argon-game/client.mjs';
    6 |
    7 | function storage(){const values=new Map();return {getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};}
    8 | function network(){let turns=0,calls=0;const seen=new Set();return {turns:()=>turns,async send(request){if(!seen.has(request.request_id)){seen.add(request.request_id);turns++;}calls++;if(calls<=2)throw new TypeError('Synthetic lost acknowledgment');return {state:{location:'stadelhofen',revision:turns},result:{accepted:true,request_id:request.request_id}};}};}
    9 |
   10 | test('two lost responses then a retry commit only one turn, even after reload',async()=>{
   11 |   const store=storage(),server=network();let ids=0;
   12 |   let queue=createCommandQueue({send:server.send,storage:store,uuid:()=>`synthetic-${++ids}`});
   13 |   await assert.rejects(queue.execute('catch_breath',{},0));
   14 |   assert(queue.hasPending());
   15 |   await assert.rejects(queue.execute('catch_breath',{},0));
   16 |   queue=createCommandQueue({send:server.send,storage:store,uuid:()=>`synthetic-${++ids}`});
   17 |   const response=await queue.retry();assert.equal(response.state.revision,1);
   18 |   assert.equal(server.turns(),1);assert.equal(ids,1);assert(!queue.hasPending());
   19 | });
   20 |
   21 | test('actual UI act entrypoint preserves the pending ID on a manual retry',async()=>{
   22 |   const file=process.env.ARGON_UI_TEST_SOURCE||new URL('../argon-game/app.mjs',import.meta.url);
   23 |   const source=fs.readFileSync(file,'utf8');const first=source.indexOf('async function act('),last=source.indexOf('\nfunction choose(',first);
   24 |   assert(first>=0&&last>first);
   25 |   const server=network(),store=storage();let ids=0;
   26 |   const queue=createCommandQueue({send:server.send,storage:store,uuid:()=>`synthetic-${++ids}`});
   27 |   const elements=new Map();const $=id=>{if(!elements.has(id))elements.set(id,{hidden:false,textContent:'',classList:{remove(){},add(){}},offsetWidth:0});return elements.get(id);};
   28 |   const context={busy:false,data:{state:{location:'stadelhofen',revision:0}},started:false,selected:null,hero:{},commandQueue:queue,$,
   29 |     api:(_path,request)=>server.send(request),render(){},showError(){},TypeError,crypto:{randomUUID:()=>`legacy-${++ids}`}};
   30 |   vm.createContext(context);vm.runInContext(source.slice(first,last),context);
   31 |   await context.act('catch_breath',{});await context.act(undefined,{},true);
   32 |   assert.equal(server.turns(),1,'A lost acknowledgment cannot cause a second committed turn');
   33 | });
   34 |
   35 | test('a definite rejection clears pending; an ambiguous success retains it',async()=>{
   36 |   const rejected=Object.assign(Error('revision changed'),{status:409,stateView:{state:{revision:2}}});
   37 |   const queue=createCommandQueue({send:async()=>{throw rejected;},storage:storage(),uuid:()=> 'synthetic'});
   38 |   await assert.rejects(queue.execute('catch_breath',{},0));assert(!queue.hasPending());
   39 |   const ambiguous=createCommandQueue({send:async()=>({result:{accepted:true,request_id:'wrong'}}),storage:storage(),uuid:()=> 'synthetic'});
   40 |   await assert.rejects(ambiguous.execute('catch_breath',{},0));assert(ambiguous.hasPending());
   41 |   const authentication=createCommandQueue({send:async()=>{throw Object.assign(Error('auth'),{status:401});},storage:storage(),uuid:()=> 'synthetic'});
   42 |   await assert.rejects(authentication.execute('catch_breath',{},0));assert(authentication.hasPending());
   43 | });
   44 |
   45 | test('honest postponement never claims a demo presentation',()=>{
   46 |   assert.equal(wasDemoShown({flags:['demo_tested'],ending:{id:'honest'}}),false);
   47 |   assert.equal(wasDemoShown({flags:['demo_tested'],ending:{id:'prepared'}}),true);
   48 |   assert.equal(wasDemoShown({flags:['demo_tested'],ending:{id:'late'}}),true);
   49 |   assert.equal(wasDemoShown({flags:[],ending:null}),false);
   50 | });
   51 |
   52 | test('actual UI checklist leaves the presentation incomplete after an honest ending',()=>{
   53 |   const file=process.env.ARGON_UI_TEST_SOURCE||new URL('../argon-game/app.mjs',import.meta.url);
   54 |   const source=fs.readFileSync(file,'utf8');const first=source.indexOf('function render(){'),last=source.indexOf('\nfunction restart(',first);
   55 |   assert(first>=0&&last>first);
   56 |   const elements=new Map();const element=()=>({children:[],className:'',replaceChildren(){this.children=[];},append(child){this.children.push(child);},setAttribute(){}});
   57 |   const $=id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id);};
   58 |   const context={$,
   59 |     document:{createElement:element},canvas:element(),data:{state:{sim_time:1160,location:'atelier',energy:70,cash_cents:1200,ending:{id:'honest'},flags:['demo_tested'],items:[],visited:['atelier'],log:[]},location:{title:'Atelier'},items:{}},
   60 |     locationNames:{},wasDemoShown,renderHotspots(){},renderInteraction(){},drawScene(){}};
   61 |   vm.createContext(context);vm.runInContext(source.slice(first,last),context);context.render();
   62 |   assert.notEqual($('tasks').children[2].className,'done','Postponement cannot be shown as a completed demo presentation');
   63 | });
````

## scripts/configure_mcp.py

Original bytes: 2347; SHA256: `2872eb3f0bf0e498a4ea694cfaff02f9e4301e997259a19a9bfc985d4516052f`. Original source line numbers follow.

````text
    1 | """Register only this checkout's local stdio adapter; never change user/account config."""
    2 | import argparse
    3 | import json
    4 | from pathlib import Path
    5 | import sys
    6 | import tomllib
    7 |
    8 | ROOT=Path(__file__).resolve().parents[1]
    9 | sys.path.insert(0,str(ROOT/'simulation-core'))
   10 | from persistence import atomic_write
   11 |
   12 |
   13 | def configuration(root,session_file=None):
   14 |     root=Path(root).resolve()
   15 |     interpreter=root/'.runtime/bridge-venv'/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
   16 |     if not interpreter.is_file():raise ValueError('BLOCKED_BRIDGE_ENV: create .runtime/bridge-venv and install requirements-bridge.txt')
   17 |     args=['-B',str(root/'scripts/mcp_server.py')]
   18 |     if session_file is not None:
   19 |         session_file=Path(session_file).resolve()
   20 |         if not session_file.is_relative_to(root/'.runtime'):raise ValueError('PROJECT_RUNTIME_SESSION_REQUIRED')
   21 |         if session_file!=root/'.runtime/simulator/session.json':args+=['--session-file',str(session_file)]
   22 |     return dict(command=str(interpreter),args=args,
   23 |                 cwd=str(root),startup_timeout_sec=30,enabled_tools=['get_state','command','probe_bridge'])
   24 |
   25 |
   26 | def register(root,session_file=None):
   27 |     root=Path(root).resolve();target=root/'.codex/config.toml';config=configuration(root,session_file)
   28 |     if not target.resolve().is_relative_to(root):raise ValueError('MCP_CONFIG_OUTSIDE_PROJECT')
   29 |     old=target.read_text(encoding='utf-8') if target.exists() else ''
   30 |     parsed=tomllib.loads(old)
   31 |     existing=parsed.get('mcp_servers',{}).get('sovereign_local')
   32 |     if existing is not None:
   33 |         if existing!=config:raise ValueError('MCP_CONFIG_CONFLICT: existing sovereign_local preserved')
   34 |         return 'UNCHANGED'
   35 |     section='\n[mcp_servers.sovereign_local]\n'+''.join(
   36 |         key+' = '+json.dumps(value,ensure_ascii=False)+'\n' for key,value in config.items())
   37 |     new=old.rstrip()+'\n'+section
   38 |     tomllib.loads(new)
   39 |     atomic_write(target,new.encode('utf-8'))
   40 |     return 'REGISTERED_PROJECT_ONLY'
   41 |
   42 |
   43 | if __name__=='__main__':
   44 |     parser=argparse.ArgumentParser();parser.add_argument('--session-file',type=Path)
   45 |     args=parser.parse_args()
   46 |     try:print(json.dumps(dict(status=register(ROOT,args.session_file),scope='this trusted project',provider_calls=0)))
   47 |     except (OSError,ValueError) as error:
   48 |         print(str(error),file=sys.stderr);raise SystemExit(2)
````

## scripts/verify.py

Original bytes: 6834; SHA256: `b254c7a91b10894f10405e952ab848e8bcdc2e99ad766e506cb2eb3a8c688e35`. Original source line numbers follow.

````text
    1 | """Portable source/contract acceptance, independent of Sol's original project paths."""
    2 | from pathlib import Path, PurePosixPath
    3 | import argparse
    4 | import hashlib
    5 | import importlib.util
    6 | import json
    7 | import re
    8 | import shutil
    9 | import subprocess
   10 | import sys
   11 | import time
   12 |
   13 | ROOT = Path(__file__).resolve().parents[1]
   14 | REQUIRED = ('PACKAGE_MANIFEST.json', 'audit/git-base.json', 'CONTEXT_MANIFEST.json', 'USER_DIGITAL_TWIN_SEED.json', 'SYNERA_LAUNCH_CHECKLIST.md',
   15 |             'TERRA_SUMMARY.uk.md', 'audit/step3-source-evidence.json', 'audit/step3-content-probe.json',
   16 |             'HANDOFF.md', 'TASKS.md', 'EXTERNAL_PROMPT.md', 'RIGHTS.md', 'audit/source-copies.json',
   17 |             'engine-isometric-ui/index.html', 'simulation-core/game-forge/sim/core.py',
   18 |             'simulation-core/revenue_lab/core.py', 'automation-nodes/catalog.json', 'mcp-bridge/events.mjs')
   19 |
   20 |
   21 | def sha(path):
   22 |     with path.open('rb') as handle:
   23 |         return hashlib.file_digest(handle, 'sha256').hexdigest()
   24 |
   25 |
   26 | def safe_target(root, relative):
   27 |     rel = PurePosixPath(relative)
   28 |     if not relative or '\\' in relative or ':' in relative or rel.is_absolute() or '..' in rel.parts:
   29 |         raise ValueError('UNSAFE_SNAPSHOT_PATH')
   30 |     path = (root / relative).resolve()
   31 |     if not path.is_relative_to(root.resolve()):
   32 |         raise ValueError('SNAPSHOT_OUTSIDE_ROOT')
   33 |     return path
   34 |
   35 |
   36 | def check_copies(root, rows):
   37 |     for row in rows:
   38 |         path = safe_target(root, row['target'])
   39 |         if not path.is_file() or sha(path) != row['sha256']:
   40 |             raise ValueError('SNAPSHOT_MISSING_OR_CHANGED: ' + row['target'])
   41 |
   42 |
   43 | def contract_checks(root):
   44 |     for name in REQUIRED:
   45 |         if not (root / name).is_file():
   46 |             raise ValueError('MISSING_REQUIRED_FILE: ' + name)
   47 |     copies = json.loads((root / 'audit/source-copies.json').read_text(encoding='utf-8'))['copies']
   48 |     check_copies(root, copies)
   49 |     manifest = json.loads((root / 'CONTEXT_MANIFEST.json').read_text(encoding='utf-8'))
   50 |     for project in manifest['projects']:
   51 |         if project['readiness_percent'] is not None:
   52 |             raise ValueError('UNSUPPORTED_READINESS_PERCENT')
   53 |     seed = json.loads((root / 'USER_DIGITAL_TWIN_SEED.json').read_text(encoding='utf-8'))
   54 |     if any(value is not None for value in seed['unknowns'].values()):
   55 |         raise ValueError('UNVERIFIED_PERSONAL_PARAMETER')
   56 |     catalog = json.loads((root / 'automation-nodes/catalog.json').read_text(encoding='utf-8'))
   57 |     if any(node['enabled'] or not node['dry_run'] or node['external_effects'] for node in catalog['nodes']):
   58 |         raise ValueError('EXTERNAL_NODE_ENABLED')
   59 |     checklist = (root / 'SYNERA_LAUNCH_CHECKLIST.md').read_text(encoding='utf-8')
   60 |     if len(re.findall(r'^\d\. \*\*', checklist, re.M)) != 5:
   61 |         raise ValueError('CHECKLIST_MUST_HAVE_FIVE_ACTIONS')
   62 |     lock = root / 'PACKAGE_MANIFEST.json'
   63 |     rows = json.loads(lock.read_text(encoding='utf-8'))['files']
   64 |     names = [row['path'] for row in rows]
   65 |     if len(names) != len(set(names)) or not set(REQUIRED[1:]).issubset(names):
   66 |         raise ValueError('PACKAGE_COVERAGE_MISSING_OR_DUPLICATED')
   67 |     for row in rows:
   68 |         path = safe_target(root, row['path'])
   69 |         if not path.is_file() or sha(path) != row['sha256']:
   70 |             raise ValueError('PACKAGE_CHANGED: ' + row['path'])
   71 |     return {'source_copies': len(copies), 'projects': len(manifest['projects']), 'seed_unknowns_preserved': True}
   72 |
   73 |
   74 | def run(command, cwd):
   75 |     start = time.monotonic()
   76 |     result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
   77 |     return {'command': command, 'cwd': str(cwd.relative_to(ROOT)), 'exit_code': result.returncode,
   78 |             'elapsed_seconds': round(time.monotonic() - start, 3),
   79 |             'summary': (result.stdout + result.stderr)[-1800:]}
   80 |
   81 |
   82 | def main():
   83 |     parser = argparse.ArgumentParser()
   84 |     parser.add_argument('--integrity-only', action='store_true')
   85 |     parser.add_argument('--report', type=Path)
   86 |     args = parser.parse_args()
   87 |     try:
   88 |         facts = contract_checks(ROOT)
   89 |     except (OSError, ValueError, KeyError) as error:
   90 |         print(json.dumps({'status': 'FAIL', 'error': str(error)}))
   91 |         return 1
   92 |     runs = []
   93 |     if not args.integrity_only:
   94 |         node = shutil.which('node')
   95 |         if not node:
   96 |             print(json.dumps({'status': 'HOLD', 'error': 'NODE_NOT_FOUND_IN_CHECKED_PATH'}))
   97 |             return 1
   98 |         commands = [
   99 |             ([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'upstream-tests', '-q'], ROOT / 'simulation-core'),
  100 |             ([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'sim/tests', '-t', '.', '-q'], ROOT / 'simulation-core/game-forge'),
  101 |             ([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-q'], ROOT),
  102 |             ([node, '--test', 'tests/model.test.mjs', 'tests/events.test.mjs', 'tests/iso-helpers.test.mjs', 'tests/emberglass.test.mjs', 'tests/argon-client.test.mjs', 'tests/scenario-forms.test.mjs'], ROOT),
  103 |             ([sys.executable, '-B', 'scripts/scenario.py', '--ticks', '96', '--action', 'rest', '--seed', '42'], ROOT),
  104 |         ]
  105 |         for command, cwd in commands:
  106 |             row = run(command, cwd)
  107 |             runs.append(row)
  108 |             print(json.dumps({'check': len(runs), 'exit_code': row['exit_code'], 'seconds': row['elapsed_seconds']}), flush=True)
  109 |             if row['exit_code']:
  110 |                 break
  111 |     success = all(row['exit_code'] == 0 for row in runs)
  112 |     sys.path.insert(0,str(ROOT/'ai-architect'))
  113 |     from sandbox import Sandbox
  114 |     sandbox=Sandbox(ROOT/'.runtime/simulator/sandbox.json').report() if not args.integrity_only else {'status':'NOT_RUN'}
  115 |     report = {'status': 'PASS' if success else 'FAIL', 'facts': facts, 'runs': runs,
  116 |               'phase2_status': 'BLOCKED_SANDBOX' if sandbox['status']!='READY' else 'LOCAL_CHECKS_PASS' if success else 'FAIL',
  117 |               'capabilities': {'python':sandbox,'paid_providers':'NOT_RUN','live_synera':'NOT_RUN',
  118 |                                'image_validator':'PRESENT' if importlib.util.find_spec('PIL') else 'BLOCKED_DEPENDENCY'},
  119 |               'boundary': 'Local component/source acceptance. Browser and official MCP SDK roundtrip have separate observed receipts. Python requires real isolation; no live Synera or paid-provider acceptance is implied.'}
  120 |     if args.report:
  121 |         target = safe_target(ROOT, args.report.as_posix())
  122 |         target.parent.mkdir(parents=True, exist_ok=True)
  123 |         target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
  124 |     print(json.dumps({'status': report['status'], **facts, 'commands': len(runs), 'phase2_status':report['phase2_status']}))
  125 |     if not success:
  126 |         print(runs[-1]['summary'])
  127 |     return int(not success)
  128 |
  129 |
  130 | if __name__ == '__main__':
  131 |     raise SystemExit(main())
````

## scripts/freeze.py

Original bytes: 1687; SHA256: `8a42efdf09da524faa5c4f4bd73550796eec42ff11ba9e9511dc7fb2b4934e38`. Original source line numbers follow.

````text
    1 | """Create a package integrity snapshot after review. This does not sign or accept it."""
    2 | from pathlib import Path
    3 | import hashlib
    4 | import json
    5 |
    6 | ROOT = Path(__file__).resolve().parents[1]
    7 |
    8 |
    9 | def included(path):
   10 |     relative = path.relative_to(ROOT)
   11 |     if relative.as_posix()=='.codex/config.toml':
   12 |         return False
   13 |     if any(part in {'.git', '__pycache__', '.runtime', '.venv', 'node_modules', 'screenshots', 'generated'} for part in relative.parts):
   14 |         return False
   15 |     if relative.name.startswith('.env') and relative.name != '.env.example':
   16 |         return False
   17 |     if relative.name in {'PACKAGE_MANIFEST.json', 'remote-readback.json', 'acceptance-local.json'}:
   18 |         return False
   19 |     return not (len(relative.parts) > 1 and relative.parts[0] == 'audit' and relative.parts[1].startswith('local-'))
   20 |
   21 |
   22 | def main():
   23 |     files = []
   24 |     for path in sorted(ROOT.rglob('*')):
   25 |         if path.is_file() and included(path):
   26 |             with path.open('rb') as handle:
   27 |                 digest = hashlib.file_digest(handle, 'sha256').hexdigest()
   28 |             files.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': digest, 'bytes': path.stat().st_size})
   29 |     target=ROOT/'PACKAGE_MANIFEST.json'
   30 |     newline='\r\n' if target.exists() and b'\r\n' in target.read_bytes() else '\n'
   31 |     with target.open('w',encoding='utf-8',newline=newline) as handle:
   32 |         handle.write(json.dumps({'schema': 'sovereign.package.v1',
   33 |             'boundary': 'SHA256 integrity only, not a signature or an acceptance verdict.', 'files': files}, indent=2) + '\n')
   34 |     print(json.dumps({'hashed_files': len(files), 'bytes': sum(row['bytes'] for row in files)}))
   35 |
   36 |
   37 | if __name__ == '__main__':
   38 |     main()
````
