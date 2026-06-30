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

PH_UNRESOLVED_STATES = {
    "ph_redirect_cloudflare_blocked",
    "github_link_detected_redirect_to_landing",
    "github_repo_url_resolved_metadata_blocked",
    "github_link_detected_unresolved",
    "supplemental_landing_repo_metadata_blocked",
    "supplemental_landing_no_repo",
}

SUPPLEMENTAL_REPO_LINK_TYPES = {
    "website",
    "homepage",
    "docs",
    "documentation",
    "vercel",
    "chrome",
    "mozilla",
}

NON_REPO_SUPPLEMENTAL_TYPES = {
    "twitter",
    "x",
    "facebook",
    "linkedin",
    "app store",
    "play store",
    "gumroad",
}


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
class ExternalLinkAudit:
    source_url: str
    link_type: str = ""
    resolved_url: str = ""
    http_status: int | None = None
    state: str = "unclassified"
    ingest_decision: str = "not_evaluated"
    detail: str = ""
    github_urls: list[str] = field(default_factory=list)
    normalized_repos: list[str] = field(default_factory=list)
    metadata_errors: list[str] = field(default_factory=list)


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
    external_link_audit: list[ExternalLinkAudit] = field(default_factory=list)
    taskpool_ingest_judgement: str = "not_poolable_no_repo_evidence"


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


def is_producthunt_redirect(url: str) -> bool:
    parsed = urllib.parse.urlparse(url or "")
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host == "producthunt.com" and parsed.path.startswith("/r/")


def resolve_url_detailed(url: str, timeout: int = 15) -> tuple[str, int | None, str]:
    if not url:
        return "", None, "empty_url"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read(0)
            return resp.geturl(), getattr(resp, "status", None), ""
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read(4096).decode("utf-8", errors="ignore").lower()
        except Exception:
            body = ""
        marker = "cloudflare" if "cloudflare" in body or "just a moment" in body else ""
        error = f"http_{exc.code}" + (f":{marker}" if marker else "")
        return getattr(exc, "url", None) or url, exc.code, error
    except Exception as exc:
        return url, None, f"{type(exc).__name__}"


def resolve_url(url: str, timeout: int = 15) -> str:
    final_url, _status, _error = resolve_url_detailed(url, timeout=timeout)
    return final_url or url


def fetch_text_detailed(url: str, timeout: int = 15, max_body: int = 500_000) -> tuple[str, int | None, str]:
    if not url:
        return "", None, "empty_url"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = (resp.headers.get("content-type") or "").lower()
            status = getattr(resp, "status", None)
            if "text/html" not in content_type and "text/plain" not in content_type:
                return "", status, f"non_text_content:{content_type[:80]}"
            return resp.read(max_body).decode("utf-8", errors="ignore"), status, ""
    except urllib.error.HTTPError as exc:
        return "", exc.code, f"http_{exc.code}"
    except Exception as exc:
        return "", None, f"{type(exc).__name__}"


def fetch_text(url: str, timeout: int = 15, max_body: int = 500_000) -> str:
    text, _status, _error = fetch_text_detailed(url, timeout=timeout, max_body=max_body)
    return text


def extract_github_urls_from_text(text: str) -> list[str]:
    if not text:
        return []
    urls: list[str] = []
    for match in re.finditer(r"https?://[^\"'<>\s)]+", text):
        url = match.group(0).rstrip(".,;]")
        if "github.com" in url.lower():
            urls.append(url)
    return urls


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


def _candidate_link_audit(link_type: str, url: str, *, resolve_redirects: bool) -> ExternalLinkAudit:
    audit = ExternalLinkAudit(source_url=url, link_type=link_type)
    if not url:
        audit.state = "github_link_detected_unresolved"
        audit.ingest_decision = "needs_source_link"
        audit.detail = "empty source link"
        return audit

    final_url = url
    if resolve_redirects:
        final_url, status, error = resolve_url_detailed(url)
        audit.http_status = status
        if error:
            audit.detail = error
            if is_producthunt_redirect(url) and (status in {403, 429} or "cloudflare" in error.lower()):
                audit.resolved_url = final_url or url
                audit.state = "ph_redirect_cloudflare_blocked"
                audit.ingest_decision = "needs_supplemental_repo_link"
                return audit
    audit.resolved_url = final_url

    if "github.com" in (final_url or "").lower():
        audit.github_urls.append(final_url)
        return audit

    if resolve_redirects and final_url.startswith(("http://", "https://")):
        text, status, error = fetch_text_detailed(final_url)
        if audit.http_status is None:
            audit.http_status = status
        if error and not audit.detail:
            audit.detail = f"landing_fetch_{error}"
        audit.github_urls.extend(extract_github_urls_from_text(text))
        if not audit.github_urls:
            audit.state = "github_link_detected_redirect_to_landing"
            audit.ingest_decision = "needs_supplemental_repo_link"
            audit.detail = audit.detail or "landing_page_no_repo"
    return audit


