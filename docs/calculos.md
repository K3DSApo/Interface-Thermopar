# Revisión matemática y plan — researcher

Fecha: 2026-09-15. Estado: implementación autorizada tras adenda; firmas de integración publicadas abajo.

Directorio confirmado mediante `pwd`: `/srv/k3ds-server/data/projects/Calibracion-LM35-termopar`.
La entrega actual se limita a `app/calculos.py`, `tests/test_calculos.py` y este documento. No modifica contrato, fuentes ni HTML; no ejecuta mediciones, instalaciones, commit/push ni administración de agentes.

## Firmas vigentes para Builder (adenda integrada)

Esta sección prevalece sobre las propuestas de la auditoría histórica que sigue. No esperar confirmación adicional para integrar estas firmas:

```python
precision(valores)
calibracion_estatica(x, y)
histeresis(asc, desc, salida_min, salida_max)  # list[float]
voltage_mv_a_lm35(voltage_mv)                 # float °C = mV / 10
estabilidad(samples, *, window_seconds=5.0, min_samples=5,
            max_excursion_c=0.3)
progreso_estatico(points)                    # dict
calibracion_dinamica(t, y, x0, xf, t0=0.0, *,
                    initial_window_seconds=5.0, initial_min_samples=5,
                    initial_max_excursion_c=0.3,
                    plateau_seconds=2.0, plateau_min_samples=5,
                    plateau_abs_c=0.3, plateau_fraction=0.01)
```

- `samples`: secuencia de diccionarios `{t,vernier,lm35}`; tiempos estrictamente crecientes. `estabilidad` selecciona los últimos 5 s respecto de la última muestra, incluidos extremos. Devuelve `{ready,reason,n,window_seconds}`; `window_seconds` es la duración observada de la ventana seleccionada. Requiere ≥5 pares y excursión ≤0.3 °C en ambos sensores; no exige cinco segundos completos. Vacío devuelve `ready=False`. Datos inválidos lanzan `ValueError`. Builder conserva/selecciona los mismos pares por `t >= samples[-1]['t']-5`; no calcula amplitud ni estabilidad. La regla de cinco muestras nuevas desde el último punto y la obsolescencia respecto del reloj pertenecen a la sesión.
- `points`: diccionarios con `vernier` (medias por nivel); `progreso_estatico` devuelve `{count,span_c,incremental,meets_goal}`. Ascenso estrictamente creciente; span = máximo−mínimo (0 para cero/un punto); objetivo: exactamente 20 puntos, ascendentes, span ≥50 °C. Con cero/un punto `incremental=True` por ausencia de contradicción; `meets_goal=False`. Builder limita la captura a 20 puntos.
- `voltage_mv_a_lm35`: conversión nominal 10 mV/°C; rechaza datos no numéricos/no finitos, admite valores negativos finitos sin inventar límites eléctricos. No equivale a calibración del ADC ni garantiza compatibilidad del montaje.
- Dinámica: meseta inicial usa muestras en `[t0−initial_window_seconds,t0]`, al menos cinco; debe existir una muestra anterior a `t0`. Final usa el sufijo más corto con ≥5 muestras y ≥2 s, completamente posterior a `t0`; no redondea tiempos. Ventanas disjuntas y cambio `abs(yf−y0)>max(plateau_abs_c,plateau_fraction*abs(yf−y0))`. Valida excursión final con esa banda. `x0=0`, `xf=0` o `y0=0` son matemáticamente válidos; la sesión/reporte acredita por separado la condición inicial no cero de la rúbrica. Amplitud de entrada cero y K no positivo se rechazan para este ensayo LM35; enfriamiento normal sí se admite.
- Cruce: primero que encierra la fracción exacta después de `t0`, interpolación lineal entre muestras reales; si falta muestra exactamente en `t0`, se permite el par que lo encierra únicamente si el cruce interpolado es posterior. `tau=t_cruce−t0`.
- Todas las curvas temporales usan segundos **relativos al escalón** (adenda): `u=0..max(t[-1]−t0,5*tau)`; 201 puntos, impulso y escalón. Frecuencia: 121 valores reales rad/s entre `0.01/tau` y `100/tau`; magnitud lineal y fase grados. `t0` permanece absoluto en la sesión.
- Errores científicos/de entrada: `ValueError`; sin I/O, sin mutar argumentos, sin NaN/Infinity de salida. Solo RSD/CV con media cero devuelve `None`.

