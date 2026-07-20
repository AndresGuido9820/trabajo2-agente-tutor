# Cargar y explorar datos: del archivo CSV a DataFrame (hoja → hoja de cálculo en Python)

Esta unidad te sirve para llevar a Python las hojas con las que trabajas en Excel. Podrás abrir un CSV como si fuera una hoja, mirar las primeras filas como en "Vista previa" y obtener un resumen estadístico tipo "Resumen rápido". Eso te acerca a preparar datos para análisis en ciencia de datos.

🔮 Predice

```python
import pandas as pd
datos = pd.read_csv('archivo.csv')
print(datos.head())
print(datos.describe())
```

¿Qué crees que imprime cada print? ¿Cuál será la diferencia entre head() y describe()?

---

## DataFrame — ¿qué es? (respuesta a la predicción)
Respuesta breve a la predicción: 
- datos.head() imprime las primeras filas del DataFrame (una vista de la hoja).  
- datos.describe() imprime un resumen estadístico para columnas numéricas (conteo, media, desviación, percentiles).

Definición: un DataFrame es una tabla en memoria —como una hoja de Excel— con filas y columnas. Cada columna tiene un tipo (número, texto). Un CSV (Comma-Separated Values) es un archivo de texto que guarda una tabla.

Analogía Excel: DataFrame = hoja; columnas = columnas; filas = filas. read_csv = Abrir → Importar datos desde un archivo .csv.

Worked example (quick win: cargar archivo.csv, mostrar 5 filas y describe()):

```python
import pandas as pd
# 1. cargar archivo en un DataFrame
datos = pd.read_csv('archivo.csv')

# 2. ver las primeras 5 filas (preview)
print(datos.head())

# 3. ver resumen estadístico (Resumen rápido tipo Excel)
print(datos.describe())
```

Estado de la máquina (estado de variables) después de cada línea relevante:
- Tras `datos = pd.read_csv('archivo.csv')`
  - datos: DataFrame con forma (n_filas, n_columnas), p. ej. columnas ['A', 'B', 'Venta']
  - no hay impresión aún.
- Tras `datos.head()` (cuando se imprime)
  - salida: tabla con índices 0..4 y las primeras 5 filas (valores de cada columna).
- Tras `datos.describe()` (cuando se imprime)
  - salida: tabla con filas ['count','mean','std','min','25%','50%','75%','max'] por cada columna numérica.

---

## pd.read_csv
Qué hace: lee un archivo CSV y devuelve un DataFrame. Parámetros útiles (más adelante): ruta del archivo, separador, encoding.

Analogía Excel: es equivalente a "Datos → Obtener y transformar → Desde archivo CSV".

Worked mini-ejemplo:
```python
# 1. cargar
datos = pd.read_csv('archivo.csv')  # datos ahora contiene toda la hoja importada
```

Estado: datos tiene todas las filas y columnas del archivo.

---

## head()
Qué hace: devuelve las primeras n filas (por defecto 5). Útil para comprobar que la importación fue correcta.

Analogía Excel: mirar las primeras filas en la vista previa.

Ejemplo:
```python
print(datos.head())  # ver 5 primeras filas
print(datos.head(10))  # ver 10 primeras filas
```

Estado: no cambia datos, solo muestra una parte.

---

## info()
Qué hace: muestra resumen de tipos de columna, cuántos valores no nulos y memoria usada. Sirve para detectar columnas con textos, números, o datos faltantes.

Ejemplo:
```python
datos.info()  # ver tipos y conteo de no nulos
```

---

## describe()
Qué hace: calcula estadísticas descriptivas para columnas numéricas: count, mean, std, min, percentiles y max.

Analogía Excel: parecido a "Resumen rápido" o a las funciones de estadísticas que usas en celdas, pero aplicado a cada columna en bloque.

Ejemplo:
```python
print(datos.describe())  # estadísticas para columnas numéricas
```

Para obtener la media de la columna "Venta":
- pista: describe() devuelve una tabla; puedes pedir la fila 'mean' y la columna 'Venta'.

---

## Columnas y filas
- Columnas: se acceden con datos.columns (lista de nombres).
- Filas: el índice que ves al lado izquierdo empieza en 0 por defecto (a diferencia de Excel, que muestra filas empezando en 1).

Ejemplo:
```python
print(datos.columns)  # nombres de columnas
print(datos.shape)    # (n_filas, n_columnas)
```

---

⚠️ Error típico — la asignación no crea copia permanente (y el índice empieza en 0)
1) Asignación enlaza, no copia:
```python
copia = datos          # copia y datos referencian la misma tabla
copia['nueva'] = 1    # modifica también datos
```
Si querías una copia independiente, usa `copia = datos.copy()`.

2) Índices empiezan en 0:
En la vista verás la primera fila con índice 0. No la confundas con la fila 1 de Excel. Para contar filas, usa datos.shape[0].

---

🔧 Modifícalo
Toma el worked example y cambia 1–2 líneas para:
- Mostrar las primeras 10 filas en vez de 5.
- Mostrar solo las estadísticas de la columna llamada 'Venta'.

(No te doy la solución; modifica los argumentos y/o el acceso a columnas.)

---

🎯 Mini-reto
Carga 'archivo.csv', muestra las primeras 5 filas y calcula la media de la columna 'Venta'. Imprime: "Media Venta: X".

Pista: usa describe() y extrae la fila 'mean' para la columna 'Venta'.

---

📌 En resumen
- pd.read_csv(...) abre un CSV y devuelve un DataFrame (una hoja en memoria).  
- datos.head() muestra las primeras filas; datos.describe() da estadísticas numéricas.  
- La asignación por defecto enlaza objetos (usa .copy() si quieres duplicar) y los índices en pandas empiezan en 0 (no en 1 como Excel).