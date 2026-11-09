# Convenciones de core

Automatización compartida de CI: acciones y workflows que los demás repositorios públicos llaman. La lógica vive aquí; cada consumidor conserva su workflow de CI y sus permisos. Este repositorio no guarda secretos ni datos de los repos que lo usan.

## Seguridad

La línea base de los repos públicos se aplica aquí sin excepción: Gitleaks sobre el historial completo en CI, Dependabot para cada ecosistema que el repositorio use, permisos mínimos en cada workflow y `main` con rama y pull request.

- No guardes secretos, credenciales ni datos de los repos consumidores. Los ejemplos usan valores ficticios.
- Un workflow declara sus permisos: `contents: read` por defecto; escritura solo en el job que la necesita.
- Las comprobaciones de seguridad no se relajan para que un cambio pase.

## Estructura

- `actions/<nombre>/`: acción compuesta (`action.yml`), con la lógica en sus pasos o en un script propio si lo hay.
- `.github/workflows/`: workflows reutilizables (`workflow_call`), `selftest.yml` y `dependabot-auto-merge.yml`.
- `tests/fixtures/`: casos que deben pasar y fallar. Un ancla inexistente tiene que devolver código 1.
- `assets/iconos/`: icono del repositorio, con sus valores en línea.

## Verificación

```bash
python3 actions/check-links/check_links.py . --skip tests/fixtures
python3 actions/check-links/check_links.py tests/fixtures/ok
python3 actions/check-links/check_links.py tests/fixtures/broken   # debe salir 1
python3 actions/check-sshd-baseline/check_sshd_baseline.py tests/fixtures/sshd/ok
python3 actions/check-sshd-baseline/check_sshd_baseline.py tests/fixtures/sshd/broken   # debe salir 1
python3 tests/test_actions.py
python3 -m compileall -q actions
GITHUB_WORKSPACE="$PWD" START_SCRIPT=tests/fixtures/e2e/start.sh WAIT_URLS=http://127.0.0.1:8099/ WORKING_DIRECTORY=tests/fixtures/e2e TEST_COMMAND="node check.mjs" bash actions/browser-e2e/browser_e2e.sh
gitleaks detect --source . --redact --exit-code 2
```

`selftest.yml` repite las comprobaciones de enlaces y de sshd, ejecuta el contrato de `sast` y `scan`, construye la imagen de prueba sin publicarla, prueba la acción de interfaz contra un servicio mínimo, escanea secretos y exige que un ancla inexistente, cada uno de los tres Dockerfiles abiertos y la fixture `scan/config/broken` devuelvan 1. Un cambio en `dotnet`, en `sast`, en `scan`, en `browser-e2e` o en la publicación se prueba en un repositorio consumidor antes de etiquetar.

## Contrato

- Los consumidores fijan una etiqueta (`v1.4`): no se mueve una etiqueta publicada. Un cambio incompatible abre `v2`. `check-sshd-baseline` y `container-publish` están en `v1.4`; `browser-e2e`, `sast` y `scan` entran en `v1.5`.
- El workflow hace `checkout` y llama a la acción; no dupliques pasos entre ambos.
- La mecánica común, igual para todos los consumidores, vive aquí: comprobar enlaces, compilar y probar .NET, escanear secretos, leer un `Dockerfile`, construir y publicar una imagen, ejecutar CodeQL y ejecutar Trivy sobre dependencias, imagen o IaC. El consumidor aporta lo suyo: qué solución compila, qué imagen publica, en qué registro, con qué credenciales, qué lenguajes analiza, qué ruta o imagen escanea, con qué umbral y si publica el SARIF. La decisión y el permiso son suyos: `sast` exige `security-events: write`; `scan` solo lo necesita cuando `upload` no es `false`. El procedimiento no se duplica.
- Un cambio de acción se prueba en un repositorio consumidor antes de dar la etiqueta por buena.

## Commits

Scopes: `ci`, `actions`, `docs`, `repo`. Los cambios entran por rama y pull request; `main` exige los checks del repositorio y rama actualizada. No hagas push directo.

Licencia: MIT.
