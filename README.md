# Proyecto 1 — Obtención y limpieza de datos

Establecimientos educativos de nivel diversificado de Guatemala, obtenidos del
portal del MINEDUC. El repo cubre todo el proceso: descarga, diagnóstico de los
datos crudos, perfilado de calidad, plan de limpieza, limpieza aplicada y
generación del conjunto limpio con su informe de calidad.

- **Fuente:** https://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/
- **Extracción:** 2026-07-16
- **Datos crudos:** 11,867 registros, 17 variables, 23 departamentos (nivel diversificado)
- **Datos limpios:** 11,867 registros, 18 variables (`output/establecimientos_limpios.csv`)
- **Integrantes:** Diego López, Nelson Escalante, Roberto Nájera (Data Science, sección 20)

## Requisitos

```
pip install -r requirements.txt
```

## Estructura

El código vive en `src/` (paquete) y las pruebas en `tests/`. Los scripts se
corren como módulos con `python -m src.<módulo>` **desde la raíz del repositorio**.

| Archivo                 | Qué hace                                                                             |
| ----------------------- | ------------------------------------------------------------------------------------- |
| `src/downloader.py`   | Descarga los 23 departamentos del portal y guarda los CSV crudos                      |
| `src/eda.py`          | Diagnóstico del dataset: filas, tipos, faltantes, únicos, duplicados                |
| `src/catalogo.py`     | Baja el catálogo oficial de municipios por departamento                              |
| `src/profiler.py`     | Perfilado de calidad: detecta problemas de texto y categorías                        |
| `src/detectores.py`   | Funciones de detección usadas por el profiler                                        |
| `src/limpieza.py`     | Funciones de limpieza + la estrategia (reglas por variable)                           |
| `src/consistencia.py` | Verifica consistencia entre variables (CODIGO↔DEPARTAMENTO, MUNICIPIO↔DEPARTAMENTO) |
| `src/dedup.py`        | Detecta duplicados exactos y parciales (RapidFuzz); no elimina, marca                 |
| `src/estrategia.py`   | Prueba las reglas sobre una muestra y mide cuánto cambiarían                        |
| `src/calidad.py`      | Genera métricas antes/después, registro de transformaciones e informe               |
| `src/main.py`         | Orquesta el pipeline: aplica la limpieza y escribe el conjunto limpio                 |
| `src/codebook_pdf.py` | Convierte el libro de códigos a PDF                                                  |
| `src/common.py`       | Utilidades compartidas (faltantes, clave canónica)                                   |

Carpetas de salida:

| Carpeta             | Contenido                                                                    |
| ------------------- | ---------------------------------------------------------------------------- |
| `raw_files/`      | CSV crudos por departamento + consolidado + metadata                         |
| `summary_tables/` | Tablas del diagnóstico (una por variable + resumen general)                 |
| `profiling/`      | Hallazgos, prioridad, catálogo, code book y estrategia                      |
| `output/`         | Conjunto limpio, informe de calidad, métricas, transformaciones, duplicados |

Documentos:

- `plan_limpieza.md` — plan de limpieza por variable (problema, regla, riesgo)
- `profiling/codebook.md` — libro de códigos (definición, dominio, tratamiento por variable)
- `output/informe_calidad.md` — comparación antes/después de la limpieza

## Cómo correr

Todos los comandos se ejecutan **desde la raíz del repositorio** (el cwd debe ser
la raíz para que las rutas a `raw_files/`, `output/`, etc. resuelvan bien). Cada
paso usa las salidas del anterior.

```
python -m src.downloader     # -> raw_files/
python -m src.eda            # -> summary_tables/
python -m src.catalogo       # -> profiling/catalogo_municipios.csv
python -m src.profiler       # -> profiling/ (hallazgos, prioridad, code book)
python -m src.estrategia     # -> profiling/ (estrategia y evidencia en muestra)
python -m src.main           # -> output/ (conjunto limpio + informe de calidad)
python -m src.codebook_pdf   # -> profiling/codebook.pdf
```

`src/downloader.py` y `src/catalogo.py` necesitan internet (consultan el portal).
El resto trabaja sobre los CSV ya descargados.

## Pruebas

```
pytest
```

Incluye pruebas de las funciones (detección, limpieza, dedup, consistencia) y
validación del conjunto limpio ya generado (`tests/test_limpio.py`).

## Entregables

Material a entregar (según la guía del proyecto):

| Entregable                                  | Ubicación                              |
| ------------------------------------------- | --------------------------------------- |
| Código (carga → limpieza)                 | `src/` (todos los módulos)           |
| Repositorio con código + datos + code book | este repo                               |
| Libro de códigos (markdown)                | `profiling/codebook.md`               |
| Libro de códigos (PDF)                     | `profiling/codebook.pdf`              |
| CSV con los datos limpios                   | `output/establecimientos_limpios.csv` |

Dónde está la evidencia de cada criterio de evaluación:

| Criterio (pts)                                 | Dónde                                                                                                                                |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Obtención y unión (5)                        | `src/downloader.py` → `raw_files/`                                                                                               |
| Diagnóstico de datos crudos (15)              | `src/eda.py`, `src/profiler.py` → `summary_tables/`, `profiling/hallazgos.csv`                                               |
| Plan de limpieza (10)                          | `plan_limpieza.md`, `profiling/estrategia_limpieza.csv`                                                                           |
| Limpieza + duplicados exactos y parciales (30) | `src/limpieza.py`, `src/dedup.py`, `src/main.py` → `output/establecimientos_limpios.csv`, `output/posibles_duplicados.csv` |
| Pruebas de calidad (10)                        | `tests/` (incl. `tests/test_limpio.py` sobre el conjunto limpio)                                                                  |
| Mejora antes/después (10)                     | `output/informe_calidad.md`, `output/metricas.csv`, `output/transformaciones.csv`                                               |
| Libro de códigos (10)                         | `profiling/codebook.md`, `profiling/codebook.pdf`                                                                                 |
| Generación del conjunto limpio (10)           | `output/establecimientos_limpios.csv`                                                                                               |
