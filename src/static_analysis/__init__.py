"""
Static Analysis module for whyx CLI.

This package now splits the previous monolithic implementation into:
- analyzer.py : AST visitor and call resolution (StaticAnalyzer)
- indexer.py  : build_index / load_index
- queries.py  : build_call_maps / find_all_paths

Public API is preserved by re-exporting the original symbols.
"""

from .analyzer import StaticAnalyzer
from .indexer import build_index, load_index
from .queries import build_call_maps, find_all_paths

__all__ = [
    "StaticAnalyzer",
    "build_index",
    "load_index",
    "build_call_maps",
    "find_all_paths",
]
