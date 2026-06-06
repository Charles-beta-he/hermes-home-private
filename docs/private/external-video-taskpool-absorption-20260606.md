# External video/repo absorption notes — 2026-06-06

## Source A: GitHub Spec Kit

- User intent: add taskpool absorption; explicitly not UVISA-specific.
- Canonical repo: https://github.com/github/spec-kit
- Live evidence inspected:
  - Repo clone HEAD: `7106858` from `/tmp/spec-kit`
  - Latest release via GitHub API: `v0.9.5`, published `2026-06-05T17:40:04Z`
  - GitHub API snapshot: ~109k stars, ~9.6k forks, MIT license
  - README workflow: `/speckit.constitution` → `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`, plus `/speckit.clarify`, `/speckit.analyze`, `/speckit.checklist`
  - Templates inspected: `templates/spec-template.md`, `templates/plan-template.md`, `templates/tasks-template.md`
  - Hermes integration inspected: `src/specify_cli/integrations/hermes/__init__.py`

### Transferable mechanisms for Hermes taskpool

1. Spec-first artifact chain: `spec.md` → `plan.md` → `tasks.md` → `quickstart.md` / contracts.
2. User-story slices with P1/P2/P3 priority and independent acceptance tests.
3. Task format with phase dependencies and `[P]` parallel markers.
4. Constitution / checklist / analyze gates before implementation.
5. Agent integration registry pattern, including existing Hermes skills integration.

### Hermes landing boundary

- Landing zone: `taskpool` + `local-brain` workflow governance.
- Non-goal: do not turn this into a UVISA-only preset or project-specific POC.
- First slice: a read-only/dry-run importer that maps Spec Kit artifacts into Hermes `TaskContract` + taskpool metadata.
- Red line: no duplicate SSOT; Spec Kit artifacts must be upstream inputs, while Hermes task records/evidence remain execution SSOT.

## Source B: WeChat video — TurboVec / TurboQuant

- User source: `https://weixin.qq.com/sph/AeI1dvNsAf`
- Browser-resolved page: `https://channels.weixin.qq.com/finder-preview/pages/sph?id=AeI1dvNsAf`
- Visible video text: `炸裂！谷歌开源神器，31GB 内存直接压成 4GB，跑 AI 向量搜索再也不怕爆显存，省出 16 倍空间`
- Author visible: `GeekTech`
- Cover OCR: `turbovec`, `Google's TurboQuant for vector search`
- Canonical repo identified: https://github.com/RyanCodrai/turbovec
- Repo clone HEAD: `efe29a1` from `/tmp/turbovec`
- GitHub API snapshot: ~4.6k stars, MIT license, Rust + Python bindings

### Transferable mechanisms for Hermes local-brain

1. TurboQuant-based vector compression: README claims 10M document corpus can compress from 31GB FP32 to 4GB at 4-bit.
2. Local-only vector index with Rust core and Python bindings.
3. Stable external ids through `IdMapIndex` and persisted index files.
4. Search-time allowlist filtering suitable for tenant/project/time-window gating.
5. Framework integrations for LangChain/LlamaIndex/Haystack/Agno.

### Hermes landing boundary

- Landing zone: `local-brain` retrieval/memory index evaluation, not UVISA.
- First slice: benchmark/evaluate against Hermes local-brain retrieval needs with a redacted/synthetic corpus; no private notes indexing during intake.
- Red line: do not install/run third-party code on private brain data without explicit approval and redaction boundary.

## Source C: WeChat video — Horizon/Trending self-evolving knowledge pipeline

- User source: `https://weixin.qq.com/sph/Ahn8Q05Lc1`
- Browser-resolved page: `https://channels.weixin.qq.com/finder-preview/pages/sph?id=Ahn8Q05Lc1`
- Visible title/body: `Horizon/Trending 每天自动获取最新知识，ai每天蒸馏方法论,每天基于方法论输出我们需要的数字资产 #知识库 #自进化 #自成长 #ai工具`
- Author visible: `AI樟榆树`
- Date visible: `2026年6月6日`
- Cover OCR: `让知识库自进化`, `Horizon/Trending`, `每天自动抓取`, `知识库每天蒸馏方法论`, `每天基于方法论输出数字资产`
- Repo/source status: no canonical public GitHub repo identified from exact title/search at intake time; treat as a workflow/pattern signal, not a verified open-source project.

### Transferable mechanisms for Hermes local-brain / taskpool

1. Daily source acquisition: curated trending/news/repo inputs become governed candidate signals, not raw feed dumps.
2. Methodology distillation: repeated source patterns are converted into reusable methods/skills/templates/checklists.
3. Asset generation: distilled methods produce durable digital assets such as skills, taskpool tasks, reference notes, eval fixtures, scripts, or report templates.
4. Feedback loop: assets are validated by selfcheck/proof gates and later task outcomes, then promoted/archived.
5. Boundary: this is a class-level pipeline design signal, not evidence that the named Horizon/Trending implementation is available or safe.

### Hermes landing boundary

- Landing zone: `local-brain` + `feeds` + `taskpool` + `skill-graph` pipeline governance.
- First slice: design a governed `source signal -> method atom -> generated asset -> verification -> promotion` pipeline using existing Hermes primitives.
- Red line: do not auto-install unknown Horizon/Trending code, do not indiscriminately ingest all trending items, and do not let generated assets bypass evidence/proof gates.
