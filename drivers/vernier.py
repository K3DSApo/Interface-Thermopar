class Vernier:
    def __init__(self,connection,device_name,channel,sample_interval,sdk_factory=None): self.connection=connection; self.name=device_name; self.channel=channel; self.interval=sample_interval; self.factory=sdk_factory; self.sdk=self.device=self.sensor=None
    def open(self):
        try:
            if self.factory:self.sdk=self.factory()
            else:
                from godirect import GoDirect; self.sdk=GoDirect(use_ble=self.connection=='ble',use_usb=self.connection=='usb')
            devices=self.sdk.list_devices(); self.device=next(d for d in devices if d.name==self.name); self.device.open(); sensors=self.device.list_sensors(); self.sensor=sensors[self.channel]; units=getattr(self.sensor,'sensor_units','')
            if 'c' not in units.lower(): raise RuntimeError('canal Vernier no es temperatura')
            self.device.enable_sensors([self.channel]); self.sensor.clear(); self.device.start(period=int(self.interval*1000))
        except Exception as e:
            self.close(); raise RuntimeError('Vernier no disponible: '+str(e)) from e
    def read(self):
        if not self.device.read(): raise RuntimeError('lectura Vernier fallida')
        if not self.sensor.values: raise RuntimeError('sin lectura Vernier')
        value = self.sensor.values[-1]
        self.sensor.clear()
        return value
    def close(self):
        if self.device:
            try:self.device.stop()
            except Exception:pass
            try:self.device.close()
            except Exception:pass
        if self.sdk:
            try:self.sdk.quit()
            except Exception:pass

        self.device = self.sdk = self.sensor = None
