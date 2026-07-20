# Proyecto final: microblog interactivo en el navegador
Vas a construir una mini-aplicación que te permita crear posts desde un formulario, validarlos, guardarlos en un array y ver la lista actualizada en la página. Esto es justo lo que necesitas para mostrar en tu portafolio: una página web que responde como una red social sencilla —como cuando preparas una diapositiva y la subes con título y comentario.

🔮 Predice
```javascript
const posts = [];
const nuevoPost = { autor: "Tú", texto: "Hola mundo" };
posts.push(nuevoPost);
console.log(posts.length);
console.log(posts[0].texto);
```
¿Qué crees que imprime en la consola y por qué?

---

Concepto: formulario y eventos
Respuesta a la predicción: imprime primero 1 (la longitud del array) y luego "Hola mundo" (el texto del primer objeto).
Explicación y analogía: rellenar un formulario es como escribir una leyenda en tu publicación antes de hacer clic en "Publicar". Un evento (por ejemplo, el clic) es el "clic" que envía eso al sitio.

Worked example
```javascript
// 1. obtener elementos del DOM
const formulario = document.getElementById('form-post'); // 1. capturar el formulario
const inputTexto = document.getElementById('input-texto'); // 1. capturar el campo de texto

// 2. almacenar posts
const posts = []; // 2. array donde guardar objetos post

// 3. manejar el envío
formulario.addEventListener('submit', function(evento) {
  evento.preventDefault(); // 3. evitar recarga de página
  // 3. leer texto del usuario
  const textoUsuario = inputTexto.value; // 3. leer valor actual del input
  // 3. crear objeto post
  const post = { autor: 'Tú', texto: textoUsuario }; // 3. construir objeto post
  posts.push(post); // 3. añadir al array
  renderizarPosts(); // 3. actualizar la UI
  inputTexto.value = ''; // 3. limpiar formulario
});
```

Estado del programa (línea a línea, después de enviar un texto "Hola"):
- Antes: posts = []
- Tras crear post: post = { autor: 'Tú', texto: 'Hola' }
- Tras push: posts = [ { autor: 'Tú', texto: 'Hola' } ]
- Tras limpiar: inputTexto.value = ''

Concepto: renderizado dinámico
Explicación y analogía: renderizar es como preparar la diapositiva final con todos los comentarios; lo haces cada vez que cambian los datos.

Worked example
```javascript
// 1. obtener contenedor de lista
const lista = document.getElementById('lista-posts'); // 1. contenedor ul/ol

// 2. función que solo muestra posts
function renderizarPosts() {
  lista.innerHTML = ''; // 2. limpiar la lista existente
  for (let i = 0; i < posts.length; i++) { // 2. recorrer posts
    const item = document.createElement('li'); // 2. crear elemento
    item.innerText = posts[i].texto; // 2. poner texto del post
    lista.appendChild(item); // 2. añadir al DOM
  }
}
```
Estado clave durante render: si posts = [{texto: 'Hola'}], tras la primera iteración se crea un li con 'Hola' y el DOM refleja ese li.

Concepto: separar responsabilidades (añadir vs renderizar)
Explicación: piensa en dos tareas distintas cuando haces una publicación: escribir (guardar) y presentar (mostrar). Mantenerlas separadas evita confusiones y te permite reutilizar renderizarPosts en otras acciones (borrar, editar).

Worked example (uso conjunto)
```javascript
// usar addPost para solo alterar datos
function addPost(texto) {
  const post = { autor: 'Tú', texto: texto }; // 1. crear objeto
  posts.push(post); // 1. añadir a datos
}
// en el submit llamas:
// addPost(textoUsuario);
// renderizarPosts();
```

⚠️ Error típico
- "Una variable guarda varios valores o recuerda su historial." Falso: posts es un array que guarda muchos valores, pero cada variable individual (p. ej. textoUsuario) guarda un solo valor actual. Si reasignas textoUsuario, no "recuerda" el valor anterior.
  Ejemplo: textoUsuario = 'A'; textoUsuario = 'B'; consola muestra 'B' si consultas textoUsuario ahora.
- "Confundir el nombre de la variable con su valor." El nombre posts no es la lista visible; es sólo la referencia al array. Cambiar el DOM no cambia la variable automáticamente.
- "Creer que declarar una función la ejecuta." Definir function renderizarPosts() { ... } no muestra nada hasta que la llames: renderizarPosts().

🔧 Modifícalo
Cambia 1-2 líneas para que los posts nuevos aparezcan al principio de la lista (más recientes arriba). Qué debe lograr: el último post añadido se muestra primero en la UI.

(Sugerencia de cambio: en addPost usa posts.unshift(post) en vez de posts.push(post). Luego renderizarPosts preserva orden.)

🎯 Mini-reto
Añade validación: no permitir posts vacíos y limitar el texto a 140 caracteres. Si la validación falla, muestra un mensaje en pantalla (no alert) y no añadas el post.
Pista: revisa inputTexto.value.length antes de crear el objeto; para mostrar el mensaje crea un elemento pequeño en el DOM y actualiza su innerText.

📌 En resumen
- Un formulario + evento captura la entrada; evita la recarga con event.preventDefault().
- Separa: una función solo modifica los datos (addPost) y otra solo pinta la interfaz (renderizarPosts).
- Cada cambio en el array requiere llamar a renderizarPosts() para que la UI se actualice.