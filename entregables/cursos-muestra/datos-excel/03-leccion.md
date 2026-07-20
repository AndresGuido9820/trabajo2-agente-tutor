# Seleccionar y filtrar: vistas y columnas calculadas (como filtros y fórmulas)

Con esto podrás, como en Excel, seleccionar columnas, aplicar filtros y crear columnas que son fórmulas nuevas. Eso te sirve para preparar tablas de ventas: por ejemplo extraer ventas > X y añadir una columna de margen calculado —el quick win de esta unidad.

🔮 Predice

```python
import pandas as pd
df = pd.DataFrame({'producto':['A','B','C'],'ventas':[80,150,120]})
print(df[df['ventas'] > 100])
```

¿Qué crees que hace / imprime?

---

## 1) Indexación por columnas
Respuesta a la predicción: imprime las filas cuyo valor en la columna ventas es mayor que 100 (productos B y C).

Explicación (analogía Excel): seleccionar una columna con df['ventas'] es como hacer clic en el encabezado de la columna "ventas" en Excel. Obtienes esa columna para operar.

Worked example
```python
import pandas as pd
# 1. crear muestra de datos
df = pd.DataFrame({
    'producto': ['A','B','C'],
    'ventas': [80,150,120],
    'coste': [50, 90, 70]
})
# Estado: df es una tabla de 3 filas con columnas producto, ventas, coste

# 2. seleccionar la columna 'ventas'
serie_ventas = df['ventas']
# Estado: serie_ventas -> [80, 150, 120]

# 3. imprimir la selección (subobjetivo: ver valores)
print(serie_ventas)
```
Máquina nocional: después de la línea de creación, df contiene la tabla; después de la asignación, serie_ventas es una Series con los tres números.

---

## 2) Máscaras booleanas (filtrado)
Definición: una máscara booleana es una lista de True/False, una por cada fila, que indica si la fila pasa el filtro. Es el equivalente al filtro de Excel que marca filas visibles.

Worked example (continúa)
```python
# 4. crear máscara: ventas > 100 (subobjetivo: marcar filas relevantes)
mascara = df['ventas'] > 100
# Estado: mascara -> [False, True, True]

# 5. aplicar máscara para obtener vista filtrada (subobjetivo: extraer filas)
vista_filtrada = df[mascara]
# Estado: vista_filtrada contiene las filas donde mascara es True (B y C)

print(vista_filtrada)
```
Máquina nocional: la comparación produce la máscara; usar df[mascara] construye una nueva tabla con solo las filas True.

---

## 3) Asignar nuevas columnas (columnas calculadas)
Definición: crear una columna nueva es como escribir una fórmula en Excel y arrastrarla; en Python asignas una Serie al nombre de la nueva columna.

Worked example (añadir margen absoluto)
```python
# 6. calcular margen = ventas - coste (subobjetivo: crear columna con fórmula entre columnas)
df['margen'] = df['ventas'] - df['coste']
# Estado: df ahora tiene columna 'margen' con [30, 60, 50]

# 7. mostrar tabla resultante (subobjetivo: ver el quick win)
print(df)
```
Resultado (estado final): tabla con producto, ventas, coste, margen. Quick win cumplido: extrajiste ventas > 100 y añadiste margen.

Operaciones columna a columna: las operaciones aritméticas entre Series se aplican elemento a elemento (fila a fila), igual que una fórmula que referencia otras columnas en la misma fila.

---

⚠️ Error típico (desmontajes)

- Leer x = x + 1 como ecuación imposible:
```python
x = 1
x = x + 1  # primero se evalúa la derecha (1+1), luego se asigna: x queda 2
```
No es una ecuación matemática; es "tomar el valor actual, calcular y guardar el nuevo".

- Creer que la asignación crea vínculo permanente:
```python
a = df['ventas']
b = a
a = a + 10  # a cambia a una nueva Series; b sigue siendo la antigua
```
Asignar no hace que dos nombres sigan idénticos si uno cambia por reasignación.

- Confundir = con == (asignación vs comparación):
```python
# filtro correcto (comparación)
mask = df['ventas'] == 100   # devuelve True/False por fila
# mientras que df['ventas'] = 100 intentaría asignar 100 a toda la columna
```

---

🔧 Modifícalo
Toma el worked example y cambia 1-2 líneas para lograr esto: en lugar de margen absoluto (ventas - coste), crea una columna 'margen_pct' que sea (ventas - coste) / ventas * 100 (porcentaje de margen).

(Qué debe lograr: añadir la columna 'margen_pct' con valores en porcentaje.)

---

🎯 Mini-reto
Usando un CSV de ventas que ya cargaste en unidades anteriores, crea una vista con filas donde ventas > 200 y añade una columna llamada 'margen' = ventas - coste. Pista: usa df[condición] para filtrar y df['nueva'] = ... para crear la columna.

---

📌 En resumen
- df['columna'] selecciona una columna; es equivalente al encabezado de columna en Excel.  
- df[mask] filtra filas: mask es una Series booleana (True/False) generada por condiciones.  
- df['nueva'] = expr crea una columna calculada; operaciones entre columnas se aplican fila a fila.