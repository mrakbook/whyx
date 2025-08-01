"""CLI package for whyx (feature-based, src-root).

Structure:
- cli/help/                : help/description
- cli/_shared.py           : shared helpers (version display, index loading/building)
- cli/dynamic_tracing/     : tracing CLI (run/diff/report + query history/search)
- cli/static_index/        : static analysis CLI (index + query callers/callees/find-path)
- cli/synonyms.py          : legacy top-level synonyms
- cli/__main__.py          : the single CLI entrypoint (`python -m src.cli`)
"""
