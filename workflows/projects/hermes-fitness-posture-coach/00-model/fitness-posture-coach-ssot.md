# Hermes Fitness Posture Coach — SSOT

Created: 2026-07-03T12:12:40+08:00

## Objective model

**Goal:** build a self-use fitness posture / exercise-coach capability on top of the existing `visual-conversation-core` pattern. First usable value is: action catalog + camera coaching + low-risk posture analysis contract. Later runtime can attach phone/webcam/glasses frame input.

**Success criteria for current landing:**
- Project has profile + SSOT + contract + roadmap + evidence index + progress ledger.
- The Douyin/GitHub action-library lead is preserved as evidence, but social claims are separated from upstream truth.
- A local metadata seed is reproducibly built from the verified GitHub dataset.
- Production/commercial/media/licensing claims remain closed.

**Constraints / non-goals:**
- Self-use only; not commercial distribution.
- No diagnosis, rehab prescription, or injury treatment.
- No heavy-load or pain-state coaching without stop/confirm behavior.
- No invented images/GIFs; upstream media is not bundled.
- No default-on camera/mic/background upload.

## Situation model

Source lead: Douyin video `7657474429714189620` from Tony讲实话 points to `hasaneyldrm/exercises-dataset`.

Verified artifact: `https://github.com/hasaneyldrm/exercises-dataset`.

Useful as **exercise content/taxonomy seed**:
- 1,324 exercise records.
- Category/body part/equipment/target/muscle group style fields.
- Multilingual instructions including Chinese.

Not a posture-analysis model:
- No keypoint detector.
- No rep/phase segmentation.
- No form scoring or safety rules.
- No included media assets according to README.

## Chosen path

A over B/C:

- **A — local SSOT + metadata seed + contract first**: reversible, evidence-backed, immediately useful for self-use and later runtime integration.
- B — directly build a full app: too much surface before pose/safety contracts are grounded.
- C — only add taskpool cards: tracking without usable artifact.

## Owned product language

`Hermes Fitness Posture Coach` is an owned local capability pack for:
1. choosing/understanding exercises;
2. camera setup guidance;
3. low-risk posture/form cues from pose evidence;
4. short spoken coaching and overlay contract.

It is not a medical device, not a commercial exercise-media library, and not an automatic personal trainer.
