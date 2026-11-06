# Fixtures de la baseline de sshd

Ocho casos para la comprobación de `actions/check-sshd-baseline`.

- `ok/`: Alpine con `openssh-server` y `PasswordAuthentication no`. Pasa.
- `ok-pam/`: Alpine con `openssh-server-pam` y `UsePAM yes`. Pasa.
- `ok-multistage/`: Alpine en la etapa de compilación y Debian en la final. No se revisa.
- `ok-authmethods/`: Alpine con `AuthenticationMethods publickey`. Pasa.
- `ok-glibc/`: Debian con `openssh-server`. No se revisa.
- `broken/`: Alpine con `openssh-server` y sin configuración. Falla.
- `broken-usepam/`: Alpine con `openssh-server-pam` y `UsePAM no`. Falla.
- `broken-apk-options/`: Alpine con `apk --no-cache add openssh-server`. Falla.
