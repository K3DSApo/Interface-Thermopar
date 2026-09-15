---
title: Calibración de LM35 y termopar — índice del proyecto
type: proyecto
status: En diseño
created: 2026-09-13
updated: 2026-09-13
orchestrator: Hermes
workspace: Interface Thermopar
herdr_workspace_id: wH
canonical_document: true
---

# Calibración de LM35 y termopar

Este archivo es el índice del proyecto. El contenido se separó en una referencia estable de drivers y un documento modificable de cálculos.

## Documentos

### Goal del proyecto

Archivo: `goal.md`

Contiene el objetivo normativo, los incisos de evaluación A–E, la rúbrica y la fecha de la demostración presencial.

**Este archivo define qué debe lograrse.**

### Referencia estable de drivers

Archivo: `Drivers Vernier Go Direct.md`

Contiene exclusivamente enlaces, `godirect`, `godirect-py`, `godirect-examples`, USB/BLE, `gdx`, dependencias, descubrimiento de canales y límites de comunicación.

**No se modifica cuando cambien los cálculos.**

### Documento modificable de cálculos

Archivo: `Cálculos y calibración del LM35.md`

Contiene el planteamiento estático y dinámico, fórmulas, métricas, Bland–Altman, precisión, exactitud, certeza, `sigma_P`, `K` y `tau`.

**Puede modificarse en futuras revisiones.**

### Prototipo base de la interfaz

Archivo: `02_Interfaz/interfaz_calibracion_LM35_v3.html`

Es la base visual y funcional inicial para desarrollar la actividad. Actualmente usa datos simulados, muestra conexiones representadas visualmente y todavía no implementa la comunicación real con ESP32 ni Vernier.

**Este archivo es el punto de partida de la interfaz; las fórmulas y métricas deben validarse contra `goal.md` y `Cálculos y calibración del LM35.md`.**

## Estado K3DS / HerDR

- Workspace: `Interface Thermopar` (`wH`).
- `architect`: `wH:p1`.
- `researcher`: `wH:p2`.
- `builder`: `wH:p3`.
- Estado: agentes preparados e inactivos.
- No hay implementación ni mediciones reales iniciadas.

## Límites

- Separar siempre drivers estables y cálculos modificables.
- La separación no autoriza instalar paquetes, modificar `udev`, conectar hardware ni iniciar mediciones.
- Los datos crudos, cuando existan, se conservarán sin sobrescribir.

## Bitácora

- **2026-09-13:** proyecto separado en referencia estable de drivers y documento modificable de cálculos.
