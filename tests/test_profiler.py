# pruebas de detectores y utilidades: todo sobre series armadas a mano, sin
# red ni disco. cada detector se prueba con lo que debe encontrar y con lo
# que debe dejar pasar

import pandas as pd
import pytest

from src.common import clave_canonica, es_faltante, sin_tildes
from src import detectores as det
from src.profiler import detectar_fuera_de_catalogo, detectar_typos_establecimiento, priorizar


def serie(valores, nombre="X"):
    return pd.Series(valores, name=nombre, dtype=str)


def casos(hallazgos):
    return sum(h.casos for h in hallazgos)


# ---------------------------------------------------------------
# common
# ---------------------------------------------------------------

def test_es_faltante():
    assert es_faltante("")
    assert es_faltante("   ")
    assert es_faltante("\xa0")          # el vacio que manda el portal
    assert not es_faltante("COBAN")
    assert not es_faltante("--")        # centinela: hay algo escrito, no es vacio


def test_sin_tildes():
    assert sin_tildes("PETÉN") == "PETEN"
    assert sin_tildes("EDUCACIÓN") == "EDUCACION"
    # la enie tambien cae: quien la use tiene que saberlo
    assert sin_tildes("AÑO") == "ANO"


def test_clave_canonica_agrupa_variantes():
    variantes = ["EDUCACIÓN", "educacion", "  EDUCACION ", "EDUCACIÒN"]
    assert len({clave_canonica(v) for v in variantes}) == 1


def test_clave_canonica_no_mezcla_distintos():
    assert clave_canonica("COBAN") != clave_canonica("TACTIC")


# ---------------------------------------------------------------
# detectores de forma
# ---------------------------------------------------------------

def test_espacios_borde():
    h = det.detectar_espacios_borde(serie([" FOO", "BAR ", "OK"]))
    assert casos(h) == 2


def test_espacios_borde_limpio():
    assert det.detectar_espacios_borde(serie(["FOO", "BAR"])) == []


def test_espacios_multiples():
    h = det.detectar_espacios_multiples(serie(["LICEO  CANADIENSE", "LICEO CANADIENSE"]))
    assert casos(h) == 1


def test_invisibles():
    h = det.detectar_invisibles(serie(["FOO\xa0BAR", "\xa0", "OK"]))
    # el \xa0 solo (celda "vacia" del portal) tambien cuenta
    assert casos(h) == 2


def test_mayusculas_inconsistentes():
    h = det.detectar_mayusculas_inconsistentes(serie(["3a. CALLE", "4A. CALLE"]))
    assert casos(h) == 1


def test_caracteres_sospechosos():
    # acento grave: no existe en espanol, es tecleo o mojibake
    h = det.detectar_caracteres_sospechosos(serie(["EDUCACIÒN", "EDUCACIÓN"]))
    assert casos(h) == 1


def test_puntuacion_borde():
    h = det.detectar_puntuacion_borde(serie(["01-", "ZONA 3.", "OK"]))
    assert casos(h) == 2


def test_puntuacion_borde_respeta_nombres():
    # parentesis y comillas legitimas no son problema
    h = det.detectar_puntuacion_borde(serie(['DIARIO(REGULAR)', 'COLEGIO "LA INMACULADA"']))
    assert h == []


def test_delimitadores_desbalanceados():
    h = det.detectar_delimitadores_desbalanceados(serie(['COLEGIO "SANTA FE', "INED (SALAMA)"]))
    assert casos(h) == 1


# ---------------------------------------------------------------
# detectores de contenido
# ---------------------------------------------------------------

def test_centinelas():
    h = det.detectar_centinelas(serie(["---", "SIN DATO", "N/A", "XXX", "JUAN PEREZ"]))
    assert casos(h) == 4


def test_centinelas_no_marca_nombres():
    assert det.detectar_centinelas(serie(["JUAN PEREZ", "MARIA LOPEZ"])) == []


def test_categorias_duplicadas_cuenta_minoritarias():
    # 3 bien escritas + 1 variante: el problema es 1, no 4
    h = det.detectar_categorias_duplicadas(
        serie(["EDUCACION", "EDUCACION", "EDUCACION", "EDUCACIÓN"])
    )
    assert casos(h) == 1
    assert h[0].valores[0][0] == "EDUCACIÓN"


