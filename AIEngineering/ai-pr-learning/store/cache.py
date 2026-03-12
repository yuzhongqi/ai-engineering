from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CacheEntry:
    etag: str | None
    last_modified: str | None
    status_code: int
    headers: dict[str, str]
    body: Any


def _key_to_path(cache_dir: Path, key: str) -> Path:
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()  # noqa: S324
    return cache_dir / f"{h}.json"


def load_cache(cache_dir: Path, key: str) -> CacheEntry | None:
    p = _key_to_path(cache_dir, key)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return CacheEntry(
        etag=data.get("etag"),
        last_modified=data.get("last_modified"),
        status_code=int(data.get("status_code", 0)),
        headers=dict(data.get("headers", {})),
        body=data.get("body"),
    )


def save_cache(cache_dir: Path, key: str, entry: CacheEntry) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    p = _key_to_path(cache_dir, key)
    p.write_text(
        json.dumps(
            {
                "etag": entry.etag,
                "last_modified": entry.last_modified,
                "status_code": entry.status_code,
                "headers": entry.headers,
                "body": entry.body,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

