# calidad del conjunto de datos (actividades 6 y 8).
#
# Este módulo calcula las métricas de calidad antes y después
# de la limpieza utilizando las funciones existentes del proyecto.
#
# Todas las funciones reciben dataframes y devuelven
# dataframes o valores simples.
#
# La escritura de metricas.csv, transformaciones.csv
# e informe_calidad.md corresponde a main.py.

import pandas as pd

from src.common import es_faltante
from src.detectores import analizar
from src.eda import tipo_inferido
from src.dedup import (
    cantidad_duplicados_exactos,
    cantidad_duplicados_parciales,
)


# ---------------------------------------------------------------
# constantes
# ---------------------------------------------------------------

# problemas que el PDF agrupa como "formato inconsistente"
PROBLEMAS_FORMATO = {
    "espacios al inicio o final",
    "espacios multiples internos",
    "caracteres invisibles",
    "mayusculas inconsistentes",
    "puntuacion sobrante al inicio o final",
    "comillas o parentesis sin cerrar",
    "telefono fuera de formato (no son 8 digitos)",
    "telefono con mas de un numero en la celda",
    "codigo fuera del patron dd-dd-dddd-dd",
}

PROBLEMA_CATEGORIA = (
    "categoria duplicada por escritura"
)

TIPOS_INCORRECTOS = {
    "entero almacenado como texto",
    "numerico almacenado como texto",
}


# ---------------------------------------------------------------
# utilidades privadas
# ---------------------------------------------------------------

def _es_valor_faltante(valor):
    """
    Unifica la definición de valor faltante.

    Funciona tanto para el dataset crudo
    (todo texto) como para el limpio
    (mezcla texto + pd.NA).
    """

    if pd.isna(valor):
        return True

    return es_faltante(valor)


def _mascara_faltantes(df):
    """
    Devuelve un dataframe booleano indicando
    qué celdas son faltantes.
    """

    return df.apply(
        lambda columna: columna.map(_es_valor_faltante)
    )

# ---------------------------------------------------------------
# métricas derivadas de detectores.py
# ---------------------------------------------------------------

def _contar_formato(df):
    """
    Número de variables que presentan
    problemas de formato y cantidad total
    de casos encontrados.
    """

    hallazgos = [
        h
        for h in analizar(df.fillna(""))
        if h.problema in PROBLEMAS_FORMATO
    ]

    variables = {
        h.variable
        for h in hallazgos
    }

    casos = sum(
        h.casos
        for h in hallazgos
    )

    return len(variables), casos


def _contar_categorias(df):
    """
    Cantidad de categorías inconsistentes.

    Se cuentan únicamente las variantes
    minoritarias detectadas.
    """

    hallazgos = [
        h
        for h in analizar(df.fillna(""))
        if h.problema == PROBLEMA_CATEGORIA
    ]

    return sum(
        len(h.valores)
        for h in hallazgos
    )


# ---------------------------------------------------------------
# generación de métricas
# ---------------------------------------------------------------

def generar_metricas(
    antes,
    despues,
):
    """
    Genera la tabla comparativa solicitada
    por la actividad 8 del proyecto.

    Devuelve un DataFrame.

    No escribe archivos.
    """

    def calcular(df):

        faltantes = _mascara_faltantes(df)

        total_faltantes = int(
            faltantes.values.sum()
        )

        total_celdas = df.shape[0] * df.shape[1]

        if total_celdas == 0:
            porcentaje_faltantes = 0
        else:
            porcentaje_faltantes = (
                total_faltantes
                / total_celdas
                * 100
            )

        variables_na = int(
            (faltantes.sum() > 0).sum()
        )

        variables_tipo = 0

        for columna in df.columns:

            presentes = df.loc[
                ~faltantes[columna],
                columna,
            ]

            presentes = presentes[
                presentes.map(
                    lambda x: isinstance(x, str)
                )
            ]

            if len(presentes) == 0:
                continue

            if tipo_inferido(
                presentes
            ) in TIPOS_INCORRECTOS:

                variables_tipo += 1

        variables_formato, _ = _contar_formato(df)

        return {
            "Registros": len(df),
            "Variables": len(df.columns),
            "Valores faltantes":
                f"{total_faltantes:,} ({porcentaje_faltantes:.2f}%)",
            "Variables con NA": variables_na,
            "Duplicados exactos":
                cantidad_duplicados_exactos(df),
            "Posibles duplicados":
                cantidad_duplicados_parciales(df),
            "Variables con formato inconsistente":
                variables_formato,
            "Variables con tipo incorrecto":
                variables_tipo,
            "Categorías inconsistentes":
                _contar_categorias(df),
        }

    metricas_antes = calcular(antes)
    metricas_despues = calcular(despues)

    filas = []

    for metrica in metricas_antes:

        filas.append(
            {
                "Métrica": metrica,
                "Antes": metricas_antes[metrica],
                "Después": metricas_despues[metrica],
            }
        )

    return pd.DataFrame(filas)

