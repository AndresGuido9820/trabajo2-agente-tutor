# Guardar y nombrar datos: variables y valores

Para qué sirve: en front-end necesitas guardar textos (titulares, botones) y números (contadores, tamaños). Aquí aprendes a darle nombre a esos datos y a verlos en la consola — el primer paso para poner contenido dinámico en tus páginas o en una diapositiva interactiva, como cuando preparas una publicación o una presentación.

🔮 Predice

```js
let likes = 10
likes = likes + 5
console.log(likes)
```

¿Qué crees que imprime eso en la consola?

---

## Valor literal y tipo (número / texto)
Respuesta a la predicción: más abajo, cuando hablemos de asignación.

Qué es un valor literal: es el dato escrito tal cual en el código. Ejemplos:
- 10 (literal numérico)
- "Me gusta" (literal de texto, también llamado string)

Analogía: un literal es como el texto que escribes en una publicación o el número de reacciones que ves en una estadística — ya viene listo.

Worked example:
// 1. guardar un número literal
let reacciones = 42

// 2. guardar un texto literal
let mensaje = "Gracias por ver mi presentación"

console.log(reacciones)
console.log(mensaje)

(La consola mostrará primero 42 y luego el texto.)

---

## Variable y asignación
Aquí respondemos la predicción.

Qué es una variable: un nombre que guarda un valor para usarlo después. Asignación es la acción de poner un valor dentro de la variable (usando =).

Analogía: una variable es como una etiqueta en tu carpeta de presentaciones: puedes cambiar el contenido de la carpeta, pero la etiqueta (nombre) sigue apuntando a lo que ahora está dentro.

Worked example (la predicción):
```js
// 1. guardar el número inicial de likes
let likes = 10

// 2. aumentar likes al recibir nueva interacción
likes = likes + 5

// 3. mostrar el total en la consola para inspección
console.log(likes)
```

Tabla de estado (línea a línea):
Línea | Código | Estado de variables
1 | let likes = 10 | likes ➜ 10
2 | likes = likes + 5 | se evalúa la derecha: 10 + 5 = 15 → likes ahora es 15
3 | console.log(likes) | imprime 15

Explicación clave: en la línea 2 se calcula la derecha y luego se guarda el resultado en la variable likes. No es una ecuación matemática en dos sentidos.

---

## console.log — ver lo que el ordenador guarda
Qué hace: imprime en la consola del navegador el valor que le pases. Es tu herramienta de inspección.

Analogía: como mostrar las notas de una diapositiva en el modo presentador para comprobarlas antes de presentar.

Worked example:
// 1. preparar datos que quieres validar antes de mostrarlos en la página
let titulo = "Mi primer componente"
let visitas = 3

// 2. inspeccionar los valores en la consola
console.log(titulo)
console.log(visitas)

(Console: mostrará el texto y luego el número.)

---

⚠️ Error típico (y por qué no)
1) Leer `likes = likes + 5` como ecuación imposible:
   - Error: pensar que pides que "likes" sea igual que "likes + 5" sin cambio.
   - Realidad: el motor calcula la derecha primero (valor actual + 5) y después guarda ese nuevo número en likes.

2) Creer que la asignación crea vínculo permanente entre variables:
```js
// 1. copiar el valor de seguidores a copia
let seguidores = 100
let copia = seguidores

// 2. cambiar seguidores
seguidores = 120

console.log(copia) // imprime 100, no 120
```
   - Explicación: copia guarda el valor en el momento de la asignación. No se actualiza automáticamente cuando la otra variable cambia.

3) Creer que una variable recuerda su historial:
```js
let contador = 1
contador = 2
console.log(contador) // imprime 2 (solo el valor actual)
```
   - Si quieres historial necesitas guardar cada valor por separado (lo veremos más adelante).

4) Confundir nombre con valor:
   - `let nombre = "Ana"` → el nombre de la variable es nombre; su valor es "Ana". No uses el nombre cuando quieres el valor en salida: usa la variable, no la palabra literal.

---

🔧 Modifícalo
Toma el worked example de likes. Cambia 1 o 2 líneas para que:
- Empiece con 7 likes y se sumen 3 más, y que la consola muestre el mensaje: "Total de likes: X" (donde X es el número).

(No pido la solución; solo modifica las líneas de valores y la línea de console.log.)

🎯 Mini-reto
Crea dos variables: una con el nombre de tu presentación (texto) y otra con la duración en minutos (número). Luego usa console.log para imprimir: "La presentación 'NOMBRE' dura X minutos".
Pista: concatena texto y variable separando con comas en console.log o usando el operador + para unir strings.

📌 En resumen
- Un literal es un dato escrito tal cual; los tipos comunes aquí son número y texto.
- Una variable nombra y guarda un valor; asignar ( =) pone un valor dentro.
- Usa console.log para ver los valores y comprobar paso a paso (inspección).