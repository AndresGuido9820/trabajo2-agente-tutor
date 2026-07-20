# Bucles vs vectorización: elegir la forma más rápida y legible

Esta unidad te ayuda a decidir cómo transformar columnas en datos reales (como en tus hojas de Excel) de la forma más clara y rápida. Aprenderás a elegir entre escribir un bucle, usar una list comprehension o aprovechar operaciones vectorizadas en pandas/numpy. Resultado práctico: crearás una columna `flag` por condición y compararás tiempos —útil para preparar datos antes de análisis o modelos.

🔮 Predice
```python
import pandas as pd
df = pd.DataFrame({'ventas': [100, 200, 150, 300]})
resultado = [v > 180 for v in df['ventas']]
df['flag'] = resultado
print(df)
```
¿Qué crees que imprime esto?

---

Sección: For loops (bucles for)
Respuesta a la predicción: ya verás la respuesta completa en la sección de comprehensions. Aquí empezamos por bucles.

Explicación (analogía Excel): Un for es como recorrer fila por fila en Excel y escribir fórmula manualmente en cada celda. Claro y controlable, pero lento si lo haces para miles de filas.

Worked example (for sobre índices)
```python
# 1. crear datos de ejemplo
import pandas as pd
df = pd.DataFrame({'ventas': [100, 200, 150, 300]})

# 2. preparar lista vacía para las flags
flags = []                    # 1. acumular resultados

# 3. recorrer filas y decidir
for i in range(len(df)):      # 2. iterar por índices
    valor = df['ventas'][i]   # 3. leer valor de la fila i
    flags.append(valor > 180) # 4. evaluar condición y guardar

# 4. asignar la columna al DataFrame
df['flag_for'] = flags        # 5. guardar resultado en la tabla
print(df)
```
Estado del programa (después de cada iteración del for):
- i=0: valor=100, flags=[False]
- i=1: valor=200, flags=[False, True]
- i=2: valor=150, flags=[False, True, False]
- i=3: valor=300, flags=[False, True, False, True]

Sección: List comprehensions
Explicación (analogía Excel): Es como escribir una fórmula una vez y arrastrarla en Excel, pero expresado en una sola línea Python. Más legible que un for para transformaciones simples.

Respuesta a la predicción (antes planteada): el código crea una lista de booleanos indicando si cada venta es mayor que 180 y la asigna a la columna `flag`. Imprime:
ventas | flag
100    | False
200    | True
150    | False
300    | True

Worked example (comprehension)
```python
# 1. crear datos de ejemplo
import pandas as pd
df = pd.DataFrame({'ventas': [100, 200, 150, 300]})

# 2. crear la lista con comprehension
flags_comp = [v > 180 for v in df['ventas']]  # 1. crear lista de condición

# 3. guardar en la tabla
df['flag_comp'] = flags_comp                   # 2. asignar columna
print(df)
```
Estado durante la comprehension (evaluación secuencial): produce [False, True, False, True].

Sección: Operaciones vectorizadas (pandas / numpy)
Explicación (analogía Excel): Es como usar una fórmula de Excel que trabaja en toda la columna interna del motor; pandas lo hace en C/NumPy y es mucho más rápido para grandes volúmenes.

Worked example + comparación de tiempo (pequeña muestra)
```python
# 1. preparar un DataFrame grande
import pandas as pd, numpy as np, time
df_big = pd.DataFrame({'ventas': np.random.randint(50, 500, size=100000)})

# 2. medir tiempo: bucle for
t0 = time.perf_counter()
flags = []
for i in range(len(df_big)):
    flags.append(df_big['ventas'].iloc[i] > 180)
df_big['flag_for'] = flags
t_for = time.perf_counter() - t0

# 3. medir tiempo: vectorizado
t0 = time.perf_counter()
df_big['flag_vec'] = df_big['ventas'] > 180
t_vec = time.perf_counter() - t0

print('for:', t_for, 'vectorizado:', t_vec)
```
Típicamente verás que `t_vec` << `t_for` para grandes tablas.

Sección: apply vs map
Explicación (definición): apply aplica una función fila/elemento a una Serie o DataFrame; map transforma valores de una Serie según una función o un diccionario. En Excel, apply ≈ arrastrar una fórmula que usa lógica compleja; map ≈ sustituir categorías por etiquetas en una columna.

Worked example
```python
# 1. función para categorizar
def categoria(valor):
    return 'alta' if valor > 250 else 'baja'   # 1. definir regla

# 2. aplicar la función por elemento (más lento que vectorizar si posible)
df_big['categoria'] = df_big['ventas'].apply(categoria)  # 2. aplicar función
```

⚠️ Error típico (desmontajes rápidos)
- x = x + 1: no es una ecuación; evalúa la derecha y guarda en x. Ejemplo:
  x = 1; x = x + 1 -> ahora x vale 2.
- Asignación y vínculo permanente: a = b liga referencias. Ejemplo con listas:
  a = [1]; b = a; a[0]=9 -> b[0] será 9. (No confundir con escalares: y = 5; z = y -> cambiar y no cambia z).
- Confundir = con ==: `if x = 1:` es error; la comparación es `if x == 1:`.
- Definir función no la ejecuta: `def f(): ...` no corre f hasta que haces `f()`.

🔧 Modifícalo
Toma el worked example vectorizado y cambia:
- Umbral de 180 a 250.
- Guarda 1/0 en vez de True/False.
Logro esperado: columna `flag_vec` con 1 donde ventas>250 y 0 en otro caso.

🎯 Mini-reto (quick win conectado a tu meta)
Usa tu DataFrame real (el que cargas desde CSV). Crea una columna `flag` que marque filas donde la columna de interés supera la media de la columna. Hazlo con vectorización y con un for; mide ambos tiempos y reporta el factor de mejora (t_for / t_vec).
Pista: usa df['col'] > df['col'].mean() para la condición; time.perf_counter() para medir.

📌 En resumen
- Para transformaciones simples, usa operaciones vectorizadas en pandas/numpy: más legible y mucho más rápido en tablas grandes.
- Las list comprehensions son limpias y eficaces para listas o cuando la lógica no puede vectorizarse fácilmente.
- Mide siempre: profiler simple (time.perf_counter) te muestra si vale la pena reescribir a vectorizado.