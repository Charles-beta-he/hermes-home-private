# Frontend global error toast: backend message first, generic copy as fallback

Applicability:
- SPA/mobile-web clients with a centralized HTTP interceptor that broadcasts global network/server-error events.
- The app currently shows a generic network/server error toast for all no-response or 5xx failures.
- Backend 5xx responses may still contain a user-facing `message` that should be shown.

Anti-conditions:
- Do not show backend messages for request cancellations, aborts, or user navigation.
- Do not convert 4xx business errors into global network toasts if callers already receive `{ success:false, message }` for page-local handling.
- Do not replace page-specific validation/business copy with this pattern; this is only for the global outage/server-error path.

Procedure:
1. Locate the central response-error interceptor and the top-level global toast listener.
2. Extend the global error event detail with an optional `message` field.
3. Extract `response.data.message` only when it is a non-blank string.
4. For no-response network failures, dispatch the event with no message so the UI keeps the generic fallback.
5. For 5xx responses, dispatch the event with the extracted backend message when present.
6. In the toast listener, render `detail.message || t("common.networkError")` (or the app’s equivalent localized fallback).
7. Preserve throttling/de-dupe behavior so a burst of failed requests does not spam toasts.
8. Add focused interceptor tests:
   - 5xx without message still dispatches the global error event and falls back to generic copy.
   - 5xx with backend `message` preserves that message in the event.
   - pure no-response network error dispatches without message.
   - canceled/aborted requests do not dispatch the global error toast.

Verification:
- Run the focused interceptor/unit test.
- Run typecheck/build for the touched frontend package.
- Run a diff/whitespace check on the touched files.

Session detail example:
- In a React/Vite frontend, the fix was: HTTP interceptor event detail gained `message?: string`, 5xx dispatch extracted `response.data.message`, and the top-level listener changed from fixed `common.networkError` to `detail?.message || common.networkError`.
