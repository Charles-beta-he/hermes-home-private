# Agentic 视频 / 数字人工作流对 Hermes media skill 的吸收边界

Generated: 2026-05-26T03:06:33+08:00
Task: `2026-05-25-评估-agentic-视频-数字人工作流对-hermes-media-skill-的吸收边界`

## Evidence commands

- `python3 ~/.hermes/scripts/brain_task_orchestrator.py next --reconcile --json` selected this task as current `dispatchable=true` next item.
- GitHub API read-back: `GET /repos/{owner}/{repo}`, `GET /repos/{owner}/{repo}/readme`, `GET /repos/{owner}/{repo}/contents` for:
  - `HBAI-Ltd/Toonflow-app`
  - `heygen-com/hyperframes`
  - `Kedreamix/Linly-Talker`
- No third-party install, model download, media generation, or GUI execution was performed; this tranche is intentionally read-only.

## Repo metadata snapshot

| Repo | Shape | Stars / Forks | License | Primary stack | Updated / pushed | Acceptance relevance |
|---|---:|---:|---|---|---|---|
| `HBAI-Ltd/Toonflow-app` | Electron / Node short-drama workstation | 8653 / 1489 | Apache-2.0 | README badges: TypeScript, Node.js, Docker, Electron; API language reports HTML | updated 2026-05-25, pushed 2026-05-12 | End-to-end planning canvas for story -> script -> storyboard -> characters -> video. |
| `heygen-com/hyperframes` | Agent-first HTML-to-video renderer and skill/plugin package | 21092 / 1989 | Apache-2.0 | TypeScript, Node >=22, skills/plugins, packages, registry | updated 2026-05-25, pushed 2026-05-25 | Directly transferable skill packaging pattern for agent-authored video compositions. |
| `Kedreamix/Linly-Talker` | Digital-human dialogue / avatar pipeline | 3326 / 528 | MIT | Python; ASR, LLM, TTS, avatar generation, WebUI/API dirs | updated 2026-05-25, pushed 2026-02-10 | Useful as a pipeline taxonomy, but heavy runtime dependencies require isolation and explicit opt-in. |

## Workflow extraction

### Toonflow-app

Observed source surface:
- Root includes `package.json`, `electron-builder.yml`, `Dockerfile`, `src/`, `data/`, `docs/`.
- README positions Toonflow as an “AI 短剧工厂” and “一站式短剧工程”: planning -> scriptwriting -> storyboard -> characters/assets -> video.
- README advertises an infinite-canvas production workbench and a three-layer agent collaboration system.

Hermes-absorbable boundary:
- Absorb as **planning schema**, not as runtime dependency.
- Useful skill template: `media-short-drama-plan` that converts a text/story seed into structured artifacts: premise, scene list, character sheet, storyboard table, asset manifest, render queue.
- Hermes evidence should be text/json artifacts and optional dry-run manifests, not generated videos by default.

Do not absorb yet:
- Do not install Electron app or run GUI.
- Do not auto-download model/video assets.
- Do not treat “short-drama factory” as a core taskpool lane; keep it under P2/P3 media workflow until an explicit media project exists.

### Hyperframes

Observed source surface:
- Root includes `AGENTS.md`, `CLAUDE.md`, `DESIGN.md`, plugin manifests (`.codex-plugin`, `.claude-plugin`, `.cursor-plugin`), `skills/`, `registry/`, `packages/`, `examples/`, `docs/`.
- README explicitly says: “Write HTML. Render video. Built for agents.”
- Quick start teaches coding agents via `npx skills add heygen-com/hyperframes`; agent commands include `/hyperframes`, `/hyperframes-cli`, `/hyperframes-media`, `/tailwind`, `/gsap`, and adapter skills.

Hermes-absorbable boundary:
- Highest-transfer item: first-class **agent skill packaging** for video generation, with separate authoring, CLI loop, media preprocessing, and animation adapter skills.
- Candidate Hermes skill pattern:
  - `hyperframes-plan`: produce composition spec only.
  - `hyperframes-author`: generate project files in a sandbox only when user explicitly requests.
  - `hyperframes-verify`: lint/preview/render commands gated by local dependency availability.
