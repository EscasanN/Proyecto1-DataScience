
from pathlib import Path

import pandas as pd

from src.downloader import (
    P,
    abrir_formulario,
    crear_sesion,
    listar_departamentos,
    seleccionar_departamento,
)

CACHE = Path("profiling") / "catalogo_municipios.csv"


def _municipios(sopa):
    combo = sopa.find("select", {"name": P + "cmbMunicipio"})
    if combo is None:
        return []

    return [
        o.get_text(strip=True)
        for o in combo.find_all("option")
        if o.get("value") not in (None, "TODOS")
    ]


# recorre los departamentos y junta sus municipios oficiales
def descargar():
    sesion = crear_sesion()
    filas = []

    for codigo, departamento in listar_departamentos(abrir_formulario(sesion)):
        sopa = seleccionar_departamento(sesion, abrir_formulario(sesion), codigo)
        municipios = _municipios(sopa)

        for municipio in municipios:
            filas.append({"DEPARTAMENTO": departamento, "MUNICIPIO": municipio})

        print(f"   [{codigo}] {departamento}: {len(municipios)} municipios")

    return pd.DataFrame(filas)


def obtener(refrescar=False):
    if CACHE.exists() and not refrescar:
        return pd.read_csv(CACHE, dtype=str, keep_default_na=False)

    print("descargando catalogo oficial del portal...")
    cat = descargar()

    CACHE.parent.mkdir(exist_ok=True)
    cat.to_csv(CACHE, index=False, encoding="utf-8-sig")

    return cat


if __name__ == "__main__":
    cat = obtener(refrescar=True)
    print(f"\n{len(cat)} municipios en {cat['DEPARTAMENTO'].nunique()} departamentos")
    print(f"guardado en {CACHE.resolve()}")
