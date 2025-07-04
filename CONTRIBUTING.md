# Contributing to whyx

Thanks for considering a contribution! This repo aims to be a friendly, practical tool for code exploration.

## Ground rules

- Be respectful and follow the **[Code of Conduct](CODE_OF_CONDUCT.md)**.
- Small, focused PRs are easier to review.
- Prefer descriptive commit messages (Conventional Commits are welcome, not required).
- By contributing, you agree your contributions are licensed under the repo's **MIT License**.

## Quick dev setup

```bash
git clone <your-fork-url> whyx
cd whyx
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
# No packaging needed; run the CLI directly:
python -m src.cli --version
```

## Running commands during development

```bash
# Build a static index for the current project
python -m src.cli index .

# Query callers, callees, or find paths
python -m src.cli query callers package.module.func
python -m src.cli query callees package.module.func --transitive
python -m src.cli query find-path --from a.b.src --to x.y.tgt

# Dynamic tracing
python -m src.cli run --trace examples/demo.py
python -m src.cli run --watch demo.User.age examples/demo.py
python -m src.cli run --coverage examples/demo.py
```

## Coding style

- Use type hints where reasonable.
- Keep functions small and readable.
- Prefer clear naming and docstrings over cleverness.
- Add/adjust docs in `README.md` as features evolve.

## Tests

- If you add behavior that can be tested deterministically, please include tests (a `tests/` folder is welcome).
- For CLI behavior, snapshotting `--json` output is a good approach.

## Pull request checklist

- [ ] The change is explained in the PR description.
- [ ] Relevant docs were updated (README / CHANGELOG).
- [ ] No unrelated refactors mixed into the PR.
- [ ] Added tests or rationale for why tests aren't needed right now.

## Releasing

- Update `__version__` in `src/__init__.py`.
- Update `CHANGELOG.md`.
- Tag the release in Git.
