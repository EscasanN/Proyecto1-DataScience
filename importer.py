from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd

INPUT_DIR = Path("files")
OUTPUT_DIR = Path("clean_files")
OUTPUT_DIR.mkdir(exist_ok=True)

todos = []

for archivo in INPUT_DIR.glob("*.xls"):

    print(f"Procesando {archivo.name}...")

    try:

        # Leer el HTML
        with open(archivo, encoding="cp1252", errors="ignore") as f:
            html = f.read()

        soup = BeautifulSoup(html, "lxml")

        # Buscar la tabla correcta
        tabla = soup.find("table", id="_ctl0_ContentPlaceHolder1_dgResultado")

        if tabla is None:
            print("No se encontró la tabla.")
            continue

        filas = tabla.find_all("tr")

        datos = []

        for fila in filas:
            celdas = fila.find_all("td")

            if not celdas:
                continue

            datos.append([
                td.get_text(strip=True)
                for td in celdas
            ])

        # Primera fila = encabezados
        encabezados = datos[0]
        registros = datos[1:]

        df = pd.DataFrame(registros, columns=encabezados)

        # Eliminar filas completamente vacías
        df = df.replace("", pd.NA).dropna(how="all").fillna("")

        # Guardar CSV individual
        salida = OUTPUT_DIR / f"{archivo.stem}.csv"

        df.to_csv(
            salida,
            index=False,
            encoding="utf-8-sig"
        )

        todos.append(df)

        print(f"   {len(df)} registros")

    except Exception as e:
        print(f"Error: {e}")

# Unir todos los departamentos
if todos:

    datos_completos = pd.concat(todos, ignore_index=True)

    datos_completos.to_csv(
        OUTPUT_DIR / "datos_completos.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\nTotal de registros: {len(datos_completos)}")

else:
    print("No se procesó ningún archivo.")