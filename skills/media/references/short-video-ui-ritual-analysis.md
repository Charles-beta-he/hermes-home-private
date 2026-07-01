# Short-video UI ritual / startup-screen analysis

Use this reference when a Douyin/TikTok-style clip is interesting because of its **interface feel** — startup screens, boot/wake sequences, sci-fi HUDs, assistant personas, command-center panels, music/player rituals, ambient dashboards, or other product/UI inspiration — rather than because it proves a backend capability.

## Applicability

- User says a startup page, UI, animation, transition, assistant persona, command phrase, or product effect is interesting.
- The clip shows a UI prototype/demo where the reusable value is interaction framing, visual hierarchy, mood, or ritual.
- You need to turn a social-video UI observation into a design note or taskpool candidate without treating the demo as technical proof.

## Anti-conditions

- Do not claim the backend/agent capability is real from the UI clip alone.
- Do not copy protected IP/brand dressing (for example Jarvis/Iron Man visuals) as-is; extract the pattern.
- Do not skip media evidence capture: page caption alone is not enough for visual-design claims.
- Do not connect real devices, paid APIs, music services, or system permissions during intake.

## Evidence pipeline

1. Resolve the short URL and save visible metadata: final URL, title/caption, author, publish time, duration, visible engagement counts, gate status.
2. Inspect DOM media; when an MP4 is accessible, save it under a scoped private evidence directory.
3. Run `ffprobe` for duration/streams and create a contact sheet with `ffmpeg` at a low frame rate (1 fps is usually enough for 30–60s UI demos).
4. Inspect the contact sheet first to identify state transitions, then analyze 2–5 key frames individually.
5. Write a concise design-analysis artifact with:
   - source metadata and evidence paths;
   - sequence map by time/state;
   - visual elements and hierarchy;
   - interaction/state changes;
   - reusable UI/UX patterns;
   - explicit risks and non-proof boundaries.
6. If the user asks to add it to taskpool, create a design/evidence task with source artifacts, claim-vs-evidence separation, non-goals, and expected verification. Prefer a follow-up prototype/design task over a vague “review video later” card.

## Analysis lens

For startup/wake screens and assistant UIs, separate these layers:

- **Wake vs loading**: does the screen say “system not ready” or “persona is waking/listening”?
- **Persona anchor**: name, voice, central symbol, greeting, or identity marker.
- **Ambient state**: listening/thinking/executing/ready feedback via particles, waveform, glow, ticker, or panel status.
- **Mode-specific stage**: news board, mission control, music player, map cockpit, market deck, task radar, etc.
- **Ritual command binding**: short memorable commands whose semantics become visible UI actions.
- **Transition choreography**: how the UI moves from wake screen to functional panel and back.
- **Information hierarchy**: what is centered, what is peripheral, what stays persistent across modes.

## Reusable pattern vocabulary

- **Persona Wake Screen**: a 1–2 second assistant identity state before chat/input appears; usually centered name + living visualizer + status.
- **Mode-specific Stage**: each high-value command opens a dedicated visual stage instead of a generic chat transcript.
- **Ritual Command Binding**: a phrase like “drop the needle” maps to a visible physical/action metaphor such as a tonearm touching a record.
- **Ambient Status over Chat-first**: first impression is presence/status/command center, not only an input box.
- **Evidence-first UI absorption**: absorb the pattern, not the demo’s implied backend or branded skin.

## Example extraction checklist

- [ ] Source link and final URL recorded.
- [ ] Video/note media saved or access boundary stated.
- [ ] Contact sheet and key frames inspected.
- [ ] Startup/wake sequence described separately from functional panels.
- [ ] UI pattern names extracted without copying protected IP.
- [ ] Backend/agent capability claims labeled as unverified unless independently proven.
- [ ] Design note or taskpool card includes evidence paths and non-goals.
