---
title: Cálculos y calibración del LM35
type: documento-de-trabajo
status: modificable
project: Calibración de LM35 y termopar
---

# Cálculos y calibración del LM35

Este documento contiene el planteamiento matemático y experimental modificable. Puede cambiar conforme se revisen las indicaciones del profesor, el montaje y los datos reales.

La información estable de drivers está separada en `Drivers Vernier Go Direct.md`.

---

# Proyecto de calibración del sensor LM35 con referencia Vernier
## Planteamiento matemático y experimental corregido según las indicaciones del profesor

> **Versión corregida**
>
> Este documento se limita a los parámetros solicitados en la actividad y a la terminología/fórmulas que aparecen en la presentación *Clinical Measurements*.  
> Se eliminan métricas adicionales que no aparecen en los apuntes del profesor, como \(R^2\), MAE y RMSE.
>
> Cuando la actividad exige algo que no aparece desarrollado matemáticamente en las diapositivas —por ejemplo Bland–Altman— se indica explícitamente.

---

# 1. Objetivo general

Desarrollar un sistema automático de calibración para un sensor de temperatura **LM35**, utilizando una sonda **Vernier** como instrumento de referencia.

El sistema deberá adquirir datos desde ambos sensores y procesarlos en una computadora en tiempo real.

Se utilizarán dos tipos de caracterización:

1. **Calibración estática**
2. **Calibración dinámica**

La computadora deberá mostrar inmediatamente:

- datos medidos;
- cálculos;
- parámetros de calibración;
- gráficas correspondientes.

---

# 2. Arquitectura general del experimento

La arquitectura prevista es:

```text
                         MISMA VARIABLE FÍSICA
                              Temperatura
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
               Sonda Vernier                  LM35
                    │                           │
          Driver / interfaz USB          Voltaje analógico
                    │                           │
                    │                         ESP32
                    │                           │
                    └───────────┬───────────────┘
                                │
                           COMPUTADORA
                              Python
                                │
                  ┌─────────────┴─────────────┐
                  │                           │
          CALIBRACIÓN ESTÁTICA       CALIBRACIÓN DINÁMICA
```

El Vernier se considerará la **referencia** y el LM35 será el sensor que se desea caracterizar.

Para la parte estática:

\[
x_i=T_{\text{Vernier},i}
\]

\[
y_i=T_{\text{LM35},i}
\]

---

# 3. Requisito A — Automatización

La actividad exige que el proceso completo sea automático.

Por ello, el programa deberá:

1. leer el LM35 mediante el ESP32;
2. leer el Vernier mediante su interfaz/driver USB;
3. mostrar las dos temperaturas en tiempo real;
4. almacenar cada muestra con su instante de tiempo;
5. realizar los cálculos de calibración automáticamente;
6. actualizar las gráficas;
7. mostrar los parámetros finales sin realizar los cálculos manualmente.

La implementación del driver Vernier se definirá cuando se confirme el modelo exacto y la biblioteca de Python.

---

# 4. Calibración estática

## 4.1 Qué solicita la actividad

Se deberán realizar:

\[
\boxed{20\text{ mediciones}}
\]

en un rango de temperatura incremental.

Para el diseño actual del experimento se plantea comenzar en:

\[
\boxed{50^\circ C}
\]

y aumentar progresivamente la temperatura.

### Aclaración importante sobre el rango

La redacción original dice:

> “un rango de temperatura incremental de al menos 50 grados o más”.

Esto puede interpretarse como un **span de al menos 50 °C**.

Si se parte de \(50^\circ C\) y además se desea cubrir un span de \(50^\circ C\), entonces el último punto deberá llegar aproximadamente a:

\[
\boxed{100^\circ C}
\]

Antes de realizar el experimento conviene confirmar con el profesor si esto es exactamente lo que espera.

---

# 5. Distribución de los 20 puntos

Si se decide trabajar desde:

\[
T_{\min}=50^\circ C
\]

hasta:

\[
T_{\max}=100^\circ C
\]

con 20 niveles igualmente espaciados:

\[
T_i=T_{\min}+(i-1)\frac{T_{\max}-T_{\min}}{19}
\]

para:

\[
i=1,2,\ldots,20
\]

En este caso:

\[
\Delta T=
\frac{100-50}{19}
\]

\[
\Delta T\approx2.63^\circ C
\]

