# Funciones: piezas reutilizables para la interfaz

Las funciones te ayudan a crear componentes reutilizables para tu web. Piensa en ellas como plantillas de slide o un formato de post en redes: defines una vez cómo debe verse algo (título, autor, fecha) y luego la usas cada vez que insertas un post. Así evitas repetir trabajo y puedes cambiar el diseño en un solo lugar.

🔮 Predice

```javascript
function dibujaTitulo(texto) {
  const h = document.createElement('h2');
  h.textContent = texto;
  return h;
}
const nodo = dibujaTitulo('Mi primer post');
console.log(nodo.tagName);
```

¿Qué crees que imprime esto en la consola?

---

## 1) Función (declaración)
Respuesta a la predicción: imprime "H2". La función se definió (declaración) y luego se ejecutó al llamarla. El valor retornado se guardó en `nodo`.

Analogía: declarar una función es como diseñar una plantilla de presentación. Diseñas la plantilla (no crea diapositivas) y cuando la usas (la ejecutas) se genera una diapositiva concreta.

Worked example: crear un título
```javascript
// 1. crear el elemento título
function dibujaTitulo(texto) {
  const h = document.createElement('h2'); // 1. crear nodo h2
  h.textContent = texto;                  // 1. poner texto en el nodo
  return h;                               // 1. devolver el nodo creado
}

const miTitulo = dibujaTitulo('Hola, público'); // 1. usar la plantilla
document.body.appendChild(miTitulo);            // 1. mostrar en la página
```

Tabla de estado (línea relevante)
| Paso | Código ejecutado | miTitulo |
|---:|---|---:|
| Después de la llamada | const miTitulo = dibujaTitulo('Hola, público'); | Nodo h2 con textContent "Hola, público" |
| Después append | document.body.appendChild(miTitulo); | miTitulo sigue siendo ese nodo h2 |

---

## 2) Parámetros
Definición: un parámetro es un nombre dentro de la función que recibe el dato que le pasas.

Analogía: el texto del título es como el contenido que pegas en una plantilla de slide: la plantilla necesita un lugar para ese contenido.

Worked example: función que recibe un objeto post
```javascript
// 2. crear nodo post a partir de un objeto post
function dibujaPost(post) {
  const cont = document.createElement('div');      // 2. contenedor del post
  const titulo = document.createElement('h3');     // 2. elemento título
  titulo.textContent = post.titulo;                 // 2. usar post.titulo
  const cuerpo = document.createElement('p');      // 2. elemento cuerpo
  cuerpo.textContent = post.contenido;             // 2. usar post.contenido
  cont.appendChild(titulo);                         // 2. armar estructura
  cont.appendChild(cuerpo);                         // 2. armar estructura
  return cont;                                      // 2. devolver nodo completo
}
```

Estado (al llamar dibujaPost({titulo:'X', contenido:'Y'}))
| Paso | Variable | Valor |
|---:|---|---|
| Dentro de la función, después de crear `titulo` | titulo.textContent | 'X' |
| Retorno | valor de retorno | nodo div con h3('X') y p('Y') |

---

## 3) Valor de retorno
Definición: el valor que la función "devuelve" al llamarla. Puedes guardarlo y volver a usarlo.

Analogía: cuando generas una diapositiva desde una plantilla, la diapositiva resultante es el retorno; puedes guardarla en una carpeta y luego presentarla.

Worked example: usar la función en un bucle para reutilizarla
```javascript
// 3. renderizar lista de posts usando la función dibujaPost
const posts = [
  {titulo: 'Entrada 1', contenido: 'Texto 1'},
  {titulo: 'Entrada 2', contenido: 'Texto 2'}
];

for (let i = 0; i < posts.length; i++) {                 // 3. recorrer posts
  const nodoPost = dibujaPost(posts[i]);                 // 3. crear nodo con la función
  document.body.appendChild(nodoPost);                   // 3. mostrar cada post
}
```

Estado (cada iteración)
| Iteración | i | posts[i].titulo | nodoPost |
|---:|---:|---|---:|
| 1 | 0 | 'Entrada 1' | nodo div con 'Entrada 1' |
| 2 | 1 | 'Entrada 2' | nodo div con 'Entrada 2' |

---

⚠️ Error típico: "Declarar una función la ejecuta"
- Falso: definir una función solo la describe. No se ejecuta hasta que la llamas (p. ej. `dibujaTitulo('X')`).
Ejemplo que desmonta:
```javascript
function plantilla() { console.log('ejecutada'); } // solo definición
// no aparece nada en consola hasta que llamas plantilla()
```

⚠️ Error típico: "Confundir el nombre de la variable con su valor"
- Falso: el nombre es una etiqueta; el valor puede cambiar.
Ejemplo:
```javascript
const a = {texto: 'A'}; // a apunta a un objeto {texto: 'A'}
const b = a;            // b apunta al mismo objeto
b.texto = 'B';          // cambiar la propiedad afecta al objeto
console.log(a.texto);   // 'B' -> no porque el nombre cambió, sino porque ambos referencian el mismo objeto
```

---

🔧 Modifícalo
Toma el worked example "dibujaPost" y cambia 1-2 líneas para que:
- el título use un h2 en lugar de h3,
- y el contenedor tenga una clase "post-card" (agrega cont.className = 'post-card').

Objetivo: cambiar la jerarquía visual y añadir estilo posible vía CSS.

---

🎯 Mini-reto
Crea una función `renderListaPosts(posts, contenedor)` que reciba un array de posts y un nodo contenedor, y use `dibujaPost(post)` para insertar todos los posts en ese contenedor.

Pista: usa un bucle for y `appendChild`.

---

📌 En resumen
- Una función es una plantilla reutilizable; la defines y la llamas para obtener un resultado.  
- Parámetros son los datos que la función recibe; return entrega el valor resultante (p. ej. un nodo DOM).  
- Reutilizar funciones reduce repetición: cambia la plantilla y se actualiza toda la interfaz.