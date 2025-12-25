from __future__ import annotations

import gzip
import re
import urllib.request
import urllib.error
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Iterable, Optional
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class NewsSource:
    """一个新闻源（推荐使用 RSS/Atom 地址，避免 HTML 结构频繁变动）。"""

    name: str
    feed_url: str


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    published_at: Optional[datetime] = None
    summary: str = ""
    source: str = ""


class GameNewsClient:
    """游戏资讯抓取客户端（标准库实现，尽量避免第三方依赖）。

    设计取舍：
    - 优先 RSS/Atom：结构稳定、解析简单、体积小。
    - 如需“抓 HTML 列表页”，建议后续在 UI/业务侧明确目标站点结构再扩展解析规则。

    返回统一的 `NewsItem` 列表，便于 UI 展示。
    """

    def __init__(
        self,
        *,
        user_agent: str = "SteaMiss/1.0 (+https://example.invalid)",
        timeout_s: float = 10.0,
        max_bytes: int = 2_000_000,
    ) -> None:
        self._user_agent = user_agent
        self._timeout_s = timeout_s
        self._max_bytes = max_bytes

    def fetch_feed(self, feed_url: str, *, source: str = "", limit: int = 30) -> list[NewsItem]:
        """抓取并解析 RSS/Atom。"""
        xml_bytes = self._http_get(feed_url)
        items = self._parse_rss_or_atom(xml_bytes, source=source)

        # 按发布时间降序（无时间的放后面），再截断
        items.sort(key=lambda it: (it.published_at is not None, it.published_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        return items[: max(0, int(limit))]

    def fetch_sources(self, sources: Iterable[NewsSource], *, per_source_limit: int = 30, total_limit: int = 60) -> list[NewsItem]:
        """抓取多个源并去重聚合。"""
        merged: list[NewsItem] = []
        seen_urls: set[str] = set()

        for src in sources:
            try:
                items = self.fetch_feed(src.feed_url, source=src.name, limit=per_source_limit)
            except Exception:
                # 源失败直接跳过：上层若需要提示/埋点可在 service 层处理
                continue

            for item in items:
                if not item.url or item.url in seen_urls:
                    continue
                seen_urls.add(item.url)
                merged.append(item)

        merged.sort(key=lambda it: (it.published_at is not None, it.published_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        return merged[: max(0, int(total_limit))]

    def _http_get(self, url: str) -> bytes:
        headers = {
            "User-Agent": self._user_agent,
            "Accept": "application/xml,text/xml,application/atom+xml,application/rss+xml,text/html;q=0.5,*/*;q=0.1",
            "Accept-Encoding": "gzip",
        }

        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                raw = resp.read(self._max_bytes + 1)
                if len(raw) > self._max_bytes:
                    raise ValueError(f"Response too large (>{self._max_bytes} bytes)")

                encoding = (resp.headers.get("Content-Encoding") or "").lower()
                if "gzip" in encoding:
                    return gzip.decompress(raw)
                return raw
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP error {e.code} for {url}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error for {url}: {e.reason}") from e

    def _parse_rss_or_atom(self, xml_bytes: bytes, *, source: str = "") -> list[NewsItem]:
        # 有些站点会返回带 BOM 的 XML
        text = xml_bytes.decode("utf-8", errors="replace")
        text = text.lstrip("\ufeff")

        try:
            root = ET.fromstring(text)
        except ET.ParseError as e:
            raise ValueError("Invalid XML (not RSS/Atom)") from e

        tag = self._strip_ns(root.tag).lower()

        if tag == "rss":
            return self._parse_rss(root, source=source)
        if tag == "feed":
            return self._parse_atom(root, source=source)

        # 有的 RSS 根节点不是 rss 而是 rdf/RDF
        if tag in {"rdf", "rdf:rdf"}:
            return self._parse_rdf_rss(root, source=source)

        raise ValueError(f"Unsupported feed root: {root.tag}")

    def _parse_rss(self, root: ET.Element, *, source: str) -> list[NewsItem]:
        channel = root.find("channel")
        if channel is None:
            return []

        items: list[NewsItem] = []
        for item in channel.findall("item"):
            title = self._text(item.find("title"))
            link = self._text(item.find("link"))
            pub_date = self._text(item.find("pubDate"))
            description = self._text(item.find("description"))

            items.append(
                NewsItem(
                    title=title,
                    url=link,
                    published_at=self._parse_date(pub_date),
                    summary=self._strip_html(description),
                    source=source,
                )
            )
        return [it for it in items if it.url]

    def _parse_atom(self, root: ET.Element, *, source: str) -> list[NewsItem]:
        ns = self._nsmap(root)
        items: list[NewsItem] = []

        for entry in root.findall(self._q("entry", ns)):
            title = self._text(entry.find(self._q("title", ns)))

            link = ""
            for link_el in entry.findall(self._q("link", ns)):
                rel = (link_el.attrib.get("rel") or "").lower()
                href = link_el.attrib.get("href") or ""
                if not href:
                    continue
                if rel in {"", "alternate"}:
                    link = href
                    break
            if not link:
                link = self._text(entry.find(self._q("link", ns)))

            published = self._text(entry.find(self._q("published", ns)))
            updated = self._text(entry.find(self._q("updated", ns)))

            summary = self._text(entry.find(self._q("summary", ns)))
            if not summary:
                summary = self._text(entry.find(self._q("content", ns)))

            items.append(
                NewsItem(
                    title=title,
                    url=link,
                    published_at=self._parse_date(published or updated),
                    summary=self._strip_html(summary),
                    source=source,
                )
            )

        return [it for it in items if it.url]

    def _parse_rdf_rss(self, root: ET.Element, *, source: str) -> list[NewsItem]:
        # 非主流 RSS 变体：尽量做兼容解析
        items: list[NewsItem] = []
        for item in root.findall(".//{*}item"):
            title = self._text(item.find("{*}title"))
            link = self._text(item.find("{*}link"))
            date = self._text(item.find("{*}date"))
            desc = self._text(item.find("{*}description"))
            items.append(
                NewsItem(
                    title=title,
                    url=link,
                    published_at=self._parse_date(date),
                    summary=self._strip_html(desc),
                    source=source,
                )
            )
        return [it for it in items if it.url]

    def _parse_date(self, value: str) -> Optional[datetime]:
        value = (value or "").strip()
        if not value:
            return None

        # RFC 2822/822
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass

        # ISO 8601
        v = value.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(v)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    def _strip_html(self, s: str) -> str:
        if not s:
            return ""
        # 极简去标签，避免引入 html2text/bs4
        s = re.sub(r"<[^>]+>", " ", s)
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    def _text(self, el: Optional[ET.Element]) -> str:
        if el is None:
            return ""
        return (el.text or "").strip()

    def _strip_ns(self, tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag

    def _nsmap(self, root: ET.Element) -> dict[str, str]:
        # ElementTree 不直接暴露 nsmap，这里用 root.tag 推断默认命名空间
        m = re.match(r"^\{([^}]+)\}", root.tag)
        if not m:
            return {}
        return {"": m.group(1)}

    def _q(self, local: str, ns: dict[str, str]) -> str:
        # 构造带默认命名空间的 tag
        default = ns.get("")
        if default:
            return f"{{{default}}}{local}"
        return local
