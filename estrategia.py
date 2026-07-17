# prototipo de limpieza: corre cada regla de limpieza.ESTRATEGIA
# sobre una COPIA de los datos, mide cuantos valores cambiaria y guarda la
# evidencia. NO modifica raw_files/ ni genera el dataset limpio final -- esa
# decision es del equipo, con esta tabla como insumo (actividad 4 de la
# guia, "plan de limpieza"). la limpieza definitiva (actividad 5) es un paso
# aparte, una vez el equipo revise y apruebe estas reglas.

from pathlib import Path

import pandas as pd

from limpieza import ESTRATEGIA, REVISION_MANUAL, reglas_categorias

ARCHIVO = "raw_files/datos_crudos_completos.csv"
OUTPUT_DIR = Path("profiling")

# tamano de la muestra para probar las reglas; None = usar todo el dataset
N_MUESTRA = 2000


# reproduce a mano los mismos problemas que detectores.py sabe encontrar
# (ver test_profiler.py), para poder probar cada regla aunque todavia no se
# tenga el csv real descargado en este entorno
def _muestra_sintetica():
    return pd.DataFrame({
        "CODIGO": ["16-01-0137-46", "16010137", " 16-01-0137-46 "],
        "DISTRITO": ["16-001", "16-001", "16-002"],
        "DEPARTAMENTO": ["GUATEMALA", "guatemala", "GUATEMALA "],
        "MUNICIPIO": ["COBAN", "COBAN", "COBAN"],
        "ESTABLECIMIENTO": [
            "INSTITUTO INTERCULTURAL",
            "INSTITUTO INTERCULTRUAL",        # typo real: NO lo corrige ninguna regla
            'COLEGIO "LA INMACULADA"',
        ],
        "DIRECCION": ["3a. CALLE 4-5 ZONA 1", "4A. CALLE  5-6 ZONA 1", "01-"],
        "TELEFONO": ["12345678", "1234567", "12345678, 87654321"],
        "SUPERVISOR": ["JUAN\xa0PEREZ", "MARIA LOPEZ", "---"],
        "DIRECTOR": ["ANA GARCIA", "N/A", "PEDRO  RUIZ"],
        "NIVEL": ["DIVERSIFICADO", "DIVERSIFICADO", "DIVERSIFICADO"],
        "SECTOR": ["OFICIAL", "oficial", "PRIVADO"],
        "AREA": ["URBANA", "URBANA", "RURAL"],
        "STATUS": ["ABIERTA", "ABIERTA", "ABIERTA"],
        "MODALIDAD": ["MONOLINGUE", "MONOLINGUE", "BILINGUE"],
        "JORNADA": ["MATUTINA", "MATUTINA", "VESPERTINA"],
        "PLAN": ["DIARIO(REGULAR)", "DIARIO(REGULAR)", "FIN DE SEMANA"],
        "DEPARTAMENTAL": ["GUATEMALA NORTE", "GUATEMALA NORTE", "GUATEMALA SUR"],
    })


def cargar_datos():
    ruta = Path(ARCHIVO)
    if ruta.exists():
        return pd.read_csv(ruta, dtype=str, keep_default_na=False), "datos crudos completos"

    print(f"aviso: no se encontro {ARCHIVO} en este entorno todavia.")
    print("se usa una muestra sintetica solo para probar que las reglas corren bien;")
    print("cuando el csv real este disponible, este mismo script se corre sobre el.\n")
    return _muestra_sintetica(), "muestra sintetica de demostracion"


# cuenta cuantas celdas cambiarian si se aplicara la regla, SIN aplicarla de
# verdad sobre df. pd.NA no es igual a si mismo con "!=", por eso se trata
# aparte del resto de comparaciones
def medir_impacto(serie, funcion):
    resultado = funcion(serie)
    ambos_nulos = serie.isna() & resultado.isna()
    distintos = (serie != resultado) & ~ambos_nulos
    return int(distintos.sum()), resultado


