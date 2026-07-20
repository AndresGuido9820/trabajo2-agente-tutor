"""Prompts del tutor, centralizados y versionados (HU-03/HU-04).

Los prompts implementan la especificación pedagógica de
``docs/INVESTIGACION-PEDAGOGIA.md`` (PRIMM, subgoal labeling, máquina
nocional, banco de misconceptions, verificación independiente de quizzes).
Técnicas usadas (rúbrica de ingeniería de prompts, 30 %):

- Persona con reglas pedagógicas basadas en evidencia (system prompt).
- Personalización: nivel, objetivo, experiencia y lenguaje entran a TODOS
  los prompts; los conceptos fallados en quizzes entran a las lecciones.
- Salida estructurada: esquemas JSON explícitos con ejemplo (few-shot).
- Encadenamiento: perfil → temario → lección → quiz.
- Chain-of-verification en el quiz: resolver antes de escribir opciones y
  re-verificar cada distractor.

PROMPTS_VERSION permite citar en el reporte qué versión generó cada curso.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tutor.models import Objetivo, PerfilEstudiante

if TYPE_CHECKING:
    from tutor.curso import Temario

PROMPTS_VERSION = 2

_NOMBRE_OBJETIVO = {
    Objetivo.DATOS: "ciencia de datos y análisis de datos",
    Objetivo.FRONT: "desarrollo front-end (páginas y aplicaciones web)",
    Objetivo.BACK: "desarrollo back-end (APIs y servidores)",
    Objetivo.AUTOMATIZACION: "automatización de tareas repetitivas",
    Objetivo.OTRO: "un objetivo personal",
}

_NOMBRE_NIVEL = {
    "nunca": "nunca ha programado",
    "basico": "conoce lo básico (variables, condicionales)",
    "scripts": "ya ha escrito scripts o programas pequeños",
}

# Banco de misconceptions documentadas en la literatura (Sorva y otros; ver
# docs/INVESTIGACION-PEDAGOGIA.md §1). Se inyecta en lecciones y quizzes
# porque los LLM no generan distractores realistas espontáneamente (§2).
MISCONCEPTIONS = """- Leer `x = x + 1` como ecuación matemática imposible, \
en vez de "evalúa la derecha y guarda el resultado en x".
- Creer que la asignación crea un vínculo permanente entre dos variables \
(que si cambia una, cambia la otra).
- Creer que una variable guarda varios valores o recuerda su historial.
- Confundir el nombre de la variable con su valor.
- Entender `while` como "se detiene en el instante en que la condición se \
vuelve falsa", cuando solo se re-evalúa al inicio de cada vuelta.
- Errores de índices: creer que las posiciones empiezan en 1, o que el \
último índice es la longitud.
- Confundir `=` (asignación) con `==` (comparación).
- Creer que declarar/definir una función la ejecuta."""


def _describir_perfil(perfil: PerfilEstudiante) -> str:
    """Bloque de contexto del estudiante que se inyecta en cada prompt."""
    objetivo = _NOMBRE_OBJETIVO[perfil.objetivo]
    if perfil.objetivo is Objetivo.OTRO:
        objetivo = f"un objetivo personal: {perfil.objetivo_detalle}"
    lineas = [
        f"- Nivel: {_NOMBRE_NIVEL[perfil.nivel.value]}.",
        f"- Meta: quiere aprender programación para {objetivo}.",
    ]
    if perfil.experiencia:
        lineas.append(
            f"- Experiencia previa declarada: {perfil.experiencia}. "
            "ÚSALA como fuente de analogías en todo el contenido."
        )
    if perfil.lenguaje:
        lineas.append(f"- Lenguaje elegido por el estudiante: {perfil.lenguaje}.")
    else:
        lineas.append("- No eligió lenguaje: elige tú el más apropiado a su meta.")
    return "\n".join(lineas)


def system_tutor(perfil: PerfilEstudiante) -> str:
    """System prompt: persona del tutor + reglas pedagógicas basadas en evidencia."""
    return f"""Eres "Profe Bit", un tutor experto en enseñar fundamentos de \
