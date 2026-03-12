from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env(name: str, default: str | None = None) -> str | None:
    v = os.environ.get(name)
    if v is None:
        return default
    v = v.strip()
    return v or default


@dataclass(frozen=True)
class Settings:
    repo_root: Path

    github_token: str
    github_repo: str
    max_prs: int

    inference_base_url: str | None
    inference_api_key: str | None
    openai_model: str

    data_dir: Path
    docs_dir: Path
    cursor_rules_dir: Path


def load_settings() -> Settings:
    repo_root = Path(__file__).resolve().parents[1]

    github_token = _env("GITHUB_TOKEN")
    github_repo = _env("GITHUB_REPO")
    if not github_token:
        raise RuntimeError("Missing env var GITHUB_TOKEN")
    if not github_repo:
        raise RuntimeError("Missing env var GITHUB_REPO (e.g. org/repo)")

    max_prs_raw = _env("MAX_PRS", "30")
    try:
        max_prs = int(max_prs_raw)  # type: ignore[arg-type]
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Invalid MAX_PRS: {max_prs_raw!r}") from e

    # Inference provider (Option B: GitHub Models)
    # Docs: https://docs.github.com/en/github-models/quickstart
    # OpenAI-compatible base: https://models.github.ai/inference
    github_models_token = _env("GITHUB_MODELS_TOKEN") or _env("GITHUB_TOKEN")
    inference_base_url = _env("INFERENCE_BASE_URL") or "https://models.github.ai/inference"
    inference_api_key = _env("INFERENCE_API_KEY") or github_models_token

    default_model = "openai/gpt-4o" if inference_api_key else "gpt-5"
    openai_model = _env("OPENAI_MODEL", default_model) or default_model

    data_dir = Path(__file__).resolve().parent / "data"
    docs_dir = repo_root / "docs"
    cursor_rules_dir = repo_root / ".cursor" / "rules"

    return Settings(
        repo_root=repo_root,
        github_token=github_token,
        github_repo=github_repo,
        max_prs=max_prs,
        inference_base_url=inference_base_url,
        inference_api_key=inference_api_key,
        openai_model=openai_model,
        data_dir=data_dir,
        docs_dir=docs_dir,
        cursor_rules_dir=cursor_rules_dir,
    )

