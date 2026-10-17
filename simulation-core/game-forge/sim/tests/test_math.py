from copy import deepcopy
import itertools
import math
import random
import unittest

from sim.core import (energy_equilibrium, energy_step, habit_alpha, habit_closed,
                      habit_step, initial_state, load_params, next_random,
                      skill_level, skill_value, step, ticks_per_day, time_fields)


class MathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = load_params()
        cls.tol = cls.p['validation']['tolerance']

    def test_habit_closed_vs_iteration(self):
        for days in (18, 66, 254):
            p = deepcopy(self.p)
            p['habits']['days_to_automaticity'] = days
            alpha = habit_alpha(p)
            for start in (0, .2, .9, 1):
                h = start
                for n in range(1, 1001):
                    h = habit_step(h, alpha)
                    self.assertLessEqual(abs(h - habit_closed(start, alpha, n)), self.tol)
            self.assertAlmostEqual(habit_closed(0, alpha, days), .95, delta=self.tol)

    def test_habit_full_steps_and_daily_cap(self):
        p = self.p
        s = initial_state(p)
        count = ticks_per_day(p)
        for _ in range(count):
            s = step(s, {'kind': 'screen'}, p, s['rng'])
        self.assertAlmostEqual(s['habits']['screen'], habit_alpha(p), delta=self.tol)
        before = s['habits']['screen']
        for _ in range(count):
            s = step(s, {'kind': 'rest'}, p, s['rng'])
        self.assertEqual(s['habits']['screen'], before, 'Missing a day must not erase habit')
        self.assertEqual(s['habit_streak']['screen'], 0)

    def test_energy_equilibrium(self):
        p = self.p
        dt = p['clock']['step_minutes'] / p['clock']['minutes_per_hour']
        for kind, burnout, weather, light in itertools.product(('rest', 'work', 'sleep'), (0, .4, 1), p['weather'], (False, True)):
            e = .55
            target = energy_equilibrium(kind, burnout, weather, 20, light, p)
            rate = p['energy']['sleep_rate_per_hour' if kind == 'sleep' else 'awake_rate_per_hour']
            for n in range(1, p['validation']['equilibrium_steps'] + 1):
                e = energy_step(e, kind, burnout, weather, 20, light, 1, p)
                if n in (1, 10, 100):
                    analytical = target + (.55 - target) * math.exp(-rate * dt * n)
                    self.assertLessEqual(abs(e - analytical), self.tol, 'ENERGY_DECAY_ORACLE')
            self.assertLessEqual(abs(e - target), self.tol, 'ENERGY_DECAY_ORACLE')

    def test_sleep_monotonic(self):
        r = random.Random(self.p['validation']['seed'])
        for _ in range(1000):
            e, burnout = r.random(), r.random()
            weather = r.choice(list(self.p['weather']))
            q1, q2 = sorted((r.random(), r.random()))
            low = energy_step(e, 'sleep', burnout, weather, 3, False, q1, self.p)
            high = energy_step(e, 'sleep', burnout, weather, 3, False, q2, self.p)
            self.assertGreaterEqual(high + self.tol, low)
            # Same starting state/environment, replace initial rest ticks with sleep.
            s1 = initial_state(self.p, weather=weather)
            s1['energy'], s1['burnout'] = e, burnout
            s2 = deepcopy(s1)
            for j in range(16):
                s1 = step(s1, {'kind': 'sleep' if j >= 8 else 'rest'}, self.p, s1['rng'])
                s2 = step(s2, {'kind': 'sleep'}, self.p, s2['rng'])
            self.assertGreaterEqual(s2['energy'] + self.tol, s1['energy'])

    def test_skill_diminishing_returns(self):
        gains = [skill_value(i + 1, self.p) - skill_value(i, self.p) for i in range(1000)]
        self.assertTrue(all(x > 0 for x in gains))
        self.assertTrue(all(a > b for a, b in zip(gains, gains[1:])))
        self.assertEqual(skill_level(0, self.p), 0)
        self.assertEqual(skill_level(1, self.p), 5)
        s = initial_state(self.p)
        before = s['practice_hours']['german']
        p = deepcopy(self.p)
        p['actions']['study']['failure_burnout_factor'] = 0
        out = step(s, {'kind': 'study'}, p, s['rng'])
        expected = before + .25 * s['energy'] * (1 - s['burnout'])
        self.assertAlmostEqual(out['practice_hours']['german'], expected, delta=self.tol)

    def test_burnout_corridor_guarantee(self):
        # All extreme accumulation/recovery/threshold/start combinations.
        # Defined overload schedule: 8h sleep then 16h unrestricted basic work.
        for accumulation, recovery, threshold, start in itertools.product((.005, .009), (.003, .007), (.7, .8), (0, .4)):
            p = deepcopy(self.p)
            p['burnout'].update(accumulation_per_hour=accumulation, recovery_per_hour=recovery, threshold=threshold)
            p['initial']['burnout'] = start
            s = initial_state(p, weather='neutral')
            crossed = None
            for tick in range(p['burnout']['overload_max_days'] * ticks_per_day(p)):
                hour = time_fields(s['tick'], p)['hour']
                s = step(s, {'kind': 'sleep' if hour < 8 else 'work'}, p, s['rng'])
                if tick < ticks_per_day(p):
                    self.assertLess(s['burnout'], threshold)
                if s['burnout'] >= threshold:
                    crossed = (tick + 1) / ticks_per_day(p)
                    break
            self.assertIsNotNone(crossed, (accumulation, recovery, threshold, start))
            self.assertLessEqual(crossed, p['burnout']['overload_max_days'])
        p = deepcopy(self.p)
        p['burnout']['accumulation_per_hour'] = .009
        s = initial_state(p)
        for _ in range(ticks_per_day(p)):
            s = step(s, {'kind': 'work'}, p, s['rng'])
        self.assertLess(s['burnout'], p['burnout']['threshold'])

    def test_weather_and_evening_light(self):
        outcomes = {}
        for weather, light in itertools.product(self.p['weather'], (False, True)):
            s = initial_state(self.p, weather=weather)
            s['tick'] = 18 * 4
            for _ in range(16):
                s = step(s, {'kind': 'rest', 'light': light}, self.p, s['rng'])
            outcomes[weather, light] = s
        for field in ('energy', 'mood'):
            self.assertLess(outcomes['gray_wet', False][field], outcomes['gray_wet', True][field])
            self.assertLess(outcomes['gray_wet', True][field], outcomes['neutral', False][field])
            self.assertLess(outcomes['neutral', False][field], outcomes['golden_autumn', False][field])
        s = initial_state(self.p)
        s['tick'] = 12 * 4
        self.assertEqual(step(s, {'kind': 'rest', 'light': True}, self.p, s['rng']),
                         step(s, {'kind': 'rest', 'light': False}, self.p, s['rng']))


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = load_params()

    def test_purity_and_seed(self):
        p = deepcopy(self.p)
        s = initial_state(p)
        a = {'kind': 'study'}
        original = deepcopy((s, a, p))
        first = step(s, a, p, s['rng'])
        self.assertEqual((s, a, p), original)
        self.assertEqual(first, step(s, a, p, s['rng']))
        self.assertNotEqual(first['rng'], step(s, a, p, s['rng'] + 1)['rng'])
        # Independent, well-known LCG vector for seed 0.
        self.assertEqual(next_random(0, p)[0], 1013904223)

    def test_time_and_rollovers(self):
        p = self.p
        self.assertEqual([time_fields(t, p)['phase'] for t in (0,24,48,72)], ['night','morning','day','evening'])
        self.assertEqual(time_fields(96, p)['day'], 2)
        self.assertEqual(time_fields(7*96, p)['week'], 2)
        self.assertEqual(time_fields(21*96, p)['season'], 'winter')
        s = initial_state(p)
        s['tick'] = ticks_per_day(p) * p['money']['support_period_days'] - 1
        out = step(s, {'kind': 'rest'}, p, s['rng'])
        amounts = {t['id']: t['amount_cents'] for t in out['transactions']}
        self.assertEqual(amounts['social_support'], p['money']['support_cents'])
        self.assertEqual(amounts['daily_living'], -p['money']['daily_cost_cents'])
        next_out = step(out, {'kind': 'rest'}, p, out['rng'])
        self.assertEqual(next_out['transactions'], [])

    def test_debt_and_action_affordability(self):
        s = initial_state(self.p)
        amount = -s['balance_cents'] - 1
        a = {'kind': 'rest', 'transactions': [{'id': 'purchase', 'amount_cents': amount}]}
        out = step(s, a, self.p, s['rng'])
        self.assertEqual(out['balance_cents'], s['balance_cents'])
        self.assertEqual(out['transactions'], [])
        a['allow_debt'] = True
        out = step(s, a, self.p, s['rng'])
        self.assertEqual(out['balance_cents'], -1)
        self.assertEqual([e for e in out['events'] if e['type']=='debt'][0]['amount_cents'], 1)
        s['balance_cents'], s['net_cents'] = 0, -self.p['initial']['balance_cents']
        out = step(s, {'kind': 'alcohol'}, self.p, s['rng'])
        self.assertEqual(out['effective_action'], 'rest')
        self.assertEqual(out['habits']['alcohol'], 0)

    def test_blocking_and_probability_threshold(self):
        s = initial_state(self.p)
        s['energy'] = 0
        out = step(s, {'kind':'craft'}, self.p, s['rng'])
        self.assertEqual(out['events'][0]['reason'], 'low_energy')
        for probability, expected in ((0, 'study'), (1, 'rest')):
            p = deepcopy(self.p)
            p['actions']['study']['failure_base'] = probability
            p['actions']['study']['failure_burnout_factor'] = 0
            s = initial_state(p)
            self.assertEqual(step(s, {'kind':'study'}, p, s['rng'])['effective_action'], expected)

    def test_morning_effect_once(self):
        p = self.p
        s = initial_state(p)
        s['tick'] = 23
        s['pending_energy'], s['pending_burnout'] = -.2, .05
        control = deepcopy(s)
        control['pending_energy'], control['pending_burnout'] = 0, 0
        out = step(s, {'kind': 'sleep'}, p, s['rng'])
        clean = step(control, {'kind': 'sleep'}, p, s['rng'])
        self.assertAlmostEqual(out['energy'], clean['energy'] - .2)
        self.assertAlmostEqual(out['burnout'], clean['burnout'] + .05)
        self.assertEqual((out['pending_energy'], out['pending_burnout']), (0, 0))

    def test_invalid_inputs(self):
        for value in (float('nan'), float('inf'), -1, 2, True):
            s = initial_state(self.p)
            s['energy'] = value
            with self.assertRaises(ValueError):
                step(s, {'kind':'rest'}, self.p, s['rng'])
        for a in ({'kind':'unknown'}, {'kind':'sleep','sleep_quality':float('nan')},
                  {'kind':'rest','light':1}, {'kind':'rest','extra':0},
                  {'kind':'rest','transactions':[{'id':'bad','amount_cents':.1}]}):
            s = initial_state(self.p)
            with self.assertRaises(ValueError):
                step(s, a, self.p, s['rng'])
        s = initial_state(self.p)
        s['tick'] = 1
        with self.assertRaises(ValueError):
            step(s, {'kind':'rest','weather':'golden_autumn'}, self.p, s['rng'])

    def test_10000_seeded_random_scenarios(self):
        p = self.p
        r = random.Random(p['validation']['seed'])
        for case in range(p['validation']['random_runs']):
            seed = r.randrange(p['rng']['modulus'])
            s = initial_state(p, seed, r.choice(list(p['weather'])))
            s['energy'], s['burnout'], s['mood'] = r.random(), r.random(), r.random()
            s['tick'] = r.randrange(31 * ticks_per_day(p))
            replay = deepcopy(s)
            initial_balance = s['balance_cents']
            net = 0
            for _ in range(r.randint(1, p['validation']['random_max_steps'])):
                a = {'kind':r.choice(list(p['actions'])), 'light':bool(r.getrandbits(1)),
                     'allow_debt':bool(r.getrandbits(1)), 'sleep_quality':r.random(),
                     'transactions':[{'id':'random', 'amount_cents':r.randint(-10000,10000)}]}
                previous = s['balance_cents']
                s = step(s, a, p, s['rng'])
                replay = step(replay, a, p, replay['rng'])
                self.assertEqual(s, replay, 'Seed replay case ' + str(case))
                delta = sum(t['amount_cents'] for t in s['transactions'])
                net += delta
                self.assertEqual(s['balance_cents'] - previous, delta)
                self.assertEqual(s['balance_cents'] - initial_balance, net)
                for x in [s['energy'], s['burnout'], s['mood'], *s['habits'].values(),
                          *(skill_value(h,p) for h in s['practice_hours'].values())]:
                    self.assertTrue(math.isfinite(x) and 0 <= x <= 1, (case, x))
                if not a['allow_debt']:
                    self.assertGreaterEqual(s['balance_cents'], min(0,previous))
                if s['balance_cents'] < min(0, previous):
                    self.assertTrue(any(e['type']=='debt' for e in s['events']))
