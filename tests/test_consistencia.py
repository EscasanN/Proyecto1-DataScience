# pruebas de consistencia entre variables y de la variable derivada TELEFONO_2.
# series/dataframes armados a mano, sin red ni disco

import pandas as pd

from src import consistencia as con
from src import limpieza as lim


def _catalogo():
    return pd.DataFrame({
        "DEPARTAMENTO": ["ALTA VERAPAZ", "PETEN", "HUEHUETENANGO"],
        "MUNICIPIO": ["COBAN", "LA LIBERTAD", "LA LIBERTAD"],
    })


# ---------------------------------------------------------------
# CODIGO vs DEPARTAMENTO
# ---------------------------------------------------------------

def test_codigo_departamento_consistente():
    # 16 = ALTA VERAPAZ: no hay contradiccion
    df = pd.DataFrame({"CODIGO": ["16-01-0137-46"], "DEPARTAMENTO": ["ALTA VERAPAZ"]})
    assert len(con.codigo_vs_departamento(df)) == 0


def test_codigo_departamento_contradice():
    # 16 es ALTA VERAPAZ pero la fila dice PETEN
    df = pd.DataFrame({"CODIGO": ["16-01-0137-46"], "DEPARTAMENTO": ["PETEN"]})
    fuera = con.codigo_vs_departamento(df)
    assert len(fuera) == 1
    assert fuera.iloc[0]["departamento_segun_codigo"] == "ALTA VERAPAZ"


def test_codigo_departamento_tolera_tildes():
    # 17 = PETEN; "PETÉN" con tilde no debe contar como contradiccion
    df = pd.DataFrame({"CODIGO": ["17-01-0001-46"], "DEPARTAMENTO": ["PETÉN"]})
    assert len(con.codigo_vs_departamento(df)) == 0


# ---------------------------------------------------------------
# MUNICIPIO vs DEPARTAMENTO
# ---------------------------------------------------------------

def test_municipio_pertenece_al_departamento():
    df = pd.DataFrame({"DEPARTAMENTO": ["ALTA VERAPAZ"], "MUNICIPIO": ["COBAN"]})
    assert len(con.municipio_vs_departamento(df, _catalogo())) == 0


def test_municipio_homonimo_en_departamento_equivocado():
    # LA LIBERTAD existe en PETEN y HUEHUE, pero NO en ALTA VERAPAZ
    df = pd.DataFrame({"DEPARTAMENTO": ["ALTA VERAPAZ"], "MUNICIPIO": ["LA LIBERTAD"]})
    assert len(con.municipio_vs_departamento(df, _catalogo())) == 1


def test_revisar_consistencia_junta_ambas():
    df = pd.DataFrame({
        "CODIGO": ["16-01-0137-46", "17-01-0001-46"],
        "DEPARTAMENTO": ["PETEN", "PETEN"],       # fila 0: codigo 16 contradice
        "MUNICIPIO": ["COBAN", "LA LIBERTAD"],    # fila 0: COBAN no es de PETEN
    })
    reporte = con.revisar_consistencia(df, _catalogo())
    tipos = set(reporte["tipo"])
    assert "CODIGO vs DEPARTAMENTO" in tipos
    assert "MUNICIPIO vs DEPARTAMENTO" in tipos


# ---------------------------------------------------------------
# variable derivada TELEFONO_2
# ---------------------------------------------------------------

def test_derivar_telefono_2():
    serie = pd.Series(["12345678-87654321", "12345678, 11111111", "12345678"], name="TELEFONO")
    resto = lim.derivar_telefono_2(serie)
    assert resto.tolist() == ["87654321", "11111111", ""]
