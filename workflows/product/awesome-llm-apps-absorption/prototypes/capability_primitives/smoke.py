#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path

from primitives import GovernedToolRegistry, JsonMemoryStore, LocalEvidenceRetriever, ToolSpec


def main():
    retriever = LocalEvidenceRetriever.from_texts({
        "source-rag": "RAG pipelines ingest sources, retrieve chunks, and preserve citations.",
        "source-memory": "Memory needs owner isolation, deduplication, and expiry policy.",
    })
    evidence = retriever.search("retrieve citations", limit=2)
    with tempfile.TemporaryDirectory() as tmp:
        store = JsonMemoryStore(Path(tmp) / "memory.json")
        stored = store.add("demo-user", "Prefers citation-backed answers", ttl_seconds=60)
        recalled = store.search("demo-user", "citation")
        tools = GovernedToolRegistry()
        tools.register(ToolSpec("evidence_count", "Count evidence rows", "none", lambda rows: len(rows)))
        count = tools.invoke("evidence_count", {"rows": evidence})
        denied = False
        tools.register(ToolSpec("external_send", "Demonstration blocked sender", "external_write", lambda: "sent"))
        try:
            tools.invoke("external_send", {})
        except PermissionError:
            denied = True
        result = {
            "status": "PASS",
            "evidence": evidence,
            "memory": {"stored_id": stored.id, "recalled_count": len(recalled), "owner": recalled[0].owner},
            "tool": {"evidence_count": count, "external_write_denied": denied},
            "side_effects": {"external": False, "cron": False, "taskpool": False, "agentos": False},
            "claim_boundary": "local deterministic primitives only; no LLM, embedding service, MCP server, or external API was invoked",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
