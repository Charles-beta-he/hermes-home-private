#!/usr/bin/env python3
"""Fetch a bounded Odaily crypto/Web3 digest for the daily briefing.

No external dependencies.  The script emits deterministic JSON so the cron LLM can
summarize and merge it into the AIHOT/GitHub/Product Hunt daily report without
scraping the Odaily homepage each run.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://web-api.odaily.news"
REFERER = "https://www.odaily.news/zh-CN"
USER_AGENT = "HermesDailyReport/1.0 (+https://www.odaily.news/zh-CN)"

SHANGHAI = timezone(timedelta(hours=8))

CORE_SYMBOLS = ["btcusdt", "ethusdt", "solusdt", "bnbusdt"]
IMPORTANT_KEYWORDS = [
    "BTC",
    "ETH",
    "SOL",
    "BNB",
    "USDT",
    "USDC",
    "稳定币",
    "比特币",
    "以太坊",
    "ETF",
    "SEC",
    "CFTC",
    "监管",
    "法案",
    "税收",
    "交易所",
    "币安",
    "OKX",
    "Coinbase",
    "清算",
    "巨鲸",
    "空单",
    "多单",
    "漏洞",
    "黑客",
    "攻击",
    "ZEC",
    "RWA",
    "代币化",
    "预测市场",
    "Polymarket",
    "Strategy",
    "BitMine",
    "HYPE",
    "链上",
    "香港",
    "美国",
    "美联储",
]
ARTICLE_INCLUDE_KEYWORDS = IMPORTANT_KEYWORDS + [
    "Perp",
    "DEX",
    "DAT",
    "财库",
    "熊市",
    "牛市",
    "解锁",
    "安全",
]
LOW_VALUE_KEYWORDS = ["广告", "报名", "早餐", "Community Breakfast", "狂欢", "战队争霸赛"]
NON_CRYPTO_KEYWORDS = [
    "HBM",
    "半导体",
    "机器人",
    "谐波",
    "A股",
    "港股",
    "美股",
    "CPI",
    "宏观",
    "电动汽车",
]
CRYPTO_REQUIRED_KEYWORDS = [k for k in IMPORTANT_KEYWORDS if k not in {"美国", "香港", "美联储"}]


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def contains_any(text: str, keywords: list[str]) -> bool:
    hay = text.lower()
    return any(k.lower() in hay for k in keywords)


def fetch_json(path: str, params: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
    query = ""
    if params:
        query = "?" + urlencode(params, doseq=True)
    url = BASE + path + query
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": REFERER,
            "x-locale": "zh-CN",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        body = resp.read(1_500_000).decode("utf-8", "replace")
        data = json.loads(body)
        data["_fetch"] = {
            "url": url,
            "status": getattr(resp, "status", None),
            "content_type": resp.headers.get("content-type", ""),
        }
        return data


def item_url(entity_type: int | str | None, entity_id: int | str | None) -> str:
    if entity_type == 4 or str(entity_type) == "4":
        return f"https://www.odaily.news/zh-CN/newsflash/{entity_id}"
    return f"https://www.odaily.news/zh-CN/post/{entity_id}"


def normalize_tags(tags: Any) -> list[str]:
    if not isinstance(tags, list):
        return []
    out: list[str] = []
    for tag in tags:
        if isinstance(tag, dict) and tag.get("name"):
            out.append(clean_text(tag["name"]))
    return out


def normalize_article(item: dict[str, Any]) -> dict[str, Any]:
    entity_id = item.get("entityId") or item.get("id")
    entity_type = item.get("entityType") or 3
    tags = normalize_tags(item.get("tags"))
    title = clean_text(item.get("title"))
    summary = clean_text(item.get("summary"))
    return {
        "id": entity_id,
        "entity_type": entity_type,
        "title": title,
        "summary": summary,
        "tags": tags,
        "published": item.get("publishedTime") or item.get("publishTimestamp"),
        "url": item_url(entity_type, entity_id),
    }


def normalize_newsflash(item: dict[str, Any]) -> dict[str, Any]:
    title = clean_text(item.get("title"))
    summary = clean_text(item.get("summary"))
    news_id = item.get("entityId") or item.get("id")
    return {
        "id": news_id,
        "title": title,
        "summary": summary,
        "important": bool(item.get("isImportant")),
        "published": item.get("publishedTime") or item.get("publishTimestamp"),
        "url": f"https://www.odaily.news/zh-CN/newsflash/{news_id}",
    }


def select_articles(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[Any] = set()
    for raw in items:
        item = normalize_article(raw)
        key = item["id"]
        if key in seen:
            continue
        seen.add(key)
        hay = " ".join([item["title"], item["summary"], " ".join(item["tags"])])
        if contains_any(hay, LOW_VALUE_KEYWORDS):
            continue
        if not contains_any(hay, CRYPTO_REQUIRED_KEYWORDS):
            continue
        selected.append(item)
        if len(selected) >= limit:
            break
    return selected


def select_newsflash(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for raw in items:
        item = normalize_newsflash(raw)
        hay = " ".join([item["title"], item["summary"]])
        if contains_any(hay, LOW_VALUE_KEYWORDS):
            continue
        # Odaily 的 important 快讯会混入股票/科技/泛宏观；日报只保留 crypto/Web3 明确相关项。
        if not contains_any(hay, CRYPTO_REQUIRED_KEYWORDS):
            continue
        selected.append(item)
        if len(selected) >= limit:
            break
    return selected


def normalize_market(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    order = {s: i for i, s in enumerate(CORE_SYMBOLS)}
    for item in sorted(items, key=lambda x: order.get(str(x.get("symbol", "")).lower(), 99)):
        symbol = str(item.get("symbol", "")).upper().replace("USDT", "/USDT")
        try:
            rate = float(item.get("rate24H", 0)) * 100
            rate_text = f"{rate:+.2f}%"
        except Exception:
            rate_text = str(item.get("rate24H", ""))
        out.append({
            "symbol": symbol,
            "price": str(item.get("price", "")),
            "rate24h": rate_text,
            "is_up": bool(item.get("isUp")),
        })
    return out


def normalize_hotspots(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in items[:limit]:
        nested = raw.get("list") or []
        out.append({
            "id": raw.get("id"),
            "name": clean_text(raw.get("name")),
            "summary": clean_text(raw.get("summary")),
            "url": f"https://www.odaily.news/zh-CN/hotspot/{raw.get('id')}",
            "related_items": [clean_text(x.get("title")) for x in nested[:3] if isinstance(x, dict)],
        })
    return out


def normalize_hotrank(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, raw in enumerate(items[:limit], 1):
        entity_id = raw.get("entityId") or raw.get("id")
        out.append({
            "rank": i,
            "id": entity_id,
            "title": clean_text(raw.get("title")),
            "url": f"https://www.odaily.news/zh-CN/post/{entity_id}",
            "note": "站内热度/观点参考，不等同事实重要性",
        })
    return out


def build_digest(args: argparse.Namespace) -> dict[str, Any]:
    endpoints: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    def call(path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            data = fetch_json(path, params)
            endpoints.append(data.get("_fetch", {"url": BASE + path}))
            if data.get("code") != 200:
                errors.append({"path": path, "error": f"code={data.get('code')} msg={data.get('msg')}"})
            return data.get("data")
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            errors.append({"path": path, "error": f"{type(exc).__name__}: {exc}"})
            return None

    market = call("/market/listBySymbols", {"symbols[]": CORE_SYMBOLS, "exchange": 1}) or []
    hotwords = call("/hotWord/list", {"limit": args.hotwords}) or []
    hotrank = call("/hotRank/list", {"hotRankType": "WEEKLY", "entityType": "POST"}) or []
    posts_page = call("/post/page", {"page": 1, "size": args.posts * 3}) or {}
    news_page = call("/newsflash/page", {"page": 1, "size": args.newsflash * 3}) or {}
    hotspot_page = call("/hotspot/page", {"page": 1, "size": args.hotspots}) or {}

    posts = posts_page.get("list", []) if isinstance(posts_page, dict) else []
    news = news_page.get("list", []) if isinstance(news_page, dict) else []
    hotspots = hotspot_page.get("list", []) if isinstance(hotspot_page, dict) else []

    digest = {
        "schema_version": "odaily_crypto_digest_v1",
        "source": {
            "name": "Odaily星球日报",
            "homepage": REFERER,
            "api_base": BASE,
            "status": "ok" if not errors else "degraded",
            "errors": errors,
            "endpoints": endpoints,
        },
        "generated_at": datetime.now(SHANGHAI).isoformat(timespec="seconds"),
        "selection_policy": {
            "use_in_daily_report": "作为加密/Web3市场信号源，不做整站新闻流全量转载",
            "must_include": ["24H热门币种/要闻", "isImportant=true或命中关键词的快讯", "热点专题", "BTC/ETH/SOL/BNB行情", "监管/安全/交易所/稳定币/巨鲸/清算/漏洞"],
            "filter_out": ["广告软文", "普通活动", "重复快讯", "无crypto影响的泛宏观", "无证据预测文"],
        },
        "market": normalize_market(market if isinstance(market, list) else []),
        "hotwords": [clean_text(x.get("name")) for x in hotwords if isinstance(x, dict) and x.get("name")],
        "hotspots": normalize_hotspots(hotspots if isinstance(hotspots, list) else [], args.hotspots),
        "important_newsflash": select_newsflash(news if isinstance(news, list) else [], args.newsflash),
        "selected_articles": select_articles(posts if isinstance(posts, list) else [], args.posts),
        "hotrank": normalize_hotrank(hotrank if isinstance(hotrank, list) else [], args.hotrank),
        "daily_report_guidance": {
            "section_title": "加密/Web3 市场",
            "max_items": "市场概览1行 + 今日主线1-3条 + 重要快讯3-6条 + 热词3-7个 + 值得读1-2篇",
            "candidate_task_rule": "只有出现对 Hermes/local-brain/taskpool/browser automation 直接可迁移且证据充分的机会时才写 sidecar candidate；普通币圈新闻不要入池。",
        },
    }
    return digest


def markdown_summary(digest: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("## 加密/Web3 市场（Odaily星球日报）")
    status = digest["source"]["status"]
    lines.append(f"- 来源状态：{status}；主页：{digest['source']['homepage']}")
    if digest.get("market"):
        market = "；".join(f"{x['symbol']} {x['price']} ({x['rate24h']})" for x in digest["market"])
        lines.append(f"- 市场概览：{market}")
    if digest.get("hotspots"):
        lines.append("- 今日主线：" + "；".join(x["name"] for x in digest["hotspots"][:3]))
    if digest.get("important_newsflash"):
        lines.append("- 重要快讯：")
        for x in digest["important_newsflash"][:5]:
            lines.append(f"  - {x['title']} — {x['url']}")
    if digest.get("hotwords"):
        lines.append("- 热词：" + "、".join(digest["hotwords"][:8]))
    if digest.get("selected_articles"):
        lines.append("- 值得读：")
        for x in digest["selected_articles"][:3]:
            tags = f" [{'/'.join(x['tags'][:4])}]" if x.get("tags") else ""
            lines.append(f"  - {x['title']}{tags} — {x['url']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Odaily crypto/Web3 digest for Hermes daily report")
    parser.add_argument("--posts", type=int, default=8)
    parser.add_argument("--newsflash", type=int, default=8)
    parser.add_argument("--hotspots", type=int, default=5)
    parser.add_argument("--hotrank", type=int, default=8)
    parser.add_argument("--hotwords", type=int, default=20)
    parser.add_argument("--markdown", action="store_true", help="Print a compact markdown section instead of JSON")
    args = parser.parse_args()

    digest = build_digest(args)
    if args.markdown:
        print(markdown_summary(digest))
    else:
        print(json.dumps(digest, ensure_ascii=False, indent=2))
    return 0 if digest["source"]["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
