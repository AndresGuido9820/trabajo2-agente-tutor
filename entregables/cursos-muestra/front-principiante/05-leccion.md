# Estructurar contenido: arrays y objetos para tus posts

Quieres que la página muestre muchos posts como en una red social o una diapositiva con notas. Esta unidad te enseña a guardar varias entradas, cada una con autor, texto y fecha, y a recorrer esa colección para renderizarla dinámicamente en la página.

🔮 Predice
```javascript
const posts = [
  { autor: "Ana", texto: "¡Hola a todos!", fecha: "2026-07-20" },
  { autor: "Tú", texto: "Mi primer post", fecha: "2026-07-20" }
];

console.log(posts[0].autor);
console.log(posts.length);
```
¿Qué crees que imprime en la consola?

---

## 1) Array
Respuesta a la predicción (aquí toca): imprime "Ana" en la primera línea y 2 en la segunda.

Qué es: un array es una lista ordenada de valores. Piensa en la lista de diapositivas de una presentación: la primera diapositiva está en la posición 0 (índice 0), la segunda en 1, etc.

Worked example (crear y añadir posts)
```javascript
// 1. crear colección vacía de posts
const posts = [];              

// 2. crear primer post como objeto
const primerPost = { autor: "Ana", texto: "¡Hola a todos!", fecha: "2026-07-20" };

// 3. añadir primer post a la colección
posts.push(primerPost);

// 4. ver cuántos hay
console.log(posts.length); // debería mostrar 1
```

Estado línea a línea (estado relevante)
- after line 1: posts = []
- after line 2: primerPost = { autor: "Ana", texto: "¡Hola a todos!", fecha: "2026-07-20" }
- after line 3: posts = [ { autor: "Ana", ... } ], posts.length = 1

(Observa cómo el computador crea valores y luego actualiza la colección al ejecutar push.)

---

## 2) Objeto (propiedades y valores)
Qué es: un objeto agrupa datos relacionados en pares nombre:valor. Para un post, nombres comunes son autor, texto, fecha. Es como una tarjeta de contacto en tus presentaciones: un lugar donde están nombre, cargo, email.

Worked example (usar un solo post)
```javascript
// 1. definir un post con propiedades
const post = { autor: "Tú", texto: "Mi primer post", fecha: "2026-07-20" };

// 2. mostrar autor y texto del post
console.log(post.autor);
console.log(post.texto);
```

Estado (después de definir)
- post = { autor: "Tú", texto: "Mi primer post", fecha: "2026-07-20" }

---

## 3) Acceder por índice
Qué es: cada elemento en un array tiene una posición llamada índice; el primer índice es 0. Para obtener el segundo post usamos posts[1].

Worked example (leer segundo post)
```javascript
// 1. colección con dos posts (ya creada)
const posts = [
  { autor: "Ana", texto: "¡Hola!", fecha: "2026-07-20" },
  { autor: "Tú", texto: "Mi primer post", fecha: "2026-07-20" }
];

// 2. acceder al autor del primer elemento
console.log(posts[0].autor); // muestra "Ana"

// 3. acceder al texto del segundo elemento
console.log(posts[1].texto); // muestra "Mi primer post"
```

Estado (relevante)
- posts.length = 2
- posts[0] = { autor: "Ana", ... }
- posts[1] = { autor: "Tú", ... }

---

## 4) Métodos básicos: push y length
Definición:
- push: añade un elemento al final de un array.
- length: número de elementos del array.

Ejemplo ya mostrado antes usa push y length; recuerda: después de push, length aumenta en 1.

---

⚠️ Error típico (y cómo evitarlo)
1. Índices empiezan en 0, no en 1.
```javascript
const a = ["x","y"];
console.log(a[1]); // "y" (no "x")
console.log(a[a.length]); // undefined — el último índice es a.length - 1
```
2. Creer que una variable guarda su historial. No: una variable contiene el valor actual.
```javascript
let contador = 1;
contador = 2;
console.log(contador); // muestra solo 2, no 1 y 2
```
3. Pensar que la asignación crea un vínculo permanente entre dos variables.  
- Si ambas apuntan al mismo objeto y cambias una propiedad, el cambio se ve desde ambas (comparten objeto).  
- Pero reasignar una variable no cambia la otra.
```javascript
let A = { autor: "Ana" };
let B = A;
B.autor = "Carlos";
console.log(A.autor); // "Carlos" (comparten el mismo objeto)
B = { autor: "Luis" };
console.log(A.autor); // sigue "Carlos" (reasignar B no cambia A)
```

---

🔧 Modifícalo
Toma el worked example de "Array" (el que usa posts.push).
- Cambia el autor del primerPost a tu nombre.
- Añade un segundo post con tu propio texto usando push.
Objetivo: que posts.length sea 2 y que console.log muestre tu nombre en uno de los posts.

🎯 Mini-reto
Crea un array llamado posts con al menos 3 objetos (autor, texto, fecha). Usa un bucle for para imprimir "autor: texto" de cada post en la consola. Pista: usa posts.length para la condición del for y posts[i] para acceder.

📌 En resumen
- Un array es una lista ordenada; el primer índice es 0 y el último es length - 1.  
- Un objeto agrupa propiedades con nombres (autor, texto, fecha) y se accede con post.propiedad.  
- push añade al final; length dice cuántos hay. Usa bucles + acceso por índice para renderizar posts.