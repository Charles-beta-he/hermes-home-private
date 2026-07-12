# P0 Source Review and Owned Primitive Slice

## Objective

Absorb the common functional contracts behind representative RAG, MCP/tool, and memory examples without importing their provider/UI coupling.

## RAG evidence

Representative source:

- `advanced_llm_apps/chat_with_X_tutorials/chat_with_pdf/chat_pdf.py`

Observed chain:

```text
API key → temporary vector DB → uploaded PDF → ingestion → prompt → generated answer
```

Transferable contracts:

- source ingestion must produce source-bound chunks;
- retrieval and generation are separate responsibilities;
- temporary-file cleanup must be explicit;
- answers need citation/evidence objects rather than plain strings.

Rejected coupling:

- OpenAI-only embedding and generation configuration;
- Streamlit credential entry;
- temporary vector DB recreated in the UI path;
- answer output without explicit source citation readback.

Owned local equivalent:

- `LocalEvidenceRetriever` provides deterministic chunking and ranked source-bound evidence.
- It intentionally does not claim answer generation or semantic embedding quality.

## MCP/tool evidence

Representative source:

- `ai_agent_framework_crash_course/google_adk_crash_course/4_tool_using_agent/4_4_mcp_tools/README.md`

Observed chain:

```text
connection parameters → MCP connection → tool discovery → framework adaptation → invocation → cleanup
```

Transferable contracts:

- discovery metadata must be separate from invocation;
- each tool needs a side-effect class;
- invocation authority must fail closed;
- connection/provider lifecycle belongs behind an adapter.

Rejected coupling:

- automatic `npx -y` execution;
- implicit filesystem read/write authority;
- Firecrawl/API credentials;
- framework-specific ADK tool wrappers as the core contract.

Owned local equivalent:

- `GovernedToolRegistry` supports discovery and invocation with exact allowed-effect checks.
- External write is denied by default and proven by test/smoke evidence.

## Memory evidence

Representative sources:

- `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py`
- `advanced_llm_apps/llm_apps_with_memory_tutorials/multi_llm_memory/multi_llm_memory.py`

Observed chain:

```text
user ID → memory add/search/get_all → context assembly → model prompt → response writeback
```

Transferable contracts:

- memory ownership must be explicit;
- recall is separate from model generation;
- provider choice should not own the memory schema;
- persistence requires dedupe, TTL and atomic writes.

Source gaps not copied:

- arbitrary username is treated as authentication;
- no visible TTL policy;
- no deterministic deduplication contract;
- broad `get_all` context assembly can overfeed or cross relevance boundaries;
- assistant output is written back without a promotion/evidence policy.

Owned local equivalent:

- `JsonMemoryStore` provides owner isolation, normalized-content dedupe, TTL expiration, atomic file replacement and lexical recall.
- It is a prototype store, not global Hermes memory and not production concurrency/storage proof.

## Evidence

- Tests: `prototypes/capability_primitives/test_primitives.py`
- Smoke: `evidence/p0-primitives-smoke.json`
- Test result: 8 tests passed.
- Negative proof: unauthorized `external_write` invocation raises `PermissionError`.

## Remaining runtime gates

- semantic embeddings and generation require a selected local/provider runtime;
- real MCP transport requires an exact read-only server target and protocol test;
- production memory requires concurrency, migration, encryption/privacy, retention, deletion and recovery evidence.
