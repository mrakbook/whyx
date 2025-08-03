"""Argparse wiring for static indexing & queries (logic preserved)."""

from ..help import INDEX_HELP, Q_CALLEES_HELP, Q_CALLERS_HELP, Q_FINDPATH_HELP
from .handlers import (
    handle_index,
    handle_query_callees,
    handle_query_callers,
    handle_query_find_paths,
)


def register_static_index_commands(subparsers, query_subparsers):
    parser_index = subparsers.add_parser("index", help=INDEX_HELP)
    parser_index.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to project (default: current directory)",
    )
    parser_index.add_argument(
        "-o", "--output", help="File path to save the index (JSON)"
    )
    parser_index.set_defaults(func=handle_index)

    parser_q_callers = query_subparsers.add_parser("callers", help=Q_CALLERS_HELP)
    parser_q_callers.add_argument(
        "function", help="Target function (e.g. module.Func or module.Class.method)"
    )
    parser_q_callers.add_argument(
        "--index",
        help="Path to a saved index JSON; defaults to ./.whyx_index.json or builds in-memory",
    )
    parser_q_callers.add_argument(
        "--project", default=".", help="Project root when building index if none exists"
    )
    parser_q_callers.add_argument(
        "--max-depth", type=int, default=64, help="Max depth when walking callers"
    )
    parser_q_callers.add_argument(
        "--limit", type=int, default=200, help="Limit number of call chains returned"
    )
    parser_q_callers.set_defaults(func=handle_query_callers)

    parser_q_callees = query_subparsers.add_parser("callees", help=Q_CALLEES_HELP)
    parser_q_callees.add_argument("function", help="Target function (fully qualified)")
    parser_q_callees.add_argument("--index", help="Path to a saved index JSON")
    parser_q_callees.add_argument(
        "--project", default=".", help="Project root when building index if none exists"
    )
    parser_q_callees.add_argument(
        "--transitive", action="store_true", help="Return transitive callees"
    )
    parser_q_callees.set_defaults(func=handle_query_callees)

    parser_q_find = query_subparsers.add_parser("find-path", help=Q_FINDPATH_HELP)
    parser_q_find.add_argument(
        "--from",
        dest="source",
        required=True,
        help="Source function (fully qualified or resolvable suffix)",
    )
    parser_q_find.add_argument(
        "--to",
        dest="target",
        required=True,
        help="Target function (fully qualified or resolvable suffix)",
    )
    parser_q_find.add_argument("--index", help="Path to a saved index JSON")
    parser_q_find.add_argument(
        "--project", default=".", help="Project root when building index if none exists"
    )
    parser_q_find.add_argument(
        "--limit", type=int, default=50, help="Limit number of paths returned"
    )
    parser_q_find.add_argument(
        "--max-depth", type=int, default=32, help="Maximum depth of paths"
    )
    parser_q_find.set_defaults(func=handle_query_find_paths)
