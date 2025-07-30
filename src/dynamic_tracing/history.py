"""Watched assignment history extraction for whyx CLI (logic preserved)."""

import json
import os
from typing import Dict, List


def get_watch_history(trace_file: str, target: str) -> List[Dict]:
    """Retrieve assignment history events for a watched target from a trace file."""
    with open(trace_file, "r", encoding="utf-8") as f:
        events = json.load(f)
    history: List[Dict] = []
    cwd = os.getcwd()
    for ev in events:
        if ev.get("type") == "assign" and ev.get("target") == target:
            file = ev.get("file", "<unknown>")
            line = ev.get("line", 0)
            func = ev.get("func", "<unknown>")
            val = ev.get("value", "")
            file_display = os.path.relpath(file, cwd) if file.startswith(cwd) else file
            history.append(
                {"file": file_display, "line": line, "func": func, "value": val}
            )
    return history
