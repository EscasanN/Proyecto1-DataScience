# pruebas de las funciones de limpieza: series armadas a mano,
# sin red ni disco. cada funcion se prueba con lo que debe transformar y con
# lo que debe dejar intacto (para no "corregir" de mas)

import pandas as pd

import limpieza as lim


def serie(valores, nombre="X"):
    return pd.Series(valores, name=nombre, dtype=str)


# ---------------------------------------------------------------
# forma
# ---------------------------------------------------------------

def test_quitar_invisibles():
    resultado = lim.quitar_invisibles(serie(["FOO\xa0BAR", "\xa0", "OK"]))
    assert resultado.tolist() == ["FOO BAR", " ", "OK"]


def test_normalizar_espacios():
    resultado = lim.normalizar_espacios(serie([" FOO", "BAR   BAZ ", "OK"]))
    assert resultado.tolist() == ["FOO", "BAR BAZ", "OK"]


def test_invisibles_antes_de_espacios():
    # el orden importa: un \xa0 aislado no cuenta como espacio para strip()
    # hasta que quitar_invisibles lo convierte en uno
    v = lim.quitar_invisibles(serie(["FOO\xa0\xa0BAR", "\xa0BORDE\xa0"]))
    resultado = lim.normalizar_espacios(v)
    assert resultado.tolist() == ["FOO BAR", "BORDE"]


def test_normalizar_mayusculas():
    resultado = lim.normalizar_mayusculas(serie(["3a. calle", "OK"]))
    assert resultado.tolist() == ["3A. CALLE", "OK"]


def test_quitar_puntuacion_borde():
    resultado = lim.quitar_puntuacion_borde(serie(["01-", "ZONA 3.", "OK"]))
    assert resultado.tolist() == ["01", "ZONA 3", "OK"]


def test_quitar_puntuacion_borde_respeta_nombres():
    # mismos casos que test_profiler.test_puntuacion_borde_respeta_nombres:
    # no debe tocar parentesis ni comillas legitimas
    resultado = lim.quitar_puntuacion_borde(
        serie(['DIARIO(REGULAR)', 'COLEGIO "LA INMACULADA"'])
    )
    assert resultado.tolist() == ['DIARIO(REGULAR)', 'COLEGIO "LA INMACULADA"']


# ---------------------------------------------------------------
# faltantes
# ---------------------------------------------------------------

def test_normalizar_faltantes():
    resultado = lim.normalizar_faltantes(serie(["", "N/A", "---", "JUAN PEREZ"]))
    assert resultado.isna().tolist() == [True, True, True, False]


def test_normalizar_faltantes_zero_es_centinela():
    # "0" esta en detectores.CENTINELAS: se marca como faltante. es un
    # riesgo documentado en limpieza.REGLA para variables donde 0 podria
    # ser un valor real
    resultado = lim.normalizar_faltantes(serie(["COBAN", "0"]))
    assert resultado.isna().tolist() == [False, True]


# ---------------------------------------------------------------
# categorias
# ---------------------------------------------------------------

def test_unificar_categoria():
    mapa = {"Guatemala": "GUATEMALA", "GUATEMLA": "GUATEMALA"}
    resultado = lim.unificar_categoria(serie(["Guatemala", "GUATEMALA", "GUATEMLA"]), mapa)
    assert resultado.tolist() == ["GUATEMALA", "GUATEMALA", "GUATEMALA"]


def test_mapa_categorias_dominantes():
    v = serie(["EDUCACION", "EDUCACION", "EDUCACION", "EDUCACIÓN"])
    mapa = lim.mapa_categorias_dominantes(v)
    assert mapa == {"EDUCACIÓN": "EDUCACION"}


def test_mapa_categorias_dominantes_sin_variantes():
    assert lim.mapa_categorias_dominantes(serie(["COBAN", "COBAN"])) == {}


def test_reglas_categorias_una_por_variable_con_variantes():
    df = pd.DataFrame({
        "DEPARTAMENTO": ["GUATEMALA", "GUATEMALA", "Guatemala"],
        "SECTOR": ["OFICIAL", "OFICIAL", "OFICIAL"],  # sin variantes: no genera regla
    })
    reglas = lim.reglas_categorias(df)
    assert [r.variable for r in reglas] == ["DEPARTAMENTO"]


# ---------------------------------------------------------------
# telefono y codigo
# ---------------------------------------------------------------

def test_normalizar_telefono():
    resultado = lim.normalizar_telefono(
        serie(["1234-5678", "1234567", "ABC12345"], nombre="TELEFONO")
    )
    assert resultado.tolist() == ["12345678", "1234567", "ABC12345"]


def test_separar_telefono_multivalor():
    primero, resto = lim.separar_telefono_multivalor(
        serie(["12345678-87654321", "12345678, 11111111", "12345678"], nombre="TELEFONO")
    )
    assert primero.tolist() == ["12345678", "12345678", "12345678"]
    assert resto.tolist() == ["87654321", "11111111", ""]


def test_normalizar_codigo():
    resultado = lim.normalizar_codigo(
        serie(["16-01-0137-46", " 16-01-0137-46 ", "16010137"], nombre="CODIGO")
    )
    assert resultado.tolist() == ["16-01-0137-46", "16-01-0137-46", "16010137"]


# ---------------------------------------------------------------
# cobertura de la estrategia
# ---------------------------------------------------------------

def test_estrategia_cubre_las_17_variables():
    variables_con_regla = {r.variable for r in lim.ESTRATEGIA}
    assert variables_con_regla == set(lim.TODAS_LAS_VARIABLES)


def test_revision_manual_no_autocorrige():
    # a proposito no tienen 'funcion': son casos donde el riesgo de
    # autocorregir es mayor que dejarlos pendientes
    for item in lim.REVISION_MANUAL:
        assert not hasattr(item, "funcion")
