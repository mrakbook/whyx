"""Trace differencing for whyx CLI (logic preserved)."""

import json
from typing import Dict, List


def diff_traces(trace_file1: str, trace_file2: str) -> Dict:
    """Compare two execution trace logs and return a structured report of differences."""
    try:
        with open(trace_file1, "r", encoding="utf-8") as f1:
            old_events = json.load(f1)
        with open(trace_file2, "r", encoding="utf-8") as f2:
            new_events = json.load(f2)
    except Exception as e:
        raise FileNotFoundError(f"Could not load trace files: {e}")

    old_edges = set()
    new_edges = set()
    old_returns: Dict[str, List[str]] = {}
    new_returns: Dict[str, List[str]] = {}
    old_watches: Dict[str, List[str]] = {}
    new_watches: Dict[str, List[str]] = {}

    def process_events(events, edges_set, returns_map, watch_map):
        call_stack: List[str] = []
        for ev in events:
            t = ev.get("type")
            if t == "call":
                f = ev.get("func")
                if call_stack:
                    edges_set.add((call_stack[-1], f))
                call_stack.append(f)
            elif t == "return":
                f = ev.get("func")
                if call_stack and call_stack[-1] == f:
                    call_stack.pop()
                returns_map.setdefault(f, []).append(ev.get("value"))
            elif t == "assign":
                target = ev.get("target")
                watch_map.setdefault(target, []).append(ev.get("value"))

    process_events(old_events, old_edges, old_returns, old_watches)
    process_events(new_events, new_edges, new_returns, new_watches)

    report = {
        "added_calls": sorted([e for e in new_edges if e not in old_edges]),
        "removed_calls": sorted([e for e in old_edges if e not in new_edges]),
        "changed_returns": {},
        "watch_diffs": {},
    }
    for f, ov in old_returns.items():
        if f in new_returns and set(ov) != set(new_returns[f]):
            report["changed_returns"][f] = {"old": ov, "new": new_returns[f]}
    for tgt, ov in old_watches.items():
        if tgt in new_watches:
            nv = new_watches[tgt]
            if ov != nv:
                report["watch_diffs"][tgt] = {"old": ov, "new": nv}
        else:
            report["watch_diffs"][tgt] = {"old": ov, "new": None}
    for tgt, nv in new_watches.items():
        if tgt not in old_watches:
            report["watch_diffs"][tgt] = {"old": None, "new": nv}
    return report
