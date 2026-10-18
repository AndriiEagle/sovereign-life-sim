import copy
import http.client
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'argon-game'))
from game import Game, WORLD, WORLD_HASH, initial_state, step, save_packet, restore
spec=importlib.util.spec_from_file_location('argon_http',ROOT/'scripts/serve_argon.py')
http_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(http_module)

ROUTE=['read_board','open_locker','to_bellevue','buy_ticket','take_tram','enter_atelier','meet_ada','test_demo','present_demo']


def play(actions):
    state=initial_state()
    for action in actions: state=step(state,action,{'code':'1942'} if action=='open_locker' else {})
    return state


class AdventureTests(unittest.TestCase):
    def test_complete_route_has_four_actual_locations_and_prepared_ending(self):
        result=play(ROUTE)
        self.assertEqual(result['visited'],['stadelhofen','bellevue','altstadt','atelier'])
        self.assertEqual(result['location'],'atelier')
        self.assertEqual(result['ending']['id'],'prepared')
        self.assertEqual(result['sim_time'],1147)
        self.assertEqual(result['cash_cents'],760)
        self.assertEqual(initial_state()['items'],['prototype'])

    def test_free_alternative_route_is_winnable_without_locker(self):
        result=play(['to_bellevue','help_musician','take_tram','borrow_cable','enter_atelier','meet_ada','test_demo','present_demo'])
        self.assertEqual(result['ending']['id'],'prepared')
        self.assertEqual(result['cash_cents'],1200)
        self.assertIn('cable',result['items'])

    def test_walking_route_and_late_ending(self):
        result=play(['to_bellevue','walk_altstadt','borrow_cable','enter_atelier','meet_ada','test_demo']+['atelier_rest']*8+['present_demo'])
        self.assertEqual(result['ending']['id'],'late')
        self.assertEqual(result['cash_cents'],1200)

    def test_honest_ending_without_false_demo_completion(self):
        result=play(['to_bellevue','walk_altstadt','enter_atelier','meet_ada','present_honest'])
        self.assertEqual(result['ending']['id'],'honest')
        self.assertNotIn('demo_tested',result['flags'])

    def test_illegal_actions_wrong_code_and_missing_prerequisites(self):
        before=initial_state()
        with self.assertRaises(ValueError): step(before,'present_demo')
        self.assertEqual(before,initial_state())
        wrong=step(before,'open_locker',{'code':'0000'})
        self.assertNotIn('cable',wrong['items'])
        self.assertEqual(wrong['sim_time'],1123)
        correct=step(wrong,'open_locker',{'code':'1942'})
        self.assertIn('cable',correct['items'])
        with self.assertRaises(ValueError):step(play(['to_bellevue']),'take_tram')
        with self.assertRaises(ValueError):step(play(ROUTE),'atelier_rest')

    def test_no_double_rewards_no_payload_money_and_no_free_teleport(self):
        state=play(['to_bellevue','buy_ticket'])
        with self.assertRaises(ValueError): step(state,'buy_ticket')
        with self.assertRaises(ValueError): step(state,'back_station',{'cash_cents':999999})
        with self.assertRaises(ValueError): step(initial_state(),'enter_atelier')

    def test_every_location_has_energy_recovery_and_no_unneeded_ticket_purchase(self):
        for location in WORLD['locations'].values():
            actions=[WORLD['actions'][a] for spot in location['hotspots'] for a in spot['actions']]
            self.assertTrue(any(a['energy']>0 and not a.get('cost') and not a.get('once') for a in actions))
        state=play(['to_bellevue','help_musician'])
        with self.assertRaises(ValueError): step(state,'buy_ticket')

    def test_save_is_validated_by_replay_not_by_trusting_state_fields(self):
        state=play(ROUTE[:-1]);packet=save_packet(state)
        self.assertEqual(restore(packet),state)
        corrupt=copy.deepcopy(packet);corrupt['actions'][0]['action']='present_demo'
        with self.assertRaises(ValueError):restore(corrupt)
        foreign=copy.deepcopy(packet);foreign['world_hash']='foreign'
        with self.assertRaises(ValueError):restore(foreign)
        from persistence import digest
        forged=copy.deepcopy(packet);forged['actions'][0]['payload']['cash_cents']=999999
        forged['sha256']=digest({k:v for k,v in forged.items() if k!='sha256'})
        with self.assertRaises(ValueError):restore(forged)

    def test_journal_restart_checkpoint_and_idempotency(self):
        with tempfile.TemporaryDirectory() as directory:
            game=Game(directory)
            first=game.command('to_bellevue',{},'test-action-0001')
            self.assertEqual(game.command('to_bellevue',{},'test-action-0001'),first)
            with self.assertRaises(ValueError):game.command('buy_ticket',{},'test-action-0001')
            game.command('buy_ticket',{},'test-action-0002')
            saved=game.store.get()
            game.command('save_checkpoint',{},'test-action-0003')
            game.command('take_tram',{},'test-action-0004')
            game.close()
            game=Game(directory)
            self.assertEqual(game.store.get()['location'],'altstadt')
            game.command('load_checkpoint',{},'test-action-0005')
            actual=game.store.get()
            for key in saved:
                if key!='revision':self.assertEqual(actual[key],saved[key])
            game.command('new_game',{},'test-action-0006')
            self.assertTrue(game.view()['saved_checkpoint'])
            game.command('load_checkpoint',{},'test-action-0007')
            self.assertEqual(game.store.get()['location'],'bellevue')
            game.close()

    def test_corrupt_checkpoint_rejected_without_changing_live_state(self):
        with tempfile.TemporaryDirectory() as directory:
            game=Game(directory)
            game.command('to_bellevue',{},'test-action-0001')
            before=game.store.get()
            Path(directory,'checkpoint.json').write_text('{"broken":true}')
            with self.assertRaises(ValueError):game.command('load_checkpoint',{},'test-action-0002')
            self.assertEqual(game.store.get(),before)
            game.close()

    def test_stale_revision_cannot_repeat_a_committed_turn_with_a_new_id(self):
        with tempfile.TemporaryDirectory() as directory:
            game=Game(directory)
            try:
                revision=game.store.get()['revision']
                first=game.command('catch_breath',{},'revision-0001',revision)
                self.assertEqual(game.command('catch_breath',{},'revision-0001',revision),first)
                before=game.store.get()
                with self.assertRaisesRegex(ValueError,'REVISION_CONFLICT'):
                    game.command('catch_breath',{},'revision-0002',revision)
                self.assertEqual(game.store.get(),before)
            finally:game.close()


