from __future__ import annotations

import inspect

import pytest

from loop_a_protected.darwin_account import (
    DarwinAccountError,
    build_account_provisioning_plan,
    validate_account_readback,
)


UID = 399
GID = 399


def exact_readback() -> dict[str, object]:
    return {
        "user": {
            "name": "_hermesloopa",
            "uid": UID,
            "primary_gid": GID,
            "shell": "/usr/bin/false",
            "home": "/var/empty",
            "hidden": True,
            "authentication_authority": [";DisabledUser;"],
        },
        "group": {"name": "_hermesloopa", "gid": GID, "members": []},
        "supplementary_groups": [],
    }


def test_plan_is_exact_idempotent_dscl_argv_without_shell_or_secret():
    assert build_account_provisioning_plan(authorized_uid=UID, authorized_gid=GID) == (
        ("/usr/bin/dscl", ".", "-create", "/Groups/_hermesloopa"),
        ("/usr/bin/dscl", ".", "-create", "/Groups/_hermesloopa", "PrimaryGroupID", "399"),
        ("/usr/bin/dscl", ".", "-create", "/Groups/_hermesloopa", "RealName", "Hermes Loop A"),
        ("/usr/bin/dscl", ".", "-create", "/Users/_hermesloopa"),
        ("/usr/bin/dscl", ".", "-create", "/Users/_hermesloopa", "UniqueID", "399"),
        ("/usr/bin/dscl", ".", "-create", "/Users/_hermesloopa", "PrimaryGroupID", "399"),
        ("/usr/bin/dscl", ".", "-create", "/Users/_hermesloopa", "UserShell", "/usr/bin/false"),
        ("/usr/bin/dscl", ".", "-create", "/Users/_hermesloopa", "NFSHomeDirectory", "/var/empty"),
        ("/usr/bin/dscl", ".", "-create", "/Users/_hermesloopa", "IsHidden", "1"),
        ("/usr/bin/dscl", ".", "-create", "/Users/_hermesloopa", "AuthenticationAuthority", ";DisabledUser;"),
    )
    source = inspect.getsource(__import__("loop_a_protected.darwin_account", fromlist=["*"]))
    assert "subprocess" not in source
    assert "shell=True" not in source
    assert "Password" not in source


@pytest.mark.parametrize(
    "uid,gid",
    [(0, GID), (UID, 0), (-1, GID), (UID, -1), (True, GID), (UID, False), ("399", GID)],
)
def test_plan_requires_explicit_non_root_numeric_authority(uid, gid):
    with pytest.raises(DarwinAccountError, match="authorized"):
        build_account_provisioning_plan(authorized_uid=uid, authorized_gid=gid)


def test_readback_accepts_only_exact_account_and_group_contract():
    assert validate_account_readback(
        exact_readback(), authorized_uid=UID, authorized_gid=GID
    ) is None


@pytest.mark.parametrize(
    "path,bad_value",
    [
        (("user", "name"), "hermesloopa"),
        (("user", "uid"), UID + 1),
        (("user", "primary_gid"), GID + 1),
        (("user", "shell"), "/bin/bash"),
        (("user", "home"), "/Users/_hermesloopa"),
        (("user", "hidden"), False),
        (("user", "authentication_authority"), []),
        (("group", "name"), "staff"),
        (("group", "gid"), GID + 1),
        (("group", "members"), ["_hermesloopa"]),
        (("supplementary_groups",), ["staff"]),
    ],
)
def test_readback_fails_closed_on_identity_login_or_group_drift(path, bad_value):
    value = exact_readback()
    target = value
    for component in path[:-1]:
        target = target[component]  # type: ignore[index,assignment]
    target[path[-1]] = bad_value  # type: ignore[index]
    with pytest.raises(DarwinAccountError):
        validate_account_readback(value, authorized_uid=UID, authorized_gid=GID)


def test_readback_rejects_extra_fields_and_mutable_or_ambiguous_types():
    extra = exact_readback()
    extra["password"] = "not-a-secret"
    with pytest.raises(DarwinAccountError, match="fields"):
        validate_account_readback(extra, authorized_uid=UID, authorized_gid=GID)

    ambiguous = exact_readback()
    ambiguous["user"]["hidden"] = 1  # type: ignore[index]
    with pytest.raises(DarwinAccountError):
        validate_account_readback(ambiguous, authorized_uid=UID, authorized_gid=GID)
