#!/usr/bin/env python3
"""Comprueba que el paquete de identidad está al día y es consumible.

    python3 identidad/verificar.py           # comprueba
    python3 identidad/verificar.py --update  # reescribe SHA256SUMS

Comprueba cuatro cosas: que la versión de `VERSION` es semver y aparece en la
cabecera de `identidad.css`, que las huellas de `SHA256SUMS` corresponden a los
cinco archivos que consume una web, que la preview se compone sin marcadores
pendientes y que el contenido no cambia sin subir la versión: compara con la
última etiqueta `identidad-v*` y falla si el manifiesto difiere con la misma
versión. En `--update`, el guardián se aplica antes de escribir `SHA256SUMS`, de
modo que una versión no publica contenido distinto dos veces.

Solo biblioteca estándar.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

PAQUETE = Path(__file__).resolve().parent

# Lo que consume una web: si cambia un byte, sube la versión.
MANIFIESTO = ("identidad.css", "plantilla.tpl", "shell.py", "menu.js", "marca-tile.svg")


def huella(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def sumas() -> str:
    return "".join(f"{huella(PAQUETE / nombre)}  {nombre}\n" for nombre in MANIFIESTO)


class EtiquetaIlegible(Exception):
    """Hay una etiqueta de identidad, pero su contenido no se puede leer."""


def publicada() -> tuple[str, str] | None:
    """Versión y `SHA256SUMS` de la última etiqueta `identidad-v*`, si existe."""
    def git(*argumentos: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                ["git", *argumentos],
                cwd=PAQUETE, capture_output=True, text=True, check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise EtiquetaIlegible(str(error)) from error

    if git("rev-parse", "--is-inside-work-tree").returncode != 0:
        return None
    etiquetas = git("tag", "--list", "identidad-v*", "--sort=-v:refname")
    if etiquetas.returncode != 0:
        raise EtiquetaIlegible(etiquetas.stderr.strip() or "git tag falló")
    if not etiquetas.stdout.strip():
        return None
    etiqueta = etiquetas.stdout.split()[0]
    version = git("show", f"{etiqueta}:identidad/VERSION")
    sumas = git("show", f"{etiqueta}:identidad/SHA256SUMS")
    if version.returncode != 0 or sumas.returncode != 0:
        raise EtiquetaIlegible(
            f"no se pudo leer {etiqueta}: {version.stderr.strip() or sumas.stderr.strip()}"
        )
    return version.stdout.strip(), sumas.stdout


def main(argv: list[str]) -> int:
    actualizar = "--update" in argv
    if not actualizar and argv:
        raise SystemExit("uso: python3 identidad/verificar.py [--update]")
    fallos: list[str] = []

    sys.path.insert(0, str(PAQUETE))
    import preview  # noqa: E402  (mismo directorio)

    version = (PAQUETE / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fallos.append(f"VERSION no es semver: {version!r}")

    css = (PAQUETE / "identidad.css").read_text(encoding="utf-8")
    if f"Versión {version}." not in css:
        fallos.append("identidad.css no declara la versión de VERSION")

    fallos += [f"preview: {fallo}" for fallo in preview.validar(preview.componer())]

    calculadas = sumas()
    fichero = PAQUETE / "SHA256SUMS"
    versionadas = fichero.read_text(encoding="utf-8") if fichero.exists() else ""

    # El guardián se aplica en las dos rutas y contra la última etiqueta, que es
    # lo que ve un consumidor: una versión no publica dos contenidos distintos.
    anterior = None
    try:
        anterior = publicada()
    except EtiquetaIlegible as error:
        fallos.append(f"no se pudo leer la última etiqueta de identidad: {error}")
    if anterior is not None and version == anterior[0] and calculadas != anterior[1]:
        fallos.append(
            "el contenido cambió pero VERSION sigue en "
            f"{version}: súbela en identidad/VERSION y regenera"
        )

    if fallos:
        for fallo in fallos:
            print(f"FALLO: {fallo}")
        return 1

    if actualizar:
        fichero.write_text(calculadas, encoding="utf-8")
        print(f"OK: SHA256SUMS actualizado para la versión {version}")
        return 0
    if calculadas != versionadas:
        print("FALLO: SHA256SUMS no corresponde: ejecuta `--update`")
        return 1
    print(f"OK: identidad {version} al día ({len(MANIFIESTO)} archivos)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
