# HU-05 — Progreso persistente

**Como** estudiante **quiero** que mi avance se conserve entre sesiones
**para** retomar el curso donde iba. *(RF-2.4; PA-06)*

## Criterios de aceptación

- `progreso.json` guarda: unidades vistas (con fecha), resultados de quizzes
  (historial completo; se muestra la mejor nota por unidad).
- Cerrar y reabrir el tutor conserva todo; se muestra en la opción `[p]`
  (tabla: unidad, vista sí/no, mejor nota, intentos).
- Escritura atómica (escribir a temporal + rename) para no corromper el
  archivo si se interrumpe el proceso.
- Archivo corrupto → advertencia clara y arranque con progreso vacío (el
  curso y perfil no se pierden: archivos separados).

## Interfaz

```python
@dataclass
class Progreso:
    vistas: dict[int, str]              # unidad -> fecha ISO
    resultados: list[Resultado]

    def marcar_vista(self, unidad: int) -> None
    def registrar(self, resultado: Resultado) -> None
    def mejor_nota(self, unidad: int) -> int | None
    def fallos_recientes(self) -> list[str]   # conceptos fallados, para HU-03

def cargar_progreso(ruta: Path) -> Progreso
def guardar_progreso(p: Progreso, ruta: Path) -> None
```

## Tareas

- [x] `progreso.py`: modelo, carga/guardado con validación y escritura atómica.
- [x] Integrar registro automático: entrar a unidad → `marcar_vista`; terminar
      quiz → `registrar`.
- [x] Render de la tabla de progreso con `rich`.
- [x] Pruebas (abajo).

## Pruebas

- `test_progreso_roundtrip_entre_instancias` (simula dos sesiones)
- `test_mejor_nota_conserva_maxima_de_varios_intentos`
- `test_progreso_corrupto_arranca_vacio_con_advertencia`
- `test_guardado_es_atomico` (no queda archivo a medias)
