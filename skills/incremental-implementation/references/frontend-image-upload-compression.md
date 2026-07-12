# Frontend oversized image upload compression slice

Use when a browser/PWA/mobile-web flow uploads camera or album images and the server/proxy has a request-size cap (for example nginx `client_max_body_size` around 5 MB). This is a reusable bugfix slice for symptoms such as generic upload failure or network-error toast after iOS camera capture.

## Applicability

- Chat/support/message composer, KYC/document upload, receipt upload, avatar upload, or similar browser File upload flows.
- Backend/proxy rejects large image payloads, and changing backend limits is not the preferred or sufficient fix.
- The client has access to browser canvas APIs and can safely normalize oversized images to JPEG.

## Anti-conditions

- Do not compress non-image files or formats that cannot be decoded by the browser image pipeline.
- Do not silently change product-owned image fidelity requirements; for KYC/legal documents, verify OCR/readability requirements before lowering dimensions/quality.
- Do not claim native iOS camera acceptance without real device/browser evidence; unit tests only prove the preprocessing contract.

## Implementation pattern

1. Locate the single upload boundary closest to the service call, not just the button handler.
2. Preserve existing small valid images as-is to avoid unnecessary quality loss and metadata churn.
3. Validate MIME and non-empty file before compression.
4. For oversized drawable image types, load through `URL.createObjectURL(file)` + `Image`, draw to a bounded canvas dimension, and emit JPEG blobs using a descending quality ladder.
5. Re-check the final `File` MIME, non-empty size, and hard byte limit before calling the upload service.
6. Revoke object URLs on success/failure cleanup.
7. Throw the same validation/upload-preparation error shape already handled by the UI so existing toast behavior remains stable.

## Test pattern

- Add/extend focused upload-flow tests proving:
  - invalid MIME and empty image do not call the upload service;
  - acceptable small images still pass through unchanged;
  - an oversized camera image is converted to a new `File` with `image/jpeg`, a safe extension, and size <= the configured cap;
  - returned image URLs/MIME are still sanitized before rendering if that contract exists.
- In Vitest/jsdom, stub browser primitives rather than relying on real image decoding:
  - `global.Image` with async `onload` and fixed `naturalWidth/naturalHeight`;
  - `URL.createObjectURL` / `URL.revokeObjectURL`;
  - `HTMLCanvasElement.prototype.getContext` returning mocked `clearRect/drawImage`;
  - `HTMLCanvasElement.prototype.toBlob` returning a deterministic JPEG `Blob` under the cap.

## Verification checklist

- Focused unit test for the upload flow.
- Touched-file ESLint/typecheck where available.
- Production build/typecheck.
- `git diff --check` before commit.
- If the task is a visual/mobile acceptance bug, follow up with real iOS/Safari/PWA smoke evidence before claiming full acceptance.
