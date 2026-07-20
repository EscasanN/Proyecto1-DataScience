# main.py -- orquesta el pipeline completo del proyecto.
#
# Aplica de verdad la limpieza que limpieza.py solo proponia y estrategia.py
# solo media (actividad 5), corre consistencia entre variables (5h) y
# deduplicacion (5g), exporta el csv limpio y el informe de calidad
# antes/despues (actividad 6 y 8). Este modulo orquesta y hace i/o; no
# redefine logica que ya vive en limpieza.py / detectores.py / consistencia.py
# / dedup.py / calidad.py.
#
# ORDEN DEL PIPELINE (importa):
#   1. cargar datos crudos + catalogo oficial
#   2. limpiar formato y faltantes de TODAS las variables (5a-5f)
#   3. crear la variable derivada TELEFONO_2 (5i)
#   4. revisar consistencia entre variables (5h) -- solo reporta, no corrige
#   5. deduplicar -- AL FINAL. Si corriera antes de limpiar texto, dos filas
#      identicas salvo un espacio de mas no se verian como duplicado exacto
#      (duplicated() compara byte a byte, no por clave canonica)
#   6. exportar establecimientos_limpios.csv
#   7. metricas + informe de calidad antes/despues
#   8. validacion automatica del conjunto limpio (actividad 7)
#
# Nada de esto elimina filas ni "arregla" valores ambiguos a ciegas: eso
# sigue siendo revision manual (ver output/revision_manual.csv y
# plan_limpieza.md SS5).

from pathlib import Path

import pandas as pd

import calidad
import consistencia
import dedup
from calidad import COLUMNAS_TRANSFORMACIONES
from catalogo import obtener as obtener_catalogo
from detectores import PATRON_CODIGO, detectar_categorias_duplicadas
from estrategia import medir_impacto
from limpieza import (
    ESTRATEGIA,
    MAYUSCULAS_ESPERADAS,
    TEXTO,
    TODAS_LAS_VARIABLES,
    normalizar_codigo,
    normalizar_telefono,
    reglas_categorias,
    separar_telefono_multivalor,
)
from profiler import detectar_fuera_de_catalogo, detectar_typos_establecimiento

ARCHIVO_CRUDO = "raw_files/datos_crudos_completos.csv"
ARCHIVO_LIMPIO = "establecimientos_limpios.csv"
OUTPUT_DIR = Path("output")

# lookup (variable, transformacion) -> Regla, para no repetir en este
# archivo la prosa (problema/justificacion/riesgo) que ya vive en
# limpieza.ESTRATEGIA / plan_limpieza.md. main.py decide el ORDEN de
# aplicacion (ver _limpiar); el contenido de cada regla sigue siendo de
# limpieza.py
_REGLAS_POR_LLAVE = {(r.variable, r.transformacion): r for r in ESTRATEGIA}


# ---------------------------------------------------------------
# carga de datos (con respaldo sintetico si no hay internet / csv crudo)
# ---------------------------------------------------------------

# catalogo chico pero real: mismos codigos de departamento que
# consistencia.CODIGO_DEPARTAMENTO, con un homonimo real (LA LIBERTAD existe
# en PETEN y en HUEHUETENANGO) para poder probar esa regla tambien
def construir_catalogo_demo():
    filas = [
        ("GUATEMALA", "MIXCO"), ("GUATEMALA", "VILLA NUEVA"),
        ("ALTA VERAPAZ", "COBAN"), ("ALTA VERAPAZ", "TACTIC"),
        ("PETEN", "LA LIBERTAD"), ("HUEHUETENANGO", "LA LIBERTAD"),
    ]
    return pd.DataFrame(filas, columns=["DEPARTAMENTO", "MUNICIPIO"])