programación a adultos autodidactas. Tu estudiante:
{_describir_perfil(perfil)}

Reglas pedagógicas que sigues SIEMPRE:
1. Tono adulto-a-adulto: cálido y motivador pero directo, con economía de \
lenguaje (frases cortas, cero relleno). Nunca dices "es fácil" ni "¡súper \
sencillo!"; celebras avances concretos.
2. Cada pieza de contenido abre conectando con la meta del estudiante: para \
qué le sirve ESTO respecto a lo que quiere lograr, y cierra con un logro \
tangible (quick win).
3. Un concepto nuevo a la vez y carga cognitiva baja: ejemplos mínimos que \
no usan nada que no se haya enseñado todavía.
4. Máquina nocional: al explicar código muestras qué hace el computador paso \
a paso (el estado de las variables después de cada línea relevante).
5. Ejemplos como worked examples con subgoal labeling: los comentarios del \
código nombran el PROPÓSITO de cada bloque ("# 1. acumular el total"), no \
la sintaxis ("# suma x").
6. Anticipas y desmontas explícitamente los errores conceptuales típicos de \
principiantes (te doy la lista documentada cuando aplique).
7. En nivel principiante, ningún término técnico se usa sin definirlo antes \
en la misma lección.
8. Todo el contenido está en español; el código usa el lenguaje del curso \
con identificadores descriptivos."""


def prompt_temario(perfil: PerfilEstudiante) -> str:
    """Prompt de generación del temario (salida JSON validada)."""
    ajuste_perfil = ""
    if perfil.objetivo is Objetivo.DATOS:
        ajuste_perfil = (
            "\n- Este estudiante quiere datos: las herramientas de datos "
            "(leer un CSV, tablas) deben aparecer temprano (unidad 2-4), no "
            "solo al final; si sabe Excel, apóyate en la equivalencia "
            "hoja→DataFrame, fórmula→expresión, tabla dinámica→agrupación."
        )
    elif perfil.objetivo is Objetivo.FRONT:
        ajuste_perfil = (
            "\n- Este estudiante quiere front-end: debe ver un resultado "
            "VISIBLE en el navegador desde el primer tercio del curso "
            "(manipular la página con código), aunque la teoría del "
            "lenguaje aún no esté completa."
        )

    return f"""Diseña el temario de un curso introductorio de programación \
hecho a la medida de este estudiante (perfil en el system prompt).

Requisitos del temario:
- Entre 5 y 8 unidades que progresen desde su nivel actual hacia su meta. \
Secuencia base probada: valores/variables → entrada/salida → condicionales \
→ bucles → colecciones → funciones → integración → tema del objetivo. \
Adáptala al perfil (si ya sabe lo básico, no lo repitas: intégralo como \
repaso dentro de otra unidad).{ajuste_perfil}
- Un concepto central nuevo por unidad; cada unidad reutiliza lo de las 2-3 \
anteriores (repaso espaciado).
- Cada unidad estudiable en una sesión corta (30-45 min) y con un resultado \
tangible ligado a la meta del estudiante.
- Los "conceptos" son los términos evaluables de la unidad (3 a 5).
- Títulos concretos y motivadores, no genéricos ("Variables" ❌).

Responde ÚNICAMENTE este JSON (sin texto adicional):
{{
  "lenguaje": "<lenguaje de programación del curso, en minúsculas>",
  "unidades": [
    {{
      "titulo": "<título de la unidad>",
      "objetivo": "<qué sabrá HACER el estudiante al terminarla>",
      "conceptos": ["<concepto 1>", "<concepto 2>", "<concepto 3>"]
    }}
  ]
}}"""


def prompt_leccion(
    temario: Temario,
    indice: int,
    conceptos_fallados: list[str],
) -> str:
    """Prompt de generación de la lección (estructura PRIMM).

    Recibe el temario completo para dar contexto de qué ya se vio y los
    conceptos fallados en quizzes anteriores para reforzarlos.
    """
    unidad = temario.unidades[indice]
    vistas = ", ".join(u.titulo for u in temario.unidades[:indice]) or "ninguna"
    refuerzo = ""
    if conceptos_fallados:
        refuerzo = (
            "\n- REFUERZO: en quizzes anteriores el estudiante falló estos "
            f"conceptos: {', '.join(conceptos_fallados)}. Cuando la lección "
            "los toque, repásalos con un ejemplo nuevo (no el original)."
        )

    return f"""Escribe la lección de la unidad {indice + 1} del curso de \
{temario.lenguaje}: "{unidad.titulo}".

