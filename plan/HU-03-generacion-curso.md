# HU-03 — Generación de temario y lecciones

**Como** estudiante **quiero** un curso con unidades coherentes con mi perfil
y lecciones motivadoras **para** aprender con material hecho para mí.
*(RF-2.2; PA-03, PA-04, PA-10; rúbrica de prompts 30 % y curso 20 %)*

## Criterios de aceptación

- Con el perfil se genera un **temario** de 5–8 unidades (título, objetivo,
  conceptos) coherente con nivel, objetivo y lenguaje; se guarda en
  `curso.json`.
- Las **lecciones** se generan bajo demanda al entrar a la unidad y se
  cachean; volver a entrar no regenera (RF-3.3).
- Los prompts viven centralizados y versionados en `prompts.py`: persona de
  tutor motivador, perfil interpolado, esquema JSON explícito, encadenamiento
  temario→lección, y adaptación según resultados de quizzes previos.
- La lección llega en Markdown (título, motivación, explicación con analogías
  del interés del estudiante, ejemplos de código en el lenguaje elegido,
  mini-reto final).
- JSON inválido o esquema incompleto → reintento y luego error claro (HU-02).

## Interfaz

```python
@dataclass(frozen=True)
class Unidad:      # titulo, objetivo, conceptos: list[str]
@dataclass(frozen=True)
class Temario:     # lenguaje: str, unidades: list[Unidad]

def generar_temario(cliente: ClienteLLM, perfil: PerfilEstudiante) -> Temario
def generar_leccion(cliente: ClienteLLM, perfil, temario, indice: int,
                    historial: Progreso) -> str  # markdown
```

## Tareas

- [x] `prompts.py`: system prompt del tutor + plantillas de temario y lección
      (documentar cada técnica usada en comentarios breves).
- [x] `curso.py`: modelos `Unidad`/`Temario`, validadores de esquema,
      `generar_temario`, `generar_leccion`, cache en `curso.json`.
- [x] Adaptación: incluir en el prompt de lección qué unidades ya vio y en qué
      preguntas falló.
- [x] Pruebas con `ClienteLLMFalso` (abajo).
- [x] Revisión manual de calidad con API real (humo) y anotar en HALLAZGOS
      qué prompts hubo que ajustar y por qué.

## Pruebas

- `test_generar_temario_parsea_y_valida_unidades`
- `test_temario_rechaza_menos_de_5_unidades`
- `test_generar_leccion_usa_cache_en_segunda_llamada`
- `test_generar_leccion_incluye_perfil_en_prompt` (inspección del fake)
- `test_temario_json_incompleto_lanza_error_claro`
