# Plan de limpieza

Actividad 4 de la guía. Para cada variable: problema detectado, regla que se
usará para corregirlo, por qué se espera que funcione y riesgo asociado.

- **Fuente de los datos:** portal MINEDUC (`raw_files/datos_crudos_completos.csv`), 11,867 registros, 17 variables, nivel diversificado, 23 departamentos. Extraído 2026-07-16.
- **Conteos:** casos reales sobre el total, tomados de `profiling/hallazgos.csv` (diagnóstico de Persona 2). Los faltantes salen de `summary_tables/resumen_general.csv`.
- **Alcance:** este documento es el *plan*, no la limpieza aplicada. Las funciones están en `limpieza.py`; el pipeline que las aplica y genera el CSV limpio es la actividad 5 (Persona 3).

## Principios

1. **No destruir ortografía.** El enunciado exige que los nombres queden bien escritos para quien use los datos después. Se corrige la *forma* (espacios, invisibles), no la *ortografía correcta* de nombres propios.
2. **No inventar valores.** Si una regla de formato no puede corregir con certeza (código o teléfono inválido), se deja el original y se marca para revisión manual, en vez de forzar un valor que parezca válido.
3. **No autocorregir lo ambiguo.** Fuera de catálogo y posibles typos entre establecimientos van a revisión manual, no a corrección automática.

---

## 1. Reglas de forma (transversales)

Aplican a las variables de texto. Se documentan una vez porque el problema y la regla son los mismos; cambia el volumen por variable.

### 1.1 Caracteres invisibles
- **Problema:** el portal manda `\xa0` (espacio duro) y otros invisibles (tabs, saltos). No se ven pero rompen comparaciones y agrupaciones.
- **Casos:** DIRECTOR 1,732 · TELEFONO 946 · DISTRITO 532 · DIRECCION 76 · ESTABLECIMIENTO 5 · SUPERVISOR 4.
- **Regla:** `quitar_invisibles` — reemplazar cada invisible por un espacio normal (no borrarlo, para no pegar `FOO\xa0BAR` en `FOOBAR`).
- **Por qué funciona:** unifica la representación; dos `COBAN` con y sin `\xa0` pasan a ser el mismo valor.
- **Riesgo:** bajo. Al reemplazar por espacio (no borrar) no se unen palabras separadas.
- **Nota de orden:** cuando el `\xa0` es la celda completa, es un faltante (ver §4), no texto. Por eso `normalizar_faltantes` debe correr junto con esta regla.

### 1.2 Espacios sobrantes
- **Problema:** espacios al inicio/final y espacios múltiples internos.
- **Casos (múltiples internos):** ESTABLECIMIENTO 1,395 · DIRECTOR 868 · DIRECCION 485 · SUPERVISOR 102 · TELEFONO 8. **(borde):** DIRECTOR 241 · SUPERVISOR 31.
- **Regla:** `normalizar_espacios` — colapsar espacios múltiples a uno y hacer strip de bordes.
- **Por qué funciona:** `COBAN ` y `COBAN` dejan de contar como valores distintos.
- **Riesgo:** mínimo; un espacio interno doble casi nunca es intencional en este dataset.

### 1.3 Puntuación sobrante en los bordes
- **Problema:** puntuación suelta al inicio o final (`01-`, `ZONA 3.`).
- **Casos:** ESTABLECIMIENTO 397 · DIRECCION 121 · DISTRITO 70 · SUPERVISOR 25 · DIRECTOR 7.
- **Regla:** `quitar_puntuacion_borde` — quitar puntuación de borde **respetando** paréntesis y comillas legítimas.
- **Por qué funciona:** elimina restos sin valor sin tocar `DIARIO(REGULAR)` ni `COLEGIO "LA INMACULADA"`.
- **Riesgo:** depende de resolver antes los delimitadores desbalanceados (§1.5); si no, puede quedar un paréntesis abierto sin cierre.

### 1.4 Mayúsculas inconsistentes
- **Problema:** minúsculas sueltas en un dataset que viene casi todo en mayúsculas.
- **Casos:** DIRECCION 10 · TELEFONO 1.
- **Regla:** `normalizar_mayusculas` — `str.upper()`.
- **Por qué funciona:** unifica bajo la convención dominante; `guatemala` y `GUATEMALA` dejan de ser categorías distintas.
- **Riesgo:** en texto libre (nombres propios) es más alto que en categóricas: no cambia letras, pero pierde cualquier estilización intencional de mayúsculas (poco probable aquí).

### 1.5 Caracteres sospechosos / delimitadores sin cerrar
- **Problema:** mojibake y acentos inválidos en español (`È`, `Ì`, `Ò`); comillas o paréntesis abiertos sin cerrar.
- **Casos (sospechosos):** DIRECTOR 15 · ESTABLECIMIENTO 14 · SUPERVISOR 4. **(sin cerrar):** ESTABLECIMIENTO 17 · DIRECCION 1 · DIRECTOR 1.
- **Regla:** **revisión manual.** No se autocorrige: `HÈCTOR` probablemente es `HÉCTOR`, pero corregir a ciegas es arriesgado en nombres propios.
- **Riesgo:** corregir mal un nombre. Por eso se listan para revisar, no se tocan.

---

## 2. Reglas de formato específicas

### 2.1 CODIGO
- **Problema:** ninguno detectado — 100% cumple `dd-dd-dddd-dd`. Solo se normaliza espacio de borde por precaución.
- **Regla:** `normalizar_codigo` — validar contra el patrón; si no calza, dejar el original.
- **Por qué funciona:** CODIGO es la llave del establecimiento; no se inventan valores.
- **Riesgo:** forzar un formato sin verificar podría mezclar dos establecimientos. Los que no calcen van a revisión manual.

