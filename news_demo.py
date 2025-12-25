from __future__ import annotations

import argparse
import gzip
import re
import sys
from pathlib import Path
import urllib.error
import urllib.request


def _setup_import_path() -> None:
    """确保从项目根目录运行时能 import 到 src.*"""
    root = Path(__file__).resolve().parent
    # 允许：from src.... import ...
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and print game news from RSS/Atom.")
    parser.add_argument("--index", type=int, default=1, help="Which item to show in detail (1-based).")
    args = parser.parse_args()

    _setup_import_path()

    from src.feature_core.adapters.http.game_news_client import GameNewsClient, NewsSource

    client = GameNewsClient(timeout_s=10.0)
    sources = [
        NewsSource(name="Gcores", feed_url="https://www.gcores.com/rss"),
        NewsSource(name="GameSpot", feed_url="https://www.gamespot.com/feeds/news/"),
    ]

    items = client.fetch_sources(sources, per_source_limit=20, total_limit=20)

    print(f"Fetched {len(items)} items.\n")
    for i, it in enumerate(items, 1):
        ts = it.published_at.isoformat() if it.published_at else "unknown"
        print(f"{i:02d}. [{it.source}] {ts}")
        print(f"    {it.title}")
        print(f"    {it.url}\n")

    if not items:
        return 0

    index = max(1, int(args.index))
    if index > len(items):
        index = 1

    item = items[index - 1]
    print("=" * 80)
    print(f"Detail for item #{index}: {item.title}")
    print(f"URL: {item.url}")
    print(f"Published: {item.published_at.isoformat() if item.published_at else 'unknown'}")
    print("-" * 80)

    detail = (item.summary or "").strip()
    if not detail:
        detail = _fetch_article_snippet(item.url)

    print(detail or "(No summary in feed; failed to fetch article snippet.)")

    return 0


def _fetch_article_snippet(url: str, *, timeout_s: float = 10.0, max_bytes: int = 2_000_000, max_chars: int = 1200) -> str:
    """非常轻量的兜底：抓文章 HTML 并抽取一段纯文本。

    注意：这不是“真正的正文抽取器”，只用于 demo 展示。
    """
    if not url:
        return ""

    headers = {
        "User-Agent": "SteaMiss/1.0 (+https://example.invalid)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.1",
        "Accept-Encoding": "gzip",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read(max_bytes + 1)
            if len(raw) > max_bytes:
                return ""

            encoding = (resp.headers.get("Content-Encoding") or "").lower()
            if "gzip" in encoding:
                raw = gzip.decompress(raw)
    except (urllib.error.HTTPError, urllib.error.URLError):
        return ""

    html = raw.decode("utf-8", errors="replace")
    html = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<style\b[^>]*>.*?</style>", " ", html, flags=re.IGNORECASE | re.DOTALL)

    # 优先 meta description
    m = re.search(r"<meta\s+name=['\"]description['\"]\s+content=['\"]([^'\"]+)['\"]", html, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()[:max_chars]

    # 再做一次极简去标签
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


if __name__ == "__main__":
    raise SystemExit(main())