# reproduce, en miniatura, cada tipo de problema que el resto del proyecto ya
# sabe detectar (ver test_profiler.py / test_consistencia.py / test_dedup.py),
# para poder correr el pipeline completo -- incluida deduplicacion y
# consistencia -- sin depender de la descarga real del portal
def construir_dataset_demo():
    filas = [
        # fila 0 y 1: identicas en contenido real, pero NO byte-a-byte antes
        # de limpiar (espacio de borde + minuscula + \xa0 interno). el
        # enunciado pide que dedup corra AL FINAL justo por este caso: si
        # duplicated() corriera sobre el crudo, no las vería iguales.
        dict(CODIGO="01-01-0001-46", DISTRITO="01-001", DEPARTAMENTO="GUATEMALA",
             MUNICIPIO="MIXCO", ESTABLECIMIENTO="INSTITUTO NACIONAL DE MIXCO",
             DIRECCION="5a. AVENIDA 3-45 ZONA 1", TELEFONO="24567890",
             SUPERVISOR="JUAN PEREZ", DIRECTOR="ANA GARCIA", NIVEL="DIVERSIFICADO",
             SECTOR="OFICIAL", AREA="URBANA", STATUS="ABIERTA", MODALIDAD="MONOLINGUE",
             JORNADA="MATUTINA", PLAN="DIARIO(REGULAR)", DEPARTAMENTAL="GUATEMALA NORTE"),
        dict(CODIGO="01-01-0001-46", DISTRITO="01-001", DEPARTAMENTO="GUATEMALA",
             MUNICIPIO="MIXCO", ESTABLECIMIENTO="INSTITUTO NACIONAL DE MIXCO ",
             DIRECCION="5a. AVENIDA 3-45 ZONA 1", TELEFONO="24567890",
             SUPERVISOR="JUAN\xa0PEREZ", DIRECTOR="ANA GARCIA", NIVEL="DIVERSIFICADO",
             SECTOR="oficial", AREA="URBANA", STATUS="ABIERTA", MODALIDAD="MONOLINGUE",
             JORNADA="MATUTINA", PLAN="DIARIO(REGULAR)", DEPARTAMENTAL="GUATEMALA NORTE"),

        # fila 2 y 3: posible duplicado PARCIAL (typo en el nombre), mismo
        # departamento/municipio, CODIGO distinto -> lo detecta dedup por
        # similitud, no por igualdad exacta
        dict(CODIGO="01-02-0003-46", DISTRITO="01-002", DEPARTAMENTO="GUATEMALA",
             MUNICIPIO="VILLA NUEVA", ESTABLECIMIENTO="COLEGIO EVANGELICO BETHESDA",
             DIRECCION="0 CALLE 0-00 ZONA 5", TELEFONO="45678901",
             SUPERVISOR="MARIA LOPEZ", DIRECTOR="PEDRO RUIZ", NIVEL="DIVERSIFICADO",
             SECTOR="PRIVADO", AREA="URBANA", STATUS="ABIERTA", MODALIDAD="MONOLINGUE",
             JORNADA="VESPERTINA", PLAN="DIARIO(REGULAR)", DEPARTAMENTAL="GUATEMALA SUR"),
        dict(CODIGO="01-02-0004-46", DISTRITO="01-002", DEPARTAMENTO="GUATEMALA",
             MUNICIPIO="VILLA NUEVA", ESTABLECIMIENTO="COLEGIO EVANGELICO BETESDA",
             DIRECCION="0 CALLE 0-00 ZONA 5", TELEFONO="45678902",
             SUPERVISOR="MARIA LOPEZ", DIRECTOR="PEDRO RUIZ", NIVEL="DIVERSIFICADO",
             SECTOR="PRIVADO", AREA="URBANA", STATUS="ABIERTA", MODALIDAD="MONOLINGUE",
             JORNADA="VESPERTINA", PLAN="DIARIO(REGULAR)", DEPARTAMENTAL="GUATEMALA SUR"),

        # fila 4: telefono multivalor + codigo fuera de patron (queda para
        # revision manual, no se inventa un valor)
        dict(CODIGO="16010137", DISTRITO="16-001", DEPARTAMENTO="ALTA VERAPAZ",
             MUNICIPIO="COBAN", ESTABLECIMIENTO="INSTITUTO INTERCULTURAL",
             DIRECCION="ZONA 1 COBAN", TELEFONO="78208583-78209143",
             SUPERVISOR="LUIS SOTO", DIRECTOR="---", NIVEL="DIVERSIFICADO",
             SECTOR="OFICIAL", AREA="RURAL", STATUS="ABIERTA", MODALIDAD="BILINGUE",
             JORNADA="MATUTINA", PLAN="DIARIO(REGULAR)", DEPARTAMENTAL="ALTA VERAPAZ"),

        # fila 5: bien formada, sirve de control
        dict(CODIGO="16-02-0005-46", DISTRITO="16-002", DEPARTAMENTO="ALTA VERAPAZ",
             MUNICIPIO="TACTIC", ESTABLECIMIENTO='COLEGIO "LA INMACULADA"',
             DIRECCION="ZONA 2 TACTIC", TELEFONO="79112233",
             SUPERVISOR="ROSA DIAZ", DIRECTOR="CARLOS LOPEZ", NIVEL="DIVERSIFICADO",
             SECTOR="PRIVADO", AREA="URBANA", STATUS="ABIERTA", MODALIDAD="MONOLINGUE",
             JORNADA="DOBLE", PLAN="FIN DE SEMANA", DEPARTAMENTAL="ALTA VERAPAZ"),

        # fila 6: CODIGO dice PETEN (17) pero DEPARTAMENTO escrito dice
        # HUEHUETENANGO -> contradiccion CODIGO vs DEPARTAMENTO. MUNICIPIO
        # "LA LIBERTAD" SI es valido bajo HUEHUETENANGO en el catalogo, para
        # que esta fila no dispare TAMBIEN la regla de municipio y se pueda
        # ver cada contradiccion por separado
        dict(CODIGO="17-01-0006-46", DISTRITO="17-001", DEPARTAMENTO="HUEHUETENANGO",
             MUNICIPIO="LA LIBERTAD", ESTABLECIMIENTO="INED LA LIBERTAD",
             DIRECCION="ZONA 1", TELEFONO="55667788",
             SUPERVISOR="ELENA RUIZ", DIRECTOR="MARIO GOMEZ", NIVEL="DIVERSIFICADO",
             SECTOR="OFICIAL", AREA="RURAL", STATUS="ABIERTA", MODALIDAD="MONOLINGUE",
             JORNADA="MATUTINA", PLAN="DIARIO(REGULAR)", DEPARTAMENTAL="PETEN"),

        # fila 7: DEPARTAMENTO valido (ALTA VERAPAZ) pero MUNICIPIO "LA
        # LIBERTAD" no pertenece a ese departamento (es homonimo de otro) ->
        # contradiccion MUNICIPIO vs DEPARTAMENTO
        dict(CODIGO="16-03-0007-46", DISTRITO="16-003", DEPARTAMENTO="ALTA VERAPAZ",
             MUNICIPIO="LA LIBERTAD", ESTABLECIMIENTO="ESCUELA RURAL MIXTA",
             DIRECCION="ALDEA EL PROGRESO", TELEFONO="59001122",
             SUPERVISOR="JORGE MARTINEZ", DIRECTOR="SILVIA PEREZ", NIVEL="DIVERSIFICADO",
             SECTOR="OFICIAL", AREA="RURAL", STATUS="ABIERTA", MODALIDAD="BILINGUE",
             JORNADA="MATUTINA", PLAN="DIARIO(REGULAR)", DEPARTAMENTAL="ALTA VERAPAZ"),

        # fila 8: DEPARTAMENTO fuera del catalogo por completo (no existe)
        dict(CODIGO="99-01-0008-46", DISTRITO="99-001", DEPARTAMENTO="XELAJU",
             MUNICIPIO="COBAN", ESTABLECIMIENTO="COLEGIO SAN JOSE",
             DIRECCION="ZONA 3", TELEFONO="41234567",
             SUPERVISOR="ANA TORRES", DIRECTOR="LUIS RAMIREZ", NIVEL="DIVERSIFICADO",
             SECTOR="OFICIAL", AREA="URBANA", STATUS="ABIERTA", MODALIDAD="MONOLINGUE",
             JORNADA="VESPERTINA", PLAN="DIARIO(REGULAR)", DEPARTAMENTAL="ALTA VERAPAZ"),

        # fila 9: faltantes de varias formas (centinela, \xa0 solo)
        dict(CODIGO="01-03-0009-46", DISTRITO="01-003", DEPARTAMENTO="GUATEMALA",
             MUNICIPIO="MIXCO", ESTABLECIMIENTO="LICEO GUATEMALA",
             DIRECCION="ZONA 7", TELEFONO="",
             SUPERVISOR="\xa0", DIRECTOR="N/A", NIVEL="DIVERSIFICADO",
             SECTOR="OFICIAL", AREA="URBANA", STATUS="ABIERTA", MODALIDAD="MONOLINGUE",
             JORNADA="NOCTURNA", PLAN="DIARIO(REGULAR)", DEPARTAMENTAL="GUATEMALA NORTE"),

        # fila 10: telefono con letra de mas, no se puede corregir con
        # certeza -> queda para revision manual
        dict(CODIGO="01-04-0010-46", DISTRITO="01-004", DEPARTAMENTO="GUATEMALA",
             MUNICIPIO="VILLA NUEVA", ESTABLECIMIENTO="INSTITUTO TECNICO",
             DIRECCION="ZONA 4.", TELEFONO="1234567A",
             SUPERVISOR="RENE CASTRO", DIRECTOR="PATRICIA LEON", NIVEL="DIVERSIFICADO",
             SECTOR="MUNICIPAL", AREA="URBANA", STATUS="CERRADA TEMPORALMENTE",
             MODALIDAD="MONOLINGUE", JORNADA="MATUTINA", PLAN="DIARIO(REGULAR)",
             DEPARTAMENTAL="GUATEMALA SUR"),
    ]
    return pd.DataFrame(filas)