def _finalize_audit_without_repo(audit: ExternalLinkAudit) -> None:
    if audit.state == "unclassified":
        audit.state = "github_link_detected_unresolved"
    if audit.ingest_decision == "not_evaluated":
        audit.ingest_decision = "needs_supplemental_repo_link"
    if not audit.detail:
        audit.detail = "no_normalized_github_repo_after_bounded_resolution"


def _is_primary_source_link(link_type: str, url: str) -> bool:
    lower_type = (link_type or "").strip().lower()
    lower_url = (url or "").lower()
    return "github" in lower_type or "gitlab" in lower_type or "source" in lower_type or "github.com" in lower_url


def _supplemental_repo_links(item: ProductItem, primary_urls: set[str]) -> list[tuple[str, str]]:
    """Return bounded non-social landing links that may expose repo URLs.

    Product Hunt often gives official GitHub/source links as /r/... redirects. When
    those redirects are Cloudflare-blocked from the terminal, a product's Website or
    docs link can still expose the same public repository in page HTML. This keeps the
    pipeline fail-closed: supplemental links may upgrade a task only after a concrete
    repo URL plus GitHub metadata/readback is observed; otherwise the original
    unresolved judgement remains.
    """
    links: list[tuple[str, str]] = []
    if item.website and item.website not in primary_urls:
        links.append(("Website", item.website))
    for link in item.links:
        link_type = (link.get("type") or "").strip()
        url = link.get("url") or ""
        lower_type = link_type.lower()
        if not url or url in primary_urls or _is_primary_source_link(link_type, url):
            continue
        if lower_type in NON_REPO_SUPPLEMENTAL_TYPES:
            continue
        if lower_type in SUPPLEMENTAL_REPO_LINK_TYPES or lower_type.endswith(" site"):
            links.append((link_type or "supplemental", url))
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for link_type, url in links:
        if url in seen:
            continue
        seen.add(url)
        unique.append((link_type, url))
    return unique


def _attach_repo_from_audit(item: ProductItem, audit: ExternalLinkAudit, seen_repos: set[str]) -> tuple[bool, bool]:
    verified_repo = False
    metadata_blocked = False
    for gh_url in audit.github_urls:
        normalized = normalize_github_repo_url(gh_url)
        if not normalized:
            continue
        repo_full, repo_url = normalized
        if repo_full in seen_repos:
            continue
        seen_repos.add(repo_full)
        audit.normalized_repos.append(repo_full)
        repo_meta = enrich_repo(repo_full, repo_url)
        item.repos.append(repo_meta)
        if repo_meta.error:
            metadata_blocked = True
            audit.metadata_errors.append(f"{repo_full}:{repo_meta.error}")
        else:
            verified_repo = True
    return verified_repo, metadata_blocked


