<img src="assets/iconos/core.svg" width="64" alt="Icono de core">

# Acciones y workflows de CI

Automatización compartida de mis repositorios públicos: comprobaciones escritas una vez y llamadas desde cada CI. La lógica vive aquí; cada repositorio conserva su workflow de CI y sus permisos.

> **Estado (2026-11-06).** Tres acciones (enlaces, .NET y Gitleaks) y dos workflows reutilizables que envuelven las dos primeras. Versionado por etiqueta; los consumidores fijan la referencia.

## Acciones

### `check-links`

Valida que los enlaces relativos de Markdown y HTML apunten a un archivo que existe y, cuando llevan `#`, a un titular o `id` real. Ignora enlaces absolutos, correo y esquemas como `data:`.

```yaml
- uses: lanuzalorenzo/core/actions/check-links@v1.1
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
- uses: lanuzalorenzo/core/actions/dotnet@v1.1
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

- uses: lanuzalorenzo/core/actions/gitleaks@v1.2
```

La versión de Gitleaks va fijada en la acción: los consumidores no la declaran.

## Workflows

### `checks.yml`

Workflow reutilizable con la comprobación de enlaces. Acepta `root` y `skip`.

```yaml
jobs:
  checks:
    uses: lanuzalorenzo/core/.github/workflows/checks.yml@v1.1
    with:
      root: .
```

### `dotnet.yml`

Compila, verifica el formato y ejecuta las pruebas de una solución .NET. Publica el `.trx` como artefacto.

```yaml
jobs:
  build:
    uses: lanuzalorenzo/core/.github/workflows/dotnet.yml@v1.1
    with:
      solution: EcommerceApi.sln
```

| Entrada | Por defecto | Qué hace |
|---|---|---|
| `solution` | `EcommerceApi.sln` | Solución o proyecto que se compila. |
| `dotnet-version` | `10.0.x` | SDK que se instala. |
| `run-format` | `true` | Verifica el formato con `dotnet format`. |

Las tareas de seguridad que dependen del código o de los permisos del consumidor —CodeQL, Trivy, contenedor y revisión de dependencias— se quedan en el repositorio que las necesita. El escaneo de secretos no depende del código: se centraliza aquí.

## Verificación

```bash
python3 actions/check-links/check_links.py . --skip tests/fixtures
python3 actions/check-links/check_links.py tests/fixtures/ok
python3 -m compileall -q actions
```

El workflow `selftest.yml` repite las comprobaciones de enlaces sobre el repositorio y las fixtures, exige que `broken/` devuelva código 1 y escanea secretos. `compileall` es una comprobación local de sintaxis; el workflow no la ejecuta.

## Versionado

- `v1.2` es la referencia actual; `v1.1` sigue publicada para los consumidores que aún no la han subido. Los consumidores fijan una etiqueta y Dependabot la sube; para fijar por seguridad, usa el SHA del commit.
- Un cambio incompatible abre `v2`; no se mueve una etiqueta publicada.

Licencia: MIT.
