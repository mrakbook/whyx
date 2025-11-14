#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../" && pwd)"
cd "$REPO_ROOT"

ARCH="$(uname -m)"

VERSION="$(
	python3 - <<'PY'
import re, pathlib
p = pathlib.Path("src/__init__.py").read_text(encoding="utf-8")
m = re.search(r'__version__\s*=\s*"([^"]+)"', p)
print(m.group(1) if m else "0.0.1")
PY
)"

# Accept tags like vX.Y.Z, vX.Y.Z-beta, vX.Y.Z-beta.3, etc.
TAG_CANDIDATE="${TAG_OVERRIDE:-${GITHUB_REF_NAME:-${GIT_TAG:-}}}"
if [[ -n "${TAG_CANDIDATE}" && "${TAG_CANDIDATE}" =~ ^v([0-9]+(\.[0-9]+){1,2})(-(dev|alpha|beta)(\.[0-9]+)?)?$ ]]; then
	VERSION="${BASH_REMATCH[1]}"
	if [[ -z "${PREID:-}" ]]; then
		PREID="${BASH_REMATCH[4]:-}${BASH_REMATCH[5]:-}"  # e.g. "beta" or "beta.5"
	fi
fi

BRANCH="${BRANCH_OVERRIDE:-${GITHUB_REF_NAME:-${CI_COMMIT_BRANCH:-${BUILDKITE_BRANCH:-${CIRCLE_BRANCH:-${BITBUCKET_BRANCH:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")}}}}}}"
PREID="${PREID:-}"
if [[ -z "${PREID}" ]]; then
	case "${BRANCH}" in
		main|master) PREID="" ;;
		beta|beta/*|release/beta|release/*beta*) PREID="beta" ;;
		alpha|alpha/*|release/alpha|release/*alpha*) PREID="alpha" ;;
		dev|develop|development|dev/*|feature/*|bugfix/*) PREID="dev" ;;
		""|*) PREID="dev" ;;
	esac
fi

# Validate PREID
if [[ -n "${PREID}" ]]; then
	if ! [[ "${PREID}" =~ ^(dev|alpha|beta)(\.[0-9]+)?$ ]]; then
		echo "error: PREID must be dev|alpha|beta (optionally with .N), or empty." >&2
		exit 2
	fi
fi

EFFECTIVE_VERSION="${VERSION}"
if [[ -n "${PREID}" ]]; then
	EFFECTIVE_VERSION="${VERSION}-${PREID}"
fi

"${SCRIPT_DIR}/build_binary.sh"

BIN="dist/whyx"
if [[ ! -x "${BIN}" ]]; then
	echo "error: dist/whyx not found; build_binary.sh must succeed first." >&2
	exit 1
fi

STAGE="build/pkgroot"
PKG_OUT="build/pkg"
rm -rf "${STAGE}" "${PKG_OUT}"
mkdir -p "${STAGE}/usr/local/bin" "${PKG_OUT}"

install -m 0755 "${BIN}" "${STAGE}/usr/local/bin/whyx"

IDENTIFIER="com.whyx.cli"
SCRIPTS_DIR="${SCRIPT_DIR}/scripts"

chmod +x "${SCRIPTS_DIR}/postinstall"

PKG_NAME="whyx-${EFFECTIVE_VERSION}-${ARCH}.pkg"

pkgbuild \
	--root "${STAGE}" \
	--identifier "${IDENTIFIER}" \
	--version "${VERSION}" \
	--install-location "/" \
	--scripts "${SCRIPTS_DIR}" \
	--ownership recommended \
	"${PKG_OUT}/${PKG_NAME}"

echo
echo "✔ Installer: ${PKG_OUT}/${PKG_NAME}"
echo
echo "Install locally with:"
echo "  sudo installer -pkg ${PKG_OUT}/${PKG_NAME} -target /"
