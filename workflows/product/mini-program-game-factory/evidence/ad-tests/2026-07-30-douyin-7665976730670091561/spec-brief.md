# Spec Brief — Reference-ad experimental lane / Stack Path Runner

## Goal

Use the user-supplied Douyin advertisement as immutable test data to exercise and improve `mini-program-game-factory`, then produce an original playable two-level vertical slice whose promise is: Level 1 is a warm-up; completing Level 2 demonstrates skill.

## Non-goals

- No claim that the clip or inferred mechanic is currently hot, ranked, profitable or retained.
- No copying of the source creator's art, audio, exact level geometry, title, copy, colors or proprietary values.
- No Cocos Creator build, Douyin mini-game package, AppID binding, DevTools/device certification, upload or publish claim.
- No ads, payments, login, analytics or external side effects.

## Source facts and boundaries

- User supplied `https://v.douyin.com/7yWAUI9FBl8/`; it resolves to aweme `7665976730670091561`.
- Captured MP4 SHA-256: `0e4c03d6049f29b559e57acf544220803b52ccf15b146b424201cf9f5e64a44d`; 56.935011 s; 576×1024.
- Frames visibly support a collect -> stack grows -> stack is spent across a route/gap loop.
- The source does not prove exact controls, level numbering, failure rules, market rank or platform runtime behavior.
- `reference-ad-observation.json` separates visible facts, inferences and unknowns.

## Business/game rules

1. Automatic forward motion; player steers horizontally.
2. Collectible route cells add exactly one stack unit.
3. Entering a gap atomically reserves its non-negative integer cost. Insufficient units loses before any negative stack state can occur.
4. Obstacles may charge an authored penalty once per obstacle; insufficient units loses.
5. Level 1 is intentionally overfunded and can be completed while centered.
6. Level 2 requires meaningful left/right steering and has two resource checks; no-input play must lose.
7. Completion of Level 1 unlocks Level 2 in the same session; restart is always available.
8. Kernel simulation is deterministic for a fixed level, input trace and timestep sequence.

## Workflow change

Add a candidate-only `reference-ad-experiment` lane:

- accepts a user-authorized reference ad with immutable local digest;
- requires explicit `verified_current_hot=false` and rejects rank claims;
- records visible facts separately from model inference and unknowns;
- requires clean-room reusable/non-copyable boundaries;
- permits deterministic browser vertical-slice experimentation;
- cannot satisfy market-to-kernel freeze, Cocos build, platform, submission or publish gates.

## Negative cases

- Missing/changed media digest -> reject.
- Rank or popularity claim in reference-ad lane -> reject.
- Empty clean-room exclusion list -> reject.
- Level 2 no-input trace wins -> reject.
- Stack goes below zero -> reject.
- A browser smoke is reported as Cocos/Douyin runtime verification -> reject.

## Evidence requirements

- Source MP4, SHA-256, ffprobe metadata and 2-second contact sheet.
- Machine-readable observation and MechanicCard.
- RED then GREEN test output for the reference-ad validator and gameplay kernel.
- Automated kernel tests proving Level 1 no-input win and Level 2 no-input loss plus a winning steering trace.
- Browser readback showing start, Level 1 completion, Level 2 interaction, restart, responsive mobile layout and zero JavaScript console errors.
- Fresh diff/status, focused tests, project tests, independent review and scoped commit.

## Acceptance boundary

A successful result is an original, locally playable browser vertical slice plus an improved, tested candidate-only workflow lane. It remains `creator_build_verified=false`, `platform_ready=false`, and `published=false` until exact external tooling and human/platform evidence are supplied.
