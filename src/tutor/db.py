"""Persistencia en SQLite (HU-19): una sola ``tutor.db`` por estudiante.

Esquema pensado alrededor del diseño del curso:
- ``curso``: el diseño (lenguaje, plan en Markdown, versión de prompts,
  metadata de creación).
- ``clases``: una fila por clase con su definición (título, objetivo,
  subtemas) y su **prompt/guion** (el guion paso a paso que el tutor sigue
  al dar la clase), más el contenido generado (lección, guía, artefacto) y
  metadata de actualización.
- ``perfil`` y ``progreso``: documentos JSON del estudiante.
- ``chat``: historial por conversación (canal 'creacion' o 'u<indice>').

Los JSON heredados (perfil.json, curso.json, progreso.json, chat.json) se
migran automáticamente la primera vez (``migrar_json_legacy``).
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS curso(
  id INTEGER PRIMARY KEY CHECK(id = 1),
  lenguaje TEXT NOT NULL,
  plan_md TEXT NOT NULL DEFAULT '',
  artefactos TEXT NOT NULL DEFAULT '{}',
  prompts_version INTEGER NOT NULL,
  creado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS clases(
  indice INTEGER PRIMARY KEY,
  titulo TEXT NOT NULL,
  objetivo TEXT NOT NULL,
  conceptos TEXT NOT NULL,
  guion TEXT,
  leccion_md TEXT,
  guia TEXT,
  actualizado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS perfil(
  id INTEGER PRIMARY KEY CHECK(id = 1),
  datos TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS progreso(
  id INTEGER PRIMARY KEY CHECK(id = 1),
  datos TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  canal TEXT NOT NULL,
  rol TEXT NOT NULL,
  texto TEXT NOT NULL,
  creado_en TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_canal ON chat(canal);
"""


def ahora() -> str:
    """Timestamp ISO 8601 en UTC para metadata."""
    return datetime.now(UTC).isoformat(timespec="seconds")


# Columnas añadidas después de la v1 del esquema (migración tolerante).
_COLUMNAS_NUEVAS = [
    ("curso", "nombre", "TEXT NOT NULL DEFAULT ''"),
    ("curso", "archivado", "INTEGER NOT NULL DEFAULT 0"),
    ("clases", "banco_preguntas", "TEXT"),
]


