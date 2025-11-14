# From repo root
python srcips/test.py                # create .venv-tests, install pytest, run tests
python srcips/test.py --recreate     # nuke & rebuild the venv
python srcips/test.py --coverage     # run with coverage (installs pytest-cov)
python srcips/test.py -- --maxfail=1 -k e2e -q   # pass custom pytest args
