# Auditoría frontend — propuesta de cambios mínimos

Fecha: 2026-09-15. Estado: auditoría documental terminada; implementación pendiente por instrucción expresa del usuario.

## Alcance y fuentes

`pwd` confirmó `/srv/k3ds-server/data/projects/Calibracion-LM35-termopar`. Toda la actividad se limitó a ese directorio. Único archivo creado por esta auditoría: `docs/frontend.md`. No se modificaron fuentes, código, pruebas ni contrato; no se hicieron commits, push, cambios de rama ni administración de agentes.

Se leyeron completos:

- [COORDINACION.md](../COORDINACION.md): fronteras, contrato inicial y aceptación del MVP.
- [Índice del proyecto](../01_Documentación/Calibración%20de%20LM35%20y%20termopar.md).
- [goal.md](../01_Documentación/goal.md): rúbrica A–E.
- [Drivers Vernier Go Direct](../01_Documentación/Drivers%20Vernier%20Go%20Direct.md): transportes, identificación y pendientes de hardware.
- [Cálculos y calibración del LM35](../01_Documentación/Cálculos%20y%20calibración%20del%20LM35.md): requisitos de representación y métricas.
- [Clinical Measurements completo](../01_Documentación/fuentes/Clinical_Measurements_completo.md): transcripción de las 34 páginas; especialmente 7, 14–20 y 28–30.
- [HTML original](../02_Interfaz/interfaz_calibracion_LM35_v3.html): estilos, estructura y script íntegros.

Las referencias a líneas siguientes corresponden al HTML original. Las observaciones evalúan su coherencia con las fuentes locales; no constituyen una validación externa del driver ni de hardware. La instrucción actual «No implementes todavía» delimita esta entrega aunque COORDINACION autorice una fase posterior de implementación.

## Dictamen

La estética se puede conservar: paleta rosa y morada, fondo claro, marca T°, Segoe UI, navegación lateral de cuatro secciones, tarjetas redondeadas, fórmulas oscuras y canvas sin dependencias externas. La capa de datos necesita sustituirse: el prototipo contiene cifras fijas, conexiones aparentes y series calculadas en JavaScript. Todavía no consume la API.

El principal riesgo funcional es presentar como adquisición o resultado experimental lo que solo es una ilustración. El principal desacuerdo científico está en las tarjetas de precisión, exactitud y certeza. Ambos se pueden corregir reutilizando los contenedores existentes.

## Mapa de cambios mínimos

Todos los cambios de implementación descritos son futuros y se limitarían a `app/web/*`, con pruebas en `tests/test_frontend.py`. Se propone `app/web/index.html` como copia de trabajo, más `app/web/styles.css` y `app/web/app.js` si separar las capas facilita revisión; estas rutas todavía no se crean.

