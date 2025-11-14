import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pytest


def _find_repo_root(start: Path) -> Path:
    """
    Walk upward until we find the repository root (heuristic: it must contain src/cli/__main__.py).
    """
    cur = start.resolve()
    for parent in [cur] + list(cur.parents):
        if (parent / "src" / "cli" / "__main__.py").exists():
            return parent
    return Path.cwd().resolve()


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return _find_repo_root(Path(__file__))


@pytest.fixture(scope="session")
def base_env(repo_root: Path) -> Dict[str, str]:
    """
    Ensure the CLI package (src/...) is importable when we spawn subprocesses
    from arbitrary working directories.
    """
    env = os.environ.copy()
    py_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root)] + ([py_path] if py_path else [])
    )

    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_whyx(
    args: List[str], cwd: Path, env: Dict[str, str]
) -> subprocess.CompletedProcess:
    """
    Run the CLI as a subprocess: `python -m src.cli <args...>`.
    We always pass `--json` at the top level when we expect JSON.
    """
    cmd = [sys.executable, "-m", "src.cli"] + args
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )


@pytest.fixture
def sample_project(tmp_path: Path) -> Tuple[Path, Dict[str, str]]:
    """
    Create a tiny real project on disk with predictable call relationships.

    Package: acmeproj
      a.py: a1 -> b1, a2 -> b2, a3 -> helper_local
      b.py: b1 -> c1, b2 (no calls)
      c.py: c1()
      f.py: shared()
      g.py: shared()     (intentionally ambiguous symbol 'shared')
    """
    root = tmp_path / "sample_proj"
    pkg = root / "acmeproj"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("# test package\n", encoding="utf-8")

    (pkg / "c.py").write_text(
        "def c1():\n    return 0\n",
        encoding="utf-8",
    )

    (pkg / "b.py").write_text(
        "from .c import c1\ndef b1():\n    c1()\ndef b2():\n    pass\n",
        encoding="utf-8",
    )

    (pkg / "a.py").write_text(
        "from .b import b1, b2\n"
        "def a1():\n"
        "    b1()\n"
        "def a2():\n"
        "    b2()\n"
        "def helper_local():\n"
        "    return 42\n"
        "def a3():\n"
        "    helper_local()\n",
        encoding="utf-8",
    )

    (pkg / "f.py").write_text(
        "def shared():\n    pass\n",
        encoding="utf-8",
    )

    (pkg / "g.py").write_text(
        "def shared():\n    return 1\n",
        encoding="utf-8",
    )

    return root, {"package": "acmeproj"}


@pytest.fixture
def demo_scripts(tmp_path: Path) -> Dict[str, Path]:
    """
    Two runnable scripts to exercise dynamic tracing, watches, search, diff, and report.

    v1: one birthday
    v2: two birthdays (so the watch history differs vs v1)
    """
    root = tmp_path / "dyn_demo"
    root.mkdir(parents=True)

    v1 = root / "demoscript_v1.py"
    v1.write_text(
        "class Person:\n"
        "    def __init__(self, name):\n"
        "        self.name = name\n"
        "        self.age = 0\n"
        "    def birthday(self):\n"
        "        self.age += 1\n"
        "\n"
        "def run():\n"
        "    p = Person('Al')\n"
        "    p.birthday()\n"
        "    return p.age\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    run()\n",
        encoding="utf-8",
    )

    v2 = root / "demoscript_v2.py"
    v2.write_text(
        "class Person:\n"
        "    def __init__(self, name):\n"
        "        self.name = name\n"
        "        self.age = 0\n"
        "    def birthday(self):\n"
        "        self.age += 1\n"
        "\n"
        "def run():\n"
        "    p = Person('Al')\n"
        "    p.birthday()\n"
        "    p.birthday()\n"
        "    return p.age\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    run()\n",
        encoding="utf-8",
    )

    return {"root": root, "v1": v1, "v2": v2}


def read_json(string: str):
    return json.loads(string)