def cargar_crudo():
    ruta = Path(ARCHIVO_CRUDO)
    if ruta.exists():
        return pd.read_csv(ruta, dtype=str, keep_default_na=False), "datos crudos completos"

    print(f"aviso: no se encontro {ARCHIVO_CRUDO} en este entorno.")
    print("se usa un dataset sintetico de demostracion (mismo esquema, 11 filas)")
    print("que ejercita cada regla del pipeline; con el csv real, este mismo")
    print("main.py corre igual, solo cambia el origen de los datos.\n")
    return construir_dataset_demo(), "dataset sintetico de demostracion"


def cargar_catalogo():
    try:
        return obtener_catalogo()
    except Exception as e:
        print(f"aviso: no se pudo obtener el catalogo oficial ({e!r}).")
        print("se usa un catalogo sintetico de demostracion.\n")
        return construir_catalogo_demo()


# ---------------------------------------------------------------
# limpieza aplicada de verdad (actividad 5). aplica las funciones puras de
# limpieza.py sobre el DataFrame completo, en el orden que garantiza
# resultados correctos (ver notas en limpieza.py y el chequeo de \s vs
# invisibles hecho antes de escribir esto), y arma el registro de
# transformaciones que pide la actividad 6.
# ---------------------------------------------------------------

def _aplicar_regla(df, regla, registro):
    casos, resultado = medir_impacto(df[regla.variable], regla.funcion)
    df[regla.variable] = resultado
    if casos:
        registro.append({
            "variable": regla.variable,
            "problema_detectado": regla.problema,
            "transformacion": regla.transformacion,
            "registros_afectados": casos,
            "justificacion": regla.justificacion,
        })
    return casos


