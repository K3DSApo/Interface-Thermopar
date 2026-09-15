"""Aceptación HTTP independiente; solo demo sintética y stdlib.

Ejecutar: python3 -B -m unittest discover -s tests -p test_acceptance.py -v
No importa módulos de implementación ni abre sensores. El servidor se lanza
con la CLI pública documentada en docs/backend.md, en un puerto loopback libre.
Los datos temporales permanecen dentro del proyecto y se eliminan al terminar.
Windows, hardware, veinte niveles reales e IEEE/Canva quedan fuera de esta suite.
"""

import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, ProxyHandler


ROOT = Path(__file__).resolve().parents[1]
# Capturados durante la auditoría de solo lectura, antes de implementación.
# COORDINACION es mutable por integración y no forma parte de estas fuentes.
SOURCE_HASHES = {
    '01_Documentación/Calibración de LM35 y termopar.md':
        '316f834ca32c4884e5eef2e796bc7dc99214908280b9d2827ea363a6e102863f',
    '01_Documentación/Cálculos y calibración del LM35.md':
        '8c2d093a6efd06684fe6da4c280970bb28f8f7e56a0cbedee80bf14b35e564d2',
    '01_Documentación/Drivers Vernier Go Direct.md':
        '22587a39ebf241d4b56e4824637798f29f7a2c4a567b1f101a31956507e8f691',
    '01_Documentación/goal.md':
        'be9ccb019b2966ff21e504abbfcf255d3b32e7d0ba42d6247f35bb58ecff2ecc',
    '01_Documentación/fuentes/Clinical_Measurements_completo.md':
        'd97c5c56e872b8c4ddf699e9e5f269834233f08abe15410d13bca83da88c3833',
    '02_Interfaz/interfaz_calibracion_LM35_v3.html':
        'f6d95928b33c9179f3861ec91fab51780946b1ecbbf468218edf8ffc2f89fb5a',
}


def reject_constant(value):
    raise ValueError('Número JSON no finito: ' + value)


class ProtectedSourcesAcceptance(unittest.TestCase):
    def test_original_sources_are_byte_identical(self):
        for name, expected in SOURCE_HASHES.items():
            with self.subTest(source=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(),
                                 expected, 'Fuente protegida modificada')


class DemoAPIAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / 'app/main.py').is_file():
            raise unittest.SkipTest('BLOCKED/NOT_RUN: falta app/main.py; API/demo pendiente')
        cls.temp = tempfile.TemporaryDirectory(prefix='.acceptance-', dir=ROOT)
        cls.addClassCleanup(cls.temp.cleanup)
        cls.data_dir = Path(cls.temp.name) / 'sesiones de prueba á'
        cls.log = open(Path(cls.temp.name) / 'server.log', 'w+b')
        cls.addClassCleanup(cls.log.close)
        cls.opener = build_opener(ProxyHandler({}))
        launcher = (
            'from servidor import create_server; '
            'from sesiones import SessionManager; '
            'import sys; '
            's=create_server(SessionManager(sys.argv[1]), 0); '
            'print("PORT="+str(s.server_port), flush=True); '
            's.serve_forever()'
        )
        cls.process = subprocess.Popen(
            [sys.executable, '-B', '-c', launcher, str(cls.data_dir)], cwd=ROOT,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
            stdout=subprocess.PIPE, stderr=cls.log, text=True,
        )
        cls.addClassCleanup(cls.stop_server)
        try:
            line = cls.process.stdout.readline().strip()
        except (OSError, ValueError):
            line = ''
        if line.startswith('PORT='):
            cls.base = f'http://127.0.0.1:{line.split("=", 1)[1]}'
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and hasattr(cls, 'base'):
            if cls.process.poll() is not None:
                break
            try:
                with cls.opener.open(cls.base + '/api/state', timeout=0.5) as res:
                    if res.status == 200:
                        return
            except (URLError, TimeoutError, OSError):
                pass
            time.sleep(0.1)
        cls.log.flush()
        cls.log.seek(0)
        diagnostic = cls.log.read().decode('utf-8', errors='replace')[-4000:]
        raise AssertionError('Servidor no disponible en 8 s; API NOT_RUN\n' + diagnostic)

    @classmethod
    def stop_server(cls):
        if cls.process.poll() is None:
            cls.process.terminate()
            try:
                cls.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.process.kill()
                cls.process.wait(timeout=5)

    def request(self, path, body=None, expected=200, raw=False):
        payload = None if body is None else json.dumps(body, allow_nan=False).encode()
        req = Request(self.base + path, data=payload,
                      headers={'Content-Type': 'application/json'})
        try:
            response = self.opener.open(req, timeout=3)
        except HTTPError as error:
            response = error
        with response:
            status, content = response.code, response.read()
        accepted = (expected,) if isinstance(expected, int) else expected
        self.assertIn(status, accepted, (path, status, content[:500]))
        if raw:
            return content.decode('utf-8-sig')
        result = json.loads(content, parse_constant=reject_constant)
        if status >= 400:
            self.assertIsInstance(result.get('error'), str)
            self.assertTrue(result['error'])
        return result

    def setUp(self):
        self.request('/api/stop', {})
        self.request('/api/reset', {})
        self.request('/api/config', {'mode': 'demo', 'sample_interval': 0.1,
                                    'demo_initial_c': 25, 'demo_target_c': 25})

    def tearDown(self):
        self.request('/api/stop', {})

    def wait_state(self, predicate, timeout=8):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            state = self.request('/api/state')
            if predicate(state):
                return state
            time.sleep(0.1)
        self.fail(f'No se alcanzó condición demo en {timeout} s; último estado: '
                  f'{state.get("stability")}, muestras={len(state.get("samples", []))}')

    def start_stable(self):
        self.request('/api/start', {})
        return self.wait_state(lambda s: s['stability']['ready'] and
                               len(s['samples']) >= 5)

    def test_initial_state_and_rejections_without_data(self):
        state = self.request('/api/state')
        for key in ('mode', 'running', 'connection', 'samples', 'points',
                    'static_result', 'dynamic_result', 'error', 'config',
                    'session_id', 'dynamic', 'stability', 'static_progress'):
            self.assertIn(key, state)
        self.assertEqual(state['mode'], 'demo')
        self.assertIs(state['running'], False)
        self.assertEqual(state['samples'], [])
        self.assertEqual(state['points'], [])
        self.assertIsNone(state['static_result'])
        self.assertIsNone(state['dynamic_result'])
        self.assertFalse(state['static_progress']['meets_goal'])
        self.request('/api/point', {}, expected=(400, 409))
        self.request('/api/dynamic/finish', {}, expected=(400, 409))
        self.request('/api/dynamic/start', {'x0': 25, 'xf': 40}, expected=(400, 409))
        self.assertEqual(self.request('/api/state')['points'], [])

    def test_configuration_validation_is_atomic_and_partial(self):
        before = self.request('/api/state')['config']
        for change in ({'sample_interval': 0}, {'sample_interval': 11},
                       {'mode': 'inventado'}, {'vernier_connection': 'inventado'}):
            with self.subTest(change=change):
                self.request('/api/config', change, expected=400)
                self.assertEqual(self.request('/api/state')['config'], before)
        after = self.request('/api/config', {'demo_target_c': 30})
        self.assertEqual(after['config']['demo_target_c'], 30)
        self.assertEqual(after['config']['sample_interval'], before['sample_interval'])

    def test_real_mode_never_falls_back_to_demo(self):
        """Sin hardware, real debe fallar o permanecer sin muestras sintéticas."""
        self.request('/api/config', {
            'mode': 'real', 'port': 'puerto-no-conectado',
            'baudrate': 115200, 'sample_interval': 0.1,
            'vernier_connection': 'usb',
        })
        self.request('/api/start', {}, expected=(200, 400, 409, 503))
        state = self.request('/api/state')
        self.assertEqual(state.get('mode'), 'real')
        self.assertEqual(state.get('samples'), [],
                         'real desconectado no debe inventar muestras')
        self.assertFalse(state.get('running'))
        connection = state.get('connection') or {}
        self.assertNotIn('simulated', connection.values())

    def test_continuous_demo_idempotent_start_stop_and_no_active_reset(self):
        first = self.start_stable()
        session = first['session_id']
        repeated = self.request('/api/start', {})
        self.assertEqual(repeated['session_id'], session)
        self.request('/api/reset', {}, expected=409)
        later = self.wait_state(lambda s: len(s['samples']) >= len(first['samples']) + 3)
        times = [row['t'] for row in later['samples']]
        self.assertTrue(all(a < b for a, b in zip(times, times[1:])))
        for row in later['samples']:
            self.assertTrue(all(math.isfinite(row[k]) for k in ('t', 'vernier', 'lm35')))
        self.assertEqual(later['mode'], 'demo')
        self.assertEqual(later['connection']['esp32'], 'simulated')
        self.assertEqual(later['connection']['vernier'], 'simulated')
        stopped = self.request('/api/stop', {})
        self.assertFalse(stopped['running'])
        self.request('/api/stop', {})
        time.sleep(0.35)
        self.assertEqual(self.request('/api/state')['samples'], stopped['samples'])

    def test_point_uses_repetitions_and_rejects_reused_window(self):
        self.start_stable()
        point_state = self.request('/api/point', {})
        self.assertEqual(len(point_state['points']), 1)
        point = point_state['points'][0]
        self.assertEqual(point['index'], 1)
        precision = point['precision']
        self.assertGreaterEqual(precision['n'], 5)
        self.assertAlmostEqual(point['lm35'], precision['media'])
        self.assertAlmostEqual(precision['varianza'], precision['s'] ** 2)
        self.assertAlmostEqual(precision['s_m'], precision['s'] / math.sqrt(precision['n']))
        self.assertAlmostEqual(precision['cv'], precision['rsd'] * 100)
        # Freeze acquisition so this negative case cannot race five new samples.
        self.request('/api/stop', {})
        self.request('/api/point', {}, expected=(400, 409))
        self.assertEqual(len(self.request('/api/state')['points']), 1)

    def test_export_and_reset_preserve_archived_session(self):
        self.start_stable()
        stopped = self.request('/api/stop', {})
        rows = list(csv.DictReader(io.StringIO(self.request('/api/export', raw=True))))
        self.assertEqual(len(rows), len(stopped['samples']))
        for raw, sample in zip(rows, stopped['samples']):
            self.assertEqual(raw['session_id'], stopped['session_id'])
            self.assertEqual(raw['mode'], 'demo')
            for key in ('t', 'vernier', 'lm35'):
                self.assertAlmostEqual(float(raw[key]), sample[key], places=6)
        results = self.request('/api/results')
        self.assertIsInstance(results, dict)
        self.assertIn(stopped['session_id'], json.dumps(results))
        fresh = self.request('/api/reset', {})
        self.assertNotEqual(fresh['session_id'], stopped['session_id'])
        self.assertEqual(fresh['samples'], [])
        # Format-neutral: find archived CSV/JSON content, not an internal layout.
        archived = [p.read_bytes() for p in self.data_dir.rglob('*') if p.is_file()]
        self.assertTrue(any(stopped['session_id'].encode() in b for b in archived),
                        'La sesión anterior no aparece en los archivos persistidos')
        old_files = {p: p.read_bytes() for p in self.data_dir.rglob('*')
                     if p.is_file() and stopped['session_id'].encode() in p.read_bytes()}
        self.request('/api/reset', {})
        for path, content in old_files.items():
            self.assertEqual(path.read_bytes(), content, 'Reset sobrescribió sesión anterior')

    def test_dynamic_requires_data_and_stop_aborts(self):
        self.start_stable()
        active = self.request('/api/dynamic/start', {'x0': 25, 'xf': 40})
        self.assertTrue(active['dynamic']['active'])
        self.assertGreaterEqual(active['dynamic']['t0'], 0)
        self.assertEqual(active['dynamic']['x0'], 25)
        self.assertEqual(active['dynamic']['xf'], 40)
        self.request('/api/dynamic/finish', {}, expected=(400, 409))
        changed = self.wait_state(lambda s: s['samples'][-1]['vernier'] > 30)
        self.assertEqual(changed['mode'], 'demo')
        stopped = self.request('/api/stop', {})
        self.assertFalse(stopped['dynamic']['active'])
        self.assertIsNone(stopped['dynamic_result'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
