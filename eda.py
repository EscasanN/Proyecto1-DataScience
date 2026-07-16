from pathlib import Path
import pandas as pd

# =====================================================
# CONFIGURACIÓN
# =====================================================

ARCHIVO = "clean_files/datos_completos.csv"

OUTPUT_DIR = Path("summary_tables")
OUTPUT_DIR.mkdir(exist_ok=True)

# =====================================================
# CARGAR DATOS
# =====================================================

print("=" * 70)
print("CARGANDO DATOS...")
print("=" * 70)

df = pd.read_csv(
    ARCHIVO,
    dtype=str,
    keep_default_na=True
)

print("Datos cargados correctamente.\n")

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

print(df.dtypes)

# =====================================================
# VALORES FALTANTES
# =====================================================

faltantes = df.isna().sum()

print("\n" + "=" * 70)
print("VALORES FALTANTES")
print("=" * 70)

print(faltantes)

# =====================================================
# VALORES ÚNICOS
# =====================================================

unicos = df.nunique(dropna=True)

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
    "Tipo": df.dtypes,
    "No nulos": df.notna().sum(),
    "Nulos": df.isna().sum(),
    "% Nulos": (df.isna().mean() * 100).round(2),
    "Valores únicos": df.nunique(dropna=True)
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
        .fillna("<<FALTANTE>>")
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