# detectores de problemas de texto y categorias sobre los datos crudos.
# esta capa solo DETECTA: no corrige, no escribe, no toca red. cada detector
# es puro y recibe una serie; el valor crudo se reporta tal cual vino

from dataclasses import dataclass
import re
import unicodedata

import pandas as pd

from src.common import clave_canonica, es_faltante


# una fila de la tabla que pide division.md, mas el listado de valores
@dataclass(frozen=True)
class Hallazgo:
    variable: str
    problema: str
    casos: int
    ejemplo: str
    valores: tuple  # ((valor_crudo, frecuencia), ...)


# ---------------------------------------------------------------
# vocabulario
# ---------------------------------------------------------------

# invisibles que se cuelan del html. el \xa0 es el que manda el portal
INVISIBLES = {
    "\xa0": "espacio duro (nbsp)",
    "\t": "tabulador",
    "\r": "retorno de carro",
    "\n": "salto de linea",
    "​": "espacio de ancho cero",
    "‌": "non-joiner",
    "‍": "joiner",
    "﻿": "BOM",
}

# marcas de mojibake y acentos que en espanol no existen (È por É, etc.)
SOSPECHOSOS = set("ÃÂ�ÈÀÌÒÙËÏ")

# texto que alguien escribio para decir "aqui no hay dato"
CENTINELAS = {
    "N/A", "NA", "N.A.", "NULL", "NONE", "NINGUNO", "SIN DATO", "SIN DATOS",
    "S/N", "NO TIENE", "NO APLICA", "X", "XX", "XXX", "0", "?", "-",
}

# valor formado solo por puntuacion: ---, ..., //, etc.
SOLO_PUNTUACION = re.compile(r"^[\W_]+$", re.UNICODE)

ESPACIOS_MULTIPLES = re.compile(r"\S\s{2,}\S")

# solo puntuacion que sobra de verdad: un guion o punto colgando al final, o
# algo raro al inicio. NO se marca el ) de "DIARIO(REGULAR)" ni las comillas
# de 'COLEGIO "LA INMACULADA"', que son parte legitima del nombre.
PUNTUACION_BORDE = re.compile(r"^[^\w\s\"'(¿¡]|[.,;:\-]$", re.UNICODE)

# comillas o parentesis que abren y no cierran
DELIMITADORES = [('"', '"'), ("(", ")")]

PATRON_CODIGO = re.compile(r"^\d{2}-\d{2}-\d{4}-\d{2}$")
TELEFONO_VALIDO = re.compile(r"^\d{8}$")
SEPARADOR_MULTIPLE = re.compile(r"[,/;]|\s-\s|\d-\d")


# la serie sin los faltantes
def _presentes(serie):
    return serie[~serie.map(es_faltante)]


# empaqueta el resultado para que todos los detectores reporten igual. el
# ejemplo va con repr() porque si no un ' FOO ' se ve igual que un 'FOO'
def _armar(serie, afectados, problema):
    if len(afectados) == 0:
        return []

    frec = afectados.value_counts()

    return [Hallazgo(
        variable=serie.name,
        problema=problema,
        casos=int(len(afectados)),
        ejemplo=repr(afectados.iloc[0]),
        valores=tuple((str(v), int(n)) for v, n in frec.items()),
    )]


# ---------------------------------------------------------------
# detectores de forma
# ---------------------------------------------------------------

def detectar_espacios_borde(serie):
    v = _presentes(serie)
    return _armar(serie, v[v != v.str.strip()], "espacios al inicio o final")


def detectar_espacios_multiples(serie):
    v = _presentes(serie)
    return _armar(serie, v[v.str.contains(ESPACIOS_MULTIPLES)], "espacios multiples internos")


def detectar_invisibles(serie):
    # aca NO se excluyen los faltantes: la celda que solo trae \xa0 es
    # justamente el caso que interesa reportar.
    hit = serie[serie.map(lambda x: any(c in x for c in INVISIBLES))]
    return _armar(serie, hit, "caracteres invisibles")


def detectar_mayusculas_inconsistentes(serie):
    v = _presentes(serie)
    return _armar(serie, v[v.str.strip() != v.str.strip().str.upper()], "mayusculas inconsistentes")


