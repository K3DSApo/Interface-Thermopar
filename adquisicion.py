import threading
import time
from drivers.esp32 import ESP32
from drivers.vernier import Vernier


class DemoAcquisition:
    def __init__(self, manager):
        self.m = manager
        self.stop_event = threading.Event()
        self.thread = None
        self.current = manager.samples_all[-1]['lm35'] if manager.samples_all else manager.config['demo_initial_c']

    def open(self):
        pass

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        try:
            while not self.stop_event.wait(self.m.config['sample_interval']):
                if not self.m.running:
                    break
                target = self.m.config['demo_target_c']
                self.current += (target-self.current)*.2
                self.m.publish(self, self.current, self.current)
        except Exception as e:
            self.m.acquisition_failed(self, e)

    def close(self):
        self.stop_event.set()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=3)


class RealAcquisition(DemoAcquisition):
    def open(self):
        c = self.m.config
        if not c['port'] or not c['vernier_device_name'] or c['vernier_channel'] is None:
            raise RuntimeError('Configure puerto, nombre del dispositivo Vernier y canal')
        self.esp = ESP32(c['port'], c['baudrate'])
        self.vernier = Vernier(c['vernier_connection'], c['vernier_device_name'],
                               c['vernier_channel'], c['sample_interval'])
        try:
            self.esp.open()
            self.vernier.open()
        except Exception:
            self._close_devices()
            raise

    def _close_devices(self):
        for name in ('esp','vernier'):
            device = getattr(self, name, None)
            if device:
                try:
                    device.close()
                except Exception:
                    pass

    def run(self):
        try:
            while not self.stop_event.is_set() and self.m.running:
                began = time.monotonic()
                frame = self.esp.read()
                reference = self.vernier.read()
                if self.stop_event.is_set():
                    break
                self.m.publish(self, reference, self.m.maths.voltage_mv_a_lm35(frame['voltage_mv']))
                if self.stop_event.wait(max(0., self.m.config['sample_interval'] - (time.monotonic()-began))):
                    break
        except Exception as e:
            if not self.stop_event.is_set():
                self.m.acquisition_failed(self, e)
        finally:
            self._close_devices()

    def close(self):
        self.stop_event.set()
        self._close_devices()
        super().close()
