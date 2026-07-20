# Agrupar y resumir: reproducir tablas dinámicas con groupby

Esta unidad te enseña a crear resúmenes tipo tabla dinámica en Python para análisis de datos —lo mismo que haces en Excel con tablas dinámicas o SUMIFs— pero reproducible y programable. Aplicación directa a tu meta: calcular rápidamente ventas por categoría, promedios y conteos para informes repetibles.

🔮 Predice
```python
# ¿Qué crees que imprime esto?
import pandas as pd
ventas = pd.DataFrame({
    "categoria": ["A","A","B","B","A"],
    "importe": [100, 200, 150, 50, 300]
})
print(ventas.groupby("categoria")["importe"].sum())
```
¿Qué crees que hace / imprime?

---

## groupby — agrupar filas por una o más columnas
Respuesta a la predicción: imprime la suma del importe por cada categoría: A → 600, B → 200.  

Explicación: agrupar (groupby) es como seleccionar en Excel por categoría y luego aplicar una función en la columna importe (SUMA). groupby crea grupos lógicos; no modifica el DataFrame original hasta que aplicas una agregación.

Worked example (paso a paso)
```python
import pandas as pd
# 1. crear la tabla de ventas (simula tu hoja de cálculo pequeña)
ventas = pd.DataFrame({
    "categoria": ["A","A","B","B","A"],
    "importe": [100, 200, 150, 50, 300]
})
# Estado: ventas es un DataFrame con 5 filas y 2 columnas

# 2. agrupar y sumar importes por categoría
resumen_suma = ventas.groupby("categoria")["importe"].sum()
# Estado: resumen_suma es una Series:
# index: ["A","B"], values: [600, 200]

print(resumen_suma)
```
Máquina nocional (estado línea a línea):
- tras crear `ventas`: ventas[0] = {"categoria":"A","importe":100}, ... ventas tiene 5 registros.
- tras groupby+sum: se crean grupos {'A':[0,1,4], 'B':[2,3]}; se suman importes de cada grupo → Series con índices A y B y valores 600 y 200.

---

## aggregate / agg — calcular varios agregados a la vez
Definición: agg aplica una o varias funciones de resumen (por ejemplo, suma, media, conteo) a columnas de cada grupo. Es el equivalente a poner varios valores en la zona de valores de una tabla dinámica.

Worked example
```python
# 1. calcular conteo, suma y media por categoría
resumen_varios = ventas.groupby("categoria").agg(
    conteo = ("importe", "count"),
    suma = ("importe", "sum"),
    media = ("importe", "mean")
)
# Estado: resumen_varios es un DataFrame con índice categoria y columnas conteo, suma, media
print(resumen_varios)
```
Máquina nocional:
- grupos creados igual que antes;
- para cada grupo se evalúan count, sum, mean y se colocan en columnas separadas.

Analogía Excel: es como arrastrar la misma columna importe tres veces a "Valores" y elegir conteo/suma/promedio en cada una.

---

## pivot_table — tabla dinámica en una sola función
Definición: pivot_table crea una tabla resumen más cercana al objeto "tabla dinámica" de Excel: puedes pivotear filas/columnas y aplicar agregados.

Worked example
```python
# 1. crear pivot_table con categoría en filas y suma de importe
tabla_pivot = pd.pivot_table(ventas, index="categoria", values="importe", aggfunc="sum")
# Estado: tabla_pivot es similar al groupby + sum pero como DataFrame
print(tabla_pivot)
```
Nota: pivot_table permite múltiples índices y columnas; útil si quieres un resumen cruzado (ej. categoría x mes).

---

## sort_values — ordenar resultados
Definición: sort_values ordena un DataFrame/Series por una o varias columnas para ver los top/low.

Worked example
```python
# 1. ordenar el resumen por suma descendente
resumen_ordenado = resumen_varios.sort_values(by="suma", ascending=False)
print(resumen_ordenado)
# Estado: resumen_ordenado igual que resumen_varios pero con filas reordenadas
```

---

⚠️ Error típico
- Creer que una variable guarda varios valores o recuerda su historial. Ejemplo: asignar `resumen = ventas.groupby("categoria")` no guarda "historial". `resumen` es un objeto que describe cómo agrupar; hasta que aplicas `.sum()` no tienes los números. Si esperas ver resultados sin llamar a una función de agregado te confunde.
- Creer que la asignación crea vínculo permanente entre dos variables. Si haces `a = b` y luego modificas `b` (por ejemplo reasignas `b = ...`), `a` no cambia automáticamente. Si `a` y `b` apuntan al mismo DataFrame mutado in-place, sí reflejan cambios; pero reasignar es diferente. En general, vuelve explícito con asignaciones claras.

Ejemplo de confusión desmontada:
```python
x = ventas
x = x.groupby("categoria").sum()  # x ahora es el resumen, ventas queda igual
# reasignar x no modifica ventas
```

---

🔧 Modifícalo
Toma el worked example de agg y cambia 1-2 líneas para:
- Mostrar además la desviación estándar ("std") por categoría.
- O agrupar por dos columnas si añadimos una columna "mes" (no hace falta programarlo aquí; solo cambia la lista de índices).

Di qué debe lograr: añadir columna "std" o agrupar por ["categoria","mes"].

---

🎯 Mini-reto
Usa lo visto para generar un DataFrame llamado `resumen_final` con, por cada `categoria`: conteo de ventas, suma de `importe` y promedio de `importe`, ordenado por suma descendente. Pista: usa groupby + agg, luego sort_values.

---

📌 En resumen
- groupby agrupa filas; hace falta una función de agregado (sum, mean, count) para obtener números.
- agg permite calcular varios agregados a la vez y devuelve un DataFrame ordenado por columnas.
- pivot_table es la versión "tabla dinámica" con index/columns/values; usa sort_values para ordenar resultados.