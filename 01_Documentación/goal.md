---
title: Goal — Calibración estática y dinámica del LM35
type: objetivo-del-proyecto
status: vigente
project: Calibración de LM35 y termopar
source: message.txt proporcionado por David
---

# Goal del proyecto

## Objetivo general

Determinar los parámetros de calibración estática y dinámica de un sensor de temperatura **LM35**, utilizando un **termopar Vernier como patrón de calibración**.

El sensor se puede modelar como un sistema de primer orden y se deben considerar condiciones iniciales diferentes de cero.

## A) Automatización del proceso — 35 puntos

El proceso de calibración deberá realizarse automáticamente mediante un equipo de cómputo conectado directamente a los sensores y mediante código que calcule de forma inmediata:

- todos los parámetros de calibración;
- las gráficas;
- las mediciones importantes.

Los resultados deberán mostrarse en tiempo real.

## B) Calibración estática — 15 puntos

Realizar **20 mediciones** en un rango de temperatura incremental de al menos **50 °C o más**.

Estimar los valores de:

- precisión;
- exactitud;
- certeza;
- error de ganancia;
- error de corrimiento;
- grado de acuerdo entre las mediciones.

Estimar la concordancia mediante un gráfico de **Bland–Altman** y discutir los resultados obtenidos.

## C) Calibración dinámica — 15 puntos

Realizar el procedimiento necesario para obtener los parámetros de un sistema de primer orden para el sensor de temperatura LM35:

- constante de tiempo;
- respuesta impulso;
- respuesta escalón;
- respuesta en frecuencia.

Se deben considerar condiciones iniciales diferentes de cero.

## D) Reporte IEEE — 20 puntos

Elaborar un reporte en formato IEEE, con un máximo de **4 páginas a doble columna**, considerando las secciones discutidas en las políticas de conducción del curso.

## E) Presentación en Canva — 15 puntos

Utilizar la plataforma Canva para realizar una presentación que incluya:

- diseño del experimento;
- resultados obtenidos;
- principales conclusiones individuales derivadas de este tipo de ejercicios.

## Evaluación presencial

La evaluación del examen se realizará de forma presencial, con el prototipo funcionando:

- **Fecha:** viernes 18 de septiembre;
- **Horario:** 09:00–11:00;
- **Lugar:** laboratorio.

## Relación con los documentos del proyecto

Este archivo define el objetivo y los criterios de evaluación. No sustituye:

- `Drivers Vernier Go Direct.md`, que contiene la referencia estable de comunicación con Vernier;
- `Cálculos y calibración del LM35.md`, que contiene el planteamiento matemático modificable;
- `Calibración de LM35 y termopar.md`, que funciona como índice del proyecto.

## Bitácora

- **2026-09-13:** se incorporó el objetivo y la rúbrica del examen a partir de `message.txt`.
