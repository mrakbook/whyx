from pathlib import Path

from conftest import run_whyx


def test_legacy_synonym_commands(sample_project, base_env):
    project_dir, _ = sample_project

    cp = run_whyx(["callers", "c1"], cwd=project_dir, env=base_env)
    out = cp.stdout
    assert "(Resolved 'c1' -> 'acmeproj.c.c1')" in out
    assert "acmeproj.c.c1 is called by:" in out
    assert " - acmeproj.a.a1 -> acmeproj.b.b1 -> acmeproj.c.c1" in out

    cp = run_whyx(["callees", "acmeproj.a.a1"], cwd=project_dir, env=base_env)
    out = cp.stdout
    assert "acmeproj.a.a1 directly calls:" in out
    assert " - acmeproj.b.b1" in out

    cp = run_whyx(["findpath", "a.a1", "c.c1"], cwd=project_dir, env=base_env)
    out = cp.stdout
    assert "(Resolved 'a.a1' -> 'acmeproj.a.a1', 'c.c1' -> 'acmeproj.c.c1')" in out
    assert "Call path found:" in out
    assert "acmeproj.a.a1 -> acmeproj.b.b1 -> acmeproj.c.c1" in out

    cp = run_whyx(["callees", "shared"], cwd=project_dir, env=base_env)
    out = cp.stdout
    assert "Ambiguous function 'shared'. Did you mean:" in out
    assert " - acmeproj.f.shared" in out
    assert " - acmeproj.g.shared" in out
