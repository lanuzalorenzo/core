#!/usr/bin/env python3
"""Detecta imágenes con sshd sobre musl y contraseña abierta.

OpenSSH, sobre musl y sin PAM, acepta cualquier contraseña de más de 256
caracteres en cuentas cuyo campo de contraseña es `*`. Esta comprobación no
construye ni arranca la imagen: lee el Dockerfile y avisa cuando la imagen
resultante reúne las condiciones de configuración que lo permiten.

Qué no ve: si existe una cuenta con `*` y otra con un hash real (estado de
ejecución), la configuración copiada con `COPY` desde otro archivo, y si el
`sshd_config` de la base incluye los fragmentos de `sshd_config.d`.

Uso:
    python3 check_sshd_baseline.py [RAÍZ] [--skip DIR]...

`RAÍZ` es el directorio que se revisa (por defecto, el actual). Cada `--skip`
añade un directorio relativo a la raíz que no se recorre. Sale 0 si no hay
hallazgos, 1 si los hay y 2 ante un error de uso o de lectura.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterator

DEFAULT_SKIP = {".git", "node_modules"}
DOCKERFILE = re.compile(
    r"^(?:Dockerfile|Containerfile)(?:\..+)?$|\.(?:dockerfile|containerfile)$",
    re.IGNORECASE,
)

# Bases con musl: alpine y sus derivados, más las que lo dicen en el nombre.
MUSL_IMAGE = re.compile(
    r"(?:^|[/:@-])(?:alpine|musl)(?:$|[/:@-])",
    re.IGNORECASE,
)

FROM = re.compile(r"^\s*FROM\s+(?:--platform=\S+\s+)?(\S+)(?:\s+AS\s+(\S+))?", re.IGNORECASE)
RUN = re.compile(r"^\s*RUN\s+(.*)$", re.IGNORECASE)
APK_ADD = re.compile(r"\bapk\b(?:\s+-\S+)*\s+add\b", re.IGNORECASE)

SERVER_PACKAGE = re.compile(r"\bopenssh-server\b", re.IGNORECASE)
PAM_PACKAGE = re.compile(r"\bopenssh-server-pam\b", re.IGNORECASE)
PASSWORD_AUTH = re.compile(r"PasswordAuthentication\s+(\w+)", re.IGNORECASE)
USE_PAM = re.compile(r"UsePAM\s+(\w+)", re.IGNORECASE)
AUTH_METHODS = re.compile(r"AuthenticationMethods\s+([^\n;&|]*)", re.IGNORECASE)
COMMENT_TAIL = re.compile(r"\s#.*$")


def is_dockerfile(name: str) -> bool:
    return bool(DOCKERFILE.search(name))


def dockerfiles(root: Path, skip: list[str]) -> list[Path]:
    if root.is_file():
        return [root]
    prefixes = [Path(item.strip("/")).parts for item in skip if item.strip("/")]
    found: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or not is_dockerfile(path.name):
            continue
        relative = path.relative_to(root).parts
        if DEFAULT_SKIP & set(relative):
            continue
        if any(relative[: len(prefix)] == prefix for prefix in prefixes):
            continue
        found.append(path)
    return sorted(found)


def logical_lines(text: str) -> Iterator[tuple[int, str]]:
    """Une las continuaciones con `\\` y conserva la línea donde empieza cada instrucción."""
    buffer = ""
    start = 0
    for number, raw in enumerate(text.splitlines(), start=1):
        if not buffer:
            start = number
        stripped = raw.rstrip()
        if stripped.endswith("\\"):
            buffer += stripped[:-1] + " "
            continue
        buffer += stripped
        if buffer.strip():
            yield start, buffer
        buffer = ""
    if buffer.strip():
        yield start, buffer


def parse_stages(text: str) -> list[dict]:
    stages: list[dict] = []
    current: dict | None = None
    for number, line in logical_lines(text):
        if line.lstrip().startswith("#"):
            continue
        match = FROM.match(line)
        if match:
            current = {
                "number": number,
                "base": match.group(1),
                "alias": match.group(2),
                "runs": [],
            }
            stages.append(current)
            continue
        if current is None:
            continue
        match = RUN.match(line)
        if match:
            body = COMMENT_TAIL.sub("", match.group(1))
            current["runs"].append((number, body))
    return stages


def resolve(stages: list[dict], index: int) -> dict:
    """Resuelve la base y las instrucciones de una etapa, incluida la que hereda de un alias."""
    stage = stages[index]
    inherited = None
    for previous in range(index):
        if stages[previous]["alias"] == stage["base"]:
            inherited = resolve(stages, previous)
            break
    musl = bool(MUSL_IMAGE.search(stage["base"])) or bool(inherited and inherited["musl"])
    runs = (inherited["runs"] if inherited else []) + stage["runs"]
    base = inherited["base"] if inherited else stage["base"]
    return {"musl": musl, "base": base, "runs": runs}


def check(text: str) -> list[tuple[int, str]]:
    stages = parse_stages(text)
    if not stages:
        return []
    effective = resolve(stages, len(stages) - 1)
    if not effective["musl"]:
        return []

    installed: int | None = None
    pam = False
    last: dict[str, str] = {}

    for number, body in effective["runs"]:
        if installed is None and APK_ADD.search(body) and SERVER_PACKAGE.search(body):
            installed = number
            pam = bool(PAM_PACKAGE.search(body))
        for match in PASSWORD_AUTH.finditer(body):
            last["password"] = match.group(1).lower()
        for match in USE_PAM.finditer(body):
            last["pam"] = match.group(1).lower()
        for match in AUTH_METHODS.finditer(body):
            last["auth"] = match.group(1).lower()

    if installed is None:
        return []
    if last.get("password") == "no":
        return []
    if "auth" in last and "password" not in last["auth"]:
        return []
    if pam and last.get("pam") == "yes":
        return []

    base = effective["base"]
    if pam:
        reason = f"instala sshd con PAM sobre {base} sin declarar UsePAM yes ni cerrar la contraseña"
    else:
        reason = f"instala sshd sobre {base} sin desactivar la autenticación por contraseña"
    return [(installed, reason)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Avisa de imágenes con sshd sobre musl y contraseña abierta."
    )
    parser.add_argument("root", nargs="?", default=".", help="Directorio o Dockerfile que se revisa.")
    parser.add_argument("--skip", action="append", default=[], help="Directorio a omitir, relativo a la raíz.")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.exists():
        print(f"No existe la ruta: {root}", file=sys.stderr)
        return 2
    if root.is_file() and not is_dockerfile(root.name):
        print(f"No es un Dockerfile: {root}", file=sys.stderr)
        return 2

    files = dockerfiles(root, args.skip)
    findings: list[tuple[str, int, str]] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            print(f"No se pudo leer {path}: {error}", file=sys.stderr)
            return 2
        name = path.name if root.is_file() else str(path.relative_to(root))
        for line, message in check(text):
            findings.append((name, line, message))

    for name, line, message in findings:
        print(f"{name}:{line}: {message}")

    if findings:
        print(f"{len(findings)} hallazgo(s) en {len(files)} Dockerfile(s).")
        return 1
    print(f"{len(files)} Dockerfile(s) revisados; sin hallazgos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
