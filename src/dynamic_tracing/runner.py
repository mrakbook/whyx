"""
Execution runner & tracer for whyx CLI.

Implements `run_script` exactly as before (logic preserved), now isolated here.
"""

import inspect
import json
import os
import runpy
import sys
import threading
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from .utils import IGNORED_MODULE_PREFIXES, module_name_for_path, parse_watch_list


def run_script(
    script_path: str,
    trace: bool = False,
    watch_list: Optional[List[str]] = None,
    coverage: bool = False,
    output_file: Optional[str] = None,
) -> Dict:
    """
    Run the given Python script under tracing and/or watch instrumentation.

    WATCH TARGETS:
      Use the script's stem as the module name. For lab/demo.py, watch as:
        --watch demo.User.age
    """
    script_path = os.path.abspath(script_path)
    stem_name = module_name_for_path(script_path)

    watch_targets: List[Tuple[str, str, str]] = parse_watch_list(watch_list or [])
    events: List[Dict] = []
    modules_executed: Set[str] = set()

    patched_classes: Set[type] = set()
    original_setattr: Dict[type, object] = {}
    class_watch_specs: Dict[type, List[Tuple[str, str]]] = defaultdict(list)
    pending_indices: Set[int] = set(range(len(watch_targets)))
    all_watches_attached = len(pending_indices) == 0

    def get_frame_name(frame):
        code = frame.f_code
        func_name = code.co_name
        mod = frame.f_globals.get("__name__", "")
        if "self" in frame.f_locals:
            cls_name = frame.f_locals["self"].__class__.__name__
            if func_name != "<module>":
                return f"{mod}.{cls_name}.{func_name}"
        return f"{mod}.{func_name}"

    def install_patch_for_class(cls: type):
        if cls in patched_classes:
            return
        orig = getattr(cls, "__setattr__", None)
        original_setattr[cls] = orig

        def wrapped_setattr(self, name, value):
            specs = class_watch_specs.get(cls, [])
            if specs:
                for watched_attr, canonical_target in specs:
                    if name == watched_attr:
                        caller_frame = inspect.currentframe().f_back
                        if caller_frame:
                            func_fq = get_frame_name(caller_frame)
                            file = caller_frame.f_code.co_filename
                            line_no = caller_frame.f_lineno
                        else:
                            func_fq = "<unknown>"
                            file = "<unknown>"
                            line_no = 0
                        events.append(
                            {
                                "type": "assign",
                                "target": canonical_target,
                                "func": func_fq,
                                "file": file,
                                "line": line_no,
                                "value": repr(value),
                            }
                        )
            if orig:
                try:
                    orig(self, name, value)
                except TypeError:
                    object.__setattr__(self, name, value)
            else:
                object.__setattr__(self, name, value)

        setattr(cls, "__setattr__", wrapped_setattr)
        patched_classes.add(cls)

    def _runtime_aliases_for_module(mod_name: str) -> Set[str]:
        """
        If the runtime module is '__main__' and its __file__ equals script_path,
        consider the stem (e.g., 'demo') an alias so '--watch demo.Class.attr' matches.
        """
        aliases = {mod_name}
        mod = sys.modules.get(mod_name)
        try:
            mod_file = os.path.abspath(getattr(mod, "__file__", "")) if mod else ""
        except Exception:
            mod_file = ""
        if (
            mod_name == "__main__"
            and mod_file
            and os.path.abspath(script_path) == mod_file
        ):
            aliases.add(stem_name)
        return aliases

    def try_patch_for_runtime_module(mod_name: str):
        nonlocal all_watches_attached
        if all_watches_attached or not pending_indices:
            return
        mod = sys.modules.get(mod_name)
        if not mod:
            return

        aliases = _runtime_aliases_for_module(mod_name)
        to_remove: List[int] = []
        for idx in list(pending_indices):
            req_mod, cls_name, attr = watch_targets[idx]
            if req_mod not in aliases:
                continue
            cls_obj = getattr(mod, cls_name, None)
            if cls_obj is None or not isinstance(cls_obj, type):
                continue
            canonical_target = f"{req_mod}.{cls_name}.{attr}"
            specs = class_watch_specs.setdefault(cls_obj, [])
            if (attr, canonical_target) not in specs:
                specs.append((attr, canonical_target))
            install_patch_for_class(cls_obj)
            to_remove.append(idx)
        for idx in to_remove:
            pending_indices.discard(idx)
        all_watches_attached = len(pending_indices) == 0

    def trace_func(frame, event, arg):
        mod = frame.f_globals.get("__name__", "")
        for prefix in IGNORED_MODULE_PREFIXES:
            if mod.startswith(prefix):
                return trace_func

        if watch_targets:
            try_patch_for_runtime_module(mod)

        if event == "call":
            if coverage or trace:
                func_fq = get_frame_name(frame)
                if coverage:
                    top = func_fq.split(".")[0] if func_fq else ""
                    if top:
                        modules_executed.add(top)
                if trace:
                    events.append({"type": "call", "func": func_fq})
            return trace_func
        elif event == "return":
            if trace:
                try:
                    val = repr(arg)
                except Exception:
                    val = "<unreprizable>"
                func_fq = get_frame_name(frame)
                events.append({"type": "return", "func": func_fq, "value": val})
            return trace_func
        else:
            return trace_func

    if trace or watch_targets or coverage:
        sys.settrace(trace_func)
        threading.settrace(trace_func)

    try:
        runpy.run_path(script_path, run_name="__main__")
    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        sys.settrace(None)
        threading.settrace(None)
        for cls in patched_classes:
            if original_setattr.get(cls):
                setattr(cls, "__setattr__", original_setattr[cls])
            else:
                setattr(cls, "__setattr__", object.__setattr__)

    result_summary: Dict = {}
    if coverage:
        executed = sorted(m for m in modules_executed if m and not m.startswith("whyx"))
        result_summary["modules"] = executed
    if trace or watch_targets:
        if output_file is None:
            output_file = os.path.join(os.getcwd(), "whyx_trace.json")
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(events, f, indent=2)
            result_summary["trace_file"] = output_file
            result_summary["event_count"] = len(events)
        except Exception as e:
            print(f"Error writing trace to {output_file}: {e}")
    return result_summary
