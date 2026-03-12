from __future__ import annotations

from pathlib import Path
from typing import Any


SYSTEM_PROMPT = """You are a staff engineer helping a team formalize engineering conventions.
You will be given PR metadata, file summaries, and review/comment evidence.
Your job: extract conventions that are supported by evidence and write them as actionable rules.

Hard requirements:
- Output MUST be valid JSON only (no markdown fences).
- Keys MUST be exactly: coding_style_md, architecture_md, review_guidelines_md, cursor_rules
- cursor_rules MUST be an object with keys: coding_style_mdc, architecture_mdc, review_mdc
- If evidence is sparse, write conservative, generic-but-useful rules and explicitly mark them as "provisional".
"""


def _read_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def learn_and_write(
    corpus: Any,
    docs_dir: Path,
    cursor_rules_dir: Path,
    model: str,
    base_url: str | None,
    api_key: str | None,
) -> None:
    try:
        from openai import OpenAI  # type: ignore
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "Missing dependency 'openai'. Install with: pip install -r ai-pr-learning/requirements.txt"
        ) from e

    if not api_key:
        raise RuntimeError(
            "Missing inference API key. For GitHub Models, set GITHUB_MODELS_TOKEN (PAT with 'models' scope). "
            "Docs: https://docs.github.com/en/github-models/quickstart"
        )

    # GitHub Models provides an OpenAI-compatible API:
    # base_url should be "https://models.github.ai/inference"
    client = OpenAI(api_key=api_key, base_url=base_url)

    existing = {
        "coding_style_md": _read_if_exists(docs_dir / "coding-style.md"),
        "architecture_md": _read_if_exists(docs_dir / "architecture.md"),
        "review_guidelines_md": _read_if_exists(docs_dir / "review-guidelines.md"),
        "coding_style_mdc": _read_if_exists(cursor_rules_dir / "coding-style.mdc"),
        "architecture_mdc": _read_if_exists(cursor_rules_dir / "architecture.mdc"),
        "review_mdc": _read_if_exists(cursor_rules_dir / "review.mdc"),
    }

    user_payload = {
        "task": "Extract conventions and update docs + Cursor rules incrementally.",
        "existing": existing,
        "corpus": corpus.prs if hasattr(corpus, "prs") else corpus,
        "report": corpus.report if hasattr(corpus, "report") else {},
        "output_files": {
            "docs": ["coding-style.md", "architecture.md", "review-guidelines.md"],
            "cursor_rules": ["coding-style.mdc", "architecture.mdc", "review.mdc"],
        },
        "style_guide": {
            "prefer_bullets": True,
            "include_examples": True,
            "include_scope": "When rule applies, mention typical paths/filetypes if inferred.",
        },
    }

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": str(user_payload)},
        ],
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content or "{}"

    import json  # local import to keep module load light

    out = json.loads(content)

    (docs_dir / "coding-style.md").write_text(out.get("coding_style_md", ""), encoding="utf-8")
    (docs_dir / "architecture.md").write_text(out.get("architecture_md", ""), encoding="utf-8")
    (docs_dir / "review-guidelines.md").write_text(out.get("review_guidelines_md", ""), encoding="utf-8")

    rules = out.get("cursor_rules", {}) if isinstance(out.get("cursor_rules"), dict) else {}
    (cursor_rules_dir / "coding-style.mdc").write_text(rules.get("coding_style_mdc", ""), encoding="utf-8")
    (cursor_rules_dir / "architecture.mdc").write_text(rules.get("architecture_mdc", ""), encoding="utf-8")
    (cursor_rules_dir / "review.mdc").write_text(rules.get("review_mdc", ""), encoding="utf-8")