Por tanto, los puntos nominales serían aproximadamente:

```text
50.00 °C
52.63 °C
55.26 °C
57.89 °C
...
97.37 °C
100.00 °C
```

Los valores realmente utilizados en los cálculos serán los medidos por Vernier.

---

# 6. Medición en cada nivel de temperatura

En cada nivel se colocarán ambos sensores en la misma condición térmica.

Se debe esperar a que el sistema alcance una condición aproximadamente estable.

No conviene utilizar una lectura instantánea aislada.

Para el punto \(i\) se registrarán varias muestras:

\[
x_{i,1},x_{i,2},...,x_{i,M}
\]

para Vernier y:

\[
y_{i,1},y_{i,2},...,y_{i,M}
\]

para LM35.

Los promedios serán:

\[
\bar{x}_i=
\frac{1}{M}
\sum_{j=1}^{M}x_{i,j}
\]

\[
\bar{y}_i=
\frac{1}{M}
\sum_{j=1}^{M}y_{i,j}
\]

El par utilizado como punto de calibración será:

\[
\boxed{
(\bar{x}_i,\bar{y}_i)
}
\]

Así existirán **20 puntos experimentales**, pero cada punto tendrá suficientes muestras para evaluar la precisión.

## 6.1 Recorrido ascendente y descendente — histéresis

La página 16 de *Clinical Measurements* indica explorar el rango de la magnitud en intervalos discretos, tanto en sentido ascendente como descendente, para identificar una posible histéresis.