def detect_and_enrich(items: list[ProductItem], resolve_redirects: bool) -> None:
    for item in items:
        candidate_links: list[tuple[str, str]] = []
        for link in item.links:
            link_type = (link.get("type") or "").strip()
            url = link.get("url") or ""
            if _is_primary_source_link(link_type, url):
                candidate_links.append((link_type, url))

        github_urls: list[str] = []
        seen_repos: set[str] = set()
        verified_repo = False
        metadata_blocked = False
        for link_type, url in candidate_links:
            audit = _candidate_link_audit(link_type, url, resolve_redirects=resolve_redirects)
            audit_verified, audit_metadata_blocked = _attach_repo_from_audit(item, audit, seen_repos)
            verified_repo = verified_repo or audit_verified
            metadata_blocked = metadata_blocked or audit_metadata_blocked
            github_urls.extend(audit.github_urls)
            if audit.normalized_repos and audit.metadata_errors and not audit_verified:
                audit.state = "github_repo_url_resolved_metadata_blocked"
                audit.ingest_decision = "limited_retry_github_metadata_or_manual_readback"
                audit.detail = ";".join(audit.metadata_errors)
            elif audit.normalized_repos:
                audit.state = "github_repo_verified"
                audit.ingest_decision = "poolable_only_after_hermes_mapping"
                audit.detail = "repo URL and GitHub metadata verified"
            else:
                _finalize_audit_without_repo(audit)
            item.external_link_audit.append(audit)

        primary_states = {audit.state for audit in item.external_link_audit}
        if not verified_repo and "ph_redirect_cloudflare_blocked" in primary_states:
            for link_type, url in _supplemental_repo_links(item, {url for _link_type, url in candidate_links}):
                audit = _candidate_link_audit(f"supplemental:{link_type}", url, resolve_redirects=resolve_redirects)
                audit_verified, audit_metadata_blocked = _attach_repo_from_audit(item, audit, seen_repos)
                verified_repo = verified_repo or audit_verified
                metadata_blocked = metadata_blocked or audit_metadata_blocked
                github_urls.extend(audit.github_urls)
                if audit.normalized_repos and audit.metadata_errors and not audit_verified:
                    audit.state = "supplemental_landing_repo_metadata_blocked"
                    audit.ingest_decision = "limited_retry_github_metadata_or_manual_readback"
                    audit.detail = ";".join(audit.metadata_errors)
                elif audit.normalized_repos:
                    audit.state = "github_repo_verified"
                    audit.ingest_decision = "poolable_only_after_hermes_mapping"
                    audit.detail = "supplemental landing page exposed repo URL and GitHub metadata was verified"
                elif audit.state in {"github_link_detected_unresolved", "github_link_detected_redirect_to_landing"}:
                    audit.state = "supplemental_landing_no_repo"
                    audit.ingest_decision = "not_poolable_supplemental_no_repo"
                    audit.detail = audit.detail or "supplemental landing page did not expose a normalized GitHub repo"
                item.external_link_audit.append(audit)
                if verified_repo:
                    break

        # Keep unresolved Product Hunt redirect URLs as evidence too. Product Hunt often
        # returns /r/... tracking redirects for productLinks, and terminal fetches may be
        # blocked by Cloudflare. The link type itself is still official API evidence.
        item.github_links = github_urls or [url for _link_type, url in candidate_links]
        if verified_repo:
            item.open_source_status = "github_repo_verified"
            item.taskpool_ingest_judgement = "poolable_only_after_hermes_mapping"
            if "ph_redirect_cloudflare_blocked" in primary_states:
                item.reasons.append("Product Hunt GitHub/source redirect was blocked, but a bounded supplemental landing-page scan exposed a verified GitHub repo")
            else:
                item.reasons.append("Product Hunt productLinks contains GitHub/source-code evidence and GitHub repo metadata was verified")
        elif metadata_blocked:
            item.open_source_status = "github_repo_url_resolved_metadata_blocked"
            item.taskpool_ingest_judgement = "limited_repo_url_resolved_metadata_blocked"
            item.reasons.append("Product Hunt GitHub/source or supplemental landing link resolved to a repo URL, but GitHub metadata readback was blocked/rate-limited")
        elif candidate_links:
            states = {audit.state for audit in item.external_link_audit}
            if "ph_redirect_cloudflare_blocked" in states:
                item.open_source_status = "ph_redirect_cloudflare_blocked"
                item.reasons.append("Product Hunt GitHub/source redirect was blocked before repo URL resolution; supplemental landing scan did not verify a repo")
            elif "github_link_detected_redirect_to_landing" in states or "supplemental_landing_no_repo" in states:
                item.open_source_status = "github_link_detected_redirect_to_landing"
                item.reasons.append("Product Hunt GitHub/source link reached a landing page, but bounded scan found no repo URL")
            else:
                item.open_source_status = "github_link_detected_unresolved"
                item.reasons.append("Product Hunt productLinks contains GitHub/source-code evidence; repo URL could not be resolved in terminal")
            item.taskpool_ingest_judgement = "not_poolable_needs_repo_link"
        else:
            text = f"{item.name} {item.tagline} {item.website} " + " ".join(l.get("url", "") for l in item.links)
            lower = text.lower()
            if any(k in lower for k in ["open source", "opensource", "github.com", "github"]):
                item.open_source_status = "possible_open_source_unverified"
                item.taskpool_ingest_judgement = "not_poolable_text_only_unverified"
                item.reasons.append("Text mentions open-source/GitHub but no repository metadata was verified")
            else:
                item.open_source_status = "unknown"
                item.taskpool_ingest_judgement = "not_poolable_true_no_repo_evidence"


