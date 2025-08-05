"""Argparse wiring for dynamic tracing CLI (logic preserved)."""

import os

from ..help import DIFF_HELP, Q_HISTORY_HELP, Q_SEARCH_HELP, REPORT_HELP, RUN_HELP
from .handlers import (
    handle_diff,
    handle_query_history,
    handle_query_trace_search,
    handle_report,
    handle_run,
)


def register_dynamic_tracing_commands(subparsers, query_subparsers):
    parser_run = subparsers.add_parser("run", help=RUN_HELP)
    parser_run.add_argument(
        "--trace",
        action="store_true",
        help="Trace all function calls and returns during execution",
    )
    parser_run.add_argument(
        "--watch",
        action="append",
        metavar="TARGET",
        help="Watch assignments to a class attribute (e.g. module.Class.attr). Can be used multiple times.",
    )
    parser_run.add_argument(
        "--coverage",
        action="store_true",
        help="Collect coverage info (modules executed)",
    )
    parser_run.add_argument(
        "-o", "--output", help="File to save the execution trace (JSON)"
    )
    parser_run.add_argument("script", help="Path to the Python script to run")
    parser_run.set_defaults(func=handle_run)

    parser_diff = subparsers.add_parser("diff", help=DIFF_HELP)
    parser_diff.add_argument("trace1", help="First trace file (JSON)")
    parser_diff.add_argument("trace2", help="Second trace file (JSON)")
    parser_diff.set_defaults(func=handle_diff)

    parser_report = subparsers.add_parser("report", help=REPORT_HELP)
    parser_report.add_argument(
        "trace_file", help="Trace JSON file produced by `whyx run`"
    )
    parser_report.add_argument(
        "--coverage", action="store_true", help="List modules touched"
    )
    parser_report.add_argument(
        "--top", type=int, default=0, help="Show only top N modules (by call events)"
    )
    parser_report.set_defaults(func=handle_report)

    parser_q_history = query_subparsers.add_parser("history", help=Q_HISTORY_HELP)
    parser_q_history.add_argument(
        "target", help="Watched target, e.g. module.Class.attr"
    )
    parser_q_history.add_argument(
        "--file",
        default=os.path.join(os.getcwd(), "whyx_trace.json"),
        help="Trace file path (default: ./whyx_trace.json)",
    )
    parser_q_history.set_defaults(func=handle_query_history)

    parser_q_search = query_subparsers.add_parser("trace-search", help=Q_SEARCH_HELP)
    parser_q_search.add_argument(
        "trace_file", nargs="?", help="Trace file path (default: ./whyx_trace.json)"
    )
    parser_q_search.add_argument(
        "--file",
        dest="trace_file_flag",
        help="(Alt) explicit trace file path (deprecated; use positional TRACE_FILE)",
    )
    parser_q_search.add_argument(
        "--contains", dest="pattern", help="Case-insensitive substring to search for"
    )
    parser_q_search.add_argument(
        "--event",
        dest="pattern_alt",
        help="(Alias for --contains) Case-insensitive substring to search for",
    )
    parser_q_search.add_argument(
        "--type",
        choices=["call", "return", "assign"],
        help="Optional event type filter",
    )
    parser_q_search.set_defaults(func=handle_query_trace_search)
