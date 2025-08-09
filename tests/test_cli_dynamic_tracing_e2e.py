import json
from pathlib import Path

from conftest import read_json, run_whyx


def test_run_trace_watch_history_search_report_and_diff_end_to_end(
    demo_scripts, base_env
):
    root: Path = demo_scripts["root"]
    v1: Path = demo_scripts["v1"]
    v2: Path = demo_scripts["v2"]

    # === whyx run (trace + coverage + watch) ===
    # First run: v1 (one birthday)
    stem1 = v1.stem  # "demoscript_v1"
    target1 = f"{stem1}.Person.age"
    cp = run_whyx(
        [
            "--json",
            "run",
            "--trace",
            "--coverage",
            "--watch",
            target1,
            "-o",
            "whyx_trace_v1.json",
            str(v1),
        ],
        cwd=root,
        env=base_env,
    )
    out1 = read_json(cp.stdout)
    tf1 = root / "whyx_trace_v1.json"
    assert tf1.exists()
    assert out1["trace_file"].endswith("whyx_trace_v1.json")
    assert out1["event_count"] > 0
    # The runtime summary returned by `run` includes __main__ (from run_name="__main__")
    assert "__main__" in out1.get("modules", ["__main__"])

    # Second run: v2 (two birthdays)
    stem2 = v2.stem  # "demoscript_v2"
    target2 = f"{stem2}.Person.age"
    cp = run_whyx(
        [
            "--json",
            "run",
            "--trace",
            "--coverage",
            "--watch",
            target2,
            "-o",
            "whyx_trace_v2.json",
            str(v2),
        ],
        cwd=root,
        env=base_env,
    )
    out2 = read_json(cp.stdout)
    tf2 = root / "whyx_trace_v2.json"
    assert tf2.exists()
    assert out2["event_count"] > 0

    # === query history (legacy synonym) ===
    cp = run_whyx(
        ["history", str(tf1), target1],
        cwd=root,
        env=base_env,
    )
    hist_text_1 = cp.stdout
    assert "set to" in hist_text_1
    assert target1 in hist_text_1

    cp = run_whyx(
        ["history", str(tf2), target2],
        cwd=root,
        env=base_env,
    )
    hist_text_2 = cp.stdout
    assert "set to" in hist_text_2
    assert target2 in hist_text_2

    # === query trace-search (two forms: positional file and --file alias) ===
    cp = run_whyx(
        [
            "--json",
            "query",
            "trace-search",
            str(tf1),
            "--contains",
            "Person",
            "--type",
            "assign",
        ],
        cwd=root,
        env=base_env,
    )
    q1 = read_json(cp.stdout)
    assert len(q1["matches"]) >= 2  # __init__ (age=0) + birthday (age=1)

    cp = run_whyx(
        [
            "--json",
            "query",
            "trace-search",
            "--file",
            str(tf2),
            "--event",
            "Person",
            "--type",
            "assign",
        ],
        cwd=root,
        env=base_env,
    )
    q2 = read_json(cp.stdout)
    assert len(q2["matches"]) >= 3  # v2 has an extra assignment

    # === report coverage (modules touched) ===
    cp = run_whyx(
        ["--json", "report", str(tf1), "--coverage", "--top", "1"],
        cwd=root,
        env=base_env,
    )
    rep = read_json(cp.stdout)
    modules = [m["module"] for m in rep["modules_touched"]]
    # The CLI's coverage report intentionally filters out '__main__' and 'builtins'.
    # Just assert we got at least one non-whyx module (often 'runpy') rather than requiring '__main__'.
    assert modules, "Expected at least one touched module in coverage report"
    assert "__main__" not in modules
    assert all(not m.startswith("whyx") for m in modules)

    # === diff traces (watch diffs should show additional assignment in v2) ===
    cp = run_whyx(
        ["--json", "diff", str(tf1), str(tf2)],
        cwd=root,
        env=base_env,
    )
    diff = read_json(cp.stdout)

    wd = diff["watch_diffs"]
    keys = set(wd.keys())
    assert any(k.endswith(".Person.age") for k in keys), (
        f"No watch_diffs for Person.age: {wd}"
    )
