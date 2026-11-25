#!/usr/bin/env python3
"""Prueba `check-linea-base` contra repositorios de fixture.

No sale a Internet ni ejecuta CI: lanza el script de la acción sobre las
fixtures versionadas y fija el contrato de `action.yml`.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACTION = ROOT / "actions" / "check-linea-base"
SCRIPT = ACTION / "check_linea_base.py"
FIXTURES = ROOT / "tests" / "fixtures" / "linea-base"
errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run(fixture: str, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(FIXTURES / fixture), *extra],
        capture_output=True,
        text=True,
        check=False,
    )


def codes(output: str) -> set[str]:
    return set(re.findall(r"^ERROR (LB\d{3})", output, re.MULTILINE))


def check_pass(fixture: str) -> None:
    result = run(fixture)
    require(result.returncode == 0, f"{fixture}: se esperaba 0 y llegó {result.returncode}\n{result.stdout}{result.stderr}")
    require("0 hallazgos" in result.stdout, f"{fixture}: no termina con «0 hallazgos»\n{result.stdout}")


def check_broken() -> None:
    result = run("broken")
    require(result.returncode == 1, f"broken: se esperaba 1 y llegó {result.returncode}")
    expected = {
        "LB003",  # estado desconocido
        "LB005",  # Validado sin evidencia localizable
        "LB103",  # sin contents: read
        "LB104",  # write-all
        "LB106",  # acción sin versión fija
        "LB107",  # valor escrito en el YAML
        "LB108",  # sin Gitleaks
        "LB109",  # sin Dependabot
        "LB110",  # sin auto-merge
        "LB111",  # documentación sin check-links
        "LB112",  # dependencias sin Trivy
        "LB113",  # Dockerfile sin construir ni escanear
        "LB114",  # IaC sin revisar
        "LB115",  # Validado sin respaldo (sast y main)
    }
    found = codes(result.stdout)
    require(
        found == expected,
        f"broken: se esperaban {sorted(expected)} y llegaron {sorted(found)}\n{result.stdout}",
    )
    require(
        len(re.findall(r"^ERROR LB115", result.stdout, re.MULTILINE)) == 2,
        "broken: sast y main deben producir LB115",
    )


def variant(name: str, mutate, expected: set[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "repo"
        shutil.copytree(FIXTURES / "ok", root)
        mutate(root)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )
        wanted = 0 if not expected else 1
        require(result.returncode == wanted, f"{name}: se esperaba {wanted} y llegó {result.returncode}\n{result.stdout}")
        found = codes(result.stdout)
        require(found == expected, f"{name}: se esperaban {sorted(expected)} y llegaron {sorted(found)}\n{result.stdout}")


def check_variantes() -> None:
    def vacia(root: Path) -> None:
        (root / "AGENTS.md").write_text(
            "# Fixture\n\n## Línea base\n\n## Verificación\n", encoding="utf-8"
        )

    def sin_evidencia(root: Path) -> None:
        agents = root / "AGENTS.md"
        text = agents.read_text(encoding="utf-8")
        text = text.replace(
            "| `contenedor` | Parcial | Sin imagen publicada todavía. |",
            "| `contenedor` | Parcial | Sin imagen publicada todavía. |\n"
            "| `vacio` | Validado | |",
        )
        agents.write_text(text, encoding="utf-8")

    def duplicado(root: Path) -> None:
        agents = root / "AGENTS.md"
        text = agents.read_text(encoding="utf-8")
        text = text.replace(
            "| `contenedor` | Parcial | Sin imagen publicada todavía. |",
            "| `contenedor` | Parcial | Sin imagen publicada todavía. |\n"
            "| `secretos` | Parcial | Segunda fila con el mismo id. |",
        )
        agents.write_text(text, encoding="utf-8")

    def diseno(root: Path) -> None:
        agents = root / "AGENTS.md"
        text = agents.read_text(encoding="utf-8")
        text = text.replace(
            "| `contenedor` | Parcial | Sin imagen publicada todavía. |",
            "| `contenedor` | Parcial | Sin imagen publicada todavía. |\n"
            "| `diseno` | Diseño | En curso, sin CI todavía. |",
        )
        agents.write_text(text, encoding="utf-8")

    def contents_write(root: Path) -> None:
        workflow = root / ".github" / "workflows" / "ci.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "  contents: read", "  contents: write"
            ),
            encoding="utf-8",
        )

    def sin_fetch(root: Path) -> None:
        workflow = root / ".github" / "workflows" / "ci.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "        with:\n          fetch-depth: 0\n", ""
            ),
            encoding="utf-8",
        )

    def fetch_en_otro(root: Path) -> None:
        sin_fetch(root)
        auto_merge = root / ".github" / "workflows" / "dependabot-auto-merge.yml"
        auto_merge.write_text(
            auto_merge.read_text(encoding="utf-8").replace(
                "        uses: actions/checkout@v7\n",
                "        uses: actions/checkout@v7\n        with:\n          fetch-depth: 0\n",
            ),
            encoding="utf-8",
        )

    variant("sección vacía", vacia, {"LB002"})
    variant("Validado sin evidencia", sin_evidencia, {"LB004"})
    variant("id duplicado", duplicado, {"LB006"})
    variant("estado Diseño", diseno, set())
    variant("contents: write", contents_write, {"LB105"})
    variant("sin fetch-depth", sin_fetch, {"LB116"})
    variant("fetch-depth en otro workflow", fetch_en_otro, {"LB116"})


def check_contract() -> None:
    body = (ACTION / "action.yml").read_text(encoding="utf-8")
    require("using: composite" in body, "action.yml no es compuesta")
    for name in ("root", "agents", "workflow"):
        require(
            re.search(rf"^  {name}:\n(?:    .*\n)*    required: false", body, re.MULTILINE)
            is not None,
            f"action.yml: falta la entrada {name}",
        )
    require("findings:" in body, "action.yml: falta la salida findings")
    require(
        "value: ${{ steps.check.outputs.findings }}" in body,
        "action.yml: la salida findings no apunta al paso de la comprobación",
    )
    require("IFS=',' read -ra items" in body, "action.yml: no trocea la entrada workflow por comas")
    require(SCRIPT.is_file(), "falta check_linea_base.py")
    require(
        'python3 "${{ github.action_path }}/check_linea_base.py"' in body,
        "action.yml no llama al script de la acción",
    )


def check_sin_seccion() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / ".github" / "workflows").mkdir(parents=True)
        (root / "AGENTS.md").write_text("# Sin línea base\n", encoding="utf-8")
        (root / ".github" / "workflows" / "ci.yml").write_text(
            "permissions:\n  contents: read\njobs: {}\n", encoding="utf-8"
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )
        require(result.returncode == 1, "sin sección: se esperaba 1")
        require("LB001" in codes(result.stdout), "sin sección: falta LB001")


def check_workflow_explicito() -> None:
    result = run(
        "ok",
        "--workflow",
        ".github/workflows/ci.yml",
        "--workflow",
        ".github/workflows/dependabot-auto-merge.yml",
    )
    require(result.returncode == 0, f"workflow explícito: se esperaba 0 y llegó {result.returncode}\n{result.stdout}")
    missing = run("ok", "--workflow", ".github/workflows/no-existe.yml")
    require(missing.returncode == 1, "workflow inexistente: se esperaba 1")
    require("LB101" in codes(missing.stdout), "workflow inexistente: falta LB101")


def check_report() -> None:
    with tempfile.TemporaryDirectory() as temp:
        report = Path(temp) / "report.json"
        result = run("broken", "--report", str(report))
        require(result.returncode == 1, "report: se esperaba 1")
        require(report.is_file(), "report: no se escribió el JSON")
        if report.is_file():
            import json

            data = json.loads(report.read_text(encoding="utf-8"))
            require(len(data) == result.stdout.count("ERROR LB"), "report: el JSON no coincide con la salida")
            require(all(item["path"] for item in data), "report: hay hallazgos sin ruta")


def main() -> int:
    check_contract()
    check_pass("ok")
    check_pass("ok-bullets")
    check_broken()
    check_variantes()
    check_sin_seccion()
    check_workflow_explicito()
    check_report()

    if errors:
        for error in errors:
            print(f"FALLO: {error}")
        return 1
    print("check-linea-base: fixtures y contrato OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
