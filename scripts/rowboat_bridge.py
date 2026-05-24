#!/usr/bin/env python3
"""
Rowboat Bridge — Integration layer for Rowboat-inspired Hermes improvements.

Ties together the three Rowboat-inspired scripts:
  - kg_entity_extractor.py  (knowledge graph)
  - live_notes_accumulator.py  (session working memory)
  - semantic_retrieval.py  (TF-IDF semantic search)

Provides a unified API for Hermes session lifecycle:
  1. on_session_start  — load working memory context
  2. on_observation     — record to live notes + extract entities
  3. on_session_end     — consolidate working memory, update graph
  4. query_context      — unified search across all three stores

Usage:
    python3 rowboat_bridge.py session-start [--session-id ID]
    python3 rowboat_bridge.py observe "text" [--tag TAG] [--category CAT]
    python3 rowboat_bridge.py session-end [--session-id ID]
    python3 rowboat_bridge.py query "search text" [--top N]
    python3 rowboat_bridge.py context-summary
    python3 rowboat_bridge.py health-check

Inspired by: Rowboat (rowboatlabs/rowboat) — local-first AI coworker
  - Knowledge Graph pattern for entity-relation triples
  - Live Notes pattern for session working memory
  - Semantic retrieval for conceptual similarity
"""

import sqlite3
import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.expanduser("~/.hermes/state")
MEMORY_DIR = os.path.expanduser("~/.hermes/memories")

# DB paths (shared with the individual scripts)
KG_DB = os.path.join(STATE_DIR, "kg_graph.sqlite")
LIVE_NOTES_DB = os.path.join(STATE_DIR, "live_notes.sqlite")
SEMANTIC_DB = os.path.join(STATE_DIR, "semantic_index.sqlite")

# Memory decay parameters (inspired by Rowboat's importance-weighted consolidation)
DECAY_HALF_LIFE_DAYS = 30  # Memories lose half importance every 30 days
MIN_IMPORTANCE = 1
MAX_IMPORTANCE = 10
ACCESS_BOOST = 0.5  # Each access boosts importance by this


def get_session_id():
    """Get or generate a session ID."""
    return os.environ.get("HERMES_SESSION_ID", f"session-{datetime.now().strftime('%Y%m%d_%H%M%S')}")


