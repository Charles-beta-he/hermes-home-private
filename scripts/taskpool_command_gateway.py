#!/usr/bin/env python3
"""Local canonical task command gateway candidate.

The gateway owns deterministic admission only: canonical task state, projection
intent, command receipt, and the actionable outbox row commit in one SQLite
transaction. It does not publish projections, wake workers, execute tasks, or
perform external effects.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
from typing import Any, Callable, Mapping, Union
import uuid

from taskpool_event_outbox import (
    ALLOWED_EVENT_TYPES,
    ConflictError,
    DurableTaskpoolEventOutbox,
    ValidationError,
    _canonical_json,
    _sha256_text,
)


COMMAND_SCHEMA = "taskpool.command.v1"
COMMAND_KEYS = frozenset(
    {
        "schema",
        "idempotency_key",
        "operation",
        "task_id",
        "expected_revision",
        "state",
        "projection",
        "event",
    }
)


def _normalized_sql(value: str) -> str:
    return " ".join(value.split())


_GATEWAY_EXTENSION_OBJECTS = frozenset(
    {
        (
            "table",
            "canonical_tasks",
            "canonical_tasks",
            _normalized_sql(
                """CREATE TABLE canonical_tasks (
                    task_id TEXT PRIMARY KEY,
                    revision INTEGER NOT NULL CHECK(revision > 0),
                    state_json TEXT NOT NULL,
                    state_sha256 TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )"""
            ),
        ),
        (
            "table",
            "projection_intents",
            "projection_intents",
            _normalized_sql(
                """CREATE TABLE projection_intents (
                    task_id TEXT NOT NULL REFERENCES canonical_tasks(task_id),
                    revision INTEGER NOT NULL CHECK(revision > 0),
                    relative_path TEXT NOT NULL,
                    canonical_sha256 TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('pending','published','failed')),
                    projection_sha256 TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    PRIMARY KEY(task_id, revision)
                )"""
            ),
        ),
        (
            "table",
            "command_receipts",
            "command_receipts",
            _normalized_sql(
                """CREATE TABLE command_receipts (
                    idempotency_key TEXT PRIMARY KEY,
                    command_sha256 TEXT NOT NULL,
                    task_id TEXT NOT NULL REFERENCES canonical_tasks(task_id),
                    revision INTEGER NOT NULL CHECK(revision > 0),
                    event_id TEXT NOT NULL REFERENCES outbox_events(event_id),
                    result_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                )"""
            ),
        ),
        (
            "table",
            "gateway_work_epoch",
            "gateway_work_epoch",
            _normalized_sql(
                """CREATE TABLE gateway_work_epoch (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    epoch INTEGER NOT NULL CHECK(epoch >= 0)
                )"""
            ),
        ),
        (
            "table",
            "command_drain_tokens",
            "command_drain_tokens",
            _normalized_sql(
                """CREATE TABLE command_drain_tokens (
                    idempotency_key TEXT PRIMARY KEY REFERENCES command_receipts(idempotency_key),
                    task_id TEXT NOT NULL REFERENCES canonical_tasks(task_id),
                    revision INTEGER NOT NULL CHECK(revision > 0),
                    event_id TEXT NOT NULL REFERENCES outbox_events(event_id),
                    work_epoch INTEGER NOT NULL CHECK(work_epoch > 0),
                    drain_token TEXT NOT NULL UNIQUE,
                    broker_ack_status TEXT NOT NULL CHECK(broker_ack_status='registered_not_broker_acked')
                )"""
            ),
        ),
        ("index", "sqlite_autoindex_canonical_tasks_1", "canonical_tasks", None),
        ("index", "sqlite_autoindex_projection_intents_1", "projection_intents", None),
        ("index", "sqlite_autoindex_command_receipts_1", "command_receipts", None),
        ("index", "sqlite_autoindex_command_drain_tokens_1", "command_drain_tokens", None),
        ("index", "sqlite_autoindex_command_drain_tokens_2", "command_drain_tokens", None),
    }
)


class _GatewayOutbox(DurableTaskpoolEventOutbox):
    def _allowed_schema_extension_sets(self) -> tuple[frozenset[tuple], ...]:
        return (_GATEWAY_EXTENSION_OBJECTS,)


class TaskpoolCommandGateway:
    """Admit one closed-schema task command into canonical SQLite state."""

    def __init__(
        self,
        db_path: Union[str, os.PathLike],
        *,
        allowed_root: Union[str, os.PathLike],
    ) -> None:
        self._db_path = Path(db_path).expanduser().absolute()
        self._outbox = _GatewayOutbox(
            self._db_path, allowed_root=allowed_root
        )
        self._initialize_gateway_schema()

    def _initialize_gateway_schema(self) -> None:
        connection = self._outbox._connect()
        try:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS canonical_tasks (
                    task_id TEXT PRIMARY KEY,
                    revision INTEGER NOT NULL CHECK(revision > 0),
                    state_json TEXT NOT NULL,
                    state_sha256 TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS projection_intents (
                    task_id TEXT NOT NULL REFERENCES canonical_tasks(task_id),
                    revision INTEGER NOT NULL CHECK(revision > 0),
                    relative_path TEXT NOT NULL,
                    canonical_sha256 TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('pending','published','failed')),
                    projection_sha256 TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    PRIMARY KEY(task_id, revision)
                );
                CREATE TABLE IF NOT EXISTS command_receipts (
                    idempotency_key TEXT PRIMARY KEY,
                    command_sha256 TEXT NOT NULL,
                    task_id TEXT NOT NULL REFERENCES canonical_tasks(task_id),
                    revision INTEGER NOT NULL CHECK(revision > 0),
                    event_id TEXT NOT NULL REFERENCES outbox_events(event_id),
                    result_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS gateway_work_epoch (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    epoch INTEGER NOT NULL CHECK(epoch >= 0)
                );
                CREATE TABLE IF NOT EXISTS command_drain_tokens (
                    idempotency_key TEXT PRIMARY KEY REFERENCES command_receipts(idempotency_key),
                    task_id TEXT NOT NULL REFERENCES canonical_tasks(task_id),
                    revision INTEGER NOT NULL CHECK(revision > 0),
                    event_id TEXT NOT NULL REFERENCES outbox_events(event_id),
                    work_epoch INTEGER NOT NULL CHECK(work_epoch > 0),
                    drain_token TEXT NOT NULL UNIQUE,
                    broker_ack_status TEXT NOT NULL CHECK(broker_ack_status='registered_not_broker_acked')
                );
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO gateway_work_epoch(id,epoch) VALUES(1,0)"
            )
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _validate_task_state(state: Any) -> dict[str, Any]:
        if type(state) is not dict or set(state) != {"frontmatter", "body"}:
            raise ValidationError("state must contain exact frontmatter/body schema")
        if type(state["frontmatter"]) is not dict or type(state["body"]) is not str:
            raise ValidationError("state must contain exact frontmatter/body schema")
        return state

    @staticmethod
    def _validate_command(command: Mapping[str, Any]) -> dict[str, Any]:
        if type(command) is not dict or set(command) != COMMAND_KEYS:
            raise ValidationError("command must use the exact closed schema")
        if command["schema"] != COMMAND_SCHEMA:
            raise ValidationError("unsupported command schema")
        for field in ("idempotency_key", "task_id"):
            value = command[field]
            if type(value) is not str or not value or value.strip() != value:
                raise ValidationError(f"{field} must be a non-empty trimmed string")
        if command["operation"] != "put":
            raise ValidationError("unsupported command operation")
        if type(command["expected_revision"]) is not int or command["expected_revision"] < 0:
            raise ValidationError("expected_revision must be a non-negative exact integer")
        TaskpoolCommandGateway._validate_task_state(command["state"])
        projection = command["projection"]
        if type(projection) is not dict or set(projection) != {"relative_path"}:
            raise ValidationError("projection must use the exact schema")
        relative_path = projection["relative_path"]
        if (
            type(relative_path) is not str
            or not relative_path
            or relative_path.strip() != relative_path
            or Path(relative_path).is_absolute()
            or ".." in Path(relative_path).parts
        ):
            raise ValidationError("projection relative_path is invalid")
        event = command["event"]
        if type(event) is not dict or set(event) != {"event_type", "payload"}:
            raise ValidationError("event must use the exact schema")
        if event["event_type"] not in ALLOWED_EVENT_TYPES:
            raise ValidationError("unsupported event_type")
        if type(event["payload"]) is not dict:
            raise ValidationError("event payload must be an object")
        _canonical_json(command)
        return dict(command)

    @staticmethod
    def _admission_timestamp(now: Union[int, float]) -> float:
        if (
            type(now) not in (int, float)
            or type(now) is bool
            or not math.isfinite(now)
        ):
            raise ValidationError("now must be a finite number")
        return float(now)

    def _receipt_result(self, idempotency_key: str) -> dict[str, Any] | None:
        connection = self._outbox._connect(readonly=True)
        try:
            row = connection.execute(
                "SELECT result_json FROM command_receipts WHERE idempotency_key=?",
                (idempotency_key,),
            ).fetchone()
            return None if row is None else json.loads(row["result_json"])
        finally:
            connection.close()

    def _current_revision(self, task_id: str) -> int:
        connection = self._outbox._connect(readonly=True)
        try:
            row = connection.execute(
                "SELECT revision FROM canonical_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            return 0 if row is None else int(row["revision"])
        finally:
            connection.close()

    def admit_projection(
        self,
        *,
        task_id: str,
        state: dict[str, Any],
        relative_path: str,
        event_payload: dict[str, Any],
        now: Union[int, float],
    ) -> dict[str, Any]:
        timestamp = self._admission_timestamp(now)
        TaskpoolCommandGateway._validate_task_state(state)
        expected_revision = self._current_revision(task_id)

        def replay_key(source_revision: int) -> str:
            semantic_material = {
                "task_id": task_id,
                "expected_revision": source_revision,
                "state": state,
                "relative_path": relative_path,
                "event_payload": event_payload,
            }
            semantic_sha256 = _sha256_text(_canonical_json(semantic_material))
            return f"projection:{task_id}:{source_revision}:{semantic_sha256}"

        if expected_revision > 0:
            replay = self._receipt_result(replay_key(expected_revision - 1))
            if replay is not None and replay.get("revision") == expected_revision:
                return replay
        idempotency_key = replay_key(expected_revision)
        command = {
            "schema": COMMAND_SCHEMA,
            "idempotency_key": idempotency_key,
            "operation": "put",
            "task_id": task_id,
            "expected_revision": expected_revision,
            "state": state,
            "projection": {"relative_path": relative_path},
            "event": {
                "event_type": "taskpool.actionable.v1",
                "payload": event_payload,
            },
        }
        try:
            return self.submit(command, now=timestamp)
        except ConflictError:
            replay = self._receipt_result(idempotency_key)
            if replay is None:
                raise
            return replay

    def submit(self, command: Mapping[str, Any], *, now: Union[int, float]) -> dict[str, Any]:
        frozen = self._validate_command(command)
        timestamp = self._admission_timestamp(now)
        command_json = _canonical_json(frozen)
        command_sha256 = _sha256_text(command_json)
        state_json = _canonical_json(frozen["state"])
        state_sha256 = _sha256_text(state_json)
        payload_json = _canonical_json(frozen["event"]["payload"])
        payload_sha256 = _sha256_text(payload_json)
        event_id = str(uuid.uuid4())
        revision = frozen["expected_revision"] + 1
        connection = self._outbox._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            receipt = connection.execute(
                "SELECT command_sha256,result_json FROM command_receipts "
                "WHERE idempotency_key=?",
                (frozen["idempotency_key"],),
            ).fetchone()
            if receipt is not None:
                if receipt["command_sha256"] != command_sha256:
                    raise ConflictError("idempotency key names a different command")
                replay = json.loads(receipt["result_json"])
                connection.rollback()
                return replay
            existing = connection.execute(
                "SELECT revision FROM canonical_tasks WHERE task_id=?",
                (frozen["task_id"],),
            ).fetchone()
            actual_revision = 0 if existing is None else existing[0]
            if actual_revision != frozen["expected_revision"]:
                raise ValidationError("canonical revision conflict")
            epoch_row = connection.execute(
                "UPDATE gateway_work_epoch SET epoch=epoch+1 WHERE id=1 RETURNING epoch"
            ).fetchone()
            if epoch_row is None:
                raise RuntimeError("gateway work epoch missing")
            work_epoch = int(epoch_row["epoch"])
            drain_token = f"{frozen['task_id']}:{revision}:{event_id}:{work_epoch}"
            result = {
                "status": "durably_admitted",
                "task_id": frozen["task_id"],
                "revision": revision,
                "event_id": event_id,
                "work_epoch": work_epoch,
                "drain_token": drain_token,
                "drain_token_scope": "admission_registered_not_broker_acked",
            }
            result_json = _canonical_json(result)
            if existing is None:
                connection.execute(
                    "INSERT INTO canonical_tasks(task_id,revision,state_json,state_sha256,updated_at) "
                    "VALUES(?,?,?,?,?)",
                    (frozen["task_id"], revision, state_json, state_sha256, timestamp),
                )
            else:
                connection.execute(
                    "UPDATE canonical_tasks SET revision=?,state_json=?,state_sha256=?,updated_at=? "
                    "WHERE task_id=? AND revision=?",
                    (
                        revision,
                        state_json,
                        state_sha256,
                        timestamp,
                        frozen["task_id"],
                        frozen["expected_revision"],
                    ),
                )
            connection.execute(
                "INSERT INTO projection_intents(task_id,revision,relative_path,canonical_sha256,status,projection_sha256,created_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (
                    frozen["task_id"],
                    revision,
                    frozen["projection"]["relative_path"],
                    state_sha256,
                    "pending",
                    "",
                    timestamp,
                ),
            )
            connection.execute(
                "INSERT INTO outbox_events(schema_version,event_id,idempotency_key,event_type,task_id,"
                "payload_json,payload_sha256,created_at,status,generation,attempt_count,updated_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    1,
                    event_id,
                    frozen["idempotency_key"],
                    frozen["event"]["event_type"],
                    frozen["task_id"],
                    payload_json,
                    payload_sha256,
                    timestamp,
                    "pending",
                    0,
                    0,
                    timestamp,
                ),
            )
            connection.execute(
                "INSERT INTO command_receipts(idempotency_key,command_sha256,task_id,revision,event_id,result_json,created_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (
                    frozen["idempotency_key"],
                    command_sha256,
                    frozen["task_id"],
                    revision,
                    event_id,
                    result_json,
                    timestamp,
                ),
            )
            connection.execute(
                "INSERT INTO command_drain_tokens(idempotency_key,task_id,revision,event_id,work_epoch,drain_token,broker_ack_status) "
                "VALUES(?,?,?,?,?,?,?)",
                (
                    frozen["idempotency_key"],
                    frozen["task_id"],
                    revision,
                    event_id,
                    work_epoch,
                    drain_token,
                    "registered_not_broker_acked",
                ),
            )
            connection.commit()
            return result
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def publish_projection(
        self,
        *,
        task_id: str,
        revision: int,
        canonical_sha256: str,
        publisher: Callable[[], Mapping[str, Any]],
        projection_reader: Callable[[], bytes],
    ) -> dict[str, Any]:
        if type(task_id) is not str or not task_id or task_id.strip() != task_id:
            raise ValidationError("task_id must be a non-empty trimmed string")
        if type(revision) is not int or revision < 1:
            raise ValidationError("revision must be a positive exact integer")
        if (
            type(canonical_sha256) is not str
            or len(canonical_sha256) != 64
            or any(character not in "0123456789abcdef" for character in canonical_sha256)
        ):
            raise ValidationError("canonical_sha256 must be lowercase SHA-256")
        if not callable(publisher) or not callable(projection_reader):
            raise ValidationError("publisher and projection_reader must be callable")

        connection = self._outbox._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT c.revision AS current_revision,p.canonical_sha256,p.status,p.relative_path,p.projection_sha256 "
                "FROM canonical_tasks AS c JOIN projection_intents AS p "
                "ON p.task_id=c.task_id AND p.revision=? "
                "WHERE c.task_id=?",
                (revision, task_id),
            ).fetchone()
            if (
                row is None
                or row["current_revision"] != revision
                or row["canonical_sha256"] != canonical_sha256
            ):
                raise ValidationError("projection intent conflict")
            result = {
                "status": "published",
                "task_id": task_id,
                "revision": revision,
                "canonical_sha256": canonical_sha256,
            }
            if row["status"] == "published":
                readback = projection_reader()
                if type(readback) is not bytes:
                    raise ValidationError("projection byte readback must return bytes")
                if hashlib.sha256(readback).hexdigest() != row["projection_sha256"]:
                    raise ValidationError("projection byte readback mismatch")
                connection.rollback()
                return result
            if row["status"] != "pending":
                raise ValidationError("projection intent conflict")
            receipt = publisher()
            readback = projection_reader()
            if type(readback) is not bytes:
                raise ValidationError("projection byte readback must return bytes")
            projection_sha256 = hashlib.sha256(readback).hexdigest()
            expected_receipt = {
                "status": "projection_written",
                "task_id": task_id,
                "revision": revision,
                "canonical_sha256": canonical_sha256,
                "relative_path": row["relative_path"],
                "projection_sha256": projection_sha256,
            }
            if type(receipt) is not dict:
                raise ValidationError("publisher receipt does not match projection intent")
            expected_without_projection_sha256 = dict(expected_receipt)
            expected_without_projection_sha256.pop("projection_sha256")
            actual_without_projection_sha256 = dict(receipt)
            actual_projection_sha256 = actual_without_projection_sha256.pop("projection_sha256", None)
            if actual_without_projection_sha256 == expected_without_projection_sha256 and actual_projection_sha256 != projection_sha256:
                raise ValidationError("projection byte readback mismatch")
            if receipt != expected_receipt:
                raise ValidationError("publisher receipt does not match projection intent and byte readback")
            updated = connection.execute(
                "UPDATE projection_intents SET status='published', projection_sha256=? "
                "WHERE task_id=? AND revision=? AND canonical_sha256=? AND status='pending'",
                (projection_sha256, task_id, revision, canonical_sha256),
            ).rowcount
            if updated != 1:
                raise ValidationError("projection intent conflict")
            connection.commit()
            return result
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def read_task(self, task_id: str) -> dict[str, Any]:
        connection = self._outbox._connect(readonly=True)
        try:
            row = connection.execute(
                "SELECT task_id,revision,state_json,state_sha256,updated_at "
                "FROM canonical_tasks WHERE task_id=?",
                (task_id,),
            ).fetchone()
            if row is None:
                raise KeyError(task_id)
            projection = connection.execute(
                "SELECT revision,relative_path,canonical_sha256,status,projection_sha256,created_at "
                "FROM projection_intents WHERE task_id=? AND revision=?",
                (task_id, row["revision"]),
            ).fetchone()
            if projection is None:
                raise RuntimeError("canonical task is missing its projection intent")
            if (
                _sha256_text(row["state_json"]) != row["state_sha256"]
                or projection["canonical_sha256"] != row["state_sha256"]
            ):
                raise RuntimeError("canonical state digest mismatch")
            return {
                "task_id": row["task_id"],
                "revision": row["revision"],
                "state": json.loads(row["state_json"]),
                "state_sha256": row["state_sha256"],
                "updated_at": row["updated_at"],
                "projection": dict(projection),
            }
        finally:
            connection.close()

    def iter_tasks(self) -> list[dict[str, Any]]:
        connection = self._outbox._connect(readonly=True)
        try:
            rows = connection.execute(
                "SELECT c.task_id,c.revision,c.state_json,c.state_sha256,c.updated_at,"
                "p.relative_path,p.canonical_sha256,p.status,p.projection_sha256,p.created_at "
                "FROM canonical_tasks AS c JOIN projection_intents AS p "
                "ON p.task_id=c.task_id AND p.revision=c.revision "
                "ORDER BY p.relative_path,c.task_id"
            ).fetchall()
            records: list[dict[str, Any]] = []
            for row in rows:
                if (
                    _sha256_text(row["state_json"]) != row["state_sha256"]
                    or row["canonical_sha256"] != row["state_sha256"]
                ):
                    raise RuntimeError("canonical state digest mismatch")
                records.append(
                    {
                        "task_id": row["task_id"],
                        "revision": row["revision"],
                        "state": json.loads(row["state_json"]),
                        "state_sha256": row["state_sha256"],
                        "updated_at": row["updated_at"],
                        "projection": {
                            "revision": row["revision"],
                            "relative_path": row["relative_path"],
                            "canonical_sha256": row["canonical_sha256"],
                            "status": row["status"],
                            "created_at": row["created_at"],
                        },
                    }
                )
            return records
        finally:
            connection.close()

    def outbox_status(self) -> dict[str, Any]:
        return self._outbox.status()

    def close(self) -> None:
        return None
