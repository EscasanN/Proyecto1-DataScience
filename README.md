# Proyecto 1 — Obtención y limpieza de datos

Establecimientos educativos de nivel diversificado de Guatemala, obtenidos del
portal del MINEDUC. El repo cubre la descarga, el diagnóstico de los datos
crudos, el perfilado de calidad y el plan de limpieza.

- **Fuente:** https://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/
- **Extracción:** 2026-07-16
- **Datos crudos:** 11,867 registros, 17 variables, 23 departamentos (nivel diversificado)

## Requisitos

```
pip install -r requirements.txt
```

## Estructura

| Archivo           | Qué hace                                                              |
| ----------------- | ---------------------------------------------------------------------- |
| `downloader.py` | Descarga los 23 departamentos del portal y guarda los CSV crudos       |
| `eda.py`        | Diagnóstico del dataset: filas, tipos, faltantes, únicos, duplicados |
| `catalogo.py`   | Baja el catálogo oficial de municipios por departamento               |
| `profiler.py`   | Perfilado de calidad: detecta problemas de texto y categorías         |
| `detectores.py` | Funciones de detección usadas por el profiler                         |
| `limpieza.py`   | Funciones de limpieza + la estrategia (reglas por variable)            |
| `estrategia.py` | Prueba las reglas sobre una muestra y mide cuánto cambiarían         |
| `common.py`     | Utilidades compartidas (faltantes, clave canónica)                    |

Carpetas de salida:

| Carpeta             | Contenido                                                    |
| ------------------- | ------------------------------------------------------------ |
| `raw_files/`      | CSV crudos por departamento + consolidado + metadata         |
| `summary_tables/` | Tablas del diagnóstico (una por variable + resumen general) |
| `profiling/`      | Hallazgos, prioridad, catálogo, code book y estrategia      |

Documentos:

- `plan_limpieza.md` — plan de limpieza por variable (problema, regla, riesgo)
- `profiling/codebook.md` — dominio esperado y problemas por variable

## Cómo correr

Los scripts se corren en este orden. Cada uno usa las salidas del anterior.

```
python downloader.py     # -> raw_files/
python eda.py            # -> summary_tables/
python catalogo.py       # -> profiling/catalogo_municipios.csv
python profiler.py       # -> profiling/ (hallazgos, prioridad, code book)
python estrategia.py     # -> profiling/ (estrategia y evidencia en muestra)
```

`downloader.py` y `catalogo.py` necesitan internet (consultan el portal).
El resto trabaja sobre los CSV ya descargados.

## Pruebas

```
pytest
```

## Estado

Hecho: descarga, diagnóstico, perfilado y plan de limpieza.

Pendiente: aplicar la limpieza y generar el CSV limpio final
(`main.py` + `establecimientos_limpios.csv`), deduplicación de registros e
informe de calidad antes/después.