def _limpiar_telefono(df, registro):
    original = df["TELEFONO"].copy()
    primero, resto = separar_telefono_multivalor(original)

    ambos_nulos = original.isna() & primero.isna()
    casos_multivalor = int(((original != primero) & ~ambos_nulos).sum())
    if casos_multivalor:
        r = _REGLAS_POR_LLAVE[("TELEFONO", "separar_telefono_multivalor")]
        registro.append({
            "variable": "TELEFONO", "problema_detectado": r.problema,
            "transformacion": r.transformacion, "registros_afectados": casos_multivalor,
            "justificacion": r.justificacion,
        })

    casos_formato, telefono_final = medir_impacto(primero, normalizar_telefono)
    df["TELEFONO"] = telefono_final
    if casos_formato:
        r = _REGLAS_POR_LLAVE[("TELEFONO", "normalizar_telefono")]
        registro.append({
            "variable": "TELEFONO", "problema_detectado": r.problema,
            "transformacion": r.transformacion, "registros_afectados": casos_formato,
            "justificacion": r.justificacion,
        })

    # variable derivada (actividad 5i): el segundo numero no se descarta,
    # queda en su propia columna. derivar_telefono_2 hace exactamente este
    # split (ver test_consistencia.test_derivar_telefono_2); se reutiliza el
    # resultado de separar_telefono_multivalor de arriba en vez de llamarla
    # de nuevo para no recalcular lo mismo dos veces
    df["TELEFONO_2"] = resto
    creados = int((resto != "").sum())
    if creados:
        registro.append({
            "variable": "TELEFONO_2",
            "problema_detectado": "variable derivada: TELEFONO traia mas de un numero en la celda",
            "transformacion": "derivar_telefono_2",
            "registros_afectados": creados,
            "justificacion": (
                "actividad 5i: se crea para no perder el segundo numero cuando "
                "TELEFONO traia mas de uno (ver plan_limpieza.md SS2.2); util para "
                "quien necesite un telefono alterno de contacto del establecimiento"
            ),
        })


