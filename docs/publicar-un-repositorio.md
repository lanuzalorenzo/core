# Pasar un repositorio de privado a público

> **Para quién es:** para quien va a cambiar la visibilidad de un repositorio y quiere evitar publicar lo que no debe.
>
> **Qué resuelve:** el orden de los pasos y las comprobaciones mínimas. No sustituye al criterio del propietario ni es asesoramiento legal.
>
> **Estado:** Runbook preparado. No valida ningún repositorio concreto; cada apertura se comprueba y se fecha por separado.

Abrir un repositorio es como abrir las cortinas de una casa: todo lo que estaba dentro se ve, incluido lo que se guardó en un cajón y se olvidó. La diferencia es que aquí se puede limpiar antes. El orden importa: primero se limpia, después se abre y al final se cierra con llave.

## 1. Antes de abrir

### 1.1 El historial

El historial publica algo más que el código: publica quién hizo cada cambio, cuándo y con qué correo. Y lo que se borró del árbol actual puede seguir en un commit antiguo.

- **Autoría:** revisa el nombre y el correo de quien hizo cada cambio y de quien lo aplicó (autor y committer). Que sean los que quieres enseñar.
- **Secretos:** pasa Gitleaks sobre todo el historial, no solo sobre el último commit. Si aparece una credencial, rótala antes de abrir; borrarla del archivo no la invalida.
- **Datos personales:** busca nombres, correos, rutas, identificadores y cualquier dato de terceros. Los datos de una colección o de un cliente no se publican.
- **Rutas y usuarios:** busca rutas absolutas (`/home/...`, `/Users/...`, `C:\...`), nombres de usuario y referencias a repositorios privados.
- **Restos borrados:** si en el pasado hubo datos sensibles, no basta con borrarlos del árbol. Comprueba clones, forks y objetos inalcanzables (restos de commits que ya no cuelgan de ninguna rama). Si el riesgo es real, rota lo que corresponda y consulta la limpieza con GitHub; no reescribas el historial.

Una reescritura de historial cambia todos los identificadores de commit y no forma parte de este procedimiento. Si aparece un dato sensible, rota lo que corresponda, sanea el estado actual y deja escrita la exposición. No reescribas el historial.

### 1.2 Datos y licencia

- **Licencia:** un repositorio público sin licencia deja claro que el código es tuyo, pero no qué puede hacer otra persona con él. Añade una licencia si quieres que se pueda reutilizar. MIT y Apache-2.0 son habituales; elige con criterio, no por copiar.
- **Qué cubre:** la licencia cubre el código, no los datos de terceros ni una colección personal. Si el repositorio mezcla ambos, separa los datos o publica un conjunto de ejemplo.
- **Datos de ejemplo:** comprueba que los datos que quedan son inventados y que la documentación no describe cifras reales.
- **README:** explica qué es, cómo se arranca y en qué estado está. Sin enlaces a repositorios privados, rutas del equipo ni documentos internos.

### 1.3 Metadatos

Antes de abrir, deja listos el nombre, la descripción, los temas, la dirección web si la hay y la imagen social. Un repositorio público sin contexto parece abandonado.

### 1.4 Línea base

Todo repositorio público cumple, como mínimo:

- Gitleaks sobre el historial completo en CI.
- Dependabot para cada ecosistema presente y para las acciones, con «Allow auto-merge» y auto-merge de parche y minor cuando los checks obligatorios de la rama principal pasan.
- Permisos mínimos en cada workflow: `contents: read` por defecto y escritura solo en el job que la necesita, sin `write-all`.
- La rama principal con pull request, checks obligatorios y rama actualizada.
- Comprobación de enlaces internos si hay documentación.
- Auditoría de dependencias de ejecución con umbral alto o crítico.
- Si sirve HTTP, comprobación de que no anuncia el producto ni la versión; si la plataforma fija esas cabeceras, se declara en el README.
- Análisis estático, infraestructura y contenedor cuando el repositorio los necesite.
- **Secretos de Actions:** revisa que ningún workflow lleve valores escritos en el YAML. Los secretos guardados no se publican, pero el archivo sí se ve.

Las acciones compartidas de [`lanuzalorenzo/core`](https://github.com/lanuzalorenzo/core) cubren enlaces, Gitleaks, .NET, baseline de sshd, publicación de imagen, interfaz, SAST y escaneo. Lo que falte se resuelve en la plataforma, no copiando pasos.

## 2. Al abrir

1. Cambia la visibilidad en los ajustes del repositorio. Es el paso que no se deshace con un clic.
2. Protege la rama principal: pull request obligatoria, checks del CI, rama actualizada y sin bypass (nadie puede saltarse los checks).
3. Activa las funciones de seguridad que GitHub ofrece en públicos: aviso de secretos, análisis de código, avisos de Dependabot y aviso privado de vulnerabilidades.
4. Comprueba que el repositorio se clona y que el CI arranca desde cero.

## 3. Después de abrir

- Pasa otra vez el escaneo de secretos y la comprobación de la línea base. Guarda la salida con fecha.
- Comprueba que los enlaces del README y de la documentación siguen funcionando desde fuera.
- Enlaza el repositorio desde el portfolio o el perfil con un motivo: qué enseña y por qué está ahí. Un repositorio público sin enlace es un repositorio suelto.
- Revisa los avisos de seguridad la primera semana. Un hallazgo no es un fallo del proceso; ignorarlo sí.

## 4. Checklist

- [ ] Historial revisado: autoría, secretos, datos personales, rutas y referencias privadas.
- [ ] Restos de datos borrados comprobados en clones, forks y objetos inalcanzables.
- [ ] Licencia añadida y datos de terceros separados o sustituidos por ejemplos.
- [ ] README con qué es, cómo se arranca y estado; sin enlaces privados.
- [ ] Metadatos y descripción listos.
- [ ] Línea base cumplida: Gitleaks, Dependabot, permisos, checks y auditoría de dependencias.
- [ ] Visibilidad cambiada.
- [ ] Rama principal protegida con los checks del CI.
- [ ] Funciones de seguridad activadas.
- [ ] Comprobaciones repetidas después de abrir, con fecha y resultado.
- [ ] Enlace desde el portfolio o el perfil, con motivo.

## 5. Lo que esta guía no hace

- No decide si el contenido puede publicarse: eso es del propietario.
- No garantiza que GitHub borre objetos antiguos.
- No sustituye al revisor de cambios ni al CI del repositorio.
- No es asesoramiento legal sobre licencias o datos de terceros.
