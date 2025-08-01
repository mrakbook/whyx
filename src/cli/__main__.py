#!/usr/bin/env python3
"""
whyx CLI single entrypoint.

Why this file?
- Python uses package/__main__.py when you run:  `python -m src.cli`
- We keep all CLI wiring here so there’s a single, obvious entrypoint.
"""

import argparse

from ._shared import DISPLAY_VERSION
from .dynamic_tracing import register_dynamic_tracing_commands
from .help import CLI_DESCRIPTION, QUERY_HELP
from .static_index import register_static_index_commands
from .synonyms import register_legacy_synonyms


def main():
    parser = argparse.ArgumentParser(prog="whyx", description=CLI_DESCRIPTION)
    parser.add_argument(
        "-V", "--version", action="version", version=f"whyx {DISPLAY_VERSION}"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results as JSON when applicable"
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Sub-command to run"
    )

    parser_query = subparsers.add_parser("query", help=QUERY_HELP)
    qsubs = parser_query.add_subparsers(dest="query_cmd", required=True)

    register_static_index_commands(subparsers, qsubs)
    register_dynamic_tracing_commands(subparsers, qsubs)

    register_legacy_synonyms(subparsers)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