| Zona / evidencia | Hallazgo | Cambio mínimo propuesto |
|---|---|---|
| Estilos, líneas 7–23 | Base visual coherente y sin CDN. | Conservar colores, tamaños, tarjetas y navegación. Añadir únicamente estilos de formulario, foco, error, deshabilitado y ausencia de datos. |
| Conexiones y progreso, 36–37 | COM4, USB, puntos verdes y 7/20 son constantes. | Enlazar a `connection`, `config` y `points`; distinguir simulación, desconexión y conexión confirmada. Contar puntos aceptados, sin confundirlos con muestras crudas. |
| Acciones, 42, 132–133 | «Conectar sensores» no tiene manejador; pausa y demo solo cambian texto. | Configuración accesible desde «Conectar sensores»; inicio y detención por API. Mostrar estado confirmado por servidor y bloquear doble envío mientras responde. |
| Banner, badges y pie, 43, 50, 57, 85, 126 | Modo demo fijo; etiqueta LIVE sin adquisición. | Mostrar modo y estado reales del backend. Demo siempre «Datos simulados»; respuestas del modelo «Derivadas del modelo». Sin muestras: «Sin datos». |
| En vivo, 45–51 | Temperaturas fijas; faltan captura, sesión y descarga. | Renderizar última muestra y series recibidas. Incorporar botones discretos «Registrar punto», «Nueva sesión», «Exportar CSV» y «Resultados JSON», reutilizando `.btn`. |
| Métricas estáticas, 59–70 | Errores y porcentajes arbitrarios, incluyendo `1 − std(...)`; faltan las medidas de precisión solicitadas. | Reutilizar `.metrics` para `n`, media, `s`, `s_m`, RSD, CV y varianza del punto seleccionado. Usar σP para inexactitud y los tres intervalos del backend para certeza provisional. |
| Calibración lineal, 73–78 | m, b, r, eG, e₀, σP son fijos. No hay gráfica patrón–resultado ni tabla de puntos. | Enlazar valores a `static_result`; añadir una tarjeta con dispersión de `points` y `curva_ajuste`, y una tabla de medias por nivel. Reutilizar estilos existentes. |
| Bland–Altman, 78, 148, 157, 163 | Une puntos con líneas y omite sesgo y límites de concordancia. | Dibujar dispersión de `medias` y `diferencias`, más líneas y valores `sesgo`, `limite_inferior`, `limite_superior` enviados por backend. |
| Histéresis, ausente | Fuentes piden ambos recorridos o NOT_RUN; la API no los representa. | Nota «Histéresis: NOT_RUN — sin ambos recorridos» mientras no existan datos y contrato; gráfica pendiente de extensión acordada. |
| Resumen dinámico, 87–118 | Parámetros fijos y contenido adicional: polo, ceros y frecuencia de corte. | Conservar tarjetas para K, τ, condiciones inicial/final y modelo. Retirar indicadores extra y sustituciones numéricas fijas; resumir la tabla con los resultados solicitados por C. |
| Obtención de τ, 98–100, 152, 158 | Usa 0.637 y marca τ sobre una curva artificial; no considera t0 de sesión. | Mostrar `nivel_tau`, `fraccion_tau`, `t0`, `y0`, `yf`, `tau`; explicar la diferencia entre 63.7 % de la fuente y `1-exp(-1)` del contrato. Acordar eje temporal antes de posicionar el marcador. |
| Inicio/fin dinámico, ausente | No hay entrada x0/xf ni delimitación del ensayo. | Añadir dos campos con unidad °C y botones «Iniciar ensayo» / «Finalizar y calcular» que usen las rutas dinámicas. No estimar parámetros en el navegador. |
| Impulso, escalón y frecuencia, 102–108, 155–156 | El navegador genera las respuestas. | Consumir las cuatro series de `dynamic_result.curvas`; conservar canvas y fórmulas simbólicas, distinguiendo entrada x0/xf de salida y0/yf. |
| Configuración, 122–124 | Son spans de solo lectura. `.card` hereda span 6 dentro de una cuadrícula de dos columnas. | Convertir datos editables a controles con etiquetas: modo, puerto, baudrate, intervalo y conexión Vernier. Sobrescribir el span para `.config > .card` y añadir opciones demo cuando se documenten. |
| Renderizador, 135–166 | Rangos fijos, línea para toda serie, dibujo de paneles ocultos y ausencia de estado vacío. | Conservar geometría y colores; añadir dispersión, rangos constantes/vacíos, redibujo del panel visible y escala logarítmica rotulada como ω [rad/s]. |

### Ajustes de accesibilidad y adaptación

- Conservar botones nativos y añadir indicación accesible de sección activa y relaciones con paneles.
- Añadir `label` a controles y mensajes de error asociados; región de estado accesible sin anunciar cada muestra a 500 ms.
- Dar a los canvas nombre y resumen textual o tabla accesible. Los puntos de conexión deben acompañarse de texto, además del color.
- Proponer ajuste de línea en `.actions`, una columna de métricas en pantallas estrechas y desplazamiento horizontal solo en tablas/fórmulas. Revisar también barra lateral en ventanas bajas.
- Son observaciones del código: el desbordamiento y la apariencia final requieren comprobación en navegador; no se realizaron capturas ni mediciones de contraste.

## Mapa de consumo de API vigente