def detectar_caracteres_sospechosos(serie):
    def sospechoso(x):
        return any(c in SOSPECHOSOS or unicodedata.category(c) == "Cc" for c in x)

    v = _presentes(serie)
    return _armar(serie, v[v.map(sospechoso)], "caracteres sospechosos o mojibake")


def detectar_puntuacion_borde(serie):
    v = _presentes(serie)
    # los centinelas (---, ...) tienen su propio detector; no los cuentes aca
    v = v[~v.str.strip().str.upper().map(_es_centinela)]
    return _armar(serie, v[v.str.strip().str.contains(PUNTUACION_BORDE)], "puntuacion sobrante al inicio o final")


def detectar_delimitadores_desbalanceados(serie):
    def desbalanceado(x):
        for abre, cierra in DELIMITADORES:
            if abre == cierra:
                if x.count(abre) % 2:
                    return True
            elif x.count(abre) != x.count(cierra):
                return True
        return False

    v = _presentes(serie)
    return _armar(serie, v[v.map(desbalanceado)], "comillas o parentesis sin cerrar")


# ---------------------------------------------------------------
# detectores de contenido
# ---------------------------------------------------------------

def _es_centinela(valor):
    return valor in CENTINELAS or bool(SOLO_PUNTUACION.match(valor))


# texto que significa "no hay dato": ---, SIN DATO, N/A... distinto del
# faltante: aca la celda no esta vacia, alguien escribio algo
def detectar_centinelas(serie):
    v = _presentes(serie)
    return _armar(serie, v[v.str.strip().str.upper().map(_es_centinela)], "centinela de dato ausente")


# mismo valor escrito de varias formas: se agrupa por clave canonica y se
# reportan solo las filas con escritura minoritaria. asi 'casos' equivale a
# cuantos valores tocaria la regla de limpieza, no al grupo entero
def detectar_categorias_duplicadas(serie):
    v = _presentes(serie)
    if len(v) == 0:
        return []

    claves = v.map(clave_canonica)

    # un valor de pura puntuacion ('--', '...') deja la clave en vacio y
    # entonces agrupa basura no relacionada. eso ya lo ve detectar_centinelas.
    v = v[claves != ""]
    claves = claves[claves != ""]

    if len(v) == 0:
        return []

    grupos = pd.DataFrame({"valor": v.values, "clave": claves.values})

    conteo = grupos.value_counts(["clave", "valor"]).rename("n").reset_index()
    # ante empate manda el alfabetico, para que la corrida sea reproducible
    dominante = (
        conteo.sort_values(["n", "valor"], ascending=[False, True])
        .drop_duplicates("clave")
        .set_index("clave")["valor"]
    )

    minoritarias = grupos[grupos["valor"] != grupos["clave"].map(dominante)]

    afectados = minoritarias["valor"].rename(serie.name)
    return _armar(serie, afectados, "categoria duplicada por escritura")


# el detector decide si aplica: asi el runner no sabe de columnas
def detectar_formato_telefono(serie):
    if serie.name != "TELEFONO":
        return []

    v = _presentes(serie).str.strip()
    return _armar(serie, v[~v.str.fullmatch(TELEFONO_VALIDO)], "telefono fuera de formato (no son 8 digitos)")


def detectar_telefono_multivalor(serie):
    if serie.name != "TELEFONO":
        return []

    v = _presentes(serie).str.strip()
    return _armar(serie, v[v.str.contains(SEPARADOR_MULTIPLE)], "telefono con mas de un numero en la celda")


def detectar_formato_codigo(serie):
    if serie.name != "CODIGO":
        return []

    v = _presentes(serie).str.strip()
    return _armar(serie, v[~v.str.fullmatch(PATRON_CODIGO)], "codigo fuera del patron dd-dd-dddd-dd")


# agregar un chequeo es agregar una funcion aca, sin tocar el runner
DETECTORES = [
    detectar_espacios_borde,
    detectar_espacios_multiples,
    detectar_invisibles,
    detectar_mayusculas_inconsistentes,
    detectar_caracteres_sospechosos,
    detectar_puntuacion_borde,
    detectar_delimitadores_desbalanceados,
    detectar_centinelas,
    detectar_categorias_duplicadas,
    detectar_formato_telefono,
    detectar_telefono_multivalor,
    detectar_formato_codigo,
]


def analizar_columna(serie):
    return [h for detector in DETECTORES for h in detector(serie)]


def analizar(df):
    return [h for col in df.columns for h in analizar_columna(df[col])]
