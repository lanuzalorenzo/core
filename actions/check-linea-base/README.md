# `check-linea-base`

Lee la sección `## Línea base` del `AGENTS.md` de un repositorio y sus
workflows de GitHub Actions, y comprueba que lo declarado y lo exigido
aparezcan en el CI. Es como cotejar la lista de la compra con lo que hay en la
nevera: no cocina, solo dice qué falta. No sale a Internet, no ejecuta el CI y
no toca reglas de rama: lee archivos.

## Uso

```yaml
- uses: actions/checkout@v7
- uses: lanuzalorenzo/core/actions/check-linea-base@v1.9
  with:
    root: .
    agents: AGENTS.md
```

| Entrada | Por defecto | Qué hace |
|---|---|---|
| `root` | `.` | Raíz del repositorio que se revisa, relativa al workspace. |
| `agents` | `AGENTS.md` | Ruta del `AGENTS.md` relativa a la raíz. |
| `workflow` | vacío | Workflows que se revisan, separados por comas y relativos a la raíz. Vacío revisa todos los `.github/workflows/*.yml` y `*.yaml`. |

| Salida | Qué devuelve |
|---|---|
| `findings` | Número de hallazgos. Cero deja el paso en verde; uno o más lo dejan en rojo. |

También se ejecuta a mano:

```bash
python3 actions/check-linea-base/check_linea_base.py --root .
python3 actions/check-linea-base/check_linea_base.py \
  --root . \
  --workflow .github/workflows/ci.yml \
  --workflow .github/workflows/dependabot-auto-merge.yml
```

Cuando se pasan workflows concretos, esa lista sustituye al descubrimiento
automático y también es el conjunto sobre el que se calculan las comprobaciones
globales. Si se filtra, hay que incluir todos los workflows relevantes; de lo
contrario el resultado puede señalar como ausente algo que vive en otro
archivo.

## Qué lee de `## Línea base`

La sección termina en el siguiente `##`. Acepta dos formas:

- una tabla con `Id`, `Estado` y `Evidencia`;
- una lista de viñetas con el control en negrita y el estado en el texto, por
  ejemplo `- **secretos:** Validado; Gitleaks en el CI.`.

Los estados reconocidos son `Validado`, `Parcial`, `Pendiente`, `Diseño` y
`Runbook preparado`. Una
fila `Validado` tiene que traer una evidencia localizable: una URL, un `run`,
un `PR`, una ruta o un fragmento entre comillas. Las demás no se exigen: el
repositorio puede declarar lo que todavía no tiene.

## Qué comprueba en el CI

Siempre:

- Gitleaks sobre el historial (`LB108`) con un checkout que traiga todo el
  historial, `fetch-depth: 0` (`LB116`).
- `.github/dependabot.yml` con `github-actions` (`LB109`) y un workflow de
  auto-merge (`LB110`).
- Permisos: bloque `permissions` global con `contents: read`, sin `write-all`
  (`LB103`, `LB104`, `LB105`).
- Acciones con versión fija, sin `@main` ni `@master` (`LB106`).
- Ningún secreto con valor escrito en el YAML (`LB107`).

Según lo que haya en el repositorio:

- Documentación (`README.md` o `docs/`) y CI sin `check-links` (`LB111`).
- Manifiestos de dependencias y CI sin Trivy (`LB112`).
- `Dockerfile` y CI que no construye ni escanea la imagen (`LB113`).
- Infraestructura (`*.bicep`, `*.tf`) y CI que no la revisa (`LB114`).

Según lo declarado:

- Un control `Validado` de `sast`, contenedor, IaC, SCA o rama principal sin
  respaldo en el workflow (`LB115`).

## Hallazgos

Cada hallazgo sale como `ERROR LBnnn ruta:línea — mensaje`. En GitHub Actions
se repite como anotación `::error` para que el archivo y la línea queden
señalados en la pestaña del PR. El código de salida es `0` sin hallazgos, `1`
con hallazgos y `2` si la raíz no existe.

## Límites

- Las comprobaciones de YAML son textuales: no es un parser. Un YAML válido
  pero construido con alias, anclas o expresiones raras puede escapar a una
  comprobación; el formato habitual de un workflow sí queda cubierto.
- No consulta la API de GitHub: no sabe si el ruleset `main` está aplicado, si
  Dependabot tiene el auto-merge activado en la plataforma ni si el run citado
  en la evidencia existe.
- La correspondencia entre un control declarado y su respaldo usa el nombre
  del control (`sast`, `contenedor`, `iac`, `sca`, `main`). Un identificador
  propio que no use esas palabras no se cruza; se sigue revisando lo global.
- No sustituye al CI del consumidor ni al revisor: señala lo que falta en los
  archivos, no decide si el repositorio puede publicarse.

## Pruebas

Las fixtures viven en `tests/fixtures/linea-base/` del repositorio `core`:

```bash
python3 tests/test_check_linea_base.py
```

La fixture `ok` declara la línea base en tabla y tiene aplicación; `ok-bullets`
la declara en viñetas y es solo documentación; `broken` incumple las
comprobaciones y tiene que salir con código 1.
