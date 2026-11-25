# Capa de identidad

Cabecera, pie, navegación, botones, insignias y tokens de la marca, en un paquete
que otra web consume tal cual. Vive en `core` desde la versión 2.0.0; antes tenía
su copia la web y esa copia deja de ser la fuente.

## Qué hay

| Archivo | Qué es |
|---|---|
| `identidad.css` | Tokens, tipografía base, cabecera y nav, pie, botones, insignias, foco y movimiento reducido |
| `plantilla.tpl` | Shell con marcadores `{{...}}` y bloques por perfil |
| `shell.py` | Compone una página con la plantilla: perfiles, nav, metadatos y comprobación de marcadores |
| `menu.js` | Abrir y cerrar el menú en móvil; sin dependencias |
| `marca-tile.svg` | La baldosa de la marca, la misma que sirve la web |
| `SHA256SUMS` | Huellas de los cinco archivos anteriores |
| `VERSION` | Versión del paquete; `identidad.css` la declara en su cabecera |
| `preview.py` | Compone `preview/index.html` con la plantilla y los recursos del propio paquete |
| `verificar.py` | Comprueba versión, huellas y preview; `--update` reescribe las huellas |
| `ejemplo/` | Sitio mínimo que usa el paquete; sirve de punto de partida |

## Preview y comprobación

```bash
python3 identidad/preview.py          # escribe identidad/preview/index.html
python3 identidad/verificar.py        # versión, huellas y preview
python3 identidad/verificar.py --update
```

La preview se compone con el CSS, la plantilla, el menú y la baldosa del
paquete, sin copiarlos a `_identidad/`. Es la comprobación visual de que la capa
sigue completa.

## Perfiles

El perfil decide qué se emite. No es un tema: es qué metadatos y qué enlaces
tienen sentido en ese sitio.

| | `publica` | `local` |
|---|---|---|
| Open Graph y Twitter | Sí | No |
| `canonical` | Sí | No |
| `robots` | Sin directiva | `noindex, nofollow` |
| Enlace al código | Sí, si se pasa `repo` | No |

Una web publicada usa `publica`. Un visor que solo escucha en `127.0.0.1` usa
`local`: no tiene sentido anunciar en redes una URL que nadie alcanza.

## Cómo se consume

El paquete se copia a `_identidad/` y se comprueba con las huellas. La copia es
la distribución, no una edición: si un archivo cambia, se sube la versión del
paquete y se actualiza la copia. La etiqueta se crea al fusionar el cambio en
`main`; mientras no exista, el consumo queda **Pendiente**, no verde. El ejemplo
copia a `salida/_identidad/` solo los tres recursos que sirve la página; el
paquete completo, con `VERSION` y `SHA256SUMS`, se copia igual para comprobar
las huellas.

```bash
base=https://raw.githubusercontent.com/lanuzalorenzo/core/identidad-v2.0.0/identidad
mkdir -p _identidad
for f in identidad.css plantilla.tpl shell.py menu.js marca-tile.svg SHA256SUMS VERSION; do
  curl -sSfL "$base/$f" -o "_identidad/$f"
done
```

## Versión

`identidad.css` y `VERSION` dicen lo mismo. Cualquier cambio en uno de los cinco
archivos que consume la web sube la versión; la etiqueta `identidad-vX.Y.Z` no se
mueve después de publicada. Un cambio incompatible —marcadores, perfiles o
estructura de la plantilla— sube el mayor.
