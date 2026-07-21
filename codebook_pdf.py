# convierte profiling/codebook.md a pdf, para el entregable que pide el PDF
# del proyecto ("archivo pdf con el libro de codigos"). el markdown sigue
# siendo la fuente de verdad; este script solo lo empaqueta para entregar.

from pathlib import Path

import markdown
from xhtml2pdf import pisa

ORIGEN = Path("profiling") / "codebook.md"
DESTINO = Path("profiling") / "codebook.pdf"

ESTILO = """
<style>
    @page { size: letter landscape; margin: 1.5cm; }
    body { font-family: Helvetica, sans-serif; font-size: 9pt; color: #1a1a1a; }
    h1 { color: #1a6b3c; font-size: 18pt; border-bottom: 2px solid #1a6b3c; padding-bottom: 6px; }
    h2 { color: #1a6b3c; font-size: 13pt; margin-top: 18px; }
    table { width: 100%; border-collapse: collapse; margin: 8px 0 14px 0; }
    th { background-color: #1a6b3c; color: white; padding: 4px 6px; text-align: left; font-size: 8pt; }
    td { padding: 4px 6px; border-bottom: 1px solid #cccccc; font-size: 8pt; }
    tr:nth-child(even) { background-color: #f2f7f4; }
    code { background-color: #eeeeee; padding: 1px 3px; font-family: Courier, monospace; }
    hr { border: none; border-top: 1px solid #cccccc; margin: 12px 0; }
    p { margin: 6px 0; }
</style>
"""


def generar():
    texto = ORIGEN.read_text(encoding="utf-8")
    cuerpo = markdown.markdown(texto, extensions=["tables"])
    html = f"<html><head>{ESTILO}</head><body>{cuerpo}</body></html>"

    with open(DESTINO, "wb") as salida:
        resultado = pisa.CreatePDF(html, dest=salida, encoding="utf-8")

    if resultado.err:
        raise RuntimeError(f"no se pudo generar el pdf ({resultado.err} errores)")

    print(f"generado: {DESTINO.resolve()}")


if __name__ == "__main__":
    generar()
