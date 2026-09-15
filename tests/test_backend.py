"""Pruebas de comportamiento; todos los datos/dispositivos son sintéticos."""
import csv
import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from sesiones import SessionManager, APIError
from almacenamiento import SessionStore
from servidor import create_server
from drivers.esp32 import parse_frame, ESP32
from drivers.vernier import Vernier


class Clock:
    def __init__(self): self.value = 0.0
    def __call__(self): return self.value


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.clock = Clock()
        self.maths = Mock()
        self.maths.evaluar_estabilidad.return_value = {
            'ready': True, 'reason': 'estable', 'n': 5, 'window_seconds': 5.0}
        self.maths.progreso_estatico.return_value = {
            'count': 0, 'span_c': 0, 'incremental': True, 'meets_goal': False}
        self.maths.precision.return_value = dict(n=5, media=25.0, s=0, s_m=0,
                                                rsd=0, cv=0, varianza=0)
        self.maths.calibracion_estatica.return_value = {'m': 1.0}
        self.maths.calibracion_dinamica.return_value = {'tau': 2.0, 'k': 1.0}
        self.manager = SessionManager(self.tmp.name, maths=self.maths, clock=self.clock)
        self.addCleanup(self.manager.stop)

    def samples(self, start=0, count=6):
        for i in range(count):
            self.clock.value = start + i * 0.5
            self.manager.record_sample(25.0, 25.0)

    def assert_api_error(self, status, action, *args):
        with self.assertRaises(APIError) as cm: action(*args)
        self.assertEqual(cm.exception.status, status)

    def test_initial_state_has_no_fictional_samples(self):
        state = self.manager.state()
        self.assertEqual(state['samples'], [])
        self.assertFalse(state['running'])
        self.assertEqual(state['connection']['esp32'], 'disconnected')
        self.assertIsNone(state['static_result'])

    def test_config_partial_and_invalid_are_atomic(self):
        self.manager.configure({'sample_interval': 0.1})
        old = self.manager.state()['config']
        self.assertEqual(old['demo_initial_c'], 25.0)
        for bad in ({'sample_interval': float('nan')}, {'sample_interval': 0},
                    {'mode': 'invalid'}, {'sample_interval': True}, {'unknown': 2}):
            self.assert_api_error(400, self.manager.configure, bad)
            self.assertEqual(self.manager.state()['config'], old)

    def test_mode_change_requires_reset(self):
        self.samples()
        self.assert_api_error(409, self.manager.configure, {'mode': 'real'})

    def test_point_rejects_missing_and_reused_data(self):
        self.assert_api_error(409, self.manager.capture_point)
        self.samples()
        state = self.manager.capture_point()
        self.assertEqual(state['points'][0]['index'], 1)
        self.assertEqual(state['points'][0]['precision']['n'], 5)
        self.assert_api_error(409, self.manager.capture_point)

    def test_unstable_window_never_adds_point(self):
        self.samples()
        self.maths.evaluar_estabilidad.return_value['ready'] = False
        self.assert_api_error(409, self.manager.capture_point)
        self.assertEqual(self.manager.state()['points'], [])

    def test_point_delegates_science(self):
        self.samples()
        self.manager.capture_point()
        self.samples(5)
        self.maths.precision.return_value['media'] = 30.0
        self.manager.capture_point()
        self.maths.calibracion_estatica.assert_called_once_with([25.0, 30.0], [25.0, 30.0])
        self.assertEqual(self.manager.state()['static_result'], {'m': 1.0})

    def test_export_keeps_full_history_and_reset_preserves_old(self):
        self.samples(count=610)
        state = self.manager.state()
        self.assertLess(len(state['samples']), 610)
        rows = list(csv.DictReader(io.StringIO(self.manager.export_csv())))
        self.assertEqual(len(rows), 610)
        self.assertEqual(rows[0]['mode'], 'demo')
        old_id = state['session_id']
        self.manager.reset()
        self.assertNotEqual(self.manager.state()['session_id'], old_id)
        self.assertEqual(self.manager.state()['samples'], [])
        saved = json.loads((Path(self.tmp.name)/old_id/'results.json').read_text())
        self.assertEqual(saved['sample_count'], 610)
        with (Path(self.tmp.name)/old_id/'samples.csv').open(encoding='utf-8', newline='') as saved_csv:
            self.assertEqual(len(list(csv.DictReader(saved_csv))), 610)

    def test_reset_storage_failure_keeps_session(self):
        self.samples()
        old = self.manager.state()['session_id']
        with patch.object(self.manager.store, 'save_results', side_effect=OSError('disco lleno')):
            self.assert_api_error(503, self.manager.reset)
        self.assertEqual(self.manager.state()['session_id'], old)
        self.assertEqual(len(self.manager.state()['samples']), 6)

    def test_record_failure_keeps_sample_in_memory_and_stops(self):
        with patch.object(self.manager.store, 'append_sample', side_effect=OSError('disco lleno')):
            with self.assertRaises(APIError): self.manager.record_sample(25, 25)
        self.assertEqual(len(self.manager.state()['samples']), 1)
        self.assertFalse(self.manager.state()['running'])
        self.assertIn('disco lleno', self.manager.state()['error'])

    def test_dynamic_requires_active_and_preserves_prehistory(self):
        self.assert_api_error(409, self.manager.dynamic_start, {'x0': 25, 'xf': 70})
        self.samples()
        self.manager.running = True  # acquisition substitute, no physical devices
        self.clock.value = 3.0
        state = self.manager.dynamic_start({'x0': 25, 'xf': 70})
        self.assertEqual(state['dynamic']['t0'], 3.0)
        self.assertEqual(state['config']['demo_target_c'], 70)
        self.assertTrue(all(s['t'] < 3 for s in state['dynamic']['samples']))
        self.samples(3.5)
        self.manager.dynamic_finish()
        args, kwargs = self.maths.calibracion_dinamica.call_args
        self.assertLess(args[0][0], kwargs['t0'])
        self.assertGreater(args[0][-1], kwargs['t0'])

    def test_stop_aborts_dynamic_and_is_idempotent(self):
        self.samples()
        self.manager.running = True
        self.clock.value = 3
        self.manager.dynamic_start({'x0': 25, 'xf': 70})
        self.manager.stop()
        self.manager.stop()
        self.assertFalse(self.manager.state()['dynamic']['active'])
        self.assertIn('abortado', self.manager.state()['error'])

    def test_real_failure_never_falls_back(self):
        self.manager.configure({'mode': 'real', 'port': 'COM999',
                                'vernier_device_name': 'NO_DEVICE', 'vernier_channel': 2})
        with patch('adquisicion.RealAcquisition.open', side_effect=RuntimeError('sin hardware')):
            self.assert_api_error(503, self.manager.start)
        state = self.manager.state()
        self.assertEqual(state['mode'], 'real')
        self.assertEqual(state['samples'], [])
        self.assertFalse(state['running'])
        self.assertEqual(state['connection']['vernier'], 'error')

    def test_dynamic_reset_requires_stop(self):
        self.manager.running = True
        self.assert_api_error(409, self.manager.reset)


