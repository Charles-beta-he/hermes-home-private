# Dual external-repo + social-lead taskpool intake

Use when the user asks to add both a canonical GitHub repo and a social/video lead into the taskpool in one flow.

## Pattern

1. Keep the two intake surfaces separate until evidence is grounded.
   - GitHub repo: verify repo identity via GitHub API, inspect top-level contents, README, agent instructions (`CLAUDE.md`/`AGENTS.md`) and package/manifest files.
   - WeChat/social lead: extract visible page text/author/date/engagement via DOM text and screenshot/OCR if needed; treat it as a lead only.

2. Write one compact shared evidence note when the two sources are thematically related.
   - Store under `~/.hermes/docs/private/`.
   - Include source URL, extracted social text, repo/API facts, canonical mapping candidates, and explicit uncertainty labels.
   - Reference this note from every created task with `--evidence-ref` so later workers can trace the source without redoing extraction.

3. Deduplicate before adding, but use bounded long timeouts.
   - `brain_task_orchestrator.py list --json` can take longer than default wrappers on large task pools; use a 300s timeout or an already-safe canonical read path.
   - If a prior command was blocked due consent/timeout guard, do not retry until the user explicitly says to continue.

4. Create separate rich tasks, not one blended vague task.
   - Repo task: source-review → architecture/gap mapping → minimal reversible integration boundary.
   - Social lead task: source evidence → canonical artifact mapping → safety/privacy/permission go-no-go.
   - Use `lane=evolution`, `priority=P2`, `project=hermes-agent`, and `architecture_target=local-brain` for Hermes self-evolution unless the material is clearly provider/cost governance.

5. Interpret add-hook output correctly.
   - `event_hook.status=OK` plus `autorun.reasons=[autorun_disabled,no_dispatchable_task]` means creation succeeded and the add event did not run bounded autorun.
   - Smart routing may still move new evolution/local-brain tasks from `pending` to `running` under `hermes-multimodel`; read back the task file before reporting final state.

## Example classification

- Open-LLM-VTuber-style repo: voice console, interruptible audio loop, Live2D/avatar projection, WebSocket session context, MCP registry, multi-engine adapters → `local-brain` / voice-visual-agent intake.
- FacePhys-style social lead: contactless physiological perception, rPPG, emotion/biometric claims → `local-brain` visual-conversation safety boundary; first task is read-only adapter and privacy/medical-claim assessment, not camera/API execution.

## Red lines

- Do not install third-party services, start daemons, request camera/microphone permissions, download large models, call credentialed SDKs, or make medical/biometric assertions during intake.
- Do not let social hype copy become acceptance evidence. Claims like model size, latency, medical-grade accuracy, or investment amount need canonical docs/papers/company/repo confirmation.
