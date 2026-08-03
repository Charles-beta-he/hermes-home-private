from __future__ import annotations

from copy import deepcopy

import pytest

from loop_a_protected.policy import (
    PolicyError,
    finalize_initial_target_bundle,
    finalize_rollback_floor,
    target_is_permitted,
    validate_floor_history,
    validate_floor_update,
)

D0 = "0" * 64
D1 = "1" * 64
D2 = "2" * 64
D3 = "3" * 64
LINEAGE = "123e4567-e89b-42d3-a456-426614174000"
AUTH = "auth-1"
NOW = "2026-08-03T01:02:03Z"


def tuple_for(kind, sequence, manifest, inventory):
    return {"kind": kind, "release_lineage": LINEAGE, "release_sequence": sequence,
            "manifest_digest": manifest, "inventory_digest": inventory}


def entry(kind, sequence, manifest, inventory, disposition="forward"):
    return {"kind": kind, "release_sequence": sequence, "manifest_digest": manifest,
            "inventory_digest": inventory, "disposition": disposition}


def test_initial_target_bundle_binds_exact_runtime_and_skill_tuples():
    runtime = tuple_for("runtime", 1, D0, D1)
    skills = tuple_for("active-skills", 1, D2, D3)
    bundle = finalize_initial_target_bundle(runtime, skills)
    assert bundle["runtime"] == runtime
    assert bundle["active_skills"] == skills
    assert bundle["bundle_digest"] != D0


@pytest.mark.parametrize("mutator", [
    lambda runtime, skills: (dict(runtime, kind="active-skills"), skills),
    lambda runtime, skills: (runtime, dict(skills, release_lineage="223e4567-e89b-42d3-a456-426614174000")),
])
def test_initial_target_bundle_rejects_kind_or_lineage_substitution(mutator):
    runtime, skills = mutator(tuple_for("runtime", 1, D0, D1), tuple_for("active-skills", 1, D2, D3))
    with pytest.raises(PolicyError):
        finalize_initial_target_bundle(runtime, skills)


def floor(generation=1, minimum=1, entries=None, prior=None):
    if entries is None:
        entries = [
            {"kind": "active-skills", "release_sequence": 1, "manifest_digest": D2,
             "inventory_digest": D3, "disposition": "forward"},
            {"kind": "runtime", "release_sequence": 1, "manifest_digest": D0,
             "inventory_digest": D1, "disposition": "forward"},
        ]
    return finalize_rollback_floor(generation, LINEAGE, minimum, entries, NOW, prior, AUTH)


def test_floor_is_self_digested_and_exact_tuple_authorizes_target():
    value = floor()
    assert target_is_permitted(value, LINEAGE, "runtime", 1, D0, D1)
    assert not target_is_permitted(value, LINEAGE, "runtime", 1, D1, D0)
    assert not target_is_permitted(value, "223e4567-e89b-42d3-a456-426614174000", "runtime", 1, D0, D1)


def test_floor_history_rejects_remove_then_rebind_across_nonadjacent_generations():
    original = entry("runtime", 1, D0, D1)
    replacement = entry("runtime", 1, D1, D0)
    generation_1 = finalize_rollback_floor(1, LINEAGE, 1, [original], NOW, None, AUTH)
    generation_2 = finalize_rollback_floor(2, LINEAGE, 2, [], NOW, generation_1["record_digest"], AUTH)
    generation_3 = finalize_rollback_floor(3, LINEAGE, 2, [replacement], NOW, generation_2["record_digest"], AUTH)
    validate_floor_update(generation_1, generation_2)
    validate_floor_update(generation_2, generation_3)
    with pytest.raises(PolicyError, match="historical sequence rebinding"):
        validate_floor_history([generation_1, generation_2, generation_3])


def test_floor_rejects_noncanonical_entry_order():
    entries = list(reversed(floor()["permitted_versions"]))
    with pytest.raises(PolicyError, match="order"):
        finalize_rollback_floor(1, LINEAGE, 1, entries, NOW, None, AUTH)


def test_floor_rejects_duplicate_kind_sequence_even_if_digests_differ():
    entries = [
        {"kind": "runtime", "release_sequence": 1, "manifest_digest": D0, "inventory_digest": D1, "disposition": "forward"},
        {"kind": "runtime", "release_sequence": 1, "manifest_digest": D2, "inventory_digest": D3, "disposition": "rollback"},
    ]
    with pytest.raises(PolicyError, match="duplicate"):
        finalize_rollback_floor(1, LINEAGE, 1, entries, NOW, None, AUTH)


def test_floor_update_requires_generation_increment_and_prior_digest_binding():
    prior = floor()
    proposed = floor(2, 1, prior=prior["record_digest"])
    validate_floor_update(prior, proposed)
    bad = finalize_rollback_floor(3, LINEAGE, 1, proposed["permitted_versions"], NOW, prior["record_digest"], AUTH)
    with pytest.raises(PolicyError, match="generation"):
        validate_floor_update(prior, bad)


def test_floor_update_cannot_lower_minimum_or_rebind_existing_sequence():
    prior = floor()
    lower = finalize_rollback_floor(2, LINEAGE, 0, prior["permitted_versions"], NOW, prior["record_digest"], AUTH)
    with pytest.raises(PolicyError, match="minimum"):
        validate_floor_update(prior, lower)
    rebound_entries = deepcopy(prior["permitted_versions"])
    rebound_entries[1]["manifest_digest"] = D2
    rebound = finalize_rollback_floor(2, LINEAGE, 1, rebound_entries, NOW, prior["record_digest"], AUTH)
    with pytest.raises(PolicyError, match="rebound"):
        validate_floor_update(prior, rebound)
