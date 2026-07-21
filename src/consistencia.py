# consistencia entre variables (actividad 5h): revisa que los valores de
# distintas columnas no se contradigan. NO corrige nada, solo reporta las
# filas contradictorias para revision manual, porque adivinar cual de las dos
# columnas esta mal es justo lo que no se puede hacer con seguridad.
#
# se apoya en dos relaciones verificadas sobre los datos crudos:
#   1. los primeros 2 digitos de CODIGO identifican el departamento (1:1)
#   2. el par (DEPARTAMENTO, MUNICIPIO) tiene que existir en el catalogo oficial
#
# ojo: DISTRITO NO codifica el departamento (usa otra numeracion, ej "25-000"),
# asi que no se usa para esta verificacion.

import pandas as pd

from src.common import clave_canonica, es_faltante

# codigo oficial de departamento -> nombre, como lo devuelve el portal del
# mineduc. es un catalogo de referencia fijo (23 valores), igual que el de
# municipios. los dos primeros digitos de CODIGO deben mapear aca
CODIGO_DEPARTAMENTO = {
    "00": "CIUDAD CAPITAL", "01": "GUATEMALA", "02": "EL PROGRESO",
    "03": "SACATEPEQUEZ", "04": "CHIMALTENANGO", "05": "ESCUINTLA",
    "06": "SANTA ROSA", "07": "SOLOLA", "08": "TOTONICAPAN",
    "09": "QUETZALTENANGO", "10": "SUCHITEPEQUEZ", "11": "RETALHULEU",
    "12": "SAN MARCOS", "13": "HUEHUETENANGO", "14": "QUICHE",
    "15": "BAJA VERAPAZ", "16": "ALTA VERAPAZ", "17": "PETEN",
    "18": "IZABAL", "19": "ZACAPA", "20": "CHIQUIMULA",
    "21": "JALAPA", "22": "JUTIAPA",
}


# filas donde el prefijo de CODIGO no corresponde al DEPARTAMENTO escrito.
# se compara por clave canonica para que una tilde o espacio no cuente como
# contradiccion (eso es un problema de escritura, no de consistencia)
def codigo_vs_departamento(df):
    esperado = df["CODIGO"].str[:2].map(CODIGO_DEPARTAMENTO)

    contradice = (
        esperado.notna()
        & ~df["DEPARTAMENTO"].map(es_faltante)
        & (df["DEPARTAMENTO"].map(clave_canonica) != esperado.map(lambda x: clave_canonica(x) if isinstance(x, str) else x))
    )

    fuera = df.loc[contradice, ["CODIGO", "DEPARTAMENTO"]].copy()
    fuera["departamento_segun_codigo"] = esperado[contradice]
    return fuera


# filas donde el par (DEPARTAMENTO, MUNICIPIO) no existe en el catalogo. el
# municipio solo es valido dentro de su departamento: hay homonimos (LA
# LIBERTAD esta en Peten y en Huehuetenango), por eso se valida el par y no
# el municipio suelto
def municipio_vs_departamento(df, catalogo):
    validos = {
        (clave_canonica(d), clave_canonica(m))
        for d, m in zip(catalogo["DEPARTAMENTO"], catalogo["MUNICIPIO"])
    }

    presente = ~df["MUNICIPIO"].map(es_faltante) & ~df["DEPARTAMENTO"].map(es_faltante)
    fuera_par = df.apply(
        lambda f: presente[f.name]
        and (clave_canonica(f["DEPARTAMENTO"]), clave_canonica(f["MUNICIPIO"])) not in validos,
        axis=1,
    )

    return df.loc[fuera_par, ["DEPARTAMENTO", "MUNICIPIO"]].copy()


# corre las dos verificaciones y devuelve un reporte unico con una fila por
# contradiccion encontrada (variables, valores y el conteo)
def revisar_consistencia(df, catalogo):
    filas = []

    cod = codigo_vs_departamento(df)
    for _, f in cod.iterrows():
        filas.append({
            "tipo": "CODIGO vs DEPARTAMENTO",
            "detalle": f"CODIGO {f['CODIGO']} es de {f['departamento_segun_codigo']}, pero dice {f['DEPARTAMENTO']}",
        })

    mun = municipio_vs_departamento(df, catalogo)
    for _, f in mun.iterrows():
        filas.append({
            "tipo": "MUNICIPIO vs DEPARTAMENTO",
            "detalle": f"{f['MUNICIPIO']} no pertenece a {f['DEPARTAMENTO']} segun el catalogo",
        })

    return pd.DataFrame(filas, columns=["tipo", "detalle"])
