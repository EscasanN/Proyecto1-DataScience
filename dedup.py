# deduplicación de registros (actividad 5.g del proyecto).
#
# Este módulo NO elimina registros automáticamente.
# Únicamente identifica:
#
#   1. duplicados exactos
#   2. posibles duplicados por similitud (RapidFuzz)
#
# dejando la decisión para revisión manual, tal como indica la guía.
#
# Todas las funciones son puras:
#
# dataframe -> dataframe
#
# No escriben archivos ni modifican el dataframe original.

from dataclasses import dataclass

import pandas as pd
from rapidfuzz import fuzz

from common import clave_canonica, es_faltante

from profiler import UMBRAL_TYPO


# mismo umbral usado por profiler.py
# preferimos pocos candidatos buenos antes que muchos falsos positivos
UMBRAL_SIMILITUD = UMBRAL_TYPO


@dataclass(frozen=True)
class PosibleDuplicado:
    """
    Representa un posible duplicado parcial.

    No implica que las filas deban fusionarse.
    Solamente documenta el caso para revisión manual.
    """

    codigo_a: str
    codigo_b: str

    departamento: str
    municipio: str

    establecimiento_a: str
    establecimiento_b: str

    similitud: float

    decision: str = "PENDIENTE DE REVISION"


# ---------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------

def _presentes(df, columnas):
    """
    Devuelve únicamente las filas donde todas las columnas
    especificadas contienen un valor.
    """

    mascara = pd.Series(True, index=df.index)

    for columna in columnas:
        mascara &= ~df[columna].map(es_faltante)

    return df.loc[mascara]


def _nombre_canonico(nombre):
    """
    Nombre usado únicamente para comparar.

    No modifica el valor original.
    """

    return clave_canonica(nombre)


# ---------------------------------------------------------------
# duplicados exactos
# ---------------------------------------------------------------

def duplicados_exactos(df):
    """
    Devuelve todas las filas que participan en un duplicado exacto.

    No elimina ninguna fila.
    """

    if df.empty:
        return df.copy()

    mascara = df.duplicated(keep=False)

    return (
        df.loc[mascara]
        .copy()
        .sort_index()
    )


def cantidad_duplicados_exactos(df):
    """
    Cantidad de registros duplicados exactos.

    Equivale a DataFrame.duplicated().
    """

    return int(df.duplicated().sum())

# ---------------------------------------------------------------
# duplicados parciales
# ---------------------------------------------------------------

def duplicados_parciales(df, umbral=UMBRAL_SIMILITUD):
    """
    Busca posibles duplicados por similitud del nombre del establecimiento.

    Criterios:

    * mismo DEPARTAMENTO
    * mismo MUNICIPIO
    * similitud >= umbral

    No elimina registros.
    Devuelve un DataFrame para revisión manual.
    """

    columnas = [
        "DEPARTAMENTO",
        "MUNICIPIO",
        "ESTABLECIMIENTO",
    ]

    for columna in columnas:
        if columna not in df.columns:
            raise KeyError(f"No existe la columna '{columna}'.")

    datos = _presentes(df, columnas)

    resultados = []
    pares_vistos = set()

    for (departamento, municipio), grupo in datos.groupby(
        ["DEPARTAMENTO", "MUNICIPIO"],
        sort=False,
    ):

        if len(grupo) < 2:
            continue

        registros = list(grupo.iterrows())

        for i in range(len(registros)):

            idx_a, fila_a = registros[i]

            nombre_a = fila_a["ESTABLECIMIENTO"]
            canonico_a = _nombre_canonico(nombre_a)

            for j in range(i + 1, len(registros)):

                idx_b, fila_b = registros[j]

                nombre_b = fila_b["ESTABLECIMIENTO"]
                canonico_b = _nombre_canonico(nombre_b)

                # evita comparar cadenas muy distintas
                if abs(len(canonico_a) - len(canonico_b)) > 5:
                    continue

                if canonico_a == canonico_b:
                    continue
                score = fuzz.ratio(canonico_a, canonico_b)

                if score < umbral:
                    continue

                llave = tuple(sorted((idx_a, idx_b)))

                if llave in pares_vistos:
                    continue

                pares_vistos.add(llave)

                resultados.append(
                    PosibleDuplicado(
                        codigo_a=fila_a["CODIGO"],
                        codigo_b=fila_b["CODIGO"],
                        departamento=departamento,
                        municipio=municipio,
                        establecimiento_a=nombre_a,
                        establecimiento_b=nombre_b,
                        similitud=float(score),
                    )
                )

    if not resultados:
        return pd.DataFrame(
            columns=[
                "codigo_a",
                "codigo_b",
                "departamento",
                "municipio",
                "establecimiento_a",
                "establecimiento_b",
                "similitud",
                "decision",
            ]
        )

    return pd.DataFrame(
        [
            {
                "codigo_a": r.codigo_a,
                "codigo_b": r.codigo_b,
                "departamento": r.departamento,
                "municipio": r.municipio,
                "establecimiento_a": r.establecimiento_a,
                "establecimiento_b": r.establecimiento_b,
                "similitud": round(r.similitud, 2),
                "decision": r.decision,
            }
            for r in resultados
        ]
    ).sort_values(
        ["departamento", "municipio", "similitud"],
        ascending=[True, True, False],
    ).reset_index(drop=True)


