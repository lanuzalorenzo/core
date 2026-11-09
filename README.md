<img src="assets/iconos/core.svg" width="64" alt="Icono de core">

# Acciones y workflows de CI

Automatización compartida de mis repositorios públicos: comprobaciones escritas una vez y llamadas desde cada CI. La lógica vive aquí; cada repositorio conserva su workflow de CI y sus permisos.

> **Estado (2026-11-09).** Seis acciones (enlaces, .NET, Gitleaks, baseline de sshd, publicación de imagen y prueba de interfaz) y dos workflows reutilizables que envuelven las dos primeras. Versionado por etiqueta; los consumidores fijan la referencia.

## Acciones

### `check-links`

Valida que los enlaces relativos de Markdown y HTML apunten a un archivo que existe y, cuando llevan `#`, a un titular o `id` real. Ignora enlaces absolutos, correo y esquemas como `data:`.

```yaml
- uses: lanuzalorenzo/core/actions/check-links@v1.4
  with:
    root: .
    skip: src,dist
```

| Entrada | Por defecto | Qué hace |
|---|---|---|
| `root` | `.` | Directorio que se revisa, relativo al workspace. |
| `skip` | vacío | Directorios que no se recorren, separados por comas. |

También se puede ejecutar a mano:

```bash
python3 actions/check-links/check_links.py .
python3 actions/check-links/check_links.py docs --skip generado
```

### `dotnet`

Restaura, compila en Release, verifica el formato y ejecuta las pruebas. Publica el `.trx` como artefacto.

```yaml
- uses: lanuzalorenzo/core/actions/dotnet@v1.4
  with:
    solution: EcommerceApi.sln
```

| Entrada | Por defecto | Qué hace |
|---|---|---|
| `solution` | `EcommerceApi.sln` | Solución o proyecto que se compila. |
| `dotnet-version` | `10.0.x` | SDK que se instala. |
| `run-format` | `true` | Verifica el formato con `dotnet format`. |
| `results-path` | `tests/**/TestResults/*.trx` | Resultados que se publican. |

### `gitleaks`

Escanea el historial completo del repositorio y falla si encuentra una credencial. Requiere que el job haga el `checkout` con `fetch-depth: 0`; si el clon es superficial, la acción falla en vez de dar un verde falso. Aplica el `.gitleaks.toml` que el consumidor tenga en la raíz, si lo hay.

```yaml
- uses: actions/checkout@v7
  with:
    fetch-depth: 0

- uses: lanuzalorenzo/core/actions/gitleaks@v1.4
```

La versión de Gitleaks va fijada en la acción: los consumidores no la declaran.

### `check-sshd-baseline`

Avisa cuando un `Dockerfile` instala `sshd` sobre una base musl —Alpine y sus derivados— y no desactiva la autenticación por contraseña. No construye la imagen: lee el archivo, igual que `check-links` lee Markdown.

Se referencia con `@v1.4`, la misma etiqueta que el resto de acciones publicadas.

| Entrada | Por defecto | Qué hace |
|---|---|---|
| `root` | `.` | Directorio o Dockerfile que se revisa, relativo al workspace. |
| `skip` | vacío | Directorios que no se recorren, separados por comas. |

Solo ve configuración declarada en el `Dockerfile`. Que exista una cuenta con `*` y otra con un hash real es estado de ejecución y no se deduce del archivo. Tampoco lee una configuración copiada con `COPY` ni comprueba que el `sshd_config` de la base incluya `sshd_config.d`.

También se puede ejecutar a mano:

```bash
python3 actions/check-sshd-baseline/check_sshd_baseline.py .
```

### `container-publish`

Construye la imagen con Buildx, la publica en el registro y adjunta procedencia. La mecánica es común; qué imagen se publica y con qué credenciales lo decide el consumidor, que declara `packages: write` en su workflow.

| Entrada | Por defecto | Qué hace |
|---|---|---|
| `image` | obligatorio | Nombre dentro del registro, sin el registro delante. |
| `registry` | `ghcr.io` | Registro de destino. |
| `context` | `.` | Directorio de contexto. |
| `dockerfile` | `Dockerfile` | Ruta del Dockerfile. |
| `push` | `true` | En `false` solo construye. |
| `provenance` | `mode=max` | Procedencia de Buildx; se desactiva sola cuando `push` es `false`. |
| `platforms` | `linux/amd64` | Plataformas separadas por comas. |
| `build-args` | vacío | Argumentos, uno por línea. |
| `secrets` | vacío | Secretos de BuildKit, `id=valor`, uno por línea. |
| `cache-from` | vacío | Origen de caché. |
| `cache-to` | vacío | Destino de caché. |
| `username` | vacío | Usuario del registro. Sin usuario ni contraseña no hay login. |
| `password` | vacío | Contraseña o token. |

Publica dos etiquetas, la del `ref` y `sha-<corto>`, y devuelve el `digest` de la imagen. La etiqueta `v1.4` ya está publicada y es la referencia de los consumidores.

### `browser-e2e`

