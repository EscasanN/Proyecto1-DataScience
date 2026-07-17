# definiciones compartidas por eda.py y profiler.py: una sola nocion de
# faltante y de clave de agrupacion para que los diagnosticos no diverjan.
# sin i/o ni efectos secundarios al importar

import re
import unicodedata

_PUNTUACION = re.compile(r"[^\w\s]", flags=re.UNICODE)
_ESPACIOS = re.compile(r"\s+")


# vacio de verdad: el portal manda \xa0 y pandas no lo lee como NA, pero
# strip() si se lo come. los centinelas tipo "SIN DATO" van en detectores.py
def es_faltante(valor):
    return valor.strip() == ""


# descompone y bota los diacriticos. la enie tambien cae, ojo al usarla
def sin_tildes(valor):
    descompuesto = unicodedata.normalize("NFD", valor)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


# clave para agrupar variantes del mismo valor. es SOLO para comparar: el
# crudo nunca se reemplaza, el enunciado pide no destruir la ortografia
def clave_canonica(valor):
    v = sin_tildes(valor).upper()
    v = _PUNTUACION.sub(" ", v)
    return _ESPACIOS.sub(" ", v).strip()
