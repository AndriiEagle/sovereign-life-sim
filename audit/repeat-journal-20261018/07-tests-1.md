# Sovereign source reader: 07-tests, part 1

Derived reading aid; original file bytes and rights are authoritative. No functions or file sections have been omitted from the listed files. Cite `original/path:line` using the numbered column. Read at the exact review commit supplied in the user message.

## tests/test_phase2.py

Original bytes: 17607; SHA256: `b92324fa3cc6cfa49fe139e7f38383170147ace64054d32545c16ef427cd8f4f`. Original source line numbers follow.

````text
    1 | from concurrent.futures import ThreadPoolExecutor
    2 | from copy import deepcopy
    3 | import hashlib
    4 | from datetime import datetime,timezone
    5 | import importlib.util
    6 | import io
    7 | import json
    8 | from pathlib import Path
    9 | import sys
   10 | import tempfile
   11 | import threading
   12 | import unittest
   13 | from unittest.mock import patch
   14 | import urllib.error
   15 | import urllib.request
   16 |
   17 | ROOT=Path(__file__).resolve().parents[1]
   18 | for directory in ('simulation-core','ai-architect','mcp-bridge'):sys.path.insert(0,str(ROOT/directory))
   19 | from unified_tick import initial_state,advance,command,apply_operations
   20 | from game_theory_shield import simulate
   21 | from persistence import Store
   22 | from runtime import Runtime
   23 | from ruleforge import compile_offline,validate_rule
   24 | from sandbox import Sandbox,check_source
   25 | from assetforge import AssetForge
   26 | from providers import ProviderGateway
   27 | from client import LocalClient
   28 |
   29 | MANIFEST=json.loads((ROOT/'CONTEXT_MANIFEST.json').read_text(encoding='utf-8'))
   30 |
   31 | class CoreTests(unittest.TestCase):
   32 |     def setUp(self):self.state=initial_state(MANIFEST)
   33 |     def test_reproducible_partitioned_ticks_and_no_input_mutation(self):
   34 |         original=deepcopy(self.state);one=advance(self.state,96)
   35 |         split=self.state
   36 |         for _ in range(24):split=advance(split,4)
   37 |         self.assertEqual(one,split);self.assertEqual(self.state,original)
   38 |     def test_all_manifest_ids_and_queue_limit(self):
   39 |         self.assertEqual({n['id'] for n in self.state['nodes']},{p['id'] for p in MANIFEST['projects']})
   40 |         self.assertEqual([n['id'] for n in self.state['nodes'] if n['status']=='FOCUSED'],['synera','brand-social-os'])
   41 |         s=command(self.state,'node_status',{'node_id':'synera','status':'SHIPPED'})
   42 |         self.assertEqual(sum(n['status']=='FOCUSED' for n in s['nodes']),2)
   43 |         self.assertEqual(s,command(s,'node_status',{'node_id':'synera','status':'SHIPPED'}))
   44 |         with self.assertRaisesRegex(ValueError,'QUEUED'):command(s,'node_status',{'node_id':'mirofish','status':'SHIPPED'})
   45 |     def test_debuff_multiplier_does_not_compound_and_expires(self):
   46 |         s=command(self.state,'update_params',{'bio':{'debuff_hours':2}})
   47 |         self.assertEqual(advance(s,4)['bio']['build_multiplier'],.6)
   48 |         self.assertEqual(advance(s,8)['bio']['build_multiplier'],1)
   49 |     def test_self_report_triggers_model_debuff_but_clear_is_explicit(self):
   50 |         s=command(self.state,'update_params',{'bio':{'Sleep_Sync_Index':20}})
   51 |         self.assertTrue(s['bio']['debuff_active'])
   52 |         self.assertFalse(command(s,'update_params',{'bio':{'debuff_hours':0}})['bio']['debuff_active'])
   53 |     def test_quest_is_explicit_and_not_reset(self):
   54 |         self.assertIsNone(self.state['quest']['start_step'])
   55 |         s=advance(command(self.state,'activate_quest',{}),4)
   56 |         self.assertEqual(command(s,'activate_quest',{})['quest']['hours_remaining'],47)
   57 |         self.assertEqual(s['economy']['gemeinde_status'],'UNCONFIGURED')
   58 |     def test_conductor_drives_active_cashflow_in_integer_cents(self):
   59 |         s=command(self.state,'configure_node',dict(node_id='synera',revenue_day_cents=10000,cost_day_cents=2000,setup_cents=10000))
   60 |         s=command(s,'node_status',dict(node_id='synera',status='SHIPPED'))
   61 |         s=command(s,'node_status',dict(node_id='synera',status='ACTIVE_CASHFLOW'))
   62 |         s=advance(s,96)
   63 |         self.assertEqual(s['tower_net_cents'],8000)
   64 |         self.assertEqual(s['economy']['conductor_nodes']['synera']['contribution_after_reserve'],'80.00')
   65 |         self.assertEqual(s['economy']['ROI']['synera'],.8)
   66 |         self.assertIsNone(s['economy']['actual_cash_chf'])
   67 |     def test_operation_batch_rejects_partial_apply(self):
   68 |         before=deepcopy(self.state)
   69 |         with self.assertRaises(ValueError):apply_operations(self.state,[dict(op='add_node',id='new-node',title='New'),dict(op='shell',cmd='bad')],'rule-test')
   70 |         self.assertEqual(before,self.state)
   71 |     def test_strategy_math_includes_first_loss_and_exit_cost(self):
   72 |         rescuer=simulate();tft=simulate(left='Sovereign_TitForTat');exit=simulate(left='Sovereign_TitForTat',exit_on_breach=True)
   73 |         self.assertEqual(rescuer['cumulative'],[0,100]);self.assertEqual(tft['cumulative'],[19,24])
   74 |         self.assertEqual(tft['exploitation_rate'][0],.05);self.assertEqual(exit['completed_rounds'],1)
   75 |         self.assertEqual(exit['energy'][0],3);self.assertEqual(exit['cumulative'][0],0)
   76 |         self.assertEqual(simulate(right='Unconditional_Rescuer')['cumulative'],[60,60])
   77 |
   78 | class RuntimeTests(unittest.TestCase):
   79 |     def setUp(self):
   80 |         self.tmp=tempfile.TemporaryDirectory();self.directory=Path(self.tmp.name);self.app=Runtime(ROOT,self.directory)
   81 |     def tearDown(self):self.app.close();self.tmp.cleanup()
   82 |     def call(self,name,payload,id='request-0001'):return self.app.execute(name,payload,id)
   83 |     def test_concurrent_retry_applies_only_once(self):
   84 |         with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(lambda _:self.call('tick',{'hours':1}),range(16)))
   85 |         self.assertEqual(self.app.get()['life']['tick'],4)
   86 |         self.assertTrue(all(r==results[0] for r in results))
   87 |         with self.assertRaisesRegex(ValueError,'CONFLICT'):self.call('tick',{'hours':2})
   88 |     def test_restart_replays_state_and_idempotency(self):
   89 |         self.call('tick',{'hours':1});state=self.app.get();self.app.close();self.app=Runtime(ROOT,self.directory)
   90 |         self.assertEqual(self.app.get(),state);self.call('tick',{'hours':1});self.assertEqual(self.app.get(),state)
   91 |     def test_fsync_failure_never_acknowledges_or_updates_memory(self):
   92 |         before=self.app.get()
   93 |         with patch('persistence.os.fsync',side_effect=OSError('disk')):
   94 |             with self.assertRaises(OSError):self.call('tick',{'hours':1})
   95 |         self.assertEqual(self.app.get(),before)
   96 |         with self.assertRaises(OSError):self.call('tick',{'hours':1},'request-0002')
   97 |     def test_rule_stages_then_activates_and_recovers(self):
   98 |         r=self.call('forge_rule',{'prompt':'Додай башту нового бота'})
   99 |         self.assertEqual(r['status'],'PENDING_TICK');self.assertEqual(len(self.app.get()['nodes']),16)
  100 |         self.call('tick',{'steps':1},'activate-0001');s=self.app.get();self.assertEqual(len(s['nodes']),17)
  101 |         new=s['nodes'][-1];self.assertIn(new['id'],s['assets']);self.assertTrue(s['rules'][r['rule_id']]['active'])
  102 |         self.app.close();self.app=Runtime(ROOT,self.directory);self.assertEqual(self.app.get(),s)
  103 |     def test_rule_hash_and_manifest_node_overwrite_rejected(self):
  104 |         rule=compile_offline('Додай бота');rule['operations'][0]['id']='synera'
  105 |         with self.assertRaisesRegex(ValueError,'OWNED_ELSEWHERE'):
  106 |             self.call('forge_rule',{'rule':{k:v for k,v in rule.items() if k!='sha256'}})
  107 |     def test_python_missing_sandbox_is_blocked_without_execution(self):
  108 |         self.app.sandbox.status='BLOCKED_SANDBOX';before=self.app.get()
  109 |         with self.assertRaisesRegex(ValueError,'BLOCKED_SANDBOX'):self.call('forge_rule',{'prompt':'Додай бота','format':'python'})
  110 |         self.assertEqual(self.app.get(),before)
  111 |     def test_invalid_and_unsupported_requests_do_not_mutate(self):
  112 |         before=self.app.get()
  113 |         for payload in ({'prompt':'write a poem'},{'prompt':'bot','format':'shell'},{'rule':{'schema':'wrong'}}):
  114 |             with self.assertRaises(ValueError):self.call('forge_rule',payload)
  115 |         self.assertEqual(self.app.get(),before)
  116 |     def test_expense_once_and_rollback_does_not_refund(self):
  117 |         r=self.call('forge_rule',{'prompt':'Імпланти за 20 CHF'})
  118 |         self.call('tick',{'steps':1},'tick-one-0001');cash=self.app.get()['life']['balance_cents']
  119 |         self.call('tick',{'steps':1},'tick-two-0001');self.assertEqual(self.app.get()['life']['balance_cents'],cash)
  120 |         self.call('rollback_rule',{'rule_id':r['rule_id']},'rollback-0001');self.assertEqual(self.app.get()['life']['balance_cents'],cash)
  121 |     def test_provider_is_disabled_without_budget(self):
  122 |         with patch('providers.subprocess.run') as run:
  123 |             with self.assertRaisesRegex(ValueError,'BLOCKED_PROVIDER'):self.call('forge_rule',{'prompt':'bot','use_provider':True})
  124 |             run.assert_not_called()
  125 |     def test_asset_regeneration_and_cache(self):
  126 |         old=self.app.get()['assets']['synera'];same=self.app.assets.fallback(self.app.get()['nodes'][0])
  127 |         self.assertEqual(old,same)
  128 |         self.call('regenerate_asset',{'node_id':'synera'});new=self.app.get()['assets']['synera']
  129 |         self.assertNotEqual(old['sha256'],new['sha256']);self.assertEqual(new['origin'],'offline-template')
  130 |     def test_recovery_ignores_snapshot_and_preserves_interrupted_tail(self):
  131 |         self.call('tick',{'hours':1});self.app.close()
  132 |         (self.directory/'state.json').write_text('broken')
  133 |         with (self.directory/'events.jsonl').open('ab') as handle:handle.write(b'{incomplete')
  134 |         self.app=Runtime(ROOT,self.directory)
  135 |         self.assertEqual(self.app.get()['life']['tick'],4)
  136 |         self.assertTrue(list(self.directory.glob('interrupted-*.bin')))
  137 |     def test_conflicting_pending_expenses_do_not_block_clock(self):
  138 |         self.call('forge_rule',{'prompt':'Імпланти за 150 CHF'},'expense-first')
  139 |         self.call('forge_rule',{'prompt':'Стоматологія за 160 CHF'},'expense-second')
  140 |         result=self.call('tick',{'steps':1},'expense-activate')
  141 |         self.assertEqual(self.app.get()['life']['tick'],1)
  142 |         self.assertEqual(self.app.get()['life']['balance_cents'],5000)
  143 |         self.assertEqual(len(result['rule_errors']),1)
  144 |     def test_corrupt_asset_cache_is_replaced_without_provider(self):
  145 |         asset=self.app.get()['assets']['synera'];path=self.app.assets.directory/(asset['key']+'.svg')
  146 |         path.write_bytes(b'corrupt')
  147 |         self.app.close();self.app=Runtime(ROOT,self.directory)
  148 |         self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),asset['sha256'])
  149 |     def test_failed_image_provider_preserves_ready_fallback(self):
  150 |         with patch.object(self.app.providers,'check'),patch.object(self.app.providers,'generate',side_effect=ValueError('fixture failure')):
  151 |             result=self.call('regenerate_asset',{'node_id':'synera','use_provider':True})
  152 |             self.app.jobs.shutdown(wait=True)
  153 |         s=self.app.get();self.assertEqual(s['jobs'][result['job_id']]['status'],'ERROR')
  154 |         self.assertEqual(s['assets']['synera']['origin'],'offline-template')
  155 |         self.assertEqual(s['assets']['synera']['status'],'READY')
  156 |     def test_mocked_rule_provider_activates_through_same_tick(self):
  157 |         raw={k:v for k,v in compile_offline('new fixture bot').items() if k!='sha256'};raw['origin']='llm'
  158 |         with patch.object(self.app.providers,'check'),patch.object(self.app.providers,'generate',return_value=raw):
  159 |             result=self.call('forge_rule',{'prompt':'new fixture bot','use_provider':True})
  160 |             self.app.jobs.shutdown(wait=True)
  161 |         s=self.app.get();self.assertEqual(len(s['nodes']),17)
  162 |         self.assertEqual(s['jobs'][result['job_id']]['status'],'ACTIVE')
  163 |
  164 | class BoundaryTests(unittest.TestCase):
  165 |     def test_python_filter_is_additional_not_a_host_executor(self):
  166 |         for source in ['import os\ndef evaluate(state, params, seed): return []','def evaluate(state, params, seed):\n return open(".env").read()', 'def evaluate(state, params, seed):\n return ().__class__.__base__']:
  167 |             with self.assertRaises(ValueError):check_source(source)
  168 |     def test_incomplete_sandbox_config_fails_closed(self):
  169 |         with tempfile.TemporaryDirectory() as t:
  170 |             self.assertEqual(Sandbox(Path(t)/'sandbox.json').status,'BLOCKED_SANDBOX')
  171 |     def test_untrusted_session_destination_rejected(self):
  172 |         with tempfile.TemporaryDirectory() as t:
  173 |             p=Path(t)/'session.json';p.write_text('{"url":"https://example.com","token":"synthetic"}')
  174 |             with self.assertRaises(ValueError):LocalClient(p).session()
  175 |     def test_image_validation_and_transparency(self):
  176 |         from PIL import Image
  177 |         with tempfile.TemporaryDirectory() as t:
  178 |             forge=AssetForge(t);n={'id':'node-test','kind':'tower','title':'Node'}
  179 |             opaque=io.BytesIO();Image.new('RGB',(64,64)).save(opaque,format='PNG')
  180 |             with self.assertRaises(ValueError):forge.accept_image(n,opaque.getvalue())
  181 |             transparent=io.BytesIO();Image.new('RGBA',(64,64),(2,3,4,0)).save(transparent,format='PNG')
  182 |             result=forge.accept_image(n,transparent.getvalue());self.assertEqual(result['format'],'png')
  183 |     def test_freeze_never_hashes_env_or_runtime_generated_data(self):
  184 |         spec=importlib.util.spec_from_file_location('freeze',ROOT/'scripts/freeze.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  185 |         for path in (ROOT/'.env',ROOT/'.env.local',ROOT/'engine-isometric-ui/assets/generated/secret.svg',ROOT/'.runtime/bridge-venv/pyvenv.cfg',ROOT/'.codex/config.toml'):
  186 |             self.assertFalse(module.included(path))
  187 |         self.assertTrue(module.included(ROOT/'.env.example'))
  188 |
  189 | class ProviderTests(unittest.TestCase):
  190 |     def setUp(self):
  191 |         self.tmp=tempfile.TemporaryDirectory();self.directory=Path(self.tmp.name)
  192 |         governor=self.directory/'gradual_ai_launcher.py';governor.write_text('# fixture, never executed')
  193 |         (self.directory/'harness').mkdir();(self.directory/'harness/power_governor.py').write_text('# fixture')
  194 |         self.gateway=ProviderGateway(ROOT,self.directory)
  195 |         self.gateway.governor=governor
  196 |         self.gateway.policy=dict(enabled=True,allow_paid=True,provider='openai',rule_model='fixture-model',
  197 |             image_model='fixture-image',task_cap_usd=.02,day_cap_usd=.02,max_call_usd=.02,
  198 |             max_output_tokens=128,pricing_verified_on=datetime.now(timezone.utc).date().isoformat(),
  199 |             input_usd_per_million=.1,output_usd_per_million=.2,image_usd=.01)
  200 |     def tearDown(self):self.tmp.cleanup()
  201 |     def test_unknown_charge_keeps_reservation_and_prevents_repeat(self):
  202 |         import subprocess
  203 |         with patch('providers.subprocess.run',side_effect=subprocess.TimeoutExpired('fixture',1)) as run:
  204 |             with self.assertRaises(subprocess.TimeoutExpired):self.gateway.generate('rule','bot')
  205 |             with self.assertRaisesRegex(ValueError,'BLOCKED_BUDGET'):self.gateway.generate('rule','bot')
  206 |             self.assertEqual(run.call_count,1)
  207 |         row=self.gateway._ledger()[0];self.assertEqual(row['status'],'UNKNOWN_REQUIRES_RECONCILIATION')
  208 |         self.assertEqual(row['reservation_usd'],'0.02');self.assertIsNone(row['reported_cost_usd'])
  209 |     def test_missing_governor_and_stale_price_never_launch(self):
  210 |         with patch('providers.subprocess.run') as run:
  211 |             self.gateway.policy['pricing_verified_on']='2000-01-01'
  212 |             with self.assertRaisesRegex(ValueError,'STALE'):self.gateway.generate('rule','bot')
  213 |             self.gateway.governor=self.directory/'missing.py'
  214 |             with self.assertRaisesRegex(ValueError,'GOVERNOR'):self.gateway.generate('rule','bot')
  215 |             run.assert_not_called()
  216 |
  217 |
  218 | spec=importlib.util.spec_from_file_location('phase2_server',ROOT/'scripts/serve.py');server_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(server_module)
  219 |
  220 | class HttpTests(unittest.TestCase):
  221 |     def setUp(self):
  222 |         self.tmp=tempfile.TemporaryDirectory();self.server=server_module.SimulationServer(0,Path(self.tmp.name))
  223 |         self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
  224 |         self.url=f'http://127.0.0.1:{self.server.server_port}'
  225 |     def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
  226 |     def request(self,path,body=None,auth=True,origin=None):
  227 |         headers={}
  228 |         if auth:headers['Authorization']='Bearer '+self.server.token
  229 |         if origin:headers['Origin']=origin
  230 |         if body is not None:headers['Content-Type']='application/json'
  231 |         req=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
  232 |         return urllib.request.urlopen(req,timeout=4)
  233 |     def test_authenticated_tick_and_origin_rejection(self):
  234 |         for auth,origin in ((False,None),(True,'https://evil.example')):
  235 |             with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/tick',{'hours':1,'request_id':'http-test-0001'},auth,origin)
  236 |             self.assertIn(error.exception.code,(401,403))
  237 |         with self.request('/api/tick',{'hours':1,'request_id':'http-test-0001'}) as response:self.assertEqual(json.load(response)['state']['life']['tick'],4)
  238 |     def test_private_paths_and_unknown_assets_unavailable(self):
  239 |         for path in ('/.env','/.git/config','/CONTEXT_MANIFEST.json','/api/assets/'+'a'*64+'.svg'):
  240 |             with self.assertRaises(urllib.error.HTTPError):self.request(path)
  241 |     def test_es_modules_have_executable_mime_type(self):
  242 |         with self.request('/engine-isometric-ui/app.mjs',auth=False) as response:
  243 |             self.assertEqual(response.headers.get_content_type(),'text/javascript')
  244 |     def test_local_client_command_stream_ack_and_resume(self):
  245 |         result=LocalClient(Path(self.tmp.name)/'session.json').probe()
  246 |         self.assertEqual(result['status'],'LIVE_LOCAL_BRIDGE')
  247 |         with self.request('/api/mcp/stream?after='+str(result['event_id']-1)) as response:
  248 |             data=[]
  249 |             for _ in range(12):
  250 |                 line=response.readline().decode();data.append(line)
  251 |                 if line.startswith('data: '):break
  252 |             self.assertIn(f'id: {result["event_id"]}\n',data)
  253 |
  254 | if __name__=='__main__':unittest.main()
````

## tests/test_audit_followup.py

Original bytes: 12477; SHA256: `f302b9d750b164c91e79a40c2c7ddb3c9716acb2e0640de98ef45b298b1dd3f0`. Original source line numbers follow.

````text
    1 | """Observable regression cases from the SOURCE_ONLY Argon audit; no providers."""
    2 | from copy import deepcopy
    3 | import importlib.util
    4 | import json
    5 | from pathlib import Path
    6 | import sys
    7 | import tempfile
    8 | import threading
    9 | import unittest
   10 |
   11 | ROOT = Path(__file__).resolve().parents[1]
   12 | for directory in ('simulation-core', 'ai-architect', 'mcp-bridge'):
   13 |     sys.path.insert(0, str(ROOT / directory))
   14 | from runtime import Runtime
   15 | from unified_tick import advance, apply_operations, command, initial_state, public_state
   16 | from client import LocalClient
   17 |
   18 | MANIFEST = json.loads((ROOT / 'CONTEXT_MANIFEST.json').read_text(encoding='utf-8'))
   19 |
   20 |
   21 | def rule(id, operations):
   22 |     return dict(schema='sovereign.rule.v1', id=id, format='json', origin='operator',
   23 |                 assumptions=['Explicit synthetic test hypothesis, not actual finances or a causal prediction.'],
   24 |                 operations=operations)
   25 |
   26 |
   27 | class EconomicsFollowupTests(unittest.TestCase):
   28 |     def setUp(self):
   29 |         self.tmp = tempfile.TemporaryDirectory()
   30 |         self.app = Runtime(ROOT, Path(self.tmp.name))
   31 |         self.seq = 0
   32 |
   33 |     def tearDown(self):
   34 |         self.app.close()
   35 |         self.tmp.cleanup()
   36 |
   37 |     def call(self, name, payload):
   38 |         self.seq += 1
   39 |         return self.app.execute(name, payload, f'audit-command-{self.seq:04}')
   40 |
   41 |     def activate(self, value):
   42 |         self.call('forge_rule', {'rule': value})
   43 |         return self.call('tick', {'steps': 1})
   44 |
   45 |     def test_new_tower_setup_debits_at_activation_only_once_across_versions_and_restart(self):
   46 |         value = rule('audit-tower', [dict(op='add_node', id='audit-bot', title='Bot',
   47 |                       setup_cents=2000, auto_deduct_setup=True)])
   48 |         before = self.app.get()['economy']['cash_cents']
   49 |         self.call('forge_rule', {'rule': value})
   50 |         self.assertEqual(self.app.get()['economy']['cash_cents'], before)
   51 |         result = self.call('tick', {'steps': 1})
   52 |         self.assertEqual(self.app.get()['economy']['cash_cents'], before - 2000)
   53 |         self.assertEqual(result['rule_errors'], {})
   54 |         value['operations'][0]['title'] = 'Bot v2'
   55 |         value['operations'][0]['setup_cents'] = 3000
   56 |         self.activate(value)
   57 |         self.call('rollback_rule', {'rule_id': value['id']})
   58 |         self.call('tick', {'steps': 1})
   59 |         self.app.close()
   60 |         self.app = Runtime(ROOT, Path(self.tmp.name))
   61 |         self.call('tick', {'steps': 1})
   62 |         self.assertEqual(self.app.get()['economy']['cash_cents'], before - 2000)
   63 |         bot = next(n for n in self.app.get()['nodes'] if n['id'] == 'audit-bot')
   64 |         self.assertEqual(bot['setup_paid_cents'], 2000)
   65 |
   66 |     def test_manual_setup_debits_on_cashflow_and_net_roi_includes_setup(self):
   67 |         before = self.app.get()['economy']['cash_cents']
   68 |         self.call('configure_node', dict(node_id='synera', setup_cents=10000,
   69 |                   auto_deduct_setup=True, revenue_day_cents=10000, cost_day_cents=2000))
   70 |         self.call('node_status', dict(node_id='synera', status='SHIPPED'))
   71 |         self.assertEqual(self.app.get()['economy']['cash_cents'], before)
   72 |         self.call('node_status', dict(node_id='synera', status='ACTIVE_CASHFLOW'))
   73 |         self.assertEqual(self.app.get()['economy']['cash_cents'], before - 10000)
   74 |         self.call('node_status', dict(node_id='synera', status='ACTIVE_CASHFLOW'))
   75 |         self.call('configure_node', dict(node_id='synera', auto_deduct_setup=True))
   76 |         self.call('tick', {'days': 1})
   77 |         state = self.app.get()
   78 |         self.assertEqual(state['economy']['ROI']['synera'], -.2)
   79 |         self.assertEqual(state['economy']['setup_paid_cents'], 10000)
   80 |         self.assertEqual(state['tower_net_cents'], 8000)
   81 |
   82 |     def test_unaffordable_setup_and_invalid_modifier_never_partially_apply(self):
   83 |         for operations in (
   84 |             [dict(op='add_node', id='too-expensive', title='No', setup_cents=999999, auto_deduct_setup=True)],
   85 |             [dict(op='expense', amount_cents=100, kpi_modifiers={'Bio_RAM': 101})],
   86 |             [dict(op='expense', amount_cents=100, kpi_modifiers={'revenue_multiplier': True})],
   87 |             [dict(op='expense', amount_cents=100, kpi_modifiers={'actual_cash_chf': 100})],
   88 |             [dict(op='add_node', id='invalid-bool', title='No', auto_deduct_setup='true')],
   89 |         ):
   90 |             before = self.app.get()
   91 |             with self.assertRaises(ValueError):
   92 |                 self.call('forge_rule', {'rule': rule('invalid-test', operations)})
   93 |             self.assertEqual(self.app.get(), before)
   94 |
   95 |     def test_new_cost_can_conflict_at_tick_without_debit_or_half_created_node(self):
   96 |         for id in ('first', 'second'):
   97 |             self.call('forge_rule', {'rule': rule('rule-'+id, [dict(op='add_node', id='tower-'+id,
   98 |                       title=id, setup_cents=15000, auto_deduct_setup=True)])})
   99 |         result = self.call('tick', {'steps': 1})
  100 |         self.assertEqual(len(result['rule_errors']), 1)
  101 |         state = self.app.get()
  102 |         self.assertEqual(state['economy']['cash_cents'], 5000)
  103 |         self.assertEqual(state['economy']['setup_paid_cents'], 15000)
  104 |         self.assertEqual(len(state['nodes']), 17)
  105 |
  106 |     def test_expense_modifiers_are_explicit_absolute_and_not_reapplied_on_rollback(self):
  107 |         self.call('configure_node', dict(node_id='synera', revenue_day_cents=10000, cost_day_cents=2000))
  108 |         self.call('node_status', dict(node_id='synera', status='SHIPPED'))
  109 |         self.call('node_status', dict(node_id='synera', status='ACTIVE_CASHFLOW'))
  110 |         value = rule('audit-expense', [dict(op='expense', amount_cents=2000,
  111 |                      kpi_modifiers={'revenue_multiplier': 1.5, 'Bio_RAM': 60})])
  112 |         self.activate(value)
  113 |         state = self.app.get()
  114 |         self.assertEqual(state['config']['revenue_multiplier'], 1.5)
  115 |         self.assertEqual(state['economy']['conductor_nodes']['synera']['contribution_after_reserve'], '130.00')
  116 |         self.assertLess(state['bio']['Bio_RAM'], 80)
  117 |         value['operations'][0].update(amount_cents=1000, kpi_modifiers={'revenue_multiplier': 2})
  118 |         self.activate(value)
  119 |         paid = self.app.get()['economy']['cash_cents']
  120 |         self.call('rollback_rule', {'rule_id': 'audit-expense'})
  121 |         self.call('tick', {'steps': 1})
  122 |         self.assertEqual(self.app.get()['config']['revenue_multiplier'], 2)
  123 |         # No expense refund/recharge. Only the active tower's ordinary next-tick income changes cash.
  124 |         self.assertGreaterEqual(self.app.get()['economy']['cash_cents'], paid)
  125 |
  126 |     def test_offline_tower_accepts_explicit_cost_but_expense_infers_no_uplift(self):
  127 |         cash = self.app.get()['economy']['cash_cents']
  128 |         self.call('forge_rule', {'prompt': 'Додай башту бота', 'template_params':
  129 |                   {'setup_cents': 1000, 'auto_deduct_setup': True}})
  130 |         self.call('tick', {'steps': 1})
  131 |         self.assertEqual(self.app.get()['economy']['cash_cents'], cash - 1000)
  132 |         self.call('forge_rule', {'prompt': 'Імпланти за 20 CHF'})
  133 |         self.call('tick', {'steps': 1})
  134 |         self.assertEqual(self.app.get()['config']['revenue_multiplier'], 1)
  135 |         self.assertEqual(self.app.get()['config']['b2b_uplift_assumption'], 0)
  136 |
  137 |     def test_multiplier_uses_integer_cents_and_partitioned_ticks(self):
  138 |         state = initial_state(MANIFEST)
  139 |         state = command(state, 'configure_node', dict(node_id='synera', revenue_day_cents=101, cost_day_cents=11))
  140 |         for status in ('SHIPPED', 'ACTIVE_CASHFLOW'):
  141 |             state = command(state, 'node_status', dict(node_id='synera', status=status))
  142 |         state = apply_operations(state, [dict(op='expense', amount_cents=0,
  143 |                                 kpi_modifiers={'revenue_multiplier': 1.5})], 'rounding')
  144 |         original = deepcopy(state)
  145 |         one = advance(state, 96)
  146 |         split = state
  147 |         for _ in range(24):
  148 |             split = advance(split, 4)
  149 |         self.assertEqual(one, split)
  150 |         self.assertEqual(state, original)
  151 |         self.assertEqual(one['tower_net_cents'], 141)  # 1.01 CHF * 1.5 -> 1.52 minus .11
  152 |         self.assertIsNone(one['economy']['actual_cash_chf'])
  153 |
  154 |     def test_old_state_defaults_do_not_rewrite_input_or_invent_a_setup_debit(self):
  155 |         state=initial_state(MANIFEST)
  156 |         del state['config']['revenue_multiplier']
  157 |         for n in state['nodes']:
  158 |             for key in ('auto_deduct_setup','setup_deducted','setup_paid_cents'):del n[key]
  159 |         old=deepcopy(state)
  160 |         view=public_state(state)
  161 |         self.assertEqual(state,old)
  162 |         self.assertEqual(view['config']['revenue_multiplier'],1)
  163 |         self.assertEqual(view['economy']['setup_paid_cents'],0)
  164 |         self.assertEqual(view['economy']['cash_cents'],old['life']['balance_cents'])
  165 |         self.assertTrue(all(n['auto_deduct_setup'] is False for n in view['nodes']))
  166 |
  167 |
  168 | spec = importlib.util.spec_from_file_location('audit_server', ROOT / 'scripts/serve.py')
  169 | server_module = importlib.util.module_from_spec(spec)
  170 | spec.loader.exec_module(server_module)
  171 |
  172 |
  173 | class BridgeFollowupTests(unittest.TestCase):
  174 |     def test_client_connects_once_per_live_server_session_and_reconnects_after_restart(self):
  175 |         with tempfile.TemporaryDirectory() as directory:
  176 |             path = Path(directory)
  177 |             client = LocalClient(path / 'session.json')
  178 |             def start():
  179 |                 server = server_module.SimulationServer(0, path)
  180 |                 thread = threading.Thread(target=server.serve_forever, daemon=True)
  181 |                 thread.start()
  182 |                 return server, thread
  183 |             server, thread = start()
  184 |             try:
  185 |                 self.assertEqual(server.app.get()['bridge']['status'], 'NOT_CONNECTED')
  186 |                 receipt = client.connect()
  187 |                 self.assertEqual(receipt['status'], 'LIVE_LOCAL_BRIDGE')
  188 |                 revision = server.app.get()['revision']
  189 |                 self.assertEqual(client.connect(), receipt)
  190 |                 self.assertEqual(server.app.get()['revision'], revision)
  191 |                 self.assertEqual(server.app.get()['bridge']['providers'], 'NOT_CONNECTED')
  192 |                 with self.assertRaisesRegex(ValueError, 'MCP_CLIENT_REQUIRED'):
  193 |                     server.app.execute('ack_event', {'event_id': receipt['event_id']}, 'forged-ui-ack')
  194 |             finally:
  195 |                 server.shutdown(); server.server_close(); thread.join()
  196 |             server, thread = start()
  197 |             try:
  198 |                 self.assertEqual(server.app.get()['bridge']['status'], 'NOT_CONNECTED')
  199 |                 with self.assertRaises(ValueError):
  200 |                     server.app.execute('ack_event', {'event_id': receipt['event_id']}, 'stale-mcp-ack', 'mcp')
  201 |                 receipt = client.connect()
  202 |                 self.assertEqual(receipt['status'], 'LIVE_LOCAL_BRIDGE')
  203 |                 self.assertGreater(receipt['event_id'], revision)
  204 |             finally:
  205 |                 server.shutdown(); server.server_close(); thread.join()
  206 |
  207 |
  208 | class ProjectConfigurationTests(unittest.TestCase):
  209 |     def test_registration_is_project_only_idempotent_and_preserves_conflicts(self):
  210 |         spec = importlib.util.spec_from_file_location('configure_local_mcp', ROOT / 'scripts/configure_mcp.py')
  211 |         module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
  212 |         with tempfile.TemporaryDirectory() as directory:
  213 |             root = Path(directory)
  214 |             interpreter = root / '.runtime/bridge-venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
  215 |             interpreter.parent.mkdir(parents=True); interpreter.write_bytes(b'fixture-not-executed')
  216 |             config = root / '.codex/config.toml'; config.parent.mkdir()
  217 |             config.write_text('other_setting = "preserved"\n')
  218 |             self.assertEqual(module.register(root), 'REGISTERED_PROJECT_ONLY')
  219 |             before = config.read_bytes()
  220 |             self.assertEqual(module.register(root), 'UNCHANGED')
  221 |             self.assertEqual(config.read_bytes(), before)
  222 |             self.assertIn('other_setting = "preserved"', before.decode())
  223 |             config.write_text('[mcp_servers.sovereign_local]\ncommand = "keep-existing"\n')
  224 |             before = config.read_bytes()
  225 |             with self.assertRaisesRegex(ValueError, 'MCP_CONFIG_CONFLICT'):module.register(root)
  226 |             self.assertEqual(config.read_bytes(), before)
  227 |             with self.assertRaisesRegex(ValueError,'PROJECT_RUNTIME_SESSION_REQUIRED'):
  228 |                 module.configuration(root,root/'outside-private-runtime.json')
  229 |
  230 |
  231 | if __name__ == '__main__':
  232 |     unittest.main()
````

## tests/test_argon.py

Original bytes: 8881; SHA256: `8d732d687843c38680b3586e7d7f0bb33831e32458ce30f7f48246d4d14529ef`. Original source line numbers follow.

````text
    1 | import copy
    2 | import http.client
    3 | import importlib.util
    4 | import json
    5 | from pathlib import Path
    6 | import sys
    7 | import tempfile
    8 | import threading
    9 | import unittest
   10 |
   11 | ROOT = Path(__file__).resolve().parents[1]
   12 | sys.path.insert(0,str(ROOT/'argon-game'))
   13 | from game import Game, WORLD, WORLD_HASH, initial_state, step, save_packet, restore
   14 | spec=importlib.util.spec_from_file_location('argon_http',ROOT/'scripts/serve_argon.py')
   15 | http_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(http_module)
   16 |
   17 | ROUTE=['read_board','open_locker','to_bellevue','buy_ticket','take_tram','enter_atelier','meet_ada','test_demo','present_demo']
   18 |
   19 |
   20 | def play(actions):
   21 |     state=initial_state()
   22 |     for action in actions: state=step(state,action,{'code':'1942'} if action=='open_locker' else {})
   23 |     return state
   24 |
   25 |
   26 | class AdventureTests(unittest.TestCase):
   27 |     def test_complete_route_has_four_actual_locations_and_prepared_ending(self):
   28 |         result=play(ROUTE)
   29 |         self.assertEqual(result['visited'],['stadelhofen','bellevue','altstadt','atelier'])
   30 |         self.assertEqual(result['location'],'atelier')
   31 |         self.assertEqual(result['ending']['id'],'prepared')
   32 |         self.assertEqual(result['sim_time'],1147)
   33 |         self.assertEqual(result['cash_cents'],760)
   34 |         self.assertEqual(initial_state()['items'],['prototype'])
   35 |
   36 |     def test_free_alternative_route_is_winnable_without_locker(self):
   37 |         result=play(['to_bellevue','help_musician','take_tram','borrow_cable','enter_atelier','meet_ada','test_demo','present_demo'])
   38 |         self.assertEqual(result['ending']['id'],'prepared')
   39 |         self.assertEqual(result['cash_cents'],1200)
   40 |         self.assertIn('cable',result['items'])
   41 |
   42 |     def test_walking_route_and_late_ending(self):
   43 |         result=play(['to_bellevue','walk_altstadt','borrow_cable','enter_atelier','meet_ada','test_demo']+['atelier_rest']*8+['present_demo'])
   44 |         self.assertEqual(result['ending']['id'],'late')
   45 |         self.assertEqual(result['cash_cents'],1200)
   46 |
   47 |     def test_honest_ending_without_false_demo_completion(self):
   48 |         result=play(['to_bellevue','walk_altstadt','enter_atelier','meet_ada','present_honest'])
   49 |         self.assertEqual(result['ending']['id'],'honest')
   50 |         self.assertNotIn('demo_tested',result['flags'])
   51 |
   52 |     def test_illegal_actions_wrong_code_and_missing_prerequisites(self):
   53 |         before=initial_state()
   54 |         with self.assertRaises(ValueError): step(before,'present_demo')
   55 |         self.assertEqual(before,initial_state())
   56 |         wrong=step(before,'open_locker',{'code':'0000'})
   57 |         self.assertNotIn('cable',wrong['items'])
   58 |         self.assertEqual(wrong['sim_time'],1123)
   59 |         correct=step(wrong,'open_locker',{'code':'1942'})
   60 |         self.assertIn('cable',correct['items'])
   61 |         with self.assertRaises(ValueError):step(play(['to_bellevue']),'take_tram')
   62 |         with self.assertRaises(ValueError):step(play(ROUTE),'atelier_rest')
   63 |
   64 |     def test_no_double_rewards_no_payload_money_and_no_free_teleport(self):
   65 |         state=play(['to_bellevue','buy_ticket'])
   66 |         with self.assertRaises(ValueError): step(state,'buy_ticket')
   67 |         with self.assertRaises(ValueError): step(state,'back_station',{'cash_cents':999999})
   68 |         with self.assertRaises(ValueError): step(initial_state(),'enter_atelier')
   69 |
   70 |     def test_every_location_has_energy_recovery_and_no_unneeded_ticket_purchase(self):
   71 |         for location in WORLD['locations'].values():
   72 |             actions=[WORLD['actions'][a] for spot in location['hotspots'] for a in spot['actions']]
   73 |             self.assertTrue(any(a['energy']>0 and not a.get('cost') and not a.get('once') for a in actions))
   74 |         state=play(['to_bellevue','help_musician'])
   75 |         with self.assertRaises(ValueError): step(state,'buy_ticket')
   76 |
   77 |     def test_save_is_validated_by_replay_not_by_trusting_state_fields(self):
   78 |         state=play(ROUTE[:-1]);packet=save_packet(state)
   79 |         self.assertEqual(restore(packet),state)
   80 |         corrupt=copy.deepcopy(packet);corrupt['actions'][0]['action']='present_demo'
   81 |         with self.assertRaises(ValueError):restore(corrupt)
   82 |         foreign=copy.deepcopy(packet);foreign['world_hash']='foreign'
   83 |         with self.assertRaises(ValueError):restore(foreign)
   84 |         from persistence import digest
   85 |         forged=copy.deepcopy(packet);forged['actions'][0]['payload']['cash_cents']=999999
   86 |         forged['sha256']=digest({k:v for k,v in forged.items() if k!='sha256'})
   87 |         with self.assertRaises(ValueError):restore(forged)
   88 |
   89 |     def test_journal_restart_checkpoint_and_idempotency(self):
   90 |         with tempfile.TemporaryDirectory() as directory:
   91 |             game=Game(directory)
   92 |             first=game.command('to_bellevue',{},'test-action-0001')
   93 |             self.assertEqual(game.command('to_bellevue',{},'test-action-0001'),first)
   94 |             with self.assertRaises(ValueError):game.command('buy_ticket',{},'test-action-0001')
   95 |             game.command('buy_ticket',{},'test-action-0002')
   96 |             saved=game.store.get()
   97 |             game.command('save_checkpoint',{},'test-action-0003')
   98 |             game.command('take_tram',{},'test-action-0004')
   99 |             game.close()
  100 |             game=Game(directory)
  101 |             self.assertEqual(game.store.get()['location'],'altstadt')
  102 |             game.command('load_checkpoint',{},'test-action-0005')
  103 |             actual=game.store.get()
  104 |             for key in saved:
  105 |                 if key!='revision':self.assertEqual(actual[key],saved[key])
  106 |             game.command('new_game',{},'test-action-0006')
  107 |             self.assertTrue(game.view()['saved_checkpoint'])
  108 |             game.command('load_checkpoint',{},'test-action-0007')
  109 |             self.assertEqual(game.store.get()['location'],'bellevue')
  110 |             game.close()
  111 |
  112 |     def test_corrupt_checkpoint_rejected_without_changing_live_state(self):
  113 |         with tempfile.TemporaryDirectory() as directory:
  114 |             game=Game(directory)
  115 |             game.command('to_bellevue',{},'test-action-0001')
  116 |             before=game.store.get()
  117 |             Path(directory,'checkpoint.json').write_text('{"broken":true}')
  118 |             with self.assertRaises(ValueError):game.command('load_checkpoint',{},'test-action-0002')
  119 |             self.assertEqual(game.store.get(),before)
  120 |             game.close()
  121 |
  122 |     def test_stale_revision_cannot_repeat_a_committed_turn_with_a_new_id(self):
  123 |         with tempfile.TemporaryDirectory() as directory:
  124 |             game=Game(directory)
  125 |             try:
  126 |                 revision=game.store.get()['revision']
  127 |                 first=game.command('catch_breath',{},'revision-0001',revision)
  128 |                 self.assertEqual(game.command('catch_breath',{},'revision-0001',revision),first)
  129 |                 before=game.store.get()
  130 |                 with self.assertRaisesRegex(ValueError,'REVISION_CONFLICT'):
  131 |                     game.command('catch_breath',{},'revision-0002',revision)
  132 |                 self.assertEqual(game.store.get(),before)
  133 |             finally:game.close()
  134 |
  135 |
  136 | class AdventureHTTPTests(unittest.TestCase):
  137 |     def test_loopback_auth_origin_static_allowlist_and_durable_action(self):
  138 |         with tempfile.TemporaryDirectory() as directory:
  139 |             server=http_module.Server(0,directory)
  140 |             thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  141 |             def request(method,path,body=None,headers=None):
  142 |                 client=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
  143 |                 client.request(method,path,json.dumps(body) if body else None,headers or {})
  144 |                 response=client.getresponse();status=response.status;data=response.read();client.close()
  145 |                 return status,data
  146 |             try:
  147 |                 self.assertEqual(request('GET','/')[0],200)
  148 |                 self.assertEqual(request('GET','/api/state')[0],401)
  149 |                 for path in ['/../.env','/.git/config','/world.json','/api/../.runtime/argon/events.jsonl','/art/../../.env']:
  150 |                     self.assertEqual(request('GET',path)[0],404)
  151 |                 status,body=request('GET','/api/session');self.assertEqual(status,200)
  152 |                 token=json.loads(body)['token']
  153 |                 payload={'action':'to_bellevue','payload':{},'request_id':'http-action-0001'}
  154 |                 self.assertEqual(request('POST','/api/action',payload,{'Content-Type':'application/json'})[0],401)
  155 |                 headers={'Content-Type':'application/json','Authorization':'Bearer '+token,'Origin':'https://foreign.invalid'}
  156 |                 self.assertEqual(request('POST','/api/action',payload,headers)[0],403)
  157 |                 del headers['Origin']
  158 |                 status,body=request('POST','/api/action',payload,headers)
  159 |                 self.assertEqual(status,200);self.assertEqual(json.loads(body)['state']['location'],'bellevue')
  160 |             finally:server.shutdown();server.server_close();thread.join()
  161 |
  162 |
  163 | if __name__=='__main__':unittest.main()
````