| Acción / presentación | Contrato actual | Conducta propuesta |
|---|---|---|
| Carga y actualización | `GET /api/state` | Sondeo nominal cada 500 ms, sin recarga del documento ni solicitudes de estado solapadas; conservar pestaña y edición de formularios. |
| Puertos | `GET /api/ports` → `{ports:[string]}` | Selector con datos recibidos; lista vacía explícita, sin COM4 predeterminado ficticio. |
| Guardar configuración | `POST /api/config {mode,port,baudrate,sample_interval,vernier_connection}` | Validación de forma y campos obligatorios; reglas y rangos definitivos del backend. Actualizar desde state devuelto. |
| Iniciar / detener | `POST /api/start {}` / `POST /api/stop {}` | Botones derivados de `running`. Confirmar si stop equivale a pausa que puede reanudarse en la misma sesión. |
| Registrar nivel | `POST /api/point {}` | Incorporar únicamente el punto devuelto; errores por falta de datos o estabilidad se muestran sin inventar una captura. |
| Ensayo dinámico | `POST /api/dynamic/start {x0,xf}` / `POST /api/dynamic/finish {}` | El servidor marca inicio y calcula el segmento; no usar reloj local para medir τ. |
| Nueva sesión | `POST /api/reset {}` | Vaciar presentación según respuesta del servidor; preservar datos anteriores es responsabilidad del backend. |
| Descargas | `GET /api/export` / `GET /api/results` | Descargar CSV crudo y JSON con metadatos; indicar fallo HTTP, sin reconstruir resultados científicos desde el DOM. |
| Errores | HTTP 400/409/503 `{error:string}` y `state.error` | Mostrar mensaje mediante texto, conservar entradas y no anunciar éxito. Si falla comunicación, marcar datos previos como históricos/sin actualización. Nunca cambiar real a demo automáticamente. |

JavaScript solo manejaría interacción, formateo, asociación de arrays y dibujo: escalas, ticks y coordenadas son presentación. Regresión, precisión, límites Bland–Altman, estabilidad, correcciones y generación de curvas pertenecen al backend. No convertir `null` en cero. Un cero recibido y válido debe seguir mostrándose como cero.

Para evitar que una respuesta vieja de sondeo reponga datos después de reset/configuración, se propone invalidar lecturas pendientes al ejecutar una mutación, serializar acciones y reconciliar con el state devuelto. No depende de agregar una ruta nueva.

## Observaciones de contrato y bloqueos de integración

Estas son propuestas para revisión del contrato inicial; no amplían unilateralmente la API ni implican que otros roles hayan aceptado cambios.