## 1. Fuentes revisadas y jerarquía

Se leyó completo [COORDINACION.md](../COORDINACION.md), todos los archivos de `01_Documentación` y el HTML de `02_Interfaz`:

| Fuente local | Uso en esta revisión |
| --- | --- |
| [Índice del proyecto](../01_Documentación/Calibración%20de%20LM35%20y%20termopar.md) | Organización, límites y estado inicial. |
| [goal.md](../01_Documentación/goal.md) | Rúbrica A–E: automatización, 20 mediciones, rango de al menos 50 °C, estática, dinámica, IEEE y Canva. |
| [Cálculos y calibración](../01_Documentación/Cálculos%20y%20calibración%20del%20LM35.md) | Diseño experimental y fórmulas propuestas, §§4–43. |
| [Clinical Measurements, transcripción completa](../01_Documentación/fuentes/Clinical_Measurements_completo.md) | 34 páginas; precisión pp. 7 y 14, calibración pp. 15–20, primer orden pp. 28–30. |
| [Drivers Vernier Go Direct](../01_Documentación/Drivers%20Vernier%20Go%20Direct.md) | Límites de adquisición, identificación del modelo/canal/unidades y sincronización. |
| [Prototipo HTML](../02_Interfaz/interfaz_calibracion_LM35_v3.html) | Auditoría de métricas, etiquetas, datos simulados y gráficas. |

La instrucción actual limita el trabajo a observaciones y plan, aunque COORDINACION autorice una implementación posterior. `goal.md` define el objetivo académico; COORDINACION define la interfaz de módulos. Las discrepancias se registran aquí sin cambiar esas fuentes. La revisión utiliza los materiales locales suministrados; no verifica enlaces externos ni la transcripción contra el PDF original, que no está entre los archivos encontrados.

## 2. Dictamen y observaciones prioritarias

1. **Base estática coherente:** medias por nivel, varianza muestral, mínimos cuadrados, corrección inversa, errores de ganancia/corrimiento y definición de `sigma_p` coinciden con el planteamiento. Falta concretar validaciones de casos degenerados y el significado preciso de ciertas salidas.
2. **Porcentaje dinámico discrepante:** Clinical p. 30 y el documento de cálculos §30 indican 63.7 %. La ecuación exponencial de esa misma fuente da exactamente `1−exp(−1) = 0.6321205588…`, es decir, 63.21205588… %. Usar 0.637 en una respuesta ideal sitúa el cruce en `−tau·ln(0.363) ≈ 1.01335·tau`, aproximadamente 1.335 % tarde. COORDINACION ya exige la expresión exacta; conservar una nota visible de la discrepancia.
3. **Correlación:** Clinical p. 17 dice 0 a 1, pero su fórmula admite −1 a 1. Una pendiente negativa puede dar `r=−1` y ajuste lineal perfecto. Ni `r=1` demuestra ausencia de sesgo ni permite concluir concordancia aceptable.
4. **HTML incompatible con la definición de precisión y certeza:** las tarjetas usan `1−std(ep)`, `1−std(ee)` y `1−std(ec)`, y porcentajes de precisión/exactitud/certeza sin respaldo en las fuentes. Sustituirlos posteriormente por las métricas del contrato. También faltan la recta estática y las líneas de sesgo/límites de Bland–Altman; este último se dibuja como una línea que une puntos.
5. **Condición inicial y ganancia:** obtener `K` de incrementos exige interpretar la función de transferencia alrededor de un equilibrio. No imponer simultáneamente `y0=K·x0` cuando existe un corrimiento. El ejemplo HTML fija `K=.992`, `T0=25`, `Tf=70` sin distinguir entradas y salidas; no constituye una identificación experimental consistente.
6. **Mesetas y origen temporal incompletos:** el contrato exige rechazarlas cuando falten, pero no define ventanas, tolerancias ni cómo conservar el equilibrio anterior a `t0`. El segmento exclusivamente posterior al inicio puede perder `y0`.
7. **Datos e inferencia:** la precisión debe calcularse sobre repeticiones del mismo nivel. La dispersión de los 20 niveles refleja principalmente el cambio de temperatura. `sigma_p` calculada con las medias usadas para ajustar no mide por sí sola el error de futuras lecturas ni la incertidumbre completa del patrón.
8. **Alcance del prototipo:** gráficas y valores están simulados; los botones actuales no adquieren datos. El MVP matemático no acredita A con sensores reales, ni los experimentos B/C, ni las entregas D/E.

