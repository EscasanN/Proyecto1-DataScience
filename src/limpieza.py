# funciones de limpieza reutilizables: correccion de texto y
# faltantes a nivel de columna. cada funcion es PURA (serie -> serie nueva),
# no muta la serie de entrada, no hace i/o ni toca red. son el prototipo que
# se prueba sobre una copia/muestra (ver estrategia.py) antes de decidir si
# se aplican de forma definitiva sobre el dataset completo.
#
# el orden importa para las de "forma": quitar_invisibles antes que
# normalizar_espacios, porque un \xa0 aislado no cuenta como espacio para
# str.strip() hasta que se convierte en uno.

from dataclasses import dataclass

import pandas as pd

from src.common import clave_canonica, es_faltante
from src.detectores import (
    CENTINELAS,
    INVISIBLES,
    PATRON_CODIGO,
    SOLO_PUNTUACION,
)

_INVISIBLES_PAT = "|".join(c for c in INVISIBLES)
_PUNTUACION_INICIO = r'^[^\w\s"\'(¿¡]+'
_PUNTUACION_FINAL = r"[.,;:\-]+$"

# igual en espiritu a detectores.SEPARADOR_MULTIPLE (que solo detecta con
# contains), pero con lookaround: ese usa "\d-\d" para detectar, y si se
# usara para PARTIR se comeria un digito de cada lado del guion. aca se
# separa en el guion sin consumir los digitos vecinos
_SEPARADOR_TELEFONO = r"[,/;]|\s-\s|(?<=\d)-(?=\d)"


# ---------------------------------------------------------------
# funciones de limpieza: serie de texto -> serie de texto (o dos series,
# cuando la regla necesita repartir una celda en mas de un campo)
# ---------------------------------------------------------------

# el \xa0 (y demas invisibles, ver detectores.INVISIBLES) casi siempre esta
# jugando el papel de un espacio normal, asi que se reemplaza por uno en vez
# de borrarlo: borrarlo pegaria "FOO\xa0BAR" en "FOOBAR"
def quitar_invisibles(serie):
    return serie.str.replace(_INVISIBLES_PAT, " ", regex=True)


# colapsa espacios internos multiples y quita los de borde
def normalizar_espacios(serie):
    return serie.str.replace(r"\s+", " ", regex=True).str.strip()


# mayusculiza. el dataset viene casi todo en mayusculas (formulario del
# portal); la minuscula suelta es el error, no el estandar
def normalizar_mayusculas(serie):
    return serie.str.upper()


# quita puntuacion suelta al inicio o al final ("01-" -> "01"). NO toca
# parentesis ni comillas: esos se resuelven aparte (ver
# detectores.detectar_delimitadores_desbalanceados), porque quitarlos a
# ciegas puede dejar un parentesis abierto sin su cierre. mismo criterio que
# detectores.PUNTUACION_BORDE, para no marcar como "sobrante" algo que la
# deteccion anterior considera legitimo
def quitar_puntuacion_borde(serie):
    v = serie.str.replace(_PUNTUACION_INICIO, "", regex=True)
    v = v.str.replace(_PUNTUACION_FINAL, "", regex=True)
    # strip final: al quitar un guion/punto de borde puede quedar el espacio
    # que lo precedia ("COSANFE -" -> "COSANFE "), y volveria a haber borde
    return v.str.strip()


# unifica bajo NA los vacios de verdad (es_faltante) y los centinelas de
# texto ("N/A", "SIN DATO", "---", ver detectores.CENTINELAS). asi hay una
# sola nocion de "no hay dato" para recalcular estadisticas de faltantes en
# vez de repartirlas entre "", "\xa0" y "N/A" como si fueran categorias
def normalizar_faltantes(serie):
    def es_nulo(valor):
        if es_faltante(valor):
            return True
        v = valor.strip().upper()
        return v in CENTINELAS or bool(SOLO_PUNTUACION.match(v))

    return serie.mask(serie.map(es_nulo), pd.NA)


