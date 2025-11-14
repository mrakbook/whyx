"""Legacy top-level synonym commands for backward compatibility."""
import os

from ._shared import load_or_build_index, resolve_symbol_suffix
from .static_index import _query_callers, _query_callees, _query_find_paths
from .dynamic_tracing import handle_query_history
from .help import LEG_CALLERS_HELP, LEG_CALLEES_HELP, LEG_FINDPATH_HELP, LEG_HISTORY_HELP


def _handle_callers(args):
    index_data = load_or_build_index(None, ".")
    target_in = args.function
    target_res, amb = resolve_symbol_suffix(index_data, target_in)
    if amb:
        print(f"Ambiguous function '{target_in}'. Did you mean:")
        for c in amb:
            print(f" - {c}")
        return
    target = target_res

    chains = _query_callers(index_data, target)
    if not chains:
        print(f"No callers found for {target}.")
    else:
        if target != target_in:
            print(f"(Resolved '{target_in}' -> '{target}')")
        print(f"{target} is called by:")
        for p in chains:
            print(" - " + " -> ".join(p))


def _handle_callees(args):
    index_data = load_or_build_index(None, ".")
    target_in = args.function
    target_res, amb = resolve_symbol_suffix(index_data, target_in)
    if amb:
        print(f"Ambiguous function '{target_in}'. Did you mean:")
        for c in amb:
            print(f" - {c}")
        return
    target = target_res

    result = _query_callees(index_data, target, transitive=False)
    if not result:
        print(f"{target} does not call any other functions directly.")
    else:
        if target != target_in:
            print(f"(Resolved '{target_in}' -> '{target}')")
        print(f"{target} directly calls:")
        for c in result:
            print(f" - {c}")


def _handle_findpath(args):
    index_data = load_or_build_index(None, ".")
    source_in = args.source
    target_in = args.target

    src_res, amb_s = resolve_symbol_suffix(index_data, source_in)
    tgt_res, amb_t = resolve_symbol_suffix(index_data, target_in)
    if amb_s or amb_t:
        if amb_s:
            print(f"Ambiguous source '{source_in}'. Did you mean:")
            for c in amb_s:
                print(f" - {c}")
        if amb_t:
            print(f"Ambiguous target '{target_in}'. Did you mean:")
            for c in amb_t:
                print(f" - {c}")
        return

    source = src_res
    target = tgt_res

    paths = _query_find_paths(index_data, source, target, limit=1, max_depth=64)
    if not paths:
        print(f"No call path found from {source} to {target}.")
    else:
        if (source != source_in) or (target != target_in):
            print(f"(Resolved '{source_in}' -> '{source}', '{target_in}' -> '{target}')")
        print("Call path found:")
        print(" -> ".join(paths[0]))


def _handle_history(args):
    class Shim:  # keep legacy args behavior
        pass

    shim = Shim()
    if args.arg2:
        shim.file = args.arg1
        shim.target = args.arg2
    else:
        shim.file = os.path.join(os.getcwd(), "whyx_trace.json")
        shim.target = args.arg1
    shim.json = False
    handle_query_history(shim)


def register_legacy_synonyms(subparsers):
    parser_callers = subparsers.add_parser("callers", help=LEG_CALLERS_HELP)
    parser_callers.add_argument("function", help="Target function")
    parser_callers.set_defaults(func=_handle_callers)

    parser_callees = subparsers.add_parser("callees", help=LEG_CALLEES_HELP)
    parser_callees.add_argument("function", help="Target function (fully qualified)")
    parser_callees.set_defaults(func=_handle_callees)

    parser_find = subparsers.add_parser("findpath", help=LEG_FINDPATH_HELP)
    parser_find.add_argument("source", help="Source function (fully qualified or resolvable suffix)")
    parser_find.add_argument("target", help="Target function (fully qualified or resolvable suffix)")
    parser_find.set_defaults(func=_handle_findpath)

    parser_history = subparsers.add_parser("history", help=LEG_HISTORY_HELP)
    parser_history.add_argument("arg1", help="Trace file path (if specifying file) or watched target name")
    parser_history.add_argument("arg2", nargs="?", help="Watched target name (if trace file provided as first argument)")
    parser_history.set_defaults(func=_handle_history)