Arranca los servicios del consumidor, espera a que las URLs respondan y ejecuta la prueba de interfaz en el navegador que instala. La prueba —qué se comprueba, a qué ancho y con qué datos— sigue siendo del consumidor; la mecánica —instalar, esperar, lanzar y recoger los registros si falla— es la misma en todos.

```yaml
- uses: lanuzalorenzo/core/actions/browser-e2e@v1.5
  with:
    working-directory: tests/e2e
    start-script: tests/e2e/start.sh
    wait-urls: http://localhost:5094/health, http://localhost:5077/
```

| Entrada | Por defecto | Qué hace |
|---|---|---|
| `working-directory` | `.` | Directorio de la prueba, con su `package.json`. |
| `start-script` | obligatorio | Arranca los servicios desde la raíz del workspace y sigue en primer plano mientras duren. Se cierra al terminar la prueba, con sus procesos hijos. |
| `wait-urls` | vacío | URLs que deben responder antes de lanzar la prueba, separadas por comas. |
| `test-command` | `npm test` | Comando de la prueba, ejecutado en `working-directory`. |
| `install-command` | `npm ci` | Instalación de las dependencias de la prueba. |
| `node-version` | `22` | Versión de Node. |
| `browser` | `chromium` | Navegador de Playwright. |
| `install-browser` | `true` | Instala el navegador con sus dependencias; en `false` usa el que ya haya. |
| `timeout-seconds` | `180` | Espera máxima de cada URL. |

La auditoría de las dependencias de la prueba y su umbral se quedan en el repositorio que la escribe, como el resto de la revisión de dependencias. La acción no sube artefactos: cuando la prueba falla, escribe las últimas cincuenta líneas del arranque en la salida del job —el lanzador no debe imprimir secretos— y deja que el consumidor decida qué guardar. Si el lanzador termina antes de que una URL responda, falla en el acto, sin esperar el tiempo máximo.

La etiqueta `v1.5` se crea al publicar este cambio; hasta entonces el ejemplo no resuelve. La verificación de este repositorio prueba la mecánica —arranque, espera, códigos y limpieza— con un servicio mínimo; el navegador y el recorrido real se prueban en un consumidor antes de dar la etiqueta por buena.

## Workflows

### `checks.yml`

Workflow reutilizable con la comprobación de enlaces. Acepta `root` y `skip`.

```yaml
jobs:
  checks:
    uses: lanuzalorenzo/core/.github/workflows/checks.yml@v1.4
    with:
      root: .
```

### `dotnet.yml`

Compila, verifica el formato y ejecuta las pruebas de una solución .NET. Publica el `.trx` como artefacto.

```yaml
jobs:
  build:
    uses: lanuzalorenzo/core/.github/workflows/dotnet.yml@v1.4
    with:
      solution: EcommerceApi.sln
```

| Entrada | Por defecto | Qué hace |
|---|---|---|
| `solution` | `EcommerceApi.sln` | Solución o proyecto que se compila. |
| `dotnet-version` | `10.0.x` | SDK que se instala. |
| `run-format` | `true` | Verifica el formato con `dotnet format`. |

Las tareas de seguridad que dependen del código o de los permisos del consumidor —CodeQL, Trivy, escaneo de imagen y revisión de dependencias— se quedan en el repositorio que las necesita. El escaneo de secretos no depende del código: se centraliza aquí. La lectura estática de un `Dockerfile` tampoco: no construye ni usa credenciales. Construir y publicar una imagen es mecánica común y vive aquí; el consumidor decide qué imagen publica, con qué credenciales y qué permisos concede.

## Verificación

```bash
python3 actions/check-links/check_links.py . --skip tests/fixtures
python3 actions/check-links/check_links.py tests/fixtures/ok
python3 actions/check-sshd-baseline/check_sshd_baseline.py tests/fixtures/sshd/ok
python3 actions/check-sshd-baseline/check_sshd_baseline.py tests/fixtures/sshd/broken   # debe salir 1
python3 -m compileall -q actions
GITHUB_WORKSPACE="$PWD" START_SCRIPT=tests/fixtures/e2e/start.sh \
  WAIT_URLS=http://127.0.0.1:8099/ WORKING_DIRECTORY=tests/fixtures/e2e \
  TEST_COMMAND="node check.mjs" bash actions/browser-e2e/browser_e2e.sh
```

El workflow `selftest.yml` repite las comprobaciones de enlaces sobre el repositorio y las fixtures, exige que `broken/` devuelva código 1, hace lo mismo con `broken-usepam/` y `broken-apk-options/`, prueba la acción de interfaz contra un servicio mínimo y comprueba que una URL que no responde devuelve 1. `compileall` es una comprobación local de sintaxis; el workflow no la ejecuta.

## Versionado

- `v1.4` es la referencia actual. La próxima etiqueta, `v1.5`, añade `browser-e2e` sobre `v1.4`, que sigue publicada y sigue siendo la referencia hasta que los consumidores suban. `v1.1` y `v1.2` también siguen publicadas. Los consumidores fijan una etiqueta y Dependabot la sube; para fijar por seguridad, usa el SHA del commit.
- Un cambio incompatible abre `v2`; no se mueve una etiqueta publicada.

Licencia: MIT.
