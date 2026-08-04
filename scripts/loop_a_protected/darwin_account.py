from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


ACCOUNT_NAME = "_hermesloopa"
GROUP_NAME = "_hermesloopa"
DISABLED_SHELL = "/usr/bin/false"
EMPTY_HOME = "/var/empty"
DISABLED_AUTHORITY = ";DisabledUser;"
DSCL = "/usr/bin/dscl"

_USER_FIELDS = {
    "name",
    "uid",
    "primary_gid",
    "shell",
    "home",
    "hidden",
    "authentication_authority",
}
_GROUP_FIELDS = {"name", "gid", "members"}
_READBACK_FIELDS = {"user", "group", "supplementary_groups"}


class DarwinAccountError(ValueError):
    """The requested or observed Darwin service-account contract is invalid."""


def _authorized_id(value: Any, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value <= 0
        or value > 2_147_483_647
    ):
        raise DarwinAccountError(f"{label} must be an explicitly authorized non-root integer")
    return value


def build_account_provisioning_plan(
    *, authorized_uid: int, authorized_gid: int
) -> tuple[tuple[str, ...], ...]:
    """Return the complete idempotent ``dscl`` argv plan; never execute it.

    UID and GID are deliberately required keyword arguments.  The caller that
    owns host-mutation authority must choose them; this pure module neither
    discovers an available identity nor invokes a process.
    """

    uid = str(_authorized_id(authorized_uid, "authorized_uid"))
    gid = str(_authorized_id(authorized_gid, "authorized_gid"))
    group = f"/Groups/{GROUP_NAME}"
    user = f"/Users/{ACCOUNT_NAME}"
    return (
        (DSCL, ".", "-create", group),
        (DSCL, ".", "-create", group, "PrimaryGroupID", gid),
        (DSCL, ".", "-create", group, "RealName", "Hermes Loop A"),
        (DSCL, ".", "-create", user),
        (DSCL, ".", "-create", user, "UniqueID", uid),
        (DSCL, ".", "-create", user, "PrimaryGroupID", gid),
        (DSCL, ".", "-create", user, "UserShell", DISABLED_SHELL),
        (DSCL, ".", "-create", user, "NFSHomeDirectory", EMPTY_HOME),
        (DSCL, ".", "-create", user, "IsHidden", "1"),
        (DSCL, ".", "-create", user, "AuthenticationAuthority", DISABLED_AUTHORITY),
    )


def _exact_mapping(value: Any, fields: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise DarwinAccountError(f"{label} fields are not exact")
    return value


def _exact_string_sequence(value: Any, expected: tuple[str, ...], label: str) -> None:
    if (
        isinstance(value, (str, bytes, bytearray))
        or not isinstance(value, Sequence)
        or tuple(value) != expected
        or any(not isinstance(item, str) for item in value)
    ):
        raise DarwinAccountError(f"{label} is not exact")


def validate_account_readback(
    readback: Mapping[str, Any], *, authorized_uid: int, authorized_gid: int
) -> None:
    """Fail closed unless normalized host readback is the exact account contract.

    ``readback`` is data produced by an outer, separately authorized adapter.
    This validator intentionally performs no host lookup and no mutation.
    """

    uid = _authorized_id(authorized_uid, "authorized_uid")
    gid = _authorized_id(authorized_gid, "authorized_gid")
    outer = _exact_mapping(readback, _READBACK_FIELDS, "account readback")
    user = _exact_mapping(outer["user"], _USER_FIELDS, "user readback")
    group = _exact_mapping(outer["group"], _GROUP_FIELDS, "group readback")

    expected_user = {
        "name": ACCOUNT_NAME,
        "uid": uid,
        "primary_gid": gid,
        "shell": DISABLED_SHELL,
        "home": EMPTY_HOME,
        "hidden": True,
    }
    for field, expected in expected_user.items():
        actual = user[field]
        if type(actual) is not type(expected) or actual != expected:
            raise DarwinAccountError(f"user {field} is not exact")

    _exact_string_sequence(
        user["authentication_authority"], (DISABLED_AUTHORITY,), "authentication authority"
    )

    expected_group = {"name": GROUP_NAME, "gid": gid}
    for field, expected in expected_group.items():
        actual = group[field]
        if type(actual) is not type(expected) or actual != expected:
            raise DarwinAccountError(f"group {field} is not exact")

    _exact_string_sequence(group["members"], (), "primary group member list")
    _exact_string_sequence(outer["supplementary_groups"], (), "supplementary groups")
