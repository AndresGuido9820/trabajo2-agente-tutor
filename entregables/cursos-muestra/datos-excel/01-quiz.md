# Quiz — De Excel a Python: tipos y expresiones como fórmulas

## Pregunta 1

¿Qué pasa / qué imprime este código?

name = "Carlos"
m1 = 100
m2 = 200
avg = (m1 + m2) / 2
message = name + " - promedio: " + avg
print(message)

- a) Carlos - promedio: 150.0
- b) Carlos - promedio: 150
- c) Da error TypeError por concatenar str y float ✅
- d) 150.0

> **Explicación:** avg es 150.0 (float). Intentar concatenar directamente str + float produce TypeError: Python no convierte números a texto automáticamente. El distractor más tentador ('Carlos - promedio: 150.0') refleja la creencia errónea de que Python hace la conversión implícita como en Excel: error de razonamiento sobre conversión automática de tipos.
> **Concepto:** conversión de tipos (casting)

## Pregunta 2

¿Qué imprime este código?

x = 5
x = x + 1
print(x)

- a) 6 ✅
- b) 5
- c) x + 1
- d) Da error porque x ya existía

> **Explicación:** La línea x = x + 1 evalúa la derecha con el valor actual de x (5 + 1 = 6) y guarda 6 en x; print muestra 6. El distractor '5' surge de leer la asignación como si fuera una ecuación matemática imposible (creencia de que x no cambia): esa es la confusión típica.
> **Concepto:** operadores y expresiones

## Pregunta 3

Falta una línea para que este código use la variable name y muestre el promedio con un decimal. ¿Qué línea falta?

name = "Luis"
sales_q1 = 1500
sales_q2 = 2300
avg = (sales_q1 + sales_q2) / 2
# línea faltante aquí
message = name + " - promedio: " + str(avg)
print(message)

- a) avg = int(avg)
- b) avg = round(avg, 1) ✅
- c) avg = str(avg)
- d) avg = avg + 1

> **Explicación:** Para fijar un decimal usamos avg = round(avg, 1); luego str(avg) produce, por ejemplo, '1900.0'. El distractor 'avg = str(avg)' confunde convertir el tipo (hacerlo str) con formatear/roundear a 1 decimal: es la confusión más tentadora entre conversión y formato.
> **Concepto:** operadores y expresiones

## Pregunta 4

Definición corta: ¿qué tipo de dato devuelve la expresión 3/2 en Python?

- a) int
- b) str
- c) datetime
- d) float ✅

> **Explicación:** En Python la división / siempre devuelve float aunque los operandos sean enteros, así 3/2 da 1.5 (float). El distractor 'int' refleja la idea errónea de que dividir enteros da entero (confusión por expectativas de división entera).
> **Concepto:** tipos de datos (int/float/str/datetime)