class AdventureHTTPTests(unittest.TestCase):
    def test_loopback_auth_origin_static_allowlist_and_durable_action(self):
        with tempfile.TemporaryDirectory() as directory:
            server=http_module.Server(0,directory)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def request(method,path,body=None,headers=None):
                client=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
                client.request(method,path,json.dumps(body) if body else None,headers or {})
                response=client.getresponse();status=response.status;data=response.read();client.close()
                return status,data
            try:
                self.assertEqual(request('GET','/')[0],200)
                self.assertEqual(request('GET','/api/state')[0],401)
                for path in ['/../.env','/.git/config','/world.json','/api/../.runtime/argon/events.jsonl','/art/../../.env']:
                    self.assertEqual(request('GET',path)[0],404)
                status,body=request('GET','/api/session');self.assertEqual(status,200)
                token=json.loads(body)['token']
                payload={'action':'to_bellevue','payload':{},'request_id':'http-action-0001'}
                self.assertEqual(request('POST','/api/action',payload,{'Content-Type':'application/json'})[0],401)
                headers={'Content-Type':'application/json','Authorization':'Bearer '+token,'Origin':'https://foreign.invalid'}
                self.assertEqual(request('POST','/api/action',payload,headers)[0],403)
                del headers['Origin']
                status,body=request('POST','/api/action',payload,headers)
                self.assertEqual(status,200);self.assertEqual(json.loads(body)['state']['location'],'bellevue')
            finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
