"""Static index query helpers (logic preserved)."""

from typing import Dict, List

from ... import static_analysis


def _query_callers(
    index_data: Dict, target: str, max_depth: int = 64, limit: int = 200
) -> List[List[str]]:
    callers_map, _ = static_analysis.build_call_maps(index_data)
    results: List[List[str]] = []

    def dfs(callee: str, path: List[str], depth: int):
        nonlocal results
        if len(results) >= limit or depth > max_depth:
            return
        parents = callers_map.get(callee, [])
        if not parents:
            results.append(path)
            return
        for caller in parents:
            if caller in path:
                continue
            dfs(caller, [caller] + path, depth + 1)

    dfs(target, [target], 0)
    return results


def _query_callees(
    index_data: Dict, target: str, transitive: bool = False, max_depth: int = 64
) -> List[str]:
    _, callees_map = static_analysis.build_call_maps(index_data)
    if not transitive:
        return sorted(set(callees_map.get(target, [])))
    seen = set()
    stack = [(target, 0)]
    while stack:
        node, depth = stack.pop()
        if depth > max_depth:
            continue
        for nb in callees_map.get(node, []):
            if nb not in seen:
                seen.add(nb)
                stack.append((nb, depth + 1))
    return sorted(seen)


def _query_find_paths(
    index_data: Dict, source: str, target: str, limit: int = 50, max_depth: int = 32
):
    _, forward = static_analysis.build_call_maps(index_data)
    return static_analysis.find_all_paths(
        source, target, forward, limit=limit, max_depth=max_depth
    )
