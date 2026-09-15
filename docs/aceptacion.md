# Matriz y plan de aceptación

Fecha: 2026-09-15. Estado: especificación documental; ninguna prueba funcional ejecutada en esta tarea.

## Criterio de evidencia

Referencias C/G/M/P/V/H e identificadores AR remiten a [arquitectura.md](arquitectura.md). Se leyó el contrato y todas las fuentes locales antes de escribir estos documentos. La inspección de HTML fue textual; no se abrió navegador ni se ejecutó JavaScript.

- PASS: existe ejecución reproducible con resultado esperado y evidencia identificada.
- FAIL: una ejecución o inspección aplicable demuestra incumplimiento; identificar cuál de ambas.
- NOT_RUN: escenario no ejecutado; nunca se interpreta como aprobado.
- BLOCKED: falta una decisión o recurso para ejecutar un criterio determinado; conservar la causa.

Aquí los casos funcionales están NOT_RUN. Las discrepancias del HTML son hallazgos de inspección, no fallos de una suite ejecutada. No se crearon `tests/test_acceptance.py` ni pruebas RED/GREEN porque el usuario pidió documentación sin implementación. En la futura implementación C exige registrar primero el fallo esperado y después el paso; ausencia de código por sí sola no constituye una ejecución RED.

## Matriz A–E

| Inciso | Puntos | Criterio verificable | Evidencia necesaria para aprobar | Estado actual |
|---|---:|---|---|---|
| A — Automatización | 35 | Computadora conectada a ambos sensores, adquisición, parámetros y gráficas actualizados automáticamente | Windows objetivo, dispositivos/canales identificados, crudos con tiempos, demostración de controles y errores, actualización sin recargar | NOT_RUN; hardware y software operativo no verificados |
| B — Estática | 15 | 20 mediciones interpretadas como niveles con repeticiones; recorrido incremental y amplitud medida >=50 °C; precisión, exactitud, certeza, e_G, e_0 y Bland–Altman con discusión | Sesión real, ventanas estables trazables, resultados recalculables, 20 pares de medias Vernier/LM35, interpretación de concordancia y supuestos | NOT_RUN; estabilidad, rango final y certeza pendientes |
| C — Dinámica | 15 | Primer orden, condición inicial no cero, tau, impulso, escalón y frecuencia | Entrada escalón documentada, salida medida con mesetas, t0, K/tau y curvas derivadas correctamente identificadas | NOT_RUN; algoritmo/segmentación y experimento pendientes |
| D — Reporte IEEE | 20 | Máximo 4 páginas, doble columna y secciones del curso | Archivo final revisado y políticas del curso para cotejo | NOT_RUN; documento y políticas no presentes |
| E — Canva | 15 | Diseño del experimento, resultados y conclusiones individuales | Presentación en Canva y revisión de contenido/procedencia | NOT_RUN; presentación no presente |

G indica demostración presencial el viernes 18 de septiembre, 09:00–11:00, laboratorio. La auditoría no verifica disponibilidad del prototipo ni sustituye esa evaluación. Un MVP demo no aprueba A–C experimentalmente y no resuelve D/E.

## Casos numéricos propuestos

Todos los vectores siguientes son **sintéticos de prueba**. No son mediciones del LM35. Los oráculos se derivan de las fórmulas locales, no del HTML. Propuesta de comparación para casos algebraicos bien condicionados: tolerancia absoluta/relativa 1e-9; tau interpolada tendrá tolerancia explícita dependiente del paso temporal y del estimador de meseta, sin presentarla como incertidumbre experimental.

