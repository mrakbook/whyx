#!/usr/bin/env python3
"""
Run tests inside an isolated virtual environment.

Usage:
  # Basic (create venv if missing, install pytest, run tests)
  python srcips/test.py

  # Recreate the venv from scratch
  python srcips/test.py --recreate

  # Enable coverage (installs pytest-cov and adds sensible defaults)
  python srcips/test.py --coverage

  # Choose a custom venv location
  python srcips/test.py --venv .venv-tests-py312

  # Pass extra args to pytest (anything after `--` goes to pytest)
  python srcips/test.py -- --maxfail=1 -q

Notes:
- The repository root is auto-detected (directory that contains the `src/` folder).
- We avoid `pip install -e .` to keep this repo’s `src/` layout importable directly via PYTHONPATH.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import venv
from pathlib import Path


def _echo(msg: str) -> None:
    print(f"[test.py] {msg}")


def _repo_root_from_here() -> Path:
    here = Path(__file__).resolve()
    # Walk upward until a directory containing 'src' exists.
    for p in [here.parent] + list(here.parents):
        if (p / "src").exists():
            return p
    # Fallback: current working directory
    return Path.cwd().resolve()


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _run(cmd: list[str], env: dict[str, str] | None = None) -> int:
    _echo(f"$ {' '.join(cmd)}")
    return subprocess.call(cmd, env=env)


def _run_checked(cmd: list[str], env: dict[str, str] | None = None) -> None:
    code = _run(cmd, env=env)
    if code != 0:
        raise SystemExit(code)


def ensure_venv(venv_dir: Path, recreate: bool) -> Path:
    if recreate and venv_dir.exists():
        _echo(f"Removing venv: {venv_dir}")
        shutil.rmtree(venv_dir)

    if not venv_dir.exists():
        _echo(f"Creating venv: {venv_dir}")
        builder = venv.EnvBuilder(with_pip=True, clear=False, upgrade=False)
        builder.create(venv_dir)

    py = _venv_python(venv_dir)
    if not py.exists():
        raise RuntimeError(f"Python interpreter not found in venv: {py}")

    # Keep tooling fresh
    _run_checked(
        [str(py), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"]
    )
    return py


def install_test_requirements(py: Path, coverage: bool) -> None:
    reqs = ["pytest"]
    if coverage:
        reqs += ["pytest-cov"]
    _run_checked([str(py), "-m", "pip", "install", "--upgrade"] + reqs)

    # Optional: if you keep a dev requirements file, install it as well.
    # This is safe to ignore if it doesn't exist.
    repo_root = _repo_root_from_here()
    for fname in ("requirements-dev.txt", "dev-requirements.txt"):
        fpath = repo_root / fname
        if fpath.exists():
            _echo(f"Installing additional dev requirements: {fpath}")
            _run_checked([str(py), "-m", "pip", "install", "-r", str(fpath)])
            break


def run_pytest(py: Path, coverage: bool, pytest_args: list[str]) -> int:
    repo_root = _repo_root_from_here()

    # Ensure 'src' layout is importable by pytest and subprocesses spawned by tests
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)

    default_args = []
    if coverage:
        # Produce concise output + a missing-lines table for the 'src' tree by default
        default_args = [
            "--maxfail=1",
            "--disable-warnings",
            "-q",
            "--cov=src",
            "--cov-report=term-missing",
        ]
    elif not pytest_args:
        # Sensible defaults when no explicit args are provided
        default_args = ["--maxfail=1", "--disable-warnings", "-q"]

    cmd = [str(py), "-m", "pytest"] + (pytest_args or default_args)
    _echo(f"Repo root: {repo_root}")
    return _run(cmd, env=env)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run tests in a dedicated virtual environment."
    )
    parser.add_argument(
        "--venv",
        dest="venv_dir",
        default=".venv-tests",
        help="Path to (or name of) the test venv",
    )
    parser.add_argument(
        "--recreate", action="store_true", help="Recreate the venv from scratch"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Install pytest-cov and run tests with coverage",
    )
    parser.add_argument(
        "pytest_remainder",
        nargs=argparse.REMAINDER,
        help="Arguments to pass through to pytest (prefix with `--`), e.g. `-- -k smoke -q`",
    )

    args = parser.parse_args(argv)

    repo_root = _repo_root_from_here()
    venv_dir = (
        (repo_root / args.venv_dir)
        if not Path(args.venv_dir).is_absolute()
        else Path(args.venv_dir)
    )
    py = ensure_venv(venv_dir, recreate=args.recreate)
    install_test_requirements(py, coverage=args.coverage)

    # Pass anything after an optional `--` straight to pytest.
    pytest_args = list(args.pytest_remainder)
    if pytest_args and pytest_args[0] == "--":
        pytest_args = pytest_args[1:]

    exit_code = run_pytest(py, coverage=args.coverage, pytest_args=pytest_args)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
