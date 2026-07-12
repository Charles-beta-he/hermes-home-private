# Cartoon Technical Infographic Reference

Use this reference when the user provides a cartoon architecture/workflow image and asks for a same-style generated diagram.

## Visual DNA

A cartoon technical infographic usually has:

- cream/white background with light decorative blobs, not a dark grid
- thick black strokes around every module and icon
- chunky rounded rectangles, stickers, badges, and cloud shapes
- high-saturation but friendly colors: cyan, lime, lavender, pink, yellow, teal
- playful icons embedded in modules, not just labels
- large numbered circles for step order
- thick curved arrows, often with oversized arrowheads
- bottom conveyor/event belt for protocols or lifecycle streams
- handwritten/rounded font direction
- dense teaching-poster composition while keeping labels short

## Architecture mapping recipe

For an agent-scheduler/system diagram:

1. Left: user/device/chat entry card.
2. Next: gateway/API card with 2-3 endpoint pills.
3. Lower-left or middle: registry/profile/skills card.
4. Center: large cloud brain for graph scheduler.
5. Near cloud: compass/router card for intent routing.
6. Right: vertical adapter stack, optionally with small robot.
7. Far-right/lower-right: external services/API/files card.
8. Bottom: conveyor belt for unified request/event protocol.
9. Overlay: shield/guard for side-effect/authority gates.

## Label guidance

Keep text short and poster-readable:

- `Human / UI 入口`
- `Gateway / API`
- `CapabilityRegistry`
- `Capability Graph 调度脑`
- `IntentRouter`
- `Tool Adapter`
- `External`
- `Unified Event Belt`

For event belts, use compact sequence labels:

```text
InvokeRequest → ROUTE → TOOL_CALL → MESSAGE → CITATION → ERROR → RECEIPT → DONE
```

## SVG/manual rendering tips

- Use bold strokes (`stroke-width` around 4-6 for cards, 6-9 for arrows).
- Use drop shadows with hard cartoon offset, not soft enterprise shadows.
- Keep background texture subtle; too much noise makes text unreadable.
- If exact Chinese text matters, prefer SVG/HTML over generative image text.
- If image generation is available, use the reference image and explicitly say “cartoon technical infographic, thick black outlines, rounded colorful cards, playful icons, cloud brain, conveyor belt.”

## Acceptance failure response

If the user says “not this style,” do not argue. Respond by naming the mismatch and regenerating:

```text
你说得对：我把它做成了 dark/whiteboard/flat style，但参考图是 cartoon technical infographic。重新按卡通信息图风格生成。
```

Then regenerate and verify visually.
