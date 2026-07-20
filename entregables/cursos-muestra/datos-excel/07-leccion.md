# Mini proyecto: pipeline reproducible — del CSV al insight y salida final
Esta unidad te muestra cómo automatizar el flujo que hoy haces manualmente en Excel (abrir archivo, limpiar datos, calcular tablas dinámicas, exportar y crear un gráfico para la reunión). Objetivo: un script/notebook que genera summary.csv y una gráfica lista para presentar.

🔮 Predice
```python
import pandas as pd
df = pd.read_csv("ventas.csv")
df["revenue"] = df["precio"] * df["cantidad"]
resumen = df.groupby("region")["revenue"].sum().reset_index()
print(resumen.head())
```
¿Qué crees que imprime / muestra ese código?

---

## 1) Pipeline reproducible — secuencia de pasos
Respuesta a la predicción: imprime las primeras filas de una tabla con columnas `region` y la suma de `revenue` por región (similar a una tabla dinámica de Excel: región vs suma de ingresos).

Explicación y analogía: Un pipeline es como la secuencia en tu libro de trabajo: abrir la hoja → aplicar filtros/fórmulas → crear tabla dinámica → copiar el resultado. Aquí codificamos cada paso para repetirlo exactamente.

Worked example (script mínimo):
```python
# 1. cargar datos
import pandas as pd
df = pd.read_csv("ventas.csv")             # propósito: traer la hoja CSV

# 2. limpiar/transformar
df = df.dropna(subset=["precio","cantidad"])  # propósito: quitar filas incompletas
df["revenue"] = df["precio"] * df["cantidad"] # propósito: calcular ingreso por fila (vectorizado)

# 3. agregar (tabla dinámica)
resumen = df.groupby("region")["revenue"].sum().reset_index()  # propósito: sumar revenue por región

# 4. exportar
resumen.to_csv("summary.csv", index=False)  # propósito: guardar tabla final para compartir
```

Estado (máquina nocional) línea a línea (ejemplo corto):
- después de read_csv: df tiene filas con columnas `precio`, `cantidad`, `region`, ...
- después dropna: filas con NaN en precio o cantidad fueron removidas
- después de crear `revenue`: df ahora tiene columna `revenue` con números
- después groupby: `resumen` es un DataFrame con 1 fila por `region` y columna `revenue` con suma

Quick win: ejecutar ese script produce `summary.csv`.

## 2) Exportar resultados (to_csv)
Explicación y analogía: En Excel guardas un rango como CSV para llevarlo a la presentación. `to_csv` hace eso programáticamente.

Worked example (comentado):
```python
# propósito: asegurar orden y formato
resumen = resumen.sort_values("revenue", ascending=False)  # propósito: ordenar para presentar
resumen.to_csv("summary.csv", index=False)                 # propósito: exportar sin columna índice extra
```
Resultado: archivo `summary.csv` listo para adjuntar en un correo o importar a PowerPoint.

## 3) Visualización básica (matplotlib / seaborn)
Explicación y analogía: En Excel usarías un gráfico de barras con la tabla dinámica. Aquí generamos la misma gráfica por código, reproducible y exportable.

Worked example (comentado):
```python
# 1. importar librería de gráficos
import matplotlib.pyplot as plt
import seaborn as sns

# 2. crear gráfico
plt.figure(figsize=(6,4))                               # propósito: tamaño del lienzo
sns.barplot(data=resumen, x="region", y="revenue")      # propósito: barras por región
plt.title("Ingresos por región")                         # propósito: etiqueta del gráfico
plt.tight_layout()                                       # propósito: mejorar ajuste
plt.savefig("revenue_by_region.png")                     # propósito: guardar imagen lista para la reunión
```
Estado relevante: archivo `revenue_by_region.png` creado.

⚠️ Error típico (desmontaje)
- Confundir `=` con `==`: `=` asigna un valor (x = 5). `==` compara (x == 5).
  Ejemplo: `if x = 5:` es error de sintaxis; usa `if x == 5:`.
- Creer que una variable guarda su historial: después de `x = 1` y `x = 2`, `x` vale 2; no existe lista automática de valores previos.
- Creer que definir una función la ejecuta: `def procesar(df): ...` solo crea la función; debes llamarla `procesar(df)` para que corra.

Breve ejemplo que desmonta la confusión de asignación:
```python
x = 1
x = x + 1  # la derecha se evalúa (1+1) y ese resultado (2) se guarda en x
# ahora x vale 2; no es una ecuación a resolver.
```

🔧 Modifícalo
Modifica 1-2 líneas del primer worked example para:
- En vez de sumar `revenue` por `region`, calcula el promedio por `vendedor`.
Describe qué debe lograr el cambio (no cómo hacerlo): el archivo `summary.csv` debe contener una fila por vendedor con su `revenue` promedio.

🎯 Mini-reto
Crea un script/notebook que:
- lea "ventas.csv",
- filtre solo ventas del año 2025,
- calcule `revenue`,
- genere un CSV con `region`, `mes`, `revenue_total` (suma por región y por mes),
- y guarde un gráfico de líneas de `revenue` por mes para la región con mayor total.

Pista: usa `pd.to_datetime` para extraer el mes y `groupby(["region","mes"])`.

📌 En resumen
- Un pipeline es una secuencia reproducible: cargar → limpiar → transformar → agregar → exportar.  
- Usa `to_csv` para compartir resultados; usa matplotlib/seaborn para guardar gráficos reproducibles.  
- Automatiza pasos que hoy haces manual en Excel para obtener `summary.csv` y una gráfica lista para la reunión.