## 3. Contrato matemático revisado

### 3.1 Convenciones comunes propuestas

- `x`: temperatura Vernier; `y`: temperatura LM35, ambas en °C y emparejadas temporalmente. Los cálculos no convierten voltajes ni eligen canales.
- Funciones puras y deterministas; sin I/O, drivers, modificación de entradas ni redondeo intermedio. El frontend solo representa resultados.
- Proponer `ValueError` para entradas vacías, ausentes, no numéricas, booleanos, NaN/Inf, longitudes incompatibles y degeneraciones que impidan la salida completa. No descartar muestras silenciosamente.
- Salidas numéricas finitas; `None` de Python se serializa como `null` únicamente cuando el contrato lo prevé. Evitar NaN/Infinity en JSON y comprobar también resultados intermedios desbordados.
- Distinguir tamaño mínimo computable de suficiencia experimental: una función estática puede trabajar con dos pares, pero eso no satisface las 20 mediciones ni el rango de la rúbrica.

### 3.2 `precision(valores)`

Para `n≥2` repeticiones del mismo nivel:

\[
\bar y=\frac{1}{n}\sum y_i,\quad
s^2=\frac{\sum(y_i-\bar y)^2}{n-1},\quad
s=\sqrt{s^2},\quad s_m=\frac{s}{\sqrt n}.
\]

Retorno exacto: `{n,media,s,s_m,rsd,cv,varianza}`. `rsd=s/media`; `cv=100·rsd`, expresado numéricamente en %. Si `media=0`, ambos son `null`; `s`, `s_m` y `varianza` siguen definidos. Las repeticiones constantes son válidas y dan dispersión cero.

Clinical p. 14 usa la media con signo. No reemplazarla silenciosamente por su valor absoluto: una media negativa produce RSD/CV negativos conforme a esa fórmula. Advertir que Celsius no es una escala absoluta; estos cocientes cambian al trasladar el origen térmico y no deben interpretarse como porcentajes universales de calidad. `s_m` tampoco incorpora automáticamente la autocorrelación de las muestras.

### 3.3 `calibracion_estatica(x,y)`

Cada posición contiene un par de **medias por nivel**, no una muestra instantánea. Proponer regresión sin ponderación, porque la firma no recibe incertidumbres ni tamaños de ventana.

Usar la forma algebraicamente equivalente centrada de las ecuaciones de Clinical p. 17:

\[
S_{xx}=\sum(x_i-\bar x)^2,\quad S_{yy}=\sum(y_i-\bar y)^2,\quad
S_{xy}=\sum(x_i-\bar x)(y_i-\bar y),
\]
\[
m=S_{xy}/S_{xx},\quad b=\bar y-m\bar x,\quad
r=S_{xy}/\sqrt{S_{xx}S_{yy}}.
\]

Esto evita parte de la cancelación por restar sumas grandes en la fórmula expandida. Un eventual ajuste de `r` a [−1,1] solo puede corregir redondeo de máquina, nunca ocultar datos inválidos.