def run_script(script_name, args):
    """Run a helper script and return its output."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    try:
        result = subprocess.run(
            [sys.executable, script_path] + args,
            capture_output=True, text=True, timeout=30
        )
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "timeout", "returncode": -1}
    except FileNotFoundError:
        return {"stdout": "", "stderr": f"script not found: {script_path}", "returncode": -1}


def compute_decay_score(created_at_str, last_accessed_str=None, access_count=0, base_importance=5):
    """
    Compute memory importance with exponential decay.
    
    Rowboat-inspired: importance-weighted memory consolidation.
    Memories decay over time but get boosted by access frequency.
    
    score = base_importance * (0.5 ^ (age_days / HALF_LIFE)) * (1 + ACCESS_BOOST * access_count)
    """
    now = datetime.now()
    try:
        created = datetime.fromisoformat(created_at_str)
    except (ValueError, TypeError):
        return base_importance
    
    age_days = max((now - created).total_seconds() / 86400, 0)
    
    # Exponential decay
    decay_factor = 0.5 ** (age_days / DECAY_HALF_LIFE_DAYS)
    
    # Access frequency boost
    access_factor = 1.0 + (ACCESS_BOOST * min(access_count, 20))
    
    score = base_importance * decay_factor * access_factor
    return max(MIN_IMPORTANCE, min(MAX_IMPORTANCE, score))


def on_session_start(session_id=None):
    """
    Session start hook — load working memory context.
    
    Returns recent live notes and relevant knowledge graph context
    for injection into the session prompt.
    """
    session_id = session_id or get_session_id()
    context = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "live_notes": [],
        "recent_entities": [],
        "semantic_suggestions": [],
    }
    
    # Load recent live notes (with access tracking)
    try:
        if os.path.exists(LIVE_NOTES_DB):
            conn = sqlite3.connect(LIVE_NOTES_DB)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT id, content, category, tags, importance, created_at
                FROM notes
                WHERE consolidated = 0
                ORDER BY importance DESC, created_at DESC
                LIMIT 10
            """).fetchall()
            context["live_notes"] = [
                {
                    "content": r["content"],
                    "category": r["category"],
                    "importance": r["importance"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
            # Record access for loaded notes
            now_iso = datetime.now().isoformat()
            for r in rows:
                conn.execute(
                    "UPDATE notes SET access_count = access_count + 1, last_accessed_at = ? WHERE id = ?",
                    (now_iso, r["id"])
                )
            conn.commit()
            conn.close()
    except Exception as e:
        context["live_notes_error"] = str(e)
    
    # Load recent entities from knowledge graph
    try:
        if os.path.exists(KG_DB):
            conn = sqlite3.connect(KG_DB)
            rows = conn.execute("""
                SELECT name, type, updated_at, metadata
                FROM entities
                ORDER BY updated_at DESC
                LIMIT 10
            """).fetchall()
            context["recent_entities"] = [
                {"name": r[0], "type": r[1], "updated_at": r[2]}
                for r in rows
            ]
            conn.close()
    except Exception as e:
        context["entities_error"] = str(e)
    
    return context


def on_observation(text, tag=None, category="observation", session_id=None):
    """
    Observation hook — record to live notes AND extract entities.
    
    This is the unified "record what happened" entry point.
    Inspired by Rowboat's pattern of extracting knowledge from every interaction.
    """
    session_id = session_id or get_session_id()
    results = {"session_id": session_id, "timestamp": datetime.now().isoformat()}
    
    # 1. Record to live notes
    ln_args = ["add", text]
    if tag:
        ln_args.extend(["--tag", tag])
    ln_args.extend(["--cat", category])
    ln_result = run_script("live_notes_accumulator.py", ln_args)
    results["live_notes"] = {
        "status": "ok" if ln_result["returncode"] == 0 else "error",
        "detail": ln_result["stdout"].strip() or ln_result["stderr"].strip(),
    }
    
    # 2. Extract entities to knowledge graph
    kg_result = run_script("kg_entity_extractor.py", ["extract", text])
    results["knowledge_graph"] = {
        "status": "ok" if kg_result["returncode"] == 0 else "error",
        "detail": kg_result["stdout"].strip() or kg_result["stderr"].strip(),
    }
    
    return results


def on_session_end(session_id=None):
    """
    Session end hook — consolidate working memory.
    
    Promotes important live notes to long-term memory and
    applies memory decay to stale entries.
    """
    session_id = session_id or get_session_id()
    results = {"session_id": session_id, "timestamp": datetime.now().isoformat()}
    
    # 1. Consolidate live notes
    try:
        if os.path.exists(LIVE_NOTES_DB):
            conn = sqlite3.connect(LIVE_NOTES_DB)
            
            # Find notes worth consolidating (importance >= 7)
            high_value = conn.execute("""
                SELECT id, content, category, importance, access_count, created_at
                FROM notes
                WHERE consolidated = 0 AND importance >= 7
                ORDER BY importance DESC
                LIMIT 20
            """).fetchall()
            
            consolidated = []
            stale = []
            
            for note_id, content, cat, importance, access_count, created_at in high_value:
                decayed = compute_decay_score(created_at, access_count=access_count, base_importance=importance)
                if decayed >= 5:
                    consolidated.append({"content": content, "category": cat, "score": round(decayed, 2)})
                    conn.execute("UPDATE notes SET consolidated = 1 WHERE id = ?", (note_id,))
                else:
                    stale.append({"content": content[:50], "score": round(decayed, 2)})
            
            # Apply decay to all unconsolidated notes — mark low-value ones
            all_notes = conn.execute("""
                SELECT id, importance, access_count, created_at
                FROM notes WHERE consolidated = 0
            """).fetchall()
            
            decayed_count = 0
            for nid, imp, ac, cat_at in all_notes:
                score = compute_decay_score(cat_at, access_count=ac, base_importance=imp)
                if score < 2:
                    conn.execute("UPDATE notes SET consolidated = -1 WHERE id = ?", (nid,))
                    decayed_count += 1
            
            conn.commit()
            conn.close()
            
            results["consolidation"] = {
                "promoted": len(consolidated),
                "decayed": decayed_count,
                "items": consolidated[:5],
            }
    except Exception as e:
        results["consolidation_error"] = str(e)
    
    # 2. Run entity extraction session summary
    kg_result = run_script("kg_entity_extractor.py", ["stats"])
    results["knowledge_graph_stats"] = kg_result["stdout"].strip()
    
    return results


def query_context(query_text, top_n=5):
    """
    Unified search across all three stores.
    
    Returns combined results from:
    - Knowledge graph entity matches
    - Live notes content matches
    - Semantic retrieval results
    """
    results = {
        "query": query_text,
        "timestamp": datetime.now().isoformat(),
        "knowledge_graph": [],
        "live_notes": [],
        "semantic": [],
    }
    
    # 1. Knowledge graph search
    try:
        if os.path.exists(KG_DB):
            conn = sqlite3.connect(KG_DB)
            rows = conn.execute("""
                SELECT name, type, metadata FROM entities
                WHERE name LIKE ? OR metadata LIKE ?
                ORDER BY updated_at DESC LIMIT ?
            """, (f"%{query_text}%", f"%{query_text}%", top_n)).fetchall()
            results["knowledge_graph"] = [
                {"name": r[0], "type": r[1]} for r in rows
            ]
            conn.close()
    except Exception as e:
        results["kg_error"] = str(e)
    
    # 2. Live notes search (with access tracking)
    try:
        if os.path.exists(LIVE_NOTES_DB):
            conn = sqlite3.connect(LIVE_NOTES_DB)
            rows = conn.execute("""
                SELECT id, content, category, importance, created_at FROM notes
                WHERE content LIKE ? AND consolidated >= 0
                ORDER BY importance DESC, created_at DESC LIMIT ?
            """, (f"%{query_text}%", top_n)).fetchall()
            results["live_notes"] = [
                {"id": r[0], "content": r[1][:200], "category": r[2], "importance": r[3]}
                for r in rows
            ]
            # Record access for matched notes (Rowboat access-boost pattern)
            now_iso = datetime.now().isoformat()
            for r in rows:
                conn.execute(
                    "UPDATE notes SET access_count = access_count + 1, last_accessed_at = ? WHERE id = ?",
                    (now_iso, r[0])
                )
            conn.commit()
            conn.close()
    except Exception as e:
        results["ln_error"] = str(e)
    
    # 3. Semantic search
    sem_result = run_script("semantic_retrieval.py", ["search", query_text, "--top", str(top_n)])
    if sem_result["returncode"] == 0:
        results["semantic_raw"] = sem_result["stdout"].strip()
    else:
        results["semantic_error"] = sem_result["stderr"].strip()
    
    return results


def context_summary():
    """
    Generate a summary of all Rowboat-inspired stores for prompt injection.
    Useful as a system context block.
    """
    summary = {
        "timestamp": datetime.now().isoformat(),
        "stores": {},
    }
    
    # KG stats
    try:
        if os.path.exists(KG_DB):
            conn = sqlite3.connect(KG_DB)
            ent_count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            rel_count = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
            summary["stores"]["knowledge_graph"] = {
                "entities": ent_count,
                "relations": rel_count,
            }
            conn.close()
        else:
            summary["stores"]["knowledge_graph"] = {"status": "not_initialized"}
    except Exception as e:
        summary["stores"]["knowledge_graph"] = {"error": str(e)}
    
    # Live notes stats
    try:
        if os.path.exists(LIVE_NOTES_DB):
            conn = sqlite3.connect(LIVE_NOTES_DB)
            active = conn.execute("SELECT COUNT(*) FROM notes WHERE consolidated = 0").fetchone()[0]
            total = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            summary["stores"]["live_notes"] = {
                "active": active,
                "total": total,
            }
            conn.close()
        else:
            summary["stores"]["live_notes"] = {"status": "not_initialized"}
    except Exception as e:
        summary["stores"]["live_notes"] = {"error": str(e)}
    
    # Semantic index stats
    try:
        if os.path.exists(SEMANTIC_DB):
            conn = sqlite3.connect(SEMANTIC_DB)
            docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            summary["stores"]["semantic_index"] = {"documents": docs}
            conn.close()
        else:
            summary["stores"]["semantic_index"] = {"status": "not_initialized"}
    except Exception as e:
        summary["stores"]["semantic_index"] = {"error": str(e)}
    
    return summary


def health_check():
    """
    Verify all Rowboat-inspired stores are healthy.
    Returns a dict of store_name -> {status, details}.
    """
    checks = {}
    
    for name, path in [("knowledge_graph", KG_DB), ("live_notes", LIVE_NOTES_DB), ("semantic_index", SEMANTIC_DB)]:
        if os.path.exists(path):
            try:
                conn = sqlite3.connect(path)
                conn.execute("SELECT 1")
                size = os.path.getsize(path)
                conn.close()
                checks[name] = {"status": "ok", "size_bytes": size, "path": path}
            except Exception as e:
                checks[name] = {"status": "error", "error": str(e), "path": path}
        else:
            checks[name] = {"status": "not_found", "path": path}
    
    return checks


def main():
    if len(sys.argv) < 2:
        print("Usage: rowboat_bridge.py <command> [args]")
        print("Commands:")
        print("  session-start    Load working memory context for session")
        print("  observe TEXT     Record observation to live notes + KG")
        print("  session-end      Consolidate working memory, apply decay")
        print("  query TEXT       Search across all stores")
        print("  context-summary  Summary of all stores")
        print("  health-check     Verify all stores are healthy")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "session-start":
        session_id = sys.argv[2] if len(sys.argv) > 2 else None
        result = on_session_start(session_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif cmd == "observe":
        if len(sys.argv) < 3:
            print("Usage: rowboat_bridge.py observe 'text' [--tag TAG] [--category CAT]")
            sys.exit(1)
        text = sys.argv[2]
        tag = None
        category = "observation"
        args = sys.argv[3:]
        i = 0
        while i < len(args):
            if args[i] == "--tag" and i + 1 < len(args):
                tag = args[i + 1]
                i += 2
            elif args[i] == "--cat" and i + 1 < len(args):
                category = args[i + 1]
                i += 2
            else:
                i += 1
        result = on_observation(text, tag=tag, category=category)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif cmd == "session-end":
        session_id = sys.argv[2] if len(sys.argv) > 2 else None
        result = on_session_end(session_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif cmd == "query":
        if len(sys.argv) < 3:
            print("Usage: rowboat_bridge.py query 'search text' [--top N]")
            sys.exit(1)
        query_text = sys.argv[2]
        top_n = 5
        if "--top" in sys.argv:
            idx = sys.argv.index("--top")
            if idx + 1 < len(sys.argv):
                top_n = int(sys.argv[idx + 1])
        result = query_context(query_text, top_n)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif cmd == "context-summary":
        result = context_summary()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif cmd == "health-check":
        result = health_check()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