| ID / prioridad | Ambigüedad o ausencia | Propuesta concreta y efecto mientras esté pendiente |
|---|---|---|
| C1 / necesaria | `config:obj` no fija unidades, rangos, defaults ni enums. Faltan campos demo para temperatura objetivo/escalón. | Documentar `sample_interval` con unidad y límites, valores de `vernier_connection`, y nombres/tipos de campos demo. Bloquea cerrar el formulario y controlar demo desde UI. No inventar nombres como contrato aceptado. |
| C2 / necesaria | `points[].precision` carece de esquema anidado y sensor al que corresponde; `index` no fija base. | Acordar si es el objeto de `precision(valores)` para LM35 y cómo se representa Vernier si se incluye; índice inicial y orden. Mostrar precisión por nivel, nunca sobre todas las temperaturas mezcladas. |
| C3 / necesaria para estado estable | `/api/point` exige ventana estable, pero state no expone disponibilidad, criterio ni estabilidad por punto. | Documentar número de muestras y criterio en backend; proponer estado de captura con disponibilidad/motivo y estabilidad por punto. Mientras tanto mostrar «Estabilidad no informada» y presentar el error del endpoint; no calcularla en JS ni anunciar «estable». |
| C4 / necesaria para dinámica | `running` solo describe adquisición; falta ensayo activo, x0/xf persistidos, t0 antes de finalizar y límites del segmento. | Proponer metadatos del ensayo con estado, entradas y comienzo/fin, incluyendo recuperación tras recargar. Precisar si `samples` contiene sesión completa o ventana. Bloquea reconstruir de forma fiable el transitorio y controles después de recarga. |
| C5 / necesaria para ejes | `samples[].t` y los x de curvas temporales no fijan origen; las x de frecuencia necesitan quedar explícitas como ω sin transformar. | Acordar segundos desde sesión o desde escalón y relación con t0. Preferir que backend entregue segmento y marcador listos para graficar. Si eje es de sesión, cruce en t0+τ; si es relativo al escalón, cruce en τ. Etiqueta τ sigue siendo duración. Magnitud con ω en rad/s y fase en grados. |
| C6 / necesaria para conexiones | `connection` contiene strings sin vocabulario; no hay frescura ni metadatos del dispositivo/canal. | Documentar estados y criterio de dato vigente, además de dónde consultar identidad, canal y unidades confirmadas. Mostrar el texto recibido; no deducir conexión física de un puerto configurado ni marcar como actual una muestra retenida. |
| C7 / necesaria para avance B | Hay conteo de puntos, pero no span medido ni cumplimiento del orden incremental. | Proponer resumen backend de mínimo, máximo, span y progresión. Hasta entonces mostrar conteo y «Rango medido pendiente de informar». 50–100 °C es diseño provisional; 20 puntos por sí solos no prueban un span ≥50 °C. |
| C8 / alcance parcial | Existe función `histeresis`, pero ninguna ruta, trayectoria, resultado ni estado público asociado. | Acordar extensión mínima para recorridos y resultado si entra en MVP; mantener NOT_RUN hasta disponer de ambos recorridos. No usar cero como sustituto. |
| C9 / necesaria para coherencia | No están fijados reinicio/reanudación, cambios de modo con datos, efectos de stop sobre dinámica ni invalidación de resultados. | Documentar transiciones y respuestas 409; proponer que cambio de modo delimite sesión para evitar mezclar datos demo/reales, y que cálculo pendiente no conserve un resultado anterior como vigente. |
| C10 / necesaria para exportación verificable | `/api/results` no define estructura de metadatos; CSV no fija columnas, unidades ni nombre de descarga. | Documentar sesión, modo, origen, unidades y resultados; definir encabezados CSV y nombres de archivo. Acordar JSON finito con `null` para indefinidos, nunca NaN/Inf. |
| C11 / integración local | Contrato indica servidor local, pero no ruta de entrada ni puerto HTTP. | Servir `app/web` desde el mismo origen que `/api/*`, en 127.0.0.1, sin URL Linux fija ni dependencia de CDN. Documentar URL de apertura en el arranque Windows. |

### Terminología científica que debe conservar la interfaz

- **Precisión:** media, s, s_m, RSD, CV y varianza de repeticiones por nivel. Unidades: media/s/s_m en °C, varianza en °C², RSD como razón y CV en %. Mostrar advertencia breve: RSD/CV en Celsius dependen de una escala no absoluta; media cero produce valores relativos no definidos.
- **Exactitud:** comparación con el patrón, errores sistemáticos y «σP — Inexactitud». No inventar porcentaje de exactitud ni usar MAE/RMSE/R².
- **Certeza:** título provisional «Certeza / intervalo probabilístico asociado a σP». Usar `intervalos.k1/k2/k3` ya calculados; describir 68/95/99.7 % como aproximaciones bajo supuesto gaussiano y terminología pendiente de confirmación docente, sin presentarlas como garantía individual.
- **Correlación:** aceptar r en [-1,1] según COORDINACION, aunque la transcripción de p. 17 dice 0–1. No equipararla a concordancia ni emitir aprobación automática a partir de r.
- **Bland–Altman:** usar la convención de las fuentes, diferencia LM35−Vernier y pares sin corregir, pendiente de ratificación explícita en el esquema del resultado. Su fórmula no se atribuye a las diapositivas. No afirmar «concordancia aceptable» sin umbral experimental acordado.
- **Dinámica:** COORDINACION fija `1-exp(-1)` (aproximadamente 63.2 %); la fuente p. 30 y el documento de cálculos usan 63.7 %. Mostrar esta discrepancia en una nota junto al nivel devuelto, sin recalcularlo en JS.
- **Modelo incremental:** H(s) relaciona cambios de entrada y salida. Mostrar y0/yf separados de x0/xf y una respuesta con condición inicial no cero y tiempo referido a t0. No evaluar exponenciales, K/τ, polo ni frecuencias de corte en el navegador. La fórmula simbólica puede permanecer; sus series vienen del servidor.