\[
e_g=m-1,\quad e_0=b,\quad c_i=(y_i-b)/m,\quad
\sigma_p=\sqrt{\frac1n\sum(c_i-x_i)^2}.
\]

`sigma_p` usa divisor **n**, no `n−1` ni `n−2`, y se presenta como **inexactitud**. Unidades: `m`, `r` y `e_g` adimensionales; `b`, `e_0`, `sigma_p` y `c_i` en °C.

Retorno del contrato: `{n,m,b,r,e_g,e_0,sigma_p,corregidas,intervalos,bland_altman,curva_ajuste}`. Propuestas para cerrar su semántica:

- `corregidas=[c_i]` conserva el orden original.
- `intervalos={k1:sigma_p,k2:2·sigma_p,k3:3·sigma_p}` contiene **semianchos**, no extremos ni porcentajes. Si se representa una banda alrededor de una lectura corregida, el centro y la interpretación deben declararse.
- `curva_ajuste={x:[min(x),max(x)],y:[m·min(x)+b,m·max(x)+b]}` basta para representar la recta, sin extrapolar.
- Rechazar `n<2`, `Sxx=0`, `Syy=0` o `m=0`: no puede devolverse conjuntamente correlación y corrección inversa. Hay pendientes no nulas pero mal condicionadas; cualquier umbral adicional debe acordarse y documentarse, no inventarse como límite físico del LM35.
- No exigir que `x` llegue ordenado: ordenar solo la serie de la recta; conservar los pares originales. Niveles repetidos no invalidan el ajuste si existe variación global de `x`.

**Certeza:** Clinical p. 20 vincula ±1, ±2 y ±3 sigma con aproximadamente 68 %, 95 % y 99.7 % bajo un modelo gaussiano. Mantenerlo como interpretación condicional de la fuente, pendiente de confirmar con el profesor. No presentarlo como cobertura experimental comprobada ni como intervalos de confianza de la regresión.

### 3.4 Bland–Altman

El documento de cálculos §§19–20 aporta las fórmulas; Clinical no las desarrolla. Aplicarlas inicialmente a pares sin corregir:

\[
M_i=(x_i+y_i)/2,\quad D_i=y_i-x_i,\quad
\bar D=\frac1n\sum D_i,\quad
s_D=\sqrt{\frac{\sum(D_i-\bar D)^2}{n-1}}.
\]

`bland_altman={medias:[M_i],diferencias:[D_i],sesgo:media(D),limite_inferior:media(D)−1.96·s_D,limite_superior:media(D)+1.96·s_D}`.

Usar dispersión y tres líneas horizontales, con unidades °C. Los límites describen las diferencias de las medias por nivel utilizadas; no equivalen automáticamente a límites de lecturas individuales. Su interpretación aproximada exige revisar distribución de diferencias, dependencia y variación con la temperatura. La aceptación de concordancia necesita una tolerancia experimental previamente acordada. Una comparación posterior a la corrección debe identificarse por separado, sin sustituir silenciosamente los pares originales.

### 3.5 `histeresis(asc,desc,salida_min,salida_max)`

Clinical p. 16:

\[
H_i=100\frac{|asc_i-desc_i|}{salida_{max}-salida_{min}}.
\]

Proponer retorno `list[float]` de porcentajes en el orden de los pares. Requerir arreglos no vacíos, finitos y del mismo tamaño, y `salida_max>salida_min`. El denominador representa un rango de salida declarado, con las mismas unidades que las mediciones; no deducirlo del rango de diferencias.

La firma no recibe entradas térmicas: quien llama debe garantizar pares del mismo nivel, reordenando el recorrido descendente cuando corresponda. Emparejar por posición de adquisición produciría un resultado erróneo. Si falta un recorrido, la función lanza `ValueError`; la capa de sesión representa `NOT_RUN`. No completar con ceros ni interpolar sin acuerdo. La API actual no define almacenamiento del sentido del recorrido ni salida de histéresis: pendiente de integración.

### 3.6 `calibracion_dinamica(t,y,x0,xf,t0=0.0)`

