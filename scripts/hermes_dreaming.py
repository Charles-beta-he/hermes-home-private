#!/usr/bin/env python3
"""Hermes Dreaming — Loop A: typed receipts, selector state, vocabulary,
ownership preflight, candidate-only generation, orchestrated run.

Frozen contract: ``docs/private/dreaming-v1-frozen-spec-20260801.md`` (Loop A).

Scope of this module:

1. a typed stage receipt + closed reason taxonomy that keeps ``job_success``,
   ``effective_audit``, ``candidate_generated``, ``state_advanced`` and
   ``promoted`` separate, plus a classifier that requires typed evidence;
   absent, malformed, stale, or inconsistent receipts all fail closed;
2. a selector that separates ``last_attempt_at`` from ``last_advanced_at``,
   records every attempt regardless of outcome, and applies deterministic
   cooldown / no-progress demotion plus a diversity rule so a repeatedly
   no-progress target cannot permanently dominate selection; it also keeps
   the old priority formula as ``shadow_score`` evidence without letting it
   drive selection;
3. generator/evaluator vocabulary alignment (including ``示例`` and
   ``约束``) with explicit classification of unsupported findings;
4. an ownership/path preflight guard (injectable euid + stat/lstat/access)
   that fails closed on EUID 0 against a non-root home, owner mismatches,
   unreadable targets and symlink escapes, before any candidate write;
5. candidate-only generation: the active ``SKILL.md`` is only ever read and
   hashed, never mutated — every write is one flat regular-file artifact under
   the pre-provisioned ``HERMES_HOME/state/dreaming/candidates`` root;
6. an orchestrated run (``run_dreaming_cycle``) that chains selection ->
   ownership -> generation -> evaluation, records every outcome against the
   selector state, and never sets ``promoted`` or ``state_advanced`` — Loop A
   has no promotion gate, so nothing about the active skill ever advances.
"""

from __future__ import annotations

import base64
import ctypes
import errno
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from hermes_evolution_store import file_sha256

# --------------------------------------------------------------------------
# receipt schema / taxonomy
# --------------------------------------------------------------------------

RECEIPT_SCHEMA = "hermes_dreaming_receipt_v1"
SELECTOR_STATE_SCHEMA = "hermes_dreaming_selector_state_v1"
TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

STAGE_SELECTION = "selection"
STAGE_OWNERSHIP = "ownership"
STAGE_GENERATION = "generation"
STAGE_EVALUATION = "evaluation"
STAGE_RUN = "run"
STAGES: tuple[str, ...] = (STAGE_SELECTION, STAGE_OWNERSHIP, STAGE_GENERATION, STAGE_EVALUATION, STAGE_RUN)

REASON_OK = "ok"
REASON_NO_TARGETS = "no_targets"
REASON_ALL_COOLING_DOWN = "all_targets_cooling_down"
REASON_NO_FINDINGS = "no_findings"
REASON_UNSUPPORTED_ONLY = "unsupported_findings_only"
REASON_EVALUATION_REJECTED = "generator_evaluator_mismatch"
REASON_NO_STATE_CHANGE = "no_state_change"
REASON_LEGACY_FALLBACK = "legacy_stdout_fallback"
REASON_RECEIPT_INVALID = "receipt_invalid"
REASON_RECEIPT_MISSING = "receipt_missing"
REASON_SCRIPT_RETURNCODE_NONZERO = "script_returncode_nonzero"
REASON_OWNERSHIP_ROOT_BLOCKED = "root_euid_blocked"
REASON_OWNERSHIP_HOME_MISMATCH = "hermes_home_owner_mismatch"
REASON_OWNERSHIP_TARGET_MISMATCH = "active_target_owner_mismatch"
REASON_OWNERSHIP_UNREADABLE = "active_target_unreadable"
REASON_OWNERSHIP_SYMLINK_ESCAPE = "symlink_escape_detected"
REASON_CANDIDATE_DEST_ESCAPE = "candidate_destination_escape"
REASON_CANDIDATE_DEST_CONFLICT = "candidate_destination_conflict"
REASON_CANDIDATE_DEST_ANCESTOR_OWNER_MISMATCH = "candidate_destination_ancestor_owner_mismatch"
REASON_CANDIDATE_ROOT_UNPROVISIONED = "candidate_root_unprovisioned"
REASON_CANDIDATE_INTERNAL_FAILURE = "candidate_internal_failure"
REASON_CANDIDATE_PUBLISH_UNSUPPORTED = "candidate_publish_unsupported"
REASON_CANDIDATE_READBACK_FAILED = "candidate_readback_failed"
REASON_CANDIDATE_ARTIFACT_INVALID = "candidate_artifact_invalid"
REASON_CANDIDATE_CLEANUP_FAILED = "candidate_cleanup_failed"
REASON_CANDIDATE_RESIDUAL_IDENTITY_MISMATCH = "candidate_residual_identity_mismatch"
REASON_CANDIDATE_RESIDUAL_UNSAFE = "candidate_residual_cleanup_unsafe"
REASON_CANDIDATE_GENERATED = "candidate_generated"
REASON_ACTIVE_TREE_SYMLINK = "active_skill_tree_symlink"
CANDIDATE_ARTIFACT_SCHEMA_VERSION = "hermes.dreaming.candidate.v2"
_ARTIFACT_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")
_ARTIFACT_NAME_MAX = 240
REASON_RECEIPT_RUN_ID_MISMATCH = "receipt_run_id_mismatch"
REASON_UNEXPECTED_EXCEPTION = "unexpected_exception"
REASON_SUBPROCESS_TIMEOUT = "subprocess_timeout"
REASON_STATE_BOUNDARY_PATH_ESCAPE = "state_dreaming_path_escape"
REASON_STATE_BOUNDARY_SYMLINK_ESCAPE = "state_dreaming_symlink_escape"

NO_STATE_CHANGE_REASONS = frozenset(
    {
        REASON_NO_TARGETS,
        REASON_ALL_COOLING_DOWN,
        REASON_NO_FINDINGS,
        REASON_UNSUPPORTED_ONLY,
        REASON_EVALUATION_REJECTED,
        REASON_NO_STATE_CHANGE,
    }
)

OWNERSHIP_BLOCK_REASONS = frozenset(
    {
        REASON_OWNERSHIP_ROOT_BLOCKED,
        REASON_OWNERSHIP_HOME_MISMATCH,
        REASON_OWNERSHIP_TARGET_MISMATCH,
        REASON_OWNERSHIP_UNREADABLE,
        REASON_OWNERSHIP_SYMLINK_ESCAPE,
        REASON_CANDIDATE_DEST_ESCAPE,
        REASON_CANDIDATE_DEST_ANCESTOR_OWNER_MISMATCH,
    }
)

# Generation-stage reasons that mean a candidate write was refused for
# safety, distinct from benign "nothing to do" outcomes: these always set
# ``write_blocked``/``degraded`` on the run receipt.
GENERATION_WRITE_BLOCK_REASONS = frozenset(
    {
        REASON_CANDIDATE_DEST_ESCAPE,
        REASON_CANDIDATE_DEST_ANCESTOR_OWNER_MISMATCH,
        REASON_CANDIDATE_ROOT_UNPROVISIONED,
        REASON_ACTIVE_TREE_SYMLINK,
        REASON_CANDIDATE_DEST_CONFLICT,
        REASON_CANDIDATE_INTERNAL_FAILURE,
        REASON_CANDIDATE_PUBLISH_UNSUPPORTED,
        REASON_CANDIDATE_READBACK_FAILED,
        REASON_CANDIDATE_ARTIFACT_INVALID,
        REASON_CANDIDATE_CLEANUP_FAILED,
        REASON_CANDIDATE_RESIDUAL_IDENTITY_MISMATCH,
        REASON_CANDIDATE_RESIDUAL_UNSAFE,
    }
)

REASON_TAXONOMY = (
    frozenset(
        {
            REASON_OK,
            REASON_LEGACY_FALLBACK,
            REASON_RECEIPT_INVALID,
            REASON_RECEIPT_MISSING,
            REASON_RECEIPT_RUN_ID_MISMATCH,
            REASON_SCRIPT_RETURNCODE_NONZERO,
            REASON_CANDIDATE_GENERATED,
            REASON_UNEXPECTED_EXCEPTION,
        }
    )
    | NO_STATE_CHANGE_REASONS
    | OWNERSHIP_BLOCK_REASONS
    | GENERATION_WRITE_BLOCK_REASONS
    | frozenset({REASON_SUBPROCESS_TIMEOUT})
    | frozenset({REASON_STATE_BOUNDARY_PATH_ESCAPE, REASON_STATE_BOUNDARY_SYMLINK_ESCAPE})
)

OUTCOME_ADVANCED = "advanced"
OUTCOME_NO_CHANGE = "no_change"
OUTCOME_REJECTED = "rejected"
OUTCOME_UNSUPPORTED = "unsupported"
OUTCOMES = frozenset({OUTCOME_ADVANCED, OUTCOME_NO_CHANGE, OUTCOME_REJECTED, OUTCOME_UNSUPPORTED})


# --------------------------------------------------------------------------
# time helpers
# --------------------------------------------------------------------------


