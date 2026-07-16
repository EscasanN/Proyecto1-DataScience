from pathlib import Path
import pandas as pd

# =====================================================
# CONFIGURACIÓN
# =====================================================

ARCHIVO = "raw_files/datos_crudos_completos.csv"

OUTPUT_DIR = Path("summary_tables")
OUTPUT_DIR.mkdir(exist_ok=True)

# =====================================================
# CARGAR DATOS
# =====================================================

print("=" * 70)
print("CARGANDO DATOS...")
print("=" * 70)

# se lee todo como texto a proposito: asi no se pierden los ceros iniciales
# de telefonos ni el formato de CODIGO. keep_default_na=False para decidir
# nosotros que es faltante (ver abajo).
df = pd.read_csv(
    ARCHIVO,
    dtype=str,
    keep_default_na=False
)

print("Datos cargados correctamente.\n")

# =====================================================
# QUE CUENTA COMO FALTANTE
# =====================================================

# el portal manda los vacios como espacio duro (\xa0), no como celda vacia.
# pandas no los reconoce como NA, asi que si no los marcamos a mano el
# conteo de faltantes sale en cero y el diagnostico queda mal.

def es_faltante(valor):
    return valor.strip() == ""


faltante = df.apply(lambda col: col.map(es_faltante))


def tipo_inferido(columna):
    """que tipo tendria la variable si no viniera todo como texto del html"""
    valores = df.loc[~faltante[columna], columna].str.strip()

    if valores.empty:
        return "vacio"
    if valores.str.fullmatch(r"-?\d+").all():
        return "entero almacenado como texto"
    if valores.str.fullmatch(r"-?\d+([.,]\d+)?").all():
        return "numerico almacenado como texto"
    if valores.nunique() <= 20:
        return "categorico"
    return "texto"

# =====================================================
# INFORMACIÓN GENERAL
# =====================================================

print("=" * 70)
print("INFORMACIÓN GENERAL")
print("=" * 70)

print(f"Filas: {df.shape[0]:,}")
print(f"Columnas: {df.shape[1]}")

print("\nNombres de columnas:")
for c in df.columns:
    print(f" - {c}")

# =====================================================
# TIPOS DE DATOS
# =====================================================

print("\n" + "=" * 70)
print("TIPOS DE DATOS")
print("=" * 70)

# todo llega como texto porque se raspo de una tabla html. lo que interesa
# es el tipo que le corresponde, para detectar numeros guardados como texto.
tipos = pd.Series({c: tipo_inferido(c) for c in df.columns})

print(tipos.to_string())

# =====================================================
# VALORES FALTANTES
# =====================================================

faltantes = faltante.sum()

print("\n" + "=" * 70)
print("VALORES FALTANTES")
print("=" * 70)

print(faltantes)

# =====================================================
# VALORES ÚNICOS
# =====================================================

# se cuentan sin los faltantes, pero sin normalizar el texto: si hay
# categorias repetidas por escritura queremos que se noten aca.
unicos = pd.Series({
    c: df.loc[~faltante[c], c].nunique() for c in df.columns
})

print("\n" + "=" * 70)
print("VALORES ÚNICOS")
print("=" * 70)

print(unicos)

# =====================================================
# DUPLICADOS
# =====================================================

duplicados = df.duplicated().sum()

print("\n" + "=" * 70)
print("DUPLICADOS EXACTOS")
print("=" * 70)

print(duplicados)

# =====================================================
# MEMORIA
# =====================================================

print("\n" + "=" * 70)
print("USO DE MEMORIA")
print("=" * 70)

memoria = df.memory_usage(deep=True).sum() / (1024 ** 2)

print(f"{memoria:.2f} MB")

# =====================================================
# RESUMEN GENERAL
# =====================================================

resumen = pd.DataFrame({
    "Tipo inferido": tipos,
    "No nulos": (~faltante).sum(),
    "Nulos": faltantes,
    "% Nulos": (faltante.mean() * 100).round(2),
    "Valores únicos": unicos
})

resumen.to_csv(
    OUTPUT_DIR / "resumen_general.csv",
    encoding="utf-8-sig"
)

print("\nResumen general guardado.")

# =====================================================
# TABLAS DE FRECUENCIA
# =====================================================

print("\n" + "=" * 70)
print("GENERANDO TABLAS DE RESUMEN")
print("=" * 70)

for columna in df.columns:

    frecuencia = (
        df[columna]
        .mask(faltante[columna], "<<FALTANTE>>")
        .value_counts(dropna=False)
        .rename_axis(columna)
        .reset_index(name="Frecuencia")
    )

    frecuencia["Porcentaje"] = (
        frecuencia["Frecuencia"] / len(df) * 100
    ).round(2)

    nombre = columna.replace("/", "_").replace("\\", "_")

    frecuencia.to_csv(
        OUTPUT_DIR / f"{nombre}.csv",
        index=False,
        encoding="utf-8-sig"
    )

print("Tablas de frecuencia generadas.")

# =====================================================
# RESUMEN EN PANTALLA
# =====================================================

print("\n" + "=" * 70)
print("RESUMEN FINAL")
print("=" * 70)

print(f"Filas                : {len(df):,}")
print(f"Columnas             : {len(df.columns)}")
print(f"Duplicados exactos   : {duplicados}")
print(f"Memoria              : {memoria:.2f} MB")

print("\nValores faltantes:")

for col in df.columns:
    print(f"{col:20} {faltantes[col]}")

print("\nValores únicos:")

for col in df.columns:
    print(f"{col:20} {unicos[col]}")

print("\nProceso finalizado correctamente.")

print(f"\nLos archivos fueron guardados en la carpeta:")
print(OUTPUT_DIR.resolve())