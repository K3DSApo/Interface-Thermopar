import copy
import csv
import io
import math
import threading
import time
import uuid
from functools import wraps
from almacenamiento import SessionStore
import app.calculos as calculos


class APIError(Exception):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def synchronized(fn):
    @wraps(fn)
    def call(self, *args, **kwargs):
        with self._lock:
            return fn(self, *args, **kwargs)
    return call


class SessionManager:
    def __init__(self, data_dir, maths=None, clock=None):
        self._lock = threading.RLock()
        self._control = threading.RLock()
        self.store = SessionStore(data_dir)
        self.maths = maths or calculos
        self.clock = clock or time.monotonic
        self.acquisition = None
        self._new_session()

    def _new_session(self):
        self.start_utc = time.time()
        self._origin = self.clock()
        self.session_id = uuid.uuid4().hex
        self.samples_all, self.samples, self.points = [], [], []
        self.running = False
        self.error = None
        self.static_result = self.dynamic_result = None
        self._last_point_count = 0
        self.dynamic = {'active': False, 'x0': None, 'xf': None, 't0': None, 'samples': []}
        self.config = {'mode': 'demo', 'port': None, 'baudrate': 115200,
                       'sample_interval': .5, 'vernier_connection': 'usb',
                       'vernier_device_name': None, 'vernier_channel': None,
                       'demo_initial_c': 25., 'demo_target_c': 25.}
        self.connection = {'esp32': 'disconnected', 'vernier': 'disconnected'}

    def elapsed(self):
        return self.clock() - self._origin

    def _window(self):
        end = self.samples_all[-1]['t'] if self.samples_all else 0
        return [r for r in self.samples_all[-51:] if r['t'] >= end - 5.]

    @synchronized
    def state(self):
        stab = self.maths.evaluar_estabilidad(self._window()) if self.samples_all else {
            'ready': False, 'reason': 'Sin datos', 'n': 0, 'window_seconds': 0}
        capture_ready = (stab['ready'] and len(self.samples_all)-self._last_point_count >= 5
                         and len(self.points) < 20 and not self.dynamic['active'])
        return copy.deepcopy({'session_id': self.session_id, 'mode': self.config['mode'],
            'running': self.running, 'connection': self.connection, 'samples': self.samples,
            'points': self.points, 'static_result': self.static_result,
            'dynamic_result': self.dynamic_result, 'error': self.error, 'config': self.config,
            'dynamic': self.dynamic, 'stability': stab, 'capture_ready': capture_ready,
            'static_progress': self.maths.progreso_estatico(self.points),
            'session_started_utc': self.start_utc,
            'metadata': {'temperature_unit': '°C', 'time_unit': 's',
                         'time_origin': 'inicio de sesión', 'dynamic_input': 'declarada por operador',
                         'dynamic_curves': 'derivadas del modelo', 'hysteresis': 'NOT_RUN'}})

    @synchronized
    def configure(self, data):
        if not isinstance(data, dict) or any(k not in self.config for k in data):
            raise APIError(400, 'Configuración inválida')
        def normalized(key, value):
            return value or None if key in ('port', 'vernier_device_name') else value
        changed = {k for k, v in data.items()
                   if normalized(k, v) != normalized(k, self.config[k])}
        if self.running and changed - {'demo_target_c'}:
            raise APIError(409, 'Detenga la adquisición antes de cambiar la configuración')
        hardware = {'mode','port','baudrate','vernier_connection','vernier_device_name','vernier_channel'}
        if self.samples_all and changed & hardware:
            raise APIError(409, 'Cree una nueva sesión antes de cambiar hardware o modo')
        if self.dynamic['active'] and 'demo_target_c' in changed:
            raise APIError(409, 'Finalice el ensayo dinámico antes de cambiar el objetivo')
        c = {**self.config, **data}
        if c['mode'] not in ('demo','real') or c['vernier_connection'] not in ('usb','ble'):
            raise APIError(400, 'Modo o conexión inválidos')
        for key in ('sample_interval','demo_initial_c','demo_target_c'):
            value = c[key]
            if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value):
                raise APIError(400, 'Valor numérico inválido: '+key)
        if not .1 <= c['sample_interval'] <= 10:
            raise APIError(400, 'El intervalo debe estar entre 0.1 y 10 segundos')
        if isinstance(c['baudrate'], bool) or not isinstance(c['baudrate'], int) or c['baudrate'] <= 0:
            raise APIError(400, 'Baudrate inválido')
        ch = c['vernier_channel']
        if ch is not None and (isinstance(ch,bool) or not isinstance(ch,int) or ch < 0):
            raise APIError(400, 'Canal Vernier inválido')
        for key in ('port','vernier_device_name'):
            if c[key] is not None and not isinstance(c[key],str):
                raise APIError(400, 'Identificador inválido: '+key)
        self.config = c
        self.error = None
        return self.state()

    @synchronized
    def record_sample(self, vernier, lm35, t=None):
        t = self.elapsed() if t is None else t
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v)
               for v in (t,vernier,lm35)):
            raise APIError(400, 'Lectura no finita')
        if self.samples_all and t <= self.samples_all[-1]['t']:
            raise APIError(400, 'Tiempos no crecientes')
        row = {'session_id': self.session_id, 'mode': self.config['mode'],
               't': float(t), 'vernier': float(vernier), 'lm35': float(lm35)}
        self.samples_all.append(row)
        self.samples = self.samples_all[-500:]
        if self.dynamic['active']:
            self.dynamic['samples'].append(row)
        try:
            self.store.append_sample(row)
        except OSError as e:
            self.error = str(e)
            self.running = False
            raise APIError(503, str(e)) from e
        return self.state()

    @synchronized
    def publish(self, acquisition, vernier, lm35):
        if self.running and self.acquisition is acquisition:
            self.record_sample(vernier, lm35)

    @synchronized
    def acquisition_failed(self, acquisition, error):
        if self.acquisition is acquisition:
            self.running = False
            self.error = str(error)
            self.connection = {'esp32': 'error', 'vernier': 'error'}
            self.dynamic['active'] = False

    def _save(self):
        try:
            self.store.save_results(self.session_id, self.state(), self.samples_all)
        except OSError as e:
            self.error = str(e)
            raise APIError(503, str(e)) from e

    @synchronized
    def capture_point(self):
        if self.dynamic['active']:
            raise APIError(409, 'Finalice el ensayo dinámico antes de registrar puntos')
        if len(self.points) >= 20:
            raise APIError(409, 'Ya se registraron los 20 puntos de esta sesión')
        if len(self.samples_all)-self._last_point_count < 5:
            raise APIError(409, 'Muestras nuevas insuficientes')
        window = self._window()
        ev = self.maths.evaluar_estabilidad(window)
        if not ev['ready']:
            raise APIError(409, ev['reason'])
        vx = self.maths.precision([r['vernier'] for r in window])
        vy = self.maths.precision([r['lm35'] for r in window])
        if self.points and vx['media'] <= self.points[-1]['vernier']:
            raise APIError(409, 'El siguiente punto debe tener una temperatura Vernier mayor')
        point = {'index': len(self.points)+1, 'vernier': vx['media'], 'lm35': vy['media'],
                 'precision': vy, 'samples': copy.deepcopy(window)}
        candidate = self.points + [point]
        try:
            result = self.maths.calibracion_estatica([p['vernier'] for p in candidate],
                     [p['lm35'] for p in candidate]) if len(candidate) >= 2 else None
        except ValueError as e:
            raise APIError(409, str(e)) from e
        self.points = candidate
        self.static_result = result
        self._last_point_count = len(self.samples_all)
        self.error = None
        self._save()
        return self.state()

    def start(self):
        from adquisicion import DemoAcquisition, RealAcquisition
        with self._control:
            with self._lock:
                if self.running:
                    return self.state()
                old = self.acquisition
            if old:
                old.close()
            with self._lock:
                real = self.config['mode'] == 'real'
                self.acquisition = RealAcquisition(self) if real else DemoAcquisition(self)
                self.connection = dict.fromkeys(('esp32','vernier'), 'connecting' if real else 'simulated')
                try:
                    self.acquisition.open()
                except Exception as e:
                    self.acquisition.close()
                    self.connection = dict.fromkeys(('esp32','vernier'), 'error')
                    self.error = str(e)
                    raise APIError(503, str(e)) from e
                self.running = True
                self.error = None
                self.connection = dict.fromkeys(('esp32','vernier'), 'connected' if real else 'simulated')
                self.acquisition.start()
                return self.state()

    def stop(self):
        with self._control:
            with self._lock:
                self.running = False
                worker = self.acquisition
                if self.dynamic['active']:
                    self.dynamic['active'] = False
                    self.error = 'Ensayo dinámico abortado'
            if worker:
                worker.close()
            with self._lock:
                if self.connection['esp32'] != 'error':
                    self.connection = dict.fromkeys(('esp32','vernier'), 'disconnected')
                self._save()
                return self.state()

    @synchronized
    def dynamic_start(self, data):
        if not self.running:
            raise APIError(409, 'Adquisición inactiva')
        if self.dynamic['active']:
            raise APIError(409, 'Ya existe un ensayo dinámico activo')
        try:
            x0, xf = data['x0'], data['xf']
            if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v)
                   for v in (x0,xf)) or x0 == xf:
                raise ValueError()
        except (KeyError,TypeError,ValueError):
            raise APIError(400, 'x0 y xf deben ser temperaturas finitas y diferentes')
        window = self._window()
        if not window or not self.maths.evaluar_estabilidad(window)['ready']:
            raise APIError(409, 'Espere una ventana inicial estable')
        self.dynamic_result = None
        self.dynamic = {'active': True, 'x0': float(x0), 'xf': float(xf),
                        't0': self.elapsed(), 'samples': copy.deepcopy(window)}
        if self.config['mode'] == 'demo':
            self.config['demo_target_c'] = float(xf)
        self.error = None
        return self.state()

    @synchronized
    def dynamic_finish(self):
        if not self.dynamic['active']:
            raise APIError(409, 'Ensayo dinámico inactivo')
        d = self.dynamic
        rows = d['samples']
        try:
            result = self.maths.calibracion_dinamica([r['t'] for r in rows],
                [r['lm35'] for r in rows], d['x0'], d['xf'], t0=d['t0'])
        except ValueError as e:
            raise APIError(409, str(e)) from e
        self.dynamic_result = result
        d['active'] = False
        self.error = None
        self._save()
        return self.state()

    @synchronized
    def export_csv(self):
        out = io.StringIO()
        w = csv.DictWriter(out, fieldnames=['session_id','mode','t','vernier','lm35'])
        w.writeheader()
        w.writerows(self.samples_all)
        return out.getvalue()

    def reset(self):
        with self._control:
            with self._lock:
                if self.running:
                    raise APIError(409, 'Detenga la adquisición antes de crear otra sesión')
                self._save()
                old = self.acquisition
            if old:
                old.close()
            with self._lock:
                self.acquisition = None
                self._new_session()
                return self.state()
