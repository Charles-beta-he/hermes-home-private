"""skill-tracker plugin — automatic skill usage tracking.

Wires into post_tool_call to record every skill_view invocation.
Usage data persists to ~/.hermes/skills/steward/skill_usage.json
so the steward cron can report hot/cold breakdown.

Monkey-patches no vendor code. Survives hermes update.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

# ── Persistence ───────────────────────────────────────────────
STEWARD_DIR = Path(os.path.expanduser("~/.hermes/skills/steward"))
USAGE_FILE = STEWARD_DIR / "skill_usage.json"

_lock = threading.Lock()

# In-memory buffer: {skill_name: [timestamp, ...]}
_usage_buffer: Dict[str, list] = {}
_flush_interval = 300  # flush to disk every 5 min
_last_flush = time.time()


def _load_usage() -> Dict[str, list]:
    """Load existing usage data from disk."""
    if not USAGE_FILE.exists():
        return {}
    try:
        with open(USAGE_FILE) as f:
            data = json.load(f)
            # Normalize: ensure values are lists
            for k in list(data.keys()):
                if not isinstance(data[k], list):
                    data[k] = []
            return data
    except (json.JSONDecodeError, OSError):
        return {}


def _flush() -> None:
    """Write buffered usage to disk."""
    global _last_flush
    with _lock:
        if not _usage_buffer:
            return
        # Merge buffer into persisted data
        persisted = _load_usage()
        for skill, timestamps in _usage_buffer.items():
            if skill not in persisted:
                persisted[skill] = []
            persisted[skill].extend(timestamps)
            # Keep last 100 timestamps per skill (avoid unbounded growth)
            if len(persisted[skill]) > 100:
                persisted[skill] = persisted[skill][-100:]
        # Write atomically
        STEWARD_DIR.mkdir(parents=True, exist_ok=True)
        tmp = USAGE_FILE.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(persisted, f, indent=2)
        tmp.replace(USAGE_FILE)
        _usage_buffer.clear()
        _last_flush = time.time()


def _track(skill_name: str) -> None:
    """Record a skill_view call in the buffer."""
    global _last_flush
    with _lock:
        if skill_name not in _usage_buffer:
            _usage_buffer[skill_name] = []
        _usage_buffer[skill_name].append(time.time())
    # Flush if interval exceeded
    if time.time() - _last_flush > _flush_interval:
        _flush()


# ── Hook callbacks ────────────────────────────────────────────

_TRACKED_TOOLS = {"skill_view", "skills_list", "skill_manage"}


def _on_post_tool_call(
    tool_name: str = "",
    args: dict = None,
    result: str = "",
    **kwargs: Any,
) -> None:
    """Record skill usage when skill_view/skills_list/skill_manage is called."""
    if tool_name not in _TRACKED_TOOLS:
        return
    if args is None:
        args = {}
    if tool_name == "skill_view":
        name = args.get("name", "")
        if name:
            _track(name)
    elif tool_name == "skills_list":
        _track("__list__")
    elif tool_name == "skill_manage":
        action = args.get("action", "")
        name = args.get("name", "")
        tag = f"__manage__{action}"
        if name:
            tag = f"__manage__{action}:{name}"
        _track(tag)


def _on_session_end(**kwargs: Any) -> None:
    """Flush usage data when a session ends."""
    _flush()


# ── Plugin entry point ────────────────────────────────────────


def register(ctx) -> None:
    """Register plugin hooks."""
    # Load any existing data at startup (for in-memory reporting)
    global _usage_buffer
    persisted = _load_usage()
    # Only pre-load if the buffer is empty (first session of agent lifetime)
    if not _usage_buffer:
        with _lock:
            if not _usage_buffer:
                _usage_buffer = {k: [] for k in persisted} if persisted else {}

    ctx.register_hook("post_tool_call", _on_post_tool_call)
    ctx.register_hook("on_session_end", _on_session_end)
    logger.info("skill-tracker plugin loaded (%d skills tracked)", len(persisted))

    # Also register a slash command for manual report
    # (handled via the __init__ pattern; hermes loads it from disk)
