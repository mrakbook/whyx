#!/usr/bin/env bash
#
# ./scripts/bump_version.sh [major|minor|patch]
#
# Bumps the __version__ in src/__init__.py and propagates the new version
# across the repository (code + docs), including:
#   - packaging/homebrew/whyx.rb (Ruby formula `version "X.Y.Z"`)
#   - SECURITY.md "Supported Versions" table
#   - Any text files that still contain the old version string
#
# Examples:
#   ./scripts/bump_version.sh patch  # 0.2.0 -> 0.2.1
#   ./scripts/bump_version.sh minor  # 0.2.0 -> 0.3.0
#   ./scripts/bump_version.sh major  # 0.2.0 -> 1.0.0
#
# Notes:
#   - Works with versions like "0.2" or "0.2.0".
#   - If only "MAJOR.MINOR" is present, PATCH is assumed to be 0.
#   - Keeps everything else in src/__init__.py intact.
#   - Skips common build/venv/cache folders while scanning.
#
# Exit codes:
#   0  success
#   1  missing files / invalid repo state
#   2  bad usage
#   3  unsupported version format

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/bump_version.sh [major|minor|patch]

Bumps __version__ in src/__init__.py and propagates the new version across the repo:
- packaging/homebrew/whyx.rb (version "X.Y.Z")
- SECURITY.md (Supported Versions table)
- Any other text files that contain the old version string

Examples:
  scripts/bump_version.sh patch   # 0.2.0 -> 0.2.1
  scripts/bump_version.sh minor   # 0.2.0 -> 0.3.0
  scripts/bump_version.sh major   # 0.2.0 -> 1.0.0
EOF
  exit 2
}

if [[ $# -ne 1 ]]; then
  usage
fi

KIND="$1"
case "${KIND}" in
  major|minor|patch) ;;
  *) echo "error: KIND must be one of: major, minor, patch" >&2; usage ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
INIT_FILE="${REPO_ROOT}/src/__init__.py"

if [[ ! -f "${INIT_FILE}" ]]; then
  echo "error: ${INIT_FILE} not found" >&2
  exit 1
fi

# Do the bump + propagation in one Python pass so we know old/new versions
python3 - <<PY
import os, re, sys
from pathlib import Path

repo_root = Path(r"${REPO_ROOT}")
init_path = Path(r"${INIT_FILE}")
kind = r"${KIND}"

def die(msg, code=1):
    print(msg, file=sys.stderr)
    raise SystemExit(code)

txt = init_path.read_text(encoding="utf-8")
m = re.search(r'__version__\s*=\s*([\'"])([^\'"]+)\1', txt)
if not m:
    die("Could not find __version__ in src/__init__.py", 3)
old = m.group(2)

parts = old.split(".")
if len(parts) == 2:
    parts.append("0")
if len(parts) != 3:
    die(f"Unsupported version format: {old!r} (expected MAJOR.MINOR[.PATCH])", 3)
try:
    M, mnr, p = map(int, parts)
except ValueError:
    die(f"Version segments must be integers: {old!r}", 3)

if kind == "major":
    M, mnr, p = M + 1, 0, 0
elif kind == "minor":
    mnr, p = mnr + 1, 0
elif kind == "patch":
    p += 1
else:
    die(f"Unsupported bump kind: {kind!r}", 2)

new = f"{M}.{mnr}.{p}"

# 1) src/__init__.py
pat = re.compile(r'(__version__\s*=\s*)([\'"])([^\'"]+)\2')
new_txt = pat.sub(lambda m: f"{m.group(1)}{m.group(2)}{new}{m.group(2)}", txt, count=1)
changed = []
if new_txt != txt:
    init_path.write_text(new_txt, encoding="utf-8")
    changed.append(init_path)

# 2) packaging/homebrew/whyx.rb
formula = repo_root / "packaging" / "homebrew" / "whyx.rb"
if formula.exists():
    t = formula.read_text(encoding="utf-8")
    t2 = re.sub(r'(^\s*version\s*")[^"]+(")', f'\\1{new}\\2', t, flags=re.M)
    if t2 != t:
        formula.write_text(t2, encoding="utf-8")
        changed.append(formula)

# 3) SECURITY.md (Supported Versions table)
sec = repo_root / "SECURITY.md"
if sec.exists():
    s = sec.read_text(encoding="utf-8")
    s2 = re.sub(r'(^\|\s*)(\d+\.\d+\.\d+)(\s*\|\s*✅)', f'\\1{new}\\3', s, flags=re.M)
    s3 = re.sub(r'(^\|\s*<\s*)(\d+\.\d+\.\d+)(\s*\|\s*❌)', f'\\1{new}\\3', s2, flags=re.M)
    if s3 != s:
        sec.write_text(s3, encoding="utf-8")
        changed.append(sec)

# 4) Conservative global replace of the exact old version
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".venv", "venv", "env", "ENV", "build", "dist", ".eggs", ".packaging-venv",
    "node_modules",
}
INCLUDE_EXTS = {
    ".py", ".sh", ".rb", ".md", ".mdx", ".txt", ".rst",
    ".yml", ".yaml", ".toml", ".cfg", ".ini", ".mk",
}
INCLUDE_BASENAMES = {"Makefile"}

def skip(p: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in p.parts)

for p in repo_root.rglob("*"):
    if not p.is_file() or skip(p):
        continue
    if p in {init_path, formula, sec}:
        continue
    if p.suffix not in INCLUDE_EXTS and p.name not in INCLUDE_BASENAMES:
        continue
    try:
        data = p.read_text(encoding="utf-8")
    except Exception:
        continue
    if old not in data:
        continue
    new_data = data.replace(old, new)
    if new_data != data:
        p.write_text(new_data, encoding="utf-8")
        changed.append(p)

print(f"Bumped version: {old} -> {new}")
if changed:
    print("Updated files:")
    for c in changed:
        try:
            rel = c.relative_to(repo_root)
        except Exception:
            rel = c
        print(f" - {rel}")
else:
    print("No files needed updates beyond src/__init__.py")
PY
