# Repetir tareas: bucles para crear listas y elementos

Esta unidad te enseña a generar muchas piezas de la interfaz de forma automática. Es lo que necesitas para mostrar una lista de mensajes o comentarios en una página —como cuando publicas varias diapositivas o varios posts en redes— sin copiar y pegar HTML a mano.

🔮 Predice

¿Qué crees que hace / muestra este código?

```javascript
const mensajes = ["Hola", "¿Cómo estás?", "Nos vemos"];
for (let i = 0; i < mensajes.length; i++) {
  const elemento = document.createElement("li");
  elemento.textContent = mensajes[i];
  document.querySelector("#lista").appendChild(elemento);
}
```

(Responde mentalmente antes de seguir.)

---

Concepto: for (bucle)

Respuesta a la predicción: crea un elemento <li> por cada texto en el arreglo `mensajes` y los añade dentro del elemento con id "lista".

Explicación (analogía): piensa en preparar las diapositivas de una presentación: tienes una lista de títulos y repites la misma acción (crear una diapositiva, ponerle el título, añadirla a la pila). El bucle `for` automatiza esa repetición.

Worked example: crear una lista de mensajes en el DOM

```javascript
// 1. datos de entrada
const mensajes = ["Hola", "¿Cómo estás?", "Nos vemos"];

// 2. preparar contenedor en la página
const contenedorLista = document.querySelector("#lista"); // 2.1 seleccionar <ul> existente

// 3. recorrer los mensajes y añadir cada uno al DOM
for (let i = 0; i < mensajes.length; i++) {
  // 3.1 crear elemento de lista
  const elemento = document.createElement("li"); 

  // 3.2 poner el texto correspondiente al índice actual
  elemento.textContent = mensajes[i]; 

  // 3.3 añadir el elemento al contenedor en la página
  contenedorLista.appendChild(elemento);
}
```

Máquina nocional — estado línea a línea (variables relevantes)
- Antes del bucle:
  - mensajes = ["Hola","¿Cómo estás?","Nos vemos"]
  - i no existe
  - contenedorLista = (referencia al <ul id="lista">)
- i = 0 (inicio 1ª vuelta)
  - mensajes[i] = "Hola"
  - elemento = <li> vacío
  - después elemento.textContent = "Hola"
  - appendChild añade <li>Hola</li> dentro de #lista
- i = 1 (2ª vuelta)
  - mensajes[i] = "¿Cómo estás?"
  - crea <li>¿Cómo estás?</li> y lo añade
- i = 2 (3ª vuelta)
  - mensajes[i] = "Nos vemos"
  - crea <li>Nos vemos</li> y lo añade
- i = 3
  - condición i < mensajes.length (3 < 3) es falsa → bucle termina

Concepto: índice (i) y iteración

Explicación: `i` indica la posición actual en la lista. Empieza en 0 y sube de a 1 cada vuelta. En nuestra analogía, `i` es el número de diapositiva que estás creando en ese momento.

Concepto: createElement y appendChild

Explicación: `createElement` fabrica un nodo HTML en memoria (como preparar una diapositiva en blanco). `appendChild` la coloca en la página (como pegar la diapositiva en el proyector).

⚠️ Error típico

- Error: creer que las posiciones empiezan en 1. Si intentas leer `mensajes[1]` pensando que es el primero, obtendrás el segundo. Ejemplo rápido:
  - mensajes = ["A","B"]; mensajes[0] es "A", mensajes[1] es "B".
- Error: leer `x = x + 1` como una ecuación imposible. En programación significa: toma el valor actual de `x`, súmale 1 y guarda ese resultado en `x`. No hay igualdad simbólica, es instrucción.
  - Ejemplo: let x = 0; x = x + 1; // ahora x vale 1
- Error: pensar que una variable guarda varios valores o historial. `i` solo contiene el valor actual; no recuerda las vueltas anteriores.

Desmontaje con ejemplo pequeño:

```javascript
let x = 0;
x = x + 1; // ahora x vale 1, no hay "vínculo" mágico con el 0.
```

🔧 Modifícalo

Toma el worked example y cambia 1-2 líneas para que:
- solo muestre los primeros 2 mensajes (no todos), o
- muestre los mensajes en mayúsculas.

Indica qué línea(s) cambiaste y qué lograbas.

🎯 Mini-reto

Crea la misma lista pero añade la palabra "(largo)" al final de cada mensaje que tenga más de 7 caracteres. Usa el bucle `for` y el condicional que ya conoces.

Pista: dentro del bucle, comprueba `mensajes[i].length` y cambia `elemento.textContent` según corresponda.

📌 En resumen
- Usa `for (let i = 0; i < arreglo.length; i++)` para repetir una acción por cada elemento.
- `i` empieza en 0; `arreglo[i]` accede al elemento actual.
- `createElement` crea nodos y `appendChild` los añade al DOM. Quick win: con el ejemplo anterior ya puedes renderizar cualquier lista de textos desde JavaScript.