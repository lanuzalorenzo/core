# Convenciones de core

Automatización compartida de CI: acciones y workflows que los demás repositorios públicos llaman. La lógica vive aquí; cada consumidor conserva su workflow de CI y sus permisos. Este repositorio no guarda secretos ni datos de los repos que lo usan.

## Estructura

- `actions/<nombre>/`: acción compuesta (`action.yml`), con la lógica en sus pasos o en un script propio si lo hay.
- `.github/workflows/`: workflows reutilizables (`workflow_call`) y `selftest.yml`.
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

- Los consumidores fijan una etiqueta (`v1.1`): no se mueve una etiqueta publicada. Un cambio incompatible abre `v2`.
- El workflow hace `checkout` y llama a la acción; no dupliques pasos entre ambos.
- Las tareas que dependen del código o los permisos de un consumidor —CodeQL, Trivy, contenedor, dependencias— se quedan en ese repositorio.
- Un cambio de acción se prueba en un repositorio consumidor antes de dar la etiqueta por buena.

## Commits

Scopes: `ci`, `actions`, `docs`, `repo`.

Licencia: MIT.