Retorno del contrato: `{k,tau,y0,yf,t0,nivel_tau,fraccion_tau,curvas}`. Distinguir `x0,xf` (entrada aplicada) de `y0,yf` (salida observada). Exigir `xf≠x0`, salida con cambio no nulo, tiempos finitos estrictamente crecientes y `tau>0`.

La frase «entradas no nulas» es ambigua entre arreglos presentes, temperaturas distintas de cero y amplitud no nula. Propuesta a ratificar: exigir arreglos presentes y amplitud distinta de cero; registrar explícitamente `y0≠0` para cumplir el ensayo académico. Cero °C es una temperatura físicamente válida y no causa por sí misma singularidad. No ampliar ni restringir esta regla sin resolver su significado contractual.

**Modelo incremental**, con `u=t−t0`:

\[
\Delta x=x-x_0,\quad \Delta y=y-y_0,\quad
\tau\frac{d\Delta y}{dt}+\Delta y=K\Delta x,\quad
K=\frac{y_f-y_0}{x_f-x_0},\quad H(s)=\frac{K}{1+\tau s}.
\]

\[
y(t)=y_0+(y_f-y_0)(1-e^{-u/\tau}),\quad u\ge0.
\]

La función de transferencia describe incrementos con condición inicial incremental cero; la temperatura absoluta inicial puede ser distinta de cero. El corrimiento de equilibrio queda separado de `K`.

**Algoritmo propuesto, todavía no implementado ni validado con hardware:**

1. Conservar muestras anteriores a `t0` para comprobar equilibrio inicial y calcular `y0`. Si solo se acepta una muestra exactamente en `t0`, no se puede afirmar que hubo meseta inicial: esta alternativa requiere una garantía externa explícita.
2. Definir ventanas inicial/final de al menos cinco muestras cada una y duración mínima acordada según la adquisición. Como punto de partida para pruebas sintéticas, usar una banda `epsilon=max(epsilon_abs,0.01·|yf−y0|)`; `epsilon_abs` y la duración siguen pendientes de resolución/ruido y frecuencia reales. No tratarlos como especificaciones del sensor.
3. Estimar `y0,yf` mediante medias de esas ventanas. Exigir en cada ventana rango pico a pico y deriva lineal acumulada dentro de `epsilon`; comprobar además persistencia final en dos ventanas consecutivas. La validación de meseta finita es operacional, no prueba de un límite asintótico.
4. Rechazar ausencia de ventanas suficientes, cambio indistinguible de su dispersión o transitorio incompatible con la aproximación elegida. Fijar el umbral señal/ruido y la política ante sobreimpulso antes de implementar.
5. Calcular `fraccion_tau=1−exp(−1)` y `nivel_tau=y0+fraccion_tau·(yf−y0)`. Normalizar `q_i=(y_i−y0)/(yf−y0)` permite tratar calentamiento y enfriamiento con el mismo criterio.
6. Buscar después de `t0` un par consecutivo que encierre ese nivel; interpolar linealmente el tiempo de cruce y devolver `tau=t_cruce−t0`. Rechazar falta de cruce, cruce no positivo o hueco temporal excesivo alrededor del cruce según el límite de adquisición acordado. Ante cruces múltiples por ruido, proponer persistencia de tres muestras sobre el nivel normalizado y usar el cruce que inicia esa persistencia; documentar su efecto y validarlo con datos sintéticos.
7. Calcular `K` y construir las series del modelo. No sustituir el cruce ausente por un `tau` fijo ni usar la última muestra como supuesto equilibrio sin validación.

La firma actual no permite pasar ventanas/tolerancias. Opciones pendientes: constantes explícitas y versionadas del módulo para un protocolo fijo, o una extensión revisada del contrato. Las decisiones anteriores son propuestas, no valores ya aprobados.

**Límite de identificabilidad:** la función no recibe `x(t)` completo; no puede demostrar que la entrada fue un escalón suficientemente rápido y sostenido. La sesión debe conservar la serie Vernier y evaluar esa condición. La selección de `x0,xf` manual no constituye evidencia de la entrada real; una rampa térmica o retardo de transporte puede sesgar `tau`.

