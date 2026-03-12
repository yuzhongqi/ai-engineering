from __future__ import annotations

import json
from pathlib import Path

from config import load_settings
from extractors.evidence import build_learning_corpus
from github.fetch_prs import fetch_and_store_prs


def main() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:  # noqa: BLE001
        load_dotenv = None
    if load_dotenv is not None:
        load_dotenv()
    settings = load_settings()

    settings.data_dir.mkdir(parents=True, exist_ok=True)

    raw_dir = settings.data_dir / "prs_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    index = fetch_and_store_prs(
        repo=settings.github_repo,
        token=settings.github_token,
        max_prs=settings.max_prs,
        out_dir=raw_dir,
    )

    corpus = build_learning_corpus(raw_dir=raw_dir, pr_numbers=list(index.get("pr_numbers", [])))

    settings.docs_dir.mkdir(parents=True, exist_ok=True)
    settings.cursor_rules_dir.mkdir(parents=True, exist_ok=True)

    from learner.ai_learner import learn_and_write

    learn_and_write(
        corpus=corpus,
        docs_dir=settings.docs_dir,
        cursor_rules_dir=settings.cursor_rules_dir,
        model=settings.openai_model,
        base_url=settings.inference_base_url,
        api_key=settings.inference_api_key,
    )

    report_path = settings.data_dir / "latest_learning_report.json"
    report_path.write_text(json.dumps(corpus.report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("AI learning complete.")
    print(f"- Docs: {settings.docs_dir}")
    print(f"- Cursor rules: {settings.cursor_rules_dir}")
    print(f"- Raw PR data: {raw_dir}")


if __name__ == "__main__":
    main()

