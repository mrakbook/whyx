"""Static indexing + static query CLI wiring.

This package now splits the previous monolithic implementation into:
- queries.py   : low-level static query helpers (_query_callers/_query_callees/_query_find_paths)
- handlers.py  : CLI handlers for index and query subcommands
- commands.py  : argparse wiring to register all static-index related commands

Public API is preserved by re-exporting the original symbols.
"""

from .commands import register_static_index_commands
from .handlers import (
    handle_index,
    handle_query_callees,
    handle_query_callers,
    handle_query_find_paths,
)
from .queries import _query_callees, _query_callers, _query_find_paths

__all__ = [
    "_query_callers",
    "_query_callees",
    "_query_find_paths",
    "handle_index",
    "handle_query_callers",
    "handle_query_callees",
    "handle_query_find_paths",
    "register_static_index_commands",
]
