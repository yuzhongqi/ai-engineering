from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import requests

from store.cache import CacheEntry, load_cache, save_cache


GITHUB_API = "https://api.github.com"


@dataclass(frozen=True)
class GitHubClient:
    token: str
    cache_dir: Path
    user_agent: str = "ai-pr-learning/1.0"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": self.user_agent,
        }

    def get_json(self, url: str, params: dict[str, Any] | None = None, cache_key: str | None = None) -> Any:
        key = cache_key or f"GET {url} {params or {}}"
        cached = load_cache(self.cache_dir, key)
        headers = self._headers()
        if cached is not None and cached.etag:
            headers["If-None-Match"] = cached.etag
        if cached is not None and cached.last_modified:
            headers["If-Modified-Since"] = cached.last_modified

        resp = requests.get(url, headers=headers, params=params, timeout=30)

        if resp.status_code == 304 and cached is not None:
            return cached.body

        if resp.status_code in (403, 429):
            # naive backoff for rate limits
            time.sleep(2)

        resp.raise_for_status()
        body = resp.json()

        save_cache(
            self.cache_dir,
            key,
            CacheEntry(
                etag=resp.headers.get("ETag"),
                last_modified=resp.headers.get("Last-Modified"),
                status_code=resp.status_code,
                headers={k: v for k, v in resp.headers.items()},
                body=body,
            ),
        )
        return body

    def get_text(self, url: str, accept: str, params: dict[str, Any] | None = None, cache_key: str | None = None) -> str:
        key = cache_key or f"GET {url} {params or {}} accept={accept}"
        cached = load_cache(self.cache_dir, key)
        headers = self._headers()
        headers["Accept"] = accept
        if cached is not None and cached.etag:
            headers["If-None-Match"] = cached.etag
        if cached is not None and cached.last_modified:
            headers["If-Modified-Since"] = cached.last_modified

        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 304 and cached is not None:
            return str(cached.body or "")

        resp.raise_for_status()
        text = resp.text
        save_cache(
            self.cache_dir,
            key,
            CacheEntry(
                etag=resp.headers.get("ETag"),
                last_modified=resp.headers.get("Last-Modified"),
                status_code=resp.status_code,
                headers={k: v for k, v in resp.headers.items()},
                body=text,
            ),
        )
        return text

    def paginate(self, url: str, params: dict[str, Any] | None = None) -> Iterable[Any]:
        base = dict(params or {})
        per_page = int(base.get("per_page", 100))
        base["per_page"] = min(max(per_page, 1), 100)
        page = 1
        while True:
            p = dict(base)
            p["page"] = page
            items = self.get_json(url, params=p, cache_key=f"{url} page={page} params={base}")
            if not items:
                return
            if isinstance(items, dict) and "items" in items:
                items = items["items"]
            if not isinstance(items, list):
                yield items
                return
            for it in items:
                yield it
            if len(items) < base["per_page"]:
                return
            page += 1

