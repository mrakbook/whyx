"""Trace event search for whyx CLI (logic preserved)."""

import json
from typing import Dict, List, Optional


def search_trace(
    trace_file: str, pattern: str, event_type: Optional[str] = None
) -> List[Dict]:
    """Search events in a trace file. Returns a list of {'index': int, 'event': dict}."""
    with open(trace_file, "r", encoding="utf-8") as f:
        events = json.load(f)
    out: List[Dict] = []
    needle = pattern.lower()
    for i, ev in enumerate(events):
        if event_type and ev.get("type") != event_type:
            continue
        blob = json.dumps(ev, ensure_ascii=False)
        if needle in blob.lower():
            out.append({"index": i, "event": ev})
    return out