def probar_estrategia(df):
    filas_tabla = []
    filas_evidencia = []

    todas_las_reglas = list(ESTRATEGIA) + reglas_categorias(df)

    for regla in todas_las_reglas:
        if regla.variable not in df.columns:
            continue

        original = df[regla.variable]
        casos, resultado = medir_impacto(original, regla.funcion)

        filas_tabla.append({
            "variable": regla.variable,
            "problema": regla.problema,
            "transformacion": regla.transformacion,
            "justificacion": regla.justificacion,
            "riesgo": regla.riesgo,
            "casos_afectados_en_muestra": casos,
        })

        if casos:
            cambiadas = original[original != resultado].head(5)
            for idx in cambiadas.index:
                filas_evidencia.append({
                    "variable": regla.variable,
                    "transformacion": regla.transformacion,
                    "antes": repr(original.loc[idx]),
                    "despues": repr(resultado.loc[idx]),
                })

    for item in REVISION_MANUAL:
        filas_tabla.append({
            "variable": item.variable,
            "problema": item.problema,
            "transformacion": "ninguna: marcar para revision manual",
            "justificacion": item.justificacion,
            "riesgo": item.riesgo,
            "casos_afectados_en_muestra": "ver profiling/hallazgos.csv",
        })

    tabla = pd.DataFrame(filas_tabla).sort_values("variable").reset_index(drop=True)
    evidencia = pd.DataFrame(filas_evidencia)
    return tabla, evidencia


def codebook_md(tabla, origen, n_filas):
    lineas = [
        "# Code book — estrategia de limpieza",
        "",
        f"Reglas probadas sobre: {origen} ({n_filas:,} filas). Tratamiento",
        "propuesto por variable. NINGUNA de estas reglas esta aplicada de forma",
        "definitiva sobre `raw_files/datos_crudos_completos.csv`: son el plan de",
        "limpieza (actividad 4), medidas sobre una muestra para saber cuanto",
        "tocaria cada una antes de decidir aplicarla sobre el dataset completo.",
        "",
        "| variable | problema | transformación propuesta | riesgo |",
        "|---|---|---|---|",
    ]

    for _, f in tabla.iterrows():
        lineas.append(f"| {f['variable']} | {f['problema']} | {f['transformacion']} | {f['riesgo']} |")

    lineas += [
        "",
        "## Como leer `casos_afectados_en_muestra`",
        "",
        "Es el número de celdas que la regla tocaría en la muestra probada,",
        "NO en el dataset completo. Antes de aplicar una regla sobre",
        "`raw_files/datos_crudos_completos.csv` hay que volver a correr",
        "`estrategia.py` sobre los datos reales (quitando `N_MUESTRA` o",
        "subiéndolo al total de filas) para tener el número real de registros",
        "afectados.",
        "",
        "Detalle de antes/después en `evidencia_muestra.csv`.",
        "",
    ]

    return "\n".join(lineas)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    df, origen = cargar_datos()

    if N_MUESTRA and len(df) > N_MUESTRA:
        df_muestra = df.sample(N_MUESTRA, random_state=0)
        print(f"probando reglas sobre una muestra aleatoria de {N_MUESTRA} de {len(df):,} filas ({origen})\n")
    else:
        df_muestra = df
        print(f"probando reglas sobre: {origen} ({len(df_muestra)} filas)\n")

    tabla, evidencia = probar_estrategia(df_muestra)

    tabla.to_csv(OUTPUT_DIR / "estrategia_limpieza.csv", index=False, encoding="utf-8-sig")
    evidencia.to_csv(OUTPUT_DIR / "evidencia_muestra.csv", index=False, encoding="utf-8-sig")
    (OUTPUT_DIR / "codebook_p3.md").write_text(
        codebook_md(tabla, origen, len(df_muestra)), encoding="utf-8"
    )

    print(tabla[["variable", "problema", "casos_afectados_en_muestra"]].to_string(index=False))
    print(f"\nsalidas en {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