def cantidad_duplicados_parciales(df, umbral=UMBRAL_SIMILITUD):
    """
    Número de posibles duplicados parciales.
    """

    return len(duplicados_parciales(df, umbral))

# ---------------------------------------------------------------
# resumen y métricas
# ---------------------------------------------------------------

def resumen_duplicados(df, umbral=UMBRAL_SIMILITUD):
    """
    Devuelve un resumen de la deduplicación.

    No modifica el dataframe.
    """

    exactos = duplicados_exactos(df)
    parciales = duplicados_parciales(df, umbral)

    return pd.DataFrame(
        [
            {
                "tipo": "Duplicados exactos",
                "casos": len(exactos),
            },
            {
                "tipo": "Posibles duplicados",
                "casos": len(parciales),
            },
        ]
    )


def exportar_metricas(df, umbral=UMBRAL_SIMILITUD):
    """
    Devuelve las métricas relacionadas únicamente con deduplicación.

    Persona 3 será quien una estas métricas con las producidas por
    eda.py y profiler.py.
    """

    exactos = cantidad_duplicados_exactos(df)
    parciales = cantidad_duplicados_parciales(df, umbral)

    return pd.DataFrame(
        [
            {
                "metrica": "Duplicados exactos",
                "valor": exactos,
            },
            {
                "metrica": "Posibles duplicados",
                "valor": parciales,
            },
        ]
    )


# ---------------------------------------------------------------
# registro de transformaciones
# ---------------------------------------------------------------

def exportar_transformaciones(df, umbral=UMBRAL_SIMILITUD):
    """
    Construye el registro solicitado por la guía.

    Como Persona 2 no elimina registros automáticamente,
    las transformaciones documentadas corresponden únicamente
    a la detección de duplicados.
    """

    filas = []

    exactos = cantidad_duplicados_exactos(df)

    if exactos:

        filas.append(
            {
                "variable": "REGISTRO",
                "problema_detectado": "duplicados exactos",
                "transformacion": (
                    "identificar duplicados exactos para revisión manual"
                ),
                "registros_afectados": exactos,
                "justificacion": (
                    "el proyecto prohíbe eliminar registros automáticamente"
                ),
            }
        )

    parciales = cantidad_duplicados_parciales(df, umbral)

    if parciales:

        filas.append(
            {
                "variable": "ESTABLECIMIENTO",
                "problema_detectado": "posibles duplicados por similitud",
                "transformacion": (
                    f"comparación con RapidFuzz (umbral {umbral})"
                ),
                "registros_afectados": parciales,
                "justificacion": (
                    "los casos deben revisarse manualmente antes de decidir "
                    "si corresponden al mismo establecimiento"
                ),
            }
        )

    return pd.DataFrame(
        filas,
        columns=[
            "variable",
            "problema_detectado",
            "transformacion",
            "registros_afectados",
            "justificacion",
        ],
    )

# ---------------------------------------------------------------
# informe en markdown
# ---------------------------------------------------------------

def generar_informe_md(df, umbral=UMBRAL_SIMILITUD):
    """
    Genera el informe de deduplicación en formato Markdown.

    Devuelve únicamente el texto.
    No escribe archivos.
    """

    exactos = duplicados_exactos(df)
    parciales = duplicados_parciales(df, umbral)

    lineas = [
        "# Informe de deduplicación",
        "",
        "Este informe resume la búsqueda de registros duplicados",
        "realizada sobre el conjunto de datos limpio.",
        "",
        "## Resumen",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
        f"| Duplicados exactos | {len(exactos)} |",
        f"| Posibles duplicados | {len(parciales)} |",
        "",
        "## Duplicados exactos",
        "",
    ]

    if exactos.empty:

        lineas.append(
            "No se encontraron registros duplicados exactos."
        )

    else:

        lineas.extend([
            "Se encontraron registros idénticos en todas sus columnas.",
            "",
            "**No fueron eliminados automáticamente.**",
            "",
        ])

    lineas.extend([
        "",
        "## Posibles duplicados",
        "",
    ])

    if parciales.empty:

        lineas.append(
            "No se encontraron posibles duplicados por similitud."
        )

    else:

        lineas.extend([
            "Los siguientes registros presentan una similitud",
            f"igual o superior a **{umbral}**.",
            "",
            "| Departamento | Municipio | Establecimiento A | Establecimiento B | Similitud | Decisión |",
            "|---|---|---|---|---:|---|",
        ])

        for _, fila in parciales.iterrows():

            lineas.append(
                f"| {fila['departamento']} "
                f"| {fila['municipio']} "
                f"| {fila['establecimiento_a']} "
                f"| {fila['establecimiento_b']} "
                f"| {fila['similitud']:.2f} "
                f"| {fila['decision']} |"
            )

    lineas.extend([
        "",
        "## Observaciones",
        "",
        "- Los duplicados exactos **no fueron eliminados automáticamente**.",
        "- Los posibles duplicados fueron detectados utilizando RapidFuzz.",
        "- Todos los casos requieren revisión manual antes de decidir",
        "  si corresponden al mismo establecimiento.",
        "",
    ])

    return "\n".join(lineas)


# ---------------------------------------------------------------
# ejecución independiente
# ---------------------------------------------------------------

def main():

    print(
        "dedup.py es un módulo reutilizable.\n"
        "Debe ser utilizado desde main.py para generar "
        "los reportes del proyecto."
    )


if __name__ == "__main__":
    main()