"""
`whyx query` umbrella: hosts subcommands from each feature.
This module wires only the query subcommands if you want to use it directly.
(Current CLI entrypoint uses direct registration in cli/__main__.py.)
"""

from __future__ import annotations

import argparse

from ..dynamic_tracing import register_dynamic_tracing_commands
from ..static_index import register_static_index_commands


def register(subparsers: argparse._SubParsersAction) -> None:
    parser_query = subparsers.add_parser("query", help="Static/dynamic queries")
    qsubs = parser_query.add_subparsers(dest="query_cmd", required=True)

    register_static_index_commands(subparsers, qsubs)
    register_dynamic_tracing_commands(subparsers, qsubs)
