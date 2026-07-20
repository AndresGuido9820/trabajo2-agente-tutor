# HU-01 — Perfil del estudiante (procesamiento de entradas)

**Como** estudiante **quiero** que el tutor me pregunte qué sé y qué quiero
aprender **para** recibir un curso hecho a mi medida. *(RF-1; PA-01, PA-02)*

## Criterios de aceptación

- Cuestionario interactivo que captura: nivel de experiencia (nunca programé /
  algo básico / he hecho scripts), experiencia previa (texto libre corto),
  objetivo (ciencia de datos / front / back / automatización / otro con texto)
  y lenguaje preferido (o "que el tutor decida").
- Toda entrada inválida (vacío, opción fuera de rango, tipo incorrecto)
  reintenta con mensaje claro; nunca hay traceback.
- El perfil se guarda en `perfil.json` y se recarga al reiniciar; si el
  archivo está corrupto se informa y se rehace el cuestionario.
- La validación es lógica pura, separada de la lectura de `input()`.

## Interfaz

```python
@dataclass(frozen=True)
class PerfilEstudiante:
    nivel: Nivel                 # enum: NUNCA, BASICO, SCRIPTS
    experiencia: str             # texto libre, puede ser ""
    objetivo: Objetivo           # enum: DATOS, FRONT, BACK, AUTOMATIZACION, OTRO
    objetivo_detalle: str        # requerido si objetivo == OTRO
    lenguaje: str                # "python", "javascript", ... o "" = decide el tutor

def preguntar_perfil(entrada: Callable[[str], str] = input) -> PerfilEstudiante
def guardar_perfil(perfil, ruta: Path) -> None
def cargar_perfil(ruta: Path) -> PerfilEstudiante | None   # None si no existe
```

Esquema `perfil.json`: `{"version": 1, "nivel": "basico", "experiencia": "...",
"objetivo": "datos", "objetivo_detalle": "", "lenguaje": "python"}`.

## Tareas

- [x] `models.py`: enums `Nivel`, `Objetivo` y dataclass `PerfilEstudiante`
      con validación en `__post_init__`.
- [x] `perfil.py`: funciones puras de validación por campo + bucle de
      preguntas con reintento; inyectar `entrada` para testear.
- [x] Serialización/carga JSON con validación de esquema y `version`.
- [x] Manejo de `perfil.json` corrupto (JSON inválido o campos faltantes) →
      advertencia + rehacer cuestionario.
- [x] Pruebas unitarias (abajo) + actualizar HALLAZGOS si aparece algo.

## Pruebas

- `test_valida_nivel_rechaza_opcion_fuera_de_rango`
- `test_valida_objetivo_otro_exige_detalle`
- `test_preguntar_perfil_reintenta_ante_entrada_vacia` (input simulado)
- `test_guardar_y_cargar_perfil_roundtrip` (tmp_path)
- `test_cargar_perfil_inexistente_devuelve_none`
- `test_cargar_perfil_corrupto_lanza_error_claro`
