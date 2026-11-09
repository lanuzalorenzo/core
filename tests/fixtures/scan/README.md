# Fixtures del escaneo

Casos para `actions/scan` con `scan-type: config` y el umbral por defecto
(`CRITICAL,HIGH`).

- `config/ok/`: Alpine con `USER` no privilegiado. No debe superar el umbral.
- `config/broken/`: Alpine sin `USER`; Trivy marca `DS-0002` («Specify at
  least 1 USER command»), de severidad alta. Debe devolver código 1.

El escaneo de imagen no se prueba aquí: depende de la imagen que construya el
consumidor. Se valida en un repositorio consumidor antes de publicar la etiqueta.