class ProtocolTests(unittest.TestCase):
    def frame(self, **values):
        data = dict(version=1, seq=1, t_ms=500, adc_raw=300, voltage_mv=250, status='ok')
        data.update(values)
        return (json.dumps(data)+'\n').encode()

    def test_frame_and_malformed_inputs(self):
        self.assertEqual(parse_frame(self.frame())['voltage_mv'], 250)
        for value in (self.frame(version=2), self.frame(seq=True), self.frame(voltage_mv=float('nan')),
                      self.frame(status='error'), b'{}\n', self.frame()[:-1], b'x'*513):
            with self.assertRaises(ValueError): parse_frame(value)

    def test_serial_drops_no_duplicate_or_reboot_silently(self):
        port = Mock()
        port.read_until.side_effect = [self.frame(), self.frame()]
        driver = ESP32('COM4', 115200, serial_factory=Mock(return_value=port))
        driver.open()
        self.assertEqual(driver.read()['seq'], 1)
        with self.assertRaises(ValueError): driver.read()
        driver.close()
        port.close.assert_called_once()

    def test_vernier_selects_explicit_channel_and_clears_values(self):
        device = Mock()
        device.name = 'GDX TEST'
        sensor = Mock()
        sensor.sensor_units = '°C'
        sensor.sensor_description = 'Temperature'
        sensor.values = [25.5]
        sensor.sensor_number = 4
        device.list_sensors.return_value = {4: sensor}
        device.get_enabled_sensors.return_value = [sensor]
        sdk = Mock()
        sdk.list_devices.return_value = [device]
        driver = Vernier('usb', 'GDX TEST', 4, 0.5, sdk_factory=Mock(return_value=sdk))
        driver.open()
        device.enable_sensors.assert_called_once_with([4])
        device.start.assert_called_once_with(period=500)
        self.assertEqual(driver.read(), 25.5)
        sensor.clear.assert_called()
        driver.close()
        device.stop.assert_called_once()
        device.close.assert_called_once()
        sdk.quit.assert_called_once()

    def test_vernier_rejects_wrong_units_and_closes(self):
        device = Mock()
        device.name = 'GDX TEST'
        sensor = Mock(sensor_units='m/s')
        device.list_sensors.return_value = {4: sensor}
        sdk = Mock()
        sdk.list_devices.return_value = [device]
        driver = Vernier('usb', 'GDX TEST', 4, 0.5, sdk_factory=Mock(return_value=sdk))
        with self.assertRaises(RuntimeError): driver.open()
        driver.close()
        self.assertTrue(device.close.called)


class HTTPTests(SessionTests):
    # Reuse setup, not parent behavioral tests in this class (set below).
    def setUp(self):
        super().setUp()
        self.server = create_server(self.manager, port=0)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = 'http://127.0.0.1:%d' % self.server.server_port

    def request(self, path, data=None, raw=None):
        body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
        req = Request(self.url+path, data=body, headers={'Content-Type': 'application/json'})
        try: response = urlopen(req, timeout=2)
        except HTTPError as e: response = e
        with response: return response.status, response.read()

    def test_http_state_config_and_error(self):
        code, body = self.request('/api/state')
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)['samples'], [])
        self.assertEqual(self.request('/api/config', {'sample_interval': .1})[0], 200)
        for raw in (b'{', b'[]', b'{"sample_interval":NaN}'):
            code, body = self.request('/api/config', raw=raw)
            self.assertEqual(code, 400)
            self.assertIsInstance(json.loads(body)['error'], str)
        self.assertEqual(self.request('/api/point', {})[0], 409)

    def test_http_does_not_serve_sources(self):
        for path in ('/COORDINACION.md', '/../COORDINACION.md', '/%2e%2e/README.md'):
            self.assertEqual(self.request(path)[0], 404)


if __name__ == '__main__':
    unittest.main()
