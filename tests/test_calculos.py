"""Pruebas con datos exclusivamente sintéticos; sin hardware ni I/O científico."""

import copy
import json
import math
import unittest

from app.calculos import (
    calibracion_dinamica, calibracion_estatica, estabilidad, histeresis,
    precision, progreso_estatico, voltage_mv_a_lm35,
)


def transient(cooling=False, offset=0.0, step=0.2):
    """Equilibrio explícito y exponencial analítica K=1.2, tau=4 s."""
    x0, xf = (60.0, 30.0) if cooling else (25.0, 55.0)
    y0 = 1.2 * x0 + 2.0
    t = [-4.0, -3.0, -2.0, -1.0, 0.0]
    t += [step * i for i in range(1, int(40 / step) + 1)]
    y = [y0 if u <= 0 else y0 + 1.2 * (xf-x0) * (1-math.exp(-u/4))
         for u in t]
    return [u+offset for u in t], y, x0, xf


class PrecisionTests(unittest.TestCase):
    def test_sample_statistics(self):
        p = precision([1, 2, 3])
        self.assertEqual(set(p), {'n', 'media', 's', 's_m', 'rsd', 'cv', 'varianza'})
        self.assertEqual((p['n'], p['media'], p['s'], p['varianza']), (3, 2, 1, 1))
        self.assertAlmostEqual(p['s_m'], 1/math.sqrt(3))
        self.assertEqual((p['rsd'], p['cv']), (0.5, 50))

    def test_zero_mean_and_constant(self):
        p = precision([-1, 1])
        self.assertIsNone(p['rsd'])
        self.assertIsNone(p['cv'])
        self.assertEqual(p['varianza'], 2)
        self.assertEqual(precision([7, 7])['s'], 0)
        self.assertEqual(precision([-3, -2, -1])['cv'], -50)

    def test_invalid_values(self):
        for values in ([], [1], None, '12', [True, 2], ['1', 2],
                       [float('nan'), 2], [float('inf'), 2], [1e308, -1e308]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                precision(values)


class StaticTests(unittest.TestCase):
    def test_exact_linear_and_bland_altman(self):
        r = calibracion_estatica([1, 2, 3], [3, 5, 7])
        self.assertEqual((r['n'], r['m'], r['b'], r['r'], r['e_g'], r['e_0']),
                         (3, 2, 1, 1, 1, 1))
        self.assertEqual(r['corregidas'], [1, 2, 3])
        self.assertEqual(r['sigma_p'], 0)
        self.assertEqual(r['intervalos'], {'k1': 0, 'k2': 0, 'k3': 0})
        ba = r['bland_altman']
        self.assertEqual(ba['medias'], [2, 3.5, 5])
        self.assertEqual(ba['diferencias'], [2, 3, 4])
        self.assertEqual(ba['sesgo'], 3)
        self.assertAlmostEqual(ba['limite_inferior'], 1.04)
        self.assertAlmostEqual(ba['limite_superior'], 4.96)
        self.assertEqual(r['curva_ajuste'], {'x': [1, 3], 'y': [3, 7]})

    def test_inaccuracy_divisor_and_correction(self):
        r = calibracion_estatica([0, 1, 2], [0, 1, 3])
        self.assertAlmostEqual(r['m'], 1.5)
        self.assertAlmostEqual(r['b'], -1/6)
        self.assertAlmostEqual(r['sigma_p'], math.sqrt(2)/9)
        self.assertAlmostEqual(r['intervalos']['k3'], math.sqrt(2)/3)

    def test_order_negative_correlation_and_repeated_levels(self):
        r = calibracion_estatica([3, 1, 2], [-1, 3, 1])
        self.assertEqual(r['r'], -1)
        self.assertEqual(r['corregidas'], [3, 1, 2])
        self.assertEqual(r['curva_ajuste']['x'], [1, 3])
        self.assertEqual(calibracion_estatica([1, 1, 2], [2, 2, 4])['m'], 2)

    def test_centering_large_offset(self):
        x = [1e9+i for i in range(5)]
        r = calibracion_estatica(x, [2*v+1 for v in x])
        self.assertEqual(r['m'], 2)
        self.assertEqual(r['b'], 1)

    def test_degenerate_inputs(self):
        for x, y in (([], []), ([1], [2]), ([1, 2], [3]),
                     ([1, 1], [2, 3]), ([1, 2], [3, 3]),
                     ([-1, 0, 1], [1, 0, 1]), ([1, 2], [2, float('nan')])):
            with self.subTest(x=x, y=y), self.assertRaises(ValueError):
                calibracion_estatica(x, y)

    def test_hysteresis(self):
        self.assertEqual(histeresis([20, 40], [21, 38], 0, 100), [1, 2])
        for a, d, lo, hi in (([], [], 0, 1), ([1], [], 0, 1),
                             ([1], [2], 1, 1), ([1], [2], 2, 1),
                             ([1], [None], 0, 1)):
            with self.subTest(a=a, d=d), self.assertRaises(ValueError):
                histeresis(a, d, lo, hi)


class IntegrationHelpersTests(unittest.TestCase):
    def test_voltage_nominal(self):
        self.assertEqual(voltage_mv_a_lm35(250), 25)
        self.assertEqual(voltage_mv_a_lm35(0), 0)
        self.assertEqual(voltage_mv_a_lm35(-100), -10)
        for v in (None, True, '250', float('inf'), float('nan')):
            with self.subTest(v=v), self.assertRaises(ValueError):
                voltage_mv_a_lm35(v)

    def test_stability_selects_last_five_seconds_both_sensors(self):
        samples = [{'t': i, 'vernier': 25., 'lm35': 25.} for i in range(8)]
        samples[0]['lm35'] = 100
        self.assertEqual(estabilidad(samples),
                         {'ready': True, 'reason': 'Ventana estable', 'n': 6,
                          'window_seconds': 5.0})
        for sensor in ('vernier', 'lm35'):
            noisy = copy.deepcopy(samples)
            noisy[-1][sensor] += .31
            self.assertFalse(estabilidad(noisy)['ready'])

    def test_stability_minimum_count_and_empty(self):
        self.assertFalse(estabilidad([])['ready'])
        samples = [{'t': i*.1, 'vernier': 25, 'lm35': 25} for i in range(5)]
        self.assertTrue(estabilidad(samples)['ready'])
        self.assertFalse(estabilidad(samples[:4])['ready'])
        samples[-1]['lm35'] = 25.3
        self.assertTrue(estabilidad(samples)['ready'])

    def test_bad_stability_samples(self):
        for s in ([{'t': 0, 'lm35': 25}],
                  [{'t': 0, 'lm35': 25, 'vernier': 25}]*5,
                  [{'t': 0, 'lm35': float('nan'), 'vernier': 25}]):
            with self.subTest(s=s), self.assertRaises(ValueError):
                estabilidad(s)
        with self.assertRaises(ValueError):
            estabilidad([], window_seconds=0)

    def test_progress_goal_and_order(self):
        self.assertEqual(progreso_estatico([]),
                         {'count': 0, 'span_c': 0., 'incremental': True, 'meets_goal': False})
        points = [{'vernier': 50 + 50*i/19} for i in range(20)]
        self.assertTrue(progreso_estatico(points)['meets_goal'])
        self.assertEqual(progreso_estatico(points)['span_c'], 50)
        self.assertFalse(progreso_estatico(points[:-1])['meets_goal'])
        self.assertFalse(progreso_estatico(points[::-1])['incremental'])
        self.assertFalse(progreso_estatico(points + [{'vernier': 103}])['meets_goal'])
        self.assertFalse(progreso_estatico([{'vernier': 5}]*20)['incremental'])
        with self.assertRaises(ValueError):
            progreso_estatico([{'vernier': None}])


class DynamicTests(unittest.TestCase):
    def test_heating_cooling_and_initial_offset(self):
        for cooling in (False, True):
            with self.subTest(cooling=cooling):
                t, y, x0, xf = transient(cooling)
                r = calibracion_dinamica(t, y, x0, xf)
                self.assertAlmostEqual(r['k'], 1.2, delta=.001)
                self.assertAlmostEqual(r['tau'], 4, delta=.01)
                self.assertEqual(r['y0'], 1.2*x0+2)
                self.assertAlmostEqual(r['fraccion_tau'], 1-math.exp(-1))
                self.assertAlmostEqual(r['nivel_tau'], r['y0']+(r['yf']-r['y0'])*r['fraccion_tau'])
                self.assertNotAlmostEqual(r['fraccion_tau'], .637, places=4)

    def test_time_translation_and_relative_curves(self):
        a = calibracion_dinamica(*transient())
        b = calibracion_dinamica(*transient(offset=100), t0=100)
        self.assertAlmostEqual(a['tau'], b['tau'])
        self.assertEqual(b['t0'], 100)
        self.assertEqual(b['curvas']['escalon']['x'][0], 0)
        self.assertEqual(a['curvas']['escalon']['x'][-1], b['curvas']['escalon']['x'][-1])

    def test_irregular_times(self):
        t, _, x0, xf = transient()
        t = [u if u <= 0 else u+.03*math.sin(u) for u in t]
        y = [32 if u <= 0 else 32+36*(1-math.exp(-u/4)) for u in t]
        self.assertAlmostEqual(calibracion_dinamica(t, y, x0, xf)['tau'], 4, delta=.01)

    def test_curve_oracles(self):
        r = calibracion_dinamica(*transient())
        curves = r['curvas']
        self.assertEqual(set(curves), {'escalon', 'impulso', 'magnitud', 'fase'})
        self.assertEqual(curves['escalon']['y'][0], r['y0'])
        self.assertEqual(curves['impulso']['y'][0], r['k']/r['tau'])
        self.assertEqual(len(curves['escalon']['x']), 201)
        self.assertEqual(len(curves['magnitud']['x']), 121)
        self.assertAlmostEqual(curves['magnitud']['x'][60], 1/r['tau'])
        self.assertAlmostEqual(curves['magnitud']['y'][60], r['k']/math.sqrt(2))
        self.assertAlmostEqual(curves['fase']['y'][60], -45)
        self.assertEqual(curves['magnitud']['x'], curves['fase']['x'])
        for curve in curves.values():
            self.assertEqual(len(curve['x']), len(curve['y']))
            self.assertTrue(all(a < b for a, b in zip(curve['x'], curve['x'][1:])))

    def test_no_initial_plateau(self):
        t, y, x0, xf = transient()
        with self.assertRaises(ValueError):
            calibracion_dinamica(t[4:], y[4:], x0, xf)
        y[0] += 1
        with self.assertRaises(ValueError):
            calibracion_dinamica(t, y, x0, xf)

    def test_no_final_plateau_or_insufficient_duration(self):
        t, y, x0, xf = transient()
        ramp = [32 if u <= 0 else 32+u for u in t]
        for times, values in ((t, ramp), (t[:10], y[:10])):
            with self.subTest(n=len(times)), self.assertRaises(ValueError):
                calibracion_dinamica(times, values, x0, xf)

    def test_final_minimum_samples_duration_configurable(self):
        t, y, x0, xf = transient()
        with self.assertRaises(ValueError):
            calibracion_dinamica(t, y, x0, xf, plateau_seconds=50)
        with self.assertRaises(ValueError):
            calibracion_dinamica(t, y, x0, xf, plateau_min_samples=500)
        self.assertGreater(calibracion_dinamica(t, y, x0, xf, plateau_seconds=3)['tau'], 0)

    def test_no_change_or_wrong_gain(self):
        t, y, x0, xf = transient()
        for values, a, b in ((y, x0, x0), ([32]*len(t), x0, xf),
                             (y, xf, x0), ([32 if u <= 0 else 32.1 for u in t], x0, xf)):
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                calibracion_dinamica(t, values, a, b)

    def test_no_post_start_crossing(self):
        t = [-4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6]
        y = [25, 25, 25, 25, 25.3] + [25.37]*6
        with self.assertRaises(ValueError):
            calibracion_dinamica(t, y, 25, 26)

    def test_zero_celsius_is_not_zero_input_step(self):
        t, y, _, _ = transient()
        self.assertGreater(calibracion_dinamica(t, [v-32 for v in y], 0, 30)['tau'], 0)

    def test_bad_times_numbers_and_options(self):
        t, y, a, b = transient()
        for times, values in ((t[::-1], y), ([0]*len(t), y), (t[:-1], y),
                              (t, [float('inf')]+y[1:])):
            with self.subTest(n=len(times)), self.assertRaises(ValueError):
                calibracion_dinamica(times, values, a, b)
        for kw in ({'plateau_seconds': 0}, {'plateau_min_samples': True},
                   {'plateau_fraction': 1}, {'initial_min_samples': 1}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                calibracion_dinamica(t, y, a, b, **kw)


class PurityTests(unittest.TestCase):
    def test_no_mutation_and_strict_json(self):
        t, y, x0, xf = transient()
        before = copy.deepcopy((t, y))
        outputs = [calibracion_dinamica(t, y, x0, xf), precision(y),
                   calibracion_estatica([1, 2, 3], [3, 5, 7]),
                   precision([-1, 1]), histeresis([1], [2], 0, 10)]
        self.assertEqual((t, y), before)
        json.dumps(outputs, allow_nan=False)


if __name__ == '__main__':
    unittest.main()
