#!/usr/bin/env python3
"""Sitio de ejemplo: compone páginas con la capa de identidad.

    python3 identidad/ejemplo/build.py           # escribe salida/
    python3 identidad/ejemplo/build.py --check   # compone sin escribir y valida

Es el punto de partida de una web nueva: `sitio.toml` declara el perfil, la nav
y las páginas; `paginas/` guarda el contenido de cada una; `shell.py` pone la
cabecera, el pie y los metadatos. Solo biblioteca estándar.
"""

from __future__ import annotations

import shutil
import sys
import tomllib
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SHELL = AQUI.parent
sys.path.insert(0, str(SHELL))

from shell import Sitio  # noqa: E402

# Lo que el sitio publica en `_identidad/`: el CSS, el menú y la baldosa.
RUNTIME = ("identidad.css", "menu.js", "marca-tile.svg")


def construir(pagina: dict, config: dict) -> str:
    sitio = Sitio(
        perfil=config.get("perfil", "publica"),
        raiz=config.get("raiz", ""),
        estilos=config.get("estilos", []),
        version=config.get("version", ""),
        repo=config.get("repo", ""),
        nota=config.get("nota", ""),
    )
    contenido = (AQUI / "paginas" / pagina["contenido"]).read_text(encoding="utf-8").strip("\n")
    campos = {
        "titulo": pagina["titulo"],
        "descripcion": pagina.get("descripcion", ""),
        "canonical": pagina.get("canonical", ""),
        "nav": [
            (item["href"], item["etiqueta"]) if "href" in item else item
            for item in config.get("nav", [])
        ],
        "actual": pagina["fichero"],
        "contenido": contenido,
    }
    if "inicio" in config:
        campos["inicio"] = config["inicio"]
    return sitio.pagina(**campos)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    config = tomllib.loads((AQUI / "sitio.toml").read_text(encoding="utf-8"))
    salida = AQUI / "salida"

    # Componer siempre: es lo que prueba que la plantilla, la nav y el perfil
    # encajan. En `--check` no se escribe nada.
    paginas = {pagina["fichero"]: construir(pagina, config) for pagina in config["paginas"]}
    if check:
        print(f"OK: el ejemplo compone ({len(paginas)} páginas)")
        return 0

    (salida / "_identidad").mkdir(parents=True, exist_ok=True)
    for nombre in RUNTIME:
        shutil.copyfile(SHELL / nombre, salida / "_identidad" / nombre)
    for fichero, html in paginas.items():
        (salida / fichero).write_text(html, encoding="utf-8")
    print(f"OK: ejemplo generado ({len(paginas)} páginas)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
