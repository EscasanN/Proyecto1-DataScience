# pipeline principal del proyecto.
#
# Ejecuta de forma reproducible todas las etapas de limpieza
# y genera los entregables finales solicitados por la guía.
#
# Flujo:
#
#   datos crudos
#          ↓
#   aplicar limpieza
#          ↓
#   validar consistencia
#          ↓
#   detectar duplicados
#          ↓
#   generar métricas
#          ↓
#   exportar resultados

from pathlib import Path

import pandas as pd

from src import calidad
from src import consistencia
from src import dedup
from src import limpieza

from src.catalogo import obtener as obtener_catalogo


# ---------------------------------------------------------------
# configuración
# ---------------------------------------------------------------

INPUT_FILE = Path("raw_files") / "datos_crudos_completos.csv"

OUTPUT_DIR = Path("output")

ARCHIVO_LIMPIO = "establecimientos_limpios.csv"
ARCHIVO_METRICAS = "metricas.csv"
ARCHIVO_TRANSFORMACIONES = "transformaciones.csv"
ARCHIVO_INFORME = "informe_calidad.md"
ARCHIVO_INCONSISTENCIAS = "inconsistencias.csv"
ARCHIVO_DUPLICADOS = "posibles_duplicados.csv"


# ---------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------

def cargar_datos():
    """
    Carga el conjunto de datos crudo.

    Todo el proyecto trabaja inicialmente
    con texto para no perder ceros iniciales
    ni formatos originales.
    """

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró {INPUT_FILE}"
        )

    return pd.read_csv(
        INPUT_FILE,
        dtype=str,
        keep_default_na=False,
    )


def preparar_salida():
    """
    Crea la carpeta de salida
    si todavía no existe.
    """

    OUTPUT_DIR.mkdir(
        exist_ok=True
    )


def guardar_csv(df, nombre):
    """
    Guarda un DataFrame en output/.
    """

    df.to_csv(
        OUTPUT_DIR / nombre,
        index=False,
        encoding="utf-8-sig",
    )


def guardar_markdown(texto, nombre):
    """
    Guarda un archivo Markdown.
    """

    (OUTPUT_DIR / nombre).write_text(
        texto,
        encoding="utf-8",
    )

# ---------------------------------------------------------------
# pipeline
# ---------------------------------------------------------------

def ejecutar_pipeline():
    """
    Ejecuta el pipeline completo del proyecto.

    Devuelve todos los objetos necesarios
    para generar los archivos finales.
    """

    print("=" * 70)
    print("CARGANDO DATOS")
    print("=" * 70)

    df_original = cargar_datos()

    print(f"Registros: {len(df_original):,}")
    print(f"Variables: {len(df_original.columns)}")

    print("\nAplicando limpieza...")

    df_limpio, registro_transformaciones = (
        limpieza.aplicar_limpieza(df_original)
    )

    print(
        f"Transformaciones aplicadas: "
        f"{len(registro_transformaciones)}"
    )

    # -----------------------------------------------------------
    # consistencia
    # -----------------------------------------------------------

    print("\nValidando consistencia...")

    try:
        catalogo = obtener_catalogo()
    except Exception as e:
        raise RuntimeError(
            "No fue posible obtener el catálogo de municipios. "
            "Ejecute 'python -m src.catalogo' previamente o conecte a internet."
        ) from e

    inconsistencias = consistencia.revisar_consistencia(
        df_limpio,
        catalogo,
    )

    print(
        f"Inconsistencias encontradas: "
        f"{len(inconsistencias)}"
    )

    # -----------------------------------------------------------
    # duplicados
    # -----------------------------------------------------------

    print("\nBuscando duplicados...")

    duplicados = dedup.duplicados_parciales(
        df_limpio
    )

    print(
        f"Posibles duplicados: "
        f"{len(duplicados)}"
    )

    # -----------------------------------------------------------
    # calidad
    # -----------------------------------------------------------

    print("\nGenerando métricas...")

    metricas = calidad.generar_metricas(
        df_original,
        df_limpio,
    )

    transformaciones = (
        calidad.generar_transformaciones(
            registro_transformaciones
        )
    )

    informe = calidad.generar_informe_md(
        metricas,
        transformaciones,
    )

    return {

        "dataset": df_limpio,

        "metricas": metricas,

        "transformaciones": transformaciones,

        "informe": informe,

        "duplicados": duplicados,

        "inconsistencias": inconsistencias,

    }

# ---------------------------------------------------------------
# main
# ---------------------------------------------------------------

def main():

    preparar_salida()

    resultados = ejecutar_pipeline()

    print("\nExportando resultados...")

    guardar_csv(
        resultados["dataset"],
        ARCHIVO_LIMPIO,
    )

    guardar_csv(
        resultados["metricas"],
        ARCHIVO_METRICAS,
    )

    guardar_csv(
        resultados["transformaciones"],
        ARCHIVO_TRANSFORMACIONES,
    )

    guardar_csv(
        resultados["duplicados"],
        ARCHIVO_DUPLICADOS,
    )

    guardar_csv(
        resultados["inconsistencias"],
        ARCHIVO_INCONSISTENCIAS,
    )

    guardar_markdown(
        resultados["informe"],
        ARCHIVO_INFORME,
    )

    print("\n" + "=" * 70)
    print("PIPELINE FINALIZADO")
    print("=" * 70)

    print(
        f"CSV limpio             : "
        f"{OUTPUT_DIR / ARCHIVO_LIMPIO}"
    )

    print(
        f"Métricas               : "
        f"{OUTPUT_DIR / ARCHIVO_METRICAS}"
    )

    print(
        f"Transformaciones       : "
        f"{OUTPUT_DIR / ARCHIVO_TRANSFORMACIONES}"
    )

    print(
        f"Informe                : "
        f"{OUTPUT_DIR / ARCHIVO_INFORME}"
    )

    print(
        f"Duplicados             : "
        f"{OUTPUT_DIR / ARCHIVO_DUPLICADOS}"
    )

    print(
        f"Inconsistencias        : "
        f"{OUTPUT_DIR / ARCHIVO_INCONSISTENCIAS}"
    )

    print("\nProceso completado correctamente.")


if __name__ == "__main__":
    main()