

from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

from src.catalogo import obtener as obtener_catalogo
from src.common import clave_canonica, es_faltante
from src.detectores import Hallazgo, analizar

ARCHIVO = "raw_files/datos_crudos_completos.csv"
OUTPUT_DIR = Path("profiling")

# umbral de similitud para sospechar typo entre dos nombres. 92 esta alto a
# proposito: preferimos pocos candidatos buenos a una lista larga de ruido.
UMBRAL_TYPO = 92

# que tanto duele que una variable venga sucia. las llaves de agrupacion
# parten el analisis si estan mal; un descriptivo sucio solo se ve feo.
CRITICIDAD = {
    "CODIGO": 3, "DEPARTAMENTO": 3, "MUNICIPIO": 3, "ESTABLECIMIENTO": 3,
    "DISTRITO": 2, "NIVEL": 2, "SECTOR": 2, "AREA": 2, "STATUS": 2,
    "MODALIDAD": 2, "JORNADA": 2, "PLAN": 2, "DEPARTAMENTAL": 2,
    "DIRECCION": 1, "TELEFONO": 1, "SUPERVISOR": 1, "DIRECTOR": 1,
}




# departamento/municipio que no aparecen en el catalogo del portal. se
# compara por clave canonica para no reportar diferencias de tildes, que ya
# las cubre categorias_duplicadas
def detectar_fuera_de_catalogo(df, cat):
    hallazgos = []

    validos_dep = {clave_canonica(x) for x in cat["DEPARTAMENTO"]}
    v = df["DEPARTAMENTO"][~df["DEPARTAMENTO"].map(es_faltante)]
    malos = v[~v.map(clave_canonica).isin(validos_dep)]
    hallazgos += _como_hallazgo("DEPARTAMENTO", malos, "departamento fuera del catalogo oficial")

    # el municipio se valida DENTRO de su departamento: TACTIC existe, pero
    # solo en alta verapaz. validar contra la lista plana dejaria pasar
    # municipios asignados al departamento equivocado.
    validos_mun = {
        (clave_canonica(d), clave_canonica(m))
        for d, m in zip(cat["DEPARTAMENTO"], cat["MUNICIPIO"])
    }
    pares = df[["DEPARTAMENTO", "MUNICIPIO"]][~df["MUNICIPIO"].map(es_faltante)]
    fuera = pares[[
        (clave_canonica(d), clave_canonica(m)) not in validos_mun
        for d, m in zip(pares["DEPARTAMENTO"], pares["MUNICIPIO"])
    ]]
    hallazgos += _como_hallazgo(
        "MUNICIPIO",
        fuera["MUNICIPIO"],
        "municipio fuera del catalogo de su departamento",
    )

    return hallazgos


def _como_hallazgo(variable, afectados, problema):
    if len(afectados) == 0:
        return []

    frec = afectados.value_counts()

    return [Hallazgo(
        variable=variable,
        problema=problema,
        casos=int(len(afectados)),
        ejemplo=repr(afectados.iloc[0]),
        valores=tuple((str(v), int(n)) for v, n in frec.items()),
    )]



# pares de nombres casi identicos dentro del mismo (departamento, municipio).
# el blocking no es solo velocidad: nombres parecidos en municipios distintos
# son escuelas distintas, no typos
def detectar_typos_establecimiento(df):
    v = df[~df["ESTABLECIMIENTO"].map(es_faltante)]
    pares_vistos = set()
    frec = {}

    for _, grupo in v.groupby(["DEPARTAMENTO", "MUNICIPIO"]):
        # se compara sobre la clave canonica: las diferencias de tildes o
        # espacios ya estan reportadas por otros detectores, aca buscamos
        # letras cambiadas de verdad.
        unicos = sorted({clave_canonica(x) for x in grupo["ESTABLECIMIENTO"]})

        for i, a in enumerate(unicos):
            for b in unicos[i + 1:]:
                if abs(len(a) - len(b)) > 5:
                    continue
                score = fuzz.ratio(a, b)
                if score >= UMBRAL_TYPO and (a, b) not in pares_vistos:
                    pares_vistos.add((a, b))
                    par = f"{a}  <->  {b}"
                    frec[par] = frec.get(par, 0) + 1

    if not frec:
        return []

    ordenados = sorted(frec.items(), key=lambda x: -x[1])

    return [Hallazgo(
        variable="ESTABLECIMIENTO",
        problema=f"posible typo entre nombres (similitud >= {UMBRAL_TYPO})",
        casos=len(frec),
        ejemplo=repr(ordenados[0][0]),
        valores=tuple(ordenados),
    )]


## priorizacion

def priorizar(hallazgos):
    filas = []

    for variable in CRITICIDAD:
        casos = sum(h.casos for h in hallazgos if h.variable == variable)
        problemas = sum(1 for h in hallazgos if h.variable == variable)
        filas.append({
            "variable": variable,
            "criticidad": CRITICIDAD[variable],
            "problemas_distintos": problemas,
            "casos": casos,
            "score": CRITICIDAD[variable] * casos,
        })

    tabla = pd.DataFrame(filas).sort_values("score", ascending=False)
    tabla["rank"] = range(1, len(tabla) + 1)
    return tabla