def test_categorias_duplicadas_ignora_puntuacion_pura():
    # '--' y '---' canonicalizan a vacio: no son "variantes" de nada
    assert det.detectar_categorias_duplicadas(serie(["--", "---", "-"])) == []


def test_formato_telefono():
    h = det.detectar_formato_telefono(serie(["12345678", "1234567", "ABC"], nombre="TELEFONO"))
    assert casos(h) == 2


def test_formato_telefono_solo_aplica_a_telefono():
    assert det.detectar_formato_telefono(serie(["1234567"], nombre="CODIGO")) == []


def test_telefono_multivalor():
    h = det.detectar_telefono_multivalor(
        serie(["12345678-87654321", "12345678, 11111111", "12345678"], nombre="TELEFONO")
    )
    assert casos(h) == 2


def test_formato_codigo():
    h = det.detectar_formato_codigo(serie(["16-01-0137-46", "16010137", "XX-01"], nombre="CODIGO"))
    assert casos(h) == 2


# ---------------------------------------------------------------
# dominio y typos
# ---------------------------------------------------------------

@pytest.fixture
def catalogo_mini():
    return pd.DataFrame({
        "DEPARTAMENTO": ["ALTA VERAPAZ", "ALTA VERAPAZ", "PETEN"],
        "MUNICIPIO": ["COBAN", "TACTIC", "LA LIBERTAD"],
    })


def test_fuera_de_catalogo(catalogo_mini):
    df = pd.DataFrame({
        "DEPARTAMENTO": ["ALTA VERAPAZ", "XELAJU"],
        "MUNICIPIO": ["COBAN", "COBAN"],
    })
    h = detectar_fuera_de_catalogo(df, catalogo_mini)
    problemas = {x.problema: x.casos for x in h}
    assert problemas["departamento fuera del catalogo oficial"] == 1
    # COBAN existe pero no bajo XELAJU: el par es lo que se valida
    assert problemas["municipio fuera del catalogo de su departamento"] == 1


def test_fuera_de_catalogo_tolera_tildes(catalogo_mini):
    # PETÉN con tilde no debe reportarse como departamento inexistente
    df = pd.DataFrame({"DEPARTAMENTO": ["PETÉN"], "MUNICIPIO": ["LA LIBERTAD"]})
    assert detectar_fuera_de_catalogo(df, catalogo_mini) == []


def test_typos_dentro_del_municipio():
    df = pd.DataFrame({
        "DEPARTAMENTO": ["BV", "BV"],
        "MUNICIPIO": ["SALAMA", "SALAMA"],
        "ESTABLECIMIENTO": ["INSTITUTO INTERCULTURAL", "INSTITUTO INTERCULTRUAL"],
    })
    h = detectar_typos_establecimiento(df)
    assert casos(h) == 1


def test_typos_no_cruza_municipios():
    # mismos nombres parecidos pero en municipios distintos: escuelas distintas
    df = pd.DataFrame({
        "DEPARTAMENTO": ["BV", "BV"],
        "MUNICIPIO": ["SALAMA", "RABINAL"],
        "ESTABLECIMIENTO": ["INSTITUTO INTERCULTURAL", "INSTITUTO INTERCULTRUAL"],
    })
    assert detectar_typos_establecimiento(df) == []


# ---------------------------------------------------------------
# priorizacion
# ---------------------------------------------------------------

def test_priorizar_cubre_todas_las_variables():
    tabla = priorizar([])
    assert len(tabla) == 17
    assert (tabla["casos"] == 0).all()


def test_priorizar_pondera_por_criticidad():
    h = [
        det.Hallazgo("MUNICIPIO", "p", 10, "e", ()),      # criticidad 3 -> 30
        det.Hallazgo("DIRECTOR", "p", 20, "e", ()),       # criticidad 1 -> 20
    ]
    tabla = priorizar(h).set_index("variable")
    assert tabla.loc["MUNICIPIO", "score"] > tabla.loc["DIRECTOR", "score"]
