"""CLI handlers for dynamic tracing (logic preserved)."""

import json
import os

from ... import dynamic_tracing as dt
from .._shared import print_or_json


def handle_run(args):
    result = dt.run_script(
        args.script,
        trace=args.trace,
        watch_list=args.watch or [],
        coverage=args.coverage,
        output_file=args.output,
    )
    print_or_json(result, args.json)


def handle_diff(args):
    try:
        diff_report = dt.diff_traces(args.trace1, args.trace2)
    except Exception as e:
        print(f"Error diffing traces: {e}")
        return
    print_or_json(diff_report, args.json)


def handle_report(args):
    if not os.path.isfile(args.trace_file):
        print(f"Trace file {args.trace_file} not found.")
        return
    with open(args.trace_file, "r", encoding="utf-8") as f:
        events = json.load(f)
    counts = {}
    for ev in events:
        if ev.get("type") != "call":
            continue
        func = ev.get("func") or ""
        mod = func.split(".")[0] if "." in func else func
        if not mod or mod.startswith("whyx") or mod in {"__main__", "builtins"}:
            continue
        counts[mod] = counts.get(mod, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    if args.coverage:
        if args.top and args.top > 0:
            ranked = ranked[: args.top]
        out = [{"module": m, "calls": n} for m, n in ranked]
        print_or_json({"modules_touched": out}, args.json)
    else:
        print_or_json({"info": "Use --coverage to list modules touched"}, args.json)


def handle_query_history(args):
    if not os.path.isfile(args.file):
        print(f"Trace file {args.file} not found.")
        return
    try:
        history = dt.get_watch_history(args.file, args.target)
    except Exception as e:
        print(f"Error reading trace: {e}")
        return
    if args.json:
        print_or_json({"target": args.target, "history": history}, True)
    else:
        if not history:
            print(f"No assignments to {args.target} were recorded in the trace.")
        else:
            for ev in history:
                file = ev["file"]
                line = ev["line"]
                func = ev["func"]
                val = ev["value"]
                func_name = func.split(".")[-1] if func else func
                print(f"{file}:{line} - {args.target} set to {val} (by {func_name})")


def handle_query_trace_search(args):
    trace_file = (
        args.trace_file
        or args.trace_file_flag
        or os.path.join(os.getcwd(), "whyx_trace.json")
    )
    if not os.path.isfile(trace_file):
        print(f"Trace file {trace_file} not found.")
        return

    pattern = getattr(args, "pattern", None) or getattr(args, "pattern_alt", None)
    if not pattern:
        print("You must supply a search pattern via --contains or --event.")
        return

    matches = dt.search_trace(trace_file, pattern=pattern, event_type=args.type)
    if args.json:
        print_or_json(
            {
                "file": trace_file,
                "pattern": pattern,
                "type": args.type,
                "matches": matches,
            },
            True,
        )
    else:
        if not matches:
            print("No matching events found.")
        else:
            print(f"Found {len(matches)} matching event(s):")
            for m in matches:
                idx = m["index"]
                ev = m["event"]
                print(f"[{idx}] {ev}")
