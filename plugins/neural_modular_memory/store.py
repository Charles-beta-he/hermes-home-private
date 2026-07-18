from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

UTC = timezone.utc
SCHEMA_VERSION = "hermes.neural_modular_memory.v1"
ACTIVE_STATUSES = ("candidate", "supported", "consolidated")
CONSOLIDATABLE_MODULES = ("constraint", "preference", "procedure", "causal", "decision")

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----.*?-----END (?:[A-Z0-9 ]+ )?PRIVATE KEY-----", re.DOTALL),
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(
        r"(?i)((?:api[_-]?key|token|secret|password|aws_access_key_id|session_cookie|cookie|set-cookie|card_number|credit_card|pan)\s*[:=]\s*)[^\s,;，；]+"
    ),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"\b(?:sk|rk|pk)-[A-Za-z0-9_-]{16,}\b"),
)
_PAN_CANDIDATE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
_SENTENCE_SPLIT = re.compile(r"(?<=[。！？!?；;\n])\s*")
_CJK = re.compile(r"[\u3400-\u9fff]+")
_WORD = re.compile(r"[A-Za-z0-9_./:-]{2,}")

MODULE_RULES = {
    "intent": ("请", "需要", "希望", "目标", "帮我", "want", "need", "goal"),
    "constraint": ("必须", "不能", "不要", "不需要", "保证", "仅", "只允许", "must", "never", "do not", "don't"),
    "preference": ("偏好", "喜欢", "习惯", "更倾向", "不喜欢", "prefer", "like"),
    "decision": ("决定", "采用", "选择", "结论", "最终方案", "选用", "decide", "chosen", "adopt"),
    "evidence": ("测试通过", "验证通过", "退出码", "exit code", "passed", "verified", "sha256=", "http 200"),
    "causal": ("因为", "因此", "所以", "导致", "由于", "because", "therefore", "caused"),
    "procedure": ("首先", "然后", "最后", "步骤", "1.", "2.", "first", "then", "finally"),
    "uncertainty": ("尚未", "未验证", "不确定", "可能", "风险", "失败", "无法", "unknown", "uncertain", "not verified"),
}


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso(value: Optional[datetime] = None) -> str:
    current = value or utc_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current.astimezone(UTC).isoformat()


def redact(text: str) -> str:
    value = str(text or "")
    try:
        from agent.redact import redact_sensitive_text
        value = redact_sensitive_text(value, force=True)
    except Exception:
        pass
    for pattern in _SECRET_PATTERNS:
        if pattern.groups:
            value = pattern.sub(lambda m: (m.group(1) or "") + "[REDACTED]", value)
        else:
            value = pattern.sub("[REDACTED]", value)
    value = _PAN_CANDIDATE.sub(
        lambda match: "[REDACTED]" if _is_valid_pan(match.group(0)) else match.group(0),
        value,
    )
    return value


