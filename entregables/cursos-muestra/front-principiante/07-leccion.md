# Integración y depuración: juntar todo y resolver errores
Esta unidad te enseña a combinar variables, arrays, condicionales, bucles, funciones y el DOM para crear una rutina completa —y a usar console.log y mensajes en pantalla para encontrar y corregir errores comunes (campo vacío, índice fuera de rango). Piensa en una publicación en redes: quieres añadir un post desde un formulario, mostrar la lista y avisar si algo falla —esa es la meta práctica aquí.

🔮 Predice
```javascript
// ¿Qué crees que hace / imprime esto?
const posts = ['Foto', 'Texto'];
const indice = 1;
const elegido = posts[indice];
console.log(elegido);
document.getElementById('salida').textContent = elegido;
```

--- 

Sección: flujo de datos (estado)
- Estado: nombre para el conjunto de valores que el programa "recuerda" mientras corre (variables y arrays).
- Analogía: tu carpeta de presentaciones (estado): contiene archivos (variables). Cambias un archivo y la carpeta sigue teniendo esa versión actual.

Respuesta a la predicción: imprime "Texto" en la consola y lo pone en el elemento con id "salida".  
Worked example (integración mínima): añadir un post desde un campo y actualizar la lista visible.

```javascript
// 1. obtener valor del input
const entrada = document.getElementById('inputPost').value; 

// 2. validar campo vacío
if (entrada === '') {
  // 2.a mostrar mensaje de error
  document.getElementById('mensaje').textContent = 'Escribe algo';
  console.log('Error: campo vacío'); // depurar
  return;
}

// 3. guardar en array de posts
posts.push(entrada);

// 4. renderizar la lista en pantalla
let html = '';
for (let i = 0; i < posts.length; i++) {
  html += '<li>' + posts[i] + '</li>';
}
document.getElementById('lista').innerHTML = html;
```

Máquina nocional — estado línea a línea (ejemplo: posts inicial = ['Foto']):
- Después línea 1: entrada = 'Mi nuevo post'
- Línea 2: condición false (entrada no es '') → no entra al bloque de error
- Línea 3: posts = ['Foto', 'Mi nuevo post']
- Bucle (línea 4): i=0 → html = '<li>Foto</li>'; i=1 → html = '<li>Foto</li><li>Mi nuevo post</li>'
- Fin: elemento lista muestra los dos ítems

Sección: depuración básica (console.log y mensajes)
- console.log: función que escribe en la consola del navegador. Sirve para ver el estado interno.
- Analogía: cuando editas una diapositiva y activas notas privadas para recordar cambios.

Ejemplo de uso para localizar un índice fuera de rango:
```javascript
console.log('posts.length:', posts.length);
console.log('indice pedido:', indice);
console.log('valor en posts[indice]:', posts[indice]);
```
Si ves undefined en el último console.log, significa que indice está fuera de los valores válidos (0..posts.length-1).

Sección: manejo de errores simples y pruebas manuales en el navegador
- Pruebas manuales: escribe entradas diferentes, mira la consola y el contenido en pantalla. Así detectas campo vacío y errores de índice.
- Recomendación práctica: cada vez que toques el array escribe su longitud y el contenido con console.log para verificar.

⚠️ Error típico (y cómo desmontarlo)
1) Leer `x = x + 1` como ecuación imposible.
- Explicación: `=` asigna. Se evalúa la derecha y se guarda en x.
Ejemplo:
```javascript
let x = 2;
x = x + 1; // ahora x vale 3
```
2) Creer que dos variables se "vinculan".
```javascript
let a = ['A'];
let b = a;
b.push('B');
console.log(a); // ['A','B'] -> porque b y a refieren al mismo array
```
Explicación: con arrays/objetos la asignación copia la referencia, no crea una cápsula independiente.

3) Error de índices: pensar que la primera posición es 1.
```javascript
const arr = ['x','y'];
console.log(arr[1]); // 'y' -> la primera es arr[0]
console.log(arr[arr.length]); // undefined -> último índice es arr.length - 1
```
4) Confundir asignación `=` con comparación `==` o `===`.
- `=` pone un valor; `==` y `===` comparan. Si usas `=` dentro de un if no comparas, asignas.

🔧 Modifícalo
Toma el worked example y cambia 1-2 líneas para que:
- El nuevo post se añada al principio de la lista (aparezca primero en la UI).
Indica qué debe lograr, no cómo: "Al modificar, el post más reciente debe aparecer arriba de todos".

🎯 Mini-reto
Crea una función agregarPost() que:
- Toma el valor del input,
- Valida que tenga al menos 3 caracteres,
- Si pasa, lo añade al inicio del array posts y actualiza la lista en pantalla,
- Si falla, muestra mensaje de error.
Pista: usa posts.unshift(valor) para poner al inicio (si ya viste unshift; si no, usa splice o reconstruye el array).

📌 En resumen
- Usa console.log y mensajes en pantalla para ver el estado (variables, longitud de arrays, valores).
- Valida siempre entradas (campo vacío, longitud mínima) antes de modificar tu estado.
- Los índices empiezan en 0; arr[arr.length] es inválido; compara con `===` y asigna con `=`.