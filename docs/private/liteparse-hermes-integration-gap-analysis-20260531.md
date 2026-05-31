# LiteParse → Hermes document parsing gap analysis (2026-05-31)

Task: `2026-05-30-分析-run-llama-liteparse-文档解析器并评估-hermes-集成潜力`

## Evidence boundary

This is a grounded reference-repo analysis, not implementation proof for a Hermes parser integration.

Live source inspected without cloning or installing dependencies, per task boundary:

- GitHub repository API: `https://api.github.com/repos/run-llama/liteparse`
- Repo: `run-llama/liteparse`
- Default branch: `main`
- Inspected commit: `cf9f08fe89a2b63478dece44f0a0c0030261ae85`
- Commit date: `2026-05-30T05:55:42Z`
- Tree API result: 226 entries, `truncated=false`
- Local evidence cache: `/tmp/agent-team-2026-05-30-分/liteparse-live/`

Fetched evidence files and short hashes:

- `README.md` sha256 prefix `1344951eda67`
- `Cargo.toml` sha256 prefix `88712e3ccdc5`
- `crates/liteparse/Cargo.toml` sha256 prefix `e88cb5099cf4`
- `crates/liteparse/src/lib.rs` sha256 prefix `f5f4c5e74720`
- `crates/liteparse/src/parser.rs` sha256 prefix `73edc73a42dd`
- `crates/liteparse/src/config.rs` sha256 prefix `fa90460765c3`
- `crates/liteparse/src/types.rs` sha256 prefix `7066faae9239`
- `crates/liteparse/src/search.rs` sha256 prefix `aa14980f1ede`
- `crates/liteparse-napi/Cargo.toml` sha256 prefix `144e413968e5`
- `crates/liteparse-napi/src/lib.rs` sha256 prefix `8dd2b0c6ed93`
- `crates/liteparse-python/Cargo.toml` sha256 prefix `fb0ab09d070a`
- `crates/liteparse-python/src/lib.rs` sha256 prefix `eef87e3e8da7`
- `crates/liteparse-wasm/Cargo.toml` sha256 prefix `61e3f1d7fad1`
- `crates/liteparse-wasm/src/lib.rs` sha256 prefix `24ba238f07f6`
- `packages/python/pyproject.toml` sha256 prefix `2307c06fb274`
- `packages/node/package.json` sha256 prefix `52a145de32fa`
- `packages/wasm/package.json` sha256 prefix `1575f220bcb1`
- `.github/workflows/ci.yml` sha256 prefix `fded12d2b451`

Hermes current file-reading evidence:

- `/Users/charles/.hermes/hermes-agent/tools/file_tools.py:1147-1155` defines `read_file` as text-only line-numbered pagination and explicitly says it cannot read images or binary files.
- `/Users/charles/.hermes/hermes-agent/tools/file_tools.py:522-531` blocks binary extensions before reading.
- `/Users/charles/.hermes/hermes-agent/tools/file_operations.py:716-806` reads text via `sed`, line counts via `wc`, and redirects images to vision instead of parsing them as documents.
- `/Users/charles/.hermes/hermes-agent/tools/file_operations.py:764-774` samples bytes and blocks likely-binary content.

## 1. Architecture extracted from liteparse

LiteParse is a Rust-first PDF/document parser with a core crate and thin language bindings.

### Rust workspace shape

Root `Cargo.toml` declares a workspace with these members:

- `crates/pdfium-sys`
- `crates/pdfium`
- `crates/liteparse`
- `crates/liteparse-napi`
- `crates/liteparse-python`
- `crates/liteparse-wasm`

The core crate (`crates/liteparse`) exposes:

- `LiteParseConfig`, `OutputFormat` from `config.rs`
- `LiteParse`, `ParseResult`, `ScreenshotResult` from `parser.rs`
- `ParsedPage`, `TextItem` from `types.rs`
- OCR modules and search helpers

Important parser flow from `crates/liteparse/src/parser.rs`:

1. Validate/resolve input as a PDF or convert supported non-PDF inputs to PDF on non-WASM targets.
2. Parse target page ranges from config (`target_pages`).
3. Extract PDF text using PDFium.
4. Optionally render pages for OCR.
5. Select OCR engine: HTTP OCR server if configured; otherwise Tesseract if the feature is enabled; WASM requires caller-provided OCR callback.
6. Merge OCR results with native text.
7. Project extracted page items into a grid/layout representation.
8. Return `ParseResult { pages, text }`.