def limpiar(df):
    df = df.copy()
    registro = []

    # 1-2: forma. quitar_invisibles ANTES que normalizar_espacios: un
    # \xa0 aislado ya lo trata \s como espacio (se probo antes de escribir
    # esto), pero otros invisibles (zero-width, joiners, BOM) NO, y quedarian
    # pegados a la palabra vecina si el orden fuera al reves.
    for variable in TODAS_LAS_VARIABLES:
        _aplicar_regla(df, _REGLAS_POR_LLAVE[(variable, "quitar_invisibles")], registro)
        _aplicar_regla(df, _REGLAS_POR_LLAVE[(variable, "normalizar_espacios")], registro)

    # 3-4: mayusculas y puntuacion de borde, solo en texto (TEXTO =
    # categoricas/geograficas + texto libre; CODIGO/TELEFONO/DISTRITO llevan
    # su propia regla de formato, no esta)
    for variable in TEXTO:
        _aplicar_regla(df, _REGLAS_POR_LLAVE[(variable, "normalizar_mayusculas")], registro)
        _aplicar_regla(df, _REGLAS_POR_LLAVE[(variable, "quitar_puntuacion_borde")], registro)

    # 5: faltantes. va DESPUES de limpiar forma para que un centinela con
    # espacios o invisibles alrededor (" n/a ", "n/a\xa0") tambien se detecte
    for variable in TODAS_LAS_VARIABLES:
        _aplicar_regla(df, _REGLAS_POR_LLAVE[(variable, "normalizar_faltantes")], registro)

    # 6: categorias duplicadas por escritura. SOLO en categoricas/geograficas
    # cerradas (MAYUSCULAS_ESPERADAS) -- en texto libre no se aplica (ver
    # plan_limpieza.md SS3: la variante mas frecuente podria ser la mal
    # escrita, y unificar destruiria la ortografia correcta). se calcula
    # sobre el dataset YA limpio de forma, para que el mapa sea el definitivo
    for regla in reglas_categorias(df):
        _aplicar_regla(df, regla, registro)

    # 7: CODIGO (formato especifico, no se inventan valores)
    _aplicar_regla(df, _REGLAS_POR_LLAVE[("CODIGO", "normalizar_codigo")], registro)

    # 8: TELEFONO + variable derivada TELEFONO_2
    _limpiar_telefono(df, registro)

    columnas = list(df.columns)
    if "TELEFONO_2" in columnas:
        # colocarla justo despues de TELEFONO, no al final, para que el csv
        # se lea en un orden logico
        columnas.remove("TELEFONO_2")
        columnas.insert(columnas.index("TELEFONO") + 1, "TELEFONO_2")
        df = df[columnas]

    registro_df = pd.DataFrame(registro, columns=COLUMNAS_TRANSFORMACIONES)
    return df, registro_df


