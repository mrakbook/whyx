"""Index building and loading for whyx static analysis (logic preserved)."""

import ast
import json
import os
import time
from typing import Dict, Optional

from .analyzer import StaticAnalyzer


def build_index(project_path: str, output_file: Optional[str] = None) -> Dict:
    """
    Analyze all Python files in the given project path to build a static call graph index.
    Returns a dict containing:
      - 'functions': List[str]
      - 'edges': List[Tuple[str, str]]
      - 'root': str (project path)
      - 'generated_at': ISO timestamp
    Optionally writes the index to a JSON file.
    """
    project_path = os.path.abspath(project_path)
    index_data = {
        "root": project_path,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "functions": [],
        "edges": [],
    }

    skip_dirs = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        ".mypy_cache",
        ".pytest_cache",
        "build",
        "dist",
        ".eggs",
        ".tox",
        "node_modules",
    }

    for root, dirs, files in os.walk(project_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            file_path = os.path.join(root, fname)
            rel_path = os.path.relpath(file_path, project_path)
            mod_name = rel_path.replace(os.sep, ".")[:-3]
            if mod_name.endswith(".__init__"):
                mod_name = mod_name[: -len(".__init__")]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source, filename=file_path)
            except Exception:
                continue
            analyzer = StaticAnalyzer(mod_name)
            analyzer.visit(tree)
            index_data["functions"].extend(analyzer.functions)
            index_data["edges"].extend(analyzer.edges)

    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2)
        except Exception as e:
            print(f"Error writing index to {output_file}: {e}")
    return index_data


def load_index(index_path: str) -> Dict:
    """Load a previously saved static index JSON file."""
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)