# reemplaza variantes de escritura por su forma canonica. el mapa se recibe
# ya armado (ver mapa_categorias_dominantes) en vez de inferirse aca adentro,
# para que quede explicito que se esta aplicando y se pueda auditar
def unificar_categoria(serie, mapa):
    return serie.replace(mapa)


# construye el mapa {variante_minoritaria: valor_dominante} para pasarle a
# unificar_categoria. reproduce a mano la misma logica de agrupacion que
# detectores.detectar_categorias_duplicadas (variante mas frecuente gana,
# empate lo resuelve el orden alfabetico), para que el mapa y el hallazgo
# que lo justifica sean consistentes. duplicado a proposito en vez de
# importado: no se toco detectores.py
def mapa_categorias_dominantes(serie):
    v = serie[~serie.map(es_faltante)]
    claves = v.map(clave_canonica)

    v = v[claves != ""]
    claves = claves[claves != ""]
    if len(v) == 0:
        return {}

    grupos = pd.DataFrame({"valor": v.values, "clave": claves.values})
    conteo = grupos.value_counts(["clave", "valor"]).rename("n").reset_index()
    dominante = (
        conteo.sort_values(["n", "valor"], ascending=[False, True])
        .drop_duplicates("clave")
        .set_index("clave")["valor"]
    )

    return {
        valor: dominante[clave]
        for clave, valor in zip(grupos["clave"], grupos["valor"])
        if valor != dominante[clave]
    }


# CODIGO es la llave del establecimiento (dd-dd-dddd-dd). solo se limpia el
# espacio de borde antes de comparar contra el patron oficial; si no calza
# no se inventa un valor nuevo, se deja el original para revision manual
def normalizar_codigo(serie):
    v = serie.str.strip()
    valido = v.str.fullmatch(PATRON_CODIGO)
    return v.where(valido, serie)


# deja solo digitos. si el resultado no queda en 8 digitos NO se fuerza: se
# devuelve el original, para que quede marcado como pendiente de revision
# manual en vez de "arreglado" a algo que parece valido pero no lo es
def normalizar_telefono(serie):
    solo_digitos = serie.str.replace(r"\D", "", regex=True)
    valido = solo_digitos.str.fullmatch(r"\d{8}")
    return solo_digitos.where(valido, serie)


# separa celdas de telefono con mas de un numero ("12345678, 87654321") en
# el primero (telefono principal) y el resto (para no perder informacion, se
# guarda en una columna aparte). devuelve (primero, resto)
def separar_telefono_multivalor(serie):
    partes = serie.str.split(_SEPARADOR_TELEFONO, n=1, regex=True)
    primero = partes.str[0].str.strip()
    resto = partes.str[1].fillna("").str.strip()

    valido = primero.str.fullmatch(r"\d{8}")
    primero = primero.where(valido, serie)

    return primero, resto


# variable derivada TELEFONO_2 (actividad 5i): cuando la celda traia mas de un
# numero, el segundo queda aqui en vez de perderse. reusa la funcion de arriba
# para no repetir la logica de separacion. queda "" cuando solo habia un numero
def derivar_telefono_2(serie):
    _, resto = separar_telefono_multivalor(serie)
    return resto


# ---------------------------------------------------------------
# estrategia de limpieza: que regla aplica a cada variable, por que y con
# que riesgo. esto es el "plan de limpieza" de la actividad 4 de la guia.
# las reglas se prueban y se miden (ver estrategia.py), pero no se aplican
# de forma definitiva aca: eso lo decide el equipo con esta tabla como
# insumo.
# ---------------------------------------------------------------

@dataclass(frozen=True)
class Regla:
    variable: str
    problema: str
    transformacion: str   # nombre legible, para las tablas de salida
    funcion: object        # callable: serie -> serie transformada
    justificacion: str
    riesgo: str


@dataclass(frozen=True)
class RevisionManual:
    variable: str
    problema: str
    justificacion: str
    riesgo: str