# ---------------------------------------------------------------
# registro de transformaciones
# ---------------------------------------------------------------

COLUMNAS_TRANSFORMACIONES = [
    "variable",
    "problema_detectado",
    "transformacion",
    "registros_afectados",
    "justificacion",
]


def generar_transformaciones(registro):
    """
    Valida y normaliza el registro de transformaciones.

    Este módulo NO calcula las transformaciones.
    Esa responsabilidad corresponde al pipeline
    de limpieza (main.py).

    Únicamente verifica que el DataFrame tenga
    el formato esperado por el proyecto.
    """

    faltantes = [
        c
        for c in COLUMNAS_TRANSFORMACIONES
        if c not in registro.columns
    ]

    if faltantes:
        raise ValueError(
            "El registro de transformaciones no contiene "
            f"las columnas requeridas: {faltantes}"
        )

    return (
        registro[COLUMNAS_TRANSFORMACIONES]
        .copy()
        .sort_values(
            ["variable", "problema_detectado"]
        )
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------
# informe de calidad
# ---------------------------------------------------------------

def generar_informe_md(
    metricas,
    transformaciones,
):
    """
    Genera el informe solicitado por
    la actividad 8.

    Devuelve únicamente el texto
    en formato Markdown.
    """
    total_transformaciones = 0

    if not transformaciones.empty:
        total_transformaciones = int(
            transformaciones["registros_afectados"].sum()
        )

    lineas = [

        "# Informe de calidad de los datos",
        "",

        "Comparación del conjunto de datos",
        "antes y después del proceso de limpieza.",
        "",

        "## Métricas",
        "",

        "| Métrica | Antes | Después |",
        "|---|---:|---:|",
    ]

    for _, fila in metricas.iterrows():

        lineas.append(
            f"| {fila['Métrica']} "
            f"| {fila['Antes']} "
            f"| {fila['Después']} |"
        )

    lineas.extend([

        "",

        "## Registro de transformaciones",
        "",

        "| Variable | Problema detectado | Transformación | Registros afectados |",
        "|---|---|---|---:|",

    ])

    if transformaciones.empty:

        lineas.append(
            "| *(sin transformaciones registradas)* | | | |"
        )

    else:

        for _, fila in transformaciones.iterrows():

            lineas.append(

                f"| {fila['variable']} "
                f"| {fila['problema_detectado']} "
                f"| {fila['transformacion']} "
                f"| {fila['registros_afectados']} |"

            )

    lineas.extend([
        "",

        "### Resumen de transformaciones",
        "",

        f"**Total de registros afectados:** {total_transformaciones}",


        "",

        "## Observaciones",
        "",

        "- Todas las métricas fueron calculadas utilizando "
        "las funciones del proyecto.",

        "- Los duplicados parciales fueron detectados "
        "mediante RapidFuzz.",

        "- Ningún registro fue eliminado automáticamente.",

        "- Todas las transformaciones corresponden al "
        "pipeline de limpieza ejecutado por `main.py`.",

        "- El aumento de valores faltantes es esperado y no implica "
        "pérdida de datos: se debe a que `normalizar_faltantes` unifica "
        "los centinelas de texto (\"N/A\", \"---\", \"0\", celdas vacías, "
        "`\\xa0`) bajo un solo NA explícito, y a la nueva columna derivada "
        "TELEFONO_2, vacía en las filas que solo traían un teléfono.",

        "- Las categorías inconsistentes que permanecen corresponden a "
        "variables de texto libre (nombres de establecimiento, dirección, "
        "personas), que NO se unifican a propósito: hacerlo destruiría la "
        "ortografía correcta de nombres propios.",

        "",

    ])

    return "\n".join(lineas)