# ---------------------------------------------------------------
# revision manual (actividad 5g/5f): consolida, en un solo reporte, los
# casos que el plan de limpieza decidio a proposito NO autocorregir. no
# modifica el dataframe.
# ---------------------------------------------------------------

def revisar_manual(df, catalogo):
    filas = []

    for h in detectar_fuera_de_catalogo(df, catalogo):
        filas.append({"tipo": h.variable, "detalle": h.problema, "casos": h.casos, "ejemplo": h.ejemplo})

    for h in detectar_typos_establecimiento(df):
        filas.append({"tipo": h.variable, "detalle": h.problema, "casos": h.casos, "ejemplo": h.ejemplo})

    presente = ~df["TELEFONO"].isna()
    valido = df["TELEFONO"].str.fullmatch(r"\d{8}").astype("boolean").fillna(False)
    invalidos = df.loc[presente & ~valido, "TELEFONO"]
    if len(invalidos):
        filas.append({
            "tipo": "TELEFONO", "detalle": "no quedo en 8 digitos tras la limpieza",
            "casos": int(len(invalidos)), "ejemplo": repr(invalidos.iloc[0]),
        })

    presente = ~df["CODIGO"].isna()
    valido = df["CODIGO"].str.fullmatch(PATRON_CODIGO).astype("boolean").fillna(False)
    invalidos = df.loc[presente & ~valido, "CODIGO"]
    if len(invalidos):
        filas.append({
            "tipo": "CODIGO", "detalle": "no calza con el patron dd-dd-dddd-dd",
            "casos": int(len(invalidos)), "ejemplo": repr(invalidos.iloc[0]),
        })

    return pd.DataFrame(filas, columns=["tipo", "detalle", "casos", "ejemplo"])


# ---------------------------------------------------------------
# validacion automatica del conjunto limpio (actividad 7)
# ---------------------------------------------------------------

def validar(df, catalogo):
    """
    Corre los chequeos que pide la actividad 7. Devuelve una tabla con una
    fila por chequeo: los que la limpieza garantiza SIEMPRE (por
    construccion, ver limpieza.py) son duros -- si fallan, es un bug de
    integracion. Los que dependen del contenido real de los datos (formato
    de telefono, catalogo, categorias en texto libre) son informativos: se
    reportan, no se fuerzan a cero, porque el proyecto decidio no
    autocorregir/no eliminar a ciegas (ver plan_limpieza.md SS3 y SS5).
    """
    filas = []

    def agregar(chequeo, ok, detalle, duro):
        filas.append({"chequeo": chequeo, "ok": bool(ok), "detalle": detalle, "tipo": "duro" if duro else "informativo"})

    sin_borde = all(
        (df[c].dropna() == df[c].dropna().str.strip()).all()
        for c in TODAS_LAS_VARIABLES if c in df.columns
    )
    agregar("sin espacios al inicio/final", sin_borde, "garantizado por normalizar_espacios sobre todas las variables", duro=True)

    exactos = dedup.cantidad_duplicados_exactos(df)
    agregar("sin duplicados exactos", exactos == 0, f"{exactos} fila(s) en output/duplicados_exactos.csv (no se eliminan solas)", duro=False)

    presente = ~df["TELEFONO"].isna()
    valido = df["TELEFONO"].str.fullmatch(r"\d{8}").astype("boolean").fillna(False)
    malos = int((presente & ~valido).sum())
    agregar("telefonos en formato consistente", malos == 0, f"{malos} sin quedar en 8 digitos (ver output/revision_manual.csv)", duro=False)

    fuera = detectar_fuera_de_catalogo(df, catalogo)
    casos_catalogo = sum(h.casos for h in fuera)
    agregar("departamento/municipio en catalogo", casos_catalogo == 0, f"{casos_catalogo} fuera de catalogo (ver output/revision_manual.csv)", duro=False)

    categoricas_sucias = sum(
        len(detectar_categorias_duplicadas(df[c].fillna(""))) for c in MAYUSCULAS_ESPERADAS
    )
    agregar("categorias cerradas sin variantes de escritura", categoricas_sucias == 0,
            f"{categoricas_sucias} variable(s) categorica/geografica con variantes (se unifican automaticamente, no deberian quedar)", duro=True)

    return pd.DataFrame(filas)


