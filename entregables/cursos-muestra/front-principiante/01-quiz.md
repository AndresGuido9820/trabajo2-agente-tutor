# Quiz — Guardar y nombrar datos: variables y valores

## Pregunta 1

Conectar con tu meta: al contar interacciones necesitas saber el total final. ¿Qué imprime este código?

let likes = 10
likes = likes + 5
console.log(likes)

- a) 10
- b) 15 ✅
- c) likes + 5
- d) Da error

> **Explicación:** Paso a paso: línea 1 → likes = 10; línea 2 → se evalúa la derecha (10 + 5 = 15) y se guarda en likes; línea 3 → imprime 15. La opción correcta es 15. El distractor más tentador ('10') refleja leer 'likes = likes + 5' como si fuera una ecuación que no cambia nada (error: leer la asignación como una igualdad matemática imposible).
> **Concepto:** variables

## Pregunta 2

En front-end a veces copias datos de una fuente. ¿Qué imprime este código?

let seguidores = 100
let copia = seguidores
seguidores = 120
console.log(copia)

- a) 120
- b) seguidores
- c) Error
- d) 100 ✅

> **Explicación:** Trazado: línea 1 → seguidores = 100; línea 2 → copia recibe el valor 100 (copia = 100); línea 3 → seguidores cambia a 120; línea 4 → console.log(copia) imprime 100. La respuesta correcta es 100. El distractor '120' refleja la creencia equivocada de que la asignación crea un vínculo permanente entre variables (error: creer que copiar hace que ambas se actualicen luego).
> **Concepto:** asignación

## Pregunta 3

Práctico para tus publicaciones: quieres que la consola muestre exactamente "Total de likes: 10" tras empezar con 7 y sumar 3. ¿Qué línea falta para lograrlo?

let likes = 7
likes = likes + 3
// ¿qué línea falta aquí?

- a) console.log("Total de likes: " + likes) ✅
- b) console.log(likes)
- c) console.log("Total de likes: X")
- d) console.log("Total de likes: likes")

> **Explicación:** Estado: likes inicia 7, luego likes = 7 + 3 → likes = 10. Para imprimir 'Total de likes: 10' necesitas concatenar el texto con el valor: console.log("Total de likes: " + likes). 'console.log("Total de likes: likes")' (distractor) imprime la palabra 'likes' literal: confusión entre el nombre de la variable y su valor (error: confundir nombre con valor).
> **Concepto:** console.log

## Pregunta 4

Concepto rápido para tus notas: ¿cuál definición describe mejor 'valor literal'?

- a) El nombre que le damos a un dato para usarlo después.
- b) Un valor que cambia con el tiempo cuando reasignas.
- c) Un dato escrito tal cual en el código, como 10 o "hola". ✅
- d) La instrucción que muestra valores en la consola.

> **Explicación:** Un valor literal es justamente un dato escrito tal cual en el código (ej.: 10, "hola"). La opción correcta es esa. El distractor más tentador ('El nombre que le damos a un dato...') confunde valor literal con variable (error: confundir variable con literal).
> **Concepto:** valor literal
