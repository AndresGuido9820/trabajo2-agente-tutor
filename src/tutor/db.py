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
