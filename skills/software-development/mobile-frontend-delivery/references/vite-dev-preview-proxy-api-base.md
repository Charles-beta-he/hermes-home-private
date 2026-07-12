# Vite dev/preview API base and proxy debugging

Use when a React/Vite mobile web or PWA page is visible but API-dependent sections are blank or empty in local dev or `vite preview`, while the same backend data is reachable through the intended test/staging service.

## Applicability

- The browser URL uses a different local host or port than the API client assumes.
- Vite `server.proxy` is configured, but `vite preview` or another local port still renders empty API data.
- API-dependent mobile pages show loading, empty, or error fallback states even though the upstream service responds.

## Anti-conditions

- The issue occurs only on a deployed production host with an explicit environment-provided API base URL.
- The route is pure static UI with no API dependency.
- The product intentionally requires a separate local backend and should not proxy to a remote test or staging backend.

## Debugging path

1. Inspect the exact URL the user opened: hostname, port, and whether it is dev server or preview server.
2. Inspect API client base URL construction. Hardcoded local origins are fragile when users open another local host, another port, or `vite preview`.
3. Inspect Vite config for both `server.proxy` and `preview.proxy`. `server.proxy` alone does not guarantee preview will proxy API calls.
4. Probe the local proxy path directly with `curl http://<local-host>:<port>/api/<endpoint>` and verify it returns backend JSON, not index HTML or a network error.
5. Run browser or screenshot verification against the exact reported URL, not only the most convenient localhost variant.

## Recommended fix pattern

- In dev and local preview, prefer same-origin relative `/api` as the frontend API base URL so the current page origin determines host and port.
- Keep explicit environment-provided API base URL support for configured production builds.
- For local preview without an environment API base, use `/api` plus `preview.proxy`, or clearly document that preview requires a backend environment variable.
- Share one proxy config object between `server.proxy` and `preview.proxy` to avoid drift.
- Preserve deployed same-origin fallback only for non-local production builds when no environment base URL is set.

Example shape:

```ts
function getBaseURL() {
  if (import.meta.env.DEV) return "/api";

  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL;
  if (configuredBaseUrl) return configuredBaseUrl;

  const hostname = typeof window === "undefined" ? "" : window.location.hostname;
  const isLocalPreview =
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname === "0.0.0.0" ||
    hostname === "::1" ||
    hostname.endsWith(".local");

  return isLocalPreview ? "/api" : "/api";
}
```

```ts
const apiProxy = {
  target: "https://staging.example.invalid/api",
  secure: false,
  changeOrigin: true,
  rewrite: (path: string) => path.replace(/^\/api/, "")
};

export default defineConfig({
  server: { proxy: { "/api": apiProxy } },
  preview: { proxy: { "/api": apiProxy } }
});
```

## Verification checklist

- Targeted build passes.
- Targeted lint for changed config/API files passes.
- Local `/api/<endpoint>` returns backend JSON from the exact host/port the user reported.
- Browser DOM or screenshot for the exact reported URL shows the API-backed rows/cards and no network-error fallback.
- If full project lint fails from pre-existing unrelated files, report it separately and include targeted lint evidence for the changed files.
