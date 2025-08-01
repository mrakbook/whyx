"""Shared utilities for CLI modules."""

import json
import os
from typing import Dict, List, Optional, Tuple

from .. import __version__ as BASE_VERSION
from .. import static_analysis

try:
    from .. import _build_meta as _bm

    DISPLAY_VERSION = getattr(_bm, "EFFECTIVE_VERSION", BASE_VERSION) or BASE_VERSION
except Exception:
    DISPLAY_VERSION = BASE_VERSION


def print_or_json(obj, as_json: bool):
    if as_json:
        print(json.dumps(obj, indent=2))
    else:
        if isinstance(obj, (dict, list)):
            print(json.dumps(obj, indent=2))
        else:
            print(obj)


def load_or_build_index(index_hint: Optional[str] = None, project: str = ".") -> Dict:
    """
    Try to load an existing index JSON (index_hint or ./.whyx_index.json).
    If not found, build one from `project` (without saving to disk).
    """
    if index_hint and os.path.isfile(index_hint):
        return static_analysis.load_index(index_hint)
    default_index = os.path.join(os.getcwd(), ".whyx_index.json")
    if os.path.isfile(default_index):
        return static_analysis.load_index(default_index)
    return static_analysis.build_index(project, output_file=None)


def resolve_symbol_suffix(
    index_data: Dict, name: str
) -> Tuple[str, Optional[List[str]]]:
    """
    Resolve a possibly-short/suffix function name to a canonical fully-qualified name
    from the index.

    Behavior:
      - If `name` is found verbatim in index['functions'], return it unchanged.
      - Else, if `name` contains a dot, look for a unique suffix match among index['functions'].
        Example: 'demo.increment' -> 'lab.demo.increment'.
      - Else (no dot), match by terminal symbol (function/method) name across the index.
        Example: 'calculateTotal' -> 'billing.invoice.calculateTotal' if unique.
      - If multiple matches exist, return ("", candidates) to signal ambiguity.
      - If no match is found, return (name, None) (callers can proceed with the original).
    """
    funcs: List[str] = index_data.get("functions", [])
    if name in funcs:
        return name, None

    candidates: List[str] = []
    if "." in name:
        suffix = "." + name
        candidates = [f for f in funcs if f.endswith(suffix)]
    else:
        candidates = [f for f in funcs if f.split(".")[-1] == name]

    if len(candidates) == 1:
        return candidates[0], None
    if len(candidates) > 1:
        return "", sorted(candidates)
    return name, None
