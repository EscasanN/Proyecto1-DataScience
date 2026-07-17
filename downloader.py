# descarga los establecimientos de nivel diversificado de todo el pais desde
# el portal del mineduc y los guarda crudos en csv (uno por departamento mas
# el consolidado). el portal es asp.net webforms: hay que respetar el
# viewstate y hacer el postback del departamento antes de consultar

from datetime import datetime, timezone
from pathlib import Path
import json
import time

from bs4 import BeautifulSoup
import pandas as pd
import requests

URL = "https://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/"
OUTPUT_DIR = Path("raw_files")

# prefijo de los controles del formulario
P = "_ctl0:ContentPlaceHolder1:"
TABLA_ID = "_ctl0_ContentPlaceHolder1_dgResultado"

# el proyecto pide solo los que llegan hasta diversificado
NIVEL_DIVERSIFICADO = "46"

TIMEOUT = (15, 180)
REINTENTOS = 3
PAUSA = 1.0


def crear_sesion():
    s = requests.Session()
    # el portal responde distinto sin user-agent de navegador
    s.headers.update({"User-Agent": "Mozilla/5.0", "Referer": URL})
    return s


# saca los hidden (__VIEWSTATE, __EVENTVALIDATION, etc.) para reenviarlos
def leer_estado(sopa):
    return {
        i["name"]: i.get("value", "")
        for i in sopa.find_all("input", type="hidden")
        if i.get("name")
    }


def postear(sesion, datos):
    r = sesion.post(URL, data=datos, timeout=TIMEOUT)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")


def abrir_formulario(sesion):
    r = sesion.get(URL, timeout=TIMEOUT)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")


def listar_departamentos(sopa):
    combo = sopa.find("select", {"name": P + "cmbDepartamento"})
    return [
        (o["value"], o.get_text(strip=True))
        for o in combo.find_all("option")
        if o["value"] != "SELECCIONE UNO"
    ]


# dispara el autopostback del combo de departamento. hay que hacerlo si o si:
# la consulta directa la rechaza el eventvalidation con un 500
def seleccionar_departamento(sesion, sopa, codigo):
    datos = leer_estado(sopa)
    datos.update({
        "__EVENTTARGET": P + "cmbDepartamento",
        "__EVENTARGUMENT": "",
        P + "cmbDepartamento": codigo,
    })
    return postear(sesion, datos)


def consultar(sesion, sopa, codigo):
    datos = leer_estado(sopa)
    datos.update({
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        P + "cmbDepartamento": codigo,
        P + "cmbMunicipio": "TODOS",
        P + "cmbNivel": NIVEL_DIVERSIFICADO,
        P + "cmbSector": "TODOS",
        P + "ddlplan": "TODOS",
        P + "ddlModalidad": "TODOS",
        # es un imagebutton, necesita las coordenadas del click
        P + "IbtnConsultar.x": "10",
        P + "IbtnConsultar.y": "10",
    })
    return postear(sesion, datos)


# tabla html -> dataframe sin tocar el contenido. NO se hace strip: los
# espacios sobrantes y los \xa0 son parte del crudo y se detectan despues
def parsear_tabla(sopa):
    tabla = sopa.find("table", id=TABLA_ID)
    if tabla is None:
        return None

    filas = []
    for tr in tabla.find_all("tr"):
        celdas = tr.find_all("td")
        if not celdas:
            continue
        # la primera columna es el boton "escoger establecimiento", no es dato
        filas.append([td.get_text() for td in celdas[1:]])

    if len(filas) < 2:
        return None

    encabezados = [h.strip() for h in filas[0]]
    registros = filas[1:]

    # el grid cierra con una fila de relleno en blanco
    registros = [f for f in registros if any(c.strip() for c in f)]

    return pd.DataFrame(registros, columns=encabezados)


def bajar_departamento(sesion, codigo, nombre):
    for intento in range(1, REINTENTOS + 1):
        try:
            sopa = abrir_formulario(sesion)
            sopa = seleccionar_departamento(sesion, sopa, codigo)
            sopa = consultar(sesion, sopa, codigo)
            return parsear_tabla(sopa)
        except requests.RequestException as e:
            print(f"      intento {intento}/{REINTENTOS} fallo: {e}")
            if intento == REINTENTOS:
                raise
            time.sleep(PAUSA * intento)


def nombre_archivo(nombre):
    return nombre.lower().replace(" ", "_")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    sesion = crear_sesion()

    departamentos = listar_departamentos(abrir_formulario(sesion))
    print(f"departamentos en el portal: {len(departamentos)}\n")

    partes = []
    conteos = {}

    for codigo, nombre in departamentos:
        print(f"[{codigo}] {nombre}...")
        df = bajar_departamento(sesion, codigo, nombre)

        if df is None or df.empty:
            print("      sin resultados")
            conteos[nombre] = 0
            continue

        df.to_csv(
            OUTPUT_DIR / f"{nombre_archivo(nombre)}.csv",
            index=False,
            encoding="utf-8-sig",
        )
        partes.append(df)
        conteos[nombre] = len(df)
        print(f"      {len(df)} registros")
        time.sleep(PAUSA)

    if not partes:
        print("\nno se descargo nada")
        return

    completo = pd.concat(partes, ignore_index=True)
    completo.to_csv(
        OUTPUT_DIR / "datos_crudos_completos.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # metadatos que pide el libro de codigos (fecha de extraccion, fuente, etc.)
    meta = {
        "fuente": URL,
        "fecha_extraccion": datetime.now(timezone.utc).isoformat(),
        "filtro_nivel": "DIVERSIFICADO",
        "filtros_restantes": "TODOS",
        "departamentos": len(partes),
        "registros": len(completo),
        "variables": len(completo.columns),
        "registros_por_departamento": conteos,
    }
    (OUTPUT_DIR / "metadata_extraccion.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\ntotal: {len(completo)} registros, {len(completo.columns)} variables")
    print(f"guardado en {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
