# Interface Thermopar — calibración LM35 con referencia Vernier

MVP local para adquirir, visualizar y analizar la calibración estática y dinámica de un LM35 frente a una referencia Vernier. El criterio del proyecto es `01_Documentación/goal.md`.

## Estado del MVP

**Verificado en Windows:** pruebas Python/JavaScript, interfaz en navegador, modo demo, API local, captura estática, ensayo dinámico, persistencia y exportación. Los dispositivos de las pruebas automatizadas son sintéticos.

**Pendiente / NOT_RUN:** ESP32 y Vernier físicos, adquisición simultánea validada con hardware, 20 mediciones físicas, calibración experimental, reporte IEEE y presentación Canva.

El modo `real` no cambia automáticamente a demo. Si falta hardware o una dependencia, devuelve un error y conserva el modo real.

## Ejecución en Windows

Requisito: Python 3.11 o posterior instalado con el lanzador `py`.

1. Abre PowerShell o el Explorador en la carpeta del proyecto.
2. Ejecuta uno de estos lanzadores:

```powershell
.\scripts\ejecutar_windows.ps1
```

Si la política local no permite ejecutar el archivo, usa:

```bat
scripts\ejecutar_windows.cmd
```

3. Abre en el navegador:

```text
http://127.0.0.1:8765/
```

El servidor escucha únicamente en `127.0.0.1`; para detenerlo usa `Ctrl+C` en la consola.

## Modo demo

El inicio se hace en modo `demo`, marcado explícitamente como simulado. No representa mediciones reales.

Permite comprobar:

- adquisición continua sintética;
- registro de puntos estables;
- resultados estáticos;
- ensayo dinámico con condición inicial distinta de cero;
- gráficas generadas desde resultados del backend;
- exportación de datos de la sesión.

## Uso de la interfaz

- **En vivo:** Iniciar, esperar una ventana estable y Registrar punto. Las temperaturas y conexiones se actualizan cada 500 ms.
- **Demo:** en Configuración, cambiar Objetivo demo para pasar al siguiente nivel. Registrar hasta 20 niveles ascendentes con un intervalo total de al menos 50 °C.
- **Estática:** consultar la tabla, seleccionar un nivel para su precisión y revisar calibración lineal, inexactitud, intervalos y Bland–Altman.
- **Dinámica:** con adquisición activa y temperatura estable, indicar x0/xf e iniciar. En demo se aplica el cambio simulado; en real lo aplica el operador. Esperar la meseta final y pulsar Finalizar y calcular. Si aún no hay meseta, el ensayo sigue activo y puede reintentarse.
- **Exportación:** CSV y JSON desde En vivo, PNG debajo de cada gráfica. Detener guarda los resultados. Nueva sesión conserva la anterior en `sesiones/`.

## Arquitectura

```text
LM35 → ESP32 → serial ──┐
                        ├─ aplicación Python local → interfaz web
Vernier → USB/BLE ──────┘
```

- `app/calculos.py`: única fuente de fórmulas y series de gráficas.
- `sesiones.py`: estado, reglas de sesión y orquestación; no contiene fórmulas científicas.
- `adquisicion.py`: demo y frontera de adquisición real.
- `drivers/`: adaptadores ESP32/Vernier.
- `servidor.py`: API HTTP local y recursos web.
- `app/web/`: interfaz basada visualmente en el HTML original, sin cálculo científico en JavaScript.

## Modo real: requisitos antes de usarlo

No se debe seleccionar modo real sin confirmar:

- puerto COM y formato del ESP32;
- nombre exacto, transporte y canal del dispositivo Vernier;
- unidades de temperatura;
- dependencias opcionales de comunicación (`pyserial`, `godirect` y las que el dispositivo requiera).

El firmware de referencia está en `firmware/esp32_lm35/`, pero **no se ha flasheado ni validado con una placa**.

## Cálculos incluidos

- media, desviación estándar, desviación estándar de la media, RSD, CV y varianza;
- regresión lineal, `m`, `b`, `r`, error de ganancia, error de corrimiento e inexactitud `σP`;
- Bland–Altman;
- histéresis cuando existan ambos recorridos;
- sistema de primer orden: `K`, `τ`, escalón, impulso y respuesta en frecuencia.

Las respuestas de impulso y frecuencia se derivan del modelo; no se presentan como mediciones directas.

## Pruebas verificadas

Desde la raíz del proyecto en Windows:

```bash
py -3 -B -m unittest discover -s tests -v
node --test pruebas/frontend/test_frontend.cjs
```

La suite automatizada verifica cálculos, persistencia, API HTTP, rechazo honesto del modo real, interfaz, fuentes protegidas y exportación. Las pruebas sintéticas no sustituyen los ensayos con hardware.

## Fuentes del proyecto

- Rúbrica: `01_Documentación/goal.md`
- Cálculos y procedimiento: `01_Documentación/Cálculos y calibración del LM35.md`
- Drivers: `01_Documentación/Drivers Vernier Go Direct.md`
- Material docente: `01_Documentación/fuentes/Clinical_Measurements_completo.md`
- Prototipo visual preservado: `02_Interfaz/interfaz_calibracion_LM35_v3.html`
