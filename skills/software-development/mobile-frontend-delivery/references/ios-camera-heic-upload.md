# iOS Camera HEIC/HEIF Upload Checklist

Use when a mobile web/PWA/WebView flow lets users choose `camera`/image files and iOS users report image upload failure, generic network errors, or server-side image validation errors.

## Reusable diagnostic path

1. Identify the exact frontend request path and multipart field name from the service layer, not from the UI label.
2. Check the frontend file picker `accept` list and any pre-upload MIME allowlist.
3. Treat iOS camera output as potentially `image/heic` or `image/heif` even when desktop tests only use JPEG/PNG.
4. Verify the request stays `multipart/form-data` with the browser-generated boundary; do not set a manual JSON/content-type wrapper around `FormData`.
5. On the backend contract, check three separate gates:
   - MIME allowlist includes `image/heic` and `image/heif`.
   - Extension mapping preserves `.heic` / `.heif` instead of relabeling as jpg/png.
   - Magic-byte/content sniffing recognizes ISO BMFF `ftyp` brands such as `heic`, `heif`, `heix`, `hevc`, `hevx`, `mif1`, or `msf1`.
6. If users see a generic “network abnormal” toast, inspect whether the upload endpoint is returning 5xx from object storage/config errors; this is often not a frontend network bug.

## Frontend-only minimum slice

When backend changes are out of scope, the frontend minimum fix is:

- Add `image/heic,image/heif` to the relevant `<input type="file" accept="...">`.
- Add `image/heic` and `image/heif` to the client-side image MIME allowlist.
- Add a unit test that sends a `File` named `.heic` with `type: 'image/heic'` and verifies it reaches the upload service.
- Add/update UI tests that assert the exact `accept` string includes HEIC/HEIF.

## Backend handoff shape

When handing off to backend, give them the exact endpoint, multipart field, and storage service path, then ask for:

- HEIC/HEIF MIME allowlist support.
- HEIC/HEIF magic-byte recognition.
- `.heic`/`.heif` object-key extension mapping.
- Object-storage failure handling that returns a business-level response or a durable fallback instead of leaking a generic 5xx, depending on product requirements.

## Verification

- Run focused service/session/UI tests for the upload flow.
- Run production build/typecheck.
- If possible, perform a real iOS Safari/WebView camera upload smoke. If not available, label the boundary and rely on synthetic HEIC `File` coverage plus backend contract tests.

## Pitfalls

- `accept="image/*"` or a desktop PNG test does not prove iOS camera HEIC works.
- Browser preview support for HEIC is not the same as upload support; sending the original file can still be correct.
- A same-origin fallback image URL may need auth/security handling because `<img>` requests usually do not carry custom Authorization headers.
- Do not mix broad mobile layout or keyboard changes into a focused image-upload PR from a dirty checkout; use a clean worktree and patch only the intended files.