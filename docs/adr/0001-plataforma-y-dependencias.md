# ADR-0001 — Plataforma y dependencias: una versión, un dueño y una puerta

> **Estado:** Aceptada
> **Ámbito:** este repositorio, `shared-dotnet`, `plantillas-dotnet` y los repositorios que consumen su plataforma: `lab-api-local-azure` y `comicteca`.
> **Relacionada con:** el [ADR-0010 de lab-api-local-azure](https://github.com/lanuzalorenzo/lab-api-local-azure/blob/main/docs/adr/0010-plataforma-dotnet-y-ciclo-de-vida.md), que decide la versión vigente y el protocolo de migración del banco de pruebas, y su [política de dependencias](https://github.com/lanuzalorenzo/lab-api-local-azure/blob/main/docs/dependencias.md), que fija plazos por severidad. Este ADR no repite sus tablas: las extiende al resto.

## 1. Contexto

En noviembre de 2026 se publicó .NET 11, una versión STS. En una semana Dependabot abrió once pull requests en cuatro repositorios. Cuatro proponían pasar a .NET 11 sobre proyectos `net10.0`; una rompió el `restore` con `NU1107` —Swashbuckle 11 exige `Microsoft.OpenApi` 3.x y `Microsoft.AspNetCore.OpenApi` 10 lo limita a 2.x— y otra entró en `main` con `DevServer 11.0.0`, que su fabricante marca como deprecado, y `Pkcs 11.0.0` en un destino `net10.0`.

La política que faltaba ya existía a medias: `lab-api-local-azure` tiene el ADR-0010, que decide mantener la LTS y migrar a la siguiente LTS, y una política de dependencias con plazos por severidad. Pero no cubre a los demás repositorios ni dice cuándo una dependencia transitiva pasa a directa. El resultado fue el mismo día tres formas distintas de fijar una transitiva: un pin central en `shared-dotnet`, una referencia directa que nadie usa en `comicteca` y nada en el banco de pruebas.

## 2. Decisión

1. **Una versión de plataforma por repositorio**, declarada en el `TargetFramework`. El mayor de un paquete de la familia de plataforma es igual al mayor del destino; no hay lista de excepciones.
2. **LTS como base y como destino.** Una versión STS no se adopta como destino. La decisión y el protocolo de migración del banco de pruebas son los del ADR-0010 y rigen para todos: se migra en la ventana de la siguiente LTS, antes de que la actual entre en mantenimiento.
3. **Los mayores de la familia de plataforma y de las imágenes `mcr.microsoft.com/dotnet/*` se bloquean en Dependabot.** No se revisan pull requests que propongan ese salto: se cierran con el motivo.
4. **Directa es la que el código usa.** Una referencia directa no se añade para mover una versión; el pin de transitivas va al centro, con motivo y fecha, y caduca. `VersionOverride` queda como excepción justificada.
5. **La invariante se comprueba en CI** con la acción `check-platform` de este repositorio, y la respuesta ante una vulnerabilidad sigue los plazos por severidad de la política del banco de pruebas.
6. **Un cambio de versión mayor de plataforma es una migración**, no una actualización: ADR, rama y CI propios, sin trabajo funcional mezclado, y se estrena en el banco de pruebas.

## 3. Alternativas descartadas

- **Adoptar cada versión STS.** Según la política de soporte vigente (actualizada el 10 de noviembre de 2026), .NET 10 y .NET 11 terminan el mismo día, el 14 de noviembre de 2028: pasar a 11 no añade ni un mes de soporte y obliga a cambiar dos veces en el mismo ciclo.
- **Dejar los mayores a revisión manual, sin bloquearlos en Dependabot.** Es lo que estaba pasando: once pull requests, una roja, un paquete deprecado en `main` y cuatro que nunca iban a poder fusionarse.
- **Fijar las transitivas con referencias directas por proyecto.** Crea dependencias que nadie usa y deja la resolución distinta en cada proyecto; fue el resultado de `comicteca#27`.
- **Que cada repositorio decida su versión.** El banco de pruebas y la aplicación principal divergen y la evidencia del banco deja de avalar a la aplicación.
- **Listas de paquetes permitidos por repositorio.** Una excepción escrita es la señal de que la regla está mal definida.

## 4. Consecuencias

- Se renuncia a la novedad de .NET 11 hasta 2027 y se gana una migración por ciclo, no dos.
- Las pull requests de mayores de la familia dejan de abrirse; las de herramientas y librerías independientes siguen entrando a mano, con el CI completo.
- `check-platform` pasa a ser una dependencia de CI en los cuatro repositorios consumidores: si falla, bloquea la fusión.
- El pin central se mantiene: cada pin lleva motivo y fecha, y se retira cuando la dependencia que lo arrastra ya trae la corrección.
- Un repositorio que no pueda cumplir la regla no se publica como parcial: se corrige la regla o el repositorio.

## 5. Criterio para revisarla

- Si Microsoft cambia la política de soporte y una STS dura más que la LTS vigente.
- Si una dependencia imprescindible exige una versión STS concreta.
- Si aparece un caso que la invariante no puede expresar, como un multi-target real con dos plataformas soportadas.
- En la migración a .NET 12, con la evidencia del banco de pruebas.