def format_ts(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime(TS_FORMAT)


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


# --------------------------------------------------------------------------
# atomic writes
# --------------------------------------------------------------------------


def atomic_write_text(path: str | Path, content: str) -> Path:
    """Write ``content`` to ``path`` via temp-file + ``os.replace``.

    Never leaves a partially written target: either the old bytes remain
    (write/replace failed, temp file cleaned up) or the new bytes are fully
    in place. Never leaves a temp-file residue in either case.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-", dir=str(target.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, target)
    except OSError:
        tmp_path.unlink(missing_ok=True)
        raise
    return target


# --------------------------------------------------------------------------
# typed receipts
# --------------------------------------------------------------------------


@dataclass
class StageReceipt:
    stage: str
    ok: bool
    reason: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"stage": self.stage, "ok": self.ok, "reason": self.reason, "details": self.details}


@dataclass
class RunReceipt:
    run_id: str
    ts: str
    target: str | None = None
    job_success: bool = True
    effective_audit: bool = False
    candidate_generated: bool = False
    state_advanced: bool = False
    promoted: bool = False
    degraded: bool = False
    write_blocked: bool = False
    reasons: list[str] = field(default_factory=list)
    stages: list[StageReceipt] = field(default_factory=list)

    def add_stage(self, stage: StageReceipt) -> StageReceipt:
        self.stages.append(stage)
        return stage

    def add_reason(self, reason: str) -> None:
        if reason not in self.reasons:
            self.reasons.append(reason)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema": RECEIPT_SCHEMA,
            "run_id": self.run_id,
            "ts": self.ts,
            "target": self.target,
            "job_success": self.job_success,
            "effective_audit": self.effective_audit,
            "candidate_generated": self.candidate_generated,
            "state_advanced": self.state_advanced,
            "promoted": self.promoted,
            "degraded": self.degraded,
            "write_blocked": self.write_blocked,
            "reasons": list(self.reasons),
            "stages": [stage.to_dict() for stage in self.stages],
        }
        payload["candidate_artifact"] = extract_candidate_artifact_projection(payload)
        return payload


REQUIRED_RECEIPT_FLAGS = (
    "job_success",
    "effective_audit",
    "candidate_generated",
    "state_advanced",
    "promoted",
    "degraded",
    "write_blocked",
)

# Canonical Loop A stage order. Receipts may be a contiguous prefix of the
# main pipeline, or a single STAGE_RUN failure stage.
_LOOP_A_PIPELINE_STAGES: tuple[str, ...] = (
    STAGE_SELECTION,
    STAGE_OWNERSHIP,
    STAGE_GENERATION,
    STAGE_EVALUATION,
)

CANDIDATE_ARTIFACT_PROJECTION_KEYS: tuple[str, ...] = (
    "candidate_artifact",
    "artifact_schema_version",
    "artifact_sha256",
    "artifact_size",
    "artifact_st_dev",
    "artifact_st_ino",
    "source_sha256",
    "candidate_sha256",
    "candidate_size",
    "run_id",
    "skill_name",
)

_TS_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _is_safe_artifact_filename(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if "/" in value or "\\" in value or "\x00" in value:
        return False
    if value != Path(value).name:
        return False
    return value.startswith("candidate-v2--") and value.endswith(".json")


def validate_candidate_artifact_projection(
    details: Any,
    *,
    expected_run_id: str | None = None,
    expected_skill_name: str | None = None,
) -> list[str]:
    """Strict V2 artifact identity projection checks."""
    errors: list[str] = []
    if not isinstance(details, dict):
        return ["candidate_artifact_projection_not_object"]
    for key in CANDIDATE_ARTIFACT_PROJECTION_KEYS:
        if key not in details:
            errors.append(f"missing_artifact_field:{key}")
    if errors:
        return errors
    filename = details.get("candidate_artifact")
    if not _is_safe_artifact_filename(filename):
        errors.append("invalid_artifact_filename")
    if details.get("artifact_schema_version") != CANDIDATE_ARTIFACT_SCHEMA_VERSION:
        errors.append("invalid_artifact_schema_version")
    for digest_key in ("artifact_sha256", "source_sha256", "candidate_sha256"):
        value = details.get(digest_key)
        if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
            errors.append(f"invalid_digest:{digest_key}")
    for int_key in ("artifact_size", "artifact_st_dev", "artifact_st_ino", "candidate_size"):
        value = details.get(int_key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"invalid_int:{int_key}")
    if not _is_nonempty_str(details.get("run_id")):
        errors.append("invalid_artifact_run_id")
    if not _is_nonempty_str(details.get("skill_name")):
        errors.append("invalid_artifact_skill_name")
    if expected_run_id is not None and details.get("run_id") != expected_run_id:
        errors.append("artifact_run_id_mismatch")
    if expected_skill_name is not None and details.get("skill_name") != expected_skill_name:
        errors.append("artifact_skill_name_mismatch")
    return errors


def extract_candidate_artifact_projection(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Return the authorizing V2 artifact projection, or None when non-authorizing."""
    if not isinstance(payload, dict):
        return None
    if payload.get("candidate_generated") is not True:
        return None
    if payload.get("job_success") is not True:
        return None
    stages = payload.get("stages")
    if not isinstance(stages, list):
        return None
    generation_success: list[dict[str, Any]] = []
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        if stage.get("stage") == STAGE_GENERATION and stage.get("ok") is True:
            generation_success.append(stage)
    if len(generation_success) != 1:
        return None
    details = generation_success[0].get("details")
    if not isinstance(details, dict):
        return None
    errors = validate_candidate_artifact_projection(
        details,
        expected_run_id=payload.get("run_id") if isinstance(payload.get("run_id"), str) else None,
        expected_skill_name=payload.get("target") if isinstance(payload.get("target"), str) else None,
    )
    if errors:
        return None
    return {key: details[key] for key in CANDIDATE_ARTIFACT_PROJECTION_KEYS}


def _validate_stage_inventory(stages: list[Any], *, candidate_generated: bool) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    names: list[str] = []
    for stage in stages:
        if not isinstance(stage, dict):
            errors.append("stage_not_object")
            continue
        name = stage.get("stage")
        if name not in STAGES:
            errors.append(f"unknown_stage:{name}")
            continue
        if name in seen:
            errors.append(f"duplicate_stage:{name}")
        seen.add(name)
        names.append(name)
        if not isinstance(stage.get("ok"), bool):
            errors.append("stage_ok_not_bool")
        reason = stage.get("reason")
        if reason not in REASON_TAXONOMY:
            errors.append(f"unknown_reason:{reason}")
        if not isinstance(stage.get("details"), dict):
            errors.append("stage_details_not_dict")
        ok = stage.get("ok")
        if ok is True and reason not in {REASON_OK, REASON_CANDIDATE_GENERATED}:
            errors.append(f"stage_ok_reason_inconsistent:{name}")
        if ok is True and name == STAGE_GENERATION and reason != REASON_CANDIDATE_GENERATED:
            errors.append("generation_success_requires_candidate_generated_reason")
        if ok is False and reason in {REASON_OK, REASON_CANDIDATE_GENERATED}:
            errors.append(f"stage_fail_reason_inconsistent:{name}")
    if not names:
        # Empty stage list is only valid when nothing was audited and no candidate.
        if candidate_generated:
            errors.append("candidate_generated_requires_stages")
        return errors
    if names == [STAGE_RUN]:
        return errors
    # Contiguous prefix of the Loop A pipeline, no gaps/reordering.
    if names[0] != STAGE_SELECTION:
        errors.append("stage_order_invalid")
        return errors
    expected_prefix = list(_LOOP_A_PIPELINE_STAGES[: len(names)])
    if names != expected_prefix:
        errors.append("stage_order_invalid")
    return errors


def validate_receipt(payload: Any) -> list[str]:
    """Return semantic schema violations; empty list means the receipt is usable."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["receipt_not_object"]
    if payload.get("schema") != RECEIPT_SCHEMA:
        errors.append("schema_mismatch")

    run_id = payload.get("run_id")
    if not _is_nonempty_str(run_id):
        errors.append("missing_run_id" if run_id in (None, "") else "run_id_not_str")

    ts = payload.get("ts")
    if not isinstance(ts, str) or not _TS_RE.fullmatch(ts):
        errors.append("ts_invalid")

    target = payload.get("target")
    if target is not None and not isinstance(target, str):
        errors.append("target_not_str_or_null")
    if isinstance(target, str) and not target:
        errors.append("target_empty_str")

    for flag in REQUIRED_RECEIPT_FLAGS:
        if flag not in payload:
            errors.append(f"missing_flag:{flag}")
        elif not isinstance(payload[flag], bool):
            errors.append(f"non_bool_flag:{flag}")

    # Loop A is candidate-only: advancement/promotion claims are never valid evidence.
    if payload.get("state_advanced") is True:
        errors.append("loop_a_state_advanced_forbidden")
    if payload.get("promoted") is True:
        errors.append("loop_a_promoted_forbidden")

    reasons = payload.get("reasons")
    if not isinstance(reasons, list):
        errors.append("reasons_not_list")
    else:
        for reason in reasons:
            if not isinstance(reason, str):
                errors.append("reason_not_str")
            elif reason not in REASON_TAXONOMY:
                errors.append(f"unknown_reason:{reason}")

    stages = payload.get("stages")
    if not isinstance(stages, list):
        errors.append("stages_not_list")
        stages = []
    else:
        errors.extend(
            _validate_stage_inventory(
                stages, candidate_generated=payload.get("candidate_generated") is True
            )
        )

    candidate_generated = payload.get("candidate_generated") is True
    generation_success = [
        stage
        for stage in stages
        if isinstance(stage, dict)
        and stage.get("stage") == STAGE_GENERATION
        and stage.get("ok") is True
    ]
    if candidate_generated:
        if len(generation_success) != 1:
            errors.append("candidate_generated_requires_one_success_generation_stage")
        else:
            details = generation_success[0].get("details")
            skill_name = None
            if isinstance(details, dict) and isinstance(details.get("skill_name"), str):
                skill_name = details.get("skill_name")
            elif isinstance(target, str):
                skill_name = target
            errors.extend(
                validate_candidate_artifact_projection(
                    details if isinstance(details, dict) else details,
                    expected_run_id=run_id if isinstance(run_id, str) else None,
                    expected_skill_name=skill_name,
                )
            )
            if isinstance(details, dict):
                if target is not None and details.get("skill_name") != target:
                    errors.append("artifact_target_skill_mismatch")
                if generation_success[0].get("reason") != REASON_CANDIDATE_GENERATED:
                    errors.append("generation_success_reason_mismatch")
        if REASON_CANDIDATE_GENERATED not in (reasons or []):
            errors.append("candidate_generated_requires_reason")
    else:
        if generation_success:
            errors.append("generation_success_requires_candidate_generated_flag")

    return errors


_RECEIPT_UNREADABLE = object()  # sentinel: path exists but is unusable as evidence


def load_receipt(path: str | Path | None) -> dict[str, Any] | None:
    """Return the parsed receipt, ``None`` if genuinely absent, or the
    ``_RECEIPT_UNREADABLE`` sentinel if something exists at ``path`` but
    cannot serve as evidence (symlink, non-regular file, unreadable, or
    malformed JSON). Absent vs. unreadable must stay distinguishable: only
    genuine absence may fall back to legacy stdout parsing.
    """
    if not path:
        return None
    target = Path(path)
    if not target.exists() and not target.is_symlink():
        return None
    if target.is_symlink() or not target.is_file():
        return _RECEIPT_UNREADABLE
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return _RECEIPT_UNREADABLE


def classify_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    """Map a typed receipt onto wrapper health semantics.

    ``job_success`` is about the process, ``effective_audit`` about whether a
    target was really audited, ``candidate_generated`` about artifact
    creation, ``state_advanced`` about persisted dreaming-state progress, and
    ``promoted`` about the active skill. They never collapse into a single
    boolean.
    """
    reasons = [r for r in (payload.get("reasons") or []) if isinstance(r, str)]
    job_success = bool(payload.get("job_success"))
    effective_audit = bool(payload.get("effective_audit"))
    candidate_generated = bool(payload.get("candidate_generated"))
    state_advanced = bool(payload.get("state_advanced"))
    promoted = bool(payload.get("promoted"))
    write_blocked = bool(payload.get("write_blocked"))
    degraded = bool(payload.get("degraded")) or write_blocked
    artifact = extract_candidate_artifact_projection(payload) if candidate_generated and job_success else None
    if candidate_generated and job_success and artifact is None:
        # Semantic refuse: flag claimed success without a bound V2 projection.
        job_success = False
        candidate_generated = False
        degraded = True
        status = "ERROR"
        if REASON_RECEIPT_INVALID not in reasons:
            reasons.append(REASON_RECEIPT_INVALID)
    elif not job_success:
        status = "ERROR"
        artifact = None
        candidate_generated = False
    elif write_blocked:
        status = "WARN"
        artifact = None
        candidate_generated = False
    elif candidate_generated:
        status = "OK"
    elif effective_audit:
        status = "OK"
        if not any(reason in NO_STATE_CHANGE_REASONS for reason in reasons):
            reasons.append(REASON_NO_STATE_CHANGE)
    else:
        status = "WARN"

    return {
        "status": status,
        "job_success": job_success,
        "effective_audit": effective_audit,
        "candidate_generated": candidate_generated,
        "state_advanced": False,  # Loop A never projects advancement
        "promoted": False,
        "degraded": degraded,
        "write_blocked": write_blocked,
        "reasons": reasons,
        "receipt_source": "typed_receipt",
        "run_id": payload.get("run_id"),
        "target": payload.get("target"),
        "candidate_artifact": artifact,
    }


def _fail_closed_receipt_result(
    fallback_reason: str, receipt_errors: list[str], payload: dict[str, Any]
) -> dict[str, Any]:
    """A receipt file exists but is malformed/invalid/mismatched.

    Its presence means this run's real evidence is untrustworthy — legacy
    stdout parsing must never be consulted to paper over that, since stdout
    reflects whatever happened, valid receipt or not, and could otherwise
    upgrade a fail-closed run to OK/advanced/candidate_generated/promoted.
    """
    return {
        "status": "ERROR",
        "job_success": False,
        "effective_audit": False,
        "candidate_generated": False,
        "state_advanced": False,
        "promoted": False,
        "degraded": True,
        "write_blocked": False,
        "reasons": [fallback_reason],
        "receipt_source": "receipt_rejected",
        "receipt_errors": receipt_errors,
        "run_id": payload.get("run_id") if isinstance(payload, dict) else None,
        "target": payload.get("target") if isinstance(payload, dict) else None,
        "candidate_artifact": None,
    }


def classify_run_result(
    returncode: int,
    stdout: str,
    stderr: str,
    receipt_path: str | Path | None = None,
    *,
    expected_run_id: str | None = None,
) -> dict[str, Any]:
    """Require a valid typed receipt for this run.

    A receipt that is absent, malformed, invalid, or has a mismatched
    ``run_id`` fails closed via ``_fail_closed_receipt_result`` (or the
    explicit absent result). Human stdout is never progress evidence here;
    ``classify_nightly_result`` remains only as a separately callable legacy
    utility in ``hermes_evolution_store``.
    """
    payload = load_receipt(receipt_path)
    if payload is _RECEIPT_UNREADABLE:
        return _fail_closed_receipt_result(REASON_RECEIPT_INVALID, ["receipt_unreadable"], {})
    if payload is not None:
        errors = validate_receipt(payload)
        if not errors and expected_run_id is not None and payload.get("run_id") != expected_run_id:
            return _fail_closed_receipt_result(
                REASON_RECEIPT_RUN_ID_MISMATCH, [f"run_id_mismatch:expected={expected_run_id}"], payload
            )
        if not errors:
            health = classify_receipt(payload)
            if returncode != 0:
                # Non-zero child rc strips every authority/progress flag.
                health["status"] = "ERROR"
                health["job_success"] = False
                health["effective_audit"] = False
                health["candidate_generated"] = False
                health["state_advanced"] = False
                health["promoted"] = False
                health["degraded"] = True
                health["candidate_artifact"] = None
                if REASON_SCRIPT_RETURNCODE_NONZERO not in health["reasons"]:
                    health["reasons"].append(REASON_SCRIPT_RETURNCODE_NONZERO)
            return health
        return _fail_closed_receipt_result(REASON_RECEIPT_INVALID, errors, payload)

    # Missing typed evidence is always closed. Human stdout remains available
    # to explicit legacy callers via classify_nightly_result, but cannot prove
    # no-agent progress.
    return {
        "status": "ERROR",
        "job_success": False,
        "effective_audit": False,
        "candidate_generated": False,
        "state_advanced": False,
        "promoted": False,
        "degraded": True,
        "write_blocked": False,
        "reasons": [REASON_RECEIPT_MISSING],
        "receipt_source": "receipt_absent",
        "receipt_errors": [],
        "run_id": None,
        "target": None,
        "candidate_artifact": None,
    }


# --------------------------------------------------------------------------
# selector state
# --------------------------------------------------------------------------

COOLDOWN_STEPS_HOURS: tuple[int, ...] = (6, 24, 72, 168)
NO_PROGRESS_PENALTY = 40.0
UNKNOWN_AGE_DAYS = 999


def selector_state_path(home: str | Path) -> Path:
    return Path(home).expanduser() / "state" / "dreaming" / "selector_state.json"


def new_selector_state() -> dict[str, Any]:
    return {"schema": SELECTOR_STATE_SCHEMA, "targets": {}, "last_selected": None}


def load_selector_state(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.is_file():
        return new_selector_state()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return new_selector_state()
    if not isinstance(data, dict):
        return new_selector_state()
    data["schema"] = SELECTOR_STATE_SCHEMA
    if not isinstance(data.get("targets"), dict):
        data["targets"] = {}
    data.setdefault("last_selected", None)
    return data


def save_selector_state(path: str | Path, state: dict[str, Any]) -> Path:
    return atomic_write_text(path, json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2))


def target_state(state: dict[str, Any], name: str) -> dict[str, Any]:
    targets = state.setdefault("targets", {})
    return targets.setdefault(
        name,
        {
            "attempts": 0,
            "last_attempt_at": None,
            "last_advanced_at": None,
            "consecutive_no_progress": 0,
            "cooldown_until": None,
            "last_outcome": None,
            "shadow_score": None,
        },
    )


def cooldown_hours(consecutive_no_progress: int) -> int:
    if consecutive_no_progress <= 0:
        return 0
    index = min(consecutive_no_progress, len(COOLDOWN_STEPS_HOURS)) - 1
    return COOLDOWN_STEPS_HOURS[index]


def cooldown_active(entry: dict[str, Any], now: datetime) -> bool:
    until = parse_ts(entry.get("cooldown_until"))
    return bool(until and until > now)


def _age_days(value: str | None, now: datetime) -> int:
    parsed = parse_ts(value)
    if parsed is None:
        return UNKNOWN_AGE_DAYS
    return max(0, int((now - parsed).total_seconds() // 86400))


def rank_targets(candidates: Sequence[dict[str, Any]], state: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
    """Deterministic ranking.

    ``base_priority`` keeps the legacy intent (low score + long neglect
    first), ``penalty`` demotes targets that keep producing no progress, and
    ``shadow_score`` preserves the *old* selector score purely as evidence so
    the two rankings can be compared without letting the old one decide.
    """
    rows: list[dict[str, Any]] = []
    targets = state.get("targets", {})
    for candidate in candidates:
        name = str(candidate.get("name"))
        score = float(candidate.get("score") or 0)
        entry = targets.get(name, {}) if isinstance(targets, dict) else {}
        advance_ref = entry.get("last_advanced_at") or candidate.get("last_audit")
        base = (100.0 - score) + _age_days(advance_ref, now)
        no_progress = int(entry.get("consecutive_no_progress") or 0)
        penalty = NO_PROGRESS_PENALTY * no_progress
        rows.append(
            {
                "name": name,
                "score": score,
                "base_priority": base,
                "penalty": penalty,
                "effective_priority": base - penalty,
                "shadow_score": (100.0 - score) + _age_days(candidate.get("last_audit"), now),
                "attempts": int(entry.get("attempts") or 0),
                "consecutive_no_progress": no_progress,
                "cooling_down": cooldown_active(entry, now),
                "cooldown_until": entry.get("cooldown_until"),
                "last_attempt_at": entry.get("last_attempt_at"),
                "last_advanced_at": entry.get("last_advanced_at"),
                "selected": False,
            }
        )
    rows.sort(key=lambda row: (-row["effective_priority"], row["attempts"], row["name"]))
    return rows


def select_target(
    candidates: Sequence[dict[str, Any]], state: dict[str, Any], now: datetime
) -> tuple[str | None, str, list[dict[str, Any]]]:
    ranking = rank_targets(candidates, state, now)
    if not ranking:
        return None, REASON_NO_TARGETS, ranking
    eligible = [row for row in ranking if not row["cooling_down"]]
    if not eligible:
        return None, REASON_ALL_COOLING_DOWN, ranking
    chosen = eligible[0]
    if len(eligible) > 1 and chosen["name"] == state.get("last_selected"):
        # diversity rule: never pick the same target twice in a row while an
        # alternative is eligible, so a repeated no-change target cannot
        # permanently dominate the loop.
        chosen = eligible[1]
    chosen["selected"] = True
    return chosen["name"], REASON_OK, ranking


def record_attempt(
    state: dict[str, Any],
    name: str,
    outcome: str,
    now: datetime,
    *,
    shadow_score: float | None = None,
) -> dict[str, Any]:
    """Every outcome updates attempt metadata; only ``advanced`` moves progress."""
    if outcome not in OUTCOMES:
        raise ValueError(f"unsupported outcome: {outcome}")
    entry = target_state(state, name)
    entry["attempts"] = int(entry.get("attempts") or 0) + 1
    entry["last_attempt_at"] = format_ts(now)
    entry["last_outcome"] = outcome
    if shadow_score is not None:
        entry["shadow_score"] = shadow_score
    if outcome == OUTCOME_ADVANCED:
        entry["last_advanced_at"] = format_ts(now)
        entry["consecutive_no_progress"] = 0
        entry["cooldown_until"] = None
    else:
        no_progress = int(entry.get("consecutive_no_progress") or 0) + 1
        entry["consecutive_no_progress"] = no_progress
        entry["cooldown_until"] = format_ts(now + timedelta(hours=cooldown_hours(no_progress)))
    state["last_selected"] = name
    return entry


# --------------------------------------------------------------------------
# generator / evaluator shared vocabulary
# --------------------------------------------------------------------------

SECTION_VOCABULARY: dict[str, tuple[str, ...]] = {
    "input": ("input", "输入"),
    "output": ("output", "输出"),
    "constraint": ("constraint", "约束", "边界", "限制"),
    "checkpoint": ("checkpoint", "检查点"),
    "example": ("example", "示例"),
}
SECTION_ORDER: tuple[str, ...] = ("input", "output", "constraint", "checkpoint", "example")

GENERATOR_TEMPLATES: dict[str, str] = {
    "input": "\n\n## 输入\n\n- 用户请求的具体参数\n",
    "output": "\n## 输出\n\n- 执行结果或交付物\n",
    "constraint": "\n## 约束\n\n- 遵循项目规范\n- 在 context budget 内完成\n",
    "checkpoint": "\n## 检查点\n\n- [ ] 输入参数完整\n- [ ] 输出符合预期格式\n",
    "example": "\n## 示例\n\n```text\n请求: <典型请求>\n结果: <期望结果>\n```\n",
}

UNSUPPORTED_FINDINGS: dict[str, str] = {
    "frontmatter": "generator_cannot_author_frontmatter",
}


def has_frontmatter(content: str) -> bool:
    return "---" in content[:50]


def missing_sections(content: str) -> list[str]:
    lowered = content.lower()
    return [key for key in SECTION_ORDER if not any(word in lowered for word in SECTION_VOCABULARY[key])]


def classify_findings(content: str) -> dict[str, Any]:
    """Split findings into what the generator can author and what it cannot.

    Unsupported findings are reported once with an explicit reason instead of
    being retried forever by the nightly loop.
    """
    supported = missing_sections(content)
    unsupported: list[dict[str, str]] = []
    if not has_frontmatter(content):
        unsupported.append({"finding": "frontmatter", "reason": UNSUPPORTED_FINDINGS["frontmatter"]})
    return {"supported": supported, "unsupported": unsupported}


def generate_sections(content: str, findings: Sequence[str]) -> tuple[str, list[str]]:
    applied: list[str] = []
    updated = content
    for key in SECTION_ORDER:
        if key not in findings:
            continue
        template = GENERATOR_TEMPLATES.get(key)
        if template is None:
            continue
        updated += template
        applied.append(key)
    return updated, applied


def evaluate_candidate(candidate_content: str, applied: Sequence[str]) -> dict[str, Any]:
    """The evaluator uses the same vocabulary the generator writes against."""
    still_missing = missing_sections(candidate_content)
    remaining = [key for key in applied if key in still_missing]
    satisfied = not remaining
    return {
        "satisfied": satisfied,
        "remaining": remaining,
        "missing_after": still_missing,
        "reason": REASON_OK if satisfied else REASON_EVALUATION_REJECTED,
    }


# --------------------------------------------------------------------------
# ownership / path preflight guard
# --------------------------------------------------------------------------


def current_euid() -> int:
    """Real ``geteuid()``, isolated so callers can inject a value in tests."""
    geteuid = getattr(os, "geteuid", None)
    return int(geteuid()) if geteuid is not None else 0


def _within(child: Path, parent: Path) -> bool:
    return child == parent or parent in child.parents


def _path_components_from(base: Path, target: Path) -> list[Path]:
    """``base`` plus every intermediate path down to ``target``, inclusive."""
    try:
        rel_parts = target.relative_to(base).parts
    except ValueError:
        return [base, target] if base != target else [base]
    components = [base]
    cur = base
    for part in rel_parts:
        cur = cur / part
        components.append(cur)
    return components


def _find_symlink_component(
    base: Path, target: Path, lstat_fn: Callable[[Path], Any] = os.lstat
) -> Path | None:
    """First symlink among ``base``'s existing descendants down to ``target``.

    Components that do not exist yet are skipped (nothing to check); this is
    used both for an active skill path (which must fully exist) and a
    candidate destination (whose deepest components may not exist yet).
    """
    for component in _path_components_from(base, target):
        try:
            component_lstat = lstat_fn(component)
        except OSError:
            continue
        if stat.S_ISLNK(component_lstat.st_mode):
            return component
    return None


def dreaming_write_boundary_preflight(
    hermes_home: str | Path,
    target_path: str | Path,
    *,
    stat_fn: Callable[[Path], Any] = os.stat,
    lstat_fn: Callable[[Path], Any] = os.lstat,
) -> str | None:
    """Fail-closed write-boundary guard shared by every ``state/dreaming``
    sink: selector state, run receipts, the event log, and the
    EvolutionStore ledger. Returns ``None`` when ``target_path`` is safely
    within a real, non-symlink, same-owner ``hermes_home/state/dreaming``
    tree; otherwise a typed reason. Only stats/lstats -- never writes.
    """
    home = Path(hermes_home)
    dreaming_root = home / "state" / "dreaming"
    target = Path(target_path)

    if ".." in target.parts:
        return REASON_STATE_BOUNDARY_PATH_ESCAPE
    lexical_root = Path(os.path.abspath(str(dreaming_root)))
    lexical_target = Path(os.path.abspath(str(target)))
    if not _within(lexical_target, lexical_root):
        return REASON_STATE_BOUNDARY_PATH_ESCAPE

    # A HERMES_HOME that does not exist yet (first-ever run) has nothing an
    # attacker could have planted; the eventual ``atomic_write_text`` creates
    # it fresh at the correct path. Only an *existing* ancestor can be a
    # symlink or owner-mismatch attack, so absence alone is not fail-closed.
    try:
        home_stat = stat_fn(home)
    except OSError:
        home_stat = None

    if _find_symlink_component(home, target, lstat_fn) is not None:
        return REASON_STATE_BOUNDARY_SYMLINK_ESCAPE

    if home_stat is not None:
        for component in _path_components_from(home, target):
            try:
                component_stat = stat_fn(component)
            except OSError:
                continue
            if component_stat.st_uid != home_stat.st_uid:
                return REASON_OWNERSHIP_TARGET_MISMATCH

    return None


def ownership_preflight(
    hermes_home: str | Path,
    active_target: str | Path,
    *,
    euid: int,
    stat_fn: Callable[[Path], Any] = os.stat,
    lstat_fn: Callable[[Path], Any] = os.lstat,
    access_fn: Callable[[Path, int], bool] = os.access,
) -> StageReceipt:
    """Fail-closed ownership/path guard, run before any candidate write.

    Rejects: EUID 0 against a non-root-owned ``HERMES_HOME``, a
    ``HERMES_HOME`` owner that does not match the invoking (non-root) euid,
    an active target whose owner does not match the home owner, an unreadable
    target, and a target that is a symlink resolving outside
    ``HERMES_HOME/skills``.
    """
    home = Path(hermes_home)
    target = Path(active_target)
    skills_root = home / "skills"

    # Check the caller's lexical spelling before normalization can erase an
    # escape, then independently check the resolved filesystem path below.
    if ".." in target.parts:
        return StageReceipt(
            STAGE_OWNERSHIP, False, REASON_OWNERSHIP_SYMLINK_ESCAPE,
            {"target": str(target), "check": "lexical_dotdot"},
        )
    lexical_home = Path(os.path.abspath(str(home)))
    lexical_skills_root = lexical_home / "skills"
    lexical_target = Path(os.path.abspath(str(target)))
    if not _within(lexical_target, lexical_skills_root):
        return StageReceipt(
            STAGE_OWNERSHIP, False, REASON_OWNERSHIP_SYMLINK_ESCAPE,
            {"target": str(target), "check": "outside_lexical_skills_root"},
        )

    try:
        home_stat = stat_fn(home)
    except OSError:
        return StageReceipt(
            STAGE_OWNERSHIP,
            False,
            REASON_OWNERSHIP_UNREADABLE,
            {"path": str(home), "check": "hermes_home_stat_failed"},
        )

    if euid == 0 and home_stat.st_uid != 0:
        return StageReceipt(
            STAGE_OWNERSHIP,
            False,
            REASON_OWNERSHIP_ROOT_BLOCKED,
            {"hermes_home": str(home), "euid": euid, "home_owner": home_stat.st_uid},
        )

    if euid != 0 and home_stat.st_uid != euid:
        return StageReceipt(
            STAGE_OWNERSHIP,
            False,
            REASON_OWNERSHIP_HOME_MISMATCH,
            {"hermes_home": str(home), "euid": euid, "home_owner": home_stat.st_uid},
        )

    try:
        target_lstat = lstat_fn(target)
    except OSError:
        return StageReceipt(
            STAGE_OWNERSHIP,
            False,
            REASON_OWNERSHIP_UNREADABLE,
            {"target": str(target), "check": "lstat_failed"},
        )

    symlink_component = _find_symlink_component(home, target, lstat_fn)
    if symlink_component is not None:
        return StageReceipt(
            STAGE_OWNERSHIP,
            False,
            REASON_OWNERSHIP_SYMLINK_ESCAPE,
            {"target": str(target), "component": str(symlink_component), "check": "path_component_symlink"},
        )

    if stat.S_ISLNK(target_lstat.st_mode) or not stat.S_ISREG(target_lstat.st_mode):
        return StageReceipt(
            STAGE_OWNERSHIP, False, REASON_OWNERSHIP_SYMLINK_ESCAPE,
            {"target": str(target), "check": "target_not_regular_nonsymlink"},
        )
    try:
        resolved = target.resolve(strict=True)
        resolved_skills_root = skills_root.resolve(strict=True)
    except OSError:
        return StageReceipt(
            STAGE_OWNERSHIP, False, REASON_OWNERSHIP_SYMLINK_ESCAPE,
            {"target": str(target), "check": "resolved_containment_failed"},
        )
    if not _within(resolved, resolved_skills_root):
        return StageReceipt(
            STAGE_OWNERSHIP, False, REASON_OWNERSHIP_SYMLINK_ESCAPE,
            {"target": str(target), "resolved": str(resolved), "skills_root": str(resolved_skills_root)},
        )

    if not access_fn(target, os.R_OK):
        return StageReceipt(
            STAGE_OWNERSHIP,
            False,
            REASON_OWNERSHIP_UNREADABLE,
            {"target": str(target), "check": "not_readable"},
        )

    try:
        target_stat = stat_fn(target)
    except OSError:
        return StageReceipt(
            STAGE_OWNERSHIP,
            False,
            REASON_OWNERSHIP_UNREADABLE,
            {"target": str(target), "check": "stat_failed"},
        )

    if target_stat.st_uid != home_stat.st_uid:
        return StageReceipt(
            STAGE_OWNERSHIP,
            False,
            REASON_OWNERSHIP_TARGET_MISMATCH,
            {"target": str(target), "target_owner": target_stat.st_uid, "home_owner": home_stat.st_uid},
        )

    return StageReceipt(STAGE_OWNERSHIP, True, REASON_OK, {"target": str(target), "euid": euid})


# --------------------------------------------------------------------------
# candidate-only generation
# --------------------------------------------------------------------------


def _is_safe_relative_component(value: str) -> bool:
    if not value or value in {".", ".."}:
        return False
    if value.startswith("/") or value.startswith("~"):
        return False
    return ".." not in Path(value).parts


def candidates_root_path(hermes_home: str | Path) -> Path:
    return Path(hermes_home) / "state" / "dreaming" / "candidates"


def candidates_root_is_provisioned(hermes_home: str | Path) -> bool:
    """True only when the pre-provisioned candidates root already exists safely."""
    root = candidates_root_path(hermes_home)
    try:
        st = os.lstat(root)
    except OSError:
        return False
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        return False
    return True


def _is_safe_artifact_token(value: str) -> bool:
    if not value or not isinstance(value, str):
        return False
    if "/" in value or "\\" in value or "\x00" in value:
        return False
    if value in {".", ".."} or value.startswith(".") or value.endswith("."):
        # Keep tokens free of leading/trailing dots and path segments.
        if value in {".", ".."}:
            return False
    if not _ARTIFACT_SAFE_TOKEN_RE.fullmatch(value):
        return False
    # Reject pure dot-segments after normalization.
    if Path(value).name != value:
        return False
    return True


def build_candidate_artifact_filename(run_id: str, skill_name: str, nonce: str) -> tuple[str | None, str]:
    """Build a single-component flat artifact name or a typed escape reason."""
    if not (
        _is_safe_artifact_token(run_id)
        and _is_safe_artifact_token(skill_name)
        and _is_safe_artifact_token(nonce)
    ):
        return None, REASON_CANDIDATE_DEST_ESCAPE
    name = f"candidate-v2--{run_id}--{skill_name}--{nonce}.json"
    if len(name) > _ARTIFACT_NAME_MAX:
        return None, REASON_CANDIDATE_DEST_ESCAPE
    if name.count("/") or name.count("\\") or "\x00" in name or name != Path(name).name:
        return None, REASON_CANDIDATE_DEST_ESCAPE
    return name, REASON_OK


def resolve_candidate_destination(
    hermes_home: str | Path, run_id: str, skill_name: str, nonce: str = "0"
) -> tuple[Path | None, str]:
    """Lexical artifact path under the candidates root (no filesystem access)."""
    home = Path(hermes_home)
    root = candidates_root_path(home)
    name, reason = build_candidate_artifact_filename(run_id, skill_name, nonce)
    if name is None:
        return None, reason
    candidate = root / name
    resolved = Path(os.path.normpath(str(candidate)))
    root_normalized = Path(os.path.normpath(str(root)))
    if resolved.parent != root_normalized:
        return None, REASON_CANDIDATE_DEST_ESCAPE
    return resolved, REASON_OK


def canonical_candidate_envelope_bytes(
    *,
    run_id: str,
    skill_name: str,
    source_sha256: str,
    candidate_bytes: bytes,
) -> bytes:
    """Canonical compact sorted-key JSON envelope with trailing newline."""
    payload = {
        "candidate_bytes_b64": base64.b64encode(candidate_bytes).decode("ascii"),
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "candidate_size": len(candidate_bytes),
        "run_id": run_id,
        "schema_version": CANDIDATE_ARTIFACT_SCHEMA_VERSION,
        "skill_name": skill_name,
        "source_sha256": source_sha256,
    }
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def validate_candidate_envelope(
    envelope_bytes: bytes,
    *,
    expected_run_id: str,
    expected_skill_name: str,
    expected_source_sha256: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Strict schema + digest coherence validation for a V2 artifact envelope."""
    required = {
        "candidate_bytes_b64",
        "candidate_sha256",
        "candidate_size",
        "run_id",
        "schema_version",
        "skill_name",
        "source_sha256",
    }
    try:
        text = envelope_bytes.decode("utf-8")
        if not text.endswith("\n") or text[:-1].find("\n") != -1:
            return None, REASON_CANDIDATE_ARTIFACT_INVALID
        payload = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    if not isinstance(payload, dict):
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    if set(payload.keys()) != required:
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    if payload.get("schema_version") != CANDIDATE_ARTIFACT_SCHEMA_VERSION:
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    if not isinstance(payload.get("run_id"), str) or payload["run_id"] != expected_run_id:
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    if not isinstance(payload.get("skill_name"), str) or payload["skill_name"] != expected_skill_name:
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    if not isinstance(payload.get("source_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", payload["source_sha256"]):
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    if expected_source_sha256 is not None and payload["source_sha256"] != expected_source_sha256:
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    if not isinstance(payload.get("candidate_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", payload["candidate_sha256"]):
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    if not isinstance(payload.get("candidate_size"), int) or isinstance(payload["candidate_size"], bool):
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    if payload["candidate_size"] < 0:
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    if not isinstance(payload.get("candidate_bytes_b64"), str):
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    try:
        candidate_bytes = base64.b64decode(payload["candidate_bytes_b64"], validate=True)
    except Exception:
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    if len(candidate_bytes) != payload["candidate_size"]:
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    if hashlib.sha256(candidate_bytes).hexdigest() != payload["candidate_sha256"]:
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    try:
        candidate_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    rebuild = canonical_candidate_envelope_bytes(
        run_id=payload["run_id"],
        skill_name=payload["skill_name"],
        source_sha256=payload["source_sha256"],
        candidate_bytes=candidate_bytes,
    )
    if rebuild != envelope_bytes:
        return None, REASON_CANDIDATE_ARTIFACT_INVALID
    out = dict(payload)
    out["candidate_bytes"] = candidate_bytes
    out["envelope_sha256"] = hashlib.sha256(envelope_bytes).hexdigest()
    return out, None


def _identity(value: Any) -> tuple[int, int]:
    return (value.st_dev, value.st_ino)


def _open_dir_at(
    parent_fd: int, name: str, *,
    owner_check: Callable[[int], bool] | None = None,
) -> int:
    """Open an existing directory component only. No mkdir capability."""
    fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
    if owner_check is not None and not owner_check(fd):
        os.close(fd)
        raise OSError(errno.EPERM, "candidate destination ancestor owner mismatch", name)
    return fd


def _open_dir_chain(
    root_fd: int, names: Sequence[str], *,
    owner_check: Callable[[int], bool] | None = None,
) -> int:
    """Open a pre-existing directory chain only; no creation capability."""
    current = os.dup(root_fd)
    try:
        for name in names:
            next_fd = _open_dir_at(current, name, owner_check=owner_check)
            os.close(current)
            current = next_fd
        return current
    except Exception:
        os.close(current)
        raise


def _hash_fd(fd: int) -> str:
    digest = hashlib.sha256()
    os.lseek(fd, 0, os.SEEK_SET)
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
    os.lseek(fd, 0, os.SEEK_SET)
    return digest.hexdigest()


def _write_all_fd(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError(errno.EIO, "short write on candidate artifact fd")
        view = view[written:]


def _read_all_fd(fd: int) -> bytes:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            break
        chunks.append(chunk)
    os.lseek(fd, 0, os.SEEK_SET)
    return b"".join(chunks)


def _classify_candidate_artifact_residual_at(
    parent_fd: int, name: str, owned_identity: tuple[int, int]
) -> str:
    """Classify residual after post-create failure. Never unlinks.

    Under the active same-UID namespace adversary model, ``lstat`` then
    ``unlink`` is not a safe cleanup primitive: a competitor can replace the
    name between the two syscalls. Architecture 2 therefore preserves every
    post-create residual and reports a typed reason only.
    """
    try:
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        # Owned bytes may still exist under another name; absence is residual.
        return REASON_CANDIDATE_RESIDUAL_UNSAFE
    except OSError:
        return REASON_CANDIDATE_RESIDUAL_UNSAFE
    if stat.S_ISLNK(current.st_mode) or not stat.S_ISREG(current.st_mode):
        return REASON_CANDIDATE_RESIDUAL_UNSAFE
    if _identity(current) != owned_identity:
        return REASON_CANDIDATE_RESIDUAL_IDENTITY_MISMATCH
    # Identity matches creation FD — residual is our owned artifact.
    return REASON_CANDIDATE_RESIDUAL_UNSAFE


# Backward-compatible name used by older tests; never unlinks.
def _cleanup_candidate_artifact_at(
    parent_fd: int, name: str, owned_identity: tuple[int, int]
) -> tuple[bool, str | None]:
    """Deprecated alias: observe residual only. Always returns cleaned=False."""
    return False, _classify_candidate_artifact_residual_at(parent_fd, name, owned_identity)


def _tree_has_symlink(root: Path) -> Path | None:
    """First symlink found in ``root`` or anywhere beneath it, else ``None``."""
    if root.is_symlink():
        return root
    for entry in root.rglob("*"):
        if entry.is_symlink():
            return entry
    return None


@dataclass
class CandidateResult:
    stage: StageReceipt
    candidate_artifact: Path | None
    active_hash_before: str | None
    active_hash_after: str | None
    applied_sections: list[str]
    unsupported: list[dict[str, str]]
    candidate_content: str | None = None


# --------------------------------------------------------------------------
# descriptor-bound flat artifact generation (V2)
# --------------------------------------------------------------------------


def generate_candidate(
    hermes_home: str | Path,
    run_id: str,
    skill_name: str,
    *,
    euid: int | None = None,
    artifact_nonce_fn: Callable[[], str] | None = None,
    ancestor_owner_of_fd: Callable[[int], int] = lambda fd: os.fstat(fd).st_uid,
    post_create_hook: Callable[[int, str, int], None] | None = None,
    write_hook: Callable[[int, bytes], None] | None = None,
    fsync_hook: Callable[[int], None] | None = None,
    readback_hook: Callable[[int], bytes] | None = None,
    post_fsync_hook: Callable[[int, str, int], None] | None = None,
) -> CandidateResult:
    """Publish one flat candidate artifact via O_CREAT|O_EXCL|O_NOFOLLOW fd.

    The candidates root must already be provisioned. Loop A never creates
    ``state``/``dreaming``/``candidates`` or per-run/per-skill directories.
    All write/fsync/hash/readback/schema validation use the creation FD only.
    """
    home = Path(hermes_home)
    resolved_euid = current_euid() if euid is None else euid
    active_md = home / "skills" / skill_name / "SKILL.md"
    root_path = candidates_root_path(home)
    nonce_fn = artifact_nonce_fn or (lambda: uuid.uuid4().hex)
    nonce = nonce_fn()
    artifact_name, name_reason = build_candidate_artifact_filename(run_id, skill_name, nonce)
    if artifact_name is None:
        stage = StageReceipt(STAGE_GENERATION, False, name_reason, {"run_id": run_id, "skill": skill_name})
        return CandidateResult(stage, None, None, None, [], [])
    dest = root_path / artifact_name

    if not _is_safe_relative_component(skill_name):
        stage = StageReceipt(STAGE_GENERATION, False, REASON_CANDIDATE_DEST_ESCAPE,
                             {"run_id": run_id, "skill": skill_name})
        return CandidateResult(stage, None, None, None, [], [])

    if not active_md.is_file():
        stage = StageReceipt(STAGE_GENERATION, False, REASON_NO_FINDINGS,
                             {"active_skill_md": str(active_md), "detail": "active_skill_md_missing"})
        return CandidateResult(stage, None, None, None, [], [])

    # SKILL.md-only generation still refuses an active tree with symlinks so
    # evaluator inputs cannot be confused with support-file escape paths.
    active_tree_symlink = _tree_has_symlink(active_md.parent)
    if active_tree_symlink is not None:
        stage = StageReceipt(STAGE_GENERATION, False, REASON_ACTIVE_TREE_SYMLINK,
                             {"active_dir": str(active_md.parent), "symlink": str(active_tree_symlink)})
        return CandidateResult(stage, None, None, None, [], [])

    fds: list[int] = []
    artifact_fd = -1
    root_fd = -1
    artifact_created = False
    artifact_id: tuple[int, int] | None = None
    active_hash: str | None = None
    applied: list[str] = []
    findings: dict[str, Any] = {"unsupported": []}
    envelope_bytes: bytes | None = None

    def keep(fd: int) -> int:
        fds.append(fd)
        return fd

    def empty_result(stage: StageReceipt, *, content: str | None = None,
                     active_after: str | None = None,
                     artifact: Path | None = None) -> CandidateResult:
        return CandidateResult(
            stage, artifact, active_hash, active_after if active_after is not None else active_hash,
            applied, findings.get("unsupported", []), content,
        )

    def fail(reason: str, check: str, *, cleanup: bool = False) -> CandidateResult:
        nonlocal artifact_created
        # Pre-create failures leave zero residue and may keep the original reason.
        cleaned = True
        residual_reason: str | None = None
        residual_identity: dict[str, int] | None = None
        identity_state = "absent"
        if cleanup and artifact_created:
            # Post-create: never unlink, even when creation identity was not captured
            # (e.g. immediate fstat failure after O_CREAT|O_EXCL). Preserve residual
            # and force cleanup_failed / unclassified residual protocol.
            cleaned = False
            if artifact_id is not None:
                identity_state = "captured"
                residual_identity = {"st_dev": artifact_id[0], "st_ino": artifact_id[1]}
                if root_fd >= 0:
                    residual_reason = _classify_candidate_artifact_residual_at(
                        root_fd, artifact_name, artifact_id
                    )
                else:
                    residual_reason = REASON_CANDIDATE_RESIDUAL_UNSAFE
            else:
                identity_state = "unclassified"
                residual_identity = None
                residual_reason = REASON_CANDIDATE_RESIDUAL_UNSAFE
        final_reason = reason if cleaned else REASON_CANDIDATE_CLEANUP_FAILED
        details: dict[str, Any] = {
            "run_id": run_id,
            "skill": skill_name,
            "check": check,
            "original_reason": reason,
            "candidate_cleaned": cleaned,
            "cleanup_failed": not cleaned,
            "candidate_artifact": artifact_name,
        }
        if residual_reason is not None:
            details["residual_reason"] = residual_reason
            details["residuals"] = [{"kind": "candidate_artifact", "reason": residual_reason}]
            details["residual_identity"] = residual_identity
            details["residual_identity_state"] = identity_state
            if residual_identity is not None:
                details["artifact_st_dev"] = residual_identity["st_dev"]
                details["artifact_st_ino"] = residual_identity["st_ino"]
        stage = StageReceipt(STAGE_GENERATION, False, final_reason, details)
        # Residual failures never grant candidate authority projection.
        return empty_result(stage, artifact=None)

    try:
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        home_fd = keep(os.open(home, os.O_RDONLY | os.O_DIRECTORY | nofollow))
        home_owner = ancestor_owner_of_fd(home_fd)
        if home_owner != resolved_euid:
            stage = StageReceipt(
                STAGE_GENERATION, False, REASON_CANDIDATE_DEST_ANCESTOR_OWNER_MISMATCH,
                {"run_id": run_id, "skill": skill_name, "path": "home",
                 "owner": home_owner, "expected_owner": resolved_euid},
            )
            return empty_result(stage)

        def _owner_ok(fd: int) -> bool:
            return ancestor_owner_of_fd(fd) == home_owner

        active_parent_fd = keep(_open_dir_chain(home_fd, ("skills", skill_name)))
        active_fd = keep(os.open("SKILL.md", os.O_RDONLY | nofollow, dir_fd=active_parent_fd))
        active_before = os.fstat(active_fd)
        if not stat.S_ISREG(active_before.st_mode):
            return fail(REASON_NO_FINDINGS, "active_not_regular")
        active_hash = _hash_fd(active_fd)
        active_content = _read_all_fd(active_fd).decode("utf-8")
        findings = classify_findings(active_content)
        if not findings["supported"]:
            reason = REASON_UNSUPPORTED_ONLY if findings["unsupported"] else REASON_NO_FINDINGS
            stage = StageReceipt(
                STAGE_GENERATION, False, reason,
                {"active_skill_md": str(active_md), "active_hash_before": active_hash,
                 "active_hash_after": active_hash, "unsupported": findings["unsupported"]},
            )
            return empty_result(stage, active_after=active_hash)

        # Provisioned root only — never create state/dreaming/candidates.
        try:
            root_fd = keep(_open_dir_chain(
                home_fd, ("state", "dreaming", "candidates"), owner_check=_owner_ok
            ))
        except FileNotFoundError:
            stage = StageReceipt(
                STAGE_GENERATION, False, REASON_CANDIDATE_ROOT_UNPROVISIONED,
                {"run_id": run_id, "skill": skill_name, "candidates_root": str(root_path)},
            )
            return empty_result(stage)
        except OSError as exc:
            if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                return fail(REASON_CANDIDATE_DEST_ESCAPE, f"root_open:{exc.errno}")
            if exc.errno == errno.EPERM:
                return fail(REASON_CANDIDATE_DEST_ANCESTOR_OWNER_MISMATCH, "root_owner")
            return fail(REASON_CANDIDATE_INTERNAL_FAILURE, f"root_open:{exc.errno}")

        updated, applied = generate_sections(active_content, findings["supported"])
        candidate_bytes = updated.encode("utf-8")
        envelope_bytes = canonical_candidate_envelope_bytes(
            run_id=run_id,
            skill_name=skill_name,
            source_sha256=active_hash,
            candidate_bytes=candidate_bytes,
        )
        envelope_sha256 = hashlib.sha256(envelope_bytes).hexdigest()

        flags = os.O_CREAT | os.O_EXCL | os.O_RDWR | nofollow
        try:
            artifact_fd = keep(os.open(artifact_name, flags, 0o600, dir_fd=root_fd))
        except FileExistsError:
            return fail(REASON_CANDIDATE_DEST_CONFLICT, "artifact_name_collision")
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                return fail(REASON_CANDIDATE_DEST_CONFLICT, "artifact_name_collision")
            return fail(REASON_CANDIDATE_INTERNAL_FAILURE, f"openat:{exc.errno}")

        artifact_created = True
        artifact_stat = os.fstat(artifact_fd)
        if not stat.S_ISREG(artifact_stat.st_mode):
            return fail(REASON_CANDIDATE_READBACK_FAILED, "created_not_regular", cleanup=True)
        artifact_id = _identity(artifact_stat)

        if post_create_hook is not None:
            try:
                post_create_hook(artifact_fd, artifact_name, root_fd)
            except Exception:
                return fail(REASON_CANDIDATE_INTERNAL_FAILURE, "post_create_hook", cleanup=True)

        try:
            if write_hook is not None:
                write_hook(artifact_fd, envelope_bytes)
            else:
                _write_all_fd(artifact_fd, envelope_bytes)
            if fsync_hook is not None:
                fsync_hook(artifact_fd)
            else:
                os.fsync(artifact_fd)
        except OSError:
            return fail(REASON_CANDIDATE_INTERNAL_FAILURE, "write_or_fsync", cleanup=True)

        if post_fsync_hook is not None:
            try:
                post_fsync_hook(artifact_fd, artifact_name, root_fd)
            except Exception:
                return fail(REASON_CANDIDATE_INTERNAL_FAILURE, "post_fsync_hook", cleanup=True)

        try:
            if readback_hook is not None:
                read_bytes = readback_hook(artifact_fd)
            else:
                read_bytes = _read_all_fd(artifact_fd)
        except OSError:
            return fail(REASON_CANDIDATE_READBACK_FAILED, "fd_readback", cleanup=True)

        if read_bytes != envelope_bytes:
            return fail(REASON_CANDIDATE_READBACK_FAILED, "fd_readback_mismatch", cleanup=True)

        validated, validate_reason = validate_candidate_envelope(
            read_bytes,
            expected_run_id=run_id,
            expected_skill_name=skill_name,
            expected_source_sha256=active_hash,
        )
        if validate_reason is not None or validated is None:
            return fail(validate_reason or REASON_CANDIDATE_ARTIFACT_INVALID, "schema_validate", cleanup=True)

        # Identity: fstat(fd) vs lstat(name) through held root dirfd.
        try:
            fd_stat = os.fstat(artifact_fd)
            name_stat = os.stat(artifact_name, dir_fd=root_fd, follow_symlinks=False)
        except OSError:
            return fail(REASON_CANDIDATE_READBACK_FAILED, "identity_stat", cleanup=True)
        if (
            not stat.S_ISREG(fd_stat.st_mode)
            or stat.S_ISLNK(name_stat.st_mode)
            or not stat.S_ISREG(name_stat.st_mode)
            or _identity(fd_stat) != _identity(name_stat)
            or _identity(fd_stat) != artifact_id
            or fd_stat.st_uid != home_owner
            or fd_stat.st_size != len(envelope_bytes)
        ):
            return fail(REASON_CANDIDATE_READBACK_FAILED, "identity_mismatch", cleanup=True)

        # Active late-swap gate via fresh non-symlink fds.
        final_fds: list[int] = []
        try:
            fresh_home = os.open(home, os.O_RDONLY | os.O_DIRECTORY | nofollow)
            final_fds.append(fresh_home)
            if _identity(os.fstat(fresh_home)) != _identity(os.fstat(home_fd)):
                raise OSError(errno.ESTALE, "home changed")
            fresh_active_parent = _open_dir_chain(fresh_home, ("skills", skill_name))
            final_fds.append(fresh_active_parent)
            fresh_active = os.open("SKILL.md", os.O_RDONLY | nofollow, dir_fd=fresh_active_parent)
            final_fds.append(fresh_active)
            active_after_stat = os.fstat(fresh_active)
            active_hash_after = _hash_fd(fresh_active)
            if _identity(active_after_stat) != _identity(active_before) or active_hash_after != active_hash:
                raise OSError(errno.ESTALE, "active changed")
            fresh_root = _open_dir_chain(fresh_home, ("state", "dreaming", "candidates"))
            final_fds.append(fresh_root)
            if _identity(os.fstat(fresh_root)) != _identity(os.fstat(root_fd)):
                raise OSError(errno.ESTALE, "root changed")
            # Re-validate from the creation FD one last time (pathname content is not authoritative).
            final_bytes = _read_all_fd(artifact_fd)
            if final_bytes != envelope_bytes:
                raise OSError(errno.ESTALE, "artifact fd changed")
            final_validated, final_reason = validate_candidate_envelope(
                final_bytes,
                expected_run_id=run_id,
                expected_skill_name=skill_name,
                expected_source_sha256=active_hash,
            )
            if final_reason is not None or final_validated is None:
                raise OSError(errno.ESTALE, "artifact invalid at final gate")
            candidate_content = final_validated["candidate_bytes"].decode("utf-8")
            candidate_sha256 = final_validated["candidate_sha256"]
            candidate_size = final_validated["candidate_size"]
        except (OSError, UnicodeDecodeError):
            final_reason = (
                REASON_OWNERSHIP_SYMLINK_ESCAPE
                if active_md.is_symlink()
                else REASON_CANDIDATE_READBACK_FAILED
            )
            return fail(final_reason, "final_identity_gate", cleanup=True)
        finally:
            for fd in reversed(final_fds):
                os.close(fd)

        stage = StageReceipt(
            STAGE_GENERATION,
            True,
            REASON_CANDIDATE_GENERATED,
            {
                "run_id": run_id,
                "skill": skill_name,
                "skill_name": skill_name,
                "candidate_artifact": artifact_name,
                "artifact_schema_version": CANDIDATE_ARTIFACT_SCHEMA_VERSION,
                "artifact_sha256": envelope_sha256,
                "artifact_size": len(envelope_bytes),
                "artifact_st_dev": artifact_id[0],
                "artifact_st_ino": artifact_id[1],
                "source_sha256": active_hash,
                "candidate_sha256": candidate_sha256,
                "candidate_size": candidate_size,
                "active_skill_md": str(active_md),
                "active_hash_before": active_hash,
                "active_hash_after": active_hash_after,
                "applied_sections": applied,
                "unsupported": findings["unsupported"],
            },
        )
        return CandidateResult(
            stage, dest, active_hash, active_hash_after, applied,
            findings["unsupported"], candidate_content,
        )
    except (OSError, UnicodeDecodeError) as exc:
        if isinstance(exc, UnicodeDecodeError):
            reason = REASON_CANDIDATE_INTERNAL_FAILURE
            check = "unicode_decode_error"
        else:
            if exc.errno == errno.EPERM:
                reason = REASON_CANDIDATE_DEST_ANCESTOR_OWNER_MISMATCH
            elif exc.errno in {errno.EEXIST, errno.ENOTEMPTY}:
                reason = REASON_CANDIDATE_DEST_CONFLICT
            elif exc.errno in {errno.ENOENT}:
                reason = REASON_CANDIDATE_ROOT_UNPROVISIONED
            elif exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                reason = REASON_CANDIDATE_DEST_ESCAPE
            elif exc.errno in {errno.ENOTSUP, getattr(errno, "EOPNOTSUPP", errno.ENOTSUP)}:
                reason = REASON_CANDIDATE_PUBLISH_UNSUPPORTED
            else:
                reason = REASON_CANDIDATE_INTERNAL_FAILURE
            check = f"oserror:{exc.errno}"
        return fail(reason, check, cleanup=artifact_created)
    except Exception as exc:
        # Post-create ordinary exceptions (e.g. RuntimeError from write/readback
        # hooks) enter the same never-unlink residual funnel. Do not catch
        # BaseException — KeyboardInterrupt/SystemExit must still propagate.
        # Pre-create ordinary exceptions keep prior escape behavior.
        if not artifact_created:
            raise
        return fail(
            REASON_CANDIDATE_INTERNAL_FAILURE,
            f"post_create_exception:{type(exc).__name__}",
            cleanup=True,
        )
    finally:
        for fd in reversed(fds):
            try:
                os.close(fd)
            except OSError:
                pass



# --------------------------------------------------------------------------
# orchestrated run: selection -> ownership -> generation -> evaluation
# --------------------------------------------------------------------------


def run_dreaming_cycle(
    hermes_home: str | Path,
    candidates: Sequence[dict[str, Any]],
    now: datetime,
    *,
    run_id: str,
    euid: int | None = None,
    state_path: str | Path | None = None,
) -> RunReceipt:
    """Run one Loop A cycle and return a typed, schema-valid receipt.

    Loop A has no promotion gate: ``promoted`` and ``state_advanced`` are
    never set True here regardless of outcome. A candidate that satisfies its
    own evaluator is recorded as ``candidate_generated`` (a real, positive
    outcome) but the selector still treats it as no-progress for cooldown
    purposes, since the active skill never changed — this is what keeps a
    single, easily-fixed target from monopolizing every run.
    """
    home = Path(hermes_home)
    path = Path(state_path) if state_path is not None else selector_state_path(home)
    resolved_euid = current_euid() if euid is None else euid

    receipt = RunReceipt(run_id=run_id, ts=format_ts(now))

    boundary_reason = dreaming_write_boundary_preflight(home, path)
    if boundary_reason is not None:
        receipt.write_blocked = True
        receipt.degraded = True
        receipt.add_reason(boundary_reason)
        receipt.add_stage(StageReceipt(STAGE_RUN, False, boundary_reason, {"selector_state_path": str(path)}))
        return receipt

    # Entire Loop A is fail-closed when the candidates root is unprovisioned:
    # no selector/log/receipt/ledger side effects from this function.
    if not candidates_root_is_provisioned(home):
        receipt.job_success = False
        receipt.write_blocked = True
        receipt.degraded = True
        receipt.add_reason(REASON_CANDIDATE_ROOT_UNPROVISIONED)
        receipt.add_stage(
            StageReceipt(
                STAGE_RUN,
                False,
                REASON_CANDIDATE_ROOT_UNPROVISIONED,
                {"candidates_root": str(candidates_root_path(home))},
            )
        )
        return receipt

    state = load_selector_state(path)

    name, reason, ranking = select_target(candidates, state, now)
    receipt.add_stage(StageReceipt(STAGE_SELECTION, name is not None, reason, {"ranking": ranking}))
    if name is None:
        receipt.add_reason(reason)
        return receipt

    chosen_row = next((row for row in ranking if row["name"] == name), None)
    chosen_shadow_score = chosen_row["shadow_score"] if chosen_row else None

    receipt.target = name
    active_target = home / "skills" / name / "SKILL.md"
    ownership_stage = ownership_preflight(home, active_target, euid=resolved_euid)
    receipt.add_stage(ownership_stage)

    if not ownership_stage.ok:
        receipt.write_blocked = True
        receipt.add_reason(ownership_stage.reason)
        record_attempt(state, name, OUTCOME_REJECTED, now, shadow_score=chosen_shadow_score)
        save_selector_state(path, state)
        return receipt

    result = generate_candidate(home, run_id, name, euid=resolved_euid)
    receipt.add_stage(result.stage)
    receipt.effective_audit = True

    if not result.stage.ok:
        receipt.add_reason(result.stage.reason)
        if result.stage.reason in GENERATION_WRITE_BLOCK_REASONS or result.stage.reason in OWNERSHIP_BLOCK_REASONS:
            receipt.write_blocked = True
            receipt.degraded = True
            if result.stage.reason == REASON_CANDIDATE_CLEANUP_FAILED:
                receipt.job_success = False
            outcome = OUTCOME_REJECTED
        elif result.stage.reason == REASON_UNSUPPORTED_ONLY:
            outcome = OUTCOME_UNSUPPORTED
        else:
            outcome = OUTCOME_NO_CHANGE
        record_attempt(state, name, outcome, now, shadow_score=chosen_shadow_score)
        save_selector_state(path, state)
        return receipt

    receipt.candidate_generated = True
    receipt.add_reason(REASON_CANDIDATE_GENERATED)

    if result.candidate_content is None:
        receipt.job_success = False
        receipt.degraded = True
        receipt.add_reason(REASON_CANDIDATE_READBACK_FAILED)
        receipt.add_stage(StageReceipt(
            STAGE_EVALUATION, False, REASON_CANDIDATE_READBACK_FAILED,
            {"check": "digest_bound_candidate_content_missing"},
        ))
        record_attempt(state, name, OUTCOME_REJECTED, now, shadow_score=chosen_shadow_score)
        save_selector_state(path, state)
        return receipt
    evaluation = evaluate_candidate(result.candidate_content, result.applied_sections)
    receipt.add_stage(StageReceipt(STAGE_EVALUATION, evaluation["satisfied"], evaluation["reason"], evaluation))

    if evaluation["satisfied"]:
        outcome = OUTCOME_NO_CHANGE
    else:
        receipt.add_reason(REASON_EVALUATION_REJECTED)
        outcome = OUTCOME_REJECTED

    record_attempt(state, name, outcome, now, shadow_score=chosen_shadow_score)
    save_selector_state(path, state)
    return receipt
