# Proyecto 1 — Obtención y limpieza de datos

Establecimientos educativos de nivel diversificado de Guatemala, obtenidos del
portal del MINEDUC. El repo cubre todo el proceso: descarga, diagnóstico de los
datos crudos, perfilado de calidad, plan de limpieza, limpieza aplicada y
generación del conjunto limpio con su informe de calidad.

- **Fuente:** https://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/
- **Extracción:** 2026-07-16
- **Datos crudos:** 11,867 registros, 17 variables, 23 departamentos (nivel diversificado)
- **Datos limpios:** 11,867 registros, 18 variables (`output/establecimientos_limpios.csv`)

## Requisitos

```
pip install -r requirements.txt
```

## Estructura

| Archivo | Qué hace |
|---|---|
| `downloader.py` | Descarga los 23 departamentos del portal y guarda los CSV crudos |
| `eda.py` | Diagnóstico del dataset: filas, tipos, faltantes, únicos, duplicados |
| `catalogo.py` | Baja el catálogo oficial de municipios por departamento |
| `profiler.py` | Perfilado de calidad: detecta problemas de texto y categorías |
| `detectores.py` | Funciones de detección usadas por el profiler |
| `limpieza.py` | Funciones de limpieza + la estrategia (reglas por variable) |
| `consistencia.py` | Verifica consistencia entre variables (CODIGO↔DEPARTAMENTO, MUNICIPIO↔DEPARTAMENTO) |
| `dedup.py` | Detecta duplicados exactos y parciales (RapidFuzz); no elimina, marca |
| `estrategia.py` | Prueba las reglas sobre una muestra y mide cuánto cambiarían |
| `calidad.py` | Genera métricas antes/después, registro de transformaciones e informe |
| `main.py` | Orquesta el pipeline: aplica la limpieza y escribe el conjunto limpio |
| `codebook_pdf.py` | Convierte el libro de códigos a PDF |
| `common.py` | Utilidades compartidas (faltantes, clave canónica) |

Carpetas de salida:

| Carpeta | Contenido |
|---|---|
| `raw_files/` | CSV crudos por departamento + consolidado + metadata |
| `summary_tables/` | Tablas del diagnóstico (una por variable + resumen general) |
| `profiling/` | Hallazgos, prioridad, catálogo, code book y estrategia |
| `output/` | Conjunto limpio, informe de calidad, métricas, transformaciones, duplicados |

Documentos:

- `plan_limpieza.md` — plan de limpieza por variable (problema, regla, riesgo)
- `profiling/codebook.md` — libro de códigos (definición, dominio, tratamiento por variable)
- `output/informe_calidad.md` — comparación antes/después de la limpieza

## Cómo correr

Los scripts se corren en este orden. Cada uno usa las salidas del anterior.

```
python downloader.py     # -> raw_files/
python eda.py            # -> summary_tables/
python catalogo.py       # -> profiling/catalogo_municipios.csv
python profiler.py       # -> profiling/ (hallazgos, prioridad, code book)
python estrategia.py     # -> profiling/ (estrategia y evidencia en muestra)
python main.py           # -> output/ (conjunto limpio + informe de calidad)
python codebook_pdf.py   # -> profiling/codebook.pdf
```

`downloader.py` y `catalogo.py` necesitan internet (consultan el portal).
El resto trabaja sobre los CSV ya descargados.

## Pruebas

```
pytest
```

Incluye pruebas de las funciones (detección, limpieza, dedup, consistencia) y
validación del conjunto limpio ya generado (`test_limpio.py`).

## Estado

Completo: descarga, diagnóstico, perfilado, plan, limpieza aplicada, dedup,
conjunto limpio, informe de calidad y libro de códigos.

Pendiente: exportar el libro de códigos a PDF.
