#!/usr/bin/env python3
"""Pure stdlib SQLite durable outbox for actionable taskpool events.

This module owns queue durability and fencing only.  It does not wake or run
workers, invoke subprocesses, contact a network, or mutate task lifecycle state.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import sqlite3
import stat
import time
from typing import Any, Dict, Optional, Tuple, Union
import uuid


SCHEMA_VERSION = 1
ALLOWED_EVENT_TYPES = frozenset({"taskpool.actionable.v1"})
JSONScalar = Union[None, bool, int, float, str]
JSONValue = Union[JSONScalar, list, dict]


class OutboxError(Exception):
    """Base class for deterministic outbox errors."""


class ValidationError(OutboxError, ValueError):
    """Input is outside the strict outbox contract."""


class ConflictError(OutboxError):
    """An idempotency key already names different semantics."""


class StaleClaimError(OutboxError):
    """A claim is absent, expired, displaced, or otherwise fenced."""


class PathSecurityError(OutboxError):
    """The configured database path is not the exact safe local path."""


def _strict_nonempty_string(value: Any, field: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValidationError(f"{field} must be a non-empty trimmed string")
    return value


def _strict_time(value: Any, field: str, *, positive: bool = False) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValidationError(f"{field} must be a finite number (not bool)")
    number = float(value)
    if number < 0 or (positive and number <= 0):
        comparator = "positive" if positive else "non-negative"
        raise ValidationError(f"{field} must be {comparator}")
    return number


def _strict_positive_int(value: Any, field: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValidationError(f"{field} must be a positive integer (not bool)")
    return value


def _validate_json(value: Any, path: str = "$") -> None:
    value_type = type(value)
    if value is None or value_type in (str, bool, int):
        return
    if value_type is float:
        if not math.isfinite(value):
            raise ValidationError(f"{path} must contain only finite numbers")
        return
    if value_type is list:
        for index, item in enumerate(value):
            _validate_json(item, f"{path}[{index}]")
        return
    if value_type is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValidationError(f"{path} object keys must be exact strings")
            _validate_json(item, f"{path}.{key}")
        return
    raise ValidationError(f"{path} contains a non-JSON value")


def _canonical_json(value: Any) -> str:
    _validate_json(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _receipt_sha256(
    *, receipt_id: str, event_id: str, generation: int,
    outcome: str, detail_json: str, created_at: float,
) -> str:
    material = _canonical_json(
        {
            "receipt_id": receipt_id,
            "event_id": event_id,
            "generation": generation,
            "outcome": outcome,
            "detail_json": detail_json,
            "created_at": created_at,
        }
    )
    return _sha256_text(material)


class DurableTaskpoolEventOutbox:
    """Durable queue with replay identity and lease-generation fencing."""

    def __init__(self, db_path: Union[str, os.PathLike], *, allowed_root: Union[str, os.PathLike]):
        self._root = Path(allowed_root).expanduser().absolute()
        self._db_path = Path(db_path).expanduser().absolute()
        self._root_real: Optional[Path] = None
        self._db_identity: Optional[Tuple[int, int]] = None
        self._store_id: Optional[str] = None
        self._prepare_path()
        self._store_id = self._initialize_schema()
        self._capture_db_identity()

    def _walk_below_root_reject_symlinks(self, path: Path) -> None:
        try:
            relative = path.relative_to(self._root)
        except ValueError as exc:
            raise PathSecurityError("path escapes allowed_root") from exc
        current = self._root
        for component in relative.parts:
            current = current / component
            try:
                mode = os.lstat(str(current)).st_mode
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(mode):
                raise PathSecurityError(f"symlink path component rejected: {current}")

    def _prepare_path(self) -> None:
        try:
            root_mode = os.lstat(str(self._root)).st_mode
        except FileNotFoundError as exc:
            raise PathSecurityError("allowed_root must be an existing directory") from exc
        if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
            raise PathSecurityError("allowed_root must be an existing directory")
        self._root_real = self._root.resolve(strict=True)
        try:
            common = os.path.commonpath((str(self._root), str(self._db_path)))
        except ValueError as exc:
            raise PathSecurityError("database path escapes allowed_root") from exc
        if common != str(self._root) or self._db_path == self._root:
            raise PathSecurityError("database path escapes allowed_root")
        self._walk_below_root_reject_symlinks(self._db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._walk_below_root_reject_symlinks(self._db_path.parent)
        expected_parent = self._root_real / self._db_path.parent.relative_to(self._root)
        if self._db_path.parent.resolve(strict=True) != expected_parent:
            raise PathSecurityError("database parent must be canonical below allowed_root")
        if self._db_path.exists():
            mode = os.lstat(str(self._db_path)).st_mode
            if not stat.S_ISREG(mode):
                raise PathSecurityError("database must be a regular file")

    def _capture_db_identity(self) -> None:
        info = os.lstat(str(self._db_path))
        if not stat.S_ISREG(info.st_mode):
            raise PathSecurityError("database must be a regular file")
        self._db_identity = (info.st_dev, info.st_ino)

    def _verify_path(self) -> None:
        self._walk_below_root_reject_symlinks(self._db_path)
        try:
            info = os.lstat(str(self._db_path))
        except FileNotFoundError as exc:
            raise PathSecurityError("database path disappeared") from exc
        if not stat.S_ISREG(info.st_mode):
            raise PathSecurityError("database path is not a regular file")
        if self._db_identity is not None and (info.st_dev, info.st_ino) != self._db_identity:
            raise PathSecurityError("database path identity changed")
        expected_parent = self._root_real / self._db_path.parent.relative_to(self._root)
        if self._db_path.parent.resolve(strict=True) != expected_parent:
            raise PathSecurityError("database parent is no longer canonical")

    def _connect(self, *, readonly: bool = False) -> sqlite3.Connection:
        self._verify_path()
        if readonly:
            uri = self._db_path.as_uri() + "?mode=ro"
            connection = sqlite3.connect(uri, uri=True, timeout=5.0)
            connection.execute("PRAGMA query_only = ON")
        else:
            connection = sqlite3.connect(str(self._db_path), timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            self._verify_path()
            store_row = connection.execute(
                "SELECT value FROM outbox_metadata WHERE key='store_id'"
            ).fetchone()
            if store_row is None or store_row[0] != self._store_id:
                raise PathSecurityError("connected database identity changed")
            return connection
        except Exception:
            connection.close()
            raise

    def _initialize_schema(self) -> str:
        # sqlite3 creates only this exact, already-validated path.
        connection = sqlite3.connect(str(self._db_path), timeout=5.0)
        try:
            connection.execute("PRAGMA journal_mode = DELETE")
            connection.execute("PRAGMA synchronous = FULL")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            if version == 0 and tables:
                raise OutboxError("incompatible unversioned schema")
            if version not in (0, SCHEMA_VERSION):
                raise OutboxError(f"unsupported schema version: {version}")
            if version == SCHEMA_VERSION:
                self._validate_schema(connection, self._allowed_schema_extension_sets())
                return self._read_store_id(connection)
            connection.executescript(
                """
                CREATE TABLE outbox_events (
                    schema_version INTEGER NOT NULL,
                    event_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('pending','claimed','completed','failed')),
                    claim_token_sha256 TEXT,
                    generation INTEGER NOT NULL DEFAULT 0 CHECK(generation >= 0),
                    lease_deadline REAL,
                    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
                    completion_receipt_id TEXT,
                    updated_at REAL NOT NULL,
                    completed_at REAL
                );
                CREATE TABLE attempt_receipts (
                    receipt_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL REFERENCES outbox_events(event_id),
                    generation INTEGER NOT NULL CHECK(generation > 0),
                    outcome TEXT NOT NULL CHECK(outcome IN (
                        'expired','completed','retryable_failure',
                        'attempts_exhausted','permanent_failure'
                    )),
                    detail_json TEXT NOT NULL,
                    detail_sha256 TEXT NOT NULL,
                    receipt_sha256 TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    UNIQUE(event_id, generation)
                );
                CREATE TABLE outbox_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE INDEX outbox_claimable
                    ON outbox_events(status, created_at, event_id);
                PRAGMA user_version = 1;
                """
            )
            store_id = str(uuid.uuid4())
            connection.execute(
                "INSERT INTO outbox_metadata(key,value) VALUES('store_id',?)",
                (store_id,),
            )
            connection.commit()
            self._validate_schema(connection, self._allowed_schema_extension_sets())
            return store_id
        finally:
            connection.close()

    def _allowed_schema_extension_sets(self) -> tuple[frozenset[tuple], ...]:
        """Exact optional schema object sets accepted by a trusted subclass."""
        return ()

    @staticmethod
    def _read_store_id(connection: sqlite3.Connection) -> str:
        row = connection.execute(
            "SELECT value FROM outbox_metadata WHERE key='store_id'"
        ).fetchone()
        if row is None or type(row[0]) is not str or not row[0]:
            raise OutboxError("incompatible schema: missing store identity")
        return row[0]

    @staticmethod
    def _validate_schema(
        connection: sqlite3.Connection,
        allowed_extension_sets: tuple[frozenset[tuple], ...] = (),
    ) -> None:
        expected_sql = {
            "outbox_events": """CREATE TABLE outbox_events (
                schema_version INTEGER NOT NULL, event_id TEXT PRIMARY KEY,
                idempotency_key TEXT NOT NULL UNIQUE, event_type TEXT NOT NULL,
                task_id TEXT NOT NULL, payload_json TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL, created_at REAL NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending','claimed','completed','failed')),
                claim_token_sha256 TEXT,
                generation INTEGER NOT NULL DEFAULT 0 CHECK(generation >= 0),
                lease_deadline REAL,
                attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
                completion_receipt_id TEXT, updated_at REAL NOT NULL, completed_at REAL
            )""",
            "attempt_receipts": """CREATE TABLE attempt_receipts (
                receipt_id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL REFERENCES outbox_events(event_id),
                generation INTEGER NOT NULL CHECK(generation > 0),
                outcome TEXT NOT NULL CHECK(outcome IN (
                    'expired','completed','retryable_failure',
                    'attempts_exhausted','permanent_failure'
                )),
                detail_json TEXT NOT NULL, detail_sha256 TEXT NOT NULL,
                receipt_sha256 TEXT NOT NULL,
                created_at REAL NOT NULL, UNIQUE(event_id, generation)
            )""",
            "outbox_metadata": """CREATE TABLE outbox_metadata (
                key TEXT PRIMARY KEY, value TEXT NOT NULL
            )""",
            "outbox_claimable": """CREATE INDEX outbox_claimable
                ON outbox_events(status, created_at, event_id)""",
        }
        normalize_sql = lambda value: None if value is None else " ".join(value.split())
        expected_objects = {
            ("table", "outbox_events", "outbox_events", normalize_sql(expected_sql["outbox_events"])),
            ("table", "attempt_receipts", "attempt_receipts", normalize_sql(expected_sql["attempt_receipts"])),
            ("table", "outbox_metadata", "outbox_metadata", normalize_sql(expected_sql["outbox_metadata"])),
            ("index", "outbox_claimable", "outbox_events", normalize_sql(expected_sql["outbox_claimable"])),
            ("index", "sqlite_autoindex_outbox_events_1", "outbox_events", None),
            ("index", "sqlite_autoindex_outbox_events_2", "outbox_events", None),
            ("index", "sqlite_autoindex_attempt_receipts_1", "attempt_receipts", None),
            ("index", "sqlite_autoindex_attempt_receipts_2", "attempt_receipts", None),
            ("index", "sqlite_autoindex_outbox_metadata_1", "outbox_metadata", None),
        }
        actual_objects = {
            (row[0], row[1], row[2], normalize_sql(row[3]))
            for row in connection.execute(
                "SELECT type,name,tbl_name,sql FROM sqlite_master"
            )
        }
        valid_object_sets = {frozenset(expected_objects)}
        valid_object_sets.update(
            frozenset(expected_objects | set(extension_objects))
            for extension_objects in allowed_extension_sets
        )
        if frozenset(actual_objects) not in valid_object_sets:
            raise OutboxError("incompatible schema object inventory")
        for name, expected in expected_sql.items():
            row = connection.execute(
                "SELECT sql FROM sqlite_master WHERE name=?", (name,)
            ).fetchone()
            actual_sql = "" if row is None or row[0] is None else " ".join(row[0].split())
            if actual_sql != " ".join(expected.split()):
                raise OutboxError(f"incompatible schema definition for {name}")

    @staticmethod
    def _event_dict(row: sqlite3.Row) -> Dict[str, Any]:
        try:
            payload = json.loads(row["payload_json"])
            canonical_payload = _canonical_json(payload)
        except (json.JSONDecodeError, ValidationError, TypeError) as exc:
            raise OutboxError("event payload integrity failure") from exc
        if (
            canonical_payload != row["payload_json"]
            or _sha256_text(row["payload_json"]) != row["payload_sha256"]
        ):
            raise OutboxError("event payload integrity failure")
        return {
            "schema_version": row["schema_version"],
            "event_id": row["event_id"],
            "idempotency_key": row["idempotency_key"],
            "event_type": row["event_type"],
            "task_id": row["task_id"],
            "payload": payload,
            "payload_sha256": row["payload_sha256"],
            "created_at": row["created_at"],
            "status": row["status"],
            "generation": row["generation"],
            "lease_deadline": row["lease_deadline"],
            "attempt_count": row["attempt_count"],
            "completion_receipt_id": row["completion_receipt_id"],
            "updated_at": row["updated_at"],
            "completed_at": row["completed_at"],
        }

    def enqueue(
        self,
        *,
        idempotency_key: str,
        event_type: str,
        task_id: str,
        payload: JSONValue,
        now: Optional[float] = None,
    ) -> Dict[str, Any]:
        idempotency_key = _strict_nonempty_string(idempotency_key, "idempotency_key")
        event_type = _strict_nonempty_string(event_type, "event_type")
        task_id = _strict_nonempty_string(task_id, "task_id")
        payload_json = _canonical_json(payload)
        payload_sha256 = _sha256_text(payload_json)
        timestamp = time.time() if now is None else _strict_time(now, "now")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM outbox_events WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing is not None:
                semantics = (event_type, task_id, payload_sha256)
                stored = (
                    existing["event_type"],
                    existing["task_id"],
                    existing["payload_sha256"],
                )
                if semantics != stored:
                    raise ConflictError("idempotency key conflicts with stored event semantics")
                validated = self._validated_event_dict(connection, existing)
                connection.commit()
                return validated
            if event_type not in ALLOWED_EVENT_TYPES:
                raise ValidationError("event_type is not an actionable outbox event")
            event_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO outbox_events (
                    schema_version,event_id,idempotency_key,event_type,task_id,
                    payload_json,payload_sha256,created_at,status,updated_at
                ) VALUES (?,?,?,?,?,?,?,?,'pending',?)
                """,
                (
                    SCHEMA_VERSION,
                    event_id,
                    idempotency_key,
                    event_type,
                    task_id,
                    payload_json,
                    payload_sha256,
                    timestamp,
                    timestamp,
                ),
            )
            row = connection.execute(
                "SELECT * FROM outbox_events WHERE event_id = ?", (event_id,)
            ).fetchone()
            connection.commit()
            return self._event_dict(row)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def claim(
        self, *, lease_seconds: Union[int, float], now: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        lease = _strict_time(lease_seconds, "lease_seconds", positive=True)
        timestamp = time.time() if now is None else _strict_time(now, "now")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT * FROM outbox_events
                WHERE status = 'pending'
                   OR (status = 'claimed' AND lease_deadline <= ?)
                ORDER BY created_at, event_id
                LIMIT 1
                """,
                (timestamp,),
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            if row["status"] == "claimed":
                self._insert_receipt(
                    connection,
                    row=row,
                    outcome="expired",
                    detail_json=_canonical_json({"lease_deadline": row["lease_deadline"]}),
                    timestamp=timestamp,
                )
            token = secrets.token_urlsafe(32)
            token_sha256 = _sha256_text(token)
            generation = row["generation"] + 1
            attempt_count = row["attempt_count"] + 1
            deadline = timestamp + lease
            updated = connection.execute(
                """
                UPDATE outbox_events
                SET status='claimed', claim_token_sha256=?, generation=?,
                    lease_deadline=?, attempt_count=?, updated_at=?
                WHERE event_id=? AND generation=? AND status=?
                """,
                (
                    token_sha256,
                    generation,
                    deadline,
                    attempt_count,
                    timestamp,
                    row["event_id"],
                    row["generation"],
                    row["status"],
                ),
            )
            if updated.rowcount != 1:
                raise StaleClaimError("claim candidate changed during serialization")
            claimed = connection.execute(
                "SELECT * FROM outbox_events WHERE event_id=?", (row["event_id"],)
            ).fetchone()
            connection.commit()
            result = self._event_dict(claimed)
            result["claim_token"] = token
            return result
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _insert_receipt(
        connection: sqlite3.Connection,
        *,
        row: sqlite3.Row,
        outcome: str,
        detail_json: str,
        timestamp: float,
        receipt_id: Optional[str] = None,
    ) -> str:
        identity = receipt_id or str(uuid.uuid4())
        receipt_sha256 = _receipt_sha256(
            receipt_id=identity,
            event_id=row["event_id"],
            generation=row["generation"],
            outcome=outcome,
            detail_json=detail_json,
            created_at=timestamp,
        )
        connection.execute(
            """
            INSERT INTO attempt_receipts (
                receipt_id,event_id,generation,outcome,detail_json,detail_sha256,
                receipt_sha256,created_at
            ) VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                identity,
                row["event_id"],
                row["generation"],
                outcome,
                detail_json,
                _sha256_text(detail_json),
                receipt_sha256,
                timestamp,
            ),
        )
        return identity

    @staticmethod
    def _receipt_detail(row: sqlite3.Row) -> JSONValue:
        try:
            detail = json.loads(row["detail_json"])
            canonical_detail = _canonical_json(detail)
        except (json.JSONDecodeError, ValidationError, TypeError) as exc:
            raise OutboxError("receipt integrity failure") from exc
        expected_receipt_sha256 = _receipt_sha256(
            receipt_id=row["receipt_id"],
            event_id=row["event_id"],
            generation=row["generation"],
            outcome=row["outcome"],
            detail_json=row["detail_json"],
            created_at=row["created_at"],
        )
        if (
            canonical_detail != row["detail_json"]
            or _sha256_text(row["detail_json"]) != row["detail_sha256"]
            or expected_receipt_sha256 != row["receipt_sha256"]
        ):
            raise OutboxError("receipt integrity failure")
        return detail

    @staticmethod
    def _assert_completion_receipt(
        event: sqlite3.Row, receipt: Optional[sqlite3.Row]
    ) -> None:
        if (
            receipt is None
            or event["status"] != "completed"
            or event["completion_receipt_id"] != receipt["receipt_id"]
            or event["event_id"] != receipt["event_id"]
            or event["generation"] != receipt["generation"]
            or receipt["outcome"] != "completed"
        ):
            raise OutboxError("completion receipt integrity failure")

    def _validated_event_dict(
        self, connection: sqlite3.Connection, event: sqlite3.Row
    ) -> Dict[str, Any]:
        if event["status"] == "completed":
            receipt = connection.execute(
                "SELECT * FROM attempt_receipts WHERE receipt_id=?",
                (event["completion_receipt_id"],),
            ).fetchone()
            self._assert_completion_receipt(event, receipt)
            assert receipt is not None
            self._receipt_detail(receipt)
        return self._event_dict(event)

    @staticmethod
    def _assert_live_claim(
        row: Optional[sqlite3.Row],
        *,
        claim_token: str,
        generation: int,
        timestamp: float,
    ) -> None:
        if (
            row is None
            or row["status"] != "claimed"
            or row["generation"] != generation
            or row["claim_token_sha256"] != _sha256_text(claim_token)
            or row["lease_deadline"] <= timestamp
        ):
            raise StaleClaimError("claim is stale or fenced")

    def renew(
        self,
        *,
        event_id: str,
        claim_token: str,
        generation: int,
        lease_seconds: Union[int, float],
        now: Optional[float] = None,
    ) -> Dict[str, Any]:
        event_id = _strict_nonempty_string(event_id, "event_id")
        claim_token = _strict_nonempty_string(claim_token, "claim_token")
        generation = _strict_positive_int(generation, "generation")
        lease = _strict_time(lease_seconds, "lease_seconds", positive=True)
        timestamp = time.time() if now is None else _strict_time(now, "now")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM outbox_events WHERE event_id=?", (event_id,)
            ).fetchone()
            self._assert_live_claim(
                row,
                claim_token=claim_token,
                generation=generation,
                timestamp=timestamp,
            )
            deadline = timestamp + lease
            updated = connection.execute(
                """
                UPDATE outbox_events
                SET lease_deadline=?, updated_at=?
                WHERE event_id=? AND status='claimed' AND generation=?
                  AND claim_token_sha256=?
                """,
                (deadline, timestamp, event_id, generation, _sha256_text(claim_token)),
            )
            if updated.rowcount != 1:
                raise StaleClaimError("claim changed while renewing")
            renewed = connection.execute(
                "SELECT * FROM outbox_events WHERE event_id=?", (event_id,)
            ).fetchone()
            connection.commit()
            return self._event_dict(renewed)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def complete(
        self,
        *,
        event_id: str,
        claim_token: str,
        generation: int,
        result: JSONValue,
        now: Optional[float] = None,
    ) -> Dict[str, Any]:
        event_id = _strict_nonempty_string(event_id, "event_id")
        claim_token = _strict_nonempty_string(claim_token, "claim_token")
        generation = _strict_positive_int(generation, "generation")
        result_json = _canonical_json(result)
        timestamp = time.time() if now is None else _strict_time(now, "now")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM outbox_events WHERE event_id=?", (event_id,)
            ).fetchone()
            if row is not None and row["status"] == "completed":
                validated = self._validated_event_dict(connection, row)
                receipt = connection.execute(
                    "SELECT * FROM attempt_receipts WHERE receipt_id=?",
                    (row["completion_receipt_id"],),
                ).fetchone()
                self._assert_completion_receipt(row, receipt)
                assert receipt is not None
                self._receipt_detail(receipt)
                if (
                    row["generation"] == generation
                    and row["claim_token_sha256"] == _sha256_text(claim_token)
                    and receipt["detail_json"] == result_json
                ):
                    connection.commit()
                    return validated
                raise StaleClaimError("completed event replay does not match immutable receipt")
            self._assert_live_claim(
                row,
                claim_token=claim_token,
                generation=generation,
                timestamp=timestamp,
            )
            receipt_id = self._insert_receipt(
                connection,
                row=row,
                outcome="completed",
                detail_json=result_json,
                timestamp=timestamp,
            )
            connection.execute(
                """
                UPDATE outbox_events
                SET status='completed', lease_deadline=NULL,
                    completion_receipt_id=?, completed_at=?, updated_at=?
                WHERE event_id=?
                """,
                (receipt_id, timestamp, timestamp, event_id),
            )
            completed = connection.execute(
                "SELECT * FROM outbox_events WHERE event_id=?", (event_id,)
            ).fetchone()
            validated = self._validated_event_dict(connection, completed)
            connection.commit()
            return validated
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def fail(
        self,
        *,
        event_id: str,
        claim_token: str,
        generation: int,
        error: JSONValue,
        retryable: bool,
        max_attempts: int,
        now: Optional[float] = None,
    ) -> Dict[str, Any]:
        event_id = _strict_nonempty_string(event_id, "event_id")
        claim_token = _strict_nonempty_string(claim_token, "claim_token")
        generation = _strict_positive_int(generation, "generation")
        if type(retryable) is not bool:
            raise ValidationError("retryable must be an exact bool")
        max_attempts = _strict_positive_int(max_attempts, "max_attempts")
        error_json = _canonical_json(error)
        timestamp = time.time() if now is None else _strict_time(now, "now")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM outbox_events WHERE event_id=?", (event_id,)
            ).fetchone()
            self._assert_live_claim(
                row,
                claim_token=claim_token,
                generation=generation,
                timestamp=timestamp,
            )
            if retryable and row["attempt_count"] < max_attempts:
                outcome, next_status = "retryable_failure", "pending"
            elif retryable:
                outcome, next_status = "attempts_exhausted", "failed"
            else:
                outcome, next_status = "permanent_failure", "failed"
            self._insert_receipt(
                connection,
                row=row,
                outcome=outcome,
                detail_json=error_json,
                timestamp=timestamp,
            )
            connection.execute(
                """
                UPDATE outbox_events
                SET status=?, claim_token_sha256=NULL, lease_deadline=NULL, updated_at=?
                WHERE event_id=?
                """,
                (next_status, timestamp, event_id),
            )
            updated = connection.execute(
                "SELECT * FROM outbox_events WHERE event_id=?", (event_id,)
            ).fetchone()
            connection.commit()
            return self._event_dict(updated)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def status(self) -> Dict[str, Any]:
        """Return a redacted projection through a query-only connection."""
        connection = self._connect(readonly=True)
        try:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version != SCHEMA_VERSION:
                raise OutboxError(f"unsupported schema version: {version}")
            event_rows = connection.execute(
                "SELECT * FROM outbox_events ORDER BY created_at,event_id"
            ).fetchall()
            receipt_rows = connection.execute(
                """
                SELECT receipt_id,event_id,generation,outcome,detail_json,
                       detail_sha256,receipt_sha256,created_at
                FROM attempt_receipts
                ORDER BY created_at,event_id,generation
                """
            ).fetchall()
            counts = {
                row["status"]: row["count"]
                for row in connection.execute(
                    "SELECT status,COUNT(*) AS count FROM outbox_events GROUP BY status"
                )
            }
            receipt_projections = []
            receipts_by_id = {}
            for row in receipt_rows:
                detail = self._receipt_detail(row)
                receipts_by_id[row["receipt_id"]] = row
                receipt_projections.append(
                    {
                        "receipt_id": row["receipt_id"],
                        "event_id": row["event_id"],
                        "generation": row["generation"],
                        "outcome": row["outcome"],
                        "detail": detail,
                        "detail_sha256": row["detail_sha256"],
                        "created_at": row["created_at"],
                    }
                )
            for event_row in event_rows:
                if event_row["status"] == "completed":
                    self._assert_completion_receipt(
                        event_row,
                        receipts_by_id.get(event_row["completion_receipt_id"]),
                    )
            return {
                "schema_version": version,
                "counts": counts,
                "events": [self._event_dict(row) for row in event_rows],
                "attempt_receipts": receipt_projections,
            }
        finally:
            connection.close()


__all__ = [
    "ALLOWED_EVENT_TYPES",
    "SCHEMA_VERSION",
    "ConflictError",
    "DurableTaskpoolEventOutbox",
    "OutboxError",
    "PathSecurityError",
    "StaleClaimError",
    "ValidationError",
]