def abrir(ruta: Path) -> sqlite3.Connection:
    """Abre (creando el esquema si falta) la base de datos.

    Raises:
        sqlite3.DatabaseError: Si el archivo existe pero no es una BD válida.
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(ruta)
    conexion.executescript(_ESQUEMA)
    for tabla, columna, ddl in _COLUMNAS_NUEVAS:
        existentes = {
            fila[1] for fila in conexion.execute(f"PRAGMA table_info({tabla})")
        }
        if columna not in existentes:
            conexion.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {ddl}")
    return conexion


def leer_meta_curso(ruta: Path) -> dict[str, object]:
    """Nombre personalizado y bandera de archivado del curso."""
    if not ruta.exists():
        return {"nombre": "", "archivado": False}
    with abrir(ruta) as conexion:
        fila = conexion.execute(
            "SELECT nombre, archivado FROM curso WHERE id = 1"
        ).fetchone()
    if not fila:
        return {"nombre": "", "archivado": False}
    return {"nombre": str(fila[0]), "archivado": bool(fila[1])}


def escribir_meta_curso(
    ruta: Path, nombre: str | None = None, archivado: bool | None = None
) -> None:
    """Actualiza nombre y/o archivado (el curso debe existir en la BD).

    Si aún no hay fila de curso (curso sin diseñar), se crea una mínima
    para poder guardar la metadata.
    """
    with abrir(ruta) as conexion:
        existe = conexion.execute("SELECT 1 FROM curso WHERE id = 1").fetchone()
        if not existe:
            conexion.execute(
                "INSERT INTO curso(id, lenguaje, prompts_version, creado_en) "
                "VALUES(1, '', 0, ?)",
                (ahora(),),
            )
        if nombre is not None:
            conexion.execute("UPDATE curso SET nombre = ? WHERE id = 1", (nombre,))
        if archivado is not None:
            conexion.execute(
                "UPDATE curso SET archivado = ? WHERE id = 1", (int(archivado),)
            )


def cargar_documento(ruta: Path, tabla: str) -> Any | None:
    """Lee el documento JSON de una tabla singleton (perfil/progreso).

    Returns:
        El JSON deserializado, o ``None`` si no hay fila.

    Raises:
        sqlite3.DatabaseError: Archivo corrupto / no es una BD.
        json.JSONDecodeError: Contenido no-JSON en la fila.
    """
    if not ruta.exists():
        return None
    with abrir(ruta) as conexion:
        fila = conexion.execute(f"SELECT datos FROM {tabla} WHERE id = 1").fetchone()
    return json.loads(fila[0]) if fila else None


def guardar_documento(ruta: Path, tabla: str, datos: Any) -> None:
    """Escribe (upsert) el documento JSON de una tabla singleton."""
    with abrir(ruta) as conexion:
        conexion.execute(
            f"INSERT OR REPLACE INTO {tabla}(id, datos) VALUES(1, ?)",
            (json.dumps(datos, ensure_ascii=False),),
        )


def anotar_chat(ruta: Path, canal: str, rol: str, texto: str) -> None:
    """Agrega un mensaje al historial de una conversación."""
    with abrir(ruta) as conexion:
        conexion.execute(
            "INSERT INTO chat(canal, rol, texto, creado_en) VALUES(?,?,?,?)",
            (canal, rol, texto, ahora()),
        )


def historial_chat(ruta: Path, canal: str, limite: int = 300) -> list[dict[str, str]]:
    """Mensajes de una conversación, en orden cronológico."""
    if not ruta.exists():
        return []
    with abrir(ruta) as conexion:
        filas = conexion.execute(
            "SELECT rol, texto FROM chat WHERE canal = ? ORDER BY id DESC LIMIT ?",
            (canal, limite),
        ).fetchall()
    return [{"rol": rol, "texto": texto} for rol, texto in reversed(filas)]


def historial_con_ids(
    ruta: Path, canal: str, limite: int = 300
) -> list[dict[str, Any]]:
    """Como ``historial_chat`` pero con el id de BD (anchor del buscador)."""
    if not ruta.exists():
        return []
    with abrir(ruta) as conexion:
        filas = conexion.execute(
            "SELECT id, rol, texto FROM chat WHERE canal = ? ORDER BY id DESC LIMIT ?",
            (canal, limite),
        ).fetchall()
    return [
        {"id": id_, "rol": rol, "texto": texto} for id_, rol, texto in reversed(filas)
    ]


def _escapar_like(q: str) -> str:
    r"""Escapa los comodines de LIKE (``%``, ``_``) con ``\``."""
    return q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _fragmento(texto: str, q: str, contexto: int = 60) -> str:
    """Snippet de ±``contexto`` caracteres alrededor de la coincidencia."""
    pos = texto.lower().find(q.lower())
    if pos < 0:
        return texto[: 2 * contexto]
    inicio = max(0, pos - contexto)
    fin = min(len(texto), pos + len(q) + contexto)
    pre = "…" if inicio > 0 else ""
    post = "…" if fin < len(texto) else ""
    return f"{pre}{texto[inicio:fin]}{post}"


def buscar_mensajes(ruta: Path, q: str, limite: int = 8) -> list[dict[str, Any]]:
    """Mensajes cuyo texto contiene ``q`` (LIKE, sin distinguir mayúsculas)."""
    if not ruta.exists():
        return []
    patron = f"%{_escapar_like(q)}%"
    with abrir(ruta) as conexion:
        filas = conexion.execute(
            r"SELECT id, canal, rol, texto FROM chat "
            r"WHERE texto LIKE ? ESCAPE '\' ORDER BY id DESC LIMIT ?",
            (patron, limite),
        ).fetchall()
    return [
        {"id": id_, "canal": canal, "rol": rol, "fragmento": _fragmento(texto, q)}
        for id_, canal, rol, texto in filas
    ]


def buscar_clases(ruta: Path, q: str, limite: int = 8) -> list[dict[str, Any]]:
    """Clases cuyo título, objetivo o subtemas contienen ``q``."""
    if not ruta.exists():
        return []
    patron = f"%{_escapar_like(q)}%"
    with abrir(ruta) as conexion:
        filas = conexion.execute(
            r"SELECT indice, titulo, objetivo, conceptos FROM clases "
            r"WHERE titulo LIKE ? ESCAPE '\' OR objetivo LIKE ? ESCAPE '\' "
            r"OR conceptos LIKE ? ESCAPE '\' ORDER BY indice LIMIT ?",
            (patron, patron, patron, limite),
        ).fetchall()
    return [
        {
            "indice": indice,
            "titulo": titulo,
            "fragmento": _fragmento(
                titulo if q.lower() in titulo.lower() else f"{objetivo} {conceptos}", q
            ),
        }
        for indice, titulo, objetivo, conceptos in filas
    ]


def ultimo_mensaje_en(ruta: Path, canal: str) -> str | None:
    """Timestamp ISO del último mensaje de una conversación, o ``None``."""
    if not ruta.exists():
        return None
    with abrir(ruta) as conexion:
        fila = conexion.execute(
            "SELECT creado_en FROM chat WHERE canal = ? ORDER BY id DESC LIMIT 1",
            (canal,),
        ).fetchone()
    return str(fila[0]) if fila else None


def leer_banco(ruta: Path, indice: int) -> list[dict[str, Any]]:
    """Banco de preguntas de una clase (HU-26); vacío si no hay.

    Cada ítem: ``{"pregunta": {...}, "intentos": [1, 3]}``.
    """
    if not ruta.exists():
        return []
    with abrir(ruta) as conexion:
        fila = conexion.execute(
            "SELECT banco_preguntas FROM clases WHERE indice = ?", (indice,)
        ).fetchone()
    if not fila or not fila[0]:
        return []
    try:
        banco = json.loads(fila[0])
        return banco if isinstance(banco, list) else []
    except json.JSONDecodeError:
        logger.warning("Banco de preguntas corrupto en la clase %d", indice)
        return []


def guardar_banco(ruta: Path, indice: int, banco: list[dict[str, Any]]) -> None:
    """Persiste el banco de preguntas de una clase (HU-26)."""
    with abrir(ruta) as conexion:
        conexion.execute(
            "UPDATE clases SET banco_preguntas = ? WHERE indice = ?",
            (json.dumps(banco, ensure_ascii=False), indice),
        )


def actividad_chat(ruta: Path, dias: int = 14) -> dict[str, int]:
    """Mensajes por día (fecha ISO → conteo), últimos ``dias`` con actividad."""
    if not ruta.exists():
        return {}
    with abrir(ruta) as conexion:
        filas = conexion.execute(
            "SELECT substr(creado_en, 1, 10) AS fecha, COUNT(*) FROM chat "
            "GROUP BY fecha ORDER BY fecha DESC LIMIT ?",
            (dias,),
        ).fetchall()
    return dict(sorted(filas))


def resumen_chats(ruta: Path) -> dict[str, int]:
    """Cuántos mensajes tiene cada conversación (barra lateral)."""
    if not ruta.exists():
        return {}
    with abrir(ruta) as conexion:
        filas = conexion.execute(
            "SELECT canal, COUNT(*) FROM chat GROUP BY canal"
        ).fetchall()
    return {canal: n for canal, n in filas}


def borrar_curso(ruta: Path) -> None:
    """Elimina el diseño del curso y sus clases (rehacer perfil)."""
    if not ruta.exists():
        return
    with abrir(ruta) as conexion:
        conexion.execute("DELETE FROM curso")
        conexion.execute("DELETE FROM clases")


# Registro de uso del LLM (HU-39). Vive en una BD GLOBAL (data/uso.db):
# el costo es del operador, no de un curso.
_ESQUEMA_USO = """
CREATE TABLE IF NOT EXISTS llm_uso(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha TEXT NOT NULL,
  carril TEXT NOT NULL,
  modelo TEXT NOT NULL,
  tokens_prompt INTEGER,
  tokens_salida INTEGER,
  duracion_ms INTEGER NOT NULL
);
"""


def anotar_uso(
    ruta: Path,
    carril: str,
    modelo: str,
    tokens_prompt: int | None,
    tokens_salida: int | None,
    duracion_ms: int,
) -> None:
    """Registra una llamada al LLM (tokens ``None`` si el SDK no los dio)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(ruta) as conexion:
        conexion.executescript(_ESQUEMA_USO)
        conexion.execute(
            "INSERT INTO llm_uso"
            "(fecha, carril, modelo, tokens_prompt, tokens_salida, duracion_ms) "
            "VALUES(?,?,?,?,?,?)",
            (ahora(), carril, modelo, tokens_prompt, tokens_salida, duracion_ms),
        )


