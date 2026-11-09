#!/usr/bin/env bash
# Arranca los servicios, espera a las URLs y ejecuta la prueba de interfaz.
# El lanzador debe seguir en primer plano mientras dure la prueba: sus procesos
# viven en un grupo propio y se cierran al terminar, haya pasado o no.
set -euo pipefail

workspace="${GITHUB_WORKSPACE:-$(pwd)}"
working_directory="${WORKING_DIRECTORY:-.}"
start_script="${START_SCRIPT:?falta start-script}"
wait_urls="${WAIT_URLS:-}"
test_command="${TEST_COMMAND:-npm test}"
timeout_seconds="${TIMEOUT_SECONDS:-180}"

logs="$(mktemp -d "${RUNNER_TEMP:-/tmp}/browser-e2e.XXXXXX")"
start_pid=""

is_running() {
  local state
  state="$(ps -o stat= -p "$start_pid" 2>/dev/null || true)"
  [[ -n "$state" && "$state" != Z* ]]
}

cleanup() {
  if [[ -n "$start_pid" ]]; then
    # El grupo se mata aunque el lanzador ya haya terminado: sus hijos pueden
    # seguir vivos y estorbar al siguiente paso del job.
    kill -- "-$start_pid" 2>/dev/null || true
    for _ in 1 2 3 4 5 6 7 8 9 10; do
      is_running || break
      sleep 0.2
    done
    kill -9 -- "-$start_pid" 2>/dev/null || true
    wait "$start_pid" 2>/dev/null || true
  fi

  rm -rf "$logs"
}
trap cleanup EXIT INT TERM

show_start_log() {
  echo "Últimas líneas del arranque:"
  tail -n 50 "$logs/start.log" || true
}

cd "$workspace"

echo "Arrancando los servicios: $start_script"
setsid bash "$start_script" >"$logs/start.log" 2>&1 &
start_pid=$!

IFS=',' read -r -a urls <<< "$wait_urls"

for url in "${urls[@]}"; do
  url="${url#"${url%%[![:space:]]*}"}"
  url="${url%"${url##*[![:space:]]}"}"
  [[ -z "$url" ]] && continue

  deadline=$(( SECONDS + timeout_seconds ))
  echo "Esperando a $url"

  until curl -sf --max-time 5 "$url" >/dev/null; do
    if ! is_running; then
      echo "El arranque terminó antes de que $url respondiera."
      show_start_log
      exit 1
    fi

    if (( SECONDS >= deadline )); then
      echo "$url no respondió en ${timeout_seconds} s."
      show_start_log
      exit 1
    fi

    sleep 1
  done
done

echo "Ejecutando la prueba: $test_command"
if ! ( cd "$working_directory" && bash -c "$test_command" ); then
  echo "La prueba de interfaz falló."
  show_start_log
  exit 1
fi
