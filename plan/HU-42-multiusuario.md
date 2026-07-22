# HU-42 — Perfiles de estudiante (multiusuario local)

**Como** hogar/aula que comparte un computador **quiero** que cada persona
tenga su propio perfil **para** que los cursos, el progreso y las
conversaciones de cada quien estén aislados.

## Qué hace

1. Al abrir la app: pantalla "¿Quién estudia hoy?" con los perfiles
   (avatar con inicial) y "Nuevo perfil" (solo nombre, sin contraseña: es
   una app local, el modelo es el selector de perfiles de Netflix).
2. Cada perfil tiene su carpeta de datos completa y aislada
   (`data/usuarios/<id>/`); el perfil "principal" apunta a `data/` para
   retro-compatibilidad con lo ya existente.
3. El avatar del navbar muestra quién estudia y permite cambiar de perfil.
4. Backend: `_Usuarios` (registro en `usuarios.json`) + `_EstadoProxy` que
   delega todo al estado del usuario activo — los endpoints existentes no
   cambiaron ni una línea.

## API

```
GET  /api/usuarios                → {usuarios: [{id, nombre}], activo}
POST /api/usuarios {nombre}       → {id, nombre}   (400 vacío; activa)
POST /api/usuarios/{id}/activar   → {ok}           (404 si no existe)
```

## Tareas

- [x] Registro `_Usuarios` + proxy `_EstadoProxy` (aislamiento por carpeta).
- [x] Endpoints usuarios (listar, crear con slug único, activar).
- [x] Front: selector de perfiles + avatar en navbar para cambiar.
- [x] Pruebas: default principal, crear/activar/persistir, AISLAMIENTO de
      datos entre usuarios, slugs sin colisión.
