from __future__ import annotations

import pytest

from loop_a_protected.installer_reconciler import InstallerReconciliationError, reconcile_installer_state

BASE = {
    "namespace": "exact", "authorization": "exact", "prior_effects": "exact",
    "current_effect": "absent", "future_effects": "absent", "smoke": "absent",
    "closure_converges": False, "locks_held": True, "fence_held": True,
}


def observed(**changes):
    return dict(BASE, **changes)


def test_pre_consumption_can_abort_or_close_the_consumption_checkpoint_gap_only_under_both_gates():
    no_auth = observed(authorization="absent")
    assert reconcile_installer_state("promote-runtime", "runtime", "PREPARED", no_auth) == ("APPEND_ABORTED",)
    assert reconcile_installer_state("promote-runtime", "runtime", "PREPARED", observed()) == (
        "APPEND_AUTH_CONSUMED", "CONTINUE_FORWARD",
    )
    for gate_change in ({"locks_held": False}, {"fence_held": False}):
        assert reconcile_installer_state(
            "promote-runtime", "runtime", "PREPARED", observed(**gate_change)
        ) == ("HUMAN_RECOVERY",)
        assert reconcile_installer_state(
            "promote-runtime", "runtime", "PREPARED", observed(authorization="absent", **gate_change)
        ) == ("HUMAN_RECOVERY",)


@pytest.mark.parametrize("operation,destination,state", [
    ("install-initial", "protected-bundle", "RUNTIME_TREE_STAGED"),
    ("promote-runtime", "runtime", "RUNTIME_POINTER_STAGED"),
    ("promote-skill", "active-skills", "SKILL_POINTER_STAGED"),
    ("update-floor", "rollback-floor", "FLOOR_STAGED"),
])
def test_exact_staged_effect_rolls_back_only_under_both_locks_and_fence(operation, destination, state):
    result = reconcile_installer_state(operation, destination, state, observed(current_effect="staged-exact"))
    assert result == ("REMOVE_EXACT_STAGED_EFFECT", "ROLL_BACK_PRIOR_EFFECTS_REVERSE_ORDER",
                      "FSYNC_EACH_PARENT", "APPEND_RECOVERY_REQUIRED", "APPEND_ROLLED_BACK")
    assert reconcile_installer_state(operation, destination, state,
                                     observed(current_effect="staged-exact", fence_held=False)) == ("HUMAN_RECOVERY",)


@pytest.mark.parametrize("operation,destination,state", [
    ("install-initial", "protected-bundle", "RUNTIME_TREE_BUILT"),
    ("install-initial", "protected-bundle", "SKILL_POINTER_SWITCHED"),
    ("promote-runtime", "runtime", "RUNTIME_POINTER_SWITCHED"),
    ("promote-skill", "active-skills", "SKILL_TREE_BUILT"),
    ("update-floor", "rollback-floor", "FLOOR_SWITCHED"),
])
def test_exact_completed_effect_continues_only_along_operation_path(operation, destination, state):
    assert reconcile_installer_state(operation, destination, state, observed(current_effect="final-exact")) == (
        "CONTINUE_FORWARD",
    )


def test_initial_mixed_two_kind_closure_never_converges():
    result = reconcile_installer_state(
        "install-initial", "protected-bundle", "SKILL_TREE_BUILT",
        observed(prior_effects="other", current_effect="final-exact"),
    )
    assert result == ("APPEND_RECOVERY_REQUIRED",)


def test_smoke_gate_accepts_only_exact_committed_smoke_and_stays_fenced_otherwise():
    exact = observed(current_effect="final-exact", smoke="exact-committed")
    assert reconcile_installer_state("install-initial", "protected-bundle", "SMOKE_GATE_PUBLISHED", exact) == (
        "APPEND_SMOKE_ACCEPTED", "CONTINUE_FORWARD",
    )
    for smoke in ("absent", "other"):
        assert reconcile_installer_state(
            "install-initial", "protected-bundle", "SMOKE_GATE_PUBLISHED",
            observed(current_effect="final-exact", smoke=smoke),
        ) == ("APPEND_RECOVERY_REQUIRED",)


def test_smoke_accepted_and_verified_require_exact_terminal_closure():
    converged = observed(current_effect="final-exact", smoke="exact-committed", closure_converges=True)
    assert reconcile_installer_state("install-initial", "protected-bundle", "SMOKE_ACCEPTED", converged) == (
        "INSTALL_FINAL_PLIST", "CLEAR_SMOKE_GATE", "ROTATE_VERIFY_EPOCH", "APPEND_VERIFIED",
    )
    assert reconcile_installer_state("install-initial", "protected-bundle", "VERIFIED", converged) == (
        "APPEND_COMMITTED",
    )
    assert reconcile_installer_state(
        "install-initial", "protected-bundle", "VERIFIED", observed(current_effect="final-exact")
    ) == ("APPEND_RECOVERY_REQUIRED",)


def test_terminal_state_requires_state_specific_exact_authorization_effect_and_closure():
    committed = observed(current_effect="final-exact", closure_converges=True)
    assert reconcile_installer_state("promote-runtime", "runtime", "COMMITTED", committed) == ("NO_ACTION",)
    for anomaly in (
        {"authorization": "absent"},
        {"current_effect": "absent"},
        {"closure_converges": False},
        {"smoke": "exact-committed"},
        {"namespace": "other"},
    ):
        assert reconcile_installer_state(
            "promote-runtime", "runtime", "COMMITTED", observed(**dict(committed, **anomaly))
        ) == ("HUMAN_RECOVERY",)

    initial_committed = observed(
        current_effect="final-exact", smoke="exact-committed", closure_converges=True
    )
    assert reconcile_installer_state(
        "install-initial", "protected-bundle", "COMMITTED", initial_committed
    ) == ("NO_ACTION",)
    assert reconcile_installer_state(
        "install-initial", "protected-bundle", "COMMITTED",
        observed(current_effect="final-exact", closure_converges=True),
    ) == ("HUMAN_RECOVERY",)

    assert reconcile_installer_state(
        "promote-runtime", "runtime", "ABORTED",
        observed(authorization="absent", closure_converges=True),
    ) == ("NO_ACTION",)
    assert reconcile_installer_state(
        "promote-runtime", "runtime", "ROLLED_BACK", observed(closure_converges=True)
    ) == ("NO_ACTION",)


def test_terminal_anomaly_and_unknown_observation_fail_closed_without_cleanup():
    assert reconcile_installer_state("promote-runtime", "runtime", "COMMITTED", observed()) == (
        "HUMAN_RECOVERY",
    )
    assert reconcile_installer_state(
        "promote-runtime", "runtime", "COMMITTED", observed(namespace="other")
    ) == ("HUMAN_RECOVERY",)
    with pytest.raises(InstallerReconciliationError):
        reconcile_installer_state("promote-runtime", "runtime", "PREPARED", dict(BASE, surprise=True))
    with pytest.raises(InstallerReconciliationError):
        reconcile_installer_state("promote-runtime", "runtime", "SKILL_TREE_BUILT", observed())