# texto libre: nombres propios (establecimiento, direccion, supervisor,
# director). se limpia la FORMA (espacios, invisibles) pero se es mas
# cauteloso con mayusculas/puntuacion que en las categoricas
TEXTO_LIBRE = ("ESTABLECIMIENTO", "DIRECCION", "SUPERVISOR", "DIRECTOR")

# categoricas y llaves geograficas: el portal las manda en mayusculas, la
# minuscula suelta es la excepcion
MAYUSCULAS_ESPERADAS = (
    "DEPARTAMENTO", "MUNICIPIO", "NIVEL", "SECTOR", "AREA", "STATUS",
    "MODALIDAD", "JORNADA", "PLAN", "DEPARTAMENTAL",
)

# todo lo que es texto (le aplican forma + mayusculas + puntuacion)
TEXTO = MAYUSCULAS_ESPERADAS + TEXTO_LIBRE

# el universo completo de variables (17, igual que profiler.CRITICIDAD):
# ademas de TEXTO estan las llaves con formato propio, que llevan su propia
# regla en vez de mayusculas/puntuacion genericas
TODAS_LAS_VARIABLES = TEXTO + ("CODIGO", "TELEFONO", "DISTRITO")


def _reglas_faltantes():
    return [
        Regla(
            variable=v,
            problema="faltantes representados de formas distintas (celda vacia, \\xa0, N/A, NULL, ---, etc.)",
            transformacion="normalizar_faltantes",
            funcion=normalizar_faltantes,
            justificacion=(
                "unifica bajo un solo NA para que las estadisticas de faltantes "
                "y los conteos de valores unicos no queden "
                "repartidos entre '', '\\xa0' y 'N/A' como si fueran categorias distintas"
            ),
            riesgo=(
                "un centinela puede ser ambiguo: '0' esta en la lista de centinelas "
                "(detectores.CENTINELAS) pero podria ser un valor real en una variable "
                "numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos"
            ),
        )
        for v in TODAS_LAS_VARIABLES
    ]


def _reglas_forma():
    reglas = []
    for v in TODAS_LAS_VARIABLES:
        reglas.append(Regla(
            variable=v,
            problema="caracteres invisibles (nbsp, tabs, saltos de linea, etc.)",
            transformacion="quitar_invisibles",
            funcion=quitar_invisibles,
            justificacion=(
                "no se ven en pantalla pero rompen comparaciones exactas y "
                "agrupaciones: dos 'COBAN' con y sin \\xa0 cuentan como categorias distintas"
            ),
            riesgo="bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas",
        ))
        reglas.append(Regla(
            variable=v,
            problema="espacios al inicio/final o multiples espacios internos",
            transformacion="normalizar_espacios",
            funcion=normalizar_espacios,
            justificacion="mismo motivo: 'COBAN' y 'COBAN ' no deberian contar como valores distintos",
            riesgo="minimo; un espacio interno multiple casi nunca es intencional en este dataset",
        ))
    return reglas


def _reglas_mayusculas():
    reglas = []
    for v in TEXTO:
        if v in TEXTO_LIBRE:
            riesgo = (
                "mas alto que en las categoricas: son nombres propios (ej. "
                "ESTABLECIMIENTO), y el enunciado pide conservar la ortografia; "
                "mayusculizar no cambia letras pero SI pierde cualquier estilizacion "
                "de mayusculas que fuera intencional (poco probable, pero no se puede "
                "verificar solo con la columna)"
            )
        else:
            riesgo = "bajo: son categoricas de dominio cerrado, casi todo el dataset ya viene en mayusculas"
        reglas.append(Regla(
            variable=v,
            problema="mayusculas inconsistentes",
            transformacion="normalizar_mayusculas",
            funcion=normalizar_mayusculas,
            justificacion="unifica bajo la convencion dominante del dataset (mayusculas) para que 'guatemala' y 'GUATEMALA' no cuenten como categorias distintas",
            riesgo=riesgo,
        ))
    return reglas


