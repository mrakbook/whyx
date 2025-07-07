#!/usr/bin/env bash

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="${ROOT}/dist/whyx"
DEST="/usr/local/bin/whyx"

if [[ ! -x "${BIN}" ]]; then
	echo "error: ${BIN} not found. Run packaging/macos/build_binary.sh first." >&2
	exit 1
fi

echo "Installing ${BIN} to ${DEST}"
sudo install -m 0755 "${BIN}" "${DEST}"
echo "✔ Installed. Try: whyx --help"
