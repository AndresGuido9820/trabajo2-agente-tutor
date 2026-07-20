# Funciones para automatizar cálculos: de fórmula puntual a herramienta reutilizable
Automatizar cálculos te permite dejar de copiar y pegar fórmulas como en Excel y crear “macros pequeñas” en Python que puedes aplicar a todo un DataFrame. Esto acelera análisis repetitivos (p. ej. normalizar columnas antes de modelar) y hace tu trabajo reproducible.

🔮 Predice
```python
import pandas as pd

s = pd.Series([10, 20, 30])

def sumar(x, inc=5):
    return x + inc

print(s.apply(sumar))
```
¿Qué crees que hace / imprime?

---

## 1) def / return — respuesta a la predicción y explicación
Respuesta a la predicción: imprime una Series con cada valor incrementado en 5 → [15, 25, 35].

Analogía Excel: definir una función en Python es como escribir una fórmula nombrada que luego puedes usar en toda la columna. Definir no calcula nada hasta que la aplicas (igual que guardar una fórmula en VBA no la ejecuta).

Worked example (mínimo):
```python
# 1. definir la función que suma un incremento
def sumar(x, inc=5):
    return x + inc

# 2. crear la Serie (como una columna)
s = pd.Series([10, 20, 30])

# 3. aplicar la función a cada celda de la columna
resultado = s.apply(sumar)

# 4. mostrar resultado
print(resultado)
```
Estado máquina (línea clave):
- tras def sumar: sumar → <función>
- tras crear s: s → Series([10,20,30])
- tras apply: resultado → Series([15,25,35])

Nota: definir (def) crea el objeto función; return envía el valor al que llama la función.

---

## 2) Parámetros y valores por defecto
Qué es: parámetro = nombre que recibe el dato dentro de la función. Valor por defecto permite llamar a la función sin dar ese argumento.

Analogía Excel: es como una fórmula con argumento opcional; p. ej. =MI_FUNCION(celda, 5) o solo =MI_FUNCION(celda) si 5 es el default.

Worked example (extendiendo el anterior):
```python
# 1. crear función con parámetro opcional
def escalar(x, factor=2):
    return x * factor

# 2. ejemplo de uso con y sin el argumento
a = escalar(10)     # usa factor=2
b = escalar(10, 3)  # usa factor=3
```
Estado máquina:
- después def escalar: escalar → <función>
- a → 20
- b → 30

Regla: el valor por defecto se usa solo si no pasas ese argumento al llamar.

---

## 3) Aplicar funciones a columnas: apply
Para qué sirve: transforma una columna aplicando la misma lógica a cada celda; equivalente a escribir fórmula y arrastrarla o usar columna calculada en Excel.

Worked example completo: función que normaliza una columna (min-max 0-1) y la aplica al DataFrame.
```python
import pandas as pd

# 1. ejemplo de DataFrame
df = pd.DataFrame({'id':[1,2,3], 'puntaje':[40, 60, 80]})

# 2. definir función para normalizar un valor
def normalizar(valor, min_val, max_val):
    return (valor - min_val) / (max_val - min_val)

# 3. calcular min y max para la columna
min_p = df['puntaje'].min()
max_p = df['puntaje'].max()

# 4. aplicar la normalización y crear nueva columna
df['puntaje_norm'] = df['puntaje'].apply(lambda v: normalizar(v, min_p, max_p))

# 5. ver resultado
print(df)
```
Estado máquina (resumen):
- df inicial → {'id':[1,2,3], 'puntaje':[40,60,80]}
- min_p → 40, max_p → 80
- df final → {'id':[1,2,3], 'puntaje':[40,60,80], 'puntaje_norm':[0.0,0.5,1.0]}

Quick win: ya tienes una función reutilizable que hace lo que en Excel harías con (x-min)/(max-min) y puedes aplicarla a cualquier columna.

---

⚠️ Error típico — desmontes rápidos
1) "Declarar una función la ejecuta": falso. def solo crea la función. Ejemplo:
```python
def hola():
    print("hola")
# no se imprime hasta que llamas: hola()
```
2) Leer `x = x + 1` como ecuación imposible: en Python significa: calcula x+1 con el valor actual de x y guarda ese resultado en x. Ejemplo:
```python
x = 2
x = x + 1  # ahora x es 3
```
3) Confundir nombre de variable con su valor: la variable es una etiqueta. Cambiar otra variable no cambia la etiqueta automática. Ejemplo:
```python
a = [1,2]
b = a
b = [3]   # ahora b apunta a otra lista; a sigue siendo [1,2]
```

---

🔧 Modifícalo
Toma el worked example de normalización. Cambia 1-2 líneas para que la función normalice usando z-score (restar media y dividir por desviación estándar). Objetivo: en la nueva columna, la media debe ser aproximadamente 0.

🎯 Mini-reto
Escribe una función llamada normalizar_columna(df, columna) que:
- calcule min y max de df[columna],
- añada una columna nueva llamada columna + '_norm',
- devuelva el DataFrame modificado.
Pista: usa df['columna'].min(), .max() y .apply() con una lambda que llame a tu función de normalización.

📌 En resumen
- def crea una función; return envía un valor cuando se ejecuta. Definir ≠ ejecutar.
- Parámetros pueden tener valores por defecto; úsalos para comportamientos opcionales.
- apply permite aplicar una función a cada celda de una columna, como arrastrar una fórmula en Excel.