from __future__ import annotations

import gzip
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass(frozen=True)
class EpicPromotionWindow:
	start_date: datetime
	end_date: datetime
	discount_percentage: int


@dataclass(frozen=True)
class EpicFreeGameOffer:
	title: str
	offer_id: str
	namespace: str
	description: str
	url: str
	image_url: str
	currency_code: str
	original_price: int
	discount_price: int
	promotion: EpicPromotionWindow
	is_upcoming: bool


class EpicFreeGamesClient:
	"""Epic 免费游戏查询客户端（仅封装接口与解析，不绑定 Qt/业务）。

	接口：
	- https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions

	返回值特点：
	- 顶层可能同时包含 `data` 与 `errors`（部分条目的映射缺失会报 404，但主体数据仍可用）。

	设计目标：
	- 提供稳定的数据结构（`EpicFreeGameOffer`），便于 UI/Service 层使用。
	- 宽容解析：尽量从响应里提取可用字段，不因局部错误中断。
	"""

	_BASE_URL = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions"

	def __init__(
		self,
		*,
		user_agent: str = "SteaMiss/1.0 (+https://example.invalid)",
		timeout_s: float = 10.0,
		max_bytes: int = 4_000_000,
	) -> None:
		self._user_agent = user_agent
		self._timeout_s = timeout_s
		self._max_bytes = max_bytes

	def fetch_promotions_raw(
		self,
		*,
		locale: str = "zh-CN",
		country: str = "CN",
		allow_countries: str = "CN",
	) -> dict[str, Any]:
		"""拉取原始 JSON（上层如需缓存/落库，建议直接存这份）。"""
		url = self._build_url(locale=locale, country=country, allow_countries=allow_countries)
		body = self._http_get(url)
		try:
			return json.loads(body.decode("utf-8"))
		except Exception as e:
			raise ValueError("Invalid JSON from Epic promotions endpoint") from e

	def get_current_free_games(
		self,
		*,
		locale: str = "zh-CN",
		country: str = "CN",
		allow_countries: str = "CN",
		now: Optional[datetime] = None,
	) -> list[EpicFreeGameOffer]:
		"""解析“当前免费”游戏列表。"""
		payload = self.fetch_promotions_raw(locale=locale, country=country, allow_countries=allow_countries)
		return self._extract_free_games(payload, locale=locale, now=now, mode="current")

	def get_upcoming_free_games(
		self,
		*,
		locale: str = "zh-CN",
		country: str = "CN",
		allow_countries: str = "CN",
		now: Optional[datetime] = None,
	) -> list[EpicFreeGameOffer]:
		"""解析“即将免费”游戏列表。"""
		payload = self.fetch_promotions_raw(locale=locale, country=country, allow_countries=allow_countries)
		return self._extract_free_games(payload, locale=locale, now=now, mode="upcoming")

	def _build_url(self, *, locale: str, country: str, allow_countries: str) -> str:
		query = urllib.parse.urlencode(
			{
				"locale": locale,
				"country": country,
				"allowCountries": allow_countries,
			}
		)
		return f"{self._BASE_URL}?{query}"

	def _http_get(self, url: str) -> bytes:
		headers = {
			"User-Agent": self._user_agent,
			"Accept": "application/json,text/plain;q=0.5,*/*;q=0.1",
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

	def _extract_free_games(
		self,
		payload: dict[str, Any],
		*,
		locale: str,
		now: Optional[datetime],
		mode: str,
	) -> list[EpicFreeGameOffer]:
		if mode not in {"current", "upcoming"}:
			raise ValueError("mode must be 'current' or 'upcoming'")

		if now is None:
			now = datetime.now(timezone.utc)
		elif now.tzinfo is None:
			now = now.replace(tzinfo=timezone.utc)

		elements = (
			payload.get("data", {})
			.get("Catalog", {})
			.get("searchStore", {})
			.get("elements", [])
		)

		offers: list[EpicFreeGameOffer] = []
		for el in elements if isinstance(elements, list) else []:
			if not isinstance(el, dict):
				continue

			promo_windows = self._extract_promo_windows(el, mode=mode)
			if not promo_windows:
				continue

			# “免费”判定：优先用促销窗口里的 discountPercentage==0；若缺失则回退到 discountPrice==0。
			total_price = (el.get("price", {}) or {}).get("totalPrice", {}) or {}
			discount_price = int(total_price.get("discountPrice") or 0)

			for window in promo_windows:
				if window.discount_percentage != 0 and discount_price != 0:
					continue

				if mode == "current":
					if not (window.start_date <= now < window.end_date):
						continue
				else:
					if not (now < window.start_date):
						continue

				offer = self._build_offer(el, locale=locale, window=window, is_upcoming=(mode == "upcoming"))
				if offer is not None:
					offers.append(offer)

		# 排序：当前免费按结束时间近→远；即将免费按开始时间近→远
		if mode == "current":
			offers.sort(key=lambda o: o.promotion.end_date)
		else:
			offers.sort(key=lambda o: o.promotion.start_date)
		return offers

	def _extract_promo_windows(self, el: dict[str, Any], *, mode: str) -> list[EpicPromotionWindow]:
		promotions = el.get("promotions")
		if not isinstance(promotions, dict):
			return []

		key = "promotionalOffers" if mode == "current" else "upcomingPromotionalOffers"
		groups = promotions.get(key, [])
		if not isinstance(groups, list):
			return []

		windows: list[EpicPromotionWindow] = []
		for g in groups:
			if not isinstance(g, dict):
				continue
			for p in g.get("promotionalOffers", []) or []:
				if not isinstance(p, dict):
					continue
				start = self._parse_iso_datetime(p.get("startDate"))
				end = self._parse_iso_datetime(p.get("endDate"))
				discount_setting = p.get("discountSetting") or {}
				discount_percentage = int((discount_setting or {}).get("discountPercentage") or 0)

				if start is None or end is None:
					continue
				windows.append(
					EpicPromotionWindow(
						start_date=start,
						end_date=end,
						discount_percentage=discount_percentage,
					)
				)
		return windows

	def _build_offer(
		self,
		el: dict[str, Any],
		*,
		locale: str,
		window: EpicPromotionWindow,
		is_upcoming: bool,
	) -> Optional[EpicFreeGameOffer]:
		title = str(el.get("title") or "").strip()
		offer_id = str(el.get("id") or "").strip()
		namespace = str(el.get("namespace") or "").strip()
		description = str(el.get("description") or "").strip()

		# Epic 年末“神秘游戏”占位标题本地化（接口可能返回英文占位文案）。
		title = title.replace("Mystery Game", "神秘游戏")
		description = description.replace("Mystery Game", "神秘游戏")

		if not title or not offer_id:
			return None

		url = self._build_store_url(el, locale=locale)
		image_url = self._pick_image_url(el)

		total_price = (el.get("price", {}) or {}).get("totalPrice", {}) or {}
		currency_code = str(total_price.get("currencyCode") or "").strip()
		original_price = int(total_price.get("originalPrice") or 0)
		discount_price = int(total_price.get("discountPrice") or 0)

		return EpicFreeGameOffer(
			title=title,
			offer_id=offer_id,
			namespace=namespace,
			description=description,
			url=url,
			image_url=image_url,
			currency_code=currency_code,
			original_price=original_price,
			discount_price=discount_price,
			promotion=window,
			is_upcoming=is_upcoming,
		)

	def _pick_image_url(self, el: dict[str, Any]) -> str:
		imgs = el.get("keyImages")
		if not isinstance(imgs, list):
			return ""

		priority = [
			"DieselStoreFrontWide",
			"OfferImageWide",
			"OfferImageTall",
			"featuredMedia",
			"Thumbnail",
		]
		by_type: dict[str, str] = {}
		for img in imgs:
			if not isinstance(img, dict):
				continue
			t = str(img.get("type") or "")
			u = str(img.get("url") or "")
			if t and u and t not in by_type:
				by_type[t] = u

		for t in priority:
			if t in by_type:
				return by_type[t]
		# 任意兜底
		for img in imgs:
			if isinstance(img, dict) and img.get("url"):
				return str(img.get("url"))
		return ""

	def _build_store_url(self, el: dict[str, Any], *, locale: str) -> str:
		product_slug = str(el.get("productSlug") or "")
		url_slug = str(el.get("urlSlug") or "")

		slug = (product_slug or url_slug).strip()
		if not slug:
			return ""

		# productSlug 可能形如 "thems-fightin-herds/home"，实际页面通常以首段 slug 为准。
		slug = slug.split("/")[0]
		loc = (locale or "en-US").strip()
		return f"https://store.epicgames.com/{loc}/p/{slug}"

	def _parse_iso_datetime(self, value: Any) -> Optional[datetime]:
		if not isinstance(value, str) or not value.strip():
			return None
		s = value.strip()

		# Epic 常用："2026-01-08T16:00:00.000Z"
		try:
			if s.endswith("Z"):
				s = s[:-1] + "+00:00"
			dt = datetime.fromisoformat(s)
			if dt.tzinfo is None:
				dt = dt.replace(tzinfo=timezone.utc)
			return dt.astimezone(timezone.utc)
		except Exception:
			return None


def _demo_print_offers(title: str, offers: list[EpicFreeGameOffer], *, limit: int = 5) -> None:
	def fmt_dt(dt: datetime) -> str:
		# 统一以 UTC 展示，避免本地时区歧义
		return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

	def fmt_price(currency: str, cents: int) -> str:
		# Epic 的 price 字段通常按最小货币单位（如分）返回
		if currency:
			return f"{cents/100:.2f} {currency}"
		return f"{cents/100:.2f}"

	print(f"\n== {title} (top {min(limit, len(offers))}/{len(offers)}) ==")
	for i, o in enumerate(offers[:limit], start=1):
		p = o.promotion
		print(
			"\n".join(
				[
					f"{i}. {o.title}",
					f"   window: {fmt_dt(p.start_date)} -> {fmt_dt(p.end_date)}  (discount={p.discount_percentage}%)",
					f"   price:  {fmt_price(o.currency_code, o.discount_price)}  (orig={fmt_price(o.currency_code, o.original_price)})",
					f"   url:    {o.url}",
					f"   desc:   {o.description}"
				]
			)
		)


if __name__ == "__main__":
	# 小 demo：直接运行本文件即可看到当前/即将免费游戏概览。
	# 运行方式（Windows 示例）：
	#   python src/feature_core/adapters/http/free_game_client.py
	client = EpicFreeGamesClient()
	try:
		current = client.get_current_free_games(locale="zh-CN", country="CN", allow_countries="CN")
		upcoming = client.get_upcoming_free_games(locale="zh-CN", country="CN", allow_countries="CN")

		_demo_print_offers("Current Free Games", current, limit=8)
		_demo_print_offers("Upcoming Free Games", upcoming, limit=8)
	except Exception:
		import logging
		logging.getLogger(__name__).exception("EpicFreeGamesClient demo failed")