def tabla_hallazgos(hallazgos):
    return pd.DataFrame([{
        "variable": h.variable,
        "problema": h.problema,
        "casos": h.casos,
        "ejemplo": h.ejemplo,
    } for h in sorted(hallazgos, key=lambda x: -x.casos)])


def tabla_valores(hallazgos):
    return pd.DataFrame([
        {"variable": h.variable, "problema": h.problema, "valor": v, "frecuencia": n}
        for h in hallazgos
        for v, n in h.valores
    ])


DOMINIOS = {
    "CODIGO": "patron dd-dd-dddd-dd, unico por establecimiento",
    "DISTRITO": "patron dd-ddd",
    "DEPARTAMENTO": "catalogo oficial del portal (23 valores; el portal separa CIUDAD CAPITAL de GUATEMALA)",
    "MUNICIPIO": "catalogo oficial del portal, dependiente del departamento; hay 6 nombres homonimos en mas de un departamento (LA LIBERTAD, SAN JOSE, ...), agrupar siempre por el par",
    "ESTABLECIMIENTO": "texto libre; nombre propio, conserva ortografia y tildes",
    "DIRECCION": "texto libre",
    "TELEFONO": "8 digitos (numeracion nacional de guatemala)",
    "SUPERVISOR": "texto libre; nombre de persona",
    "DIRECTOR": "texto libre; nombre de persona",
    "NIVEL": "categorico: DIVERSIFICADO (fijado por el filtro de descarga)",
    "SECTOR": "categorico: OFICIAL, PRIVADO, MUNICIPAL, COOPERATIVA",
    "AREA": "categorico: URBANA, RURAL, SIN ESPECIFICAR",
    "STATUS": "categorico: ABIERTA, CERRADA TEMPORALMENTE, ...",
    "MODALIDAD": "categorico: MONOLINGUE, BILINGUE",
    "JORNADA": "categorico: MATUTINA, VESPERTINA, DOBLE, NOCTURNA, ...",
    "PLAN": "categorico: DIARIO(REGULAR), FIN DE SEMANA, ...",
    "DEPARTAMENTAL": "direccion departamental del mineduc (26 valores: guatemala se parte en 4, quiche en 2)",
}


def tabla_codebook(hallazgos):
    filas = []

    for variable in DOMINIOS:
        problemas = sorted({
            f"{h.problema} ({h.casos})"
            for h in hallazgos if h.variable == variable
        })
        filas.append({
            "variable": variable,
            "dominio_esperado": DOMINIOS[variable],
            "problemas_encontrados": "; ".join(problemas) if problemas else "ninguno",
        })

    return pd.DataFrame(filas)


def codebook_md(codebook, prioridad):
    lineas = [
        "# Code book — perfilado (persona 2)",
        "",
        "Dominio esperado y problemas detectados por variable, sobre los datos",
        "crudos (`raw_files/datos_crudos_completos.csv`, 11,867 filas). Nada esta",
        "corregido: la limpieza se decide con esta evidencia.",
        "",
        "| variable | dominio esperado | problemas encontrados |",
        "|---|---|---|",
    ]

    for _, f in codebook.iterrows():
        lineas.append(f"| {f['variable']} | {f['dominio_esperado']} | {f['problemas_encontrados']} |")

    lineas += [
        "",
        "## Prioridad de limpieza",
        "",
        "score = criticidad (3 llave de agrupacion, 2 categorica, 1 descriptiva) x casos.",
        "",
        "| rank | variable | casos | score |",
        "|---|---|---|---|",
    ]

    for _, f in prioridad.iterrows():
        lineas.append(f"| {f['rank']} | {f['variable']} | {f['casos']} | {f['score']} |")

    lineas += [
        "",
        "Detalle por valor en `valores_problematicos.csv`.",
        "",
    ]

    return "\n".join(lineas)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(ARCHIVO, dtype=str, keep_default_na=False)
    print(f"{len(df):,} filas, {len(df.columns)} columnas\n")

    print("corriendo detectores...")
    hallazgos = analizar(df)

    print("contrastando contra el catalogo oficial...")
    hallazgos += detectar_fuera_de_catalogo(df, obtener_catalogo())

    print("buscando posibles typos entre establecimientos...")
    hallazgos += detectar_typos_establecimiento(df)

    prioridad = priorizar(hallazgos)
    codebook = tabla_codebook(hallazgos)

    salidas = {
        "hallazgos.csv": tabla_hallazgos(hallazgos),
        "valores_problematicos.csv": tabla_valores(hallazgos),
        "prioridad.csv": prioridad,
        "codebook_p2.csv": codebook,
    }

    for nombre, tabla in salidas.items():
        tabla.to_csv(OUTPUT_DIR / nombre, index=False, encoding="utf-8-sig")

    (OUTPUT_DIR / "codebook_p2.md").write_text(
        codebook_md(codebook, prioridad), encoding="utf-8"
    )

    print(f"\n{len(hallazgos)} hallazgos, {sum(h.casos for h in hallazgos):,} casos\n")
    print(prioridad.to_string(index=False))
    print(f"\nsalidas en {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
