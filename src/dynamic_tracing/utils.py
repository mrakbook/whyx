"""Shared helpers and constants for whyx dynamic tracing."""

from pathlib import Path
from typing import List, Tuple

_PARENT_PKG_PREFIX = __name__.rsplit(".", 1)[0]

IGNORED_MODULE_PREFIXES = ["whyx.", _PARENT_PKG_PREFIX]


def module_name_for_path(script_path: str) -> str:
    """Use the file stem as the module name (lab/demo.py -> 'demo')."""
    return Path(script_path).stem or "__main__"


def parse_watch_list(watch_list: List[str]) -> List[Tuple[str, str, str]]:
    """Parse 'module.Class.attr' strings into (module, class, attr)."""
    parsed: List[Tuple[str, str, str]] = []
    for watch in watch_list or []:
        try:
            mod_name, cls_name, attr_name = watch.rsplit(".", 2)
        except ValueError:
            continue
        parsed.append((mod_name, cls_name, attr_name))
    return parsed
