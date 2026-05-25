# Contributing to cognitive-agent-core

Thank you for your interest in contributing! This guide will get you up and running.

## Setup

```bash
git clone https://github.com/AkshatRaj00/cognitive-agent-core
cd cognitive-agent-core
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v --cov=core --cov-report=term-missing
```

## Code Style

- Follow PEP 8, enforced via `ruff`
- Type hints on all public methods
- Google-style docstrings
- Run `ruff check . --fix` before committing

## Pull Request Process

1. Fork the repo and create a feature branch: `git checkout -b feat/your-feature`
2. Write tests for your changes
3. Ensure all tests pass: `pytest tests/`
4. Update `docs/api.md` if you change the public API
5. Open a PR against `main` with a clear description

## Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(scope): short description
fix(scope): short description
docs: what was documented
test(scope): what was tested
refactor(scope): what changed internally
```

## Code of Conduct

Be kind, be constructive, be collaborative. 🙌
