"""git-branch-inject plugin — inject current git branch + repo into LLM context.

Registers a pre_llm_call hook that returns the current git branch name.
The context is injected into the user message before every LLM call.
"""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Any, Optional

logger = logging.getLogger(__name__)

_cache: Optional[str] = None
_cache_cwd: Optional[str] = None


def _get_git_context() -> str:
    """Return a human-readable git context string, or empty if not in a repo."""
    global _cache, _cache_cwd

    cwd = os.getcwd()
    if _cache_cwd == cwd and _cache is not None:
        return _cache

    try:
        # Get branch name
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        if not branch or branch == "HEAD":
            # Detached HEAD — get commit hash
            branch = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
            branch = f"detached@{branch}"

        # Get repo name
        remote = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        repo = remote.split("/")[-1].replace(".git", "") if remote else os.path.basename(cwd)

        # Check for dirty files
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        dirty_count = len([l for l in dirty.split("\n") if l.strip()]) if dirty else 0

        ctx = f"[git] {repo}:{branch}"
        if dirty_count:
            ctx += f" ({dirty_count} uncommitted)"

        _cache = ctx
        _cache_cwd = cwd
        return ctx
    except Exception as exc:
        logger.debug("git-branch-inject: %s", exc)
        return ""


def register(ctx) -> None:
    """Register the pre_llm_call hook."""
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)
    logger.info("git-branch-inject plugin loaded")


def _on_pre_llm_call(**kwargs: Any) -> Optional[str]:
    """Return git context for injection into the user message."""
    git_ctx = _get_git_context()
    if git_ctx:
        return {"context": git_ctx}
    return None
