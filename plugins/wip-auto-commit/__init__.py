"""wip-auto-commit plugin — auto-create WIP git checkpoints after LLM turns.

Creates lightweight git commits with a "WIP:" prefix after each LLM turn.
Configurable cooldown (default: 60s) prevents commit spam on rapid successive turns.
Only commits when files have actually changed.
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from typing import Any

logger = logging.getLogger(__name__)

_last_commit_time: float = 0
_COOLDOWN = 60  # seconds between WIP commits


def _has_changes() -> bool:
    """Check if there are uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def _wip_commit() -> None:
    """Create a WIP commit with timestamp."""
    global _last_commit_time

    now = time.time()
    if now - _last_commit_time < _COOLDOWN:
        logger.debug("wip-auto-commit: skipping (cooldown %.0fs remaining)",
                      _COOLDOWN - (now - _last_commit_time))
        return

    if not _has_changes():
        logger.debug("wip-auto-commit: no changes to commit")
        return

    try:
        ts = time.strftime("%H:%M:%S")
        subprocess.run(
            ["git", "add", "-A"],
            capture_output=True, timeout=10,
        )
        result = subprocess.run(
            ["git", "commit", "-m", f"WIP: auto-checkpoint @{ts} [hermes]",
             "--no-verify", "--allow-empty"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            logger.info("wip-auto-commit: created WIP checkpoint @%s", ts)
            _last_commit_time = now
        else:
            logger.debug("wip-auto-commit: %s", result.stderr.strip() or "no-op")
    except Exception as exc:
        logger.debug("wip-auto-commit: failed — %s", exc)


def register(ctx) -> None:
    """Register the post_llm_call and on_session_end hooks."""
    ctx.register_hook("post_llm_call", _on_post_llm_call)
    ctx.register_hook("on_session_end", _on_session_end)
    logger.info("wip-auto-commit plugin loaded (cooldown=%ds)", _COOLDOWN)


def _on_post_llm_call(**kwargs: Any) -> None:
    """Create WIP checkpoint after each LLM call."""
    _wip_commit()


def _on_session_end(**kwargs: Any) -> None:
    """Force a final WIP checkpoint when session ends."""
    global _last_commit_time
    _last_commit_time = 0  # bypass cooldown
    _wip_commit()
