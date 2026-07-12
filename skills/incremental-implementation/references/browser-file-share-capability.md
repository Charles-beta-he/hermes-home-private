# Browser file-share capability and download fallback slice

## Applicability

Use when a web UI generates a local file (PNG, PDF, export) and prefers Web Share while retaining a local download fallback.

Anti-conditions:
- Do not use `navigator.share` presence as proof of file-share support; some browsers support only text/URLs.
- Do not treat a stubbed share promise as real device/WebView evidence.
- Do not claim external publication unless a real target was intentionally selected and separately authorized.

## Capability rule

Call native Web Share for a generated file only when both conditions are true:

```ts
navigator.share &&
typeof navigator.canShare === "function" &&
navigator.canShare({ files: [file] })
```

Then call `navigator.share(fullShareData)`. Otherwise create an object URL and trigger a local download. Revoke the object URL after the click is initiated.

Why: `navigator.share` can exist while file sharing is unsupported. Treating missing `canShare` as success can open a text-only share sheet and silently omit the generated file.

## RED → GREEN truth table

Instrument both native-share calls and anchor clicks.

| share | canShare | expected |
|---|---|---|
| absent | absent | download once |
| present | absent | download once; share zero |
| present | false | download once; share zero |
| present | true for files | share once; download zero |

Also verify:
- generated file is nonblank and has the expected MIME/name;
- action disables during capture and re-enables afterward;
- `AbortError` is treated as user cancellation, not a failure toast;
- non-Abort errors retain existing error handling;
- no backend/auth/order/funds behavior changes.

Prefer intercepting `HTMLAnchorElement.prototype.click` for fallback assertions. Counting files in a download directory is unreliable because browsers may overwrite an existing filename instead of creating a numbered file.

## Evidence boundary

Browser automation with a stubbed `navigator.share` proves branch selection and UI cleanup only. Real Web Share and transient user-activation preservation after asynchronous capture require browser/device evidence. Keep the slice local/L2 until independent review, and keep device-native claims gated.
