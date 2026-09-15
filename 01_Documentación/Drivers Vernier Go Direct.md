---
title: Drivers Vernier Go Direct
type: referencia-tecnica
status: estable
project: Calibración de LM35 y termopar
---

# Drivers Vernier Go Direct

Este documento contiene exclusivamente la información estable del driver Vernier y sus enlaces oficiales. Los cambios en cálculos, métricas o requisitos del proyecto no deben modificarlo.

## Enlaces oficiales

- PyPI `godirect`: <https://pypi.org/project/godirect/>
- Biblioteca fuente `godirect-py`: <https://github.com/VernierST/godirect-py>
- Ejemplos oficiales: <https://github.com/VernierST/godirect-examples>
- Guía Python: <https://raw.githubusercontent.com/VernierST/godirect-examples/main/python/readme.md>
- Información del dispositivo: <https://raw.githubusercontent.com/VernierST/godirect-examples/main/python/gdx_getting_started_device_info.py>
- Múltiples dispositivos: <https://raw.githubusercontent.com/VernierST/godirect-examples/main/python/gdx_getting_started_two_devices.py>

## Biblioteca y transportes

`godirect` es la biblioteca Python de Vernier para sensores Go Direct mediante:

- USB;
- Bluetooth Low Energy (BLE).

Dependencias principales:

- `hidapi` para USB HID;
- `bleak` para BLE.

Instalación documentada:

```bash
pip install godirect
```

La biblioteca base no instala automáticamente la utilidad `gdx` de los ejemplos.

## Repositorios

`godirect-py` contiene el código fuente de la biblioteca principal.

`godirect-examples` contiene ejemplos Python, JavaScript y Web VPython. Para este proyecto interesa `python/`, que incluye ejemplos USB/BLE, descubrimiento de dispositivos, selección de canales, lectura, exportación, uso directo de `godirect`, utilidad `gdx` y la regla Linux `vstlibusb.rules`.

## Flujo de comunicación

```text
Python 3
  ↓
godirect / gdx
  ↓
descubrimiento del dispositivo
  ↓
apertura USB o BLE
  ↓
identificación y selección de canales
  ↓
inicio del muestreo
  ↓
lectura de valores
  ↓
detención y cierre
```

Flujo simplificado con `gdx`:

```python
from gdx import gdx

sensor = gdx.gdx()
sensor.open(connection='usb')
sensor.select_sensors()
sensor.start(1000)
lecturas = sensor.read()
sensor.stop()
sensor.close()
```

Funciones principales: `open()`, `select_sensors()`, `start(period)`, `read()`, `stop()` y `close()`.

Para mayor control se puede usar directamente:

```python
from godirect import GoDirect
```

La decisión entre `gdx` y `godirect` directo se tomará después de una prueba mínima.

## Descubrimiento de dispositivo y canal

No se debe adivinar el canal térmico. Primero se deben registrar:

- nombre y descripción del dispositivo;
- número de canal;
- descripción del sensor;
- unidades;
- batería y estado;
- RSSI en BLE;
- canales incompatibles.

El canal puede no comenzar en 1 ni ser consecutivo. La configuración final debe conservar el canal confirmado y sus unidades.

## USB en Linux

La guía puede requerir:

```bash
sudo apt install libusb1.0.0
sudo apt install libudev-dev
```

Y la regla:

```text
vstlibusb.rules
```

en:

```text
/etc/udev/rules.d/
```

Instalar paquetes o modificar reglas `udev` son cambios persistentes y administrativos; no se realizarán automáticamente.

## Bluetooth Low Energy

`godirect` usa `bleak` para BLE nativo. También conserva soporte heredado para `vernierpygatt` y el dongle Bluegiga.

Se recomienda seleccionar el dispositivo por nombre exacto:

```text
connection='ble'
device_to_open='NOMBRE_EXACTO_DEL_DISPOSITIVO'
```

No se usará inicialmente `proximity_pairing`, para evitar conectar otro dispositivo cercano.

## Integración con el proyecto

```text
Vernier Go Direct → USB/BLE → adaptador Python → T_ref
LM35 → ESP32 → Serial/USB → adaptador Python → T_LM35
                                      ↓
                            sincronización en Python
```

El adaptador Vernier debe entregar como mínimo:

```text
timestamp_pc
vernier_device_name
sensor_channel
sensor_description
sensor_units
temperature_value
connection
battery_or_status
```

El adaptador solo manejará comunicación y adquisición. No contendrá regresión, `sigma_P`, Bland–Altman ni el modelo dinámico.

## Límite respecto al termopar

`godirect` es para dispositivos Vernier Go Direct compatibles; no es un driver genérico para cualquier termopar.

```text
Sonda Vernier Go Direct → godirect/gdx → Python
Termopar convencional → acondicionamiento y compensación → ESP32 → Python
```

No se debe conectar un termopar directamente al ADC del ESP32 sin acondicionamiento, compensación de unión fría y protección.

## Prueba mínima futura

1. Confirmar Python 3.
2. Crear o seleccionar un entorno virtual.
3. Verificar `godirect` dentro del entorno.
4. Conectar el dispositivo por USB o BLE.
5. Ejecutar el ejemplo de información del dispositivo.
6. Registrar nombre, modelo, canales y unidades.
7. Leer brevemente el canal térmico confirmado.
8. Verificar unidades y timestamps.
9. Cerrar correctamente.

Esta prueba no constituye la calibración del LM35.

## Estado de esta referencia

- Biblioteca identificada: `godirect` / `godirect-py`.
- Transportes: USB y BLE.
- Modelo físico: pendiente de confirmar.
- Canal térmico: pendiente de confirmar.
- Instalación en el equipo: no verificada.
- Comunicación en este proyecto: no probada.

## Bitácora

- **2026-09-13:** referencia de drivers separada del documento de cálculos para conservarla estable.
