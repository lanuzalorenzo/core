# Guía para agentes: core

Automatización de CI compartida entre mis repositorios públicos: una comprobación de enlaces y los workflows de compilación y pruebas. La lógica vive aquí; cada repositorio conserva su `ci.yml` y sus permisos.

## Estructura

- `actions/<accion>/`: acción compuesta. El contrato son las entradas de `action.yml`, y el README las documenta.
- `.github/workflows/`: workflows reutilizables (`workflow_call`). `selftest.yml` es el CI de este repositorio.
- `tests/fixtures/`: casos de la comprobación de enlaces. `ok/` debe pasar y `broken/` debe fallar con código 1.
- `assets/iconos/`: material gráfico del README.

## Reglas

- Sin secretos, credenciales ni datos personales en el repositorio.
- Las acciones no instalan dependencias externas: solo la biblioteca estándar de Python y las actions oficiales de GitHub.
- La entrada se valida en `action.yml` y se documenta en el README en el mismo cambio.
- No se duplica lógica entre una acción y un workflow: el workflow llama a la acción.
- Las tareas de seguridad —CodeQL, Trivy, contenedor y revisión de dependencias— se quedan en el repositorio que las necesita: dependen de su código y de sus permisos.

## Verificación

```bash
python3 actions/check-links/check_links.py . --skip tests/fixtures
python3 actions/check-links/check_links.py tests/fixtures/ok
python3 -m compileall -q actions
```

`selftest.yml` repite esas comprobaciones y exige que un ancla inexistente devuelva código 1. Es el mismo criterio de `.github/workflows/selftest.yml`: un cambio está listo cuando los jobs del pipeline pasan en verde.

## Versionado

- `v1` es el contrato actual. Los consumidores fijan una etiqueta y Dependabot la sube; para fijar por seguridad se usa el SHA del commit.
- Una etiqueta publicada no se mueve. Un cambio incompatible abre `v2`.

## Commits

Formato: `type(scope): imperative summary in English`. Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`. Scopes: `actions`, `ci`, `docs`, `repo`, `tests`.

Los cambios entran por rama y pull request. El primer commit del repositorio se hizo directamente sobre `main` porque aún no existía la rama; es la única excepción y no se repite.
