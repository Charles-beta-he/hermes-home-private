# Rowboat Analysis — 2026-05-24

## Source
Repository: rowboatlabs/rowboat (YC S24, ~14k stars)
Type: Electron desktop app — local-first AI coworker with persistent knowledge graph

## Architecture

- Monorepo: Electron app (apps/x), Next.js web dashboard (apps/rowboat), CLI, Python SDK
- DI container using Awilix (container.ts) with singleton registrations
- Build: esbuild for Electron main, Vite for renderer

## Key Patterns Discovered

### Two-Pass Event Routing (Most Novel)
Event Producer → events/pending/{monotonic_id}.json → Event Processor (polls 5s) → Consumers

Pass-1: LLM classifies event against all targets' intent+matchCriteria (liberal, batch 20)
Pass-2: Agent itself judges relevance before acting

### Agent Definitions
Each agent: {name, description, instructions, tools: Record<string, ToolAttachment>}
Loaded via loadAgent(), dispatched by agentId in createRun()

### Skill Lazy Loading
15+ skills in catalog. Agents call loadSkill("skill-name") at runtime.
Skills registered with alias resolution (path variants, .ts/.js).

### Background Task Infrastructure
- OUTPUT mode: maintain index.md
- ACTION mode: side-effect + journal entry
- Concurrency guard: Set<string> of running slugs
- Disk-persistent backstop: lastAttemptAt > lastRunAt
- Backoff prevents retry storms

### Knowledge Graph
- Plain Markdown in knowledge/ dir (People/, Organizations/, Projects/, Topics/)
- Incremental processing with file hashes
- Batches of 10 files per agent run
- State saved after each successful batch for crash recovery

### Security Layer
- extractCommandNames() parses shell commands
- isBlocked() checks against security allow-list
- "always" scope persists commands to config
- AbortSignal with process group killing

### ETag-Based Concurrency
workspace-writeFile supports expectedEtag parameter for conflict detection

## What Hermes Already Had (Pre-2026-05-24)
- kg_entity_extractor.py (knowledge graph)
- live_notes_accumulator.py (session working memory)
- semantic_retrieval.py (TF-IDF search)
- rowboat_bridge.py (unification layer)
- 20 tests passing

## Bug Fixed (2026-05-24)
- access_count column missing from live_notes_accumulator.py schema
- Bridge's compute_decay_score() referenced access_count but column didn't exist
- Added: access_count INTEGER DEFAULT 0, last_accessed_at TEXT
- Added: migration for existing DBs
- Added: record_access() function
- Added: access tracking in search_notes(), on_session_start(), query_context()

## Patterns NOT Adopted
- Electron/React UI
- Composio integrations
- Deepgram/ElevenLabs/Exa
- Full event sourcing for agent runs (Hermes uses SQLite sessions)
- MCP layer (Hermes has its own MCP implementation)