def score_items(items: list[ProductItem]) -> None:
    for item in items:
        text = f"{item.name} {item.tagline} {item.website} " + " ".join(l.get("type", "") + " " + l.get("url", "") for l in item.links)
        lower = text.lower()
        score = 0
        for kw in INTEREST_KEYWORDS:
            if kw in lower:
                score += 2 if kw in {"ai", "agent", "developer", "github", "open source", "api", "cli", "llm", "code"} else 1
        if item.open_source_status in {"github_repo_verified", "github_link_detected_unresolved", "github_repo_url_resolved_metadata_blocked", "ph_redirect_cloudflare_blocked", "github_link_detected_redirect_to_landing"}:
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
        "external_link_audit": [audit.__dict__ for audit in item.external_link_audit],
        "taskpool_ingest_judgement": item.taskpool_ingest_judgement,
        "reasons": item.reasons,
    }


def render_markdown(result: dict[str, Any], top: int) -> str:
    lines = []
    lines.append("## Product Hunt 产品发现")
    lines.append("")
    audit_summary = result.get("ph_external_link_audit") or {}
    lines.append(f"- 状态：{result['status']}；来源：{result['source_mode']}；采样：{result['items_seen']}；GitHub/source 外链命中：{result.get('github_source_link_count', 0)}；repo 元数据命中：{result['github_repo_count']}")
    if audit_summary:
        lines.append(f"- PH 外链审计：{audit_summary.get('state_counts', {})}；入池判定：{audit_summary.get('decision_counts', {})}")
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
        elif item.get("open_source_status") in PH_UNRESOLVED_STATES:
            status = item.get("open_source_status")
            audit_bits = []
            for audit in item.get("external_link_audit") or []:
                audit_bits.append(f"{audit.get('state')} / {audit.get('ingest_decision')}")
            detail = "；".join(audit_bits) if audit_bits else status
            lines.append(f"   - 开源证据：Product Hunt 官方 API 标记了 GitHub/source 外链；分层判定：{detail}")
        else:
            status = item.get("open_source_status") or "unknown"
            label = "未发现开源证据" if status == "unknown" else "疑似开源但未验证"
            lines.append(f"   - 开源证据：{label}")
        if item.get("taskpool_ingest_judgement"):
            lines.append(f"   - 入池判定：{item['taskpool_ingest_judgement']}")
        if item.get("reasons"):
            lines.append(f"   - 入选理由：{'；'.join(item['reasons'][:2])}")
    audit_items = (result.get("ph_external_link_audit") or {}).get("items") or []
    if audit_items:
        lines.append("")
        lines.append("### PH GitHub/source 外链审计")
        lines.append("| 产品 | 状态 | 入池判定 | 证据/局限 |")
        lines.append("|---|---|---|---|")
        for audit in audit_items[:top]:
            lines.append(f"| {audit.get('name')} | `{audit.get('state')}` | `{audit.get('ingest_decision')}` | {audit.get('detail') or audit.get('source_url') or ''} |")
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
    repo_count = sum(1 for it in items for repo in it.repos if not repo.error)
    repo_url_count = sum(1 for it in items for repo in it.repos)
    source_link_count = sum(1 for it in items if it.open_source_status in {"github_repo_verified", "github_link_detected_unresolved", "github_repo_url_resolved_metadata_blocked", "ph_redirect_cloudflare_blocked", "github_link_detected_redirect_to_landing"})
    state_counts: dict[str, int] = {}
    decision_counts: dict[str, int] = {}
    audit_items: list[dict[str, Any]] = []
    for it in items:
        state_counts[it.open_source_status] = state_counts.get(it.open_source_status, 0) + 1
        decision_counts[it.taskpool_ingest_judgement] = decision_counts.get(it.taskpool_ingest_judgement, 0) + 1
        for audit in it.external_link_audit:
            audit_items.append({
                "name": it.name,
                "state": audit.state,
                "ingest_decision": audit.ingest_decision,
                "detail": audit.detail,
                "source_url": audit.source_url,
                "resolved_url": audit.resolved_url,
                "normalized_repos": audit.normalized_repos,
                "metadata_errors": audit.metadata_errors,
            })
    result = {
        "status": status,
        "source": "producthunt",
        "source_mode": meta.get("mode"),
        "endpoint": meta.get("endpoint"),
        "items_seen": len(items),
        "github_source_link_count": source_link_count,
        "github_repo_count": repo_count,
        "github_repo_url_count": repo_url_count,
        "ph_external_link_audit": {
            "state_counts": state_counts,
            "decision_counts": decision_counts,
            "items": audit_items,
        },
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