| ID | Entrada / acción | Resultado esperado | Dependencia |
|---|---|---|---|
| N01 | precision([1,2,3]) | n=3, media=2, s=1, s_m=1/sqrt(3), rsd=0.5, cv=50, varianza=1 | C; P p.14 |
| N02 | precision([-1,0,1]); precision([5,5]) | Primera: media=0, rsd/cv=null, s=1. Segunda: dispersión cero, n=2 | C |
| N03 | Vacío, una muestra, NaN/Inf o datos no numéricos | Rechazo explícito; nunca JSON con NaN/Infinity ni coerción silenciosa de texto | C; cierre AR-08 |
| N04 | Estática x=[10,20,30], y=[21,41,61] | m=2, b=1, r=1, e_g=1, e_0=1, corregidas=x, sigma_P=0, intervalos cero | C; M §§9–17 |
| N05 | En N04, Bland–Altman de datos sin corregir | medias=[15.5,30.5,45.5], diferencias=[11,21,31], sesgo=21, límites=1.4 y 40.6 | M §19; AR-08 |
| N06 | x=[1,2,3], y=[2,1,0] | m=-1, b=3, r=-1; conservar correlación negativa | C; discrepancia P p.17 |
| N07 | Estática x=[1,2,3], y=[2,5,5] | m=1.5, b=1, corregidas=[2/3,8/3,8/3], sigma_P=sqrt(2)/3; intervalos múltiplos correspondientes | M §16; evita validar solo rectas perfectas |
| N08 | Arrays desiguales, x constante, y constante, pendiente cero | Resultado completo rechazado con causa; política definitiva antes de fijar excepción exacta | BLOCKED AR-08 |
| N09 | Dinámica sintética: x0=20, xf=60, y0=25, yf=65, t0=7 s, tau=4 s; salida exponencial con prehistoria y meseta suficientes | K≈1; fraccion_tau=1-exp(-1); nivel_tau≈50.284822; cruce absoluto≈11 s, tau≈4 s. El offset 5 °C no altera K incremental | C; AR-05/06/07 |
| N10 | N09 con escalón descendente x0=60, xf=20, y0=65, yf=25 | K≈1, tau positiva, umbral en descenso detectado; no exigir aumento de y | Algoritmo por cerrar |
| N11 | Desplazar todos los tiempos y t0 por +100 s | Mismos K/tau y forma relativa; se desplaza el instante absoluto del cruce | C |
| N12 | Sin meseta final, sin cruce, tiempos duplicados/decrecientes, xf=x0, salida plana, NaN/Inf, t0 sin cobertura suficiente | Rechazo explícito sin parámetros inventados; distinguir datos inválidos de ensayo todavía insuficiente en API | C; AR-05/06 |
| N13 | Curvas con K=1, tau=4; comparar en tiempos/frecuencias acordados | Escalón parte de y0; impulso en tiempo relativo 0 vale 0.25 s⁻¹; en omega=0.25 rad/s magnitud=1/sqrt(2), fase=-45°. Arrays x/y pareados y finitos | C; dominio/malla por cerrar |
| N14 | Histéresis asc=[10,20], desc=[11,18], salida_min=0, salida_max=100 | [1,2]%; datos faltantes rechazan; rango cero/invertido requiere rechazo acordado | C; P p.16 |

Para N09–N13, especificar cuánto dura cada meseta, qué ruido se acepta y cómo se estima y0/yf antes de convertir el caso en prueba ejecutable. Un transitorio truncado no puede usarse como meseta final solo por ser la última muestra. No ajustar tolerancias a posteriori para hacer pasar una implementación.

## API y sesiones: escenarios propuestos

Todas las rutas se prueban en 127.0.0.1 y deben producir JSON válido salvo CSV de exportación. Se cotejan claves de C, tipos, null cuando corresponde y consistencia entre la respuesta de una acción y el siguiente state. Las extensiones propuestas en AR requieren acuerdo previo.

