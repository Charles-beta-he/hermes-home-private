# Cross-End Capability SDK

## Scope / Applicability / Anti-conditions

Scope: reusable mobile/web frontend architecture pattern for device capabilities whose behavior differs across browser H5, installed PWA/WebView, and native/hybrid shells.

Applicability: use when a product action depends on device/system capability such as camera scan, file upload, geolocation, push notification, biometrics, share sheet, contacts, clipboard, or deep links, and a single Web API or component-level check is being used as the total support gate.

Anti-conditions: do not use for purely visual UI bugs, server-only capability checks, or simple browser APIs that have no permission/device/native fallback boundary. Keep project URLs, task IDs, PR numbers, and branch names out of this reference; store those in project evidence only.

## Core Rule

Do not use one platform API as the support switch for an entire product capability.

Represent the capability as layered contracts:

```text
user action
→ capability resolver
→ permission layer
→ device/session layer
→ processing layer
→ result projection
→ cleanup / recovery
```

For cross-end delivery, the SDK should choose the owner/adapter by runtime:

```text
native/hybrid bridge
→ browser/PWA native Web API
→ JS/library fallback
→ preview-only or manual fallback
→ unsupported with recovery copy
```

## Three-Layer Device Capability Contract

### 1. Permission layer

Question: can the user be asked for the system permission and can the app receive a permission result?

Examples:
- camera prompt
- location prompt
- notification permission
- file picker open
- clipboard read permission

Rules:
- Permission must not be blocked by an optional processing capability.
- If the product requirement is “prompt permission/open device,” tests must assert that permission request path fires.
- Product-owned pre-permission education is allowed and often desirable on mobile/PWA (for example a sheet saying why camera is needed), but treat it as a product overlay contract, not as part of the capability SDK itself. When the product asks to remove that overlay, delete its UI, i18n keys, and dedicated tests together, then restore tests so opening the feature immediately reaches the system permission/session path while preserving the lower-layer SDK behavior.
- If a product pre-permission prompt remains required, model it as a user-gesture gate before the system permission request, not as a replacement for it. Add tests for both states: before “Allow”, no system API call; after “Allow”, the system permission/session request fires even if optional processors such as `BarcodeDetector` are missing.
- Permission denial is a first-class result, not a generic unsupported state.

### 2. Device/session layer

Question: after permission, can the app establish and own the device/session surface?

Examples:
- camera stream attached to video preview
- native scanner view opened
- geolocation watch started
- file handle obtained
- push token registered

Rules:
- Open/preview/session success is separate from post-processing success.
- Cleanup is part of the contract: stop media tracks, close native sessions, clear watchers/listeners.
- A preview-only/manual fallback may still satisfy part of the user flow if processing is unavailable.

### 3. Processing/result layer

Question: can the app process the device/session output into the product result?

Examples:
- QR decoding
- image compression/OCR
- geofence classification
- biometric auth token validation
- file type extraction

Rules:
- Processing libraries are adapters, not permission gates.
- Prefer native SDK/bridge when available, then Web-native processor, then JS fallback.
- If processing is missing, preserve the lower-layer capability when useful and show a manual/retry path.

## SDK Shape

Expose a small product-facing interface. Hide platform checks inside adapters.

```ts
export type CapabilityMode =
  | 'native-bridge'
  | 'web-native'
  | 'web-js-fallback'
  | 'preview-only'
  | 'unsupported';

export type CapabilityErrorCode =
  | 'PERMISSION_DENIED'
  | 'DEVICE_UNAVAILABLE'
  | 'PROCESSOR_UNAVAILABLE'
  | 'USER_CANCELLED'
  | 'TIMEOUT'
  | 'UNKNOWN';

export interface CapabilityReport {
  canRequestPermission: boolean;
  canOpenDeviceSession: boolean;
  canProcessResult: boolean;
  preferredMode: CapabilityMode;
  reason?: string;
}

export interface CapabilitySession {
  mode: CapabilityMode;
  stop: () => void;
}
```

A feature-specific SDK can refine the generic shape, e.g. `ScanResult`, `CameraSession`, `GeoResult`, or `ShareResult`.

## QR / Camera Scan Example

Bad path:

