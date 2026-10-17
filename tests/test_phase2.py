from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
from datetime import datetime,timezone
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
for directory in ('simulation-core','ai-architect','mcp-bridge'):sys.path.insert(0,str(ROOT/directory))
from unified_tick import initial_state,advance,command,apply_operations
from game_theory_shield import simulate
from persistence import Store
from runtime import Runtime
from ruleforge import compile_offline,validate_rule
from sandbox import Sandbox,check_source
from assetforge import AssetForge
from providers import ProviderGateway
from client import LocalClient

MANIFEST=json.loads((ROOT/'CONTEXT_MANIFEST.json').read_text(encoding='utf-8'))

class CoreTests(unittest.TestCase):
    def setUp(self):self.state=initial_state(MANIFEST)
    def test_reproducible_partitioned_ticks_and_no_input_mutation(self):
        original=deepcopy(self.state);one=advance(self.state,96)
        split=self.state
        for _ in range(24):split=advance(split,4)
        self.assertEqual(one,split);self.assertEqual(self.state,original)
    def test_all_manifest_ids_and_queue_limit(self):
        self.assertEqual({n['id'] for n in self.state['nodes']},{p['id'] for p in MANIFEST['projects']})
        self.assertEqual([n['id'] for n in self.state['nodes'] if n['status']=='FOCUSED'],['synera','brand-social-os'])
        s=command(self.state,'node_status',{'node_id':'synera','status':'SHIPPED'})
        self.assertEqual(sum(n['status']=='FOCUSED' for n in s['nodes']),2)
        self.assertEqual(s,command(s,'node_status',{'node_id':'synera','status':'SHIPPED'}))
        with self.assertRaisesRegex(ValueError,'QUEUED'):command(s,'node_status',{'node_id':'mirofish','status':'SHIPPED'})
    def test_debuff_multiplier_does_not_compound_and_expires(self):
        s=command(self.state,'update_params',{'bio':{'debuff_hours':2}})
        self.assertEqual(advance(s,4)['bio']['build_multiplier'],.6)
        self.assertEqual(advance(s,8)['bio']['build_multiplier'],1)
    def test_self_report_triggers_model_debuff_but_clear_is_explicit(self):
        s=command(self.state,'update_params',{'bio':{'Sleep_Sync_Index':20}})
        self.assertTrue(s['bio']['debuff_active'])
        self.assertFalse(command(s,'update_params',{'bio':{'debuff_hours':0}})['bio']['debuff_active'])
    def test_quest_is_explicit_and_not_reset(self):
        self.assertIsNone(self.state['quest']['start_step'])
        s=advance(command(self.state,'activate_quest',{}),4)
        self.assertEqual(command(s,'activate_quest',{})['quest']['hours_remaining'],47)
        self.assertEqual(s['economy']['gemeinde_status'],'UNCONFIGURED')
    def test_conductor_drives_active_cashflow_in_integer_cents(self):
        s=command(self.state,'configure_node',dict(node_id='synera',revenue_day_cents=10000,cost_day_cents=2000,setup_cents=10000))
        s=command(s,'node_status',dict(node_id='synera',status='SHIPPED'))
        s=command(s,'node_status',dict(node_id='synera',status='ACTIVE_CASHFLOW'))
        s=advance(s,96)
        self.assertEqual(s['tower_net_cents'],8000)
        self.assertEqual(s['economy']['conductor_nodes']['synera']['contribution_after_reserve'],'80.00')
        self.assertEqual(s['economy']['ROI']['synera'],.8)
        self.assertIsNone(s['economy']['actual_cash_chf'])
    def test_operation_batch_rejects_partial_apply(self):
        before=deepcopy(self.state)
        with self.assertRaises(ValueError):apply_operations(self.state,[dict(op='add_node',id='new-node',title='New'),dict(op='shell',cmd='bad')],'rule-test')
        self.assertEqual(before,self.state)
    def test_strategy_math_includes_first_loss_and_exit_cost(self):
        rescuer=simulate();tft=simulate(left='Sovereign_TitForTat');exit=simulate(left='Sovereign_TitForTat',exit_on_breach=True)
        self.assertEqual(rescuer['cumulative'],[0,100]);self.assertEqual(tft['cumulative'],[19,24])
        self.assertEqual(tft['exploitation_rate'][0],.05);self.assertEqual(exit['completed_rounds'],1)
        self.assertEqual(exit['energy'][0],3);self.assertEqual(exit['cumulative'][0],0)
        self.assertEqual(simulate(right='Unconditional_Rescuer')['cumulative'],[60,60])

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.directory=Path(self.tmp.name);self.app=Runtime(ROOT,self.directory)
    def tearDown(self):self.app.close();self.tmp.cleanup()
    def call(self,name,payload,id='request-0001'):return self.app.execute(name,payload,id)
    def test_concurrent_retry_applies_only_once(self):
        with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(lambda _:self.call('tick',{'hours':1}),range(16)))
        self.assertEqual(self.app.get()['life']['tick'],4)
        self.assertTrue(all(r==results[0] for r in results))
        with self.assertRaisesRegex(ValueError,'CONFLICT'):self.call('tick',{'hours':2})
    def test_restart_replays_state_and_idempotency(self):
        self.call('tick',{'hours':1});state=self.app.get();self.app.close();self.app=Runtime(ROOT,self.directory)
        self.assertEqual(self.app.get(),state);self.call('tick',{'hours':1});self.assertEqual(self.app.get(),state)
    def test_fsync_failure_never_acknowledges_or_updates_memory(self):
        before=self.app.get()
        with patch('persistence.os.fsync',side_effect=OSError('disk')):
            with self.assertRaises(OSError):self.call('tick',{'hours':1})
        self.assertEqual(self.app.get(),before)
        with self.assertRaises(OSError):self.call('tick',{'hours':1},'request-0002')
    def test_rule_stages_then_activates_and_recovers(self):
        r=self.call('forge_rule',{'prompt':'Додай башту нового бота'})
        self.assertEqual(r['status'],'PENDING_TICK');self.assertEqual(len(self.app.get()['nodes']),16)
        self.call('tick',{'steps':1},'activate-0001');s=self.app.get();self.assertEqual(len(s['nodes']),17)
        new=s['nodes'][-1];self.assertIn(new['id'],s['assets']);self.assertTrue(s['rules'][r['rule_id']]['active'])
        self.app.close();self.app=Runtime(ROOT,self.directory);self.assertEqual(self.app.get(),s)
    def test_rule_hash_and_manifest_node_overwrite_rejected(self):
        rule=compile_offline('Додай бота');rule['operations'][0]['id']='synera'
        with self.assertRaisesRegex(ValueError,'OWNED_ELSEWHERE'):
            self.call('forge_rule',{'rule':{k:v for k,v in rule.items() if k!='sha256'}})
    def test_python_missing_sandbox_is_blocked_without_execution(self):
        self.app.sandbox.status='BLOCKED_SANDBOX';before=self.app.get()
        with self.assertRaisesRegex(ValueError,'BLOCKED_SANDBOX'):self.call('forge_rule',{'prompt':'Додай бота','format':'python'})
        self.assertEqual(self.app.get(),before)
    def test_invalid_and_unsupported_requests_do_not_mutate(self):
        before=self.app.get()
        for payload in ({'prompt':'write a poem'},{'prompt':'bot','format':'shell'},{'rule':{'schema':'wrong'}}):
            with self.assertRaises(ValueError):self.call('forge_rule',payload)
        self.assertEqual(self.app.get(),before)
    def test_expense_once_and_rollback_does_not_refund(self):
        r=self.call('forge_rule',{'prompt':'Імпланти за 20 CHF'})
        self.call('tick',{'steps':1},'tick-one-0001');cash=self.app.get()['life']['balance_cents']
        self.call('tick',{'steps':1},'tick-two-0001');self.assertEqual(self.app.get()['life']['balance_cents'],cash)
        self.call('rollback_rule',{'rule_id':r['rule_id']},'rollback-0001');self.assertEqual(self.app.get()['life']['balance_cents'],cash)
    def test_provider_is_disabled_without_budget(self):
        with patch('providers.subprocess.run') as run:
            with self.assertRaisesRegex(ValueError,'BLOCKED_PROVIDER'):self.call('forge_rule',{'prompt':'bot','use_provider':True})
            run.assert_not_called()
    def test_asset_regeneration_and_cache(self):
        old=self.app.get()['assets']['synera'];same=self.app.assets.fallback(self.app.get()['nodes'][0])
        self.assertEqual(old,same)
        self.call('regenerate_asset',{'node_id':'synera'});new=self.app.get()['assets']['synera']
        self.assertNotEqual(old['sha256'],new['sha256']);self.assertEqual(new['origin'],'offline-template')
    def test_recovery_ignores_snapshot_and_preserves_interrupted_tail(self):
        self.call('tick',{'hours':1});self.app.close()
        (self.directory/'state.json').write_text('broken')
        with (self.directory/'events.jsonl').open('ab') as handle:handle.write(b'{incomplete')
        self.app=Runtime(ROOT,self.directory)
        self.assertEqual(self.app.get()['life']['tick'],4)
        self.assertTrue(list(self.directory.glob('interrupted-*.bin')))
    def test_conflicting_pending_expenses_do_not_block_clock(self):
        self.call('forge_rule',{'prompt':'Імпланти за 150 CHF'},'expense-first')
        self.call('forge_rule',{'prompt':'Стоматологія за 160 CHF'},'expense-second')
        result=self.call('tick',{'steps':1},'expense-activate')
        self.assertEqual(self.app.get()['life']['tick'],1)
        self.assertEqual(self.app.get()['life']['balance_cents'],5000)
        self.assertEqual(len(result['rule_errors']),1)
    def test_corrupt_asset_cache_is_replaced_without_provider(self):
        asset=self.app.get()['assets']['synera'];path=self.app.assets.directory/(asset['key']+'.svg')
        path.write_bytes(b'corrupt')
        self.app.close();self.app=Runtime(ROOT,self.directory)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),asset['sha256'])
    def test_failed_image_provider_preserves_ready_fallback(self):
        with patch.object(self.app.providers,'check'),patch.object(self.app.providers,'generate',side_effect=ValueError('fixture failure')):
            result=self.call('regenerate_asset',{'node_id':'synera','use_provider':True})
            self.app.jobs.shutdown(wait=True)
        s=self.app.get();self.assertEqual(s['jobs'][result['job_id']]['status'],'ERROR')
        self.assertEqual(s['assets']['synera']['origin'],'offline-template')
        self.assertEqual(s['assets']['synera']['status'],'READY')
    def test_mocked_rule_provider_activates_through_same_tick(self):
        raw={k:v for k,v in compile_offline('new fixture bot').items() if k!='sha256'};raw['origin']='llm'
        with patch.object(self.app.providers,'check'),patch.object(self.app.providers,'generate',return_value=raw):
            result=self.call('forge_rule',{'prompt':'new fixture bot','use_provider':True})
            self.app.jobs.shutdown(wait=True)
        s=self.app.get();self.assertEqual(len(s['nodes']),17)
        self.assertEqual(s['jobs'][result['job_id']]['status'],'ACTIVE')

