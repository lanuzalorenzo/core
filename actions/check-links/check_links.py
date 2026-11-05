#!/usr/bin/env python3
"""Comprueba enlaces relativos en Markdown y HTML. No sale a Internet.

Valida rutas dentro del repositorio y, cuando el destino es Markdown o HTML,
que el ancla (`#...`) corresponda a un titular o a un `id` real. Ignora
enlaces absolutos, correo y esquemas como `data:` o `javascript:`.

Uso:
    python3 check_links.py [RAÍZ] [--skip DIR]...

`RAÍZ` es el directorio que se revisa (por defecto, el actual). Cada `--skip`
añade un directorio relativo a la raíz que no se recorre.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

SUFFIXES = {".md", ".html", ".htm"}
DEFAULT_SKIP = {".git", "node_modules", "_site"}
MD_LINK = re.compile(r"!?\[[^\]]*\]\((?:<([^>]+)>|([^)\s]+))")
HTML_ATTR = re.compile(r"""(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.IGNORECASE)
HTML_ID = re.compile(r"""\bid\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.IGNORECASE)
MD_HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")
HTML_HEADING = re.compile(r"<h[1-6]\b[^>]*>(.*?)</h[1-6]>", re.IGNORECASE | re.DOTALL)


def documents(root: Path, skip: list[str]) -> list[Path]:
    prefixes = [Path(item.strip("/")).parts for item in skip if item.strip("/")]
    found = []
    for path in root.rglob("*"):
        if path.suffix.lower() not in SUFFIXES:
            continue
        relative = path.relative_to(root).parts
        if DEFAULT_SKIP & set(relative):
            continue
        if any(relative[: len(prefix)] == prefix for prefix in prefixes):
            continue
        found.append(path)
    return found


def targets(path: Path, text: str):
    if path.suffix.lower() == ".md":
        for angle, plain in MD_LINK.findall(text):
            yield angle or plain
    else:
        for double, single in HTML_ATTR.findall(text):
            yield double or single


def normalize(anchor: str) -> str:
    return re.sub(r"-{2,}", "-", anchor.strip().lower()).strip("-")


def slug(text: str) -> str:
    """Aproxima el ancla que GitHub genera para un titular."""
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.strip().lower().replace(" ", "-")
    text = re.sub(r"[^\w\-]", "", text, flags=re.UNICODE)
    return normalize(text)


def anchors(path: Path, text: str) -> set[str]:
    found = {
        html.unescape(double or single)
        for double, single in HTML_ID.findall(text)
    }
    if path.suffix.lower() == ".md":
        for line in text.splitlines():
            match = MD_HEADING.match(line)
            if match:
                found.add(slug(match.group(1)))
    else:
        for heading in HTML_HEADING.findall(text):
            found.add(slug(heading))
    return {normalize(anchor) for anchor in found if anchor}


def check(root: Path, skip: list[str]) -> list[tuple[Path, str, str]]:
    broken: list[tuple[Path, str, str]] = []
    cache: dict[Path, set[str]] = {}

    for path in documents(root, skip):
        text = path.read_text(encoding="utf-8", errors="replace")
        for raw in targets(path, text):
            target = html.unescape(raw).strip()
            if not target or target.startswith(("mailto:", "tel:", "data:", "javascript:")):
                continue
            parsed = urlparse(target)
            if parsed.scheme or parsed.netloc:
                continue
            clean = unquote(parsed.path)
            base = root if clean.startswith("/") else path.parent
            resolved = (base / clean.lstrip("/")).resolve() if clean else path
            if clean and not resolved.exists():
                broken.append((path.relative_to(root), target, "ruta"))
                continue
            fragment = unquote(parsed.fragment).strip()
            if not fragment or resolved.suffix.lower() not in SUFFIXES:
                continue
            if resolved not in cache:
                cache[resolved] = anchors(
                    resolved,
                    resolved.read_text(encoding="utf-8", errors="replace"),
                )
            if normalize(fragment) not in cache[resolved]:
                broken.append((path.relative_to(root), target, "ancla"))

    return broken


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="directorio a revisar")
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        metavar="DIR",
        help="directorio relativo a la raíz que no se recorre",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"ERROR: no existe el directorio {root}", file=sys.stderr)
        return 2
    skip = DEFAULT_SKIP | set(args.skip)

    broken = check(root, skip)
    if broken:
        for path, target, kind in broken:
            print(f"{path}: {target} ({kind} rota)")
        print(f"\n{len(broken)} enlaces rotos")
        return 1

    print(f"OK: {len(documents(root, skip))} documentos sin enlaces rotos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
