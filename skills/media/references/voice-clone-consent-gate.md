# Voice-clone consent gate for AI voice/TTS media signals

Applicability: use when a short video, social-media signal, repo, or user request suggests adding AI voice cloning / reference-audio TTS to Hermes or another media workflow. This is the safe bridge from "interesting voice tool" to "C is selectable" without silently cloning a voice.

Anti-conditions:
- Do not use this to authorize production/default voice replacement.
- Do not use this to bypass model-download/GPU/runtime approval.
- Do not send generated clone audio externally from this gate; external delivery is a separate gate after a local artifact exists.
- Do not treat social-video claims as technical truth; verify the underlying repo/API/model directly.

## Procedure

1. Split the signal into two evidence classes:
   - market/use-case signal: caption, screenshots, video frames, comments, creator claims;
   - technical truth: upstream repo/API/docs, license, README, model cards, current runtime requirements.
2. Deduplicate against previous tasks/notes before adding a new taskpool item. If existing VoxCPM/VoxCPM2/TTS tasks exist, create a follow-up provider-selection or consent-gate task, not another broad repo-reading task.
3. Classify the path:
   - A: watch/no model execution;
   - B: synthetic-only voice design / no reference audio;
   - C: reference-audio voice clone.
4. For C, land a consent/provenance gate before any synthesis:
   - explicit consent is true;
   - consent scope includes `tts_voice_clone`;
   - consent record is a real local file;
   - reference audio paths are real local regular files and non-empty;
   - purpose is explicit;
   - output label is `consented_voice_clone` or `synthetic_clone`;
   - first delivery boundary is `local_file` only.
5. Make the gate return a narrow status such as `selectable_for_local_clone_prototype`; this means "prototype may start" only, not "voice clone is approved for default use or external sending".
6. Keep heavy runtime dependencies out of Hermes core. Provider integration should be optional, disabled by default, and behind config/runtime checks.

## Hermes implementation pattern

A reusable local gate can be shaped like:

```bash
python scripts/voice_clone_gate.py --template
python scripts/voice_clone_gate.py --json /path/to/voice-clone-manifest.json
```

Expected pass shape:

```json
{
  "ok": true,
  "status": "selectable_for_local_clone_prototype",
  "findings": []
}
```

Expected blocked cases include missing explicit consent, missing `tts_voice_clone` scope, missing/empty reference audio, missing purpose, and any Telegram/external delivery in the first clone gate.

## Enabling C after the user explicitly selects it

When the user says to enable C and a previous voice identity/style already exists, do not jump to real-person cloning or a heavy local model. Prefer the smallest local prototype path:

1. Recover the style from memory/session notes/skill references and summarize it as an abstract voice identity, not a person to imitate.
2. Prefer a previously generated synthetic sample owned by the workflow as reference audio. Mark the manifest `subject_type: synthetic` and `output_label: synthetic_clone`.
3. Create a scoped C workspace containing: `consent.md`, `voice-clone-manifest.json`, `target-script.txt`, `style-found.md`, generated audio outputs, and `receipt.json`.
4. Run the manifest gate before synthesis. A provider mismatch warning (for example using a cloud voiceclone provider while the original market signal was VoxCPM2) is acceptable only if the gate still returns `ok=true` and the provider/runtime choice is recorded.
5. Generate only a local file first. Post-process/normalize for fair listening comparison, then verify with `ffprobe` or equivalent audio metadata inspection.
6. Update the task/proof record with the gate result, provider/model, local artifact paths, ffprobe metadata, and explicit non-actions: no external send, no default TTS activation, no public release/deploy.
7. Treat qualitative taste/listening approval as a human decision. Do not auto-promote the voice to Hermes default from a successful local artifact.

## After the user approves a local C audio sample

Listening approval unlocks the next safe slice, but still not default activation. Preferred rollout sequence:

1. Add a selectable command TTS provider rather than switching `tts.provider` immediately.
2. Back up the active config before mutation.
3. Make the provider command validate the consent/provenance manifest on every invocation, not only during the first prototype run.
4. Keep the provider script outside Hermes core if it depends on optional cloud/runtime credentials or heavy media dependencies.
5. Run a short smoke phrase through the exact command provider and inspect the output with audio metadata (`ffprobe` or equivalent): codec, sample rate, channels, and duration.
6. Record the rollout receipt/readback with: provider key, config backup, manifest path, smoke artifact, verification commands, and explicit non-actions.
7. Update the task/proof record and project/profile ledger as `validated-local-selectable-slice` or equivalent. Keep default activation and external delivery as separate explicit gates.

## Verification checklist

- [ ] Social-video claim resolved to canonical URL and local evidence bundle if needed.
- [ ] Upstream technical source verified directly, not inferred from the video.
- [ ] Existing tasks/notes checked for dedupe.
- [ ] C path has a manifest gate and failing tests for missing consent/reference audio.
- [ ] Valid local manifest smoke returns `selectable_for_local_clone_prototype`.
- [ ] If C is enabled, synthetic/self-owned reference provenance is recorded before synthesis.
- [ ] Generated local audio is verified with codec/sample-rate/channel/duration metadata.
- [ ] If the user approves and asks for default activation, config is backed up, `tts.provider` is switched only after direct provider smoke passes, official `text_to_speech` confirms the provider in use, and a receipt/readback is written.
- [ ] No model download, GPU use, external delivery, default activation, or paid API call occurs without a later explicit gate.

## Promoting an approved local clone to a default Hermes TTS provider

When the user explicitly approves the local audio and asks to make it default, treat this as a separate activation gate after C succeeds:

1. Back up `~/.hermes/config.yaml` before mutation.
2. Add or select a command provider under `tts.providers.<name>` that validates the consent/provenance manifest on every invocation, reads `{input_path}`, writes `{output_path}`, and exits non-zero on gate/provider/audio failures.
3. Smoke the provider directly first with a short Chinese phrase and verify the output with `ffprobe` or equivalent codec/sample-rate/channel/duration metadata.
4. Only then set `tts.provider` to the approved provider.
5. Run the official Hermes TTS path (`text_to_speech`) to prove the configured default is actually used; provider selection in the tool result is stronger evidence than config inspection alone.
6. Write a scoped receipt/readback containing: config backup path, active provider name, manifest path, smoke output, hash/metadata, and explicit boundaries.
7. External delivery through the current user-triggered TTS response can be allowed only after the user has requested/authorized the default activation or send; real-person cloning, public release, model downloads, deploys, and push remain separate gates.

## Pitfalls

- "Free/open-source voice clone" does not remove identity/consent risk.
- A successful consent/provenance gate is not an audio artifact; it only makes the next local prototype step selectable.
- Telegram voice/audio delivery is an external side effect even if the target is the current chat; keep it separate from local generation.
- Do not encode project-specific repo stars, task IDs, commit hashes, or local artifact paths in the class-level skill; keep them in taskpool/profile references.
