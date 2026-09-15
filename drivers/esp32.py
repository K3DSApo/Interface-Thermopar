import json, math

def parse_frame(raw):
    if not isinstance(raw,(bytes,bytearray)) or len(raw)>512 or not raw.endswith(b'\n'): raise ValueError('trama invalida')
    try:d=json.loads(raw.decode('utf-8'))
    except Exception as e: raise ValueError('JSON invalido') from e
    req=('version','seq','t_ms','adc_raw','voltage_mv','status')
    if any(k not in d for k in req) or d['version']!=1 or not isinstance(d['seq'],int) or isinstance(d['seq'],bool) or d['status']!='ok': raise ValueError('trama incompatible')
    for k in ('t_ms','adc_raw','voltage_mv'):
        if not isinstance(d[k],(int,float)) or isinstance(d[k],bool) or not math.isfinite(d[k]): raise ValueError('numero invalido')
    return d

class ESP32:
    def __init__(self,port,baudrate=115200,serial_factory=None): self.port=port; self.baudrate=baudrate; self.factory=serial_factory; self.serial=None; self.seq=None
    def open(self):
        if self.factory is None:
            try:
                import serial
                self.serial=serial.Serial(self.port,self.baudrate,timeout=1)
            except Exception as e: raise RuntimeError('pyserial no disponible o puerto inaccesible') from e
        else:self.serial=self.factory(self.port,self.baudrate,timeout=1)
    def read(self):
        d=parse_frame(self.serial.read_until(b'\n'))
        if self.seq is not None and d['seq']<=self.seq: raise ValueError('secuencia repetida o reinicio')
        self.seq=d['seq']; return d
    def close(self):
        if self.serial:
            self.serial.close(); self.serial=None