- This maps cleanly to Hermes proof requirements: manifest read-back, file tree diff, lint command, optional render artifact hash.

Do not absorb yet:
- Do not run `npx skills add` automatically.
- Do not install Node >=22 packages in the Hermes checkout.
- Do not render media in the default taskpool lane; rendering is a separately authorized write/cost step.

### Linly-Talker

Observed source surface:
- Root includes `ASR/`, `LLM/`, `TTS/`, `Musetalk/`, `NeRF/`, `VITS/`, `GPT_SoVITS/`, `api/`, `webui.py`, multiple `app_*.py`, `requirements_app.txt`, `requirements_webui.txt`, `checkpoints/`, and docs/examples.
- README describes ASR + LLM + TTS + talking-head/avatar generation, with later streaming/WebRTC work in Linly-Talker-Stream.

Hermes-absorbable boundary:
- Absorb as a **digital-human pipeline taxonomy** and safety checklist, not as executable runtime.
- Candidate Hermes skill template: `digital-human-pipeline-plan` producing:
  1. input consent/source image/audio manifest,
  2. ASR/TTS/LLM/avatar module selection,
  3. local-vs-remote dependency risk table,
  4. output validation and disclosure checklist.
- Useful for planning a bridge to external/avatar services, but only after explicit consent and model/storage budget gates.

Do not absorb yet:
- Do not download checkpoints or Hugging Face models.
- Do not run WebUI/API locally from cron.
- Do not process user likeness/voice assets without explicit consent, provenance, and output labeling.

## Hermes skill boundary proposal

### Main transferable pattern

Create a future **media workflow skill graph**, not a single all-in-one generator:

1. `media-intake-contract`
   - Inputs: objective, audience, duration, aspect ratio, source material, consent/provenance.
   - Outputs: normalized JSON/YAML brief and risk labels.
2. `short-drama-storyboard-plan`
   - Inspired by Toonflow.
   - Outputs: scene table, characters, storyboard beats, asset manifest.
3. `html-video-composition-plan`
   - Inspired by Hyperframes.
   - Outputs: composition spec, timing, animation runtime hints, dependency plan.
4. `digital-human-pipeline-plan`
   - Inspired by Linly-Talker.
   - Outputs: ASR/LLM/TTS/avatar chain plan and consent/safety checklist.
5. `media-render-execution` (separate opt-in task)
   - Only runs after dependency, disk, copyright, and user-consent gates pass.

### Proof gates for future implementation tasks

A media skill implementation task must not close on `py_compile` or generic selfcheck alone. It needs at least:
- source repo/readme read-back evidence;
- generated skill file or template diff;
- fixture input -> generated plan output read-back;
- schema validation or deterministic test for the generated plan;
- explicit statement that no third-party media runtime was installed/executed unless separately authorized.

## Refusal / risk checklist

- Copyright: generated video, voice, avatar, or source media must include provenance and rights labels.
- Likeness/voice: digital-human flows require explicit consent and disclosure.
- Cost/disk: video models/checkpoints/rendering must be budget-gated and never cron-default.
- Runtime isolation: GUI/Electron/WebUI/Node renderers must run outside the Hermes source checkout and only in a sandbox/worktree.
- Governance: media output is product work, not Hermes control-plane health evidence.

## Follow-up tasks to enqueue separately if desired

P2:
- Implement `media-intake-contract` + deterministic fixture test for structured media briefs.
- Convert Hyperframes-style skill packaging into a Hermes optional skill scaffold (`plan` only, default-off).

P3:
- Draft `digital-human-pipeline-plan` safety template for consent/provenance/output labeling.
- Add a docs-only comparison of Toonflow canvas workflow vs Hermes taskpool artifact graph.

## Closeout recommendation

This bounded tranche satisfies the current task’s acceptance evidence at the analysis/report level: repo metadata, workflow extraction, input/output boundaries, skill-template mapping, refusal/risk checklist, and follow-up tasks are recorded here. Because the task is in evolution lane with previous multimodel `FAIL/CONTINUE_LOOP`, it should move to `review`, not `done`, until normal review/ratification certifies the closeout.
