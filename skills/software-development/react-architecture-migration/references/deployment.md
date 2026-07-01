# React Migration Deployment Notes

Extracted from `/Users/charles/.hermes/skills/software-development/react-architecture-migration/SKILL.md` on 2026-07-01T08:53:45.426287+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Deployment

### Build
```bash
npm run build          # → dist/ (944KB, 71 JS chunks + PWA files)
npm run preview        # → localhost:4173 preview
```

### Deploy Frontend
```bash
# Cloudflare Pages
wrangler pages deploy dist --project-name uvisa-app

# Vercel
vercel --prod

# Netlify
netlify deploy --prod --dir=dist
```

### Deploy Mock Server (separate)
```bash
# On VPS
scp -r mock-server/ user@server:/opt/uvisa-mock/
ssh user@server "cd /opt/uvisa-mock && npm install --production && pm2 start server.js"

# Or Railway
cd mock-server && railway up
```

### Environment Variables
```bash
# .env.production
VITE_API_BASE=https://mock.uvisa.app/api  # → real API later
VITE_SENTRY_DSN=https://xxx@sentry.io/123
VITE_DEMO_PIN=                            # empty in prod
VITE_DEMO_SMS_CODE=                       # empty in prod
```

### CI/CD (GitHub Actions)
```yaml
on: push to main
steps: npm ci → npm test → npm run build → deploy to CDN
```

- `p10` — CTO strategic review
- `p10-architecture-self-check` — Architecture health check
- `loop` — PUA loop iteration
- `subagent-driven-development` — Parallel task execution
- `save-workflow-as-skill` — Save after completion
