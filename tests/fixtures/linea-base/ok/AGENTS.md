# Fixture de línea base completa

Repositorio de prueba para `check-linea-base`. No contiene datos reales.

## Línea base

Los estados siguen la tabla de la guía de publicación.

| Id | Estado | Evidencia |
|---|---|---|
| `secretos` | Validado | Gitleaks en el CI; [run 123](https://example.test/run/123). |
| `enlaces` | Validado | `check-links` en el CI. |
| `dependabot` | Validado | `.github/dependabot.yml` y auto-merge. |
| `permisos` | Validado | `contents: read` global. |
| `sca` | Validado | `scan` con Trivy sobre las dependencias. |
| `contenedor` | Parcial | Sin imagen publicada todavía. |
