# Independent Source Review Convergence

Source commit: `426cfa66b5fd832090038c36e50a6aa1dab3119c`
Review mode: three independent read-only subagents; no external API/runtime invocation.

## RAG

Representative sources:

- `rag_tutorials/local_hybrid_search_rag/local_main.py`
- `rag_tutorials/rag_database_routing/rag_database_routing.py`
- `rag_tutorials/multimodal_agentic_rag/backend/rag_store.py`
- `rag_tutorials/multimodal_agentic_rag/backend/server.py`

Accepted patterns:

- explicit ingest/retrieve/rerank/generate boundaries;
- one immutable evidence packet shared by generation and citations;
- explicit no-route/empty-retrieval states;
- source/chunk metadata and readiness surface.

Rejected or gated patterns:

- empty retrieval falling back to unrestricted model knowledge;
- uncalibrated score semantics and hard-coded thresholds;
- duplicate ingestion on UI rerun;
- cloud/multimodal transfer without exact authority;
- URL ingestion without redirect revalidation and MIME sniffing.

Ratchet applied locally:

- `LocalEvidenceRetriever.search()` now accepts a minimum score and deterministically abstains below it.
- Added negative tests for threshold abstention and invalid thresholds.

## MCP / Tools

Representative sources:

- `mcp_ai_agents/multi_mcp_agent_router/agent_forge.py`
- `mcp_ai_agents/github_mcp_agent/github_agent.py`
- `mcp_ai_agents/notion_mcp_agent/notion_mcp_agent.py`
- `mcp_ai_agents/multi_mcp_agent/multi_mcp_agent.py`
- `advanced_ai_agents/single_agent_apps/ai_agent_governance/ai_agent_governance.py`

Accepted patterns:

- connect → initialize → discover → normalize → filter → gated invoke → receipt → close;
- domain-scoped server/tool exposure;
- deterministic policy interception outside prompts;
- namespaced tool ownership and normalized results.

Rejected or gated patterns:

- `npx -y`/`@latest` execution;
- wholesale parent-environment propagation;
- prompt text acting as write authorization;
- browser/shell/file mutation without exact target and readback;
- client-controlled MCP URLs without SSRF controls;
- tool-name collision overwrite.

Current owned registry remains local and fail-closed. Live third-party MCP runtime stays outside the current authority/evidence boundary.

## Memory

Representative sources:

- `advanced_llm_apps/llm_apps_with_memory_tutorials/ai_travel_agent_memory/travel_agent_memory.py`
- `advanced_llm_apps/llm_apps_with_memory_tutorials/multi_llm_memory/multi_llm_memory.py`
- `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py`
- `ai_agent_framework_crash_course/google_adk_crash_course/5_memory_agent/5_2_persistent_conversation_agent/agent.py`
- `ai_agent_framework_crash_course/openai_sdk_crash_course/7_sessions/7_2_memory_operations/agent.py`
- `generative_ui_agents/ai-shadcn-component-generator/apps/agent/src/bounded_memory_saver.py`

Accepted patterns:

- owner/app/conversation scoping;
- bounded recall;
- explicit inspect/delete/clear lifecycle;
- TTL/capacity controls;
- role and provenance retention.

Rejected or gated patterns:

- self-asserted user IDs treated as authentication;
- cross-app recall filtered only by user ID;
- storing model output as trusted user fact;
- unbounded `get_all()` prompt injection;
- undocumented Mem0 response-shape assumptions;
- UI clear being mislabeled as persistent-memory deletion.

Ratchet applied locally:

- explicit idempotency key support;
- scoped metadata contract: domain, conversation ID, role and provenance;
- delete-one and clear-owner/conversation operations;
- negative test for incomplete scope metadata.

## Remaining evidence boundary

The reviews and local tests establish source-grounded contracts, not upstream runtime health. Real PostgreSQL/Qdrant/Ollama/provider/MCP/device operation remains unverified and requires an exact runtime target, dependency review, credentials where applicable, and fresh readback.
