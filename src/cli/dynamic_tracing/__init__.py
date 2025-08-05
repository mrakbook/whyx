"""Dynamic tracing CLI wiring.

This package now splits the previous monolithic implementation into:
- handlers.py  : CLI handlers for run/diff/report/history/trace-search
- commands.py  : argparse wiring to register dynamic tracing commands

Public API is preserved by re-exporting the original symbols so existing imports like
`from .dynamic_tracing import register_dynamic_tracing_commands` and
`from .dynamic_tracing import handle_query_history` continue to work.
"""

from .commands import register_dynamic_tracing_commands
from .handlers import (
    handle_diff,
    handle_query_history,
    handle_query_trace_search,
    handle_report,
    handle_run,
)

__all__ = [
    "handle_run",
    "handle_diff",
    "handle_report",
    "handle_query_history",
    "handle_query_trace_search",
    "register_dynamic_tracing_commands",
]
