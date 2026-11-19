#!/usr/bin/env python3
"""Comprueba que la familia de plataforma sigue al TargetFramework.

La regla es una: si el destino es netN.0, cualquier paquete que publique el
propio .NET va en N.x, y las imágenes y el SDK del CI, en la misma rama. Una
excepción no se admite: durante una migración se cambia el destino y la familia
lo sigue. Si no se encuentra el destino, falla: una puerta que no puede
comprobar no da verde.

Uso:
    python3 check_platform.py <directorio> [--skip <directorio>]...
"""

import json
import re
import sys
from pathlib import Path

# Paquetes que se publican con cada versión de .NET. Un nombre empieza por el
# patrón o es exactamente el patrón.
FAMILIA = (
    "Microsoft.AspNetCore.",
    "Microsoft.Extensions.",
    "Microsoft.EntityFrameworkCore.",
    "Microsoft.Data.Sqlite",
    "Microsoft.Authentication.WebAssembly.Msal",
    "Microsoft.JSInterop",
    "System.Security.Cryptography.Pkcs",
)

# Directorios que no son código del repositorio.
OMITIR = {".git", "bin", "obj", "node_modules", ".template.config", "artifacts", "publish", "TestResults"}

ATRIBUTO = re.compile(r'(\w+)="([^"]*)"')
TFM = re.compile(r"<TargetFrameworks?>([^<]+)</TargetFrameworks?>")
MAYOR = re.compile(r"net(\d+)\.\d+")
IMAGEN = re.compile(r"mcr\.microsoft\.com/dotnet/([\w.-]+):([^\s]+)")
SDK_CI = re.compile(r"dotnet-version:\s*[\"']?(\d+)\.")
COMENTARIO_XML = re.compile(r"<!--.*?-->")


def es_familia(nombre):
    return any(nombre == patron or nombre.startswith(patron) for patron in FAMILIA)


def leer(ruta):
    return ruta.read_text(encoding="utf-8", errors="replace")


def sin_comentario_xml(texto):
    return COMENTARIO_XML.sub("", texto)


def omitida(ruta, raiz, omitir):
    relativa = ruta.relative_to(raiz).as_posix()
    partes = relativa.split("/")
    if any(parte in OMITIR for parte in partes):
        return True
    return any(relativa == prefijo or relativa.startswith(prefijo + "/") for prefijo in omitir)


def destinos(raiz, omitir):
    """Mayores de TargetFramework declarados en el repositorio."""
    mayores = set()
    candidatos = list(raiz.rglob("*.csproj")) + list(raiz.rglob("Directory.Build.props"))
    for archivo in candidatos:
        if omitida(archivo, raiz, omitir):
            continue
        for grupo in TFM.findall(sin_comentario_xml(leer(archivo))):
            for destino in grupo.split(";"):
                encontrado = MAYOR.search(destino.strip())
                if encontrado:
                    mayores.add(int(encontrado.group(1)))
    return mayores


def revisar_paquetes(raiz, omitir, esperado, hallazgos):
    for props in raiz.rglob("Directory.Packages.props"):
        if omitida(props, raiz, omitir):
            continue
        for linea, texto in enumerate(leer(props).splitlines(), start=1):
            texto = sin_comentario_xml(texto)
            for etiqueta in ("PackageVersion", "PackageReference"):
                elemento = re.search(rf"<{etiqueta}\b([^>]*)>", texto)
                if not elemento:
                    continue
                atributos = dict(ATRIBUTO.findall(elemento.group(1)))
                nombre, version = atributos.get("Include"), atributos.get("Version")
                if not nombre or not version or not es_familia(nombre):
                    continue
                encontrado = re.match(r"(\d+)\.", version)
                if encontrado and int(encontrado.group(1)) != esperado:
                    hallazgos.append(
                        f"{props}:{linea}: {nombre} {version} no sigue al destino net{esperado}.0"
                    )


def revisar_imagenes(raiz, omitir, esperado, hallazgos):
    for dockerfile in raiz.rglob("Dockerfile*"):
        if omitida(dockerfile, raiz, omitir) or not dockerfile.is_file():
            continue
        for linea, texto in enumerate(leer(dockerfile).splitlines(), start=1):
            texto = texto.split("#", 1)[0]
            for _, etiqueta in IMAGEN.findall(texto):
                mayor = re.match(r"(\d+)\.", etiqueta)
                if not mayor:
                    hallazgos.append(
                        f"{dockerfile}:{linea}: la etiqueta {etiqueta} no permite comprobar la versión"
                    )
                elif int(mayor.group(1)) != esperado:
                    hallazgos.append(
                        f"{dockerfile}:{linea}: la imagen usa {etiqueta} y el destino es net{esperado}.0"
                    )


def revisar_ci(raiz, omitir, esperado, hallazgos):
    for global_json in raiz.rglob("global.json"):
        if omitida(global_json, raiz, omitir):
            continue
        try:
            version = json.loads(leer(global_json))["sdk"]["version"]
        except (ValueError, KeyError):
            continue
        mayor = re.match(r"(\d+)\.", version)
        if mayor and int(mayor.group(1)) != esperado:
            hallazgos.append(
                f"{global_json}: el SDK {version} no sigue al destino net{esperado}.0"
            )

    workflows = raiz / ".github" / "workflows"
    if not workflows.is_dir():
        return
    for workflow in sorted(list(workflows.glob("*.yml")) + list(workflows.glob("*.yaml"))):
        for linea, texto in enumerate(leer(workflow).splitlines(), start=1):
            texto = texto.split("#", 1)[0]
            encontrado = SDK_CI.search(texto)
            if encontrado and int(encontrado.group(1)) != esperado:
                hallazgos.append(
                    f"{workflow}:{linea}: el CI instala {encontrado.group(1)}.0 y el destino es net{esperado}.0"
                )


def main():
    argumentos = sys.argv[1:]
    omitir = []
    while "--skip" in argumentos:
        posicion = argumentos.index("--skip")
        if posicion + 1 >= len(argumentos):
            print("--skip necesita un valor", file=sys.stderr)
            return 2
        omitir.append(argumentos[posicion + 1].strip("/"))
        del argumentos[posicion:posicion + 2]
    if len(argumentos) != 1:
        print("Uso: check_platform.py <directorio> [--skip <directorio>]...", file=sys.stderr)
        return 2
    raiz = Path(argumentos[0]).resolve()
    if not raiz.is_dir():
        print(f"No es un directorio: {raiz}", file=sys.stderr)
        return 2

    hallazgos = []
    mayores = destinos(raiz, omitir)
    if not mayores:
        hallazgos.append(f"{raiz}: no se encontró ningún TargetFramework que comprobar")
    elif len(mayores) > 1:
        lista = ", ".join(f"net{mayor}.0" for mayor in sorted(mayores))
        hallazgos.append(f"{raiz}: destinos mezclados ({lista}); la plataforma es una por repositorio")
    if mayores:
        esperado = max(mayores)
        revisar_paquetes(raiz, omitir, esperado, hallazgos)
        revisar_imagenes(raiz, omitir, esperado, hallazgos)
        revisar_ci(raiz, omitir, esperado, hallazgos)

    if hallazgos:
        for hallazgo in hallazgos:
            print(hallazgo, file=sys.stderr)
        print(f"Fallo: {len(hallazgos)} comprobaciones no siguen al TargetFramework.", file=sys.stderr)
        return 1
    print("OK: la familia de plataforma, las imágenes y el CI siguen al TargetFramework.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
