# Elegir qué mostrar: condicionales que cambian la interfaz

Qué te sirve: en front-end necesitas decidir qué ver según lo que escribe el usuario. Igual que en una presentación: si no hay foto, muestras un título; si hay foto, muestras la foto y menos texto. Aquí aprenderás a hacer exactamente eso en la página.

🔮 Predice

```javascript
// Predice: ¿qué crees que muestra esto en #mensaje si #inputNombre está vacío?
const campo = document.getElementById('inputNombre');
const salida = document.getElementById('mensaje');

if (campo.value) {
  salida.textContent = 'Hola, ' + campo.value;
} else {
  salida.textContent = 'Por favor escribe tu nombre';
}
```

¿Qué crees que hace / imprime?

---

Concepto: if / else
- Respuesta a la predicción: si el campo tiene texto muestra "Hola, <texto>", si está vacío muestra "Por favor escribe tu nombre".
- Qué es: if/else es una decisión: si (if) se cumple una condición, ejecuta un bloque; si no, ejecuta el else.
- Analogía (redes sociales/presentaciones): como decidir si publicar una foto o un mensaje: si hay foto, la pones; si no, pones un texto alternativo.

Worked example (completo, mínimo):
```javascript
// 1. leer entrada
const entradaNombre = document.getElementById('inputNombre'); // elemento input
// 2. seleccionar donde mostrar
const areaMensaje = document.getElementById('mensaje'); // elemento para texto
// 3. decidir qué mostrar
if (entradaNombre.value === '') { // 3.1 condición: ¿está vacío?
  // 3.2 mostrar aviso si está vacío
  areaMensaje.textContent = 'Por favor escribe tu nombre';
} else {
  // 3.3 mostrar saludo si hay nombre
  areaMensaje.textContent = 'Hola, ' + entradaNombre.value;
}
```

Tabla de estado (máquina nocional), si entradaNombre.value es '' al empezar:
- Línea 1: entradaNombre → referencia al elemento input (su .value es '')
- Línea 2: areaMensaje → referencia al elemento donde escribir
- Línea 3 (evaluar condición): entradaNombre.value === '' → true
- Ejecuta 3.2: areaMensaje.textContent -> 'Por favor escribe tu nombre'

Si entradaNombre.value es 'Ana':
- Línea 3 condición → false
- Ejecuta 3.3: areaMensaje.textContent -> 'Hola, Ana'

Concepto: comparaciones (==, ===, !=, !==)
- Qué es: comparar es preguntar si dos cosas son iguales o diferentes. Resultado: true o false (booleano).
- Definición rápida: == compara valor con conversión de tipos; === compara valor y tipo (estricto).
- Ejemplo mínimo:
  - '5' == 5 → true (convierte)
  - '5' === 5 → false (diferente tipo)
- Consejo práctico: usa === y !== para evitar sorpresas.

Concepto: booleano (true / false)
- Qué es: un booleano es un valor que solo puede ser true (verdadero) o false (falso).
- Cómo aparece: las comparaciones producen booleanos. En if, la condición se evalúa a true/false.
- Analogía: en una presentación, la condición es como una pregunta binaria: ¿hay imagen? sí/no.

Concepto: bloque de código
- Qué es: líneas entre { } que se ejecutan juntas cuando la condición es true o dentro de una función.
- Por qué importa: todo lo dentro de { } se ejecuta o no como una unidad.

⚠️ Error típico (desmontajes)
1) Confundir = con ==:
```javascript
let x = 1;
if (x = 2) { /* mal */ } // esto asigna 2 a x y la condición usa el valor asignado
```
Arreglo: usa comparación:
```javascript
if (x === 2) { /* bien: pregunta si x vale 2 */ }
```

2) Creer que una variable guarda su historial:
```javascript
let mensaje = 'hola';
mensaje = 'adiós';
// mensaje ahora vale 'adiós'. No "recuerda" 'hola'.
```
Explicación: la variable contiene solo el valor actual.

3) Confundir nombre de variable con su valor:
```javascript
let nombre = 'Laura';
// escribir nombre en la página muestra 'Laura', no "nombre"
```
Piensa: la variable es una caja con una etiqueta; lo que mostramos es lo dentro de la caja.

🔧 Modifícalo
Toma el worked example anterior y cambia 1-2 líneas para que:
- Si el nombre tiene solo espacios (p. ej. '   '), trate como vacío y muestre el aviso.
(No te doy la solución completa; modifica la condición para lograrlo.)

🎯 Mini-reto
Crea una pequeña verificación para una "publicación": si el texto del input #textoPublicacion tiene más de 140 caracteres muestra "Demasiado largo", si tiene 0 muestra "Escribe algo", si está entre 1 y 140 muestra "Listo para publicar".
Pista: usa propiedad .length del string y comparaciones (>, ===, <).

📌 En resumen
- if/else decide entre dos caminos según una condición que se evalúa a true/false.
- Usa === y !== para comparar tipo+y valor; == hace conversiones implícitas.
- Un bloque { } agrupa instrucciones que se ejecutan juntas cuando la condición aplica.