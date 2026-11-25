#!/usr/bin/env python3
"""Compone una página de muestra con la plantilla de la capa de identidad.

    python3 identidad/preview.py            # escribe identidad/preview/index.html
    python3 identidad/preview.py --check    # compone y valida sin escribir

La preview usa los mismos archivos que consume una web —CSS, plantilla, menú y
baldosa— y los referencia desde el directorio padre, sin copiarlos a
`_identidad/`. Sirve para ver la capa completa sin montar un sitio.

Solo biblioteca estándar.
"""

from __future__ import annotations

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from shell import Sitio  # noqa: E402  (mismo directorio)

CONTENIDO = """\
    <section id="perfil">
      <h1>Lorenzo Lanuza</h1>
      <p class="lead">Arquitectura de seguridad en la nube, DevSecOps y desarrollo .NET.</p>
      <p>La cabecera, el pie y los botones son de la capa de identidad. Esta página
      solo aporta contenido y comprueba que la plantilla se compone entera.</p>
      <p><a class="button button-quiet" href="#contenido">Ver el contenido</a>
      <span class="module-status status-validated">Validado</span></p>
    </section>
    <section id="contenido">
      <h2>Qué prueba</h2>
      <p>Que los marcadores se resuelven, que la navegación marca la página actual
      y que los recursos apuntan a los archivos del paquete.</p>
    </section>"""


def componer() -> str:
    """Devuelve el HTML de la preview compuesto con la plantilla del paquete."""
    sitio = Sitio(
        perfil="publica",
        estilos=("../identidad.css",),
        version=(AQUI / "VERSION").read_text(encoding="utf-8").strip(),
        repo="https://github.com/lanuzalorenzo/core",
        nota="Preview de la capa de identidad",
        recursos="..",
    )
    return sitio.pagina(
        titulo="Preview de la identidad",
        descripcion="Página de muestra compuesta con la plantilla de la capa de identidad.",
        canonical="https://example.org/preview/",
        nav=[
            ("#perfil", "Perfil"),
            {"grupo": "Recursos"},
            ("#contenido", "Contenido"),
        ],
        actual="index.html",
        inicio="#contenido",
        contenido=CONTENIDO,
    )


def validar(html: str) -> list[str]:
    """Comprueba que la preview está completa y apunta a los recursos del paquete."""
    fallos: list[str] = []
    if "{{" in html:
        fallos.append("quedan marcadores sin resolver")
    for pieza in ("<header", "<nav", "<footer", "../identidad.css", "../marca-tile.svg", "../menu.js"):
        if pieza not in html:
            fallos.append(f"falta {pieza}")
    return fallos


def main(argv: list[str]) -> int:
    if argv and argv != ["--check"]:
        raise SystemExit("uso: python3 identidad/preview.py [--check]")
    html = componer()
    fallos = validar(html)
    if fallos:
        for fallo in fallos:
            print(f"FALLO: {fallo}")
        return 1
    if argv == ["--check"]:
        print("OK: la preview se compone completa")
        return 0
    destino = AQUI / "preview" / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    print(f"OK: preview escrita en {destino.relative_to(AQUI.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