Configuration (`config.rs`) includes:

- `ocr_language`
- `ocr_enabled`
- `ocr_server_url`
- `max_pages`
- `target_pages`
- `dpi`
- `password`
- `output_format`
- `num_workers`

Data model (`types.rs`) includes page-level and text-item structures with spatial metadata such as bounding boxes and OCR confidence.

### Binding pattern: napi-rs + PyO3 + wasm-bindgen

LiteParse uses the standard Rust-core/multi-binding pattern:

- Node/TypeScript native binding:
  - Crate: `crates/liteparse-napi`
  - `crate-type = ["cdylib"]`
  - Dependencies: `napi`, `napi-derive`, `napi-build`
  - Exposes `LiteParse` class and async `parse()` accepting file path or bytes.
  - Package: `packages/node/package.json` (`@llamaindex/liteparse`) builds via `napi build --cargo-cwd ../../crates/liteparse-napi`.

- Python native binding:
  - Crate: `crates/liteparse-python`
  - `crate-type = ["cdylib"]`
  - Dependency: `pyo3 = { version = "0.28", features = ["extension-module"] }`
  - Package: `packages/python/pyproject.toml` uses `maturin` with `module-name = "liteparse._liteparse"` and bundles platform PDFium libraries.
  - Python class wraps Rust async work through a Tokio runtime and exposes `parse`, `parse_bytes`, screenshot, config, and helper functions.

- Browser/WASM binding:
  - Crate: `crates/liteparse-wasm`
  - `crate-type = ["cdylib", "rlib"]`
  - Dependencies: `wasm-bindgen`, `wasm-bindgen-futures`, `serde-wasm-bindgen`
  - Exposes a JS `LiteParse` class and `searchItems`; accepts PDF bytes in browser contexts.
  - WASM OCR depends on a JS callback object; no built-in OCR engine is available there.

### Capabilities observed

Grounded capabilities from README/source:

- Fast PDF parsing using PDFium.
- Spatial text extraction with bounding boxes.
- Page-level layout projection to text.
- Optional OCR for text-sparse pages / images via Tesseract or HTTP OCR server.
- Targeted page selection and max-page limits.
- Parse local file paths and raw PDF bytes.
- Screenshot/render pages as PNG bytes on non-WASM targets.
- Non-PDF conversion path depends on external system tools: LibreOffice for office documents and ImageMagick for images.
- Search helper that merges adjacent text items for phrase-like matches.

## 2. Mapping to Hermes primitives and gaps

### Current Hermes primitives

Hermes already has these relevant primitives:

- `read_file`: safe text read with pagination, line numbers, dedup guards, binary/image block, internal path denylist.
- `read_media_file` / `vision_analyze`: image/media handling through separate vision channel.
- `terminal`: can invoke external CLIs, but should not be the primary document ingestion path because permission/proof gates and command execution risks are broader than a purpose-built parser tool.
- Tool registry/tool schemas: `tools/*.py` register functions and schemas that route through `model_tools.py`.
- File permission/read guards: existing path resolution, binary extension denylist, internal Hermes path protection, and cross-profile write guards.
- Context/token safeguards: `read_file` pagination, duplicate-read blocking, output limits, and token compression.

### Capability delta vs current Hermes file reading

| Area | Current Hermes `read_file` | LiteParse capability | Delta |
|---|---|---|---|
| Plain text | Strong: paginated line-numbered reads | Not the core target | No need to replace current path |
| PDF text | Treated as binary and blocked | Extracts text with page layout | Major gap |
| Spatial metadata | None | Bounding boxes, pages, dimensions, OCR confidence | Major gap for citation/QA |
| Office documents | No direct parse; user must convert externally | Converts through LibreOffice to PDF before parse/render | Potential gap, but depends on external tools |
| Images/scanned docs | Routed to vision, not structured doc parser | ImageMagick conversion + OCR path, Tesseract/HTTP OCR | Potential gap with dependency risk |
| Page selection | Text-line offsets only | `target_pages`, `max_pages` | Better for documents |
| Output control | Line windows, total lines | text/json structured result | Need Hermes truncation/schema wrapper |
| Safety | Mature Hermes path guards | Library accepts paths/bytes | Must wrap with Hermes guards before invocation |
| Install footprint | Pure Python/shell path | Rust native library + PDFium; optional Tesseract/LibreOffice/ImageMagick | High distribution risk |

