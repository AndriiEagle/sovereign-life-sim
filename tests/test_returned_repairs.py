"""Semantic regressions recovered from the returned audit; synthetic stores only."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
for directory in ('simulation-core', 'ai-architect'):
    sys.path.insert(0, str(ROOT / directory))
from contracts import canonical
from persistence import Store
from runtime import Runtime


def rule(name, operations):
    return dict(schema='sovereign.rule.v1', id=name, format='json', origin='operator',
                assumptions=['Synthetic regression fixture.'], operations=operations)


class ReturnedRepairsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        self.app = Runtime(ROOT, self.directory)
        self.sequence = 0

    def tearDown(self):
        self.app.close()
        self.tmp.cleanup()

    def call(self, name, payload):
        self.sequence += 1
        return self.app.execute(name, payload, f'repair-review-{self.sequence:04}')

    def activate(self, raw):
        result = self.call('forge_rule', {'rule': raw})
        self.assertEqual(self.call('tick', {'steps': 1})['rule_errors'], {})
        return result['sha256']

    def restart(self):
        self.app.close()
        self.app = Runtime(ROOT, self.directory)

    def test_disabled_node_cannot_bypass_rollback_and_reactivation_does_not_recharge(self):
        raw = rule('review-node', [dict(op='add_node', id='review-tower', title='Tower',
                   setup_cents=1000, auto_deduct_setup=True, revenue_day_cents=9600)])
        version = self.activate(raw)
        while any(n['status'] == 'Queued' for n in self.app.get()['nodes']):
            focused = next(n for n in self.app.get()['nodes'] if n['status'] == 'FOCUSED')
            self.call('node_status', {'node_id': focused['id'], 'status': 'SHIPPED'})
        self.call('rollback_rule', {'rule_id': raw['id']})
        before = self.app.get()
        for status in ('SHIPPED', 'ACTIVE_CASHFLOW', 'FOCUSED'):
            with self.subTest(status=status):
                with self.assertRaisesRegex(ValueError, 'DISABLED_NODE_LOCKED'):
                    self.call('node_status', {'node_id': 'review-tower', 'status': status})
                self.assertEqual(self.app.get(), before)
        self.assertEqual(self.activate(raw), version)
        state = self.app.get()
        node = next(n for n in state['nodes'] if n['id'] == 'review-tower')
        self.assertIn(node['status'], ('FOCUSED', 'Queued'))
        self.assertEqual(state['economy']['cash_cents'], before['economy']['cash_cents'])
        self.assertEqual(state['economy']['setup_paid_cents'], 1000)
        self.assertLessEqual(sum(n['status'] == 'FOCUSED' for n in state['nodes']), 2)
        self.restart()
        self.assertEqual(self.app.get(), state)

    def test_cancelled_rollback_keeps_history_and_duplicate_after_restart(self):
        raw = rule('review-expense', [dict(op='expense', amount_cents=1000)])
        first = self.activate(raw)
        raw['operations'][0]['amount_cents'] = 2000
        second = self.activate(raw)
        cash = self.app.get()['economy']['cash_cents']
        self.call('rollback_rule', {'rule_id': raw['id']})
        self.restart()
        canceled = self.call('rollback_rule', {'rule_id': raw['id']})
        self.assertEqual(self.app.get()['rules'][raw['id']]['history'], [first])
        before = self.app.get()
        self.restart()
        self.assertEqual(self.app.execute('rollback_rule', {'rule_id': raw['id']}, canceled['request_id']), canceled)
        self.assertEqual(self.app.get(), before)
        for expected, previous in ((first, second), (second, first)):
            self.call('rollback_rule', {'rule_id': raw['id']})
            self.assertEqual(self.call('tick', {'steps': 1})['rule_errors'], {})
            view = self.app.get()
            self.assertEqual(view['rules'][raw['id']]['active'], expected)
            self.assertEqual(view['rules'][raw['id']]['history'], [previous])
            self.assertEqual(view['economy']['cash_cents'], cash)

    def test_rejected_provider_activation_is_terminal_and_version_bound(self):
        raw = rule('review-provider', [dict(op='expense', amount_cents=15000)])
        self.call('forge_rule', {'rule': rule('review-first', [dict(op='expense', amount_cents=15000)])})
        state = self.app.store.get()
        old = dict(status='PENDING_TICK', kind='rule', rule_id=raw['id'], sha256='older')
        state['jobs'] = {'older': deepcopy(old)}
        self.app.store.commit('fixture', {}, 'test', 'review-fixture-0001', {}, state)
        with patch.object(self.app.providers, 'check'), patch.object(self.app.providers, 'generate', return_value=raw) as generate:
            result = self.call('forge_rule', {'prompt': 'fixture', 'use_provider': True})
            self.app.jobs.shutdown(wait=True)
            generate.assert_called_once()
        jobs = self.app.store.get()['jobs']
        self.assertEqual(jobs[result['job_id']]['status'], 'ERROR')
        self.assertEqual(jobs[result['job_id']]['error'], 'INSUFFICIENT_SCENARIO_FUNDS')
        self.assertEqual(jobs['older'], old)
        self.restart()
        self.assertEqual(self.app.store.get()['jobs'], jobs)

    def test_bad_complete_records_preserve_journal_and_release_lease(self):
        self.app.close()
        path = self.directory / 'events.jsonl'
        original = path.read_bytes()
        initial = {'sim_time': '2026-10-19T00:00:00Z', 'revision': 0}
        for value in ({}, [], None, 123):
            with self.subTest(value=value):
                damaged = original + canonical(value).encode() + b'\nunfinished\xe2'
                path.write_bytes(damaged)
                try:
                    opened = Store(self.directory, initial)
                except Exception as error:
                    self.assertIs(type(error), ValueError)
                    self.assertEqual(str(error), 'JOURNAL_CORRUPT')
                else:
                    opened.close()
                    self.fail('Malformed completed row was accepted')
                finally:
                    self.assertEqual(path.read_bytes(), damaged)
                    path.write_bytes(original)
                reopened = Store(self.directory, initial)
                reopened.close()

    def test_bom_crlf_and_interrupted_unicode_tail_remain_compatible(self):
        expected = self.app.get()
        self.app.close()
        path = self.directory / 'events.jsonl'
        original = b'\xef\xbb\xbf' + path.read_bytes().replace(b'\n', b'\r\n')
        tail = '{"unfinished":"Львів'.encode('utf8') + b'\xe2'
        path.write_bytes(original + tail)
        self.restart()
        self.assertEqual(self.app.get(), expected)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual([p.read_bytes() for p in self.directory.glob('interrupted-*.bin')], [tail])
