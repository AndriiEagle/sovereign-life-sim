"""Observable regression cases from the SOURCE_ONLY Argon audit; no providers."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
for directory in ('simulation-core', 'ai-architect', 'mcp-bridge'):
    sys.path.insert(0, str(ROOT / directory))
from runtime import Runtime
from unified_tick import advance, apply_operations, command, initial_state, public_state
from client import LocalClient

MANIFEST = json.loads((ROOT / 'CONTEXT_MANIFEST.json').read_text(encoding='utf-8'))


def rule(id, operations):
    return dict(schema='sovereign.rule.v1', id=id, format='json', origin='operator',
                assumptions=['Explicit synthetic test hypothesis, not actual finances or a causal prediction.'],
                operations=operations)


class EconomicsFollowupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Runtime(ROOT, Path(self.tmp.name))
        self.seq = 0

    def tearDown(self):
        self.app.close()
        self.tmp.cleanup()

    def call(self, name, payload):
        self.seq += 1
        return self.app.execute(name, payload, f'audit-command-{self.seq:04}')

    def activate(self, value):
        self.call('forge_rule', {'rule': value})
        return self.call('tick', {'steps': 1})

    def test_new_tower_setup_debits_at_activation_only_once_across_versions_and_restart(self):
        value = rule('audit-tower', [dict(op='add_node', id='audit-bot', title='Bot',
                      setup_cents=2000, auto_deduct_setup=True)])
        before = self.app.get()['economy']['cash_cents']
        self.call('forge_rule', {'rule': value})
        self.assertEqual(self.app.get()['economy']['cash_cents'], before)
        result = self.call('tick', {'steps': 1})
        self.assertEqual(self.app.get()['economy']['cash_cents'], before - 2000)
        self.assertEqual(result['rule_errors'], {})
        value['operations'][0]['title'] = 'Bot v2'
        value['operations'][0]['setup_cents'] = 3000
        self.activate(value)
        self.call('rollback_rule', {'rule_id': value['id']})
        self.call('tick', {'steps': 1})
        self.app.close()
        self.app = Runtime(ROOT, Path(self.tmp.name))
        self.call('tick', {'steps': 1})
        self.assertEqual(self.app.get()['economy']['cash_cents'], before - 2000)
        bot = next(n for n in self.app.get()['nodes'] if n['id'] == 'audit-bot')
        self.assertEqual(bot['setup_paid_cents'], 2000)

    def test_manual_setup_debits_on_cashflow_and_net_roi_includes_setup(self):
        before = self.app.get()['economy']['cash_cents']
        self.call('configure_node', dict(node_id='synera', setup_cents=10000,
                  auto_deduct_setup=True, revenue_day_cents=10000, cost_day_cents=2000))
        self.call('node_status', dict(node_id='synera', status='SHIPPED'))
        self.assertEqual(self.app.get()['economy']['cash_cents'], before)
        self.call('node_status', dict(node_id='synera', status='ACTIVE_CASHFLOW'))
        self.assertEqual(self.app.get()['economy']['cash_cents'], before - 10000)
        self.call('node_status', dict(node_id='synera', status='ACTIVE_CASHFLOW'))
        self.call('configure_node', dict(node_id='synera', auto_deduct_setup=True))
        self.call('tick', {'days': 1})
        state = self.app.get()
        self.assertEqual(state['economy']['ROI']['synera'], -.2)
        self.assertEqual(state['economy']['setup_paid_cents'], 10000)
        self.assertEqual(state['tower_net_cents'], 8000)

    def test_unaffordable_setup_and_invalid_modifier_never_partially_apply(self):
        for operations in (
            [dict(op='add_node', id='too-expensive', title='No', setup_cents=999999, auto_deduct_setup=True)],
            [dict(op='expense', amount_cents=100, kpi_modifiers={'Bio_RAM': 101})],
            [dict(op='expense', amount_cents=100, kpi_modifiers={'revenue_multiplier': True})],
            [dict(op='expense', amount_cents=100, kpi_modifiers={'actual_cash_chf': 100})],
            [dict(op='add_node', id='invalid-bool', title='No', auto_deduct_setup='true')],
        ):
            before = self.app.get()
            with self.assertRaises(ValueError):
                self.call('forge_rule', {'rule': rule('invalid-test', operations)})
            self.assertEqual(self.app.get(), before)

    def test_new_cost_can_conflict_at_tick_without_debit_or_half_created_node(self):
        for id in ('first', 'second'):
            self.call('forge_rule', {'rule': rule('rule-'+id, [dict(op='add_node', id='tower-'+id,
                      title=id, setup_cents=15000, auto_deduct_setup=True)])})
        result = self.call('tick', {'steps': 1})
        self.assertEqual(len(result['rule_errors']), 1)
        state = self.app.get()
        self.assertEqual(state['economy']['cash_cents'], 5000)
        self.assertEqual(state['economy']['setup_paid_cents'], 15000)
        self.assertEqual(len(state['nodes']), 17)

    def test_expense_modifiers_are_explicit_absolute_and_not_reapplied_on_rollback(self):
        self.call('configure_node', dict(node_id='synera', revenue_day_cents=10000, cost_day_cents=2000))
        self.call('node_status', dict(node_id='synera', status='SHIPPED'))
        self.call('node_status', dict(node_id='synera', status='ACTIVE_CASHFLOW'))
        value = rule('audit-expense', [dict(op='expense', amount_cents=2000,
                     kpi_modifiers={'revenue_multiplier': 1.5, 'Bio_RAM': 60})])
        self.activate(value)
        state = self.app.get()
        self.assertEqual(state['config']['revenue_multiplier'], 1.5)
        self.assertEqual(state['economy']['conductor_nodes']['synera']['contribution_after_reserve'], '130.00')
        self.assertLess(state['bio']['Bio_RAM'], 80)
        value['operations'][0].update(amount_cents=1000, kpi_modifiers={'revenue_multiplier': 2})
        self.activate(value)
        paid = self.app.get()['economy']['cash_cents']
        self.call('rollback_rule', {'rule_id': 'audit-expense'})
        self.call('tick', {'steps': 1})
        self.assertEqual(self.app.get()['config']['revenue_multiplier'], 2)
        # No expense refund/recharge. Only the active tower's ordinary next-tick income changes cash.
        self.assertGreaterEqual(self.app.get()['economy']['cash_cents'], paid)

    def test_offline_tower_accepts_explicit_cost_but_expense_infers_no_uplift(self):
        cash = self.app.get()['economy']['cash_cents']
        self.call('forge_rule', {'prompt': 'Додай башту бота', 'template_params':
                  {'setup_cents': 1000, 'auto_deduct_setup': True}})
        self.call('tick', {'steps': 1})
        self.assertEqual(self.app.get()['economy']['cash_cents'], cash - 1000)
        self.call('forge_rule', {'prompt': 'Імпланти за 20 CHF'})
        self.call('tick', {'steps': 1})
        self.assertEqual(self.app.get()['config']['revenue_multiplier'], 1)
        self.assertEqual(self.app.get()['config']['b2b_uplift_assumption'], 0)

    def test_multiplier_uses_integer_cents_and_partitioned_ticks(self):
        state = initial_state(MANIFEST)
        state = command(state, 'configure_node', dict(node_id='synera', revenue_day_cents=101, cost_day_cents=11))
        for status in ('SHIPPED', 'ACTIVE_CASHFLOW'):
            state = command(state, 'node_status', dict(node_id='synera', status=status))
        state = apply_operations(state, [dict(op='expense', amount_cents=0,
                                kpi_modifiers={'revenue_multiplier': 1.5})], 'rounding')
        original = deepcopy(state)
        one = advance(state, 96)
        split = state
        for _ in range(24):
            split = advance(split, 4)
        self.assertEqual(one, split)
        self.assertEqual(state, original)
        self.assertEqual(one['tower_net_cents'], 141)  # 1.01 CHF * 1.5 -> 1.52 minus .11
        self.assertIsNone(one['economy']['actual_cash_chf'])

    def test_old_state_defaults_do_not_rewrite_input_or_invent_a_setup_debit(self):
        state=initial_state(MANIFEST)
        del state['config']['revenue_multiplier']
        for n in state['nodes']:
            for key in ('auto_deduct_setup','setup_deducted','setup_paid_cents'):del n[key]
        old=deepcopy(state)
        view=public_state(state)
        self.assertEqual(state,old)
        self.assertEqual(view['config']['revenue_multiplier'],1)
        self.assertEqual(view['economy']['setup_paid_cents'],0)
        self.assertEqual(view['economy']['cash_cents'],old['life']['balance_cents'])
        self.assertTrue(all(n['auto_deduct_setup'] is False for n in view['nodes']))


spec = importlib.util.spec_from_file_location('audit_server', ROOT / 'scripts/serve.py')
server_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)


class BridgeFollowupTests(unittest.TestCase):
    def test_client_connects_once_per_live_server_session_and_reconnects_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            client = LocalClient(path / 'session.json')
            def start():
                server = server_module.SimulationServer(0, path)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                return server, thread
            server, thread = start()
            try:
                self.assertEqual(server.app.get()['bridge']['status'], 'NOT_CONNECTED')
                receipt = client.connect()
                self.assertEqual(receipt['status'], 'LIVE_LOCAL_BRIDGE')
                revision = server.app.get()['revision']
                self.assertEqual(client.connect(), receipt)
                self.assertEqual(server.app.get()['revision'], revision)
                self.assertEqual(server.app.get()['bridge']['providers'], 'NOT_CONNECTED')
                with self.assertRaisesRegex(ValueError, 'MCP_CLIENT_REQUIRED'):
                    server.app.execute('ack_event', {'event_id': receipt['event_id']}, 'forged-ui-ack')
            finally:
                server.shutdown(); server.server_close(); thread.join()
            server, thread = start()
            try:
                self.assertEqual(server.app.get()['bridge']['status'], 'NOT_CONNECTED')
                with self.assertRaises(ValueError):
                    server.app.execute('ack_event', {'event_id': receipt['event_id']}, 'stale-mcp-ack', 'mcp')
                receipt = client.connect()
                self.assertEqual(receipt['status'], 'LIVE_LOCAL_BRIDGE')
                self.assertGreater(receipt['event_id'], revision)
            finally:
                server.shutdown(); server.server_close(); thread.join()


class ProjectConfigurationTests(unittest.TestCase):
    def test_registration_is_project_only_idempotent_and_preserves_conflicts(self):
        spec = importlib.util.spec_from_file_location('configure_local_mcp', ROOT / 'scripts/configure_mcp.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            interpreter = root / '.runtime/bridge-venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
            interpreter.parent.mkdir(parents=True); interpreter.write_bytes(b'fixture-not-executed')
            config = root / '.codex/config.toml'; config.parent.mkdir()
            config.write_text('other_setting = "preserved"\n')
            self.assertEqual(module.register(root), 'REGISTERED_PROJECT_ONLY')
            before = config.read_bytes()
            self.assertEqual(module.register(root), 'UNCHANGED')
            self.assertEqual(config.read_bytes(), before)
            self.assertIn('other_setting = "preserved"', before.decode())
            config.write_text('[mcp_servers.sovereign_local]\ncommand = "keep-existing"\n')
            before = config.read_bytes()
            with self.assertRaisesRegex(ValueError, 'MCP_CONFIG_CONFLICT'):module.register(root)
            self.assertEqual(config.read_bytes(), before)
            with self.assertRaisesRegex(ValueError,'PROJECT_RUNTIME_SESSION_REQUIRED'):
                module.configuration(root,root/'outside-private-runtime.json')


if __name__ == '__main__':
    unittest.main()