Cuando existan dos salidas para una misma entrada —una ascendente y otra descendente— se conservarán como \(O_i\) y \(O_i'\). El porcentaje de histéresis se calculará como:

\[
\boxed{
H\%=\frac{|O_i-O_i'|}{O_{\max}-O_{\min}}\times100
}
\]

La interfaz podrá mostrar la trayectoria ascendente, la trayectoria descendente y el valor de histéresis. Si solo se realiza un recorrido, la histéresis deberá marcarse como `NOT_RUN`, no como cero.

---

# 7. Precisión

## Fuente en los apuntes

La presentación define la precisión como el grado de acuerdo entre los resultados de una serie de mediciones repetidas.

En la diapositiva de **Parámetros de Calidad** aparecen como medidas de precisión:

- desviación estándar absoluta;
- desviación estándar relativa;
- coeficiente de variación;
- varianza.

## 7.1 Media

La fórmula mostrada en los apuntes es:

\[
\boxed{
\bar{x}=
\frac{\sum_{i=1}^{N}x_i}{N}
}
\]

## 7.1.1 Desviación estándar de la media

La página 14 también define la desviación estándar de la media:

\[
\boxed{
s_m=\frac{s}{\sqrt{N}}
}
\]

Este parámetro se conservará separado de la desviación estándar absoluta \(s\), porque no representan la misma magnitud.

## 7.2 Desviación estándar absoluta

La fórmula mostrada en los apuntes es:

\[
\boxed{
s=
\sqrt{
\frac{
\sum_{i=1}^{N}(x_i-\bar{x})^2
}{
N-1
}
}
}
\]

Para el LM35 se aplicará a las muestras repetidas de cada nivel.

Una desviación estándar menor implica mayor precisión o repetibilidad.

## 7.3 Desviación estándar relativa

La diapositiva expresa la desviación estándar relativa como la desviación estándar normalizada respecto a la media:

\[
\boxed{
RSD=\frac{s}{\bar{x}}
}
\]

## 7.4 Coeficiente de variación

La fórmula mostrada es:

\[
\boxed{
CV=
\frac{s}{\bar{x}}\times100\%
}
\]

## 7.5 Varianza

\[
\boxed{
s^2
}
\]

La interfaz estática deberá mostrar estos resultados dentro del apartado de **Precisión**, sin sustituirlos por métricas externas.

---

# 8. Exactitud

## Fuente en los apuntes

La presentación define la exactitud como:

> grado de acuerdo entre el valor obtenido en la medición de una magnitud y el valor considerado verdadero.

En este experimento se considerará:

\[
T_{\text{Vernier}}
\]

como valor de referencia y:

\[
T_{\text{LM35}}
\]

como valor obtenido por el instrumento bajo calibración.

La presentación no proporciona en esas diapositivas una única ecuación llamada “fórmula de exactitud”.

Por esa razón, en este proyecto **no se inventará un porcentaje de exactitud ni se sustituirá por MAE o RMSE**.

La exactitud se analizará mediante:

1. comparación directa con el patrón;
2. errores sistemáticos;
3. error de ganancia;
4. error de corrimiento;
5. inexactitud \(\sigma_P\) definida por el profesor.

---

# 9. Modelo de calibración por mínimos cuadrados

## Fuente en los apuntes — Paso 2

El profesor indica establecer un modelo matemático que describa la relación entrada–salida del instrumento.

La gráfica es:

\[
\boxed{\text{Patrón vs. resultado}}
\]

y se determina la tendencia general por el método de mínimos cuadrados.

El modelo utilizado es:

\[
\boxed{
y=mx+b
}
\]

donde:

\[
x=T_{\text{Vernier}}
\]

\[
y=T_{\text{LM35}}
\]

---

# 10. Pendiente \(m\)

La fórmula mostrada por el profesor es:

\[
\boxed{
m=
\frac{
n\sum xy-(\sum x)(\sum y)
}{
n\sum x^2-(\sum x)^2
}
}
\]

La pendiente indica cuánto aumenta la salida \(y\) por cada unidad de aumento de \(x\).

El comportamiento ideal para temperaturas expresadas en la misma unidad sería:

\[
\boxed{m=1}
\]

---

# 11. Ordenada al origen \(b\)

La fórmula utilizada en la presentación es:

\[
\boxed{
b=
\frac{
(\sum y)(\sum x^2)-(\sum x)(\sum xy)
}{
n\sum x^2-(\sum x)^2
}
}
\]

También puede expresarse algebraicamente como:

\[
b=\bar{y}-m\bar{x}
\]

pero para mantener la interfaz alineada con la presentación se utilizará como referencia principal la expresión mostrada por el profesor.

---

# 12. Coeficiente de correlación \(r\)

## Fuente en los apuntes — Paso 2

El profesor utiliza el **coeficiente de correlación \(r\)**.

No se utilizará \(R^2\) como parámetro principal porque no es el término presentado en esta sección de los apuntes.

La fórmula mostrada es:

\[
\boxed{
r=
\frac{
n\sum xy-(\sum x)(\sum y)
}{
\sqrt{
[n\sum x^2-(\sum x)^2]
[n\sum y^2-(\sum y)^2]
}
}
}
\]

Su interpretación se alineará con la presentación del profesor:

- \(r\) cercano a \(1\): mayor ajuste lineal de los puntos experimentales;
- valores más alejados de \(1\): menor bondad de ajuste.

Para este experimento se espera:

\[
\boxed{r\approx1}
\]

porque al aumentar la temperatura de referencia también debe aumentar la lectura del LM35.

---

# 13. Error de ganancia

## Fuente en los apuntes — Paso 3

La presentación define:

\[
\boxed{
e_G=m-1
}
\]

Ésta será la fórmula utilizada exactamente.

Idealmente:

\[
m=1
\]

por lo tanto:

\[
\boxed{
e_G=0
}
\]

---

# 14. Error de corrimiento

## Fuente en los apuntes — Paso 3

La presentación define:

\[
\boxed{
e_0=b
}
\]

Idealmente:

\[
\boxed{
e_0=0
}
\]

---

# 15. Corrección de la lectura mediante la recta de calibración

El modelo experimental es:

\[
y=mx+b
\]

Para recuperar el valor correspondiente al patrón:

\[
x=
\frac{y-b}{m}
\]

por tanto:

\[
\boxed{
T_{\text{LM35,calibrado}}
=
\frac{
T_{\text{LM35}}-b
}{
m
}
}
\]

Esta misma transformación aparece dentro de la ecuación de inexactitud utilizada por el profesor en el Paso 4.

---

# 16. Inexactitud del proceso de calibración

## Fuente en los apuntes — Paso 4

El profesor define la inexactitud mediante:

\[
\boxed{
\sigma_P=
\sqrt{
\frac{1}{N}
\sum_{n=1}^{N}
\left(
\frac{y_{nk}-b}{m}
-y_n
\right)^2
}
}
\]

Esta fórmula deberá utilizarse en el software tal como aparece conceptualmente en los apuntes.

Donde:

- \(y_{nk}\): resultado del instrumento;
- \(m\): pendiente;
- \(b\): ordenada al origen;
- \(\frac{y_{nk}-b}{m}\): valor corregido mediante la calibración;
- \(y_n\): valor del patrón;
- \(N\): número de mediciones.

**No se mostrará esta cantidad bajo el nombre RMSE.**

En la interfaz deberá aparecer como:

\[
\boxed{\sigma_P\text{ — Inexactitud}}
\]

---

# 17. Certeza

La actividad solicita explícitamente estimar la **certeza**.

Sin embargo, en las diapositivas revisadas el profesor no presenta una ecuación denominada literalmente “certeza”.

Lo que sí presenta en el Paso 5 es una interpretación probabilística de la incertidumbre/inexactitud bajo un modelo gaussiano.

Por ello, hasta confirmar la terminología exacta con el profesor, la interfaz puede mostrar:

## Certeza asociada al intervalo de calibración

Según la presentación:

\[
\boxed{
x_n=y_n\pm\sigma_P
}
\]

con aproximadamente:

\[
\boxed{68\%}
\]

de probabilidad.

También:

\[
\boxed{
x_n=y_n\pm2\sigma_P
}
\]

con aproximadamente:

\[
\boxed{95\%}
\]

y:

\[
\boxed{
x_n=y_n\pm3\sigma_P
}
\]

con aproximadamente:

\[
\boxed{99.7\%}
\]

### Importante

En la interfaz debe indicarse como **Certeza / intervalo probabilístico asociado a \(\sigma_P\)** hasta que el profesor confirme si éste es exactamente el parámetro que espera bajo el nombre “certeza”.

No se debe sustituir por una métrica inventada.

---

# 18. Grado de acuerdo entre las mediciones

La actividad pide explícitamente:

> grado de acuerdo entre las mediciones.

En la presentación, el coeficiente \(r\) permite estudiar el grado de relación lineal entre patrón y resultado.

Por ello, dentro del resumen de calibración estática se mostrará:

\[
\boxed{\text{Coeficiente de correlación }r}
\]

No se mostrará \(R^2\).

Además, la actividad solicita específicamente evaluar la concordancia mediante Bland–Altman, por lo que el grado de acuerdo no se limitará únicamente a \(r\).

---

# 19. Concordancia mediante Bland–Altman

## Importante sobre la fuente

La actividad exige el gráfico de **Bland–Altman**, pero las diapositivas proporcionadas no desarrollan su fórmula.

Por tanto, las siguientes ecuaciones corresponden al procedimiento estándar requerido para poder cumplir con la actividad; no deben presentarse como una fórmula tomada de las diapositivas del profesor.

Para cada par de mediciones:

\[
T_{\text{Vernier},i}
\]

y:

\[
T_{\text{LM35},i}
\]

se calcula la media:

\[
\boxed{
M_i=
\frac{
T_{\text{Vernier},i}
+
T_{\text{LM35},i}
}{2}
}
\]

y la diferencia:

\[
\boxed{
D_i=
T_{\text{LM35},i}
-
T_{\text{Vernier},i}
}
\]

La diferencia media es:

\[
\boxed{
\bar D=
\frac{1}{N}
\sum_{i=1}^{N}D_i
}
\]

La desviación estándar de las diferencias es:

\[
\boxed{
s_D=
\sqrt{
\frac{
\sum_{i=1}^{N}(D_i-\bar D)^2
}{
N-1
}
}
}
\]

Los límites de concordancia se calculan como:

\[
\boxed{
L_{\text{sup}}=
\bar D+1.96s_D
}
\]

\[
\boxed{
L_{\text{inf}}=
\bar D-1.96s_D
}
\]

---

# 20. Gráfica Bland–Altman esperada

El eje horizontal será:

\[
\boxed{
M_i=
\frac{
T_{\text{Vernier},i}
+
T_{\text{LM35},i}
}{2}
}
\]

El eje vertical será:

\[
\boxed{
D_i=
T_{\text{LM35},i}
-
T_{\text{Vernier},i}
}
\]

La gráfica deberá mostrar:

- los 20 puntos;
- diferencia media \(\bar D\);
- límite superior;
- límite inferior.

Se utilizará para discutir la concordancia entre el LM35 y el Vernier.

---

# 21. Elementos que deben aparecer en la sección ESTÁTICA de la interfaz

La sección de calibración estática deberá contener **solamente** los elementos relacionados con los requisitos solicitados.

## 21.1 Datos principales

- número de mediciones realizadas;
- \(T_{\text{Vernier}}\);
- \(T_{\text{LM35}}\);
- estado estable;
- rango de temperaturas.

## 21.2 Precisión

- media;
- desviación estándar \(s\);
- desviación estándar de la media \(s_m\);
- RSD;
- coeficiente de variación \(CV\);
- varianza \(s^2\).

## 21.3 Exactitud

- comparación entre LM35 y Vernier;
- inexactitud \(\sigma_P\).

## 21.4 Certeza

- intervalo asociado a \(\sigma_P\):
  - \(1\sigma_P\) → 68 %;
  - \(2\sigma_P\) → 95 %;
  - \(3\sigma_P\) → 99.7 %.

## 21.5 Calibración lineal

- pendiente \(m\);
- ordenada \(b\);
- coeficiente de correlación \(r\);
- error de ganancia \(e_G=m-1\);
- error de corrimiento \(e_0=b\).

## 21.6 Concordancia

- gráfico Bland–Altman;
- diferencia media;
- límites de concordancia.

No deberán aparecer en esta sección:

- \(R^2\);
- MAE;
- RMSE;
- métricas adicionales no solicitadas.

---

# 22. Gráficas de la calibración estática

## Gráfica 1 — Datos en tiempo real

Eje horizontal:

\[
t
\]

Eje vertical:

\[
T
\]

Se muestran:

\[
T_{\text{Vernier}}(t)
\]

y:

\[
T_{\text{LM35}}(t)
\]

Su objetivo es comprobar que ambas mediciones se encuentran en condición aproximadamente estable antes de registrar cada punto.

---

## Gráfica 2 — Patrón vs. resultados

Ésta es la gráfica del Paso 2 de la presentación.

Eje \(x\):

\[
\boxed{T_{\text{Vernier}}}
\]

Eje \(y\):

\[
\boxed{T_{\text{LM35}}}
\]

Se muestran:

- los 20 puntos;
- la recta:

\[
\boxed{y=mx+b}
\]

- los valores de \(m\), \(b\) y \(r\).

---

## Gráfica 3 — Bland–Altman

Eje \(x\):

\[
\frac{
T_{\text{Vernier}}+
T_{\text{LM35}}
}{2}
\]

Eje \(y\):

\[
T_{\text{LM35}}-
T_{\text{Vernier}}
\]

Se muestran:

- \(\bar D\);
- \(L_{\text{sup}}\);
- \(L_{\text{inf}}\).

---

## Gráfica 4 — Histéresis, si se realizan ambos recorridos

Si se realizan recorridos ascendente y descendente, se mostrarán ambas trayectorias en función de la temperatura de referencia y se calculará \(H\%\). Si solo existe un recorrido, la gráfica y el parámetro se marcarán como `NOT_RUN`.
---

# 23. Tabla de datos estáticos

La tabla principal debe ser simple:

| Medición | \(T_{\text{Vernier}}\) | \(T_{\text{LM35}}\) | Estado |
|---:|---:|---:|---|
| 1 | ... | ... | estable |
| 2 | ... | ... | estable |
| ... | ... | ... | ... |
| 20 | ... | ... | estable |

Para los cálculos de precisión pueden conservarse internamente las muestras individuales tomadas durante cada nivel.

---

# 24. Resumen final esperado para la calibración estática

Al terminar las 20 mediciones la interfaz debe mostrar:

\[
\boxed{\text{Precisión}}
\]

\[
\boxed{\text{Exactitud}}
\]

\[
\boxed{\text{Certeza}}
\]

\[
\boxed{m}
\]

\[
\boxed{b}
\]

\[
\boxed{r}
\]

\[
\boxed{e_G=m-1}
\]

\[
\boxed{e_0=b}
\]

\[
\boxed{\sigma_P}
\]

y la concordancia Bland–Altman.

---

# 25. Calibración dinámica

## 25.1 Qué solicita la actividad

Para el LM35 se deberán obtener los parámetros de un **sistema de primer orden**:

1. constante de tiempo \(\tau\);
2. respuesta impulso;
3. respuesta escalón;
4. respuesta en frecuencia.

Además:

\[
\boxed{\text{las condiciones iniciales son diferentes de cero}}
\]

---

# 26. Modelo de primer orden del profesor

## Fuente en los apuntes — Dynamic Characteristics

La ecuación mostrada es:

\[
\boxed{
a_1\frac{dy(t)}{dt}
+
a_0y(t)
=
b_0x(t)
}
\]

El profesor también la expresa como:

\[
\boxed{
\tau\frac{dy(t)}{dt}
+
y(t)
=
Kx(t)
}
\]

y define:

\[
\boxed{
K=\frac{b_0}{a_0}
}
\]

como sensibilidad estática.

La función de transferencia mostrada es:

\[
\boxed{
H(s)=
\frac{K}{1+\tau s}
}
\]

Estas expresiones se mantendrán sin sustituirlas por otra notación.

---

# 27. Entrada y salida del modelo dinámico

Se utilizará:

\[
x(t)=\text{temperatura aplicada al LM35}
\]

\[
y(t)=\text{temperatura medida por el LM35}
\]

El experimento deberá provocar un cambio suficientemente rápido de temperatura para aproximar una entrada escalón.

---

# 28. Experimento para la respuesta escalón

Una opción adecuada es utilizar dos condiciones térmicas.

## Condición inicial

El LM35 se mantiene a:

\[
T_0
\]

hasta alcanzar equilibrio.

Por ejemplo:

\[
T_0\neq0
\]

## Condición final

Después se lleva rápidamente a un medio estable a:

\[
T_f
\]

con:

\[
T_f\neq T_0
\]

La computadora registra:

\[
y(t)
\]

durante todo el transitorio.

---

# 29. Condición inicial diferente de cero

La diapositiva del profesor muestra para una entrada escalón normalizada:

\[
\boxed{
y(t)=K(1-e^{-t/\tau})
}
\]

Esta expresión comienza en cero.

Como la actividad exige condiciones iniciales diferentes de cero, se utiliza la solución del mismo modelo de primer orden para una condición inicial general.

Partimos de:

\[
\tau\frac{dy}{dt}+y=Kx
\]

Si después del cambio:

\[
x(t)=x_f
\]

constante, entonces:

\[
\boxed{
y(t)=
Kx_f+
\left[y(0)-Kx_f\right]
e^{-t/\tau}
}
\]

Esta expresión conserva el modelo del profesor, pero incorpora:

\[
\boxed{y(0)\neq0}
\]

Si el sistema parte del equilibrio en \(x_0\):

\[
y(0)=Kx_0
\]

entonces:

\[
\boxed{
y(t)=
Kx_f+
K(x_0-x_f)e^{-t/\tau}
}
\]

---

# 30. Constante de tiempo \(\tau\)

La presentación muestra que, para un sistema de primer orden, en:

\[
\boxed{t=\tau}
\]

la respuesta alcanza aproximadamente:

\[
\boxed{63.7\%}
\]

del valor de estado estable en la representación normalizada del profesor.

Para condiciones iniciales diferentes de cero, se aplica el mismo concepto al **cambio total**.

Si:

\[
y_0=y(0)
\]

y:

\[
y_f=y(\infty)
\]

el cambio es:

\[
\Delta y=y_f-y_0
\]

El nivel asociado a una constante de tiempo es aproximadamente:

\[
\boxed{
y_\tau=
y_0+0.637(y_f-y_0)
}
\]

Siguiendo el valor mostrado en la diapositiva del profesor.

El tiempo necesario para alcanzar ese nivel corresponde aproximadamente a:

\[
\boxed{\tau}
\]

---

# 31. Ganancia estática \(K\)

A partir del modelo:

\[
\tau\dot y+y=Kx
\]

en estado estable:

\[
\dot y=0
\]

por tanto:

\[
y=Kx
\]

Para trabajar con un cambio alrededor de una condición inicial:

\[
\boxed{
K=
\frac{
y_f-y_0
}{
x_f-x_0
}
}
\]

Este valor se utilizará para construir la función de transferencia.

---

# 32. Función de transferencia

Una vez obtenidos \(K\) y \(\tau\):

\[
\boxed{
H(s)=
\frac{K}{1+\tau s}
}
\]

Éste será el modelo dinámico final del LM35.

---

# 33. Respuesta escalón

La expresión mostrada por el profesor para la respuesta normalizada de primer orden es:

\[
\boxed{
y(t)=
K(1-e^{-t/\tau})
}
\]

Para el experimento con condición inicial diferente de cero, la gráfica deberá utilizar la solución general:

\[
\boxed{
y(t)=
y_f+
(y_0-y_f)e^{-t/\tau}
}
\]

donde:

\[
y_0\neq0
\]

---

# 34. Respuesta impulso

La actividad solicita obtener la respuesta impulso.

Ésta no aparece escrita explícitamente para primer orden en las diapositivas proporcionadas, pero se obtiene directamente de la función de transferencia del profesor:

\[
H(s)=\frac{K}{1+\tau s}
\]

La transformada inversa produce:

\[
\boxed{
h(t)=
\frac{K}{\tau}
e^{-t/\tau}
}
\]

para:

\[
t\ge0
\]

Esta gráfica se calculará a partir de los parámetros \(K\) y \(\tau\) obtenidos experimentalmente.

---

# 35. Respuesta en frecuencia

La actividad también solicita la respuesta en frecuencia.

Se parte nuevamente de:

\[
H(s)=
\frac{K}{1+\tau s}
\]

y se sustituye:

\[
s=j\omega
\]

obteniendo:

\[
\boxed{
H(j\omega)=
\frac{K}{
1+j\omega\tau
}
}
\]

La magnitud es:

\[
\boxed{
|H(j\omega)|
=
\frac{
K
}{
\sqrt{
1+(\omega\tau)^2
}
}
}
\]

La fase es:

\[
\boxed{
\phi(\omega)=
-\tan^{-1}(\omega\tau)
}
\]

Estas expresiones se derivan directamente de la función de transferencia de primer orden mostrada por el profesor.

---

# 36. Gráficas de la calibración dinámica

La sección dinámica de la interfaz debe mostrar solamente lo solicitado.

## Gráfica 1 — Respuesta temporal experimental

Eje \(x\):

\[
t
\]

Eje \(y\):

\[
T_{\text{LM35}}
\]

Debe mostrar:

- condición inicial;
- cambio térmico;
- respuesta del LM35;
- estado final.

---

## Gráfica 2 — Determinación de \(\tau\)

Debe incluir:

- \(y_0\);
- \(y_f\);
- nivel correspondiente al 63.7 % del cambio;
- instante \(\tau\).

---

## Gráfica 3 — Respuesta escalón

Debe mostrar la respuesta del modelo de primer orden obtenida con:

\[
K
\]

y:

\[
\tau
\]

---

## Gráfica 4 — Respuesta impulso

Debe mostrar:

\[
h(t)=
\frac{K}{\tau}e^{-t/\tau}
\]

---

## Gráfica 5 — Respuesta en frecuencia

Debe representar:

- magnitud;
- fase;

en función de la frecuencia.

---

# 37. Elementos que deben aparecer en la sección DINÁMICA de la interfaz

Solamente:

- \(T_0\);
- \(T_f\);
- \(K\);
- \(\tau\);
- ecuación:

\[
\tau\frac{dy}{dt}+y=Kx
\]

- función de transferencia:

\[
H(s)=\frac{K}{1+\tau s}
\]

- respuesta escalón;
- respuesta impulso;
- respuesta en frecuencia.

No se agregarán otros indicadores que no sean necesarios para cumplir el inciso C.

---

# 38. Datos a almacenar

## 38.1 Para la calibración estática

```text
tiempo
numero_medicion
temperatura_vernier
temperatura_lm35
estado_estable
```

Las muestras internas utilizadas para calcular la precisión también deben conservarse.

## 38.2 Para la calibración dinámica

```text
tiempo
temperatura_entrada
temperatura_lm35
```

Estos datos permitirán calcular:

\[
K
\]

y:

\[
\tau
\]

y generar las respuestas solicitadas.

---

# 39. Flujo de trabajo completo

## Parte estática

```text
INICIAR
   │
   ↓
Conectar Vernier y ESP32
   │
   ↓
Leer ambos sensores
   │
   ↓
Estabilizar temperatura
   │
   ↓
Registrar punto
   │
   ↓
Repetir hasta 20 mediciones
   │
   ↓
Mínimos cuadrados
   │
   ├── m
   ├── b
   └── r
   │
   ↓
Calcular:
   ├── Precisión
   ├── Exactitud
   ├── Certeza
   ├── eG = m − 1
   ├── e0 = b
   ├── σP
   └── Bland–Altman
```

## Parte dinámica

```text
Estabilizar LM35 en T0 ≠ 0
   │
   ↓
Aplicar cambio de temperatura
   │
   ↓
Registrar y(t)
   │
   ↓
Obtener τ
   │
   ↓
Obtener K
   │
   ↓
H(s) = K/(1 + τs)
   │
   ├── Respuesta escalón
   ├── Respuesta impulso
   └── Respuesta en frecuencia
```

---

# 40. Resumen de correspondencia con las diapositivas

| Elemento | Fuente principal |
|---|---|
| Exactitud | Diapositiva 6 |
| Precisión | Diapositiva 7 |
| Desviación estándar, RSD, CV, varianza | Diapositiva 14 |
| Concepto de calibración | Diapositiva 15 |
| Rango en intervalos discretos | Diapositiva 16 |
| \(y=mx+b\), \(m\), \(b\), \(r\), mínimos cuadrados | Diapositiva 17 |
| \(e_G=m-1\), \(e_0=b\) | Diapositiva 18 |
| \(\sigma_P\), inexactitud | Diapositiva 19 |
| Intervalos \(1\sigma_P\), \(2\sigma_P\), \(3\sigma_P\) | Diapositiva 20 |
| Características dinámicas | Diapositiva 28 |
| \(\tau\dot y+y=Kx\), \(H(s)=K/(1+\tau s)\) | Diapositiva 29 |
| Respuesta de primer orden y 63.7 % | Diapositiva 30 |
| Bland–Altman | Solicitado por la actividad; fórmula no desarrollada en las diapositivas proporcionadas |
| Respuesta impulso de primer orden | Solicitada por la actividad; derivada de \(H(s)\) |
| Respuesta en frecuencia de primer orden | Solicitada por la actividad; derivada de \(H(s)\) |

---

# 41. Qué NO debe aparecer en la interfaz corregida

Para mantener exactamente el enfoque solicitado:

- no usar \(R^2\) como indicador principal;
- no usar MAE;
- no usar RMSE;
- no sustituir \(\sigma_P\) por otro nombre;
- no sustituir el coeficiente \(r\) por \(R^2\);
- no agregar métricas que no sean necesarias para los incisos B y C.

---

# 42. Resultado final esperado del proyecto

Al finalizar la calibración estática deberán quedar determinados:

\[
\boxed{
\text{Precisión}
}
\]

\[
\boxed{
\text{Exactitud}
}
\]

\[
\boxed{
\text{Certeza}
}
\]

\[
\boxed{
m,\;b,\;r
}
\]

\[
\boxed{
e_G=m-1
}
\]

\[
\boxed{
e_0=b
}
\]

\[
\boxed{
\sigma_P
}
\]

y la concordancia mediante Bland–Altman.

Al finalizar la calibración dinámica deberán quedar determinados:

\[
\boxed{
K
}
\]

\[
\boxed{
\tau
}
\]

\[
\boxed{
H(s)=
\frac{K}{1+\tau s}
}
\]

junto con:

\[
\boxed{
\text{respuesta escalón}
}
\]

\[
\boxed{
\text{respuesta impulso}
}
\]

\[
\boxed{
\text{respuesta en frecuencia}
}
\]

considerando que la temperatura inicial es diferente de cero.

---

# 43. Pendientes antes de programar

Antes de construir el código definitivo todavía se deben confirmar:

1. modelo exacto de la sonda Vernier;
2. driver de Python del Vernier;
3. forma de conexión USB;
4. frecuencia de adquisición;
5. configuración real del ADC del ESP32;
6. rango experimental final;
7. confirmar si el rango debe ser exactamente \(50^\circ C\rightarrow100^\circ C\);
8. confirmar con el profesor qué definición desea específicamente para “certeza”.

Una vez confirmados estos puntos se podrá diseñar la interfaz final y posteriormente implementar la adquisición en tiempo real.

---

# Seguimiento de cambios

- **2026-09-13:** documento de cálculos separado de la referencia estable de drivers.
- **2026-09-13:** se conserva la versión matemática corregida como base actual.
- Este documento queda deliberadamente modificable.