### Gaps before adoption

1. Dependency footprint: LiteParse likely adds Rust/native wheel and PDFium runtime concerns. OCR/office/image support needs optional external programs/services.
2. Permission boundary: Hermes must not let a parser tool bypass existing read guards, binary guards, internal denylist, workspace permissions, or task envelope constraints.
3. Output/token boundary: parse results can be huge. Hermes needs deterministic page/char/item caps and summary modes before exposing to the agent loop.
4. Trust boundary: PDF parsing is untrusted binary document handling. Running in-process inside the main agent process increases blast radius; a subprocess/sandbox wrapper is safer.
5. Platform coverage: macOS/Linux/Windows native package availability must be verified separately. This analysis did not install or build LiteParse.
6. WASM is not the best immediate Hermes path: it avoids native Python wheel complexity but still needs JS/WASM runtime integration and does not provide built-in OCR.

## 3. Smallest verifiable Hermes integration slice

Recommended smallest slice: add a default-off `parse_document` tool focused only on local PDF text extraction through the Python LiteParse package, executed out-of-process.

Scope of the first slice:

- Input: one local `.pdf` path already allowed by Hermes read policy.
- No OCR by default (`ocr_enabled=false`).
- No office/image conversion in first slice.
- No remote URLs.
- No password-handling initially unless passed explicitly and redacted from logs.
- Output: bounded JSON envelope containing:
  - `path`
  - `parser`: `liteparse`
  - `pages_returned`
  - `total_pages_seen` if available
  - `text` capped by char budget
  - optional `pages[*].page_num`, `width`, `height`, and capped `text_items` if `include_layout=true`
  - `truncated=true/false`
  - `warnings`

Implementation shape:

1. Keep Hermes `read_file` unchanged.
2. Add a new document tool module or plugin path, e.g. `tools/document_parse_tool.py` or optional plugin.
3. Reuse the same path resolution and read denylist logic before invoking LiteParse.
4. Spawn a subprocess rather than importing the native parser into the main agent process. Use a fixed helper command with JSON stdin/stdout.
5. Time-limit and output-limit the subprocess.
6. Treat missing LiteParse dependency as a clean blocked/unavailable response, not an auto-install.
7. Add tests with a tiny fixture PDF and one binary-deny/internal-deny regression test.

Verification for the slice:

- Unit test: allowed fixture PDF returns deterministic text and page count.
- Unit test: non-PDF path is rejected in v0 slice.
- Unit test: Hermes internal/credential path is rejected before parser invocation.
- Unit test: large output is truncated deterministically.
- Smoke command: run the helper directly on a fixture PDF under the test repo.

## 4. Long-term adoption decision

Decision: `adopt experimentally, not as a mainline replacement yet`.

Rationale:

- Strong fit: LiteParse fills a real Hermes gap: structured PDF parsing with page/layout metadata, which current text-oriented `read_file` intentionally cannot provide.
- Good architecture: Rust core with napi-rs/PyO3/wasm-bindgen bindings cleanly separates parser core from host languages and matches the kind of optional high-performance capability Hermes can expose through a narrow tool.
- Major caveat: native dependencies and document-parser attack surface make it inappropriate to import directly into the main Hermes process or to make default-on without sandboxing and package verification.
- Best path: optional plugin/tool, default-off, PDF-only first, no OCR/conversion first, subprocess isolation, strict caps, and no weakening of proof/permission/mission-envelope gates.

Reject conditions for mainline adoption:

- No stable wheel/package path for supported Hermes platforms.
- Parser helper cannot be sandboxed/time-limited reliably.
- Output sizes cannot be bounded without losing deterministic behavior.
- LiteParse license/package/runtime dependencies conflict with Hermes distribution needs.
- Any integration requires weakening existing read, permission, proof, or mission-envelope gates.

## 5. Proposed next dependency / handoff

Next bounded engineering task:

> Build a throwaway, default-off `parse_document` prototype in a scratch branch/worktree that shells to an already-installed LiteParse Python package if present, rejects unsupported inputs, and proves the permission + truncation gates with fixture tests. Do not auto-install LiteParse and do not wire into default toolsets until dependency/platform review passes.

This research task should not be closed as implementation proof for that prototype. It only supplies the architecture/gap/adoption evidence pack.
