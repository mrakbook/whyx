"""
Dynamic Tracing module for whyx CLI.

This package exposes the same public API as before, but its implementation
is now split across smaller modules:

- runner.py     : run_script (tracing, watchpoints, coverage)
- diffing.py    : diff_traces (trace diff)
- history.py    : get_watch_history (watched assignments)
- search.py     : search_trace (trace event search)
- utils.py      : shared helpers/constants

Public API is preserved to avoid any CLI or import changes.
"""

from .diffing import diff_traces
from .history import get_watch_history
from .runner import run_script
from .search import search_trace

__all__ = [
    "run_script",
    "diff_traces",
    "get_watch_history",
    "search_trace",
]
