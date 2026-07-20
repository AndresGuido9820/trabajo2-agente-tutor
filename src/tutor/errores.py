"""Excepciones propias del tutor.

Todas heredan de ``ErrorTutor`` para que la CLI pueda capturarlas en un solo
punto y mostrar mensajes limpios (sin traceback) al estudiante.
"""


class ErrorTutor(Exception):
    """Error base de la aplicación."""


class ErrorConfiguracion(ErrorTutor):
    """Configuración inválida o incompleta (p. ej. falta la API key)."""


class ErrorLLM(ErrorTutor):
    """Fallo definitivo al interactuar con la API del LLM."""


class ErrorDatos(ErrorTutor):
    """Archivo de datos locales (perfil/curso/progreso) inválido o corrupto."""