## Orden propuesto para una fase de implementación

1. Cerrar unidades y esquemas imprescindibles C1–C6 y transiciones C9 con ejemplos JSON de estados vacío, demo, real desconectado, punto aceptado y ensayo finalizado.
2. Escribir pruebas frontend de fallos observables antes de sustituir el prototipo; copiar base visual a `app/web` y conectar estado, errores, configuración y acciones.
3. Sustituir métricas/series, incorporar tabla y dispersión estática, corregir dinámica y etiquetas científicas; cerrar C7/C8/C10 según alcance acordado.
4. Verificar navegación, foco, adaptación y flujo completo contra backend local; separar evidencia Linux/offline, Windows y hardware.

## Verificación y aceptación futura

**Realizado:** lectura íntegra de fuentes locales y revisión estática del HTML, sus manejadores, fórmulas y renderizador; inventario inicial sin `app/` ni `tests/`; consulta de estado Git de solo lectura. `COORDINACION.md` ya figuraba sin seguimiento antes de esta entrega.

**No ejecutado:** pruebas RED/GREEN, servidor/API, navegador, adquisición, Windows ni hardware. Son NOT_RUN en esta auditoría: el usuario pidió documentación sin implementación. No se afirma que el prototipo pase aceptación funcional ni visual.

Casos propuestos para `tests/test_frontend.py` y revisión en navegador, pendientes de implementación:

| Caso | Resultado observable esperado |
|---|---|
| State vacío, resultados null y puertos vacíos | Sin números de ejemplo, gráficas vacías y selección de puerto sin inventar dispositivos. |
| Start demo y varios sondeos | Aumentan muestras desde backend, badge de simulación visible y documento sin recargas. |
| Real desconectado o HTTP 503 | Mensaje explícito, sin datos ficticios y sin transición a demo. |
| Doble clic y sondeo lento seguido de reset | Una acción pendiente; ninguna respuesta obsoleta restaura datos de la sesión previa. |
| Point rechazado / aceptado | Error no incrementa progreso; éxito agrega las medias y precisión de ese nivel. |
| Estática conocida, r negativo, métricas cero/null | Valores del backend respetados, null distinguido de cero, BA con puntos y tres líneas; no porcentajes inventados. |
| Dinámica con t0 y y0 no nulos | Marcador en origen temporal correcto; nivel y curvas idénticos al backend, nota 63.7 % visible y derivadas identificadas. |
| Ensayo sin meseta/cruce | Error del backend, sin τ ni curvas exitosas inventadas. |
| Stop, recarga y reanudación | Controles y ensayo reflejan estado persistido; no se presupone un inicio desde cero. |
| Exportar CSV/JSON y nueva sesión | Descargas desde endpoints con metadatos de modo/sesión; preservación histórica verificada por backend. |
| Teclado, ventana estrecha y navegación entre canvas | Foco visible, controles etiquetados, panel correcto y gráficas redibujadas sin deformación. |

Las pruebas deben verificar estas conductas con respuestas sintéticas etiquetadas y un flujo contra el backend, no solo buscar cadenas en el HTML. La semejanza visual requiere revisión en navegador. Aprobar software A–C no certifica ensayos reales, reporte IEEE (D), presentación Canva (E) ni evaluación presencial.

## Bloqueos y conclusión

No hay bloqueo para entregar esta auditoría. La implementación queda pendiente por alcance expreso de la solicitud. La integración completa depende de precisar el contrato indicado arriba; la aceptación real depende además de hardware/modelo/canal Vernier y pruebas Windows aún no confirmados en las fuentes.

Propuesta central: conservar la estructura visual, reemplazar datos y manejadores por consumo de API y limitar las adiciones a controles de adquisición, tabla/gráfica estática y estados honestos de disponibilidad. Los cambios de contrato se presentan para revisión; ninguno fue aplicado.
