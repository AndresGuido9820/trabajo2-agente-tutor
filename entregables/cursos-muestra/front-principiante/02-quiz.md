# Quiz — Haz que la página responda: salida y entrada (DOM básico)

## Pregunta 1

¿Qué muestra este código en el párrafo <p id="salida"> tras hacer clic en el botón?

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

- a) Se muestra 'Hola, mundo' dentro del párrafo
- b) No ocurre nada porque la función no se ejecuta
- c) Se muestra el texto que hay en el campo (Hola, mundo) ✅
- d) Se muestra la palabra 'campo' en el párrafo

> **Explicación:** Al hacer clic se lee campo.value ("Hola, mundo") y se asigna a salida.innerText; por eso el párrafo muestra ese texto. El distractor más tentador dice que no se ejecuta la función: eso refleja la confusión 'declarar/definir una función la ejecuta' (error típico).
> **Concepto:** propiedad innerText / value

## Pregunta 2

¿Dónde está el error en este código que provoca que al hacer clic aparezca un fallo en la consola?

<input id="campoTexto" value="Hola">
<button id="miBoton">Mostrar</button>
<p id="salida"></p>

<script>
const campo = document.querySelector('campoTexto');
const boton = document.querySelector('#miBoton');
const salida = document.querySelector('#salida');

boton.addEventListener('click', function () {
  const texto = campo.value;
  salida.innerText = texto;
});
</script>

- a) Falta usar .value al leer el campo, por eso no hay texto
- b) La función no se invoca porque solo fue definida, no llamada
- c) El selector del campo no usa '#' (querySelector('campoTexto') es incorrecto) ✅
- d) El botón carece del id 'miBoton' y por eso boton es undefined

> **Explicación:** querySelector necesita el selector CSS correcto; para un id debe usarse '#campoTexto'. Aquí querySelector('campoTexto') devuelve null y luego campo.value provoca error. El distractor que dice 'falta .value' es tentador porque confunde el nombre de la variable con su valor: asume que 'campo' ya contiene el texto (error 'confundir el nombre de la variable con su valor').
> **Concepto:** seleccionar elemento (querySelector)

## Pregunta 3

En este fragmento falta una línea que vacíe el campo después de copiar su texto al párrafo. ¿Cuál debe añadirse dentro del handler para dejar el campo vacío?

// dentro del addEventListener
const textoCapturado = campo.value;
salida.innerText = textoCapturado;
// ¿LÍNEA QUE FALTA?

- a) campo.value = ''; ✅
- b) salida.innerText = '';
- c) campo = '';
- d) campo.innerText = '';

> **Explicación:** Para vaciar lo que el usuario ve en el <input> hay que cambiar su propiedad .value: campo.value = ''. El distractor 'campo = "";' es tentador porque confunde la referencia con el contenido: reasignar la variable 'campo' a una cadena no modifica el elemento en el DOM (error 'confundir el nombre de la variable con su valor').
> **Concepto:** propiedad innerText / value

## Pregunta 4

Si dentro del click handler, después de actualizar salida.innerText, añadimos la línea boton.disabled = true;, ¿qué ocurrirá tras el primer clic?

- a) El párrafo no cambia y el botón queda desactivado
- b) El párrafo muestra el texto y el botón desaparece de la página
- c) Se produce un error porque 'disabled' no es una propiedad válida
- d) El párrafo muestra el texto y el botón queda desactivado ✅

> **Explicación:** boton.disabled = true marca el botón como inactivo; la asignación no afecta al párrafo, así que primero se muestra el texto y luego el botón queda desactivado. El distractor más llamativo afirma que 'disabled' no existe: eso refleja desconfiar de propiedades del DOM sin comprobarlas, una falsa creencia sobre la inexistencia de propiedades estándar.
> **Concepto:** evento click (addEventListener)
