# AI PR Learning (GitHub PR → Docs + Cursor Rules)

Run one command to learn engineering conventions from GitHub PR diffs + comments, then write:

- `docs/coding-style.md`
- `docs/architecture.md`
- `docs/review-guidelines.md`
- `.cursor/rules/coding-style.mdc`
- `.cursor/rules/architecture.mdc`
- `.cursor/rules/review.mdc`

## Setup

Create and activate a virtualenv, then install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r ai-pr-learning/requirements.txt
```

Environment variables:

```bash
export GITHUB_TOKEN="..."
export GITHUB_REPO="org/repo"   # e.g. octocat/Hello-World
# GitHub Models (recommended): PAT with `models` scope
export GITHUB_MODELS_TOKEN="..."
```

Optional:

```bash
export MAX_PRS=30
export OPENAI_MODEL="openai/gpt-4o"
```

## Run

```bash
python ai-pr-learning/run_learning.py
```

Artifacts are written to:

- `docs/` (repo root)
- `.cursor/rules/` (repo root)

Raw fetched PR data is cached under `ai-pr-learning/data/`.

