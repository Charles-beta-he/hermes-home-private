# WeChat Channels intake: Alibaba Open Code Review

Date: 2026-07-01
Source link: https://weixin.qq.com/sph/A2NMvhXr6r
Resolved preview URL: https://channels.weixin.qq.com/finder-preview/pages/sph?id=A2NMvhXr6r
Attached screenshot: /Users/charles/.hermes/images/clip_20260701_143210_3.png

## Access boundary

- Public preview metadata and cover frame were accessible.
- Full video playback is QR/App gated: page shows “可扫码前往微信观看此内容”.
- Browser DOM exposed caption, author, date, engagement counts, cover image, and preview text.
- Attached screenshot is a Hermes terminal/MCP reload state, not the video frame.
- This report does not claim full-video transcription; it analyzes public preview facts plus directly verified external artifacts.

## Public preview facts

Author: 林夕AI研究所
Location wording: 苏州市
Preview date: 2026-06-13
API createtime: 1781309251 = 2026-06-13T00:07:31Z
Engagement shown in DOM/API:
- favCountFmt: 215
- forwardCountFmt: 1101
- likeCountFmt: 92
- commentCountFmt: 12

Caption/description:

> 阿里王炸开源！内部用两年的 AI 代码审查 Agent 放出来了
>
> 太狠了！阿里把内部实战两年的 AI 代码审查工具正式开源，项目上线 25 天狂揽 6.4k Star！
> 项目名叫 Open Code Review，前身是阿里内部官方代码审查助手，两年服务数万开发者，累计识别数百万代码缺陷。
> 针对性解决普通 AI 审查三大痛点：覆盖不全、位置漂移、输出质量不稳定。
> 不再简单丢代码 diff 给大模型，直接做成可约束、可并发、能接入 CI 的全自动审查流水线，程序员效率直接拉满！
>
> #阿里开源 #代码审查 #AI 编程 #程序员 #开发工具 #AI Agent

Visible cover OCR from browser vision:
- “阿里开源内部 AI Code Review”
- “25 天 6.4k Star”
- QR modal partially blocks lower cover text.

## Verified external artifact

Repo: https://github.com/alibaba/open-code-review
Package: https://www.npmjs.com/package/@alibaba-group/open-code-review
Official site: https://alibaba.github.io/open-code-review/

GitHub API readback on 2026-07-01:

- full_name: alibaba/open-code-review
- description: Open-source & free — Battle-tested at Alibaba's scale. Hybrid architecture code review tool: deterministic pipelines + LLM Agent, precise line-level comments, built-in fine-tuned ruleset (NPE, thread-safety, XSS, SQL injection), OpenAI & Anthropic compatible.
- stars: 9703
- forks: 630
- open issues: 44
- default branch: main
- language: Go
- license: Apache-2.0
- created_at: 2026-05-18T02:16:36Z
- pushed_at: 2026-07-01T06:33:12Z
- latest observed commit: 52a51f86f8860b8e7128fa2dcd52291174dd287c
- latest observed commit message: test(diff): add tests for gitignore pattern matching and mode getters

Root inventory includes:
`.claude-plugin`, `.claude`, `.github`, `ASSURANCE_CASE.md`, `GOVERNANCE.md`, `LICENSE`, `Makefile`, multilingual README files, `ROADMAP.md`, `SECURITY.md`, `bin`, `cmd`, `examples`, `extensions`, `go.mod`, `install.sh`, `internal`, `npm`, `package.json`, `pages`, `plugins`, `scripts`, `skills`.

NPM registry readback:

- name: @alibaba-group/open-code-review
- latest: 1.6.6
- description: OpenCodeReview CLI — AI-powered code review tool
- license: Apache-2.0
- bin: `ocr` -> `bin/ocr.js`
- unpackedSize: 1756422
- latest publish time: 2026-06-30T05:48:53.768Z

## Verified README claims

The README confirms:

- It originated as Alibaba Group's internal official AI code review assistant.
- It reads Git diffs, sends changed files to a configurable LLM via an agent with tool-use capabilities, and generates structured line-level comments.
- It supports full-file scan via `ocr scan`.
- It positions itself as deterministic engineering plus agent hybrid.
- Compared to general-purpose agents, it claims higher precision/F1, about 1/9 token use, faster reviews, and lower recall as an intentional precision/noise trade-off.
- Benchmark source claim: 50 repositories, 200 real PRs, 10 languages, 80+ senior engineers, 1,505 annotated ground-truth issues.
- Problem framing matches preview: incomplete coverage, position drift, unstable quality.
- Deterministic pieces: precise file selection, smart bundling, rule matching, positioning/reflection modules.
- Agent pieces: scenario-tuned prompts and code-review-specific toolset.

Security assurance notes from `ASSURANCE_CASE.md`:

- Threat boundaries: Git repo/diffs, LLM provider API, local output, local web viewer.
- Mitigations include no shell expansion, API keys from env only, TLS, schema validation, line bounds checking, path validation, host-header allowlist, govulncheck/Dependabot.

## Judgment

This is materially stronger than “put diff into a general LLM reviewer.” Its reusable insight for Hermes is not the CLI install itself; it is the architecture pattern:

Deterministic review control plane + bounded specialist agent + exact line/comment projection + reflection/positioning verifier + CI-friendly output.

For Hermes, this should influence `requesting-code-review` and future taskpool review gates. It should not be globally installed or enabled from a video preview.

## Hermes adaptation plan

1. Patch `requesting-code-review` with an Open Code Review reference pattern:
   - coverage manifest before review;
   - file bundling for large diffs;
   - line-position verification after model review;
   - reflection pass to filter low-confidence comments;
   - precision/recall trade-off made explicit;
   - CI output compatibility as a separate gate.
2. Keep current independent reviewer subagent pipeline for now; do not replace it with OCR.
3. Create a bounded evaluation card for optional OCR CLI spike:
   - local temp repo only;
   - no global npm install;
   - no API key entry by agent;
   - use fixture diffs and mock/fake endpoint if possible;
   - compare output coverage, line positions, token/cost estimate, and false positives.
4. If later approved, integrate as an optional validator adapter, not as a mandatory global reviewer.

## Anti-claims / boundaries

- Public preview did not expose full video playback.
- Video’s “6.4k stars in 25 days” was time-scoped; current verified stars are 9703.
- Benchmark claims are from project README; not independently reproduced here.
- No package installed, no API key used, no CI integration changed.
- No external code copied into Hermes runtime.
