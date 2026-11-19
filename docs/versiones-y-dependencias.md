# Versiones de plataforma y dependencias

> **Para quién es:** para quien mantiene los repositorios .NET del portfolio y revisa las pull requests de Dependabot.
>
> **Qué resuelve:** qué versión de .NET se usa, cuándo se cambia, cómo se tratan las actualizaciones mayores y cómo se declaran las dependencias directas y transitivas.
>
> **Decisión:** [ADR-0001](adr/0001-plataforma-y-dependencias.md). Este documento es el procedimiento; el ADR guarda el motivo y las alternativas descartadas.
>
> **Estado:** Validado (2026-11-19) para la comprobación y el bloqueo de mayores: `check-platform@v1.8` corre en el job obligatorio de los cuatro consumidores y su CI está en verde —[lab-api](https://github.com/lanuzalorenzo/lab-api-local-azure/pull/80), [plantillas](https://github.com/lanuzalorenzo/plantillas-dotnet/pull/26), [comicteca](https://github.com/lanuzalorenzo/comicteca/pull/34) y [shared](https://github.com/lanuzalorenzo/shared-dotnet/pull/17)—. · Diseño para la migración a .NET 12: el protocolo está escrito y no se ha ejecutado; se estrena en noviembre de 2027.

Cambiar la versión de .NET no es instalar la última actualización de una aplicación: es cambiar los cimientos de una casa. Los paquetes, las imágenes de contenedor, el CI y las pruebas se apoyan en esa versión, y si una parte se mueve sola, la casa cruje. Por eso la versión de plataforma se elige y se migra, no se actualiza sola.

## 1. Una versión de plataforma por repositorio

La versión se declara una vez, en el `TargetFramework`, y todo lo demás la sigue:

| Sitio | Qué declara |
|---|---|
| `global.json` | El SDK que compila; `rollForward` solo avanza dentro de la misma rama mayor |
| `TargetFramework` de cada proyecto | La plataforma de destino; es la declaración |
| `Directory.Packages.props` | La versión de los paquetes atados a la plataforma |
| `Dockerfile` | Las imágenes `sdk` y `aspnet` o `runtime` del mismo mayor |
| Workflow de CI | `setup-dotnet` con la misma rama |

La invariante es una: **el mayor de un paquete de plataforma es igual al mayor del `TargetFramework`**. Si el destino es `net10.0`, los paquetes que publica el propio .NET van en 10.x. Entran en esa familia, como mínimo:

- `Microsoft.AspNetCore.*`, incluidas las piezas de Blazor y `Mvc.Testing`
- `Microsoft.Extensions.*`
- `Microsoft.EntityFrameworkCore.*` y `Microsoft.Data.Sqlite`
- `Microsoft.Authentication.WebAssembly.Msal` y `Microsoft.JSInterop`
- `System.Security.Cryptography.Pkcs`

No hay lista de excepciones ni versión permitida a mano: durante una migración se cambia el destino y la familia lo sigue. La comprobación es la acción `check-platform` de este repositorio y falla cuando la invariante se rompe. Se aplica a los cuatro consumidores —`lab-api-local-azure`, `comicteca`, `shared-dotnet` y `plantillas-dotnet`— y a las tres plantillas que este último genera.

## 2. LTS, no STS

Según la [política de soporte de .NET](https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core), actualizada el 10 de noviembre de 2026, las versiones pares son LTS y reciben parches tres años; las impares son STS y reciben dos.

| Versión | Lanzamiento | Tipo | Fin de soporte |
|---|---|---|---|
| .NET 10 | 11 de noviembre de 2025 | LTS | 14 de noviembre de 2028 |
| .NET 11 | 10 de noviembre de 2026 | STS | 14 de noviembre de 2028 |

Las dos terminan el mismo día. Pasar a .NET 11 no alarga la vida del proyecto: obliga a cambiar dos veces de base en el mismo periodo y deja menos margen para la siguiente. La decisión, por tanto:

- **La base es la LTS.** Hoy, .NET 10.
- **Una STS no se adopta como destino.** Solo se acepta si una dependencia imprescindible la exige, y entonces entra con su fecha de salida escrita en el ADR.
- **El destino de la siguiente migración es la LTS siguiente**, .NET 12, prevista para noviembre de 2027.
- **La ventana se abre con esa LTS y se cierra antes del mantenimiento.** Los últimos seis meses de una versión son solo de seguridad. Para .NET 10, la migración se hace entre noviembre de 2027 y mayo de 2028.
- **Antes de la ventana no se abre.** Una pull request que proponga el salto se cierra con el motivo, y si el caso se repite, se bloquea en Dependabot.

En el calendario: **10 LTS en uso**, **11 STS que convive y no entra como destino** —los mayores de la familia están bloqueados y, donde `global.json` fija la rama, su SDK no compila—, **12 LTS como destino**.

### Los pasos de una migración

1. Escribir el ADR del repositorio con la versión de destino, la ventana y la evidencia que cierra el cambio.
2. Subir `global.json` al SDK de la versión nueva, sin cambiar `rollForward`, si el repositorio lo fija.
3. Cambiar el `TargetFramework` y las versiones de la familia en `Directory.Packages.props`.
4. Subir las imágenes del `Dockerfile` al mismo mayor.
5. Subir el `dotnet-version` del CI y lo que la infraestructura declare: el `linuxFxVersion` de una Function, el SDK de su proyecto y lo que el Bicep fije.
6. Revisar que las migraciones de EF Core siguen aplicando, si hay base de datos, y actualizar `AGENTS.md`, `README.md` y los documentos que declaren la versión.
7. Estrenarlo en el banco de pruebas con el CI en verde y adoptarlo después en cada consumidor, con su propia pull request y su evidencia.

La migración toca los cinco sitios de §1 y, si el repositorio tiene infraestructura o Functions, también lo que declare allí la versión; no se mezcla con trabajo funcional. El [ADR-0010 del banco](https://github.com/lanuzalorenzo/lab-api-local-azure/blob/main/docs/adr/0010-plataforma-dotnet-y-ciclo-de-vida.md) es el caso detallado, con sus doce proyectos y su evidencia.

## 3. Qué cuenta como actualización mayor

| Tipo | Ejemplos | Cómo entra |
|---|---|---|
| Plataforma | `Microsoft.AspNetCore.*`, `Microsoft.Extensions.*`, EF Core, imágenes `mcr.microsoft.com/dotnet/*` | Solo con una migración de §2 |
| Herramientas | `xunit.*`, `Microsoft.NET.Test.Sdk`, `coverlet.collector` | Mayor permitido; CI completo y fusión a mano |
| Librerías | `Swashbuckle.AspNetCore`, SDK de Azure, `Microsoft.Azure.Functions.Worker`, `System.IdentityModel.Tokens.Jwt` | Mayor permitido; CI completo y fusión a mano |
| Prueba de interfaz | dependencias `npm` de `tests/e2e` | Mayor permitido; CI completo y fusión a mano |
| Deprecado | un paquete que su fabricante retira | No se sube aunque haya versión nueva: se sustituye en la migración |

## 4. Dependencias directas y transitivas

- **Directa es la que el código usa.** Si un `using` nombra un tipo de un paquete, ese paquete se referencia en ese proyecto. Compilar contra una transitiva es un hallazgo, no una comodidad.
- **Una referencia directa no se añade para mover una versión.** Para eso está el pin central; una referencia que nadie usa es deuda disfrazada.
- **El pin de transitivas va al centro.** `CentralPackageTransitivePinningEnabled` está activo en todos los repositorios y en las plantillas, y la versión se escribe en `Directory.Packages.props`.
- **Un pin lleva motivo y fecha**, y solo se abre por una de estas causas: una vulnerabilidad sin parche en la cadena, dos directas con rangos incompatibles o un parche de seguridad que se queda atrás. Sin motivo, no hay pin.
- **El pin caduca.** Cuando la dependencia que lo arrastra ya trae la versión corregida, se retira en el mismo cambio.
- **Una versión por identificador.** `VersionOverride` se reserva para el proyecto que de verdad necesita otra versión y se justifica en la línea; hoy no hay ninguno.
- **Sin rangos flotantes.** Los paquetes `LL.*` se fijan a su versión exacta.
- **Lo que solo sirve para compilar o probar no se publica:** `PrivateAssets="all"` en el runner de pruebas y en las herramientas de diseño.
- **Los conflictos no se tapan.** `NU1107` y `NU1605` se resuelven fijando la transitiva en el centro o cambiando la directa que la impone. Añadir referencias hasta que compile traslada el problema al siguiente.

## 5. Dependabot

- **Agrupado y con auto-merge solo para parche y menor**, cuando los checks obligatorios de `main` están en verde. Un grupo que contenga un mayor no se fusiona solo.
- **El mayor de la familia de plataforma y de las imágenes `mcr.microsoft.com/dotnet/*` se ignora** en `dependabot.yml`. La lista de §1 y la del `ignore` se cambian juntas.
- **Enfriamiento de siete días** para las actualizaciones de versión. Una versión que se retira a los dos días no llega a entrar.
- **Las actualizaciones de seguridad no pasan por ese filtro.** La referencia de configuración de Dependabot lo dice: `update-types` afecta a las actualizaciones de versión, no a las de seguridad.
- **Una pull request mayor que no puede entrar se cierra con el motivo.** No se deja abierta como recordatorio ni se rebasa indefinidamente; si el caso va a repetirse, se añade al `ignore`.

## 6. Vulnerabilidades

- `NuGetAudit` en modo `all` y `NU1901`–`NU1904` como errores en todos los repositorios: una vulnerabilidad conocida, directa o transitiva, rompe la compilación.
- Cuando el informe y la compilación discrepen, manda la compilación. Un paso que solo informa no autoriza a fusionar.
- Las dependencias `npm` de la prueba de interfaz se auditan con `npm audit --audit-level=high`.
- Los plazos por severidad y el informe semanal son los de la [política de dependencias del banco de pruebas](https://github.com/lanuzalorenzo/lab-api-local-azure/blob/main/docs/dependencias.md); aquí no se copian.
- Si una transitiva vulnerable no tiene versión corregida, se fija en la última disponible y se documenta el aviso junto a la línea que lo silencia, con identificador y fecha. Se retira cuando salga la corrección. No hay silencios globales.

## 7. Discrepancias

- **Dentro de un repositorio**, manda §4: una versión por identificador y el pin en el centro.
- **Entre repositorios**, `shared-dotnet` y `core` publican; el consumidor adopta en su propio cambio y no espera. La aplicación principal no se queda atrás más de lo que tarde el banco de pruebas en estar verde.
- **Plataforma:** todos en la misma LTS. `lab-api-local-azure` migra primero, `comicteca` cuando el banco esté en verde y las plantillas cuando la plantilla generada pase su verificación. Durante la ventana, la diferencia es esperada y se declara en el ADR de la migración.
- **La discrepancia se resuelve donde se origina.** No se copia código entre repositorios ni se parte una versión en dos sitios para que cada uno compile.

## 8. Cuando algo no encaja

1. Rojo por conflicto de versiones: fijar la transitiva en el centro.
2. Rojo porque el mayor pertenece a otra plataforma: cerrar y, si se repetirá, ignorar.
3. Rojo porque el paquete está deprecado: cerrar y planificar el sustituto.
4. Verde pero con dos familias mezcladas: la comprobación debería haberlo cazado; se corrige en su propio cambio antes de seguir.
5. Nunca se relaja una comprobación para que una pull request pase.

## 9. Dónde vive y cómo se cambia

El criterio se decide en el [ADR-0001](adr/0001-plataforma-y-dependencias.md); este documento es su procedimiento. Cada repositorio enlaza aquí desde su `AGENTS.md` con una línea y no copia las tablas. El `ignore` de `dependabot.yml` aplica §1 y §3; si cambia la lista de la familia, cambian los dos. Un cambio de criterio se decide en el ADR, se aplica aquí y se traslada a los consumidores en el mismo lote o en uno inmediato.
