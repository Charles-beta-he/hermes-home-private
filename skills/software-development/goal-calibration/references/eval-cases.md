# Goal Calibration Eval Cases

Use these as routing and behavior regression examples for the `goal-calibration` skill.

## Positive triggers

1. “下拉框对齐一下。”
   - Expected: calibrate dimensions before implementation: visual, interaction, options, state, business linkage, payload/read-back.
   - Do not assume CSS-only.

2. “按原型把通知态补齐。”
   - Expected: treat prototype as UX/effect spec; audit observable effects; map missing business facts vs frontend visual/CTA mapping.
   - Do not require backend display fields just because prototype mock data has them.

3. “优化这个 prompt。”
   - Expected: calibrate target behavior, positive/negative cases, output contract, failure modes, verification.
   - Do not merely polish wording.

4. “这个页面感觉不对，修一下。”
   - Expected: identify baseline (prototype/design system/sibling/live), expand into visual/interaction/data/state dimensions, then act or ask if baselines conflict.

5. “让 agent 以后别误判这种目标。”
   - Expected: self-optimization path: classify learning, update memory/skill/norm/proposal as appropriate, verify and commit scoped Hermes changes.

6. “把旧版这个功能迁到新版。”
   - Expected: decide whether target is UX/effect parity, business behavior parity, contract parity, or structure parity; do not copy old implementation structure blindly.

## Negative / light-path cases

1. “把按钮文案从 Submit 改成 Continue。”
   - Expected: exact scoped edit; no heavy goal calibration unless context reveals broader behavior.

2. “现在几点？”
   - Expected: use time/date tool or terminal per mandatory tool rule; no goal calibration.

3. “运行 npm test 并告诉我结果。”
   - Expected: run command; no clarification unless project context is missing and unretrievable.

4. “读取 /tmp/a.txt 第 20 行。”
   - Expected: read exact file/line; no calibration.

5. “计算 123*456。”
   - Expected: use calculator/terminal; no calibration.

## Neighbor-skill boundaries

- If the task is a bug with concrete failure and stack trace, load systematic-debugging after light goal calibration.
- If the task is a project audit with docs/prototype/live implementation, load project-evidence-grounding after goal calibration.
- If the task is API contract design, load api-and-interface-design after goal calibration.
- If the task is Hermes self-optimization, load agent-boundary-audit and hermes-agent after goal calibration.

## Failure checks

A response fails this eval set if it:

- treats ambiguous UX language as a single CSS edit without checking hidden dimensions
- copies prototype mock fields as API contract without effect mapping
- asks broad open-ended “what is your goal?” when context already implies a dominant baseline
- optimizes a prompt only for surface wording
- verifies only the touched layer instead of the calibrated target
