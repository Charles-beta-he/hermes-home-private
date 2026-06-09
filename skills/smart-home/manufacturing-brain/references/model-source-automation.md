# Model Source Fetch Automation

When the user provides a model URL (MakerWorld, Printables, Thingiverse, etc.), the first step is fetching the STL/3MF file. This reference documents which sources allow automated fetch and which require manual download.

## Automation status by source

| Source | Auto-fetch? | Notes |
|---|---|---|
| **MakerWorld** (.com / .com.cn) | **NO** | Aggressive Cloudflare Turnstile. Browser automation detected as bot; clicking checkbox does not pass. curl/API all 403/404. No public download API without auth. |
| **Printables** (printables.com) | **YES** | Direct STL download links work with curl. API available. |
| **Thingiverse** (thingiverse.com) | **YES** | Direct download links work. API available. |
| **GitHub raw links** | **YES** | `raw.githubusercontent.com` direct links work with curl. |
| **Direct CDN/file links** | **YES** | Any direct `.stl`/`.3mf`/`.zip` URL works. |

## Cloudflare-protected sites (known)

These sites use Cloudflare Turnstile or similar JS challenges that block headless browsers and curl:

- `makerworld.com` / `makerworld.com.cn` (拓竹 MakerWorld)
- Sites with "Under Attack" mode Cloudflare

## Fallback workflow when auto-fetch fails

1. Tell the user clearly: "This site has Cloudflare bot protection, automation cannot pass it."
2. Offer two options:
   - User downloads manually to a local path, then tells you the file path
   - User drags the file into `~/Desktop/folder/` or another known directory
3. Once you have the local file path, resume the full pipeline:
   `preflight → AMS auto-inject → mesh QA → orientation search → slice → slicer preview parse → quality review → user confirmation`

## MakerWorld API patterns (for reference)

These patterns exist but all return 403/404 without Cloudflare cookies:

```
GET /api/v1/designs/{id}/detail
GET /api/v1/designs/{id}/download
GET /api/v1/models/{id}
GET /api/v2/designs/{id}
```

Model URL pattern: `https://makerworld.com/zh/models/{id}-{slug}#profileId-{profile_id}`

## Key lesson

Do NOT spend >2 attempts trying to bypass Cloudflare. If the first curl and first browser attempt both fail with Cloudflare challenge, immediately pivot to the manual-download fallback. Time spent on Cloudflare bypass is wasted.
