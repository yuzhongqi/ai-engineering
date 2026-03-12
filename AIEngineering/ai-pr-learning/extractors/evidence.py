from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LearningCorpus:
    """
    Model-friendly corpus extracted from raw PR payloads.
    Keep this small and high-signal: comments + relevant patches + file summaries.
    """

    prs: list[dict[str, Any]]
    report: dict[str, Any]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_str(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    return str(x)


def _extract_patch_context(files_payload: list[dict[str, Any]], path: str) -> str:
    # GitHub /pulls/{n}/files includes "patch" for small diffs; for big files it may be absent.
    for f in files_payload:
        if _safe_str(f.get("filename")) == path:
            patch = f.get("patch")
            if isinstance(patch, str) and patch.strip():
                return patch
            return ""
    return ""


def build_learning_corpus(raw_dir: Path, pr_numbers: list[int]) -> LearningCorpus:
    prs: list[dict[str, Any]] = []
    missing: list[int] = []

    for n in pr_numbers:
        pr_dir = raw_dir / f"pr_{n}"
        if not pr_dir.exists():
            missing.append(n)
            continue

        pr = _read_json(pr_dir / "pr.json")
        files = _read_json(pr_dir / "files.json")
        issue_comments = _read_json(pr_dir / "issue_comments.json")
        review_comments = _read_json(pr_dir / "review_comments.json")
        reviews = _read_json(pr_dir / "reviews.json")

        # Build concise file summary
        file_summaries: list[dict[str, Any]] = []
        for f in files:
            file_summaries.append(
                {
                    "path": f.get("filename"),
                    "status": f.get("status"),
                    "additions": f.get("additions"),
                    "deletions": f.get("deletions"),
                    "changes": f.get("changes"),
                }
            )

        # Evidence records: comment + associated patch (best-effort)
        evidence: list[dict[str, Any]] = []
        for c in review_comments:
            body = _safe_str(c.get("body")).strip()
            if not body:
                continue
            path = _safe_str(c.get("path"))
            patch = _extract_patch_context(files, path) if path else ""
            evidence.append(
                {
                    "type": "review_comment",
                    "path": path or None,
                    "body": body,
                    "patch": patch or None,
                }
            )

        for c in issue_comments:
            body = _safe_str(c.get("body")).strip()
            if not body:
                continue
            evidence.append({"type": "issue_comment", "body": body})

        for r in reviews:
            body = _safe_str(r.get("body")).strip()
            state = _safe_str(r.get("state")).strip()
            if not body and not state:
                continue
            evidence.append({"type": "review", "state": state or None, "body": body or None})

        prs.append(
            {
                "number": n,
                "title": pr.get("title"),
                "description": pr.get("body"),
                "base": pr.get("base", {}).get("ref") if isinstance(pr.get("base"), dict) else None,
                "head": pr.get("head", {}).get("ref") if isinstance(pr.get("head"), dict) else None,
                "files": file_summaries,
                "evidence": evidence,
            }
        )

    report = {
        "raw_dir": str(raw_dir),
        "requested_prs": pr_numbers,
        "loaded_prs": [p["number"] for p in prs],
        "missing_prs": missing,
        "counts": {
            "prs": len(prs),
            "evidence_items": sum(len(p["evidence"]) for p in prs),
        },
    }

    return LearningCorpus(prs=prs, report=report)

