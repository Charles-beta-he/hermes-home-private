# MarkItDown 功能接入任务池 Intake

时间：2026-06-06

## Source identity

- GitHub: https://github.com/microsoft/markitdown
- GitHub full_name: `microsoft/markitdown`
- Description: `Python tool for converting files and office documents to Markdown.`
- Stars at verification: 145,585（约 14.6 万）
- Forks at verification: 9,970
- Default branch: `main`
- Primary language: Python
- License: MIT License
- PyPI package: `markitdown`
- PyPI version observed: `0.1.6`
- Python requirement: `>=3.10`
- PyPI project URLs: Source / Issues / Documentation all point to the official GitHub repo.

## Source surface snapshot

Top-level repo layout observed through GitHub API:

- `README.md`
- `LICENSE`
- `SECURITY.md`
- `SUPPORT.md`
- `CODE_OF_CONDUCT.md`
- `Dockerfile`
- `packages/`
- `.github/`
- `.devcontainer/`

README-supported conversion surfaces:

- PDF
- PowerPoint
- Word
- Excel
- Images: EXIF metadata and OCR
- Audio: EXIF metadata and speech transcription
- HTML
- Text formats: CSV, JSON, XML
- ZIP files: iterate over contents
- YouTube URLs
- EPUBs
- more formats through optional dependencies/plugins

Install/use signals:

- CLI: `markitdown path-to-file.pdf > document.md`
- CLI output option: `markitdown path-to-file.pdf -o document.md`
- Python API: `from markitdown import MarkItDown; MarkItDown().convert("test.xlsx")`
- PyPI install: `pip install 'markitdown[all]'` or targeted extras such as `markitdown[pdf, docx, pptx]`
- Plugins disabled by default; `--use-plugins` opt-in.
- MCP package exists: `markitdown-mcp`, exposing `convert_to_markdown(uri)` over STDIO / localhost HTTP / SSE.

## Security / red-line signals

MarkItDown README explicitly warns:

- It performs I/O with the privileges of the current process.
- Inputs must be sanitized in untrusted environments.
- Prefer the narrowest conversion API needed, e.g. `convert_stream()` / `convert_local()`.

MarkItDown-MCP README warns:

- MCP server is meant for local trusted agents.
- HTTP/SSE binds to localhost by default.
- Do not bind to non-localhost unless security implications are understood.
- The tool can read files/network resources accessible to the server process.

## Existing Hermes context

There is an existing completed task:

- `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-30-评估liteparse作为markitdown替代方案的可行性.md`

That task evaluated LiteParse as a MarkItDown alternative and recorded a conservative fallback stance: keep MarkItDown as default unless a measured replacement proves better. The new task should therefore focus on a guarded MarkItDown integration as a baseline document-ingestion capability, not on replacing it.

## Taskpool classification

- lane: `evolution`
- priority: `P2`
- priority_layer: `P2`
- project: `hermes-agent`
- architecture_target: `local-brain`
- multimodel_triage_result: `advisory`
- dependency_order: `0`
- parallel_boundary: `hermes-agent:local-brain:document-ingestion:markitdown`

Rationale: this is a concrete Hermes capability task: add/plan a safe document-to-Markdown ingestion path for local brain / RAG / evidence workflows, using MarkItDown as the default baseline and preserving security boundaries.

## Acceptance evidence expectation

A future worker should produce:

1. Source-review artifact: official repo, license, PyPI, supported formats, security warnings verified.
2. Architecture decision: CLI wrapper vs Python API vs MCP server; prefer least-privilege/local-only path.
3. Minimal integration slice: convert local trusted PDF/DOCX/XLSX/PPTX/HTML/text fixture to Markdown under a sandbox/workdir, with no broad filesystem/network read.
4. Security gate: explicit allowlist/sandbox path, plugin disabled by default, MCP non-localhost forbidden unless separately approved.
5. Regression tests or deterministic smoke proofs: fixture conversion output exists and preserves key structure; failure modes are explicit.
6. A/B context: reference existing LiteParse comparison and keep MarkItDown default unless benchmark evidence says otherwise.

## Anti-drift checks

- Do not auto-install or run third-party code during intake.
- Do not expose MarkItDown-MCP beyond localhost.
- Do not enable plugins by default.
- Do not let conversion tools read arbitrary paths; require explicit local file/sandbox allowlist.
- Do not claim replacement of LiteParse or other parsers without measured A/B evidence.
- Do not treat Markdown output as high-fidelity human document rendering; README positions it for LLM/text-analysis pipelines.
