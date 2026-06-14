# Cost-gated DaVinci/AutoEdit workflow intake pattern

Use when a social post, GitHub repo, or user request points to AI-assisted video editing, DaVinci Resolve automation, MCP-controlled editing, VLM-based material review, or TTS-assisted rough cuts.

## Class-level lesson

Automatic editing is valuable only if it is **approval-gated and cost-aware**. Treat VLM/TTS/LLM calls and timeline writes as separate gates. A rough-cut demo is not proof of a production workflow.

## Evidence to collect

- Social/source URL, author, date, metrics, caption/hashtags.
- Canonical repo/docs if named in video frames or comments.
- Video/contact-sheet OCR for:
  - repo names and install commands;
  - model/API names;
  - cost screenshots or pricing clues;
  - step-by-step workflow claims;
  - supported editing software/MCP surface;
  - comments about long preprocessing time.
- Canonical repo facts: license, language, requirements, bundled skills/plugins, read/write surfaces, external dependencies.

## Recommended workflow model

```text
brief
→ media manifest / source-immutable scan scope
→ frame/transcript/material review
→ material taxonomy + evidence map
→ script/copy draft
→ optional TTS plan
→ edit blueprint / EDL
→ optional DaVinci Resolve/MCP write
→ timeline/read-back audit
→ render/output audit
→ pickup-shot or missing-material report
```

Every creative artifact should be previewed and approved before the next stage. Source media stays read-only.

## Cost gate

Before the first billable request, estimate and ask for a budget decision.

Cost drivers:
- total video duration and clip count;
- frame sampling rate and frame resolution;
- number of VLM passes and re-analysis loops;
- transcript/OCR/audio analysis;
- TTS length, voice cloning, and reference-audio processing;
- cloud LLM script/refinement iterations;
- 360/Insta360 or other preprocessing time;
- render/export time and storage.

Suggested controls:
- `budget_mode: dry_run | low | normal | high`;
- `max_spend_per_run` and `max_paid_calls`;
- sample-first analysis on a short segment or low-fps proxy;
- cache frame sheets, transcripts, material tags, and VLM results by media hash;
- default TTS off unless requested;
- blueprint-only fallback when Resolve/MCP or budget is unavailable;
- explicit confirmation before timeline write, render, or source-derivative creation.

## Write-surface gates

DaVinci Resolve/MCP operations are external writes. Require:
- target project/timeline name;
- command preview or edit blueprint;
- explicit user approval for the write gate;
- read-back proof: timeline exists, clips/markers/subtitles/audio were actually written, source bounds are valid, no gaps/repetition beyond plan;
- versioned outputs; never overwrite an existing project/timeline unless explicitly requested.

Do not treat a successful MCP/API call as proof of an edit. Verify the target state or generated artifacts.

## Red lines

- Do not install editing skills, Resolve MCP servers, or dependencies during intake.
- Do not call paid VLM/TTS APIs without explicit budget approval.
- Do not mutate or delete source media.
- Do not download private/social media assets without permission.
- Do not write a Resolve timeline, render, or export without an explicit write gate.
- Do not assume DaVinci Resolve Free supports external scripting; provide blueprint-only fallback.