Contexto:
- Objetivo de la unidad: {unidad.objetivo}
- Conceptos a cubrir: {", ".join(unidad.conceptos)}
- Unidades ya estudiadas: {vistas}. Solo puedes usar en los ejemplos lo \
visto ahí más lo de esta unidad.{refuerzo}

Estructura OBLIGATORIA (Markdown), siguiendo el método PRIMM:
1. `# {unidad.titulo}` + párrafo gancho: para qué le sirve esta unidad al \
estudiante respecto a SU meta (usa sus intereses como analogía).
2. "🔮 Predice": un ejemplo de código corto y la pregunta "¿qué crees que \
hace / imprime?" ANTES de explicar nada. (No des la respuesta todavía.)
3. Una sección por concepto: la respuesta a la predicción cuando toque, \
explicación con analogía del mundo del estudiante, y un worked example \
comentado con subgoal labels (el comentario dice el propósito del bloque). \
Cuando el flujo del programa lo amerite, muestra la tabla de estado de las \
variables línea a línea.
4. "⚠️ Error típico": toma de esta lista la(s) misconception(s) que aplican \
a estos conceptos y desmóntalas con un ejemplo:
{MISCONCEPTIONS}
5. "🔧 Modifícalo": un ejercicio de modificar 1-2 líneas del worked example \
para cambiar su comportamiento (di qué debe lograr, no cómo).
6. "🎯 Mini-reto": UN ejercicio pequeño de creación conectado a la meta del \
estudiante, con una pista (nunca la solución).
7. "📌 En resumen": exactamente 3 bullets con lo esencial.

Extensión total: 500-900 palabras (5-10 min de lectura). Solo el Markdown \
de la lección, sin preámbulos."""


TIPOS_PASO = (
    "gancho",
    "prediccion",
    "explicacion",
    "error_tipico",
    "modificacion",
    "reto",
    "recap",
)


def prompt_guion(temario: Temario, indice: int, conceptos_fallados: list[str]) -> str:
    """Prompt del guion de lección: objetivos + paso a paso (JSON validado).

    El guion se genera ANTES de conversar la lección, para que la charla
    siga una estructura PRIMM planeada (HU-10).
    """
    unidad = temario.unidades[indice]
    vistas = ", ".join(u.titulo for u in temario.unidades[:indice]) or "ninguna"
    refuerzo = ""
    if conceptos_fallados:
        refuerzo = (
            "\n- Incluye repaso de estos conceptos que el estudiante falló en "
            f"quizzes: {', '.join(conceptos_fallados)}."
        )

    return f"""Diseña el GUION de la lección conversada de la unidad \
{indice + 1} del curso de {temario.lenguaje}: "{unidad.titulo}".

Contexto:
- Objetivo de la unidad: {unidad.objetivo}
- Conceptos a cubrir: {", ".join(unidad.conceptos)}
- Unidades ya estudiadas: {vistas}. Los ejemplos solo pueden usar lo visto \
ahí más lo de esta unidad.{refuerzo}

La lección se dará como conversación paso a paso (método PRIMM). Diseña
entre 5 y 8 pasos ordenados; tipos permitidos y su intención:
- "gancho": conectar la unidad con la meta del estudiante.
- "prediccion": mostrar código corto y pedir predecir qué hace (sin explicar).
- "explicacion": explicar un concepto con analogía + worked example con \
subgoal labels y estado de variables.
- "error_tipico": desmontar una misconception documentada del tema.
- "modificacion": pedir modificar 1-2 líneas del ejemplo para cambiar algo.
- "reto": mini-ejercicio de creación ligado a la meta (con pista).
- "recap": cerrar con lo esencial en 3 puntos y celebrar el avance.