```text
click scan
→ check BarcodeDetector
→ BarcodeDetector missing
→ return unsupported
→ never request camera permission
```

Good path:

```text
click scan
→ native bridge scan if available
→ otherwise request camera permission
→ attach camera preview
→ choose decoder:
   - native bridge / native SDK
   - BarcodeDetector
   - ZXing/jsQR fallback
   - preview-only + paste/manual fallback
→ return decoded text or typed error
→ stop tracks/session on close
```

Recommended project-local structure:

```text
src/lib/scan/
  index.ts
  types.ts
  capability.ts
  errors.ts
  adapters/
    nativeBridgeScanner.ts
    webCamera.ts
    barcodeDetectorDecoder.ts
    zxingDecoder.ts
  __tests__/
    capability.test.ts
    webCamera.test.ts
    qrScanSdk.test.ts
```

Implementation sequence for an existing component:
1. Write RED tests against the current UI that prove the layer separation, especially "processor missing but camera available still requests permission".
2. Extract the SDK files behind the existing component without changing page-level callers.
3. Change the component to consume SDK operations and typed results/errors; keep screens receiving only `onResult(text)`.
4. Add a JS decoder fallback (for QR, `@zxing/browser` or equivalent) after camera start; if decoder setup fails, keep preview/manual fallback instead of closing the camera path.
5. Run focused component tests, affected screen tests, build/typecheck, then the full suite. If full-suite failures are unrelated style-selector brittleness in touched wrappers, prefer stable test IDs over reverting functional layout changes.

UI components should depend on the SDK, not on platform APIs directly.

```tsx
<QrScanSheet
  open={open}
  onClose={close}
  onResult={(text) => applyResult(text)}
/>
```

The screen should not know whether the result came from native bridge, Web camera, BarcodeDetector, ZXing, or a future adapter.

## Adapter Priority

1. Native/hybrid bridge when present and trusted.
   - Example shape: `window.AppNative?.scanQr()`.
   - Requires native permission declarations and native-side error mapping.
2. Web permission/session API.
   - Example: `navigator.mediaDevices.getUserMedia`, geolocation, Notification API, file picker.
3. Web-native processor.
   - Example: `BarcodeDetector`.
4. JS/library fallback.
   - Example: `@zxing/browser`, `jsQR`.
5. Manual fallback / preview-only / unsupported.
   - Example: paste address, upload image, open settings, retry.

## Testing Matrix

For every extracted capability SDK, add tests for owner selection and layer separation.

Minimum tests:
- native bridge present → uses bridge and does not call Web API unnecessarily;
- product pre-permission prompt present → opening the UI does not call the system API until the user taps the product “Allow” action;
- product pre-permission prompt removed → opening the UI immediately starts the permission/session path; residual prompt test IDs, prompt i18n keys, and prompt-only tests should be gone;
- Web-native path present → requests permission/device session and processes with Web API;
- Web-native processor missing but permission/session available → after the active product gate (if any), still requests permission/session and uses JS fallback or preview-only mode;
- permission denied → returns `PERMISSION_DENIED`, not `unsupported`;
- processor failure → does not misclassify as permission denial;
- close/unmount → stops tracks, watchers, listeners, or native sessions;
- build artifact or runtime environment constraints are checked when packaging transforms the source.


## Review Checklist

Before approving capability-related frontend changes:

- [ ] Is the product action modeled as layered capability, not a single API check?
- [ ] Is the permission request independent from optional processing support?
- [ ] Are browser/PWA/native owners separated by adapters?
- [ ] Does the UI receive typed results/errors instead of inspecting platform APIs?
- [ ] Is there a manual/recovery path when processing is unavailable but permission/session works?
- [ ] Do tests cover at least one missing-processor-but-available-device case?
- [ ] Does cleanup stop underlying device/session resources?

## Pitfalls

1. Treating optional processors as device support gates.
2. Returning `unsupported` before the system permission prompt can fire.
3. Putting platform branching in page components instead of an SDK/adapter layer.
4. Testing only the happy-path platform currently used by the developer machine.
5. Calling native bridge and Web API in parallel without owner priority or cleanup.
6. Collapsing permission denial, device unavailable, processor unavailable, and user cancel into one error string.
