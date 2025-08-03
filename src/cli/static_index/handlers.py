"""CLI handlers for static indexing and static queries (logic preserved)."""

import os

from ... import static_analysis
from .._shared import load_or_build_index, print_or_json, resolve_symbol_suffix
from .queries import _query_callees, _query_callers, _query_find_paths


def handle_index(args):
    proj_path = args.path
    output = args.output or os.path.join(proj_path, ".whyx_index.json")
    index_data = static_analysis.build_index(proj_path, output_file=output)
    out = {
        "project": proj_path,
        "functions": len(index_data["functions"]),
        "edges": len(index_data["edges"]),
        "index_file": output,
    }
    print_or_json(out, args.json)


def handle_query_callers(args):
    index_data = load_or_build_index(args.index, args.project)
    target_in = args.function
    target_res, amb = resolve_symbol_suffix(index_data, target_in)
    if amb:
        if args.json:
            print_or_json(
                {"error": "ambiguous", "input": target_in, "candidates": amb}, True
            )
        else:
            print(f"Ambiguous function '{target_in}'. Did you mean:")
            for c in amb:
                print(f" - {c}")
        return

    target = target_res
    chains = _query_callers(
        index_data, target, max_depth=args.max_depth, limit=args.limit
    )
    if args.json:
        print_or_json({"target": target_in, "resolved": target, "chains": chains}, True)
    else:
        if target != target_in:
            print(f"(Resolved '{target_in}' -> '{target}')")
        if not chains:
            print(f"No callers found for {target}.")
        else:
            print(f"{target} is called by:")
            for p in chains:
                print(" - " + " -> ".join(p))


def handle_query_callees(args):
    index_data = load_or_build_index(args.index, args.project)
    target_in = args.function
    target_res, amb = resolve_symbol_suffix(index_data, target_in)
    if amb:
        if args.json:
            print_or_json(
                {"error": "ambiguous", "input": target_in, "candidates": amb}, True
            )
        else:
            print(f"Ambiguous function '{target_in}'. Did you mean:")
            for c in amb:
                print(f" - {c}")
        return

    target = target_res
    result = _query_callees(index_data, target, transitive=args.transitive)
    if args.json:
        print_or_json(
            {
                "target": target_in,
                "resolved": target,
                "callees": result,
                "transitive": args.transitive,
            },
            True,
        )
    else:
        if target != target_in:
            print(f"(Resolved '{target_in}' -> '{target}')")
        if not result:
            print(
                f"{target} does not call any other functions directly."
                if not args.transitive
                else f"No transitive callees found for {target}."
            )
        else:
            header = "directly calls" if not args.transitive else "transitively calls"
            print(f"{target} {header}:")
            for c in result:
                print(f" - {c}")


def handle_query_find_paths(args):
    index_data = load_or_build_index(args.index, args.project)

    src_in = args.source
    tgt_in = args.target
    src_res, amb_s = resolve_symbol_suffix(index_data, src_in)
    tgt_res, amb_t = resolve_symbol_suffix(index_data, tgt_in)

    if amb_s or amb_t:
        if args.json:
            print_or_json(
                {
                    "error": "ambiguous",
                    "from_input": src_in,
                    "from_candidates": amb_s,
                    "to_input": tgt_in,
                    "to_candidates": amb_t,
                },
                True,
            )
        else:
            if amb_s:
                print(f"Ambiguous source '{src_in}'. Did you mean:")
                for c in amb_s:
                    print(f" - {c}")
            if amb_t:
                print(f"Ambiguous target '{tgt_in}'. Did you mean:")
                for c in amb_t:
                    print(f" - {c}")
        return

    src = src_res
    tgt = tgt_res

    paths = _query_find_paths(
        index_data, src, tgt, limit=args.limit, max_depth=args.max_depth
    )
    if args.json:
        print_or_json(
            {
                "source": src_in,
                "source_resolved": src,
                "target": tgt_in,
                "target_resolved": tgt,
                "paths": paths,
            },
            True,
        )
    else:
        any_resolved = (src != src_in) or (tgt != tgt_in)
        if any_resolved:
            print(
                f"(Resolved '--from {src_in}' -> '{src}', '--to {tgt_in}' -> '{tgt}')"
            )
        if not paths:
            print(f"No call path found from {src} to {tgt}.")
        else:
            print(f"Found {len(paths)} path(s):")
            for p in paths:
                print(" - " + " -> ".join(p))
