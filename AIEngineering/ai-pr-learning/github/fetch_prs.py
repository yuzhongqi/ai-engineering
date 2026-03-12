from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from github.client import GITHUB_API, GitHubClient


@dataclass(frozen=True)
class StoredPR:
    number: int
    dir: Path


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_and_store_prs(repo: str, token: str, max_prs: int, out_dir: Path) -> dict[str, Any]:
    """
    Fetch recent closed PRs and store raw payloads for reproducible learning.

    Layout:
      out_dir/pr_<number>/
        pr.json
        files.json
        issue_comments.json
        review_comments.json
        reviews.json
    """
    cache_dir = out_dir / ".http_cache"
    gh = GitHubClient(token=token, cache_dir=cache_dir)

    pulls_url = f"{GITHUB_API}/repos/{repo}/pulls"
    prs: list[dict[str, Any]] = []
    for pr in gh.paginate(pulls_url, params={"state": "closed", "per_page": 100, "sort": "updated", "direction": "desc"}):
        if not isinstance(pr, dict) or "number" not in pr:
            continue
        prs.append(pr)
        if len(prs) >= max_prs:
            break

    pr_numbers: list[int] = []
    for pr in prs:
        number = int(pr["number"])
        pr_numbers.append(number)

        pr_dir = out_dir / f"pr_{number}"
        pr_dir.mkdir(parents=True, exist_ok=True)

        pr_api = f"{GITHUB_API}/repos/{repo}/pulls/{number}"
        pr_full = gh.get_json(pr_api, cache_key=f"pr:{repo}:{number}")
        _write_json(pr_dir / "pr.json", pr_full)

        files_api = f"{GITHUB_API}/repos/{repo}/pulls/{number}/files"
        files = list(gh.paginate(files_api, params={"per_page": 100}))
        _write_json(pr_dir / "files.json", files)

        issue_comments_api = f"{GITHUB_API}/repos/{repo}/issues/{number}/comments"
        issue_comments = list(gh.paginate(issue_comments_api, params={"per_page": 100}))
        _write_json(pr_dir / "issue_comments.json", issue_comments)

        review_comments_api = f"{GITHUB_API}/repos/{repo}/pulls/{number}/comments"
        review_comments = list(gh.paginate(review_comments_api, params={"per_page": 100}))
        _write_json(pr_dir / "review_comments.json", review_comments)

        reviews_api = f"{GITHUB_API}/repos/{repo}/pulls/{number}/reviews"
        reviews = list(gh.paginate(reviews_api, params={"per_page": 100}))
        _write_json(pr_dir / "reviews.json", reviews)

    index = {"repo": repo, "max_prs": max_prs, "pr_numbers": pr_numbers}
    _write_json(out_dir / "index.json", index)
    return index

