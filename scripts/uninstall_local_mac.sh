#!/usr/bin/env bash

set -euo pipefail
DEST="/usr/local/bin/whyx"
if [[ -f "${DEST}" ]]; then
	echo "Removing ${DEST}"
	sudo rm -f "${DEST}"
	echo "✔ Removed"
else
	echo "whyx not found at ${DEST}"
fi
