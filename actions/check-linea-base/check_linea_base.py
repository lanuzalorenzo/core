#!/usr/bin/env python3
"""Comprueba una línea base declarada contra el CI de un repositorio.

Lee la sección `## Línea base` de un `AGENTS.md` y los workflows de GitHub
Actions, y avisa de lo que la línea base exige y no aparece, de lo que se
declara como `Validado` sin respaldo en el workflow y de los permisos o
secretos escritos que rompen la línea base.

No sale a Internet ni ejecuta el CI: lee archivos. Las comprobaciones sobre
YAML son textuales, no un parser completo.

Uso:
    python3 check_linea_base.py [--root DIR] [--agents RUTA]
                                [--workflow RUTA]... [--report ARCHIVO]

`--root` es la raíz del repositorio (por defecto, el actual). `--agents` es
relativo a la raíz (por defecto, `AGENTS.md`). Sin `--workflow` se revisan
todos los `.github/workflows/*.yml` y `*.yaml`. `--report` escribe los
hallazgos en JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

STATES = {
    "validado": "Validado",
    "parcial": "Parcial",
    "pendiente": "Pendiente",
    "diseño": "Diseño",
    "diseno": "Diseño",
    "runbook preparado": "Runbook preparado",
}
HEADING = re.compile(r"^##\s+Línea base\s*$", re.IGNORECASE)
NEXT_HEADING = re.compile(r"^##\s+")
TABLE_SEPARATOR = re.compile(r"^:?-{3,}:?$")
BULLET = re.compile(
    r"^\s*[-*]\s+(?:\*\*(?P<bold>[^*]+?):?\*\*|(?P<plain>[^:]+))"
    r"(?:\s*:\s*|\s+)(?P<text>.+)$"
)
STATE_WORD = re.compile(
    r"\b(Validado|Parcial|Pendiente|Diseño|Diseno|Runbook preparado)\b",
    re.IGNORECASE,
)
LOCATOR = re.compile(
    r"https?://"
    r"|\b(?:run|job|PR|pull)\s*#?\s*\d+"
    r"|`[^`]+`"
    r"|[\w./-]+\.(?:md|markdown|ya?ml|json|cs|csproj|slnx?|py|sh|toml|props|bicep|tf)\b",
    re.IGNORECASE,
)
USE_LINE = re.compile(r"^\s*uses:\s*(\S+)")
KEY_LINE = re.compile(r"^\s*([\w.-]+):\s*(.*)$")
SECRET_KEY = re.compile(
    r"^(?:password|passwd|pwd|token|secret|api[_-]?key|access[_-]?key|client[_-]?secret)$",
    re.IGNORECASE,
)
MANIFESTS = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
}
MANIFEST_SUFFIXES = {".csproj", ".fsproj", ".vbproj", ".sln", ".slnx"}
IAC_SUFFIXES = {".bicep", ".tf"}
IGNORED_DIRS = {".git", "node_modules", "bin", "obj", ".venv", "venv"}

# Control que puede declarar la sección -> texto que lo respalda en el CI.
DECLARED_CONTROLS = (
    ("sast", ("sast", "codeql", "análisis estático", "analisis estatico", "estático", "estatico")),
    ("contenedor", ("contenedor", "docker", "imagen")),
    ("iac", ("iac", "infraestructura", "bicep", "terraform")),
    ("sca", ("sca", "trivy", "auditoría", "auditoria", "dependencias")),
    ("main", ("main", "rama", "ruleset", "protección", "proteccion")),
)
SUPPORT = {
    "sast": re.compile(r"codeql|actions/sast@", re.IGNORECASE),
    "contenedor": re.compile(r"docker|container-publish|buildx", re.IGNORECASE),
    "iac": re.compile(r"bicep|terraform|scan-type:\s*config", re.IGNORECASE),
    "sca": re.compile(r"trivy|actions/scan@", re.IGNORECASE),
    "main": re.compile(r"regla-rama|ruleset", re.IGNORECASE),
}
GLOBAL_CONTROLS = {"secretos", "enlaces", "dependabot", "permisos"}


class Report:
    def __init__(self) -> None:
        self.findings: list[dict] = []

    def add(self, code: str, message: str, path: Path | None = None, line: int | None = None) -> None:
        self.findings.append(
            {
                "code": code,
                "message": message,
                "path": str(path) if path is not None else "",
                "line": line,
            }
        )

    def has(self, code: str) -> bool:
        return any(finding["code"] == code for finding in self.findings)


def read_text(path: Path, report: Report, code: str, missing: str) -> str | None:
    if not path.is_file():
        report.add(code, missing)
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def split_section(text: str) -> tuple[int, list[tuple[int, str]]] | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if HEADING.match(line.strip()):
            body = []
            for offset in range(index + 1, len(lines)):
                candidate = lines[offset]
                if NEXT_HEADING.match(candidate.strip()):
                    break
                body.append((offset + 1, candidate))
            return index + 1, body
    return None


def clean_cell(cell: str) -> str:
    return cell.strip().strip("*_ ").strip()


def declarations(
    section: list[tuple[int, str]], path: Path, report: Report
) -> list[dict]:
    rows: list[dict] = []
    table = [(number, line) for number, line in section if line.strip().startswith("|")]
    bullets = [(number, line) for number, line in section if BULLET.match(line)]

    if table:
        parsed: list[tuple[int, list[str]]] = []
        header_skipped = False
        for number, line in table:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells and all(TABLE_SEPARATOR.match(cell) or not cell for cell in cells):
                continue
            if not header_skipped and any(
                clean_cell(cell).lower() in {"id", "control", "estado", "state"}
                for cell in cells
            ):
                header_skipped = True
                continue
            parsed.append((number, cells))
        for number, cells in parsed:
            if len(cells) < 3:
                report.add("LB003", "una fila de la tabla no tiene id, estado y evidencia", path, number)
                continue
            identifier = clean_cell(cells[0]).strip("`")
            state = clean_cell(cells[1]).strip("`")
            evidence = clean_cell(cells[2])
            rows.append(
                {
                    "id": identifier,
                    "state": state,
                    "evidence": evidence,
                    "line": number,
                    "path": path,
                }
            )

    for number, line in bullets:
        match = BULLET.match(line)
        assert match is not None
        identifier = clean_cell(match.group("bold") or match.group("plain"))
        text = match.group("text").strip()
        state_match = STATE_WORD.search(text)
        state = state_match.group(1) if state_match else ""
        evidence = text
        if state_match:
            evidence = (text[: state_match.start()] + text[state_match.end() :]).strip(" ;,.-")
        rows.append(
            {
                "id": identifier,
                "state": state,
                "evidence": evidence,
                "line": number,
                "path": path,
            }
        )

    if not rows:
        report.add("LB002", "la sección ## Línea base no declara ningún control", path)
        return []

    seen: dict[str, int] = {}
    for row in rows:
        identifier = row["id"]
        normalized_state = STATES.get(row["state"].strip().lower())
        if row["state"] and normalized_state is None:
            report.add(
                "LB003",
                f"«{identifier}» declara un estado desconocido: {row['state']}",
                path,
                row["line"],
            )
        row["state"] = normalized_state or row["state"]
        if identifier in seen:
            report.add("LB006", f"«{identifier}» aparece dos veces", path, row["line"])
        seen[identifier] = row["line"]
        if row["state"] == "Validado" and not row["evidence"]:
            report.add("LB004", f"«{identifier}» está Validado sin evidencia", path, row["line"])
        elif row["state"] == "Validado" and not LOCATOR.search(row["evidence"]):
            report.add(
                "LB005",
                f"«{identifier}» está Validado sin una evidencia localizable "
                "(URL, run, PR, ruta o código entre comillas)",
                path,
                row["line"],
            )
    return rows


def workflow_paths(root: Path, selected: list[str], report: Report) -> list[Path]:
    if selected:
        paths = []
        for item in selected:
            path = (root / item).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                report.add("LB101", f"el workflow {item} queda fuera de la raíz", root / item)
                continue
            if not path.is_file():
                report.add("LB101", f"no existe el workflow {item}", path)
                continue
            paths.append(path)
        return paths

    folder = root / ".github" / "workflows"
    if not folder.is_dir():
        report.add("LB101", "no hay .github/workflows", folder)
        return []
    paths = sorted(
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    )
    if not paths:
        report.add("LB101", "no hay workflows en .github/workflows", folder)
    return paths


def top_level_permissions(lines: list[str]) -> tuple[int | None, list[tuple[int, str]]]:
    for index, line in enumerate(lines):
        if re.match(r"^permissions:\s*", line):
            block = []
            for offset in range(index + 1, len(lines)):
                candidate = lines[offset]
                if candidate.strip() and not candidate.startswith((" ", "\t")):
                    break
                block.append((offset + 1, candidate))
            return index + 1, block
    return None, []


def check_workflow(path: Path, root: Path, text: str, report: Report) -> None:
    relative = path.relative_to(root)
    lines = text.splitlines()
    line_number, block = top_level_permissions(lines)
    if line_number is None:
        report.add("LB103", "el workflow no declara permisos", relative)
    else:
        inline = lines[line_number - 1].split(":", 1)[1].strip()
        if inline and inline not in {"{}", "read-all", "write-all"}:
            report.add("LB104", f"el workflow declara permisos amplios: {inline}", relative, line_number)
        contents = [
            (number, line.split(":", 1)[1].strip())
            for number, line in block
            if line.strip().startswith("contents:")
        ]
        if not contents:
            report.add("LB103", "el workflow no declara contents: read", relative, line_number)
        for number, value in contents:
            if value != "read":
                report.add(
                    "LB105",
                    f"contents debe ser read en el bloque global: {value}",
                    relative,
                    number,
                )

    for number, line in enumerate(lines, start=1):
        if re.search(r"write-all", line):
            report.add("LB104", "el workflow usa write-all", relative, number)
        use = USE_LINE.match(line)
        if use:
            reference = use.group(1).strip("'\"")
            if reference.startswith(("./", "docker://")):
                continue
            if "@" not in reference:
                report.add("LB106", f"la acción {reference} no fija una versión", relative, number)
            elif reference.rsplit("@", 1)[1].lower() in {"main", "master"}:
                report.add("LB106", f"la acción {reference} apunta a una rama móvil", relative, number)
        key = KEY_LINE.match(line)
        if not key:
            continue
        name, value = key.group(1), key.group(2).strip()
        if name.lower() == "secrets" or not SECRET_KEY.match(name):
            continue
        if value.startswith(("${{", "$", "|", ">")) or value in {'""', "''", ""}:
            continue
        report.add(
            "LB107",
            f"«{name}» lleva un valor escrito en el YAML; usa ${{{{ secrets.* }}}}",
            relative,
            number,
        )


def check_global(
    root: Path,
    workflows: dict[Path, str],
    combined: str,
    report: Report,
) -> None:
    gitleaks = [
        (path, text)
        for path, text in workflows.items()
        if re.search(r"gitleaks", text, re.IGNORECASE)
    ]
    if not gitleaks:
        report.add("LB108", "el CI no ejecuta Gitleaks sobre el historial", root / ".github" / "workflows")
    else:
        for path, text in gitleaks:
            if not re.search(
                r"^\s*fetch-depth:\s*['\"]?0['\"]?\s*(?:#.*)?$", text, re.MULTILINE
            ):
                report.add(
                    "LB116",
                    "Gitleaks necesita un checkout con fetch-depth: 0 para ver el historial",
                    path.relative_to(root),
                )

    dependabot = next(
        (
            path
            for path in (root / ".github" / "dependabot.yml", root / ".github" / "dependabot.yaml")
            if path.is_file()
        ),
        None,
    )
    if dependabot is None:
        report.add("LB109", "no hay .github/dependabot.yml", root / ".github")
    else:
        text = dependabot.read_text(encoding="utf-8", errors="replace")
        if "package-ecosystem:" not in text or "github-actions" not in text:
            report.add(
                "LB109",
                "Dependabot no cubre GitHub Actions",
                dependabot.relative_to(root),
            )

    auto_merge = any(
        path.name.startswith("dependabot")
        or ("dependabot" in text.lower() and "merge" in text.lower())
        for path, text in workflows.items()
    )
    if not auto_merge:
        report.add("LB110", "ningún workflow aplica el auto-merge de Dependabot", root / ".github" / "workflows")

    has_docs = (root / "README.md").is_file() or any(
        path.suffix.lower() in {".md", ".markdown"}
        for path in (root / "docs").rglob("*")
        if path.is_file() and not IGNORED_DIRS & set(path.parts)
    )
    if has_docs and not re.search(r"check[-_]links", combined, re.IGNORECASE):
        report.add("LB111", "hay documentación y el CI no comprueba los enlaces", root / "README.md")

    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and not IGNORED_DIRS & set(path.parts)
    ]
    manifests = [
        path
        for path in files
        if path.name in MANIFESTS or path.suffix.lower() in MANIFEST_SUFFIXES
    ]
    if manifests and not re.search(r"trivy|actions/scan@", combined, re.IGNORECASE):
        report.add(
            "LB112",
            "hay dependencias de ejecución y el CI no las audita con Trivy",
            manifests[0].relative_to(root),
        )

    dockerfiles = [path for path in files if path.name.lower().startswith("dockerfile")]
    if dockerfiles and not re.search(r"docker|container-publish|buildx", combined, re.IGNORECASE):
        report.add(
            "LB113",
            "hay un Dockerfile y el CI no construye ni escanea la imagen",
            dockerfiles[0].relative_to(root),
        )

    iac = [path for path in files if path.suffix.lower() in IAC_SUFFIXES]
    if iac and not SUPPORT["iac"].search(combined):
        report.add(
            "LB114",
            "hay infraestructura como código y el CI no la revisa",
            iac[0].relative_to(root),
        )


def check_declarations(
    rows: list[dict],
    combined: str,
    report: Report,
) -> None:
    reported: set[str] = set()
    for row in rows:
        if row["state"] != "Validado":
            continue
        identifier = row["id"].lower()
        control = None
        for name, keywords in DECLARED_CONTROLS:
            if any(keyword in identifier for keyword in keywords):
                control = name
                break
        if control is None or control in GLOBAL_CONTROLS or control in reported:
            continue
        if not SUPPORT[control].search(combined):
            report.add(
                "LB115",
                f"«{row['id']}» está Validado y el CI no lo respalda",
                row["path"],
                row["line"],
            )
            reported.add(control)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="raíz del repositorio")
    parser.add_argument("--agents", default="AGENTS.md", help="AGENTS.md relativo a la raíz")
    parser.add_argument(
        "--workflow",
        action="append",
        default=[],
        metavar="RUTA",
        help="workflow relativo a la raíz; repetible. Sin ninguno, todos los de .github/workflows",
    )
    parser.add_argument("--report", help="archivo JSON donde dejar los hallazgos")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"ERROR LB000 no existe la raíz {root}", file=sys.stderr)
        return 2

    report = Report()
    agents = (root / args.agents).resolve()
    try:
        agents.relative_to(root)
    except ValueError:
        report.add("LB001", f"el AGENTS.md {args.agents} queda fuera de la raíz", agents)
        agents = root / args.agents

    text = read_text(agents, report, "LB001", f"no existe {args.agents}")
    rows: list[dict] = []
    if text is not None:
        section = split_section(text)
        if section is None:
            report.add("LB001", "no hay una sección ## Línea base", agents)
        else:
            rows = declarations(section[1], agents, report)

    paths = workflow_paths(root, args.workflow, report)
    workflows: dict[Path, str] = {}
    for path in paths:
        content = read_text(path, report, "LB101", f"no existe el workflow {path}")
        if content is None:
            continue
        workflows[path] = content
        check_workflow(path, root, content, report)
    combined = "\n".join(workflows.values())
    if workflows:
        check_global(root, workflows, combined, report)
        check_declarations(rows, combined, report)

    for finding in report.findings:
        if finding["path"]:
            try:
                finding["path"] = str(Path(finding["path"]).resolve().relative_to(root))
            except ValueError:
                pass
        location = finding["path"]
        if finding["line"]:
            location = f"{location}:{finding['line']}"
        print(f"ERROR {finding['code']} {location} — {finding['message']}")
        if os.environ.get("GITHUB_ACTIONS") == "true":
            print(f"::error file={finding['path']},line={finding['line'] or 1}::{finding['code']} {finding['message']}")

    if args.report:
        Path(args.report).write_text(
            json.dumps(report.findings, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    total = len(report.findings)
    print(f"{total} hallazgo{'s' if total != 1 else ''}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