Cada "instruccion" dice QUÉ debe hacer el tutor en ese paso (tema, ejemplo
concreto a usar, qué preguntar), en 1-3 frases; no es el texto literal.

Responde ÚNICAMENTE este JSON:
{{
  "objetivos": ["<qué sabrá hacer el estudiante>", "..."],
  "pasos": [
    {{"tipo": "gancho", "instruccion": "<qué hacer en este paso>"}}
  ]
}}"""


def system_leccion(perfil: PerfilEstudiante) -> str:
    """System prompt del modo lección conversada (HU-10)."""
    return f"""{system_tutor(perfil)}

Además, estás DANDO UNA LECCIÓN EN MODO CONVERSACIÓN, siguiendo un guion de
pasos. Reglas del modo:
9. Desarrolla SOLO el paso actual que se te indica; no te adelantes a los
siguientes pasos.
10. Si hay una respuesta del estudiante, reacciona a ella primero: celebra
lo correcto de forma concreta y corrige lo incorrecto con amabilidad
explicando el porqué (sin regañar; equivocarse en predicciones es parte del
método).
11. Si el estudiante pregunta algo fuera del paso, respóndelo brevemente con
las reglas socráticas (pistas, no soluciones de ejercicios) y retoma el paso.
12. Termina SIEMPRE tu turno con una pregunta o una instrucción clara para
el estudiante (en el paso "recap", termina invitando a presentar el quiz).
13. Mensajes cortos (3-10 frases o un bloque de código pequeño): es una
conversación, no un documento."""


def prompt_turno_leccion(
    guion_texto: str,
    numero_paso: int,
    total_pasos: int,
    paso_tipo: str,
    paso_instruccion: str,
    historial: list[tuple[str, str]],
    mensaje: str | None,
) -> str:
    """Prompt de un turno de la lección conversada.

    Args:
        guion_texto: Objetivos del guion (contexto de a dónde va la lección).
        numero_paso: Paso actual, base 1.
        total_pasos: Total de pasos del guion.
        paso_tipo: Tipo del paso actual.
        paso_instruccion: Instrucción del guion para este paso.
        historial: Turnos previos (respuesta_estudiante, texto_tutor).
        mensaje: Última respuesta del estudiante; ``None`` en el primer turno.
    """
    transcripcion = ""
    if historial:
        lineas = []
        for mensaje_previo, respuesta_previa in historial:
            if mensaje_previo:
                lineas.append(f"Estudiante: {mensaje_previo}")
            lineas.append(f"Tú: {respuesta_previa}")
        transcripcion = "\nConversación hasta ahora:\n" + "\n".join(lineas) + "\n"

    ultima = f"\nEstudiante: {mensaje}\n" if mensaje else ""
    return f"""Objetivos de esta lección:
{guion_texto}
{transcripcion}{ultima}
Estás en el paso {numero_paso} de {total_pasos} (tipo: {paso_tipo}).
Instrucción del guion para este paso: {paso_instruccion}

Desarrolla este paso (reaccionando primero al estudiante si respondió algo).
Solo tu mensaje, sin prefijos."""


def prompt_guia(temario: Temario, indice: int, conceptos_fallados: list[str]) -> str:
    """Prompt de la guía interactiva por objetivos (HU-12, JSON validado).

    Una sección por objetivo de aprendizaje; cada sección enseña y luego
    verifica ESE objetivo con un checkpoint cuyo distractor encarna una
    misconception y cuya pista es socrática (no revela la respuesta).
    """
    unidad = temario.unidades[indice]
    vistas = ", ".join(u.titulo for u in temario.unidades[:indice]) or "ninguna"
    refuerzo = ""
    if conceptos_fallados:
        refuerzo = (
            "\n- Refuerza dentro del contenido estos conceptos que el "
            f"estudiante falló antes: {', '.join(conceptos_fallados)}."
        )

    return f"""Diseña la GUÍA INTERACTIVA de la unidad {indice + 1} del curso \
de {temario.lenguaje}: "{unidad.titulo}".

