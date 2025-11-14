from pathlib import Path

from conftest import read_json, run_whyx


def test_index_and_static_queries_end_to_end(sample_project, base_env):
    project_dir, meta = sample_project

    cp = run_whyx(["--json", "index", str(project_dir)], cwd=project_dir, env=base_env)
    out = read_json(cp.stdout)

    index_file = Path(out["index_file"])
    assert index_file.exists(), f"Index file not created at {index_file}"
    assert out["functions"] == 9
    assert out["edges"] == 4

    cp = run_whyx(
        ["--json", "query", "callees", "acmeproj.a.a1", "--index", str(index_file)],
        cwd=project_dir,
        env=base_env,
    )
    q = read_json(cp.stdout)
    assert q["resolved"] == "acmeproj.a.a1"
    assert "acmeproj.b.b1" in q["callees"]

    cp = run_whyx(
        [
            "--json",
            "query",
            "callees",
            "acmeproj.a.a1",
            "--index",
            str(index_file),
            "--transitive",
        ],
        cwd=project_dir,
        env=base_env,
    )
    q = read_json(cp.stdout)
    assert set(q["callees"]) >= {"acmeproj.b.b1", "acmeproj.c.c1"}

    cp = run_whyx(
        ["--json", "query", "callers", "acmeproj.c.c1", "--index", str(index_file)],
        cwd=project_dir,
        env=base_env,
    )
    q = read_json(cp.stdout)
    assert q["resolved"] == "acmeproj.c.c1"
    chains = q["chains"]
    assert ["acmeproj.a.a1", "acmeproj.b.b1", "acmeproj.c.c1"] in chains

    cp = run_whyx(
        [
            "--json",
            "query",
            "find-path",
            "--from",
            "a.a1",
            "--to",
            "acmeproj.c.c1",
            "--index",
            str(index_file),
        ],
        cwd=project_dir,
        env=base_env,
    )
    q = read_json(cp.stdout)
    assert ["acmeproj.a.a1", "acmeproj.b.b1", "acmeproj.c.c1"] in q["paths"]

    cp = run_whyx(
        ["query", "callees", "shared", "--index", str(index_file)],
        cwd=project_dir,
        env=base_env,
    )
    text = cp.stdout
    assert "Ambiguous function 'shared'. Did you mean:" in text
    assert " - acmeproj.f.shared" in text
    assert " - acmeproj.g.shared" in text
