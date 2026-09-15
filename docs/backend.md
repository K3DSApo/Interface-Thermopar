# Backend MVP — contrato de integración builder

Implementación en curso (2026-09-15). Windows y hardware: NOT_RUN.

## Auxiliares solicitadas a calculos.py

El builder no implementa fórmulas científicas. Necesita estas funciones públicas;
se adaptarán a nombres equivalentes publicados por researcher en docs/calculos.md:

- `evaluar_estabilidad(samples, ...)` → `{ready,reason,n,window_seconds}`; últimos
  cinco segundos, al menos cinco pares, excursión ≤0.3 °C en ambos sensores.
- `progreso_estatico(points)` → `{count,span_c,incremental,meets_goal}`; 20 puntos
  ascendentes y span ≥50 °C.
- `lm35_desde_mv(voltage_mv)` → temperatura °C nominal.
- `simular_paso(y_anterior, objetivo, dt, tau=...)` → nueva salida sintética de
  primer orden. Si no existe, se requiere una función pública equivalente para
  generar demo continua sin duplicar ecuaciones en adquisición.

Se usan además `precision`, `calibracion_estatica` y `calibracion_dinamica`
del contrato. Para media Vernier se toma `precision(valores)['media']`.
Dinámica recibe ventana previa y segmento completo con tiempos de sesión y t0.

## API y ejecución pública

`python -m app.main --port 8765 --data-dir sesiones` y
`python servidor.py --port 8765` (compatibilidad). Bind exclusivo 127.0.0.1.
La aplicación servirá app/web/index.html sin modificar esa frontera.

Las pruebas de backend se ejecutarán con
`python -m unittest discover -s tests -p test_backend.py -v`.
Se documentará aquí el resultado RED/GREEN real, no mediciones de sensores.
