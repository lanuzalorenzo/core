#!/usr/bin/env python3
"""Aplica la regla de rama común a un repositorio público.

Crea o actualiza un ruleset «main» con lo mismo que el resto de repositorios
del propietario: pull request obligatoria, checks en estricto, historial
lineal, sin borrado, sin force push y solo squash. Los checks los pone el
consumidor, porque son los suyos.

Es idempotente: si el ruleset existe, lo reemplaza con esta forma exacta.

Uso:
    regla_rama.py --repo lanuzalorenzo/comicteca --check "Pruebas" --check "Enlaces"
    regla_rama.py --check "Pruebas" --comprobar
    regla_rama.py --listar

Código de salida:
    0 = aplicada o sin cambios
    1 = hay un fallo al aplicar
    2 = error de entorno o de uso
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

NOMBRE = "main"


def ejecutar(
    *args: str,
    cwd: Path | None = None,
    entrada: str | None = None,
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            args, cwd=cwd, input=entrada, capture_output=True, text=True, check=False
        )
    except OSError as error:
        return subprocess.CompletedProcess(args, 127, "", str(error))


def remoto(cwd: Path) -> str | None:
    salida = ejecutar("git", "remote", "get-url", "origin", cwd=cwd)
    if salida.returncode != 0:
        return None
    coincidencia = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", salida.stdout.strip())
    return coincidencia.group(1) if coincidencia else None


def cuerpo(checks: list[str]) -> dict:
    return {
        "name": NOMBRE,
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 0,
                    "dismiss_stale_reviews_on_push": True,
                    "required_reviewers": [],
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_review_thread_resolution": False,
                    "allowed_merge_methods": ["squash"],
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "do_not_enforce_on_create": False,
                    "required_status_checks": [{"context": c} for c in checks],
                },
            },
            {"type": "required_linear_history"},
        ],
        "bypass_actors": [],
    }


def reglas(nwo: str) -> list[dict] | None:
    salida = ejecutar("gh", "api", f"repos/{nwo}/rulesets")
    if salida.returncode != 0:
        print(f"error: no se pudieron leer las reglas de {nwo}: {salida.stderr.strip()}",
              file=sys.stderr)
        return None
    try:
        return json.loads(salida.stdout)
    except json.JSONDecodeError:
        print("error: la respuesta de reglas no es JSON", file=sys.stderr)
        return None


def existente(nwo: str) -> int | None:
    conjuntos = reglas(nwo)
    if conjuntos is None:
        return None
    for conjunto in conjuntos:
        if conjunto.get("target") == "branch" and conjunto.get("name") == NOMBRE:
            return int(conjunto["id"])
    return 0


def enviar(nwo: str, datos: dict, identificador: int | None) -> bool:
    orden = ["gh", "api", "--method", "POST", f"repos/{nwo}/rulesets", "--input", "-"]
    if identificador:
        orden = [
            "gh", "api", "--method", "PUT",
            f"repos/{nwo}/rulesets/{identificador}", "--input", "-",
        ]
    salida = ejecutar(*orden, entrada=json.dumps(datos, ensure_ascii=False))
    if salida.returncode != 0:
        print(f"error: GitHub rechazó la regla: {salida.stderr.strip()}", file=sys.stderr)
        return False
    return True


def resumen(nwo: str) -> int:
    conjuntos = reglas(nwo)
    if conjuntos is None:
        return 1
    for conjunto in conjuntos:
        if conjunto.get("target") != "branch":
            continue
        detalle = ejecutar("gh", "api", f"repos/{nwo}/rulesets/{conjunto['id']}")
        if detalle.returncode != 0:
            print(f"error: no se pudo leer la regla {conjunto['name']}", file=sys.stderr)
            return 1
        datos = json.loads(detalle.stdout)
        tipos = [regla["type"] for regla in datos["rules"]]
        checks = next(
            (r["parameters"]["required_status_checks"] for r in datos["rules"]
             if r["type"] == "required_status_checks"),
            [],
        )
        print(f"{nwo}: regla «{datos['name']}» {datos['enforcement']}")
        print(f"  reglas: {', '.join(tipos)}")
        print(f"  checks: {len(checks)}")
        for check in checks:
            print(f"    - {check['context']}")
        print(f"  bypass: {datos.get('bypass_actors') or 'ninguno'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aplica la regla de rama común a un repositorio público.",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="owner/nombre; por defecto, el remoto origin del directorio actual.",
    )
    parser.add_argument(
        "--check",
        action="append",
        default=[],
        help="nombre de un check obligatorio; se puede repetir.",
    )
    parser.add_argument(
        "--comprobar",
        action="store_true",
        help="muestra lo que se aplicaría, sin tocar GitHub.",
    )
    parser.add_argument(
        "--listar",
        action="store_true",
        help="muestra las reglas del repositorio y sale.",
    )
    args = parser.parse_args()

    nwo = args.repo or remoto(Path.cwd())
    if not nwo:
        print("error: indica --repo owner/nombre", file=sys.stderr)
        return 2
    if re.fullmatch(r"[\w.-]+/[\w.-]+", nwo) is None:
        print(f"error: «{nwo}» no tiene forma owner/nombre", file=sys.stderr)
        return 2

    if args.listar:
        return resumen(nwo)

    if not args.check:
        print(
            "error: sin --check la regla no exigiría ninguna comprobación; "
            "se niega a aplicarla",
            file=sys.stderr,
        )
        return 2

    datos = cuerpo(args.check)
    if args.comprobar:
        print(json.dumps(datos, indent=2, ensure_ascii=False))
        return 0

    identificador = existente(nwo)
    if identificador is None:
        return 1
    if not enviar(nwo, datos, identificador or None):
        return 1
    print(f"{nwo}: regla «{NOMBRE}» {'actualizada' if identificador else 'creada'}")
    return resumen(nwo)


if __name__ == "__main__":
    raise SystemExit(main())
