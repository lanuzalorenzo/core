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
python3 -m compileall -q actions
gitleaks detect --source . --redact --exit-code 2
```

`selftest.yml` repite las tres primeras en CI, escanea secretos y exige que un ancla inexistente devuelva 1. Un cambio en `check-links` se prueba ahí; uno en `dotnet` se prueba en un repositorio consumidor antes de etiquetar.

## Contrato

- Los consumidores fijan una etiqueta (`v1.2`): no se mueve una etiqueta publicada. Un cambio incompatible abre `v2`.
- El workflow hace `checkout` y llama a la acción; no dupliques pasos entre ambos.
- Las tareas que dependen del código o los permisos de un consumidor —CodeQL, Trivy, contenedor, dependencias— se quedan en ese repositorio.
- Un cambio de acción se prueba en un repositorio consumidor antes de dar la etiqueta por buena.

## Commits

Scopes: `ci`, `actions`, `docs`, `repo`. Los cambios entran por rama y pull request; `main` exige los checks del repositorio y rama actualizada. No hagas push directo.

Licencia: MIT.
