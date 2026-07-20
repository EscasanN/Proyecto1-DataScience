# Libro de códigos

Establecimientos educativos de nivel diversificado de Guatemala.

| Metadato | Valor |
|---|---|
| Fuente | Portal MINEDUC — <https://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/> |
| Fecha de extracción | 2026-07-16 |
| Registros (crudo) | 11,867 |
| Variables (crudo) | 17 (+1 derivada, ver §3) |
| Nivel | DIVERSIFICADO (filtro de la descarga) |
| Cobertura | 23 departamentos |
| Registros (limpio) | 11,867 (sin cambio; no se eliminaron filas) |
| Variables (limpio) | 18 (17 + `TELEFONO_2`) |
| Versión del conjunto limpio | 1.0 — `output/establecimientos_limpios.csv` |
| Fecha de generación del limpio | 2026-07-20 |

Todas las variables se extraen como texto de una tabla HTML. El "tipo" indica
el tipo que le corresponde al dato, no el de almacenamiento.

---

## 1. Definición de variables

| Variable | Descripción | Tipo | Dominio / valores posibles |
|---|---|---|---|
| CODIGO | Código único del establecimiento | Identificador | Patrón `dd-dd-dddd-dd`; los 2 primeros dígitos son el departamento |
| DISTRITO | Código del distrito escolar | Identificador | Patrón `dd-ddd`; numeración propia, no codifica el departamento |
| DEPARTAMENTO | Departamento del establecimiento | Categórico | 23 valores del catálogo oficial (el portal separa CIUDAD CAPITAL de GUATEMALA) |
| MUNICIPIO | Municipio del establecimiento | Categórico | Catálogo oficial por departamento (`profiling/catalogo_municipios.csv`); válido solo dentro de su departamento |
| ESTABLECIMIENTO | Nombre del establecimiento | Texto libre | Nombre propio; conserva ortografía y tildes |
| DIRECCION | Dirección física | Texto libre | — |
| TELEFONO | Teléfono principal | Numérico | 8 dígitos (numeración nacional) |
| SUPERVISOR | Nombre del supervisor | Texto libre | Nombre de persona |
| DIRECTOR | Nombre del director | Texto libre | Nombre de persona |
| NIVEL | Nivel educativo | Categórico | DIVERSIFICADO |
| SECTOR | Sector administrativo | Categórico | PRIVADO, OFICIAL, COOPERATIVA, MUNICIPAL |
| AREA | Área geográfica | Categórico | URBANA, RURAL, SIN ESPECIFICAR |
| STATUS | Estado del establecimiento | Categórico | ABIERTA, CERRADA TEMPORALMENTE, CERRADA DEFINITIVAMENTE, TEMPORAL TITULOS, TEMPORAL NOMBRAMIENTO |
| MODALIDAD | Modalidad lingüística | Categórico | MONOLINGUE, BILINGUE |
| JORNADA | Jornada | Categórico | DOBLE, VESPERTINA, MATUTINA, SIN JORNADA, NOCTURNA, INTERMEDIA |
| PLAN | Plan de estudios | Categórico | DIARIO(REGULAR), FIN DE SEMANA, SEMIPRESENCIAL (y variantes), A DISTANCIA, VIRTUAL A DISTANCIA, SABATINO, DOMINICAL, MIXTO, IRREGULAR, INTERCALADO |
| DEPARTAMENTAL | Dirección departamental del MINEDUC | Categórico | 26 valores (GUATEMALA se divide en 4, QUICHÉ en 2) |

---

## 2. Calidad y tratamiento por variable

`Faltantes` sobre 11,867 (crudo). `Registros afectados` = filas que cambió la
limpieza aplicada por `main.py` (detalle en `output/transformaciones.csv`).

| Variable | Faltantes | Problemas detectados | Tratamiento aplicado | Registros afectados |
|---|---|---|---|---:|
| CODIGO | 0 | Ninguno | Validar patrón; sin cambios | 0 |
| DISTRITO | 532 (4.48%) | Invisibles, puntuación de borde | Normalizar faltantes | 532 |
| DEPARTAMENTO | 0 | Ninguno | Sin cambios; verificado contra CODIGO | 0 |
| MUNICIPIO | 0 | Ninguno | Sin cambios; verificado par con DEPARTAMENTO | 0 |
| ESTABLECIMIENTO | 5 (0.04%) | Categorías duplicadas (2130), espacios (1395), puntuación (397), typos (218) | Normalizar forma (espacios, puntuación). Ortografía/typos: **revisión manual** | 1,797 |
| DIRECCION | 76 (0.64%) | Categorías duplicadas (853), espacios (485), puntuación (121) | Normalizar forma + mayúsculas + faltantes | 705 |
| TELEFONO | 946 (7.97%) | Fuera de formato (251), multivalor (183) | Solo dígitos; 2º número → TELEFONO_2 (§3) | 1,089 |
| SUPERVISOR | 535 (4.51%) | Categorías duplicadas (1198), espacios (133) | Normalizar forma + faltantes | 700 |
| DIRECTOR | 1,732 (14.6%) | Centinelas (414), espacios (1109), categorías duplicadas (244) | Normalizar forma + faltantes; mojibake a revisión manual | 3,235 |
| NIVEL | 0 | Ninguno | Sin cambios | 0 |
| SECTOR | 0 | Ninguno | Sin cambios | 0 |
| AREA | 0 | Ninguno | Sin cambios | 0 |
| STATUS | 0 | Ninguno | Sin cambios | 0 |
| MODALIDAD | 0 | Ninguno | Sin cambios | 0 |
| JORNADA | 0 | Ninguno | Sin cambios | 0 |
| PLAN | 0 | Ninguno | Sin cambios | 0 |
| DEPARTAMENTAL | 0 | Ninguno | Sin cambios | 0 |

**Total de registros afectados: 8,058.** Ningún registro fue eliminado.
Detalle de faltantes en `summary_tables/resumen_general.csv`; problemas por
valor en `profiling/valores_problematicos.csv`; transformaciones en
`output/transformaciones.csv`.

---

## 3. Variables derivadas

| Variable | Origen | Descripción |
|---|---|---|
| TELEFONO_2 | TELEFONO | Segundo número, cuando la celda traía más de uno (183 casos). Se separa para no perder el dato. Vacío si solo había un número |

---

## 4. Reproducibilidad

El conjunto limpio se regenera con `python main.py`, que aplica las reglas de
`limpieza.py` sobre el crudo y escribe `output/establecimientos_limpios.csv`.
El informe de comparación antes/después está en `output/informe_calidad.md`.
