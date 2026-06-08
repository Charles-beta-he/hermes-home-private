#!/usr/bin/env python3
"""Product Hunt daily digest with open-source evidence enrichment.

Outputs deterministic JSON by default, or Markdown with --markdown.
Uses the official Product Hunt GraphQL API when a local token is configured;
falls back to Product Hunt Atom feed with reduced fields.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PH_GRAPHQL = "https://api.producthunt.com/v2/api/graphql"
PH_FEED = "https://www.producthunt.com/feed"
UA = "HermesProductHuntDailyDigest/1.0 (+local daily report)"
MAX_BODY = 3_000_000

INTEREST_KEYWORDS = [
    "ai", "agent", "automation", "developer", "github", "open source", "opensource",
    "api", "cli", "devtool", "database", "data", "security", "privacy", "productivity",
    "workflow", "browser", "infra", "infrastructure", "llm", "code", "coding",
]

LOW_SIGNAL_KEYWORDS = ["wallpaper", "meme", "dating", "game", "coupon", "casino"]


@dataclass
class RepoMeta:
    repo: str
    url: str
    stars: int | None = None
    forks: int | None = None
    open_issues: int | None = None
    license: str | None = None
    description: str | None = None
    archived: bool | None = None
    pushed_at: str | None = None
    error: str | None = None


@dataclass
class ProductItem:
    name: str
    tagline: str = ""
    url: str = ""
    website: str = ""
    votes: int | None = None
    created_at: str = ""
    links: list[dict[str, str]] = field(default_factory=list)
    github_links: list[str] = field(default_factory=list)
    repos: list[RepoMeta] = field(default_factory=list)
    open_source_status: str = "unknown"
    interest_score: int = 0
    reasons: list[str] = field(default_factory=list)


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def http_json(url: str, *, headers: dict[str, str] | None = None, data: bytes | None = None, timeout: int = 25) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})}, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read(MAX_BODY)
    return json.loads(body.decode("utf-8"))


def fetch_producthunt_api(limit: int) -> tuple[list[ProductItem], dict[str, Any]]:
    token = os.environ.get("PRODUCTHUNT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("missing local Product Hunt token")
    query = """
    query DailyPosts($first: Int!) {
      posts(first: $first) {
        edges {
          node {
            id
            name
            tagline
            url
            website
            votesCount
            createdAt
            productLinks { type url }
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"first": limit}}).encode("utf-8")
    data = http_json(
        PH_GRAPHQL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=payload,
    )
    if data.get("errors"):
        raise RuntimeError("GraphQL errors: " + json.dumps(data["errors"], ensure_ascii=False)[:1000])
    edges = (((data.get("data") or {}).get("posts") or {}).get("edges") or [])
    items: list[ProductItem] = []
    for edge in edges:
        node = (edge or {}).get("node") or {}
        links = []
        for link in node.get("productLinks") or []:
            if isinstance(link, dict) and link.get("url"):
                links.append({"type": str(link.get("type") or ""), "url": str(link.get("url") or "")})
        items.append(ProductItem(
            name=str(node.get("name") or "").strip(),
            tagline=str(node.get("tagline") or "").strip(),
            url=str(node.get("url") or "").strip(),
            website=str(node.get("website") or "").strip(),
            votes=node.get("votesCount"),
            created_at=str(node.get("createdAt") or ""),
            links=links,
        ))
    meta = {"mode": "official_api", "endpoint": PH_GRAPHQL, "items_seen": len(items)}
    return items, meta


def fetch_producthunt_feed(limit: int) -> tuple[list[ProductItem], dict[str, Any]]:
    req = urllib.request.Request(PH_FEED, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        body = resp.read(MAX_BODY)
    root = ET.fromstring(body)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items: list[ProductItem] = []
    for entry in root.findall("atom:entry", ns)[:limit]:
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
        updated = (entry.findtext("atom:updated", default="", namespaces=ns) or "").strip()
        link = ""
        for link_el in entry.findall("atom:link", ns):
            href = link_el.attrib.get("href", "")
            if href:
                link = href
                break
        items.append(ProductItem(name=title, tagline=strip_html(summary), url=link, created_at=updated))
    meta = {"mode": "atom_fallback", "endpoint": PH_FEED, "items_seen": len(items)}
    return items, meta


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def resolve_url(url: str, timeout: int = 15) -> str:
    if not url:
        return ""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read(0)
            return resp.geturl()
    except Exception:
        return url


def normalize_github_repo_url(url: str) -> tuple[str, str] | None:
    if not url:
        return None
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host != "github.com":
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        return None
    owner = parts[0]
    repo = parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    if owner in {"features", "topics", "marketplace", "pricing", "login", "sponsors"}:
        return None
    if not re.match(r"^[A-Za-z0-9_.-]+$", owner) or not re.match(r"^[A-Za-z0-9_.-]+$", repo):
        return None
    full = f"{owner}/{repo}"
    return full, f"https://github.com/{full}"


def enrich_repo(repo_full: str, repo_url: str) -> RepoMeta:
    api_url = f"https://api.github.com/repos/{repo_full}"
    try:
        data = http_json(api_url, headers={"Accept": "application/vnd.github+json"}, timeout=20)
        lic = data.get("license")
        license_name = None
        if isinstance(lic, dict):
            license_name = lic.get("spdx_id") or lic.get("name") or lic.get("key")
        return RepoMeta(
            repo=repo_full,
            url=data.get("html_url") or repo_url,
            stars=data.get("stargazers_count"),
            forks=data.get("forks_count"),
            open_issues=data.get("open_issues_count"),
            license=license_name,
            description=data.get("description"),
            archived=data.get("archived"),
            pushed_at=data.get("pushed_at"),
        )
    except urllib.error.HTTPError as exc:
        return RepoMeta(repo=repo_full, url=repo_url, error=f"github_api_http_{exc.code}")
    except Exception as exc:
        return RepoMeta(repo=repo_full, url=repo_url, error=f"github_api_error:{type(exc).__name__}")


def detect_and_enrich(items: list[ProductItem], resolve_redirects: bool) -> None:
    for item in items:
        candidate_urls: list[str] = []
        for link in item.links:
            link_type = (link.get("type") or "").lower()
            url = link.get("url") or ""
            if "github" in link_type or "gitlab" in link_type or "source" in link_type or "github.com" in url:
                candidate_urls.append(url)
        # Product Hunt sometimes stores outbound redirect URLs; resolve only likely code links.
        github_urls: list[str] = []
        for url in candidate_urls:
            final_url = resolve_url(url) if resolve_redirects else url
            if "github.com" in final_url:
                github_urls.append(final_url)
        seen_repos = set()
        for gh_url in github_urls:
            normalized = normalize_github_repo_url(gh_url)
            if not normalized:
                continue
            repo_full, repo_url = normalized
            if repo_full in seen_repos:
                continue
            seen_repos.add(repo_full)
            item.repos.append(enrich_repo(repo_full, repo_url))
        # Keep unresolved Product Hunt redirect URLs as evidence too. Product Hunt often
        # returns /r/... tracking redirects for productLinks, and terminal fetches may be
        # blocked by Cloudflare. The link type itself is still official API evidence.
        item.github_links = github_urls or candidate_urls
        if item.repos:
            item.open_source_status = "github_repo_verified"
            item.reasons.append("Product Hunt productLinks contains GitHub/source-code evidence and GitHub repo metadata was verified")
        elif candidate_urls:
            item.open_source_status = "github_link_detected_unresolved"
            item.reasons.append("Product Hunt productLinks contains GitHub/source-code evidence; repo URL could not be resolved in terminal")
        else:
            text = f"{item.name} {item.tagline} {item.website} " + " ".join(l.get("url", "") for l in item.links)
            lower = text.lower()
            if any(k in lower for k in ["open source", "opensource", "github.com", "github"]):
                item.open_source_status = "possible_open_source_unverified"
                item.reasons.append("Text mentions open-source/GitHub but no repository metadata was verified")
            else:
                item.open_source_status = "unknown"


def score_items(items: list[ProductItem]) -> None:
    for item in items:
        text = f"{item.name} {item.tagline} {item.website} " + " ".join(l.get("type", "") + " " + l.get("url", "") for l in item.links)
        lower = text.lower()
        score = 0
        for kw in INTEREST_KEYWORDS:
            if kw in lower:
                score += 2 if kw in {"ai", "agent", "developer", "github", "open source", "api", "cli", "llm", "code"} else 1
        if item.open_source_status in {"github_repo_verified", "github_link_detected_unresolved"}:
            score += 5
        if item.votes:
            score += min(int(item.votes) // 50, 4)
        for kw in LOW_SIGNAL_KEYWORDS:
            if kw in lower:
                score -= 3
        item.interest_score = score
        if score >= 7:
            item.reasons.append("high relevance for AI/dev/productivity/open-source daily digest")
        elif score >= 3:
            item.reasons.append("medium relevance for product discovery")


def item_to_dict(item: ProductItem) -> dict[str, Any]:
    return {
        "name": item.name,
        "tagline": item.tagline,
        "url": item.url,
        "website": item.website,
        "votes": item.votes,
        "created_at": item.created_at,
        "interest_score": item.interest_score,
        "open_source_status": item.open_source_status,
        "github_links": item.github_links,
        "repos": [repo.__dict__ for repo in item.repos],
        "links": item.links,
        "reasons": item.reasons,
    }


def render_markdown(result: dict[str, Any], top: int) -> str:
    lines = []
    lines.append("## Product Hunt 产品发现")
    lines.append("")
    lines.append(f"- 状态：{result['status']}；来源：{result['source_mode']}；采样：{result['items_seen']}；GitHub/source 外链命中：{result.get('github_source_link_count', 0)}；repo 元数据命中：{result['github_repo_count']}")
    if result.get("error"):
        lines.append(f"- 降级/错误：{result['error']}")
    lines.append("")
    lines.append("### 值得关注")
    for idx, item in enumerate(result["top_items"][:top], 1):
        votes = "" if item.get("votes") is None else f"，{item['votes']} votes"
        lines.append(f"{idx}. {item['name']}（score {item['interest_score']}{votes}）")
        if item.get("tagline"):
            lines.append(f"   - {item['tagline']}")
        if item.get("url"):
            lines.append(f"   - Product Hunt: {item['url']}")
        if item.get("website"):
            lines.append(f"   - Website: {item['website']}")
        if item.get("repos"):
            for repo in item["repos"]:
                repo_bits = []
                if repo.get("stars") is not None:
                    repo_bits.append(f"{repo['stars']} stars")
                if repo.get("license"):
                    repo_bits.append(f"license {repo['license']}")
                if repo.get("archived") is not None:
                    repo_bits.append("archived" if repo.get("archived") else "active")
                suffix = "；" + "，".join(repo_bits) if repo_bits else ""
                lines.append(f"   - 开源证据：GitHub {repo['repo']} {repo['url']}{suffix}")
        elif item.get("open_source_status") == "github_link_detected_unresolved":
            lines.append("   - 开源证据：Product Hunt 官方 API 标记了 GitHub/source-code 外链；终端环境被跳转/Cloudflare 阻断，未解析到 repo 元数据")
        else:
            status = item.get("open_source_status") or "unknown"
            label = "未发现开源证据" if status == "unknown" else "疑似开源但未验证"
            lines.append(f"   - 开源证据：{label}")
        if item.get("reasons"):
            lines.append(f"   - 入选理由：{'；'.join(item['reasons'][:2])}")
    if not result["top_items"]:
        lines.append("- 今日未筛出高相关产品。")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--no-resolve", action="store_true", help="skip outbound redirect resolution")
    args = parser.parse_args()

    load_dotenv(Path.home() / ".hermes" / ".env")
    started = time.time()
    error = None
    try:
        items, meta = fetch_producthunt_api(args.limit)
        status = "ok"
    except Exception as exc:
        error = f"official_api_failed:{type(exc).__name__}:{exc}"
        try:
            items, meta = fetch_producthunt_feed(args.limit)
            status = "degraded"
        except Exception as feed_exc:
            result = {
                "status": "failed",
                "source": "producthunt",
                "source_mode": "none",
                "items_seen": 0,
                "github_repo_count": 0,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "duration_sec": round(time.time() - started, 2),
                "error": error + f"; atom_fallback_failed:{type(feed_exc).__name__}:{feed_exc}",
                "top_items": [],
                "items": [],
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 2

    detect_and_enrich(items, resolve_redirects=not args.no_resolve)
    score_items(items)
    ranked = sorted(items, key=lambda it: (it.interest_score, it.votes or 0, it.created_at), reverse=True)
    top_items = [it for it in ranked if it.interest_score >= 2 or it.open_source_status != "unknown"][: args.top]
    repo_count = sum(len(it.repos) for it in items)
    source_link_count = sum(1 for it in items if it.open_source_status in {"github_repo_verified", "github_link_detected_unresolved"})
    result = {
        "status": status,
        "source": "producthunt",
        "source_mode": meta.get("mode"),
        "endpoint": meta.get("endpoint"),
        "items_seen": len(items),
        "github_source_link_count": source_link_count,
        "github_repo_count": repo_count,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "duration_sec": round(time.time() - started, 2),
        "error": error,
        "top_items": [item_to_dict(it) for it in top_items],
        "items": [item_to_dict(it) for it in ranked],
    }
    if args.markdown:
        print(render_markdown(result, args.top))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status in {"ok", "degraded"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