class BoundaryTests(unittest.TestCase):
    def test_python_filter_is_additional_not_a_host_executor(self):
        for source in ['import os\ndef evaluate(state, params, seed): return []','def evaluate(state, params, seed):\n return open(".env").read()', 'def evaluate(state, params, seed):\n return ().__class__.__base__']:
            with self.assertRaises(ValueError):check_source(source)
    def test_incomplete_sandbox_config_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(Sandbox(Path(t)/'sandbox.json').status,'BLOCKED_SANDBOX')
    def test_untrusted_session_destination_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'session.json';p.write_text('{"url":"https://example.com","token":"synthetic"}')
            with self.assertRaises(ValueError):LocalClient(p).session()
    def test_image_validation_and_transparency(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as t:
            forge=AssetForge(t);n={'id':'node-test','kind':'tower','title':'Node'}
            opaque=io.BytesIO();Image.new('RGB',(64,64)).save(opaque,format='PNG')
            with self.assertRaises(ValueError):forge.accept_image(n,opaque.getvalue())
            transparent=io.BytesIO();Image.new('RGBA',(64,64),(2,3,4,0)).save(transparent,format='PNG')
            result=forge.accept_image(n,transparent.getvalue());self.assertEqual(result['format'],'png')
    def test_freeze_never_hashes_env_or_runtime_generated_data(self):
        spec=importlib.util.spec_from_file_location('freeze',ROOT/'scripts/freeze.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for path in (ROOT/'.env',ROOT/'.env.local',ROOT/'engine-isometric-ui/assets/generated/secret.svg',ROOT/'.runtime/bridge-venv/pyvenv.cfg'):
            self.assertFalse(module.included(path))
        self.assertTrue(module.included(ROOT/'.env.example'))

class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.directory=Path(self.tmp.name)
        governor=self.directory/'gradual_ai_launcher.py';governor.write_text('# fixture, never executed')
        (self.directory/'harness').mkdir();(self.directory/'harness/power_governor.py').write_text('# fixture')
        self.gateway=ProviderGateway(ROOT,self.directory)
        self.gateway.governor=governor
        self.gateway.policy=dict(enabled=True,allow_paid=True,provider='openai',rule_model='fixture-model',
            image_model='fixture-image',task_cap_usd=.02,day_cap_usd=.02,max_call_usd=.02,
            max_output_tokens=128,pricing_verified_on=datetime.now(timezone.utc).date().isoformat(),
            input_usd_per_million=.1,output_usd_per_million=.2,image_usd=.01)
    def tearDown(self):self.tmp.cleanup()
    def test_unknown_charge_keeps_reservation_and_prevents_repeat(self):
        import subprocess
        with patch('providers.subprocess.run',side_effect=subprocess.TimeoutExpired('fixture',1)) as run:
            with self.assertRaises(subprocess.TimeoutExpired):self.gateway.generate('rule','bot')
            with self.assertRaisesRegex(ValueError,'BLOCKED_BUDGET'):self.gateway.generate('rule','bot')
            self.assertEqual(run.call_count,1)
        row=self.gateway._ledger()[0];self.assertEqual(row['status'],'UNKNOWN_REQUIRES_RECONCILIATION')
        self.assertEqual(row['reservation_usd'],'0.02');self.assertIsNone(row['reported_cost_usd'])
    def test_missing_governor_and_stale_price_never_launch(self):
        with patch('providers.subprocess.run') as run:
            self.gateway.policy['pricing_verified_on']='2000-01-01'
            with self.assertRaisesRegex(ValueError,'STALE'):self.gateway.generate('rule','bot')
            self.gateway.governor=self.directory/'missing.py'
            with self.assertRaisesRegex(ValueError,'GOVERNOR'):self.gateway.generate('rule','bot')
            run.assert_not_called()


spec=importlib.util.spec_from_file_location('phase2_server',ROOT/'scripts/serve.py');server_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(server_module)

class HttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.server=server_module.SimulationServer(0,Path(self.tmp.name))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def request(self,path,body=None,auth=True,origin=None):
        headers={}
        if auth:headers['Authorization']='Bearer '+self.server.token
        if origin:headers['Origin']=origin
        if body is not None:headers['Content-Type']='application/json'
        req=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
        return urllib.request.urlopen(req,timeout=4)
    def test_authenticated_tick_and_origin_rejection(self):
        for auth,origin in ((False,None),(True,'https://evil.example')):
            with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/tick',{'hours':1,'request_id':'http-test-0001'},auth,origin)
            self.assertIn(error.exception.code,(401,403))
        with self.request('/api/tick',{'hours':1,'request_id':'http-test-0001'}) as response:self.assertEqual(json.load(response)['state']['life']['tick'],4)
    def test_private_paths_and_unknown_assets_unavailable(self):
        for path in ('/.env','/.git/config','/CONTEXT_MANIFEST.json','/api/assets/'+'a'*64+'.svg'):
            with self.assertRaises(urllib.error.HTTPError):self.request(path)
    def test_es_modules_have_executable_mime_type(self):
        with self.request('/engine-isometric-ui/app.mjs',auth=False) as response:
            self.assertEqual(response.headers.get_content_type(),'text/javascript')
    def test_local_client_command_stream_ack_and_resume(self):
        result=LocalClient(Path(self.tmp.name)/'session.json').probe()
        self.assertEqual(result['status'],'LIVE_LOCAL_BRIDGE')
        with self.request('/api/mcp/stream?after='+str(result['event_id']-1)) as response:
            data=[]
            for _ in range(12):
                line=response.readline().decode();data.append(line)
                if line.startswith('data: '):break
            self.assertIn(f'id: {result["event_id"]}\n',data)

if __name__=='__main__':unittest.main()
