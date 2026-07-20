# Haz que la página responda: salida y entrada (DOM básico)

Esta unidad te enseña a leer lo que escribe un usuario y mostrarlo en la página cuando pulsa un botón — justo lo que necesitas para crear formularios, comentarios o pequeños widgets en tus páginas (piensa en el cuadro de texto de una publicación y el botón "Publicar" en redes). Al final tendrás un botón que, al hacer clic, copia el texto del campo y lo muestra en la página. Quick win: verás tu texto en la pantalla con un solo clic.

🔮 Predice

¿Qué crees que hace / muestra este código en el navegador?

```html
<input id="campoTexto" value="Hola, mundo">
<button id="miBoton">Mostrar</button>
<p id="salida"></p>

<script>
const campo = document.querySelector('#campoTexto');
const boton = document.querySelector('#miBoton');
const salida = document.querySelector('#salida');

boton.addEventListener('click', function () {
  const textoCapturado = campo.value;
  salida.innerText = textoCapturado;
});
</script>
```

(Guarda tu idea; no leas la explicación todavía.)

Concepto 1 — DOM (Documento)
Respuesta a la predicción: cuando haces clic en el botón, el texto que esté en el campo aparece dentro del párrafo vacío.  
Explicación: el DOM es la versión que el navegador crea de la página: una "lista" de cajas (elementos) que JavaScript puede leer y cambiar. Analogy: tu presentación en PowerPoint tiene cuadros de texto editables; el DOM es la diapositiva viva que JavaScript puede editar mientras presentas.

Worked example (completo, paso a paso)
// 1. preparar referencias a los elementos
```javascript
// 1. obtener referencia al campo de texto
const campo = document.querySelector('#campoTexto');
// 2. obtener referencia al botón
const boton = document.querySelector('#miBoton');
// 3. obtener referencia al párrafo de salida
const salida = document.querySelector('#salida');

// 4. cuando el usuario hace clic, copiar el texto del campo a la página
boton.addEventListener('click', function () {
  // 4.1 leer el valor actual del campo
  const textoCapturado = campo.value;
  // 4.2 mostrar ese texto en la página
  salida.innerText = textoCapturado;
});
```

Máquina nocional — estado línea a línea (cuando el script carga)
- Después de línea 1: campo → referencia al <input id="campoTexto"> (no su valor, sino la caja).
- Después de línea 2: boton → referencia al <button id="miBoton">.
- Después de línea 3: salida → referencia al <p id="salida">.
- Al añadir el event listener (línea 4): hay una regla en la página: "si el usuario hace clic en boton, ejecutar la función".
- Al hacer clic:
  - Se crea textoCapturado y se le asigna el contenido actual de campo.value (ej.: "Hola, mundo").
  - salida.innerText se actualiza con ese valor, y el usuario lo ve en pantalla.

Concepto 2 — querySelector
Explicación: querySelector busca en el DOM el elemento que coincida con el selector CSS que le pases (por ejemplo '#miBoton'). Analogy: es como buscar el slide que tiene un cuadro con un título concreto en tu presentación.

Concepto 3 — value / innerText
Definición: value es el texto que el usuario escribió en un campo <input>. innerText es el texto que aparece dentro de un elemento visible (<p>, <div>). Analogy: value es lo que escribes en el cajetín de comentarios; innerText es lo que aparece en la publicación.

Concepto 4 — addEventListener('click', ...)
Explicación: addEventListener conecta una acción del usuario (evento) con una función que se ejecuta cuando ocurre. Defino "función": es un bloque de instrucciones que solo se ejecuta cuando se le pide (no se ejecuta al definirla). Analogy: agregar un recordatorio que diga "cuando presione este botón, pega el texto en la diapositiva".  

⚠️ Error típico (y desmontes)

- "Confundir el nombre de la variable con su valor."  
  Ejemplo incorrecto: creer que escribir campo = "hola" cambia el input en la página.  
  Aclaración: campo es una referencia al elemento; campo.value guarda el texto. Para cambiar lo visible debes escribir campo.value = "hola".

- "Una variable guarda varios valores o recuerda su historial."  
  Ejemplo incorrecto: pensar que después de asignar textoCapturado = campo.value las asignaciones anteriores siguen guardadas en textoCapturado.  
  Aclaración: una variable solo tiene el último valor que le asignaste. Si quieres historial, necesitas otra estructura (aun no vista).

- "Declarar/definir una función la ejecuta."  
  Ejemplo incorrecto: escribir function prueba() { ... } y esperar que corra sin llamarla.  
  Aclaración: en addEventListener pasamos la función para que el navegador la ejecute al hacer clic; definirla no la ejecuta automáticamente.

🔧 Modifícalo
Cambia 1-2 líneas del worked example para lograr esto: después de mostrar el texto en la página, borrar el contenido del campo (dejarlo vacío). (Qué debes lograr: al hacer clic, el párrafo muestra el texto y el campo queda vacío).

🎯 Mini-reto
Crea la misma página pero que, además de mostrar el texto en el párrafo, el botón se desactive (no se pueda pulsar otra vez) después del primer clic — como "publicar" que solo se permite una vez. Pista: hay una propiedad que controla si un botón está activo (hint: se escribe en el elemento del botón).

📌 En resumen
- querySelector devuelve una referencia a un elemento del DOM; usa selectores CSS.  
- Lee texto del usuario con .value y muestra texto en la página con .innerText.  
- addEventListener('click', función) ejecuta esa función solo cuando el usuario hace clic.