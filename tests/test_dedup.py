# pruebas de deduplicación.
#
# todo sobre dataframes armados a mano,
# sin red ni disco.
#
# se valida:
#
# - duplicados exactos
# - duplicados parciales
# - bloqueo por departamento/municipio
# - umbral de similitud
# - comportamiento cuando no hay duplicados

import pandas as pd

from src import dedup


# ---------------------------------------------------------------
# duplicados exactos
# ---------------------------------------------------------------

def test_duplicados_exactos_vacio():

    df = pd.DataFrame(columns=["A", "B"])

    resultado = dedup.duplicados_exactos(df)

    assert resultado.empty


def test_detecta_duplicados_exactos():

    df = pd.DataFrame({
        "CODIGO": ["1", "2", "2"],
        "ESTABLECIMIENTO": [
            "INED",
            "COLEGIO",
            "COLEGIO",
        ],
    })

    resultado = dedup.duplicados_exactos(df)

    assert len(resultado) == 2


def test_cantidad_duplicados_exactos():

    df = pd.DataFrame({
        "A": [1, 2, 2, 3],
    })

    assert dedup.cantidad_duplicados_exactos(df) == 1


# ---------------------------------------------------------------
# duplicados parciales
# ---------------------------------------------------------------

def test_detecta_posible_typo():

    df = pd.DataFrame({

        "CODIGO": [
            "01",
            "02",
        ],

        "DEPARTAMENTO": [
            "GUATEMALA",
            "GUATEMALA",
        ],

        "MUNICIPIO": [
            "MIXCO",
            "MIXCO",
        ],

        "ESTABLECIMIENTO": [
            "INSTITUTO INTERCULTURAL",
            "INSTITUTO INTERCULTRUAL",
        ],
    })

    resultado = dedup.duplicados_parciales(df)

    assert len(resultado) == 1


def test_no_cruza_municipios():

    df = pd.DataFrame({

        "CODIGO": [
            "01",
            "02",
        ],

        "DEPARTAMENTO": [
            "GUATEMALA",
            "GUATEMALA",
        ],

        "MUNICIPIO": [
            "MIXCO",
            "VILLA NUEVA",
        ],

        "ESTABLECIMIENTO": [
            "INSTITUTO INTERCULTURAL",
            "INSTITUTO INTERCULTRUAL",
        ],
    })

    resultado = dedup.duplicados_parciales(df)

    assert resultado.empty


def test_no_cruza_departamentos():

    df = pd.DataFrame({

        "CODIGO": [
            "01",
            "02",
        ],

        "DEPARTAMENTO": [
            "GUATEMALA",
            "ESCUINTLA",
        ],

        "MUNICIPIO": [
            "MIXCO",
            "MIXCO",
        ],

        "ESTABLECIMIENTO": [
            "INSTITUTO INTERCULTURAL",
            "INSTITUTO INTERCULTRUAL",
        ],
    })

    resultado = dedup.duplicados_parciales(df)

    assert resultado.empty


def test_nombre_identico_no_es_typo():

    df = pd.DataFrame({

        "CODIGO": [
            "01",
            "02",
        ],

        "DEPARTAMENTO": [
            "GUATEMALA",
            "GUATEMALA",
        ],

        "MUNICIPIO": [
            "MIXCO",
            "MIXCO",
        ],

        "ESTABLECIMIENTO": [
            "COLEGIO NACIONAL",
            "COLEGIO NACIONAL",
        ],
    })

    resultado = dedup.duplicados_parciales(df)

    assert resultado.empty


def test_umbral_funciona():

    df = pd.DataFrame({

        "CODIGO": [
            "01",
            "02",
        ],

        "DEPARTAMENTO": [
            "GUATEMALA",
            "GUATEMALA",
        ],

        "MUNICIPIO": [
            "MIXCO",
            "MIXCO",
        ],

        "ESTABLECIMIENTO": [
            "INSTITUTO INTERCULTURAL",
            "INSTITUTO INTERCULTRUAL",
        ],
    })

    resultado = dedup.duplicados_parciales(
        df,
        umbral=100,
    )

    assert resultado.empty


# ---------------------------------------------------------------
# resumen
# ---------------------------------------------------------------

def test_resumen_duplicados():

    df = pd.DataFrame({

        "CODIGO": [
            "1",
            "2",
            "2",
        ],

        "DEPARTAMENTO": [
            "GUATEMALA",
            "GUATEMALA",
            "GUATEMALA",
        ],

        "MUNICIPIO": [
            "MIXCO",
            "MIXCO",
            "MIXCO",
        ],

        "ESTABLECIMIENTO": [
            "A",
            "B",
            "B",
        ],
    })

    resumen = dedup.resumen_duplicados(df)

    assert len(resumen) == 2
    assert "Duplicados exactos" in resumen["tipo"].values
    assert "Posibles duplicados" in resumen["tipo"].values