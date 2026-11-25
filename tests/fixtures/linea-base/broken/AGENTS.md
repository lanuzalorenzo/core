# Fixture de línea base rota

Repositorio de prueba con la línea base declarada y el CI en contra. No
contiene datos reales.

## Línea base

| Id | Estado | Evidencia |
|---|---|---|
| `secretos` | Validado | Debería estar. |
| `enlaces` | Validado | `check-links` en el CI. |
| `sast` | Validado | CodeQL en `.github/workflows/ci.yml`. |
| `main` | Validado | Ruleset `main` con los checks. |
| `raro` | Hecho | sin estado conocido. |