### 3.7 Series dinámicas para gráficas

Todas se generan en Python a partir de los parámetros obtenidos y se etiquetan como **respuestas derivadas del modelo**. La serie experimental se conserva aparte en `samples`.

| Campo dentro de `curvas` | Coordenada x propuesta | Coordenada y |
| --- | --- | --- |
| `escalon` | Tiempo de sesión `t0+u`, s | `y0+(yf−y0)·(1−exp(−u/tau))`, °C |
| `impulso` | Tiempo relativo `u`, s | `(K/tau)·exp(−u/tau)`, s⁻¹ para ganancia térmica adimensional |
| `magnitud` | Frecuencia angular real `omega>0`, rad/s | `abs(K)/sqrt(1+(omega·tau)^2)`, lineal y adimensional |
| `fase` | La misma `omega`, rad/s | Argumento de `K/(1+j·omega·tau)`, en grados |

Cada campo contiene `{x:[],y:[]}` con longitudes iguales. Proponer 201 muestras temporales entre `u=0` y `max(t_final−t0,5·tau)`, y 121 frecuencias logarítmicas entre `0.01/tau` y `100/tau`, incluyendo `1/tau`. La cola modelada fuera del registro no es una medición.

Para `K>0`, la fase es `−atan(omega·tau)·180/pi`. Si se admiten ganancias negativas, la magnitud requiere `abs(K)` y la fase el cuadrante correcto, por ejemplo `atan2(−K·omega·tau,K)` en grados. Alternativa: rechazar `K≤0` como ensayo LM35 incompatible; el contrato debe decidirlo explícitamente. Un enfriamiento normal tiene ambos incrementos negativos y sigue dando `K>0`.

La API debe entregar frecuencias reales; el frontend puede aplicar una escala logarítmica al eje, sin recalcular las respuestas. El punto temporal de tau se representa en `(t0+tau,nivel_tau)`, no en `(tau,nivel_tau)` cuando se usa tiempo de sesión.

## 4. Bloqueos y decisiones pendientes

| Prioridad | Pendiente | Propuesta y efecto |
| --- | --- | --- |
| Alta: identificación dinámica | Mesetas, ventanas, tolerancias, cruces múltiples, huecos y prehistoria de `t0` | Acordar el protocolo reproducible de §3.6 y conservar prehistoria. Sin ello no hay aceptación objetiva de `tau`. |
| Alta: contrato dinámico | Significado de «entradas no nulas» y política de `K≤0` | Separar nulidad de datos, amplitud nula y requisito de condición inicial; decidir soporte matemático o rechazo físico. |
| Alta: integración | Coordenadas de series, esquema de histéresis y forma de `points[].precision` | Ratificar §3.7 y retorno de histéresis; indicar si precisión corresponde solo a LM35 o a ambos sensores. |
| Experimental | Modelo/canal Vernier, unidades, ADC ESP32, frecuencia y sincronización | Confirmar antes de ensayos reales; no bloquea la futura implementación pura ni pruebas sintéticas. |
| Académica | Definición de certeza y significado de rango ≥50 °C | Presentar interpretación gaussiana condicional; proponer span ≥50 °C medido por Vernier. 50–100 °C permanece provisional. |
| Experimental | Tolerancia aceptable de concordancia y emparejamiento de recorridos | Declarar antes de juzgar Bland–Altman o histéresis; no inferir aprobación a partir de `r`. |

No hay bloqueo para esta entrega documental. La implementación queda pendiente por instrucción expresa del usuario. Las decisiones listadas deben reflejarse en el contrato compartido antes de fijar comportamientos que afecten a otras capas.

## 5. Plan de implementación posterior y pruebas RED/GREEN

