"""Regresiones de integración con datos y dispositivos sintéticos."""
import math
import tempfile
import threading
import time
import unittest
from urllib.request import urlopen
from unittest.mock import patch
from sesiones import SessionManager, APIError
from servidor import create_server


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.now = 100.
        self.m = SessionManager(self.tmp.name, clock=lambda: self.now)
        self.addCleanup(self.m.stop)

    def samples(self, value, start, count=12):
        for i in range(count):
            self.now = start + i * .5
            self.m.record_sample(value, value)

    def test_browser_script_is_served(self):
        server = create_server(self.m, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        with urlopen(f'http://127.0.0.1:{server.server_port}/app.js') as r:
            self.assertIn('javascript', r.headers['Content-Type'])
            self.assertIn(b'buildPlots', r.read())

    def test_empty_hardware_fields_do_not_force_reset(self):
        self.samples(25, 100)
        state=self.m.configure({'port':'','vernier_device_name':'','sample_interval':1.})
        self.assertEqual(state['config']['sample_interval'],1.)

    def test_times_are_relative_to_session(self):
        self.now = 102.
        self.m.record_sample(25, 25)
        self.assertEqual(self.m.state()['samples'][0]['t'], 2.)

    def test_rejected_point_does_not_change_results(self):
        self.samples(25, 100)
        self.m.capture_point()
        self.samples(25, 106)
        with self.assertRaises(APIError):
            self.m.capture_point()
        self.assertEqual(len(self.m.state()['points']), 1)

    def test_capture_and_indicator_use_same_window(self):
        self.samples(25, 100)
        self.now += .5
        self.m.record_sample(26, 26)
        for _ in range(5):
            self.now += .5
            self.m.record_sample(25, 25)
        self.assertFalse(self.m.state()['stability']['ready'])
        with self.assertRaises(APIError): self.m.capture_point()

    def test_dynamic_requires_stable_start_and_finish_can_retry(self):
        self.m.running = True
        with self.assertRaises(APIError): self.m.dynamic_start({'x0':25,'xf':55})
        self.samples(25, 100)
        self.now += .1
        self.m.dynamic_start({'x0':25,'xf':55})
        with self.assertRaises(APIError): self.m.dynamic_finish()
        self.assertTrue(self.m.state()['dynamic']['active'])

    def test_stopped_session_persists_results(self):
        self.samples(25, 100)
        self.m.capture_point()
        self.m.stop()
        self.assertTrue((self.m.store.root / self.m.session_id / 'results.json').exists())

    def test_real_worker_records_and_disconnects_without_demo(self):
        class Serial:
            def __init__(self,*args): pass
            def open(self): pass
            def read(self):
                time.sleep(.01)
                return {'voltage_mv':260}
            def close(self): pass
        class Reference(Serial):
            def read(self): return 25.5
        self.m = SessionManager(self.tmp.name)
        self.addCleanup(self.m.stop)
        self.m.configure({'mode':'real','port':'COM_TEST','vernier_device_name':'TEST',
                          'vernier_channel':1,'sample_interval':.1})
        with patch('adquisicion.ESP32',Serial), patch('adquisicion.Vernier',Reference):
            self.m.start()
            deadline=time.monotonic()+2
            while time.monotonic()<deadline and not self.m.state()['samples']: time.sleep(.02)
            self.m.stop()
        rows=self.m.state()['samples']
        self.assertTrue(rows)
        self.assertEqual((rows[0]['vernier'],rows[0]['lm35'],rows[0]['mode']),(25.5,26.,'real'))
        self.assertEqual(self.m.state()['connection']['esp32'],'disconnected')

class CompleteFlowTests(unittest.TestCase):
    def test_twenty_levels_dynamic_and_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            clock=[0.]
            m=SessionManager(directory,clock=lambda:clock[0])
            for level in range(20):
                reference=25+50*level/19
                for _ in range(12):
                    clock[0]+=.5
                    m.record_sample(reference,1.02*reference+.4)
                m.capture_point()
            state=m.state()
            self.assertTrue(state['static_progress']['meets_goal'])
            self.assertAlmostEqual(state['static_result']['m'],1.02)
            self.assertAlmostEqual(state['static_result']['b'],.4)
            with self.assertRaises(APIError): m.capture_point()
            m.reset()
            for _ in range(12):
                clock[0]+=.5
                m.record_sample(25,25)
            m.running=True
            m.dynamic_start({'x0':25,'xf':55})
            for i in range(1,101):
                clock[0]+=.5
                m.record_sample(55,25+30*(1-math.exp(-i*.5/4)))
            result=m.dynamic_finish()['dynamic_result']
            self.assertAlmostEqual(result['tau'],4,delta=.03)
            self.assertAlmostEqual(result['k'],1,delta=.001)
            m.stop()
            self.assertTrue((m.store.root/m.session_id/'results.json').exists())


if __name__=='__main__': unittest.main()
