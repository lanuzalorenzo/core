#!/usr/bin/env python3
"""Comprueba el contrato de las acciones `sast` y `scan` sin dependencias externas.

No sustituye a ejecutarlas en un consumidor: fija las entradas, los umbrales y
las versiones fijadas para que un cambio accidental no relaje el escaneo.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []


def read(action):
    return (ROOT / "actions" / action / "action.yml").read_text(encoding="utf-8")


def input_block(body, name):
    match = re.search(
        rf"^  {re.escape(name)}:\n((?:(?:    .*)?\n)*)", body, re.MULTILINE
    )
    return match.group(1) if match else ""


def input_default(body, name):
    match = re.search(r"^    default: (.+)$", input_block(body, name), re.MULTILINE)
    return match.group(1).strip().strip('"').strip("'") if match else None


def require(condition, message):
    if not condition:
        errors.append(message)


def check_common(action, body):
    require("using: composite" in body, f"{action}: la acción no es compuesta")


def check_pins(action, body):
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("uses:"):
            continue
        ref = stripped.split("uses:", 1)[1].strip()
        require("@" in ref, f"{action}: '{ref}' no fija una versión")
        require(
            not ref.endswith(("@main", "@master")),
            f"{action}: '{ref}' apunta a una rama móvil",
        )


def check_sast(body):
    require(
        re.search(r"^  languages:\n(?:    .*\n)*    required: true", body, re.MULTILINE)
        is not None,
        "sast: 'languages' debe ser obligatorio",
    )
    require(
        input_default(body, "queries") == "security-extended",
        "sast: 'queries' debe valer security-extended",
    )
    for ref in (
        "github/codeql-action/init@v4",
        "github/codeql-action/autobuild@v4",
        "github/codeql-action/analyze@v4",
    ):
        require(ref in body, f"sast: falta {ref}")


def check_scan(body):
    expected = {
        "scan-type": "fs",
        "severity": "CRITICAL,HIGH",
        "exit-code": "1",
        "ignore-unfixed": "true",
        "upload": "true",
    }
    for name, value in expected.items():
        require(
            input_default(body, name) == value,
            f"scan: '{name}' debe valer {value}",
        )
    require(
        "aquasecurity/trivy-action@v0.36.0" in body,
        "scan: falta aquasecurity/trivy-action@v0.36.0",
    )
    require("version: 'v0.76.0'" in body, "scan: Trivy debe ir fijado en v0.76.0")
    require(
        'TRIVY_SKIP_CHECK_UPDATE: "true"' in body,
        "scan: los checks de configuración deben viajar con el binario fijado",
    )
    require(
        "github/codeql-action/upload-sarif@v4" in body,
        "scan: falta la publicación del SARIF",
    )
    require(
        "if: always()" in body,
        "scan: la publicación del SARIF debe ejecutarse con always()",
    )
    require(
        "trivy-${SCAN_TYPE}.sarif" in body,
        "scan: el SARIF por defecto debe llamarse trivy-<scan-type>.sarif",
    )
    require(
        "category=${CATEGORY:-trivy-${SCAN_TYPE}}" in body,
        "scan: la categoría por defecto debe ser trivy-<scan-type>",
    )
    require(
        "scan-type image exige image-ref" in body,
        "scan: un escaneo de imagen sin image-ref debe fallar",
    )


def main():
    sast = read("sast")
    scan = read("scan")

    check_common("sast", sast)
    check_common("scan", scan)
    check_pins("sast", sast)
    check_pins("scan", scan)
    check_sast(sast)
    check_scan(scan)

    if errors:
        for error in errors:
            print(f"FALLO: {error}")
        return 1
    print("Contrato de sast y scan: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