| ID | Ruta / secuencia | Evidencia y condición de aceptación |
|---|---|---|
| A01 | GET /api/state al abrir | mode/running/connection/samples/points/static_result/dynamic_result/error/config presentes; sin resultados o conexiones ficticias |
| A02 | GET /api/ports sin hardware | ports es lista de cadenas; vacía si no hay puertos, sin COM4 inventado |
| A03 | POST /api/config válido e inválido | Persistir y devolver configuración efectiva; rechazar tipos/rangos inválidos. Acordar campos demo, segundos y política durante running antes de probar |
| A04 | Configurar demo, POST /api/start, observar varios períodos, POST /api/stop | samples crece con el tiempo sin pulsar punto; stop detiene crecimiento; iniciar de nuevo no duplica trabajadores. Variar objetivo/escalón cambia datos futuros, no resultados precargados |
| A05 | Configurar real sin dependencia o sensor; POST /api/start | Error claro 503 según propuesta; ningún fallback a demo ni muestras sintéticas; identidad de modo conservada |
| A06 | POST /api/point sin datos, con datos antiguos/inestables, y con ventana válida | Sin punto en casos inválidos; ventana válida produce medias y precisión de múltiples repeticiones, con vínculo a sus crudos. No reutilizar ventana como nivel nuevo sin política explícita |
| A07 | Completar 20 niveles demo, luego probar 19 niveles y amplitud <50 °C | Solo el caso completo satisface control de cantidad/amplitud; etiquetar siempre sintético. Recalcular resultados desde exportación. La política para >20 niveles debe documentarse |
| A08 | POST /api/dynamic/start {x0,xf}, adquirir, POST /api/dynamic/finish | t0/ventana previa/segmento preservados; cálculo solo del ensayo correspondiente; parámetros no contaminados por un ensayo anterior |
| A09 | Finish sin start; start dinámico doble; cambiar config durante ensayo | Rechazo 409 propuesto sin corrupción; behavior definitivo requiere AR-13 |
| A10 | GET /api/export y GET /api/results | CSV UTF-8 con crudos y unidades inequívocas; JSON con resultados y metadatos suficientes para reproducirlos. Comparar contra muestras archivadas, no solo la ventana visible |
| A11 | POST /api/reset tras sesión con datos; repetir con fallo de escritura | Éxito crea sesión diferente y conserva original. Fallo informa y no destruye sesión. Verificar recuperación de la anterior; ruta y esquema pendientes AR-10 |
| A12 | Dos solicitudes de punto/reset/stop en concurrencia | Snapshot coherente y sin duplicados accidentales, mezcla de sesiones o escrituras parciales; política de serialización documentada |
| A13 | JSON roto, valores ausentes, endpoint incorrecto, cálculo inválido | 400/409/503 con {error:string} según caso acordado; 404 para ruta desconocida por proponer. Sin éxito aparente ni traceback como respuesta de usuario |
| A14 | Desconectar uno de los sensores durante real | Cesa generación de pares válidos; error/conexión actualizados; no repetir última lectura como nueva, no usar demo; conservar historial con tiempos |

## Interfaz y presentación

| ID | Comprobación | Aceptación |
|---|---|---|
| U01 | Comparación visual con H en navegador | Rosa, tarjetas, navegación y adaptación a ventana estrecha conservadas; controles conectados con API |
| U02 | Polling durante adquisición y error HTTP | Consulta nominal cada 500 ms sin refrescar documento; error visible; evitar respuestas antiguas sobrescribiendo estado nuevo |
| U03 | Datos presentados vs API | Mismas series/valores con redondeo solo visual; sin cálculo científico ni generación de señales en JS. Transformación de coordenadas de dibujo permitida |
| U04 | Estática | Precisión por nivel, sigma_P, intervalos y supuestos; m/b/r/e_G/e_0; tabla, curva de ajuste y Bland–Altman con sesgo/límites. Ausencia de 1−std y porcentajes de exactitud inventados |
| U05 | Dinámica | Condición inicial no cero, t0/tau distinguibles, nota 63.7% de fuente frente a valor exacto usado; impulso/frecuencia etiquetados derivados; rad/s y grados coherentes |
| U06 | Demo, real desconectado e histéresis ausente | Etiquetas explícitas; datos ausentes no se muestran como cero. Histéresis NOT_RUN si falta recorrido descendente; imágenes sintéticas no rotuladas como medición experimental |

## Plataforma y conservación

| ID | Verificación futura | Criterio |
|---|---|---|
| W01 | Inicio limpio en Windows con Python 3.11+ | Entorno local, rutas con espacios/acentos, pathlib y UTF-8; alternativa .cmd; sin cambios globales de política PowerShell |
| W02 | Demo sin dependencias de hardware ni internet | UI y backend operativos localmente; ninguna importación hardware obligatoria impide demo |
| W03 | Exposición y cierre | Escucha solo 127.0.0.1, cierre libera puerto/dispositivos; sin servicio persistente ni apertura pública |
| W04 | Hardware objetivo | Registrar equipo/Windows/Python/driver, transporte/canal/unidad, ADC y trama firmware; capturas reales con timestamps. No flashear firmware en esta tarea |
| W05 | Fuentes y sesiones | Fuentes protegidas intactas; datos fuera de ellas; anteriores no sobrescritos; configuración/metadatos acompañan cada sesión |

