#!/usr/bin/env bash
# Sirve la página de prueba mientras dure la acción.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -m http.server 8099 --bind 127.0.0.1 --directory "$here/www"
