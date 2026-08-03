from __future__ import annotations

from typing import Dict, FrozenSet, List, Tuple


class StateTransitionError(ValueError):
    pass


SERVICE_EDGES: Dict[str, FrozenSet[str]] = {
    "START": frozenset({"PREPARED"}),
    "PREPARED": frozenset({"SOURCE_CAPTURED", "ABORTED", "RECOVERY_REQUIRED"}),
    "SOURCE_CAPTURED": frozenset({"SMOKE_STARTED", "ABORTED", "RECOVERY_REQUIRED"}),
    "SMOKE_STARTED": frozenset({"CANDIDATE_STAGED", "ABORTED", "RECOVERY_REQUIRED"}),
    "CANDIDATE_STAGED": frozenset({"CANDIDATE_WRITTEN", "ABORTED", "RECOVERY_REQUIRED"}),
    "CANDIDATE_WRITTEN": frozenset({"RECEIPT_WRITTEN", "RECOVERY_REQUIRED"}),
    "RECEIPT_WRITTEN": frozenset({"VERIFIED", "ABORTED", "RECOVERY_REQUIRED"}),
    "VERIFIED": frozenset({"COMMITTED", "RECOVERY_REQUIRED"}),
    "RECOVERY_REQUIRED": frozenset({"ROLLED_BACK"}),
    "COMMITTED": frozenset(), "ABORTED": frozenset(), "ROLLED_BACK": frozenset(),
}

INSTALLER_PATHS: Dict[Tuple[str, str], List[str]] = {
    ("install-initial", "protected-bundle"): ["START", "PREPARED", "AUTH_CONSUMED", "RUNTIME_TREE_STAGED", "RUNTIME_TREE_BUILT", "SKILL_TREE_STAGED", "SKILL_TREE_BUILT", "RUNTIME_POINTER_STAGED", "RUNTIME_POINTER_SWITCHED", "SKILL_POINTER_STAGED", "SKILL_POINTER_SWITCHED", "FLOOR_STAGED", "FLOOR_SWITCHED", "SMOKE_GATE_PUBLISHED", "SMOKE_ACCEPTED", "VERIFIED", "COMMITTED"],
    ("promote-runtime", "runtime"): ["START", "PREPARED", "AUTH_CONSUMED", "RUNTIME_TREE_STAGED", "RUNTIME_TREE_BUILT", "RUNTIME_POINTER_STAGED", "RUNTIME_POINTER_SWITCHED", "VERIFIED", "COMMITTED"],
    ("promote-skill", "active-skills"): ["START", "PREPARED", "AUTH_CONSUMED", "SKILL_TREE_STAGED", "SKILL_TREE_BUILT", "SKILL_POINTER_STAGED", "SKILL_POINTER_SWITCHED", "VERIFIED", "COMMITTED"],
    ("rollback-protected", "runtime"): ["START", "PREPARED", "AUTH_CONSUMED", "RUNTIME_POINTER_STAGED", "RUNTIME_POINTER_SWITCHED", "VERIFIED", "COMMITTED"],
    ("rollback-protected", "active-skills"): ["START", "PREPARED", "AUTH_CONSUMED", "SKILL_POINTER_STAGED", "SKILL_POINTER_SWITCHED", "VERIFIED", "COMMITTED"],
    ("update-floor", "rollback-floor"): ["START", "PREPARED", "AUTH_CONSUMED", "FLOOR_STAGED", "FLOOR_SWITCHED", "VERIFIED", "COMMITTED"],
}
_RECOVERABLE = frozenset({state for path in INSTALLER_PATHS.values() for state in path[2:-1]})


def require_service_transition(source: str, target: str) -> None:
    if target not in SERVICE_EDGES.get(source, frozenset()):
        raise StateTransitionError(f"forbidden service transition: {source} -> {target}")


def require_installer_transition(operation: str, destination: str, source: str, target: str) -> None:
    path = INSTALLER_PATHS.get((operation, destination))
    if path is None:
        raise StateTransitionError("invalid operation/destination pair")
    allowed = any(a == source and b == target for a, b in zip(path, path[1:]))
    allowed |= source == "PREPARED" and target == "ABORTED"
    allowed |= source in _RECOVERABLE and target == "RECOVERY_REQUIRED"
    allowed |= source == "RECOVERY_REQUIRED" and target == "ROLLED_BACK"
    if not allowed:
        raise StateTransitionError(f"forbidden installer transition: {source} -> {target}")
