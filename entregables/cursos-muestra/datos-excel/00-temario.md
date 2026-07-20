# Curso de muestra: datos-excel

Generado con prompts v2.

**Perfil del estudiante:**

- Nivel: Sé algo básico (variables, condicionales)
- Experiencia: manejo Excel avanzado en mi trabajo (fórmulas, tablas dinámicas)
- Objetivo: Ciencia de datos / análisis
- Lenguaje: python

---

## Temario

1. **De Excel a Python: tipos y expresiones como fórmulas** — Será capaz de traducir fórmulas de Excel a expresiones Python: distinguir números, texto y fechas, convertir tipos cuando haga falta y devolver resultados listos para análisis. Reutiliza variables y condicionales como repaso. Quick win: calcular un promedio y concatenar texto similar a una celda con fórmula. (_conceptos: tipos de datos (int/float/str/datetime), operadores y expresiones, conversión de tipos (casting)_)
2. **Cargar y explorar datos: del archivo CSV a DataFrame (hoja → hoja de cálculo en Python)** — Sabrá leer un CSV en un DataFrame (equivalente a una hoja), inspeccionarlo y obtener estadísticas básicas (como 'Resumen rápido' en Excel). Reutiliza tipos y expresiones para interpretar columnas. Quick win: cargar archivo.csv y mostrar las primeras 5 filas y describe(). (_conceptos: DataFrame (pandas), pd.read_csv, head(), info(), describe(), columnas y filas_)
3. **Seleccionar y filtrar: vistas y columnas calculadas (como filtros y fórmulas)** — Podrá seleccionar columnas, filtrar filas con condiciones (filtros de Excel) y crear columnas calculadas que derivan de otras (como una fórmula nueva). Reutiliza lectura de CSV y manejo de tipos. Quick win: extraer ventas > X y añadir una columna de margen calculado. (_conceptos: indexación por columnas, máscaras booleanas (filtrado), asignar nuevas columnas, operaciones columna a columna_)
4. **Agrupar y resumir: reproducir tablas dinámicas con groupby** — Aprenderá a agrupar por una o varias columnas y calcular agregados (suma, media, conteo), equivalente a tablas dinámicas. Reutiliza indexación y columnas calculadas. Quick win: obtener resumen de ventas por categoría con conteo, suma y media. (_conceptos: groupby, aggregate/agg, pivot_table, ordenar resultados (sort_values)_)
5. **Funciones para automatizar cálculos: de fórmula puntual a herramienta reutilizable** — Podrá encapsular lógica de cálculo en funciones con parámetros y aplicarlas al DataFrame para evitar repetir pasos (como crear una macro simple). Reutiliza agrupación y columnas calculadas. Quick win: escribir una función que normalice una columna y aplicarla al conjunto de datos. (_conceptos: def / return, parámetros y valores por defecto, aplicar funciones a columnas (apply)_)
6. **Bucles vs vectorización: elegir la forma más rápida y legible** — Entenderá cuándo usar bucles, comprehensions o operaciones vectorizadas (pandas/numpy) y cómo medir su rendimiento; aplicará la mejor opción a tareas de transformación. Reutiliza funciones y operaciones columna a columna. Quick win: crear una columna 'flag' por condición usando vectorización y comparar tiempo con un for. (_conceptos: for loops, list comprehensions, operaciones vectorizadas (pandas/numpy), apply vs map_)
7. **Mini proyecto: pipeline reproducible — del CSV al insight y salida final** — Integrará todo en un pipeline reproducible (carga, limpieza, transformación, agregación y exportación) y generará una salida utilizable para análisis o presentación. Reutiliza groupby, funciones y vectorización. Quick win: ejecutar un script/notebook que produce summary.csv y una gráfica simple lista para mostrar en una reunión. (_conceptos: pipeline reproducible (secuencia de pasos), exportar resultados (to_csv), visualización básica (matplotlib/seaborn)_)