def _reglas_puntuacion():
    return [
        Regla(
            variable=v,
            problema="puntuacion sobrante al inicio o final",
            transformacion="quitar_puntuacion_borde",
            funcion=quitar_puntuacion_borde,
            justificacion="quita restos de puntuacion que no aportan informacion ('01-' -> '01'), preservando parentesis y comillas legitimas (ver detectores.detectar_delimitadores_desbalanceados)",
            riesgo="bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre",
        )
        for v in TEXTO
    ]


def _reglas_codigo():
    return [Regla(
        variable="CODIGO",
        problema="codigo fuera del patron dd-dd-dddd-dd",
        transformacion="normalizar_codigo",
        funcion=normalizar_codigo,
        justificacion="normaliza solo el espacio de borde antes de comparar contra el patron oficial; si el codigo no calza no se inventa uno nuevo",
        riesgo="CODIGO es la llave del establecimiento: forzar un formato sin verificar el valor real podria mezclar dos establecimientos o dejar uno sin identificador valido; los que no calcen quedan para revision manual, no se tocan",
    )]


def _reglas_telefono():
    return [
        Regla(
            variable="TELEFONO",
            problema="telefono con mas de un numero en la celda",
            transformacion="separar_telefono_multivalor",
            funcion=lambda s: separar_telefono_multivalor(s)[0],
            justificacion="se queda con el primer numero de la celda como telefono principal; el resto no se descarta (deberia guardarse en una columna TELEFONO_2, ver riesgo)",
            riesgo="el 'primer numero' es una convencion arbitraria y podria no ser el principal; el numero descartado tiene que guardarse aparte para no perder informacion, no solo botarse",
        ),
        Regla(
            variable="TELEFONO",
            problema="telefono fuera de formato (no son 8 digitos)",
            transformacion="normalizar_telefono",
            funcion=normalizar_telefono,
            justificacion="quita separadores y espacios que no deberian estar en un numero de telefono; si tras limpiarlo no quedan 8 digitos no se fuerza el formato",
            riesgo="un telefono con una letra de mas ('12345678A') podria quedar en 8 digitos 'validos' por coincidencia sin que el numero real sea correcto; una regla de formato no puede detectar eso",
        ),
    ]


ESTRATEGIA = (
    _reglas_faltantes()
    + _reglas_forma()
    + _reglas_mayusculas()
    + _reglas_puntuacion()
    + _reglas_codigo()
    + _reglas_telefono()
)


# a diferencia de las anteriores, la regla de categorias duplicadas necesita
# ver los datos primero (el mapa depende de cual variante es la dominante).
# por eso no vive en ESTRATEGIA como una regla estatica: estrategia.py la
# arma llamando esta funcion sobre el dataframe que este probando
def reglas_categorias(df):
    reglas = []
    for variable in MAYUSCULAS_ESPERADAS:
        if variable not in df.columns:
            continue
        mapa = mapa_categorias_dominantes(df[variable])
        if not mapa:
            continue
        reglas.append(Regla(
            variable=variable,
            problema="categoria duplicada por escritura (mayusculas, tildes o espacios distintos para el mismo valor)",
            transformacion="unificar_categoria",
            funcion=lambda serie, mapa=mapa: unificar_categoria(serie, mapa),
            justificacion="agrupa variantes de escritura de la misma categoria bajo la forma mas frecuente, para no contar 'GUATEMALA' y 'Guatemala' como valores distintos",
            riesgo="el mapa se calcula sobre la muestra actual; con el dataset completo la variante 'dominante' puede cambiar, hay que recalcularlo sobre los datos finales antes de aplicarlo de verdad",
        ))
    return reglas


