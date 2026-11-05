<img src="assets/iconos/core.svg" width="64" alt="Icono de core">

# Acciones y workflows de CI

Automatización compartida de mis repositorios públicos: comprobaciones escritas una vez y llamadas desde cada CI. La lógica vive aquí; cada repositorio conserva su workflow de CI y sus permisos.

> **Estado (2026-11-05).** Dos acciones (enlaces y .NET) y dos workflows reutilizables que las envuelven. Versionado por etiqueta; los consumidores fijan la referencia.

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

Las tareas de seguridad —CodeQL, Trivy, contenedor y revisión de dependencias— se quedan en el repositorio que las necesita: dependen de su código y de sus permisos.

## Verificación

```bash
python3 actions/check-links/check_links.py . --skip tests/fixtures
python3 actions/check-links/check_links.py tests/fixtures/ok
python3 -m compileall -q actions
```

El workflow `selftest.yml` repite las comprobaciones de enlaces sobre el repositorio y las fixtures, exige que `broken/` devuelva código 1 y escanea secretos. `compileall` es una comprobación local de sintaxis; el workflow no la ejecuta.

## Versionado

- `v1.1` es la referencia actual. Los consumidores fijan una etiqueta y Dependabot la sube; para fijar por seguridad, usa el SHA del commit.
- Un cambio incompatible abre `v2`; no se mueve una etiqueta publicada.

Licencia: MIT.
