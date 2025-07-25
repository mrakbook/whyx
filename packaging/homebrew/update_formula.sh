#!/usr/bin/env bash

set -euo pipefail

TAG="${1:-}"
SUMS="${2:-}"
if [[ -z "${TAG}" || -z "${SUMS}" ]]; then
  echo "usage: $0 <tag> path/to/SHA256SUMS" >&2
  echo "examples:" >&2
  echo "  $0 release/0.3.0 build/artifacts/SHA256SUMS" >&2
  echo "  $0 v0.3.0        build/artifacts/SHA256SUMS" >&2
  exit 2
fi

# Extract EFFECTIVE_VERSION from supported tags:
# - release/X.Y.Z  (preferred for stable)
# - vX.Y.Z         (legacy stable)
# (beta tags like vX.Y.Z-beta are intentionally rejected for Homebrew)
EFFECTIVE_VERSION=""
if [[ "${TAG}" =~ ^release/([0-9]+(\.[0-9]+){1,2})$ ]]; then
  EFFECTIVE_VERSION="${BASH_REMATCH[1]}"
elif [[ "${TAG}" =~ ^v([0-9]+(\.[0-9]+){1,2})$ ]]; then
  EFFECTIVE_VERSION="${BASH_REMATCH[1]}"
elif [[ "${TAG}" =~ ^v([0-9]+(\.[0-9]+){1,2})-beta$ ]]; then
  echo "error: Beta tag '${TAG}' is not valid for Homebrew stable formula." >&2
  exit 3
else
  echo "error: Unsupported tag format '${TAG}'. Expected release/X.Y.Z or vX.Y.Z" >&2
  exit 3
fi

ARM_SHA="$(grep "whyx_${EFFECTIVE_VERSION}_darwin_arm64\.tar\.gz" "${SUMS}" | awk '{print $1}' | tail -n1 || true)"
X64_SHA="$(grep "whyx_${EFFECTIVE_VERSION}_darwin_x86_64\.tar\.gz" "${SUMS}" | awk '{print $1}' | tail -n1 || true)"

if [[ -z "${ARM_SHA}" ]]; then
  echo "error: ARM64 tarball checksum for ${EFFECTIVE_VERSION} not found in ${SUMS}" >&2
  exit 3
fi
if [[ -z "${X64_SHA}" ]]; then
  echo "error: x86_64 tarball checksum for ${EFFECTIVE_VERSION} not found in ${SUMS}" >&2
  exit 3
fi

FORMULA="packaging/homebrew/whyx.rb"

# Set version
sed -i '' -e "s/version \".*\"/version \"${EFFECTIVE_VERSION}\"/" "${FORMULA}"

# Update URLs to point at release/<version>
# (The Ruby file already uses release/#{version} in the URL; we only update sha256 lines.)
sed -i '' -e "/darwin_arm64.*\.tar\.gz/{n;s/sha256 \".*\"/sha256 \"${ARM_SHA}\"/;}" "${FORMULA}"
sed -i '' -e "/darwin_x86_64.*\.tar\.gz/{n;s/sha256 \".*\"/sha256 \"${X64_SHA}\"/;}" "${FORMULA}"

echo "✔ Updated ${FORMULA} to ${EFFECTIVE_VERSION}"
echo "  arm64 sha256:  ${ARM_SHA}"
echo "  x86_64 sha256: ${X64_SHA}"
echo "Next: commit and push; or publish to a tap repo and 'brew tap' it."
