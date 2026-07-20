# Quiz — Cargar y explorar datos: del archivo CSV a DataFrame (hoja → hoja de cálculo en Python)

## Pregunta 1

¿Qué imprime este código?

import pandas as pd
datos = pd.DataFrame({'A':[1,2,3], 'Venta':[10,20,30]})
print(datos.head(2))

- a) Tabla con las filas índice 0 y 1: A 1,2; Venta 10,20 ✅
- b) Tabla con las tres filas (índices 0,1,2) mostrando A y Venta
- c) Tabla con las filas índice 1 y 2 (como si el índice empezara en 1)
- d) Da error porque head espera un archivo, no un DataFrame

> **Explicación:** datos.head(2) devuelve las primeras 2 filas (índices 0 y 1). El distractor más tentador asume que el índice empieza en 1; eso refleja la falsa creencia de que las posiciones comienzan en 1 (error típico al comparar con Excel).
> **Concepto:** head()

## Pregunta 2

¿Qué imprime este código?

import pandas as pd
datos = pd.DataFrame({'Venta':[100,200]})
copia = datos
copia['Nueva'] = 1
print(datos.columns)

- a) Index(['Venta'])
- b) Error: no se puede asignar a la copia
- c) Index(['Venta', 'Nueva']) ✅
- d) Index(['Nueva'])

> **Explicación:** La asignación copia = datos hace que ambas variables referencien la misma tabla; añadir la columna vía copia modifica datos, por eso aparecen 'Venta' y 'Nueva'. El distractor más atractivo supone que copia creó una copia independiente; eso muestra la confusión 'creer que la asignación crea una copia independiente en vez de un enlace'.
> **Concepto:** columnas y filas

## Pregunta 3

Falta una línea para que este código use describe() y luego imprima la media de la columna 'Venta'. ¿Cuál línea hace eso?

import pandas as pd
datos = pd.DataFrame({'Venta':[10,20,30,40]})
# ¿qué línea falta aquí?
print('Media Venta:', media)

- a) media = datos.describe()['Venta','mean']
- b) media = datos.describe().loc['mean', 'Venta'] ✅
- c) media = datos.describe().loc['Venta','mean']
- d) media = datos['Venta'].mean

> **Explicación:** describe() devuelve un DataFrame con filas como 'mean' y columnas por nombre; usar .loc['mean','Venta'] extrae la media correcta. El distractor más tendente es usar datos['Venta'].mean sin paréntesis — eso confunde el método con su resultado (se está eligiendo el objeto función en vez de ejecutar la operación).
> **Concepto:** describe()

## Pregunta 4

¿Qué hace pd.read_csv('archivo.csv')?

- a) Muestra por pantalla las primeras filas sin cargar toda la tabla en memoria
- b) Convierte un DataFrame en un archivo CSV y lo guarda en disco
- c) Lee un archivo .xlsx (Excel) y lo abre como DataFrame
- d) Lee un archivo CSV y devuelve un DataFrame con la tabla cargada en memoria ✅

> **Explicación:** pd.read_csv lee el archivo CSV y devuelve un DataFrame (una tabla en memoria). El distractor más atractivo piensa que solo muestra una vista sin cargar; esa idea confunde 'visualizar una vista previa' con la acción de importar los datos en memoria.
> **Concepto:** pd.read_csv
