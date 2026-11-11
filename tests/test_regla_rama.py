#!/usr/bin/env python3
"""Ejecuta la regla de rama contra un `gh` falso.

El contrato de `test_actions.py` lee texto y no habría visto el fallo que
importa: una llamada mal formada a `ejecutar` deja el repositorio sin regla
después de haber quitado la anterior. Aquí se recorre el camino completo
—listar, crear y actualizar— con un `gh` de mentira que no toca GitHub.
"""

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "actions" / "regla-rama" / "regla_rama.py"

FALSO = """#!/usr/bin/env bash
set -euo pipefail
registro="${GH_FALSO_REGISTRO}"
printf '%s\\n' "$*" >> "$registro"
if [[ "$*" == *"--method POST"* || "$*" == *"--method PUT"* ]]; then
  cat > /dev/null
  echo '{"id": 7, "name": "main"}'
  exit 0
fi
if [[ "$*" == *"rulesets/7"* ]]; then
  echo '{"id":7,"name":"main","enforcement":"active","bypass_actors":[],
  "rules":[{"type":"deletion"},{"type":"non_fast_forward"},
  {"type":"pull_request","parameters":{"allowed_merge_methods":["squash"]}},
  {"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"Pruebas"}]}},
  {"type":"required_linear_history"}]}'
  exit 0
fi
echo "${GH_FALSO_REGLAS:-[]}"
"""


def ejecutar(script, path, registro, reglas):
    entorno = dict(os.environ)
    entorno["PATH"] = f"{path}:{entorno['PATH']}"
    entorno["GH_FALSO_REGISTRO"] = str(registro)
    entorno["GH_FALSO_REGLAS"] = reglas
    return subprocess.run(
        [sys.executable, str(SCRIPT), *script],
        capture_output=True, text=True, env=entorno, check=False,
    )


def main():
    with tempfile.TemporaryDirectory() as carpeta:
        temporal = Path(carpeta)
        falso = temporal / "gh"
        falso.write_text(FALSO, encoding="utf-8")
        falso.chmod(falso.stat().st_mode | stat.S_IEXEC)
        registro = temporal / "registro.txt"
        registro.touch()

        errores = []

        crear = ejecutar(
            ["--repo", "duenio/repo", "--check", "Pruebas"], temporal, registro, "[]",
        )
        if crear.returncode != 0:
            errores.append(f"crear: salida {crear.returncode}: {crear.stderr.strip()}")
        llamadas = registro.read_text(encoding="utf-8")
        if "--method POST" not in llamadas:
            errores.append("crear: no se llamó a POST del ruleset")

        registro.write_text("", encoding="utf-8")
        actualizar = ejecutar(
            ["--repo", "duenio/repo", "--check", "Pruebas"], temporal, registro,
            '[{"id": 7, "name": "main", "target": "branch", "enforcement": "active"}]',
        )
        if actualizar.returncode != 0:
            errores.append(
                f"actualizar: salida {actualizar.returncode}: {actualizar.stderr.strip()}"
            )
        if "--method PUT" not in registro.read_text(encoding="utf-8"):
            errores.append("actualizar: un ruleset existente debe ir por PUT")

        sin_checks = ejecutar(["--repo", "duenio/repo"], temporal, registro, "[]")
        if sin_checks.returncode != 2:
            errores.append("sin checks: debería salir con 2 y no tocar nada")

        forma = ejecutar(["--repo", "sin/forma!x", "--check", "a"], temporal, registro, "[]")
        if forma.returncode != 2:
            errores.append("repositorio mal formado: debería salir con 2")

    if errores:
        for error in errores:
            print(f"FALLO: {error}")
        return 1
    print("Regla de rama: contrato de ejecución OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