def resumen_uso(ruta: Path) -> list[dict[str, Any]]:
    """Uso agregado por día/carril/modelo (llamadas, tokens, duración)."""
    if not ruta.exists():
        return []
    with sqlite3.connect(ruta) as conexion:
        conexion.executescript(_ESQUEMA_USO)
        filas = conexion.execute(
            "SELECT substr(fecha, 1, 10) AS dia, carril, modelo, COUNT(*), "
            "SUM(COALESCE(tokens_prompt, 0)), SUM(COALESCE(tokens_salida, 0)), "
            "SUM(duracion_ms) FROM llm_uso GROUP BY dia, carril, modelo "
            "ORDER BY dia"
        ).fetchall()
    return [
        {
            "dia": dia,
            "carril": carril,
            "modelo": modelo,
            "llamadas": llamadas,
            "tokens_prompt": tp,
            "tokens_salida": ts,
            "duracion_ms": ms,
        }
        for dia, carril, modelo, llamadas, tp, ts, ms in filas
    ]


def migrar_json_legacy(dir_datos: Path) -> None:
    """Importa una sola vez los JSON del formato viejo a la BD.

    Best-effort: cualquier archivo ilegible se omite con advertencia (el
    sistema regenera lo que falte).
    """
    ruta_db = dir_datos / "tutor.db"
    if ruta_db.exists() or not dir_datos.exists():
        return

    def _leer(nombre: str) -> Any | None:
        archivo = dir_datos / nombre
        if not archivo.exists():
            return None
        try:
            return json.loads(archivo.read_text("utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            logger.warning("No se migró %s (%s)", nombre, error)
            return None

    perfil = _leer("perfil.json")
    progreso = _leer("progreso.json")
    curso = _leer("curso.json")
    chat = _leer("chat.json")
    if not any([perfil, progreso, curso, chat]):
        return

    logger.info("Migrando datos JSON heredados a %s", ruta_db)
    with abrir(ruta_db) as conexion:
        if perfil:
            conexion.execute(
                "INSERT OR REPLACE INTO perfil(id, datos) VALUES(1, ?)",
                (json.dumps(perfil, ensure_ascii=False),),
            )
        if progreso:
            conexion.execute(
                "INSERT OR REPLACE INTO progreso(id, datos) VALUES(1, ?)",
                (json.dumps(progreso, ensure_ascii=False),),
            )
        if isinstance(curso, dict) and "unidades" in curso:
            conexion.execute(
                "INSERT OR REPLACE INTO curso"
                "(id, lenguaje, plan_md, artefactos, prompts_version, creado_en) "
                "VALUES(1, ?, ?, ?, ?, ?)",
                (
                    str(curso.get("lenguaje", "")),
                    (dir_datos / "curso.md").read_text("utf-8")
                    if (dir_datos / "curso.md").exists()
                    else "",
                    json.dumps(curso.get("artefactos", {}), ensure_ascii=False),
                    2,
                    ahora(),
                ),
            )
            for indice, unidad in enumerate(curso.get("unidades", [])):
                guion = curso.get("guiones", {}).get(str(indice))
                guia = curso.get("guias", {}).get(str(indice))
                leccion = curso.get("lecciones", {}).get(str(indice))
                conexion.execute(
                    "INSERT OR REPLACE INTO clases"
                    "(indice, titulo, objetivo, conceptos, guion, leccion_md, "
                    "guia, actualizado_en) VALUES(?,?,?,?,?,?,?,?)",
                    (
                        indice,
                        str(unidad.get("titulo", "")),
                        str(unidad.get("objetivo", "")),
                        json.dumps(unidad.get("conceptos", []), ensure_ascii=False),
                        json.dumps(guion, ensure_ascii=False) if guion else None,
                        leccion,
                        json.dumps(guia, ensure_ascii=False) if guia else None,
                        ahora(),
                    ),
                )
        if isinstance(chat, dict):
            for canal, mensajes in chat.items():
                for m in mensajes:
                    conexion.execute(
                        "INSERT INTO chat(canal, rol, texto, creado_en) "
                        "VALUES(?,?,?,?)",
                        (
                            canal,
                            str(m.get("rol", "tutor")),
                            str(m.get("texto", "")),
                            ahora(),
                        ),
                    )