# problemas que se detectan pero DELIBERADAMENTE no tienen una regla
# automatica: el riesgo de corregir mal es mayor que el de dejarlos
# pendientes de revision manual
REVISION_MANUAL = [
    RevisionManual(
        variable="DEPARTAMENTO",
        problema="valor fuera del catalogo oficial (ver profiler.detectar_fuera_de_catalogo)",
        justificacion="el catalogo tiene solo 23 valores; cualquier variante nueva es o un typo o un valor invalido, y son pocos casos como para automatizar el mapeo con confianza",
        riesgo="autocorregir a ciegas por similitud de texto podria asignar un establecimiento al departamento equivocado; se revisa a mano contra profiling/valores_problematicos.csv",
    ),
    RevisionManual(
        variable="MUNICIPIO",
        problema="valor fuera del catalogo de su departamento (hay nombres homonimos en mas de un departamento)",
        justificacion="mismo motivo que DEPARTAMENTO, agravado porque el municipio solo es valido dentro de su departamento (ej. TACTIC en ALTA VERAPAZ)",
        riesgo="un mapeo automatico por similitud de texto podria reasignar un municipio homonimo al departamento equivocado",
    ),
    RevisionManual(
        variable="ESTABLECIMIENTO",
        problema="posibles typos entre nombres de establecimiento (ver profiler.detectar_typos_establecimiento)",
        justificacion="rapidfuzz ya senala los pares candidatos; fusionarlos automaticamente es el riesgo mas alto de todo el dataset",
        riesgo="dos establecimientos legitimos y distintos pueden tener nombres parecidos (ej. dos sedes de un mismo colegio); fusionarlos sin revisar perderia un registro real",
    ),
]

# ---------------------------------------------------------------
# aplicación completa de la estrategia de limpieza
# ---------------------------------------------------------------

def aplicar_limpieza(df):
    """
    Aplica todas las reglas de limpieza sobre un dataframe.

    Devuelve:

        dataframe_limpio
        registro_transformaciones

    El orden de aplicación sigue exactamente ESTRATEGIA.
    """

    df_limpio = df.copy()

    transformaciones = []

    def medir_cambios(original, resultado):
        ambos_na = original.isna() & resultado.isna()
        distintos = (original != resultado) & ~ambos_na
        return int(distintos.sum())

    # -----------------------------------------------------------
    # reglas principales
    # -----------------------------------------------------------

    for regla in ESTRATEGIA:

        if regla.variable not in df_limpio.columns:
            continue

        original = df_limpio[regla.variable]

        resultado = regla.funcion(original)

        cambios = medir_cambios(original, resultado)

        df_limpio[regla.variable] = resultado

        if cambios:

            transformaciones.append({

                "variable": regla.variable,

                "problema_detectado": regla.problema,

                "transformacion": regla.transformacion,

                "registros_afectados": cambios,

                "justificacion": regla.justificacion,

            })

    # -----------------------------------------------------------
    # categorías
    # -----------------------------------------------------------

    for regla in reglas_categorias(df_limpio.fillna("")):

        original = df_limpio[regla.variable]

        resultado = regla.funcion(original)

        cambios = medir_cambios(original, resultado)

        df_limpio[regla.variable] = resultado

        if cambios:

            transformaciones.append({

                "variable": regla.variable,

                "problema_detectado": regla.problema,

                "transformacion": regla.transformacion,

                "registros_afectados": cambios,

                "justificacion": regla.justificacion,

            })

    # -----------------------------------------------------------
    # variable derivada
    # -----------------------------------------------------------

    if "TELEFONO" in df_limpio.columns:

        # se deriva del TELEFONO ORIGINAL (df), no del ya limpiado: para este
        # punto separar_telefono_multivalor ya recorto la celda al primer
        # numero, asi que el segundo solo sigue disponible en el crudo
        df_limpio["TELEFONO_2"] = derivar_telefono_2(
            df["TELEFONO"]
        )

    registro = pd.DataFrame(

        transformaciones,

        columns=[
            "variable",
            "problema_detectado",
            "transformacion",
            "registros_afectados",
            "justificacion",
        ],

    )

    return df_limpio, registro
