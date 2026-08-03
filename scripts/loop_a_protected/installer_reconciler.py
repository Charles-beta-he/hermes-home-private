from __future__ import annotations

from typing import Any, Dict, Tuple

from .states import INSTALLER_PATHS


class InstallerReconciliationError(ValueError):
    pass


_FIELDS = {
    "namespace", "authorization", "prior_effects", "current_effect", "future_effects", "smoke",
    "closure_converges", "locks_held", "fence_held",
}
_ENUMS = {
    "namespace": {"exact", "other"},
    "authorization": {"absent", "exact", "other"},
    "prior_effects": {"exact", "other"},
    "current_effect": {"absent", "staged-exact", "final-exact", "other"},
    "future_effects": {"absent", "other"},
    "smoke": {"absent", "exact-committed", "other"},
}
_TERMINAL = {"COMMITTED", "ABORTED", "ROLLED_BACK"}


def _validate_observation(value: Dict[str, Any]) -> None:
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise InstallerReconciliationError("installer observation fields differ from exact schema")
    for field, allowed in _ENUMS.items():
        if value[field] not in allowed:
            raise InstallerReconciliationError(f"unknown installer observation value for {field}")
    for field in ("closure_converges", "locks_held", "fence_held"):
        if not isinstance(value[field], bool):
            raise InstallerReconciliationError(f"{field} must be boolean")


def _fenced_mismatch() -> Tuple[str, ...]:
    return ("APPEND_RECOVERY_REQUIRED",)


def reconcile_installer_state(operation: str, destination: str, state: str,
                              observation: Dict[str, Any]) -> Tuple[str, ...]:
    _validate_observation(observation)
    path = INSTALLER_PATHS.get((operation, destination))
    if path is None:
        raise InstallerReconciliationError("invalid installer operation/destination pair")
    if state not in set(path) | _TERMINAL | {"RECOVERY_REQUIRED"}:
        raise InstallerReconciliationError("state is not valid for installer operation path")

    if state in _TERMINAL:
        common_exact = (
            observation["namespace"] == "exact"
            and observation["prior_effects"] == "exact"
            and observation["future_effects"] == "absent"
            and observation["closure_converges"]
        )
        if state == "COMMITTED":
            expected_smoke = "exact-committed" if operation == "install-initial" else "absent"
            exact = (
                common_exact
                and observation["authorization"] == "exact"
                and observation["current_effect"] == "final-exact"
                and observation["smoke"] == expected_smoke
            )
        elif state == "ABORTED":
            exact = (
                common_exact
                and observation["authorization"] == "absent"
                and observation["current_effect"] == "absent"
                and observation["smoke"] == "absent"
            )
        else:  # ROLLED_BACK
            exact = (
                common_exact
                and observation["authorization"] == "exact"
                and observation["current_effect"] == "absent"
                and observation["smoke"] == "absent"
            )
        return ("NO_ACTION",) if exact else ("HUMAN_RECOVERY",)
    if state == "RECOVERY_REQUIRED":
        return ("HUMAN_RECOVERY",)

    if observation["namespace"] != "exact" or observation["authorization"] == "other":
        return ("HUMAN_RECOVERY",)
    if not observation["locks_held"] or not observation["fence_held"]:
        return ("HUMAN_RECOVERY",)

    if state == "PREPARED":
        clean = (observation["prior_effects"] == "exact" and observation["current_effect"] == "absent" and
                 observation["future_effects"] == "absent" and observation["smoke"] == "absent")
        if not clean:
            return ("HUMAN_RECOVERY",)
        if observation["authorization"] == "absent":
            return ("APPEND_ABORTED",)
        return ("APPEND_AUTH_CONSUMED", "CONTINUE_FORWARD")

    if observation["authorization"] != "exact":
        return ("HUMAN_RECOVERY",)
    if observation["prior_effects"] != "exact" or observation["future_effects"] != "absent":
        return _fenced_mismatch()

    if state == "AUTH_CONSUMED":
        if observation["current_effect"] == "absent" and observation["smoke"] == "absent":
            return ("CONTINUE_FORWARD",)
        return _fenced_mismatch()

    if state.endswith("_STAGED"):
        if observation["current_effect"] == "staged-exact" and observation["smoke"] == "absent":
            return ("REMOVE_EXACT_STAGED_EFFECT", "ROLL_BACK_PRIOR_EFFECTS_REVERSE_ORDER",
                    "FSYNC_EACH_PARENT", "APPEND_RECOVERY_REQUIRED", "APPEND_ROLLED_BACK")
        return _fenced_mismatch()

    if state == "SMOKE_GATE_PUBLISHED":
        if observation["current_effect"] != "final-exact":
            return _fenced_mismatch()
        if observation["smoke"] == "exact-committed":
            return ("APPEND_SMOKE_ACCEPTED", "CONTINUE_FORWARD")
        return _fenced_mismatch()

    if state == "SMOKE_ACCEPTED":
        if (observation["current_effect"] == "final-exact" and observation["smoke"] == "exact-committed" and
                observation["closure_converges"]):
            return ("INSTALL_FINAL_PLIST", "CLEAR_SMOKE_GATE", "ROTATE_VERIFY_EPOCH", "APPEND_VERIFIED")
        return _fenced_mismatch()

    if state == "VERIFIED":
        smoke_ok = operation != "install-initial" or observation["smoke"] == "exact-committed"
        if observation["current_effect"] == "final-exact" and observation["closure_converges"] and smoke_ok:
            return ("APPEND_COMMITTED",)
        return _fenced_mismatch()

    if state.endswith("_BUILT") or state.endswith("_SWITCHED"):
        if observation["current_effect"] == "final-exact" and observation["smoke"] == "absent":
            return ("CONTINUE_FORWARD",)
        return _fenced_mismatch()

    raise InstallerReconciliationError("unhandled installer state")
