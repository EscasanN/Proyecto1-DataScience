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
| Versión del conjunto limpio | *(pendiente — la asigna la integración, Persona 3)* |

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

`Faltantes` sobre 11,867. `Tratamiento` = regla propuesta en `plan_limpieza.md`.
El tratamiento **aplicado** se confirma cuando la limpieza corra sobre el
dataset completo (Persona 3).

| Variable | Faltantes | Problemas detectados | Tratamiento propuesto |
|---|---|---|---|
| CODIGO | 0 | Ninguno | Validar patrón; sin cambios |
| DISTRITO | 532 (4.48%) | Invisibles, puntuación de borde | Quitar invisibles, normalizar espacios/puntuación |
| DEPARTAMENTO | 0 | Ninguno | Sin cambios; verificar contra CODIGO (consistencia) |
| MUNICIPIO | 0 | Ninguno | Sin cambios; verificar par con DEPARTAMENTO |
| ESTABLECIMIENTO | 5 (0.04%) | Categorías duplicadas (2130), espacios (1395), puntuación (397), typos (218), mojibake (14) | Forma: espacios/invisibles. Ortografía y typos: **revisión manual** (no destruir nombres) |
| DIRECCION | 76 (0.64%) | Categorías duplicadas (853), espacios (485), puntuación (121) | Normalizar forma |
| TELEFONO | 946 (7.97%) | Fuera de formato (251), multivalor (183) | Dejar solo dígitos; 2º número → TELEFONO_2 (§3) |
| SUPERVISOR | 535 (4.51%) | Categorías duplicadas (1198), espacios (133) | Normalizar forma |
| DIRECTOR | 1,732 (14.6%) | Centinelas (414), espacios (1109), categorías duplicadas (244) | Normalizar forma + faltantes; mojibake a revisión manual |
| NIVEL | 0 | Ninguno | Sin cambios |
| SECTOR | 0 | Ninguno | Sin cambios |
| AREA | 0 | Ninguno | Sin cambios |
| STATUS | 0 | Ninguno | Sin cambios |
| MODALIDAD | 0 | Ninguno | Sin cambios |
| JORNADA | 0 | Ninguno | Sin cambios |
| PLAN | 0 | Ninguno | Sin cambios |
| DEPARTAMENTAL | 0 | Ninguno | Sin cambios |

Detalle de faltantes en `summary_tables/resumen_general.csv`; de problemas por
valor en `profiling/valores_problematicos.csv`.

---

## 3. Variables derivadas

| Variable | Origen | Descripción |
|---|---|---|
| TELEFONO_2 | TELEFONO | Segundo número, cuando la celda traía más de uno (183 casos). Se separa para no perder el dato. Vacío si solo había un número |

---

## 4. Pendiente (depende del conjunto limpio)

- **Tratamiento aplicado:** arriba está el *propuesto*; el aplicado se documenta cuando la limpieza corra sobre el total.
- **Versión del conjunto limpio:** se asigna al generar `establecimientos_limpios.csv`.