## Registro real de esta entrega

Se ejecutaron únicamente lecturas e inspecciones locales (`pwd`, inventario con `rg`, lectura completa por tramos, `git status --short` y SHA-256), creación de los dos documentos y comprobaciones documentales. No hubo adquisición, servidor, navegador, suite de pruebas ni ejecución Windows. No se asigna PASS funcional a ningún caso anterior.

## Ajustes de aceptación tras la adenda concurrente

Se releyó completo C al detectar un cambio durante el cierre. La actualización de arquitectura identifica los puntos resueltos. **Las precisiones siguientes prevalecen sobre los escenarios iniciales cuando difieren.** Ninguno pasa a PASS por haberse especificado.

- N09–N12/A06/A08: usar ventana inicial de 5 s con >=5 pares y amplitud <=0.3 °C en ambos sensores; >=5 muestras nuevas por punto. El tramo final dinámico debe tener >=5 muestras, >=2 s y excursión <=max(0.3 °C,1% del cambio); cruce con interpolación lineal y tiempo relativo a t0. Incluir pruebas a ambos lados de esos límites; persiste la definición de cambio insignificante y selección exacta de tramo.
- A01/A08/U05: cotejar además session_id, dynamic:{active,x0,xf,t0,samples}, stability:{ready,reason,n,window_seconds} y static_progress:{count,span_c,incremental,meets_goal}. `t` es relativo al inicio de sesión; x de curvas temporales es relativo al escalón. Conservar UTC de inicio y referencias reales declaradas como tales.
- A03: cambios parciales; período en segundos, default 0.5 y rango 0.1–10; pendiente resolver `interval` frente a `sample_interval`. Modo/hardware solo detenido y sin muestras. Demo inicia con 25 °C y admite demo_target_c durante adquisición. Real exige nombre/dispositivo, canal y transporte usb/ble explícitos.
- A04/A09/A11: start/stop son idempotentes; stop aborta ensayo activo; **reset requiere detenido**. Intentarlo durante adquisición debe rechazarse, no detener automáticamente como proponía la auditoría inicial. Falla de guardado conserva estado.
- A07: ciclo base con máximo 20 puntos ascendentes; rechazar el punto adicional según error acordado. Histéresis NOT_RUN sin descenso ya es decisión vigente, no vacío bloqueante del MVP.
- A10/W05: CSV con session_id,mode,t,vernier,lm35; results incluye configuración, metadatos, puntos, resultados y validación. Ensayar exportación mayor al buffer visible para comprobar que no se truncaron crudos científicos.
- A14/U06: connection solo disconnected/connecting/connected/simulated/error; detectar obsolescencia sin inventar ceros. Umbral de obsolescencia y sincronización siguen pendientes.
- W01–W04: puerto por defecto 8765, raíz web app/web/index.html; scripts resuelven su raíz; trama MCU version=1,seq,t_ms,adc_raw,voltage_mv,status; verificar conversión nominal desde voltage_mv en calculos.py y advertencia ADC/montaje. Nada de esto acredita hardware sin ejecución.

Verificación documental: los dos archivos se leyeron como UTF-8 y sus enlaces locales resolvieron dentro del proyecto. La primera invocación `python` no estaba disponible; la comprobación se ejecutó correctamente con `python3`. Los hashes de fuentes y HTML coincidieron; el cambio ajeno en C se incorporó a la auditoría, sin sobrescribirlo.

## Condiciones para una futura aceptación

1. Cerrar por escrito los vacíos del contrato identificados en arquitectura; conservar decisiones y parámetros junto a las pruebas.
2. Ejecutar casos numéricos, API, frontend y conservación con evidencia RED/GREEN conforme a C, sin resultados hardcodeados.
3. Distinguir resultados Linux/offline de Windows/hardware: cada entorno debe tener su registro propio, con NOT_RUN donde falte ejecución.
4. Para aceptar B/C experimentalmente, adjuntar datos reales reproducibles y análisis; para aceptar A–E completos, incluir además Windows/prototipo presencial, IEEE y Canva.

El bloqueo de hardware no debe ocultarse con una demo aprobada. Las propuestas de contrato de esta entrega son revisables y no modifican COORDINACION.md.
