#!/usr/bin/env python3
from pathlib import Path
from research_pipeline import CitationGate, Claim, render_report, write_packet

SOURCE=Path('/Users/charles/.hermes/runs/awesome-llm-apps-reference-review-20260713/repo')
OUT=Path(__file__).resolve().parents[2]/'evidence'/'p1-research-packet'
claims=[
    Claim('rag-pdf-chain','The PDF example couples upload, ingestion and chat through Embedchain with OpenAI embedding/generation configuration.',('advanced_llm_apps/chat_with_X_tutorials/chat_with_pdf/chat_pdf.py',),'verified_static',('local upstream runtime health','answer citation correctness')),
    Claim('mcp-bridge-chain','The MCP tutorial describes connection, discovery, adaptation, invocation and cleanup as distinct integration stages.',('ai_agent_framework_crash_course/google_adk_crash_course/4_tool_using_agent/4_4_mcp_tools/README.md',),'verified_static',('MCP server compatibility','external tool authorization')),
    Claim('memory-owner-chain','The local memory example scopes reads and writes by a user_id and feeds retrieved memory into model context.',('advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py',),'verified_static',('user authentication strength','TTL/dedupe policy','production isolation')),
]
gate=CitationGate(SOURCE); verdict=gate.validate(claims)
write_packet(OUT,'Awesome LLM Apps P1 Source Claims',claims,verdict,render_report('Awesome LLM Apps P1 Source Claims',claims,verdict))
print(verdict)
raise SystemExit(0 if verdict['status']=='PASS' else 1)