def _is_valid_pan(value: str) -> bool:
    digits = [int(char) for char in value if char.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def normalize(text: str) -> str:
    return " ".join(str(text or "").lower().split()).strip(" 。.!！?？;；,，")


def digest(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def search_tokens(text: str) -> List[str]:
    normalized = normalize(text)
    tokens = set(_WORD.findall(normalized))
    for block in _CJK.findall(normalized):
        if len(block) == 1:
            tokens.add(block)
        else:
            tokens.update(block[index:index + 2] for index in range(len(block) - 1))
    return sorted(token for token in tokens if token)


def clauses(text: str) -> List[str]:
    return [item.strip() for item in _SENTENCE_SPLIT.split(text) if item.strip()]


def _contains_any(text: str, markers: Sequence[str]) -> bool:
    low = text.lower()
    return any(marker.lower() in low for marker in markers)


def correction_target_tokens(text: str) -> set[str]:
    """Extract only the explicitly replaced subject of a correction."""
    value = normalize(text)
    patterns = (
        r"(?:不要|不是|不喜欢)\s*([^，,；;。.!！？?]+)",
        r"(?:纠正|更正)\s*[:：]\s*(.+?)\s*(?:改用|换成|而是)",
        r"(?:instead of|not)\s+([^,;.!?]+)",
    )
    generic = {"必须", "不要", "需要", "偏好", "纠正", "更正", "改用", "must", "not", "prefer"}
    for pattern in patterns:
        match = re.search(pattern, value, flags=re.IGNORECASE)
        if match:
            return set(search_tokens(match.group(1))) - generic
    return set()


class MemoryStore:
    def __init__(self, path: Path, now_fn: Callable[[], datetime] = utc_now):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._now_fn = now_fn
        self.conn = sqlite3.connect(str(self.path), timeout=5.0)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
              id TEXT PRIMARY KEY,
              session_id TEXT NOT NULL,
              turn_key TEXT NOT NULL,
              role TEXT NOT NULL CHECK(role IN ('user','assistant')),
              scope TEXT NOT NULL,
              observed_at TEXT NOT NULL,
              text_redacted TEXT NOT NULL,
              content_hash TEXT NOT NULL,
              created_at TEXT NOT NULL,
              UNIQUE(session_id, turn_key, role)
            );
            CREATE TRIGGER IF NOT EXISTS events_no_update
              BEFORE UPDATE ON events
              BEGIN SELECT RAISE(ABORT, 'L0 events are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS events_no_delete
              BEFORE DELETE ON events
              BEGIN SELECT RAISE(ABORT, 'L0 events are immutable'); END;
            CREATE TABLE IF NOT EXISTS projections (
              id TEXT PRIMARY KEY,
              source_event_id TEXT NOT NULL REFERENCES events(id),
              source_hash TEXT NOT NULL,
              session_id TEXT NOT NULL,
              module TEXT NOT NULL,
              abstraction_level TEXT NOT NULL,
              scope TEXT NOT NULL,
              claim TEXT NOT NULL,
              semantic_key TEXT NOT NULL,
              confidence REAL NOT NULL,
              strength REAL NOT NULL,
              status TEXT NOT NULL,
              applicability TEXT NOT NULL,
              negative_conditions TEXT NOT NULL,
              reference_only INTEGER NOT NULL DEFAULT 1,
              valid_from TEXT NOT NULL,
              expires_at TEXT,
              last_accessed_at TEXT,
              access_count INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              UNIQUE(source_event_id, module, semantic_key, claim)
            );
            CREATE INDEX IF NOT EXISTS idx_projection_scope_status
              ON projections(scope, status, module);
            CREATE INDEX IF NOT EXISTS idx_projection_semantic
              ON projections(module, scope, semantic_key);
            CREATE TABLE IF NOT EXISTS edges (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              source_projection_id TEXT NOT NULL REFERENCES projections(id),
              target_projection_id TEXT NOT NULL REFERENCES projections(id),
              relation TEXT NOT NULL,
              created_at TEXT NOT NULL,
              UNIQUE(source_projection_id, target_projection_id, relation)
            );
            CREATE TABLE IF NOT EXISTS activations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              projection_id TEXT NOT NULL REFERENCES projections(id),
              query_hash TEXT NOT NULL,
              activated_at TEXT NOT NULL,
              score REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS consolidation_receipts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              semantic_key TEXT NOT NULL,
              module TEXT NOT NULL,
              scope TEXT NOT NULL,
              action TEXT NOT NULL,
              support_sessions TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS projections_fts USING fts5(
              projection_id UNINDEXED,
              search_text,
              tokenize='unicode61'
            );
            """
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO metadata(key, value) VALUES('schema_version', ?)",
            (SCHEMA_VERSION,),
        )
        self.conn.commit()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    def _event_id(self, session_id: str, turn_key: str, role: str, text: str) -> str:
        return digest("event", session_id, turn_key, role, text)

    def _insert_event(
        self,
        session_id: str,
        turn_key: str,
        role: str,
        scope: str,
        text: str,
        observed_at: datetime,
    ) -> str:
        cleaned = redact(text)
        event_id = self._event_id(session_id, turn_key, role, cleaned)
        content_hash = digest(cleaned)
        timestamp = iso(observed_at)
        existing = self.conn.execute(
            "SELECT id,content_hash,scope FROM events WHERE session_id=? AND turn_key=? AND role=?",
            (session_id, turn_key, role),
        ).fetchone()
        if existing is not None:
            if existing["content_hash"] != content_hash or existing["scope"] != scope:
                raise ValueError("turn replay changed immutable event content or scope")
            return str(existing["id"])
        self.conn.execute(
            """INSERT INTO events
               (id, session_id, turn_key, role, scope, observed_at, text_redacted, content_hash, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, session_id, turn_key, role, scope, timestamp, cleaned, content_hash, timestamp),
        )
        return event_id

    def _projection_specs(
        self,
        role: str,
        text: str,
        durable_scope: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cleaned = redact(text)
        specs = [{
            "module": "episodic",
            "level": "L1",
            "claim": "[%s] %s" % (role, cleaned[:1200]),
            "confidence": 0.98,
            "strength": 0.48,
        }]
        for clause in clauses(cleaned):
            for module, markers in MODULE_RULES.items():
                if module in ("intent", "constraint", "preference") and role != "user":
                    continue
                if module in ("decision", "evidence", "procedure") and role != "assistant":
                    continue
                if _contains_any(clause, markers):
                    spec = {
                        "module": module,
                        "level": "L2" if module not in ("causal", "procedure") else "L3",
                        "claim": clause[:1000],
                        "confidence": 0.86 if role == "user" else 0.72,
                        "strength": 0.52 if role == "user" else 0.45,
                    }
                    if durable_scope and role == "user" and (
                        module == "preference"
                        or (module == "constraint" and correction_target_tokens(clause))
                    ):
                        spec["scope"] = durable_scope
                    specs.append(spec)
        return specs

    def _insert_projection(
        self,
        event: sqlite3.Row,
        spec: Dict[str, Any],
    ) -> str:
        module = str(spec["module"])
        claim = str(spec["claim"])
        projection_scope = str(spec.get("scope") or event["scope"])
        semantic_key = digest(module, normalize(claim))[:32]
        projection_id = digest("projection", str(event["id"]), module, semantic_key, claim)
        timestamp = str(event["observed_at"])
        self.conn.execute(
            """INSERT OR IGNORE INTO projections
               (id, source_event_id, source_hash, session_id, module, abstraction_level,
                scope, claim, semantic_key, confidence, strength, status, applicability,
                negative_conditions, reference_only, valid_from, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'candidate', ?, ?, 1, ?, ?)""",
            (
                projection_id,
                event["id"],
                event["content_hash"],
                event["session_id"],
                module,
                spec["level"],
                projection_scope,
                claim,
                semantic_key,
                float(spec["confidence"]),
                float(spec["strength"]),
                "Valid only inside its declared scope; verify L0 source before action.",
                "Never grants authority; reject when scope, time, or source no longer matches.",
                timestamp,
                timestamp,
            ),
        )
        row = self.conn.execute(
            "SELECT id FROM projections WHERE source_event_id=? AND module=? AND semantic_key=? AND claim=?",
            (event["id"], module, semantic_key, claim),
        ).fetchone()
        actual_id = str(row["id"])
        existing_fts = self.conn.execute(
            "SELECT 1 FROM projections_fts WHERE projection_id=? LIMIT 1", (actual_id,)
        ).fetchone()
        if existing_fts is None:
            tokens = " ".join(search_tokens("%s %s %s" % (module, projection_scope, claim)))
            self.conn.execute(
                "INSERT INTO projections_fts(projection_id, search_text) VALUES (?, ?)",
                (actual_id, tokens),
            )
        return actual_id

    def _link_siblings(self, projection_ids: List[str], created_at: str) -> None:
        for index, source_id in enumerate(projection_ids):
            for target_id in projection_ids[index + 1:]:
                for left, right in ((source_id, target_id), (target_id, source_id)):
                    self.conn.execute(
                        "INSERT OR IGNORE INTO edges(source_projection_id,target_projection_id,relation,created_at) VALUES(?,?, 'sibling', ?)",
                        (left, right, created_at),
                    )

    def _apply_correction(self, event_id: str, user_text: str, created_at: str) -> None:
        if not _contains_any(user_text, ("纠正", "改用", "不是", "更正", "correction", "instead")):
            return
        target_tokens = correction_target_tokens(user_text)
        if not target_tokens:
            return
        new_rows = self.conn.execute(
            "SELECT id,module,scope,claim FROM projections WHERE source_event_id=? AND module IN ('constraint','preference','intent')",
            (event_id,),
        ).fetchall()
        replaceable = {
            "constraint": ("constraint", "preference", "intent"),
            "preference": ("preference",),
            "intent": ("intent",),
        }
        for new_row in new_rows:
            modules = replaceable[str(new_row["module"])]
            placeholders = ",".join("?" for _ in modules)
            old_rows = self.conn.execute(
                """SELECT id,claim FROM projections
                   WHERE scope=? AND module IN (%s)
                     AND source_event_id<>?
                     AND status IN ('candidate','supported','consolidated')
                   ORDER BY created_at DESC LIMIT 24""" % placeholders,
                (new_row["scope"], *modules, event_id),
            ).fetchall()
            for old_row in old_rows:
                old_tokens = set(search_tokens(old_row["claim"]))
                coverage = len(target_tokens & old_tokens) / float(max(1, len(target_tokens)))
                if coverage < 0.6:
                    continue
                self.conn.execute(
                    "UPDATE projections SET status='contradicted', strength=MIN(strength,0.2) WHERE id=?",
                    (old_row["id"],),
                )
                self.conn.execute(
                    "INSERT OR IGNORE INTO edges(source_projection_id,target_projection_id,relation,created_at) VALUES(?,?, 'supersedes', ?)",
                    (new_row["id"], old_row["id"], created_at),
                )

    def ingest_turn(
        self,
        session_id: str,
        user_text: str,
        assistant_text: str,
        scope: Optional[str] = None,
        durable_scope: Optional[str] = None,
        turn_key: Optional[str] = None,
        observed_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        timestamp = observed_at or self._now_fn()
        actual_scope = scope or "session:%s" % session_id
        stable_turn_key = turn_key or digest(normalize(user_text), normalize(assistant_text))[:24]
        with self.conn:
            user_event_id = self._insert_event(session_id, stable_turn_key, "user", actual_scope, user_text, timestamp)
            assistant_event_id = self._insert_event(session_id, stable_turn_key, "assistant", actual_scope, assistant_text, timestamp)
            projection_ids: List[str] = []
            for event_id in (user_event_id, assistant_event_id):
                event = self.conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
                source_ids = [
                    self._insert_projection(event, spec)
                    for spec in self._projection_specs(
                        event["role"],
                        event["text_redacted"],
                        durable_scope=durable_scope,
                    )
                ]
                self._link_siblings(source_ids, str(event["observed_at"]))
                projection_ids.extend(source_ids)
            self._apply_correction(user_event_id, redact(user_text), iso(timestamp))
        return {
            "user_event_id": user_event_id,
            "assistant_event_id": assistant_event_id,
            "projection_ids": projection_ids,
        }

    def _candidate_ids(self, query: str) -> set[str]:
        tokens = search_tokens(query)
        if not tokens:
            return set()
        expression = " OR ".join('"%s"' % token.replace('"', '') for token in tokens[:24])
        try:
            rows = self.conn.execute(
                "SELECT projection_id FROM projections_fts WHERE projections_fts MATCH ? LIMIT 400",
                (expression,),
            ).fetchall()
            return {str(row["projection_id"]) for row in rows}
        except sqlite3.Error:
            return set()

    def recall(
        self,
        query: str,
        current_scope: str,
        limit: int = 8,
        max_chars: int = 4000,
        complete_siblings: bool = True,
        now: Optional[datetime] = None,
        additional_scopes: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, Any]]:
        del max_chars  # rendering owns the byte/character envelope
        limit = max(1, min(int(limit), 20))
        ids = self._candidate_ids(query)
        if not ids:
            return []
        allowed_scopes = sorted({current_scope, "global", *(additional_scopes or ())})
        scope_placeholders = ",".join("?" for _ in allowed_scopes)
        params: List[Any] = list(allowed_scopes)
        sql = """SELECT * FROM projections
                 WHERE status IN ('candidate','supported','consolidated')
                   AND reference_only=1
                   AND source_event_id<>'' AND length(source_hash)=64
                   AND source_hash NOT GLOB '*[^0-9a-f]*'
                   AND EXISTS (
                     SELECT 1 FROM events source_event
                     WHERE source_event.id=projections.source_event_id
                       AND source_event.content_hash=projections.source_hash
                   )
                   AND scope IN (%s)
                   AND (expires_at IS NULL OR expires_at >= ?)""" % scope_placeholders
        params.append(iso(now or self._now_fn()))
        placeholders = ",".join("?" for _ in ids)
        sql += " AND id IN (%s)" % placeholders
        params.extend(sorted(ids))
        rows = self.conn.execute(sql, params).fetchall()
        qtokens = set(search_tokens(query))
        ranked = []
        current = now or self._now_fn()
        for row in rows:
            rtokens = set(search_tokens(row["claim"]))
            overlap = len(qtokens & rtokens) / float(max(1, len(qtokens)))
            if qtokens and overlap == 0:
                continue
            created = datetime.fromisoformat(row["created_at"])
            age_days = max(0.0, (current.astimezone(UTC) - created.astimezone(UTC)).total_seconds() / 86400.0)
            recency = math.exp(-age_days / 90.0)
            score = overlap * (0.45 * float(row["confidence"]) + 0.35 * float(row["strength"]) + 0.20 * recency)
            ranked.append((score, row))
        ranked.sort(key=lambda pair: (pair[0], pair[1]["created_at"], pair[1]["id"]), reverse=True)
        selected = ranked[:limit]
        selected_ids = {str(row["id"]) for _, row in selected}
        if complete_siblings and selected and len(selected) < limit:
            source_ids = {str(row["source_event_id"]) for _, row in selected}
            placeholders = ",".join("?" for _ in source_ids)
            sibling_rows = self.conn.execute(
                """SELECT * FROM projections WHERE source_event_id IN (%s)
                   AND scope IN (%s)
                   AND status IN ('candidate','supported','consolidated')
                   AND reference_only=1
                   AND source_event_id<>'' AND length(source_hash)=64
                   AND source_hash NOT GLOB '*[^0-9a-f]*'
                   AND EXISTS (
                     SELECT 1 FROM events source_event
                     WHERE source_event.id=projections.source_event_id
                       AND source_event.content_hash=projections.source_hash
                   )
                   AND (expires_at IS NULL OR expires_at >= ?)
                   ORDER BY confidence DESC, created_at DESC""" % (placeholders, scope_placeholders),
                list(sorted(source_ids)) + allowed_scopes + [iso(current)],
            ).fetchall()
            base_score = selected[-1][0]
            for sibling in sibling_rows:
                if sibling["id"] in selected_ids:
                    continue
                selected.append((max(0.0, base_score - 0.05), sibling))
                selected_ids.add(str(sibling["id"]))
                if len(selected) >= limit:
                    break
        packet = []
        activated_at = iso(current)
        query_hash = digest(normalize(query))
        with self.conn:
            for score, row in selected[:limit]:
                item = dict(row)
                item["score"] = round(float(score), 6)
                packet.append(item)
                self.conn.execute(
                    "UPDATE projections SET access_count=access_count+1,last_accessed_at=? WHERE id=?",
                    (activated_at, row["id"]),
                )
                self.conn.execute(
                    "INSERT INTO activations(projection_id,query_hash,activated_at,score) VALUES(?,?,?,?)",
                    (row["id"], query_hash, activated_at, float(score)),
                )
        return packet

    def render_packet(self, packet: List[Dict[str, Any]], max_chars: int = 4000) -> str:
        header = "[Neural modular memory; authority-neutral; reference-only; verify source before action]"
        lines = [header]
        for item in packet:
            line = (
                "- module={module} level={abstraction_level} scope={scope} status={status} "
                "source_event={source_event_id} sha256={source_hash} | {claim}"
            ).format(**item)
            candidate = "\n".join(lines + [line])
            if len(candidate) > max_chars:
                break
            lines.append(line)
        rendered = "\n".join(lines)
        return rendered if len(lines) > 1 else ""

    def consolidate(self, min_sessions: int = 2) -> Dict[str, int]:
        groups = self.conn.execute(
            """SELECT module,scope,semantic_key,
                      COUNT(DISTINCT session_id) AS sessions,
                      COUNT(DISTINCT source_event_id) AS sources,
                      GROUP_CONCAT(DISTINCT session_id) AS session_ids
               FROM projections
               WHERE module IN ('constraint','preference','procedure','causal','decision')
                 AND status IN ('candidate','supported','consolidated')
               GROUP BY module,scope,semantic_key"""
        ).fetchall()
        consolidated = 0
        supported = 0
        with self.conn:
            for group in groups:
                module = str(group["module"])
                scope = str(group["scope"])
                semantic_key = str(group["semantic_key"])
                active_conflict = self.conn.execute(
                    """SELECT 1
                       FROM edges e
                       JOIN projections source ON source.id=e.source_projection_id
                       JOIN projections target ON target.id=e.target_projection_id
                       WHERE e.relation='contradicts'
                         AND (
                           (source.module=? AND source.scope=? AND source.semantic_key=?
                            AND target.status IN ('candidate','supported','consolidated'))
                           OR
                           (target.module=? AND target.scope=? AND target.semantic_key=?
                            AND source.status IN ('candidate','supported','consolidated'))
                         )
                       LIMIT 1""",
                    (module, scope, semantic_key, module, scope, semantic_key),
                ).fetchone()
                if active_conflict is not None:
                    continue

                session_count = int(group["sessions"])
                source_count = int(group["sources"])
                evidence_sessions = 0
                if module in ("procedure", "causal", "decision"):
                    evidence_sessions = int(self.conn.execute(
                        """SELECT COUNT(DISTINCT claim.session_id)
                           FROM projections claim
                           WHERE claim.module=? AND claim.scope=? AND claim.semantic_key=?
                             AND claim.status IN ('candidate','supported','consolidated')
                             AND EXISTS (
                               SELECT 1 FROM projections evidence
                               WHERE evidence.source_event_id=claim.source_event_id
                                 AND evidence.module='evidence'
                                 AND evidence.reference_only=1
                                 AND evidence.status IN ('candidate','supported','consolidated')
                             )""",
                        (module, scope, semantic_key),
                    ).fetchone()[0])

                evidence_ok = module not in ("procedure", "causal", "decision") or evidence_sessions == session_count
                if session_count >= min_sessions and evidence_ok:
                    cursor = self.conn.execute(
                        """UPDATE projections SET status='consolidated',strength=MAX(strength,0.8)
                           WHERE module=? AND scope=? AND semantic_key=?
                             AND status IN ('candidate','supported','consolidated')""",
                        (module, scope, semantic_key),
                    )
                    if cursor.rowcount:
                        consolidated += 1
                        self.conn.execute(
                            """INSERT INTO consolidation_receipts
                               (semantic_key,module,scope,action,support_sessions,created_at)
                               VALUES(?,?,?,'consolidated',?,?)""",
                            (semantic_key, module, scope, group["session_ids"], iso(self._now_fn())),
                        )
                elif source_count >= 2:
                    cursor = self.conn.execute(
                        """UPDATE projections SET status='supported'
                           WHERE module=? AND scope=? AND semantic_key=? AND status='candidate'""",
                        (module, scope, semantic_key),
                    )
                    if cursor.rowcount:
                        supported += 1
        return {"consolidated": consolidated, "supported": supported}

    def decay(
        self,
        now: Optional[datetime] = None,
        half_life_days: float = 45.0,
        archive_threshold: float = 0.12,
    ) -> Dict[str, int]:
        current = now or self._now_fn()
        rows = self.conn.execute(
            "SELECT id,strength,created_at,status FROM projections WHERE status IN ('candidate','supported')"
        ).fetchall()
        archived = 0
        with self.conn:
            for row in rows:
                created = datetime.fromisoformat(row["created_at"])
                age_days = max(0.0, (current.astimezone(UTC) - created.astimezone(UTC)).total_seconds() / 86400.0)
                effective = float(row["strength"]) * math.pow(0.5, age_days / max(0.1, half_life_days))
                if effective < archive_threshold:
                    self.conn.execute("UPDATE projections SET status='archived',strength=? WHERE id=?", (effective, row["id"]))
                    archived += 1
                else:
                    self.conn.execute("UPDATE projections SET strength=? WHERE id=?", (effective, row["id"]))
        return {"archived": archived}

    def stats(self) -> Dict[str, int]:
        return {
            "events": int(self.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]),
            "projections": int(self.conn.execute("SELECT COUNT(*) FROM projections").fetchone()[0]),
            "edges": int(self.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]),
            "activations": int(self.conn.execute("SELECT COUNT(*) FROM activations").fetchone()[0]),
        }

    def _list(self, table: str, where: str = "", params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        if table not in {"events", "projections", "edges", "consolidation_receipts"}:
            raise ValueError("unsupported table")
        sql = "SELECT * FROM %s" % table
        if where:
            sql += " WHERE " + where
        sql += " ORDER BY rowid"
        return [dict(row) for row in self.conn.execute(sql, params).fetchall()]

    def list_events(self) -> List[Dict[str, Any]]:
        return self._list("events")

    def list_projections(self, source_event_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if source_event_id:
            return self._list("projections", "source_event_id=?", (source_event_id,))
        return self._list("projections")

    def list_edges(self) -> List[Dict[str, Any]]:
        return self._list("edges")
