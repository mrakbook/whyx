#!/usr/bin/env bash
# run-whyx.sh
# Bootstraps a venv and launches the whyx CLI from the src-rooted layout.
#
# Repo layout:
#   src/                  (package root 'src')
#   src/cli/              (CLI package; run as: python -m src.cli)
#   src/static_analysis/  (static analysis engine)
#   src/dynamic_tracing/  (dynamic tracing engine)
#
# Usage (from anywhere):
#   ./lab/run-whyx.sh help
#   ./lab/run-whyx.sh -V
#   ./lab/run-whyx.sh index .
#   ./lab/run-whyx.sh query callers module.func
#   ./lab/run-whyx.sh run --trace lab/demo.py -o trace.json
#   ./lab/run-whyx.sh run lab/demo.py --watch demo.User.age -o watch.json
#   ./lab/run-whyx.sh diff trace_before.json trace_after.json
#
# Optional env overrides:
#   PY_BIN=/path/to/python3  VENV_DIR=/custom/.venv  ./lab/run-whyx.sh --version

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

PY_BIN="${PY_BIN:-python3}"

VENV_DIR="${VENV_DIR:-${REPO_ROOT}/.venv}"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtual environment at: $VENV_DIR"
  "$PY_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

if [[ -f "requirements.txt" ]]; then
  python -m pip install -r requirements.txt
fi

export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"

if [[ "${1:-}" == "help" ]]; then
  set -- -h
fi

if [[ -f "${REPO_ROOT}/src/cli/__main__.py" ]]; then
  exec python -m src.cli "$@"
elif [[ -f "${REPO_ROOT}/src/cli/main.py" ]]; then
  exec python -m src.cli.main "$@"
else
  echo "Cannot locate CLI entry under src/. Expected one of:"
  echo "  - ${REPO_ROOT}/src/cli/__main__.py"
  echo "  - ${REPO_ROOT}/src/cli/main.py"
  exit 1
fi