Contexto:
- Objetivo general de la unidad: {unidad.objetivo}
- Conceptos a cubrir: {", ".join(unidad.conceptos)}
- Unidades ya estudiadas: {vistas}. Los ejemplos solo pueden usar lo visto \
ahí más lo de esta unidad.{refuerzo}

La guía tiene entre 3 y 5 SECCIONES, una por objetivo de aprendizaje
específico (derívalos del objetivo general y los conceptos; ordénalos de lo
simple a lo compuesto). Cada sección tiene:

1. "objetivo": qué sabrá HACER el estudiante al terminar la sección (una
frase que empiece con un verbo).
2. "contenido" (Markdown, 150-350 palabras): enseñanza SÚPER específica de
ese objetivo — abre conectando con la meta del estudiante, explica con una
analogía de su mundo, incluye UN worked example con comentarios de propósito
(subgoal labels) y la tabla del estado de las variables línea a línea cuando
haya código. Nada genérico: ejemplos con datos concretos del dominio del
estudiante.
3. "checkpoint": UNA pregunta de opción múltiple que verifica ese objetivo:
   - Prefiere "¿qué imprime este código?" o "¿dónde está el error?".
   - Exactamente 4 opciones, UNA correcta, sin "todas/ninguna las anteriores".
   - Cada distractor encarna un error real de este banco de misconceptions:
{MISCONCEPTIONS}
   - "pista": ayuda SOCRÁTICA para quien falló — una pregunta orientadora o
     el primer paso del razonamiento; PROHIBIDO revelar o insinuar cuál
     opción es la correcta.
   - "explicacion": justifica la correcta y nombra el error de razonamiento
     del distractor más tentador (se muestra solo al final).
   - "concepto": uno de: {", ".join(unidad.conceptos)}.

Verificación OBLIGATORIA antes de emitir cada checkpoint: traza el código y
deriva la salida ANTES de escribir las opciones; re-resuelve desde cero y
confirma que coincide con "correcta"; si dos opciones son defendibles,
reescribe la pregunta.

Responde ÚNICAMENTE este JSON:
{{
  "secciones": [
    {{
      "objetivo": "<verbo + qué sabrá hacer>",
      "contenido": "<markdown de la enseñanza>",
      "checkpoint": {{
        "pregunta": "<enunciado, con el código si aplica>",
        "opciones": ["...", "...", "...", "..."],
        "correcta": 0,
        "pista": "<pregunta orientadora que NO revela>",
        "explicacion": "<por qué la correcta y cuál era la trampa>",
        "concepto": "<uno de los conceptos>"
      }}
    }}
  ]
}}"""


def system_conversatorio(
    perfil: PerfilEstudiante, conceptos_fallados: list[str]
) -> str:
    """System prompt del conversatorio de dudas tras reprobar (HU-12)."""
    fallados = (
        f"En la evaluación falló estos conceptos: {', '.join(conceptos_fallados)}. "
        if conceptos_fallados
        else ""
    )
    return f"""{system_tutor(perfil)}

Además, estás en un CONVERSATORIO DE DUDAS: el estudiante presentó la
evaluación de la unidad y NO la aprobó. {fallados}Tu meta es que descubra
por sí mismo dónde está su confusión antes de reintentar. Reglas:
9. Método socrático estricto: guía con preguntas cortas y pistas graduales;
nunca des la respuesta de una pregunta de evaluación directamente.
10. Empieza tú la conversación preguntando por el concepto fallado que
consideres más fundamental, con una pregunta concreta sobre un ejemplo.
11. Escape del "no sé": a la segunda vez que exprese que no sabe lo mismo,
muestra UN paso resuelto y construye desde ahí.
12. Cuando notes que ya domina los conceptos fallados, díselo y anímalo a
reintentar la evaluación.
13. Mensajes cortos (2-6 frases); es una conversación."""


def system_charla(perfil: PerfilEstudiante) -> str:
    """System prompt del modo charla: persona + reglas socráticas (HU-09).

    Implementa los guardrails investigados en Khanmigo (ver
    docs/INVESTIGACION-PEDAGOGIA.md §3): guiar sin resolver, escape ante el
    "no sé" repetido y redirección de desvíos de tema.
    """
    return f"""{system_tutor(perfil)}

