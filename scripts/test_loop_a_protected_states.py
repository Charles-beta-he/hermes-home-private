from __future__ import annotations

import pytest
from loop_a_protected.states import INSTALLER_PATHS, SERVICE_EDGES, StateTransitionError, require_installer_transition, require_service_transition


def test_service_accepts_every_frozen_graph_edge():
    for source, targets in SERVICE_EDGES.items():
        for target in targets: require_service_transition(source, target)


@pytest.mark.parametrize("source,target", [("CANDIDATE_WRITTEN", "ABORTED"), ("RECOVERY_REQUIRED", "COMMITTED"), ("COMMITTED", "PREPARED")])
def test_service_rejects_forbidden_or_post_terminal_edges(source, target):
    with pytest.raises(StateTransitionError): require_service_transition(source, target)


def test_each_installer_operation_accepts_only_its_exact_forward_path():
    for (operation, destination), path in INSTALLER_PATHS.items():
        for source, target in zip(path, path[1:]): require_installer_transition(operation, destination, source, target)


def test_install_initial_rejects_mixed_or_skipped_kind_steps():
    with pytest.raises(StateTransitionError): require_installer_transition("install-initial", "protected-bundle", "RUNTIME_TREE_BUILT", "RUNTIME_POINTER_STAGED")
    with pytest.raises(StateTransitionError): require_installer_transition("install-initial", "protected-bundle", "SKILL_TREE_BUILT", "SKILL_POINTER_STAGED")


def test_recovery_required_can_only_roll_back_and_never_commit():
    require_installer_transition("promote-runtime", "runtime", "RECOVERY_REQUIRED", "ROLLED_BACK")
    with pytest.raises(StateTransitionError): require_installer_transition("promote-runtime", "runtime", "RECOVERY_REQUIRED", "VERIFIED")


def test_operation_destination_pairs_are_exact():
    with pytest.raises(StateTransitionError): require_installer_transition("promote-runtime", "active-skills", "START", "PREPARED")
