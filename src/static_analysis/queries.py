"""Query helpers for whyx static analysis (logic preserved)."""

from typing import Dict, List, Set, Tuple


def build_call_maps(
    index_data: Dict,
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    From an index, build:
      - callers_map: callee -> [callers]
      - callees_map: caller -> [callees]
    """
    edges = index_data.get("edges", [])
    callers_map: Dict[str, List[str]] = {}
    callees_map: Dict[str, List[str]] = {}
    for caller, callee in set(tuple(e) for e in edges):
        callers_map.setdefault(callee, []).append(caller)
        callees_map.setdefault(caller, []).append(callee)
    for m in (callers_map, callees_map):
        for k in m:
            m[k] = sorted(set(m[k]))
    return callers_map, callees_map


def find_all_paths(
    source: str,
    target: str,
    forward_adj: Dict[str, List[str]],
    limit: int = 50,
    max_depth: int = 32,
) -> List[List[str]]:
    """
    Enumerate up to `limit` simple call paths from `source` to `target` using DFS (bounded by `max_depth`).
    """
    results: List[List[str]] = []
    path: List[str] = []

    def dfs(node: str, depth: int, visited: Set[str]):
        if len(results) >= limit or depth > max_depth:
            return
        visited.add(node)
        path.append(node)
        if node == target:
            results.append(list(path))
        else:
            for nb in forward_adj.get(node, []):
                if nb not in visited:
                    dfs(nb, depth + 1, visited)
        path.pop()
        visited.remove(node)

    dfs(source, 0, set())
    return results
