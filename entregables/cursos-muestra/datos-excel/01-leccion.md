# De Excel a Python: tipos y expresiones como fórmulas

En esta unidad aprenderás a traducir fórmulas de Excel a expresiones Python: reconocerás números, texto y fechas; usarás operadores como en una celda; y convertirás tipos cuando haga falta. Esto te sirve para preparar datos listos para análisis (igual que cuando limpias celdas en Excel antes de un gráfico). Quick win: calcularás un promedio y concatenarás texto tal como harías con una fórmula de celda.

🔮 Predice
```python
name = "María"
sales_q1 = 1500
sales_q2 = 2300
avg = (sales_q1 + sales_q2) / 2
message = name + " - promedio: " + str(avg)
print(message)
```
¿Qué crees que hace / imprime?

---

## Tipos de datos: número, texto, fecha
Respuesta a la predicción: imprime la cadena "María - promedio: 1900.0". Ahora lo explico.

Analogía Excel: una celda puede contener número, texto o fecha. En Python pasa igual: int (enteros), float (decimales), str (texto) y datetime (fechas).

Worked example (paso a paso)
```python
# 1. definir ventas como números
sales_q1 = 1500          # int
sales_q2 = 2300          # int

# 2. calcular promedio como expresión aritmética
avg = (sales_q1 + sales_q2) / 2   # float por la división

# 3. combinar texto con el promedio para un mensaje
message = "María" + " - promedio: " + str(avg)  # cast float->str

# 4. mostrar resultado final
print(message)
```
Estado tras cada línea relevante:
- después de sales_q1 = 1500
  - sales_q1: 1500 (int)
- después de sales_q2 = 2300
  - sales_q1: 1500 (int), sales_q2: 2300 (int)
- después de avg = (sales_q1 + sales_q2) / 2
  - avg: 1900.0 (float)
- después de message = ...
  - message: "María - promedio: 1900.0" (str)

Nota: en Excel, dividir celdas numéricas da número; en Python, la división / devuelve float aunque los operandos sean enteros.

---

## Operadores y expresiones
Concepto: una expresión combina valores y operadores para producir un resultado (como una fórmula en Excel =A1 + B1).

Ejemplo mínimo
```python
# 1. propósito: sumar y multiplicar para un total ponderado
valor1 = 10
valor2 = 5
total = valor1 + valor2 * 2   # * tiene prioridad, como en Excel
```
Estado:
- total: 20

Reglas importantes:
- Prioridad: * y / antes que + y - (igual que Excel).
- + sirve para sumar números y para concatenar cadenas, pero solo si los tipos encajan.

---

## Conversión de tipos (casting)
Cuando concatene texto y números, debes convertir el número a texto: en Excel usarías TEXT(), en Python usas str() o formateo.

Worked example: fecha sencilla
```python
# 1. propósito: crear una fecha desde texto (similar a DATEVALUE en Excel)
from datetime import datetime               # importar módulo de fechas
fecha_str = "2026-07-20"                    # string con formato ISO
fecha = datetime.strptime(fecha_str, "%Y-%m-%d")  # obtener datetime

# 2. propósito: extraer año como número para análisis
anio = fecha.year                            # int

# 3. propósito: mostrar texto con año
mensaje_fecha = "Año: " + str(anio)
print(mensaje_fecha)
```
Estado clave:
- fecha: datetime(2026, 7, 20)
- anio: 2026 (int)
- mensaje_fecha: "Año: 2026" (str)

Consejo: siempre piensa el tipo que necesitas antes de operar (¿quiero sumar? usa número. ¿quiero mostrar? convierte a str).

---

⚠️ Error típico (desmontando confusiones)
1) Leer `x = x + 1` como ecuación imposible. En Python significa: evalúa la derecha con el valor actual de x y guarda el nuevo valor en x. Ejemplo:
```python
x = 5
x = x + 1   # ahora x vale 6
```
2) Creer que asignar crea vínculo permanente:
```python
a = 10
b = a
a = 20
# b sigue siendo 10; b no cambia si a cambia
```
3) Confundir `=` con `==`: `=` asigna, `==` compara.
```python
x = 5      # asigna
x == 5     # pregunta si x es 5 -> True
```
4) Confundir nombre con valor: el nombre `avg` no es el número en sí, es la etiqueta que apunta al valor. Cambiar el valor crea uno nuevo apuntado por el nombre.

---

🔧 Modifícalo
Toma el primer worked example (promedio y mensaje).
- Cambia una línea para que el promedio se redondee a 1 decimal.
- Cambia otra línea para que el mensaje use el nombre de la variable `name` en lugar de "María".

Qué debe lograr: imprimir algo como "María - promedio: 1900.0" pero con un decimal fijo, por ejemplo "María - promedio: 1900.0" o "María - promedio: 1900.0" (si cambias name, usa la nueva cadena).

---

🎯 Mini-reto (conexo a tu meta: pasar fórmulas Excel a Python)
Crea código que:
- Tome tres valores de ventas: m1, m2, m3.
- Calcule el promedio.
- Imprima: "Promedio ventas: X.XX" con dos decimales y precedido por tu nombre (p. ej. "Carlos - Promedio ventas: 1234.56").

Pista: usa sum(...) o la suma directa, divide por 3, y convierte el número a texto con dos decimales usando round(...) o f-strings (si no viste f-strings aún, usa str(round(...,2))).

---

📌 En resumen
- Tipos: int/float/str/datetime determinan qué operaciones puedes hacer (como en las celdas de Excel).
- Expresiones combinan valores y operadores; la prioridad importa (* y / antes que + y -).
- Convierte tipos explícitamente (str(), int(), float(), datetime.strptime) antes de mezclar texto y números.