#!/usr/bin/env python3
"""
Quality helper for the Pulsar repo.

Usage:
  python scripts/quality.py lint   # run lints (no changes)
  python scripts/quality.py fmt    # auto-format + import sort (in place)

Behavior:
  - Ensures a per-repo virtualenv exists (ROOT/.venv or $PULSAR_VENV).
  - Re-execs under that venv's python if necessary.
  - Ensures 'ruff' is installed in the venv (auto-installs if missing).
  - After the run, cleans temp artifacts quietly and prints one summary line.

Env:
  QUALITY_KEEP_VENV=1  # keep the venv after run
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VENV_DIR = ROOT / ".venv"
VENV_DIR = Path(os.environ.get("PULSAR_VENV") or DEFAULT_VENV_DIR)

# Only operate on src/
DEFAULT_TARGETS = ["src"] if (ROOT / "src").exists() else []

VENV_PY: Path


def _venv_python_path(venv_dir: Path) -> Path:
    if os.name == "nt":
        candidates = [
            venv_dir / "Scripts" / "python.exe",
            venv_dir / "Scripts" / "python",
        ]
    else:
        candidates = [venv_dir / "bin" / "python3", venv_dir / "bin" / "python"]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def _run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT).returncode


def _ruff_cmd(*args: str) -> list[str]:
    return [str(VENV_PY), "-m", "ruff", *args]


def _ensure_venv() -> Path:
    vpy = _venv_python_path(VENV_DIR)
    if not vpy.exists():
        print(f"• Creating virtualenv: {VENV_DIR}")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        vpy = _venv_python_path(VENV_DIR)
        subprocess.run(
            [
                str(vpy),
                "-m",
                "pip",
                "install",
                "-q",
                "--upgrade",
                "pip",
                "setuptools",
                "wheel",
            ],
            check=True,
        )
    return vpy


def _reexec_under_venv(vpy: Path) -> None:
    cur = Path(sys.executable).resolve()
    if cur != vpy.resolve():
        env = os.environ.copy()
        env.setdefault("QUALITY_OUTER_PY", str(cur))
        os.execve(str(vpy), [str(vpy), __file__, *sys.argv[1:]], env)


def _ensure_ruff_installed(vpy: Path) -> None:
    rc = subprocess.run([str(vpy), "-m", "ruff", "--version"], cwd=ROOT).returncode
    if rc == 0:
        return
    print("• Installing Ruff into the project virtualenv …")
    subprocess.run([str(vpy), "-m", "pip", "install", "ruff"], check=True)
    rc2 = subprocess.run([str(vpy), "-m", "ruff", "--version"], cwd=ROOT).returncode
    if rc2 != 0:
        print("error: Ruff installation failed.", file=sys.stderr)
        raise SystemExit(127)


def _remove_tree_quiet(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        shutil.rmtree(path, ignore_errors=True)
        return True
    except Exception:
        return False


def _outer_python_candidate() -> Optional[Path]:
    p = os.environ.get("QUALITY_OUTER_PY")
    return Path(p) if p and Path(p).exists() else None


def _schedule_delete_tree(path: Path, outer_python: Optional[Path]) -> bool:
    if not path.exists():
        return False

    helper_code = r"""
import os, sys, time, shutil, pathlib
target = pathlib.Path(sys.argv[1])

def _onerror(func, pth, exc):
    try:
        os.chmod(pth, 0o700)
    except Exception:
        pass
    try:
        func(pth)
    except Exception:
        pass

for _ in range(24):
    try:
        if target.is_dir():
            shutil.rmtree(target, onerror=_onerror)
        elif target.exists():
            target.unlink()
        break
    except Exception:
        time.sleep(0.25)
"""

    try:
        if outer_python and outer_python.exists():
            subprocess.Popen(
                [str(outer_python), "-c", helper_code, str(path)],
                cwd=str(ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=(os.name != "nt"),
            )
            return True
        if os.name != "nt" and shutil.which("sh"):
            cmd = f"sleep 0.5; rm -rf -- {shlex.quote(str(path))}"
            subprocess.Popen(
                ["sh", "-c", cmd],
                cwd=str(ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            return True
    except Exception:
        pass

    return _remove_tree_quiet(path)


def _cleanup_rufcache_and_pycache() -> Tuple[bool, int]:
    removed_ruff = _remove_tree_quiet(ROOT / ".ruff_cache")
    count = 0
    try:
        for d in ROOT.rglob("__pycache__"):
            if _remove_tree_quiet(d):
                count += 1
    except Exception:
        pass
    return removed_ruff, count


def _cleanup_venv() -> bool:
    if os.environ.get("QUALITY_KEEP_VENV") == "1":
        return False
    if not VENV_DIR.exists():
        return False
    if (
        os.environ.get("PULSAR_VENV")
        and VENV_DIR.resolve() != DEFAULT_VENV_DIR.resolve()
        and os.environ.get("QUALITY_FORCE_REMOVE_VENV") != "1"
    ):
        return False
    return _schedule_delete_tree(VENV_DIR, _outer_python_candidate())


def do_lint(targets: list[str]) -> int:
    return _run(_ruff_cmd("check", *targets))


def do_fmt(targets: list[str]) -> int:
    rc1 = _run(_ruff_cmd("check", "--select", "I", "--fix", *targets))
    rc2 = _run(_ruff_cmd("format", *targets))
    return rc1 if rc1 != 0 else rc2


def main() -> int:
    global VENV_PY

    if len(sys.argv) != 2 or sys.argv[1] not in {"lint", "fmt"}:
        print("Usage: scripts/quality.py [lint|fmt]", file=sys.stderr)
        return 2

    VENV_PY = _ensure_venv()
    _reexec_under_venv(VENV_PY)
    _ensure_ruff_installed(VENV_PY)

    action = sys.argv[1]
    try:
        rc = do_lint(DEFAULT_TARGETS) if action == "lint" else do_fmt(DEFAULT_TARGETS)
    finally:
        removed_ruff, pycache_count = _cleanup_rufcache_and_pycache()
        venv_removed = _cleanup_venv()
        parts = ["cleanup done"]
        if removed_ruff:
            parts.append("(.ruff_cache removed)")
        if pycache_count:
            parts.append(f"({pycache_count} __pycache__ dirs removed)")
        if venv_removed:
            parts.append("(venv removed)")
        print(" ".join(parts))

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