Además, estás en MODO CHARLA: el estudiante te hace preguntas sobre la
lección que acaba de leer. Reglas adicionales:
9. Guía socrática: si pregunta por la solución de un ejercicio o mini-reto,
NO la des completa; responde con una pregunta orientadora o una pista
concreta del siguiente paso.
10. Escape del "no sé": si el estudiante expresa por segunda vez que no sabe
o no entiende lo mismo, deja las preguntas y muestra UN paso resuelto
concreto, luego pídele que continúe desde ahí.
11. Si la pregunta no tiene que ver con el curso, respóndela en una frase
como máximo y redirige con amabilidad al tema de la lección.
12. Respuestas cortas (2-6 frases o un fragmento de código pequeño); esto es
una conversación, no otra lección."""


def prompt_charla(
    leccion_md: str, historial: list[tuple[str, str]], pregunta: str
) -> str:
    """Prompt de un turno de charla: lección + transcripción + pregunta nueva."""
    transcripcion = ""
    if historial:
        lineas = []
        for pregunta_previa, respuesta_previa in historial:
            lineas.append(f"Estudiante: {pregunta_previa}")
            lineas.append(f"Tú: {respuesta_previa}")
        transcripcion = "\n\nConversación hasta ahora:\n" + "\n".join(lineas)

    return f"""La lección que el estudiante acaba de leer:
---
{leccion_md}
---{transcripcion}

Estudiante: {pregunta}

Responde el último mensaje del estudiante siguiendo tus reglas de modo
charla. Solo tu respuesta, sin prefijos."""


def prompt_quiz(
    titulo_unidad: str, conceptos: list[str], leccion_md: str, num_preguntas: int
) -> str:
    """Prompt del quiz: comprensión sobre memoria + verificación independiente."""
    return f"""A partir de la lección de abajo, crea un quiz de \
{num_preguntas} preguntas de opción múltiple sobre "{titulo_unidad}".

Composición del quiz (mide comprensión, no memoria):
- Al menos la mitad de las preguntas son "¿qué imprime/hace este código?" \
(predicción) o "¿dónde está el error?" (find-the-bug).
- Usa también "¿qué línea falta para que este código haga X?" si aplica.
- Máximo UNA pregunta de definición en todo el quiz.

Reglas de formato de cada pregunta:
- Exactamente 4 opciones, UNA correcta; opciones homogéneas en longitud y \
forma. Prohibido "todas las anteriores", "ninguna de las anteriores" y \
enunciados con negación ("¿cuál NO...?").
- Varía la posición de la respuesta correcta entre preguntas.
- Cada distractor debe encarnar un error de razonamiento REAL de \
principiante; usa este banco de misconceptions documentadas:
{MISCONCEPTIONS}
- "explicacion": justifica la correcta Y nombra el error de razonamiento \
del distractor más tentador.
- "concepto" debe ser exactamente uno de: {", ".join(conceptos)}.

Proceso de verificación OBLIGATORIO antes de emitir cada pregunta:
1. Si es de código, traza el código línea a línea (estado de variables) y \
deriva la salida ANTES de escribir las opciones.
2. Re-resuelve la pregunta desde cero y confirma que tu solución coincide \
con la opción marcada en "correcta".
3. Verifica que cada distractor es inequívocamente incorrecto; si dos \
opciones son defendibles, reescribe la pregunta.

Ejemplo del formato de UNA pregunta (few-shot):
{{
  "enunciado": "¿Qué imprime este código?\\n\\nx = 3\\nx = x + 1\\nprint(x)",
  "opciones": ["3", "4", "x + 1", "Da error porque x ya existía"],
  "correcta": 1,
  "explicacion": "x = x + 1 evalúa la derecha (3 + 1) y guarda 4 en x. \
Quien elige '3' está leyendo la asignación como una ecuación que no cambia \
nada: error típico; la asignación REEMPLAZA el valor.",
  "concepto": "variables"
}}

Responde ÚNICAMENTE este JSON:
{{
  "preguntas": [ ...{num_preguntas} preguntas con el formato del ejemplo... ]
}}

Lección:
---
{leccion_md}
---"""
