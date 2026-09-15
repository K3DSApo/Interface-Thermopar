# MVP Windows — contrato del orquestador

## Autorización y objetivo
David autoriza iniciar implementación con los cuatro agentes HerDR y publicar un MVP verificado en https://github.com/K3DSApo/Interface-Thermopar.git. Hermes integra y publica; agentes NO hacen commit/push ni cambian ramas. Windows es la plataforma objetivo; CHISPI Linux es solo desarrollo. goal.md es la rúbrica íntegra A–E: software MVP NO significa aprobar hardware, reporte IEEE ni Canva.

## Fuentes protegidas
Leer todos los archivos en 01_Documentación y HTML en 02_Interfaz. No editar esas fuentes ni borrar archivos ajenos. Clinical_Measurements está en 01_Documentación/fuentes. Original HTML se conserva; trabajar en app/web. Apariencia original (rosa, tarjetas, navegación) con cambios mínimos para funciones correctas.

## Fronteras
- architect: contrato, revisión independiente, matriz A–E y pruebas de aceptación. Escribe solo docs/arquitectura.md, docs/aceptacion.md y tests/test_acceptance.py. Primera tarea auditar contrato, no cambiarlo unilateralmente.
- researcher: solo app/calculos.py, tests/test_calculos.py, docs/calculos.md. Funciones puras, sin I/O ni drivers. Incluye cálculos de series para gráficas. Pruebas RED/GREEN documentadas.
- builder: app/main.py, servidor.py, adquisicion.py, sesiones.py, almacenamiento.py, drivers/, app/__init__.py, firmware/, tests/test_backend.py, requirements*.txt, pyproject.toml, .gitignore, scripts Windows, README.md. NO app/calculos.py ni app/web.
- frontend: app/web/* y tests/test_frontend.py, docs/frontend.md. Conserva diseño. NO matemáticas científicas JS. Usa API del contrato.
- Hermes: integra, prueba y publica. Ningún agente administra a los otros.

## Contrato inicial de módulos
Python 3.11+ Windows. Preferir backend stdlib HTTP en 127.0.0.1, pyserial/godirect opcionales para real. Sin servicios persistentes ni instalaciones globales. No hardware disponible confirmado.
calculos.py exporta:
precision(valores) -> {n,media,s,s_m,rsd,cv,varianza} (n>=2, varianza muestral; razón/cv null si media cero)
calibracion_estatica(x,y) -> {n,m,b,r,e_g,e_0,sigma_p,corregidas,intervalos,bland_altman,curva_ajuste}; arrays pares de medias por nivel. intervalos={k1:sigma,k2:2sigma,k3:3sigma}; bland_altman={medias,diferencias,sesgo,limite_inferior,limite_superior}; curva_ajuste={x:[],y:[]}.
calibracion_dinamica(t,y,x0,xf,t0=0.0) -> {k,tau,y0,yf,t0,nivel_tau,fraccion_tau,curvas}; curvas={escalon:{x:[],y:[]},impulso:{x:[],y:[]},magnitud:{x:[],y:[]},fase:{x:[],y:[]}}. t en segundos, tau desde t0, entradas no nulas; rechazar datos sin meseta o cruce, NaN/Inf, tiempos no crecientes. Documentar algoritmo. Fórmula exacta 1-exp(-1), nota fuente 63.7%; no esconder diferencia. Función de transferencia incremental, condición inicial no cero. Magnitud rad/s y fase grados. Respuestas derivadas, no mediciones reales.
histeresis(asc,desc,salida_min,salida_max) -> porcentajes por pares, datos faltantes ValueError. Fuentes matemáticas ambiguas se documentan, no inventar exactitud porcentual/certeza 1-std. Correlación [-1,1] no equivale concordancia. RSD/CV Celsius con advertencia escala no absoluta.

## API compartida MVP
GET /api/state -> JSON {mode:'demo'|'real',running:bool,connection:{esp32:string,vernier:string},samples:[{t,vernier,lm35}],points:[{index,vernier,lm35,precision}],static_result:null|obj,dynamic_result:null|obj,error:null|string,config:obj}.
GET /api/ports -> {ports:[string]}
POST /api/config {mode,port,baudrate,sample_interval,vernier_connection} -> state
POST /api/start {} -> state
POST /api/stop {} -> state
POST /api/point {} -> state (ventana estable, múltiples muestras, no punto si sin datos)
POST /api/dynamic/start {x0,xf} -> state (marca t0)
POST /api/dynamic/finish {} -> state (calcula desde segmento dinámico)
POST /api/reset {} -> state (nueva sesión, preservar datos anteriores)
GET /api/export -> CSV datos crudos sesión; GET /api/results -> JSON resultados y metadatos.
Errores HTTP 400/409/503 JSON {error:string}. Nunca fallback real->demo. Poll frontend 500ms sin refrescar documento. Datos de gráficas exclusivamente backend. No valores ficticios cuando real desconectado. Start demo debe generar datos continuamente; permitir configurar en demo temperatura objetivo/escalón (builder documenta campos), no hardcodear resultados ni inventar ensayos reales. Muestra protocolo firmware real explícito.

## Decisiones de integración tras auditoría (vigentes)
- Implementación autorizada después de leer esta adenda. No pedir confirmación para empezar. Primero un MVP offline completo; hardware y Windows real se reportan NOT_RUN hasta ejecutarlos.
- API /api/config admite cambios parciales; interval en segundos, default 0.5, rango 0.1–10. vernier_connection 'usb'|'ble', vernier_device_name y vernier_channel explícitos para real. Cambios hardware/modo solo detenido y sin muestras (reset previo). Demo permite demo_target_c durante adquisición; demo_initial_c=25.0, demo_target_c=25.0 inicialmente. No calentar hardware automáticamente.
- t es segundos monotónicos desde sesión; conservar UTC de inicio. Curvas dinámicas temporales x son segundos relativos al escalón; t0 es tiempo absoluto dentro de sesión. GET state agrega session_id, dynamic:{active,x0,xf,t0,samples}, stability:{ready,reason,n,window_seconds}, static_progress:{count,span_c,incremental,meets_goal}. Campos adicionales compatibles.
- Ventana estática: últimos 5 segundos, mínimo 5 pares, amplitud max-min <=0.3 °C en AMBOS sensores. Criterio operativo provisional documentado, no especificación docente. /point no reutiliza ventana previamente capturada; rechazo si <5 muestras nuevas. Puntos index desde 1 y precision es precisión LM35 por nivel. Span y tendencia backend, máximo 20 puntos ascendentes para ciclo base; histéresis NOT_RUN en MVP sin recorrido descendente.
- Toda decisión matemática (estabilidad, span, criterio de meseta) se implementa en calculos.py mediante funciones auxiliares adicionales acordadas en docs/calculos.md. Builder llama funciones, no duplica fórmulas; front solo muestra.
- Dinámica /start requiere adquisición activa y ventana inicial estable conservada; ancla t0 justo antes de cambio demo a xf. /finish entrega a cálculos ventana inicial + segmento. Para real, operador aplica el escalón; x0/xf son referencia declarada y deben quedar identificados en metadatos, no fingir medición. El algoritmo admite t<t0 para meseta inicial; último tramo >=5 muestras y >=2s, excursión <= max(0.3°C, 1% del cambio), criterio provisional configurable/documentado. Rechaza sin cruce o cambio insignificante. y0 de ventana inicial, yf ventana final; interpolación lineal del cruce. Pueden añadirse kwargs opcionales sin romper firma base.
- Estado connection: disconnected/connecting/connected/simulated/error. Sin datos o obsoletos mostrar desconexión/error, no ceros inventados. start/stop idempotentes, reset requiere detenido, conserva sesión anterior. stop aborta ensayo activo claramente. Falla guardado no pierde estado.
- CSV incluye session_id, mode,t,vernier,lm35; JSON incluye configuración, metadatos de fuentes, puntos, resultados y estado de validación. Persistir crudos completos; buffer state acotado pero no truncar datos científicos/export.
- Servir / desde app/web/index.html, puerto por defecto 8765 configurable y bind solo loopback. Scripts Windows .cmd/.ps1 resuelven raíz propia, sin paths Linux. No cambiar execution policy global.
- MCU envía JSON línea: version=1,seq,t_ms,adc_raw,voltage_mv,status. Temperatura LM35 desde voltage_mv se calcula en calculos.py (10mV/°C nominal, advertencia ADC/montaje), firmware mide ADC con analogReadMilliVolts y nunca afirma calibración. Pin configurable y no flashear.

## Aceptación y seguridad
Cada implementador lee fuentes antes de actuar, verifica cwd real con pwd, pruebas fallan antes de implementación, después verdes. Sin borrar trabajo concurrente. Sin credenciales ni datos reales en Git. No paquetes globales, billing, push, ni abrir puertos públicos. Firmware no se flashea. Fuentes sintéticas etiquetadas como pruebas. Guardar sesiones fuera de fuentes, con rutas pathlib, UTF8 y sin paths Linux obligatorios. PowerShell sin cambiar política de ejecución global; alternativa .cmd. Dependencias hardware opcionales con errores claros. README separa probado Linux/offline de Windows/hardware NOT_RUN. Agentes reportan pruebas reales, archivos y bloqueos.