### 2.2 TELEFONO
- **Problema:** 251 fuera de formato (no son 8 dígitos) y 183 con más de un número en la celda (`78208583-78209143`).
- **Regla:** `normalizar_telefono` (dejar solo dígitos; si no quedan 8, no forzar) + `separar_telefono_multivalor` (primer número como principal, resto a una columna derivada `TELEFONO_2`).
- **Por qué funciona:** quita separadores sin descartar información; el segundo número se conserva aparte.
- **Riesgo:** el "primer número" es una convención arbitraria y podría no ser el principal; un teléfono con letra extra podría quedar en 8 dígitos "válidos" por coincidencia. `TELEFONO_2` debe crearse para no perder el segundo número.

---

## 3. Consistencia de categorías (duplicados por escritura)

- **Problema:** el mismo valor escrito de varias formas (mayúsculas, tildes o espacios distintos).
- **Casos:** ESTABLECIMIENTO 2,130 · SUPERVISOR 1,198 · DIRECCION 853 · DIRECTOR 244 · TELEFONO 3.
- **Regla:** `unificar_categoria` con el mapa de `mapa_categorias_dominantes` — agrupa variantes por clave canónica y las lleva a la forma más frecuente. **Solo se aplica a categóricas y llaves geográficas** (DEPARTAMENTO, MUNICIPIO, NIVEL, SECTOR, AREA, STATUS, MODALIDAD, JORNADA, PLAN, DEPARTAMENTAL).
- **Por qué funciona:** `GUATEMALA` y `Guatemala` se cuentan como un solo valor.
- **Riesgo ALTO en texto libre:** en ESTABLECIMIENTO/SUPERVISOR/DIRECCION/DIRECTOR **no se aplica automáticamente**. La variante más frecuente puede ser la mal escrita (ej. `EDUCACION` sin tilde supera a `EDUCACIÓN`), y unificar a la mayoría destruiría la ortografía correcta — justo lo que el enunciado prohíbe. Estas van a revisión manual.
- **Riesgo adicional:** el mapa se recalcula sobre el dataset completo antes de aplicar; la variante dominante puede cambiar respecto a la muestra.

---

## 4. Valores faltantes

- **Problema:** los faltantes vienen representados de formas distintas: celda vacía, `\xa0`, y centinelas de texto (`N/A`, `SIN DATO`, `---`, `.`, `0`). Centinelas detectados: DIRECTOR 414 · DIRECCION 13 · SUPERVISOR 3.
- **Faltantes por vacío/`\xa0`:** DIRECTOR 1,732 (14.6%) · TELEFONO 946 (7.97%) · SUPERVISOR 535 (4.51%) · DISTRITO 532 (4.48%) · DIRECCION 76 (0.64%) · ESTABLECIMIENTO 5 (0.04%).
- **Regla:** `normalizar_faltantes` — unificar todo bajo un solo `NA`.
- **Por qué funciona:** las estadísticas de faltantes y los conteos de únicos dejan de repartirse entre `''`, `'\xa0'` y `'N/A'` como si fueran categorías.
- **Riesgo:** `0` está en la lista de centinelas, pero podría ser un valor real en una variable numérica distinta de TELEFONO/CODIGO. Revisar antes de aplicar fuera de esas dos.

---

## 5. Revisión manual (no se automatiza)

| Variable | Problema | Casos | Por qué no se corrige solo |
|---|---|---|---|
| DEPARTAMENTO | Fuera del catálogo oficial | 0 | Sin casos hoy; si aparecen, mapear a mano contra el catálogo (23 valores) |
| MUNICIPIO | Fuera del catálogo de su departamento | 0 | Sin casos hoy; hay homónimos entre departamentos, un mapeo por similitud podría reasignar al equivocado |
| ESTABLECIMIENTO | Posibles typos entre nombres (RapidFuzz) | 218 pares | Fusionar automáticamente es el mayor riesgo del dataset: dos sedes distintas pueden tener nombres casi iguales |

---

## 6. Prioridad de limpieza

Orden sugerido de trabajo (de `profiling/prioridad.csv`, score = criticidad × casos):

| # | Variable | Casos | Foco principal |
|---|---|---|---|
| 1 | ESTABLECIMIENTO | 4,176 | Categorías duplicadas, espacios, typos (manual) |
| 2 | DIRECTOR | 3,522 | Invisibles/faltantes, centinelas, espacios |
| 3 | DIRECCION | 1,559 | Categorías duplicadas, espacios |
| 4 | TELEFONO | 1,392 | Faltantes, formato, multivalor |
| 5 | SUPERVISOR | 1,367 | Categorías duplicadas, espacios |
| 6 | DISTRITO | 602 | Invisibles/faltantes, puntuación |

CODIGO, MUNICIPIO, DEPARTAMENTO y las 8 categóricas restantes salieron sin problemas en el diagnóstico.

---

## Pendientes fuera de este plan

Requisitos del PDF que las reglas anteriores **no** cubren y que corresponden a la limpieza aplicada (actividad 5, Persona 3):

- **Duplicados de registros:** exactos (0 hoy) y **parciales por similitud** — no hay regla; hay que implementarlo.
- **Consistencia entre variables (5h):** ej. que MUNICIPIO pertenezca a su DEPARTAMENTO. No hay regla todavía.
- **Variables derivadas (5i):** al menos `TELEFONO_2` (segundo número). Documentar en el code book al crearse.
