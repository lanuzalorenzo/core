"""La capa de identidad se verifica como cualquier otro artefacto de core.

Ejecuta el mismo contrato que el CI —versión, huellas, preview y ejemplo— y
comprueba que las rutas de fallo fallan: una huella manipulada y un contenido
cambiado sin subir la versión ya etiquetada.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def ejecutar(script: Path, *argumentos: str, cwd: Path | None = None) -> tuple[int, str]:
    resultado = subprocess.run(
        [sys.executable, str(script), *argumentos],
        cwd=cwd or RAIZ,
        capture_output=True,
        text=True,
        check=False,
    )
    return resultado.returncode, resultado.stdout + resultado.stderr


class IdentidadTest(unittest.TestCase):
    def comprobar(self, script: Path, *argumentos: str) -> None:
        codigo, salida = ejecutar(script, *argumentos)
        self.assertEqual(codigo, 0, msg=salida)

    def test_version_huellas_y_preview(self) -> None:
        self.comprobar(RAIZ / "identidad/verificar.py")

    def test_preview_se_compone(self) -> None:
        self.comprobar(RAIZ / "identidad/preview.py", "--check")

    def test_ejemplo_consume_el_paquete(self) -> None:
        self.comprobar(RAIZ / "identidad/ejemplo/build.py", "--check")


class IdentidadFalloTest(unittest.TestCase):
    def copiar(self, destino: Path) -> Path:
        paquete = destino / "identidad"
        shutil.copytree(
            RAIZ / "identidad",
            paquete,
            ignore=shutil.ignore_patterns("__pycache__", "preview"),
        )
        return paquete

    def test_huella_manipulada_falla(self) -> None:
        with tempfile.TemporaryDirectory() as temporal:
            paquete = self.copiar(Path(temporal))
            css = paquete / "identidad.css"
            css.write_text(css.read_text(encoding="utf-8") + "\n.x { color: red; }\n", encoding="utf-8")
            codigo, salida = ejecutar(paquete / "verificar.py")
            self.assertEqual(codigo, 1, msg=salida)
            self.assertIn("SHA256SUMS", salida)

    def test_contenido_cambiado_sin_subir_version_falla(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git no está disponible")
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            paquete = self.copiar(raiz)
            git = ["git", "-c", "user.name=test", "-c", "user.email=test@example.org"]
            subprocess.run(["git", "init", "-q"], cwd=raiz, check=True)
            subprocess.run(["git", "add", "-A"], cwd=raiz, check=True)
            subprocess.run([*git, "commit", "-qm", "paquete"], cwd=raiz, check=True)
            version = (paquete / "VERSION").read_text(encoding="utf-8").strip()
            subprocess.run([*git, "tag", f"identidad-v{version}"], cwd=raiz, check=True)
            css = paquete / "identidad.css"
            css.write_text(css.read_text(encoding="utf-8") + "\n.y { color: red; }\n", encoding="utf-8")
            codigo, salida = ejecutar(paquete / "verificar.py", "--update")
            self.assertEqual(codigo, 1, msg=salida)
            self.assertIn("VERSION", salida)


if __name__ == "__main__":
    unittest.main()
