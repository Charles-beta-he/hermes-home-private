# Gemini CLI / OAuth provider chain diagnostic

When `consult_models.py run` reports Gemini 429 or planner failure but direct `hermes chat --provider google-gemini-cli` works, trace the full provider chain before concluding it's a quota issue.

## The chain

```
consult_models.py run
  → effective_model_provider(config, model)    # ~L759
    → model_provider(config, model)            # ~L741 — reads pricing.models.<model>.provider
      → config["pricing"]["models"]["gemini-3.1-pro-preview"]["provider"]
        → "google-gemini-cli"   (or "gemini" for API-key path)
    → returns provider string
  → call_planner_model(model, prompt, ...)     # ~L3728
    → adapter = "hermes-chat"
    → cmd = [hermes, "chat", "-q", prompt, "--model", model,
             "--quiet", "--max-turns", "1",
             "--source", "multi-brain", "--ignore-rules"]
    → if provider in SUPPORTED_HERMES_PROVIDERS:
        cmd += ["--provider", provider]
    → subprocess.run(cmd, ...)
```

## Diagnostic checklist

Order matters — check from bottom up:

1. **Direct short prompt**: `hermes chat --provider google-gemini-cli -m gemini-3.1-pro-preview -q 'GEMINI_OK' --quiet --max-turns 1 --ignore-rules`
   - If this fails: provider/CLI path is broken (auth, binary, OAuth session)
   - If this passes: CLI path works, continue

2. **Router probe**: `python3 ~/.hermes/scripts/model-router.py probe`
   - Confirms provider availability snapshot
   - Look for `gemini-3.1-pro-preview` under Available/Unavailable

3. **Pricing config**: verify `pricing.models["gemini-3.1-pro-preview"]["provider"]` is `"google-gemini-cli"` (not `"gemini"`)
   - `gemini` = Google AI Studio API-key provider (different auth path)
   - `google-gemini-cli` = Cloud Code Assist OAuth path

4. **Medium prompt with multi-brain flags**: `hermes chat --provider google-gemini-cli -m gemini-3.1-pro-preview --source multi-brain --ignore-rules --quiet --max-turns 1 -q '<JSON response prompt>'`
   - If this fails but step 1 passed: prompt size or `--source multi-brain` flag matters
   - If this passes: full consult_models path should work

5. **OAuth session**: `hermes doctor | grep -i gemini`
   - Should show: `Google Gemini OAuth (logged in ...)`
   - Token file: `~/.hermes/auth/google_oauth.json`
   - Missing refresh token = capacity issues on re-auth

6. **Consult_models quorum config**: `python3 ~/.hermes/scripts/consult_models.py status`
   - T2/T3 tiers include `gemini-3.1-pro-preview`
   - `quorum >= min_quorum` even if one planner fails

7. **Actual tick output**: check `~/.hermes/tick-*/plans/gemini-3.1-pro-preview.json`
   - `confidence=0.2` + no provider/adapter fields = shadow plan (real call failed)
   - `confidence>=0.8` + `provider: google-gemini-cli` = real plan succeeded
   - `error: "capacity exhausted"` = Google-side throttle, not Hermes issue

## Common failure modes

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Direct call works, planner fails | Prompt too large for Gemini capacity | Accept degraded fan-out or use Flash model |
| Both fail with 429 | Google-side capacity throttle | Wait or switch model |
| `provider: "unknown"` in plan | pricing.models entry missing | Add to config.yaml |
| `adapter: "none"` | `shutil.which("hermes")` failed | Hermes not in PATH |
| Planner exits but consult_models killed (-15) | Fan-out timeout exceeded all 5 planners | Use --background, check tick dir later |

## Red herrings to avoid

- Do NOT change the provider from `google-gemini-cli` to `gemini` to "fix" 429 — these are different auth paths and swapping hides the real issue.
- Do NOT remove Gemini from quorum to silence planner failures — the failure evidence is valuable for diagnosing capacity vs. configuration issues.
- A short-prompt success does NOT guarantee planner-prompt success — Gemini Pro capacity throttles on input size.
