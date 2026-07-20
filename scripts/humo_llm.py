"""Prueba de humo MANUAL contra la API real (cuesta tokens; no corre en CI).

Uso: ``uv run python scripts/humo_llm.py``. Verifica key, modelo y que el
contrato de salida JSON (pedir_json) funciona de punta a punta.
"""

from __future__ import annotations

import sys
from typing import Any

from tutor.config import cargar_configuracion
from tutor.errores import ErrorTutor
from tutor.llm import ClienteOpenAI, pedir_json


def _validar(datos: Any) -> list[str]:
    conceptos = datos["conceptos"]
    if not isinstance(conceptos, list) or len(conceptos) != 3:
        raise ValueError("se esperaban exactamente 3 conceptos")
    return [str(c) for c in conceptos]


def main() -> int:
    """Hace una petición JSON mínima real y reporta el resultado."""
    try:
        configuracion = cargar_configuracion()
        cliente = ClienteOpenAI(configuracion)
        conceptos = pedir_json(
            cliente,
            system="Eres un tutor de programación conciso.",
            prompt=(
                "Dame exactamente 3 conceptos básicos de programación. "
                'Responde SOLO este JSON: {"conceptos": ["...", "...", "..."]}'
            ),
            validar=_validar,
        )
        print(f"OK — modelo {configuracion.modelo} respondió: {conceptos}")
        return 0
    except ErrorTutor as error:
        print(f"FALLO — {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
