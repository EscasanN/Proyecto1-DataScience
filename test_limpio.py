# validacion del conjunto limpio (actividad 7): pruebas sobre el CSV ya
# generado en output/. a diferencia de los otros test_*, estas SI leen disco:
# comprueban que el resultado del pipeline cumple las reglas de calidad.
#
# si el CSV no existe todavia, los tests se saltan con un aviso (correr main.py)

from pathlib import Path

import pandas as pd
import pytest

from catalogo import obtener as obtener_catalogo
from common import clave_canonica, es_faltante
import consistencia

CSV_LIMPIO = Path("output") / "establecimientos_limpios.csv"

COLUMNAS_ESPERADAS = [
    "CODIGO", "DISTRITO", "DEPARTAMENTO", "MUNICIPIO", "ESTABLECIMIENTO",
    "DIRECCION", "TELEFONO", "SUPERVISOR", "DIRECTOR", "NIVEL", "SECTOR",
    "AREA", "STATUS", "MODALIDAD", "JORNADA", "PLAN", "DEPARTAMENTAL",
    "TELEFONO_2",
]

DOMINIOS = {
    "NIVEL": {"DIVERSIFICADO"},
    "SECTOR": {"OFICIAL", "PRIVADO", "MUNICIPAL", "COOPERATIVA"},
    "AREA": {"URBANA", "RURAL", "SIN ESPECIFICAR"},
    "MODALIDAD": {"MONOLINGUE", "BILINGUE"},
    "STATUS": {"ABIERTA", "CERRADA TEMPORALMENTE", "CERRADA DEFINITIVAMENTE",
               "TEMPORAL TITULOS", "TEMPORAL NOMBRAMIENTO"},
}


@pytest.fixture(scope="module")
def limpio():
    if not CSV_LIMPIO.exists():
        pytest.skip(f"no existe {CSV_LIMPIO}; correr main.py primero")
    return pd.read_csv(CSV_LIMPIO, dtype=str, keep_default_na=False)


def _texto(serie):
    return serie[~serie.map(es_faltante)]


# ---------------------------------------------------------------
# estructura
# ---------------------------------------------------------------

def test_columnas_esperadas(limpio):
    assert list(limpio.columns) == COLUMNAS_ESPERADAS


def test_no_se_perdieron_filas(limpio):
    # la limpieza no elimina registros; deben seguir las 11,867
    assert len(limpio) == 11867


# ---------------------------------------------------------------
# reglas de calidad (actividad 7)
# ---------------------------------------------------------------

def test_sin_duplicados_exactos(limpio):
    assert limpio.duplicated().sum() == 0


def test_sin_espacios_en_bordes(limpio):
    for c in limpio.columns:
        v = _texto(limpio[c])
        assert (v == v.str.strip()).all(), f"{c} tiene espacios en el borde"


def test_sin_caracteres_invisibles(limpio):
    for c in limpio.columns:
        assert not limpio[c].str.contains("\xa0", regex=False).any(), f"{c} tiene \\xa0"


def test_codigo_cumple_patron(limpio):
    v = _texto(limpio["CODIGO"])
    assert v.str.fullmatch(r"\d{2}-\d{2}-\d{4}-\d{2}").all()


def test_categoricas_en_dominio(limpio):
    for col, dominio in DOMINIOS.items():
        valores = set(_texto(limpio[col]).unique())
        assert valores <= dominio, f"{col} tiene valores fuera de dominio: {valores - dominio}"


def test_departamento_en_catalogo(limpio):
    cat = obtener_catalogo()
    validos = {clave_canonica(x) for x in cat["DEPARTAMENTO"]}
    v = _texto(limpio["DEPARTAMENTO"])
    assert v.map(clave_canonica).isin(validos).all()


def test_consistencia_entre_variables(limpio):
    # CODIGO[:2] concuerda con DEPARTAMENTO y MUNICIPIO pertenece a su depto
    reporte = consistencia.revisar_consistencia(limpio, obtener_catalogo())
    assert len(reporte) == 0, f"inconsistencias: {reporte.to_dict('records')}"
