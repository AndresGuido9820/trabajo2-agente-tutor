# HU-30 — Bienvenida inteligente: "¿dónde iba?" al volver

**Como** estudiante **quiero** que al volver a una clase el tutor me
resuma en qué íbamos y me proponga cómo seguir **para** retomar en
segundos, sin releer todo el historial.

## Qué hace, explícito

1. Al entrar a una clase CON historial y con >8 horas desde el último
   mensaje, el tutor abre con una **tarjeta de reencuentro** generada por
   el LLM a partir de los últimos ~12 mensajes + estado del progreso:
   - "La última vez viste X y te quedaste en Y (paso 4/7)."
   - "Te costó: Z" (si hubo fallos anotados).
   - Tres chips: **"Continuar donde iba →"**, **"Repásame lo anterior en
     2 min"** (mini-resumen en el chat), **"Ir directo a la evaluación"**
     (solo si está disponible).
2. El resumen NO avanza la lección (es un mensaje informativo; contrato
   `{avanza: false}` implícito: se genera con un prompt propio).
3. Si han pasado <8 h, se mantiene el comportamiento actual (continuar sin
   ceremonia). El umbral vive en `config.HORAS_PARA_REENCUENTRO = 8`.
4. La tarjeta queda en el historial del chat (rol `tutor`).

## API

```
POST /api/clase/{i}/reencuentro → {texto, evaluacion_disponible}
   (el front lo llama al abrir la clase si el último mensaje es viejo;
    la marca de tiempo del último mensaje ya existe en la tabla chat)
GET  /api/historial/{canal} → cada mensaje incluye "creado_en"
```

## Tareas

- [ ] `db.py`: exponer `creado_en` en `historial_chat`.
- [ ] `prompts.py`: `prompt_reencuentro(ultimos_mensajes, progreso_resumen)`.
- [ ] `agente.py`: `reencuentro(indice)` (usa historial de BD + progreso).
- [ ] Front: detectar antigüedad al abrir la clase; tarjeta con los 3 chips.
- [ ] Pruebas: umbral de horas, contenido del prompt (mensajes+progreso),
      no-avance de la lección, chips correctos según estado.

## Casos borde

- Clase sin historial → sin reencuentro (flujo actual de primera vez).
- Historial enorme → solo últimos 12 mensajes al prompt (cota de tokens).
- Reloj del sistema raro (mensaje "futuro") → tratar como reciente.

## Pruebas

`test_reencuentro_solo_tras_umbral_de_horas` · `test_prompt_incluye_mensajes_y_progreso`
· `test_reencuentro_no_avanza_paso` · `test_chip_evaluacion_solo_si_disponible`
