# Douyin 图文：淬念阁 SKILL 完整架构 intake

Captured: 2026-06-14

## Source

Original share:
> 1.23 复制打开抖音，看看【老韩的图文作品】淬念阁 · SKILL 完整架构。淬念阁是我目前最... https://v.douyin.com/OkuLE6wWcrk/ t@R.kP :7pm 05/19 IIi:/

Resolved:
- short: https://v.douyin.com/OkuLE6wWcrk/
- share: https://www.iesdouyin.com/share/note/7649440117685341476/?from_ssr=1
- canonical: https://www.douyin.com/note/7649440117685341476

Metadata:
- aweme_id: `7649440117685341476`
- author: `老韩`
- signature: `在职产品经理，闲暇时间做AI探索，分享思考`
- create_time: 2026-06-10
- stats at capture: 928 likes, 1291 collects, 184 shares, 19 comments
- images_count: 7
- evidence dir: `/Users/charles/.hermes/docs/private/douyin-cuinian-skill-architecture-7649440117685341476/`

## Main claim

The post presents `淬念阁` as a pre-thinking / problem-clarification skill. It solves a common AI collaboration failure: starting work before the problem is clear, then repeatedly changing direction and making the output worse.

The skill is not supposed to make decisions for the user. It helps the user clarify thinking, produce structured options, and preserve a process artifact.

## OCR summary of architecture

### Function definition

Visible YAML:
- `name: quench-think`
- `description`: pre-structured thinking; classify fuzzy user problems,回溯经验, search external references, match thinking models by depth, then output an integrated proposal and write process files.
- Thinking models live in `思考模型/` and are read on demand.

Core rule:
- After each stage output, wait for user confirmation before continuing, unless the user says `全自动`.

### Seven-stage flow

0. Define the problem / 定义问题
   - Start by asking back, not directly executing.
   - Confirm: type (decision/creative/analysis/planning/diagnosis), boundary/scope, expected output.
   - Output: problem definition card.
   - If user cannot classify, ask what the most tangled point is.
   - If user says everything is included, recommend focusing one topic first.
   - Analysis/diagnosis questions cannot skip knowledge-base retrieval even in full-auto mode.

1. Recall historical experience / 回溯经验
   - Load knowledge-base skill.
   - Search by stage-0 keywords.
   - If matched, show similar past case, prior solution, and effect.
   - If no match, record no historical reference.
   - If knowledge-base loading fails: non-analysis tasks can continue with gap marked; analysis/diagnosis must pause.

2. External reference / 外部参考
   - Ask whether to search public materials or open-source projects.
   - If yes, use web search/fetch and extract reusable methods.
   - If timeout: ask retry / skip / user supplies reference.
   - If irrelevant: mark external no reference.

3. Decide depth and route thinking models / 定深度+选模型
   - Problem types: decision, creative, analysis, planning, diagnosis.
   - Depths: quick, standard, deep.
   - Routes visible:
     - Decision: six hats; six hats + SWOT; six hats + SWOT + Socratic.
     - Creative: first principles; first principles + pyramid; first principles + pyramid + IEE/Socratic.
     - Analysis: critical thinking; critical + Socratic; critical + Socratic + SWOT + six hats.
     - Planning: pyramid; pyramid + reverse; pyramid + reverse + SWOT + Socratic.
     - Diagnosis: 5Whys; 5Whys + Socratic; 5Whys + Socratic + critical + first principles.
   - Output three directions: aggressive, conservative, balanced; each includes depth, model combination, fit and risk.
   - Ask which direction or combination the user prefers.
   - After confirmation, optionally remember depth/model preference into project config.

4. Per-model thinking / 逐模型思考
   - For each model: read its `思考模型/{model}.md`, bring in the stage problem and accumulated information, output by that model's steps.
   - Stop after output and ask whether to continue to next model.
   - If user asks about a sub-step, deepen only that step.
   - If stuck, offer rollback / switch model / skip.
   - If reasoning loops, stop: path has no new progress.
   - In `全自动` mode, no per-model confirmation, but stuck/loop still interrupts.
   - Available models include Socratic, Six Hats, Pyramid, 5Whys, First Principles, SWOT, Reverse, Critical Thinking.

5. Integrated output / 综合产出
   - Includes a self-check block:
     1. Does every conclusion have traceable evidence?
     2. Are inferred items marked with medium/low confidence?
     3. Are assumptions requiring user validation listed?
   - Output one-sentence conclusion, supporting reasons with sources and confidence, discarded directions, assumptions to verify, and recommended next step.
   - If contradictions exist, preserve them instead of forcing a single answer.

6. Process file / 沉淀过程文件
   - Ask for path; default `{project_root}/{question_summary}_prethink_{date}.md`.
   - Write all stage outputs in UTF-8 without BOM.
   - Sections: problem definition, historical experience, external reference, thinking process per model, integrated conclusion.
   - If path missing, fall back to Desktop. If file exists, append `_2` instead of overwriting.

### Exception branch summary

- Knowledge-base load failure: non-analysis skip with gap; analysis/diagnosis pause.
- Search timeout: ask retry/skip/manual reference.
- Search irrelevant: mark and continue.
- Model step stuck: pause, offer rollback/skip/switch model.
- Reasoning loop: interrupt.
- Path write failure: write to Desktop working path.
- User says rollback: return to previous confirmation point.
- User says terminate: write produced content to process file.
- User says full-auto: later stages no per-step confirmation, but stuck still interrupts.

### Experience iteration

After each run append to `经验/迭代记录.md`:
- date + problem summary
- type/depth
- models used
- total confirmation rounds
- whether exception occurred
- output quality/user feedback

Every 20 entries archive into `经验/archive/`.

## Interpretation for Hermes

This is directly relevant to Hermes' `goal-calibration` and user-dialogue requirements refinement.

Strong transferable patterns:
1. Treat fuzzy user asks as pre-thinking tasks before execution.
2. Split clarification into type, boundary, and expected output.
3. Use staged confirmation, but allow explicit `全自动` with stuck/loop interrupts.
4. Route thinking models by problem type and depth instead of always using every framework.
5. Keep evidence provenance: historical memory, external references, and model-derived reasoning are distinct sources.
6. Self-check every conclusion with evidence traceability, confidence marking, and assumptions needing validation.
7. Persist a process artifact for multi-session continuity.
8. Track effectiveness and evolve after enough cases.

Limitations / anti-drift:
- The Douyin post is a social-source skill screenshot, not a validated canonical implementation.
- It should not make Hermes ask too many questions by default. Hermes should keep the existing act-don't-ask rule: ask only when ambiguity changes the work.
- Multi-model/framework routing should support the user's task, not become ritualized overhead.
- Process file writing should be used for complex work, not every tiny chat.

Recommended absorption:
- Evaluate a targeted enhancement to Hermes `goal-calibration`: add staged prethink pattern for medium/high ambiguity tasks, model-routing by task type/depth, contradiction preservation, and process artifact schema.
- Do not replace existing goal-calibration; map this as a richer mode for product/design/strategy/creative ambiguity.