# ---------------------------------------------------------------
# orquestacion
# ---------------------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    crudo, origen_datos = cargar_crudo()
    catalogo = cargar_catalogo()
    print(f"procesando {len(crudo):,} filas, {len(crudo.columns)} variables ({origen_datos})\n")

    print("aplicando limpieza sobre el dataset completo...")
    limpio, transformaciones = limpiar(crudo)

    print("revisando consistencia entre variables...")
    inconsistencias = consistencia.revisar_consistencia(limpio, catalogo)

    print("consolidando revision manual (catalogo, typos, formatos sin corregir)...")
    manual = revisar_manual(limpio, catalogo)

    # dedup AL FINAL: sobre el dataset YA limpio de texto, o dos filas
    # identicas salvo un espacio de mas no se detectan como duplicado exacto
    print("buscando duplicados (exactos y por similitud) sobre el dataset ya limpio...")
    duplicados_exactos = dedup.duplicados_exactos(limpio)
    posibles_duplicados = dedup.duplicados_parciales(limpio)
    transformaciones_dedup = dedup.exportar_transformaciones(limpio)
    transformaciones = pd.concat([transformaciones, transformaciones_dedup], ignore_index=True)
    transformaciones = calidad.generar_transformaciones(transformaciones)

    print("calculando metricas de calidad antes/despues...")
    metricas = calidad.generar_metricas(crudo, limpio)
    # calidad.py no incluye "Errores corregidos" porque depende del registro
    # de transformaciones, que se arma aca en main.py con datos de varios
    # modulos (limpieza + dedup); se agrega como fila aparte para completar
    # la tabla que pide la actividad 8
    total_corregidos = int(transformaciones["registros_afectados"].sum()) if not transformaciones.empty else 0
    metricas = pd.concat([
        metricas,
        pd.DataFrame([{"Métrica": "Errores corregidos", "Antes": "—", "Después": total_corregidos}]),
    ], ignore_index=True)

    print("validando el conjunto limpio...")
    validacion = validar(limpio, catalogo)

    # ------------------ escribir salidas ------------------

    limpio.to_csv(ARCHIVO_LIMPIO, index=False, encoding="utf-8-sig")

    transformaciones.to_csv(OUTPUT_DIR / "transformaciones.csv", index=False, encoding="utf-8-sig")
    metricas.to_csv(OUTPUT_DIR / "metricas.csv", index=False, encoding="utf-8-sig")
    inconsistencias.to_csv(OUTPUT_DIR / "consistencia.csv", index=False, encoding="utf-8-sig")
    manual.to_csv(OUTPUT_DIR / "revision_manual.csv", index=False, encoding="utf-8-sig")
    duplicados_exactos.to_csv(OUTPUT_DIR / "duplicados_exactos.csv", index=False, encoding="utf-8-sig")
    posibles_duplicados.to_csv(OUTPUT_DIR / "posibles_duplicados.csv", index=False, encoding="utf-8-sig")
    validacion.to_csv(OUTPUT_DIR / "validacion.csv", index=False, encoding="utf-8-sig")

    (OUTPUT_DIR / "informe_calidad.md").write_text(
        calidad.generar_informe_md(metricas, transformaciones) ,#+ _notas_adicionales(),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "informe_deduplicacion.md").write_text(
        dedup.generar_informe_md(limpio), encoding="utf-8"
    )

    # ------------------ resumen en pantalla ------------------

    print(f"\n{len(limpio):,} filas limpias -> {Path(ARCHIVO_LIMPIO).resolve()}")
    print(f"{len(transformaciones)} tipos de transformacion, {total_corregidos:,} celdas/filas afectadas en total")
    print(f"{len(inconsistencias)} inconsistencia(s) entre variables")
    print(f"{len(manual)} item(s) para revision manual")
    print(f"{len(duplicados_exactos)} filas en duplicados exactos, {len(posibles_duplicados)} posibles duplicados parciales")
    print("\nvalidacion del conjunto limpio:")
    print(validacion.to_string(index=False))
    print(f"\nsalidas en {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
