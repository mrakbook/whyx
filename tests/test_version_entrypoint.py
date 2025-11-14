from conftest import run_whyx


def test_version_flag_works(repo_root, base_env):
    cp = run_whyx(["-V"], cwd=repo_root, env=base_env)
    out = cp.stdout.strip()
    assert out.startswith("whyx ")
    assert any(c.isdigit() for c in out)