1. Resolver las decisiones anteriores con la revisión del contrato, sin modificarlo unilateralmente.
2. Escribir pruebas en `tests/test_calculos.py` con datos inequívocamente sintéticos y oráculos independientes; ejecutar antes de crear `app/calculos.py` y conservar el resultado RED real. No se ha ejecutado RED en esta entrega.
3. Implementar validación común, precisión, estática/Bland–Altman e histéresis como funciones puras. Ejecutar pruebas hasta GREEN y registrar comando, entorno y resultado reales.
4. Implementar identificación dinámica y series tras cerrar las mesetas y coordenadas. Verificar exactitud numérica, invariancias y rechazos; evitar exigir igualdad exacta donde interviene interpolación.
5. Documentar interpretación, unidades, restricciones y estado de verificación; entregar a integración sin alterar frontend, adquisición ni fuentes.

Casos mínimos propuestos:

| Grupo | Datos o propiedad | Resultado esperado |
| --- | --- | --- |
| Precisión | `[1,2,3]` | Media 2, varianza 1, `s=1`, `s_m=1/sqrt(3)`, RSD .5, CV 50. |
| Precisión | `[-1,1]`; repeticiones constantes; media negativa | RSD/CV nulos en media cero; dispersión cero para constantes; signo conforme a la fuente. |
| Estática | `x=[1,2,3]`, `y=[3,5,7]` | `m=2,b=1,r=1,e_g=1,e_0=1`, corregidas iguales a x y `sigma_p=0`. |
| Bland–Altman | El par anterior | Medias `[2,3.5,5]`, diferencias `[2,3,4]`, sesgo 3, límites 1.04 y 4.96; ilustra que `r=1` no prueba concordancia. |
| Inexactitud | `x=[0,1,2]`, `y=[0,1,3]` | `m=1.5,b=−1/6`, residuos corregidos `[1/9,−2/9,1/9]`, `sigma_p=sqrt(2)/9`. Detecta divisor incorrecto. |
| Regresión | Pares invertidos de orden; pendiente negativa; x constante; y constante; covarianza cero | Orden no altera parámetros; correlación negativa válida; rechazos definidos para ajuste/corrección imposibles. |
| Histéresis | `asc=[20,40]`, `desc=[21,38]`, salida 0–100 | `[1,2]` %; rechazar faltantes y rango cero/invertido. |
| Dinámica | Exponencial sintética con equilibrio inicial no cero, offset y meseta final suficientemente prolongada | Recuperar `K,tau` dentro de tolerancia fijada según muestreo y estimación de meseta. |
| Dinámica | Trasladar todos los tiempos y `t0` por la misma constante | `tau,K` invariantes; curva escalón y cruce se desplazan igual. |
| Dinámica | Calentamiento/enfriamiento; pasos temporales irregulares crecientes | Misma lógica de fracción e interpolación; nunca usar índice como segundos. |
| Rechazo dinámico | Rampa sin meseta, constante, sin cruce, ruido con cruces múltiples, tiempos repetidos/decrecientes, prehistoria insuficiente | Errores definidos; sin parámetros ficticios. |
| Series | `u=0`, `u=tau`, `omega=1/tau` | Escalón comienza en `y0`; fracción exacta en tau; impulso inicial `K/tau`; magnitud `abs(K)/sqrt(2)` y fase −45° si `K>0`. |
| Robustez común | NaN/Inf, entradas inválidas, desbordamiento, no mutación de arreglos | Rechazo explícito y resultados serializables sin no-finitos. |

Las pruebas de identificación deben distinguir el error de muestreo del error por estimar `yf` con una meseta finita. Evitar construir un oráculo que simplemente replique el mismo detector o sus tolerancias. Incluir transitorios insuficientes que deban fallar, además de casos ideales.

## 6. Verificación de esta entrega

- Lectura documental completa y contraste algebraico de fórmulas, tipos de datos y gráficas.
- Único archivo entregado: `docs/calculos.md`.
- Implementación, pruebas automatizadas RED/GREEN, Windows, sensores y ensayos reales: **NOT_RUN**.
- No se afirma cumplimiento experimental de A–C ni realización de IEEE/Canva D–E.
