# Awesome LLM Apps P1 Source Claims

Citation gate: **PASS**

## Claims

### rag-pdf-chain

The PDF example couples upload, ingestion and chat through Embedchain with OpenAI embedding/generation configuration.

Status: `verified_static`

Evidence:
- `advanced_llm_apps/chat_with_X_tutorials/chat_with_pdf/chat_pdf.py`

Cannot prove:
- local upstream runtime health
- answer citation correctness

### mcp-bridge-chain

The MCP tutorial describes connection, discovery, adaptation, invocation and cleanup as distinct integration stages.

Status: `verified_static`

Evidence:
- `ai_agent_framework_crash_course/google_adk_crash_course/4_tool_using_agent/4_4_mcp_tools/README.md`

Cannot prove:
- MCP server compatibility
- external tool authorization

### memory-owner-chain

The local memory example scopes reads and writes by a user_id and feeds retrieved memory into model context.

Status: `verified_static`

Evidence:
- `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py`

Cannot prove:
- user authentication strength
- TTL/dedupe policy
- production isolation
