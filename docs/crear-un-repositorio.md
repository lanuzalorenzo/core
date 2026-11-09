# Crear un repositorio

> **Para quién es:** para quien empieza un repositorio y quiere que nazca con la línea base puesta, no con la intención de ponerla después.
>
> **Qué resuelve:** qué pieza usar, cómo se elige la licencia, qué comprobaciones se ejecutan antes del primer commit y qué se da por hecho al terminar. No sustituye al criterio del propietario.
>
> **Estado:** Runbook preparado. No valida ningún repositorio concreto; cada alta se comprueba y se fecha por separado.

Crear un repositorio es como levantar una casa: los planos se copian fácil, pero la cimentación no se ve hasta que falta. Un repositorio sin licencia, sin escaneo de secretos o sin pull request obligatoria funciona igual el primer día; el problema aparece cuando alguien lo usa o cuando una credencial se cuela en el historial. Por eso el orden no es «crear el repositorio y luego añadir controles», sino crear el esqueleto con los controles dentro.

## 1. Elegir la pieza

La pieza la decide el artefacto, no la costumbre. Si existe una que lo cubre, se usa; no se copia otro repositorio ni se improvisa uno nuevo.

| Artefacto | Pieza | Dónde |
|---|---|---|
| API ASP.NET Core | plantilla `ll-api` | [plantillas-dotnet](https://github.com/lanuzalorenzo/plantillas-dotnet) |
| Aplicación Blazor | plantilla `ll-blazor` | [plantillas-dotnet](https://github.com/lanuzalorenzo/plantillas-dotnet) |
| Biblioteca NuGet | plantilla `ll-nuget` | [plantillas-dotnet](https://github.com/lanuzalorenzo/plantillas-dotnet) |
| Sitio o documentación estática | sin plantilla: `check-links` y la línea base | [core](https://github.com/lanuzalorenzo/core) |
| Acción o workflow de CI | acción o workflow nuevo | [core](https://github.com/lanuzalorenzo/core) |

Si el artefacto no encaja en ninguna fila, primero se decide qué repositorio es su dueño y se crea la pieza allí, con su rama y su pull request. Un repositorio nuevo no lleva dentro una pieza que no existe todavía.

## 2. Licencia y titular

La licencia la decide el propietario; el procedimiento solo recomienda.

- **MIT** es la recomendación también para documentación. Es permisiva, compatible con las dependencias habituales y la que traen las plantillas.
- **Apache-2.0** añade una concesión explícita de patentes. Tiene sentido si el repositorio va a recibir contribuciones de terceros.
- **CC BY 4.0** sirve para documentación separada del código.
- **Sin licencia** es una opción válida: el código sigue siendo del autor, pero nadie sabe qué puede hacer con él.

Un repositorio privado que no vaya a abrirse no lleva licencia pública. Si va a abrirse, se deja puesta la que tendrá al publicarse, para no cambiarla justo antes de la apertura.

En una biblioteca, la licencia se declara dos veces y tienen que coincidir: el archivo `LICENSE` y `PackageLicenseExpression` en `Directory.Build.props`. El titular del copyright es el mismo en `LICENSE`, el README, `AGENTS.md` y los metadatos del paquete.

## 3. Generar

```bash
dotnet new install ./templates/ll-api        # o ll-blazor, ll-nuget
dotnet new ll-api -n MiApi -o ../mi-api
```

La plantilla `ll-api` restaura los paquetes `LL.*` de GitHub Packages, que exige autenticación incluso para leer paquetes públicos: define `GH_PACKAGES_TOKEN` con permiso `read:packages` antes de restaurar. `ll-blazor` y `ll-nuget` solo usan nuget.org.

Un sitio o una documentación estática se crea a mano: sin plantilla, pero con la misma línea base y `check-links` en el CI.

## 4. Los archivos que hacen el repositorio

- `README.md`: qué es, cómo se arranca y en qué estado está. Si el esqueleto no lo trae, se escribe.
- `AGENTS.md`: estructura, verificación, scopes de commit y flujo de cambios. Es el contrato de operación del repositorio y se ajusta al código real, no a la plantilla que lo generó.
- `LICENSE`: solo si el repositorio es público o va a abrirse.
- `.github/workflows/`: el CI de la pieza, con las acciones de `core` fijadas a una etiqueta.
- `.github/dependabot.yml`: un ecosistema por cada dependencia real, y GitHub Actions.
- `.gitignore`: suficiente para el lenguaje y para los secretos locales que el proyecto use.

## 5. El CI del repositorio nuevo

Los pasos comunes se llaman desde `core` con una etiqueta publicada; no se copian. Lo que depende del código o de la política del consumidor se queda en su workflow, porque ahí se decide el umbral y el permiso:

- qué solución compila y qué pruebas se ejecutan;
- qué lenguajes analiza el análisis estático y con qué permisos;
- qué rutas o imágenes escanea y a partir de qué severidad;
- si publica el SARIF y en qué registro construye la imagen.

Un repositorio con menos CI que el de referencia no se presenta como completo: se declara **Parcial** y se dice qué falta.

## 6. Comprobaciones antes del primer push

```bash
dotnet restore MiApi.slnx
dotnet build MiApi.slnx -c Release --no-restore
dotnet test MiApi.slnx -c Release --no-build --no-restore
dotnet format MiApi.slnx --verify-no-changes --no-restore
gitleaks detect --source . --redact --verbose --exit-code 2
```

Los comandos exactos son los que declare el `AGENTS.md` del repositorio generado; estos son el mínimo de una API. Si alguno falla, el repositorio no está listo: no se relaja la comprobación para que pase.

## 7. Publicar el primer commit

Un repositorio público nace con `main` protegida, rama y pull request, checks obligatorios y Dependabot con auto-merge de parche y minor. La línea base completa —Gitleaks sobre el historial, permisos mínimos, auto-merge— es la misma que exige la [guía de publicación](publicar-un-repositorio.md) y no se repite aquí.

El primer cambio entra por rama y pull request, nunca con un push directo a `main`. Si el remoto se crea vacío, el primer push publica la rama, no `main`.

## 8. Cuándo está hecho

- **Validado:** el repositorio existe, el pipeline ha pasado en verde con sus checks y la línea base está comprobada sobre el remoto real.
- **Parcial:** se generó y compila, pero algún control no se ha ejecutado todavía en ese repositorio.
- **Pendiente:** el remoto no existe o la línea base no se ha comprobado.

Una plantilla que se genera y compila en local no demuestra que su CI funcione: eso solo lo dice una ejecución real en un repositorio generado.

## Lista de comprobación

- [ ] La pieza es la que corresponde al artefacto.
- [ ] Licencia y titular decididos, y coincidentes en `LICENSE`, README, `AGENTS.md` y metadatos.
- [ ] El repositorio genera, compila, prueba y verifica formato.
- [ ] El CI llama a las acciones de `core` por etiqueta y conserva lo que depende de su política.
- [ ] `AGENTS.md` describe la estructura y la verificación reales.
- [ ] Dependabot cubre todos los ecosistemas presentes y GitHub Actions.
- [ ] Gitleaks limpio sobre el historial completo.
- [ ] `main` protegida con rama, pull request y checks obligatorios.
- [ ] El estado declarado coincide con lo ejecutado.
