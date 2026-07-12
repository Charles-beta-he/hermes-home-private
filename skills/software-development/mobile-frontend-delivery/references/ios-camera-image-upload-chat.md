# iOS camera image upload failures in mobile chat/composer flows

Use when a mobile web/PWA/WebView chat or support composer lets users choose Camera/Photo Library and then shows a generic “send image failed” or “network error”.

## Applicability

- Mobile web/PWA/WebView image upload from a chat/composer/support surface.
- iOS users specifically reproduce via Camera after tapping an image/attachment button.
- Upload path is multipart/form-data and backend stores images in OSS/S3/CDN/local storage.

Anti-conditions:
- Do not use this as proof that a specific project’s OSS credentials or runtime are broken; verify current backend logs/config.
- Do not make local filesystem fallback the long-term production answer for multi-instance deployments unless storage affinity/persistence is explicitly designed.
- Do not weaken image validation to accept arbitrary files; expand allowed types with magic-byte checks.

## Debugging path

1. Trace the exact user path: composer button -> hidden file input/native picker -> selected `File` -> frontend validation -> service call -> backend endpoint -> storage service -> response message rendering.
2. Verify the frontend request is really multipart:
   - service appends the file into `FormData` under the backend-expected field name;
   - shared HTTP client does not force `Content-Type: application/json` for FormData;
   - browser/XHR is allowed to attach the multipart boundary.
3. Check iOS camera MIME/extension handling:
   - iOS camera may produce `image/heic` or `image/heif` with `.HEIC/.HEIF` names;
   - add these to frontend `accept` and validation allowlists where appropriate;
   - backend must also allow them and verify HEIF/HEIC magic bytes (`ftyp` brand such as `heic`, `heix`, `hevc`, `hevx`, `mif1`, `msf1`).
4. Separate validation errors from network/storage errors:
   - 4xx validation/business errors should surface as local “image send failed” or backend message;
   - no-response/5xx/storage exceptions often trigger global network-error toasts.
5. Inspect backend storage behavior:
   - OSS/S3 bean may be absent in local/test if credentials are not configured;
   - upload exceptions should be logged with conversation/file metadata but without user secrets;
   - if a fallback is added, it must be same-origin-safe, bounded by size/type checks, path-traversal resistant, and visibly documented as non-final for multi-instance production.
6. Verify message rendering accepts returned URLs:
   - if backend returns same-origin local fallback URLs, frontend URL sanitizer must allow only that narrow prefix;
   - external URLs should usually require `https://` and a length cap;
   - image bubble should render returned `url`, `fileName`, `mime`, `sizeBytes` safely.

## Implementation checklist

Frontend:
- `accept` includes all supported MIME types, including `image/heic,image/heif` if iOS camera is in scope.
- Validation allowlist matches backend accepted MIME types.
- Unit tests cover HEIC/HEIF selection and existing png/jpeg paths.
- File input value is reset after upload attempt so the same photo can be retried.

Backend:
- Multipart endpoint uses the expected part name (e.g. `image`).
- MIME allowlist and magic-byte checks are aligned.
- Object names preserve or normalize safe extensions; do not trust raw path components from file names.
- Storage failures do not accidentally become misleading auth/session errors.
- Optional local fallback has a read endpoint with strict filename regex, size/type revalidation, and no-store cache headers.
- Security config permits only the narrow fallback read route if images must render without additional headers.

## Verification ladder

1. Focused frontend tests for service/FormData, validation, and chat composer behavior.
2. Focused backend storage tests: valid PNG/JPEG, HEIC/HEIF, invalid MIME/magic, OSS unavailable/fallback.
3. Backend compile/test with duplicate local scratch files quarantined if ignored files are polluting javac.
4. Frontend build.
5. If available, browser/device verification with an actual iOS camera HEIC upload; otherwise report the physical-device boundary explicitly.

## Common pitfalls

- Frontend accepts HEIC but backend rejects it, or vice versa.
- Hidden `* 2.java` / copied scratch files in Java source/test trees can cause duplicate-class compilation failures; quarantine ignored scratch files rather than changing product code.
- Logging a caught business exception as a full stack trace can make expected fallback look like an outage; log a concise fallback reason for expected UNKNOWN/storage-unavailable cases.
- Local filesystem fallback works on one process but is not durable across pods/instances/restarts; treat it as a short-term degradation path, not a storage architecture.
