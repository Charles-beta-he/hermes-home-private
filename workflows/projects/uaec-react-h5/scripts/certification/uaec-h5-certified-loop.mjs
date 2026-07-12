import { existsSync, mkdirSync, readFileSync, writeFileSync, copyFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const scriptPath = fileURLToPath(import.meta.url);
const ssotRoot = resolve(dirname(scriptPath), '../..');
const repoRoot = process.argv[2] ? resolve(process.argv[2]) : process.cwd();
const now = new Date();
const timestamp = now.toISOString().replace(/[:.]/g, '-');
const evidenceRoot = join(ssotRoot, 'evidence');
const outDir = join(evidenceRoot, 'certification');
const latestPath = join(outDir, 'local-h5-loop-latest.json');
const timestampPath = join(outDir, `local-h5-loop-${timestamp}.json`);
mkdirSync(outDir, { recursive: true });

const evidence = {
  homeRanking: '2026-07-09-h5-api-preview/home-ranking-api-response.json',
  homeRankingScreenshot: '2026-07-09-h5-api-preview/home-ranking-preview-127-4173-390x844.png',
  homeTopRoute: '2026-07-09-slice2/home-top-click-route-smoke-390x844.json',
  tabbarSafeArea: '2026-07-09-slice3/tabbar-safe-area-smoke.json',
  tabRoute: '2026-07-09-slice4/tab-route-smoke-390x844.json',
  bannerRuntime: '2026-07-09-slice1/banner-runtime-smoke-390x844.json',
  bannerFixture: '2026-07-09-slice1/banner-navigation-fixture-smoke.json',
};

const report = {
  generatedAt: now.toISOString(),
  target: 'uaec-react-h5 local H5 preview certification loop',
  certificationLevel: 'L2-local-loop-verified',
  boundedClaim: 'local H5 preview runtime evidence packet validated from Hermes project SSOT; not production/device/auth certified',
  repoRoot,
  ssotRoot,
  commands: [],
  checks: [],
  blockers: [],
  boundaries: [
    'remote push/deploy requires explicit authorization',
    'authenticated route behavior requires valid user session/token supplied by human or pre-existing browser session',
    'iOS Safari / Android Chrome / App WebView safe-area acceptance requires real device or explicitly accepted simulator/device readback',
    'production/test-domain acceptance requires deployed URL and rollback/readback gate',
    'full-repo lint remains a historical baseline issue and is not hidden by this local certification loop',
  ],
};

function run(name, args) {
  const res = spawnSync(name, args, {
    cwd: repoRoot,
    encoding: 'utf8',
    shell: false,
    maxBuffer: 20 * 1024 * 1024,
  });
  const entry = {
    command: [name, ...args].join(' '),
    exitCode: res.status,
    stdoutTail: (res.stdout || '').split('\n').slice(-30).join('\n').trim(),
    stderrTail: (res.stderr || '').split('\n').slice(-30).join('\n').trim(),
  };
  report.commands.push(entry);
  return res;
}

function addCheck(name, ok, details = {}) {
  report.checks.push({ name, ok: Boolean(ok), ...details });
  if (!ok) report.blockers.push({ name, details });
}

function readJson(rel) {
  const abs = join(evidenceRoot, rel);
  if (!existsSync(abs)) throw new Error(`Missing SSOT evidence file: ${rel}`);
  return JSON.parse(readFileSync(abs, 'utf8'));
}

function fileExists(rel) {
  return existsSync(join(evidenceRoot, rel));
}

function ensureCommandOk(label, res) {
  addCheck(label, res.status === 0, {
    exitCode: res.status,
    stdoutTail: (res.stdout || '').split('\n').slice(-15).join('\n').trim(),
    stderrTail: (res.stderr || '').split('\n').slice(-15).join('\n').trim(),
  });
}

try {
  const status = run('git', ['status', '--short', '--branch']);
  ensureCommandOk('repo git status readback', status);
  report.gitStatus = (status.stdout || '').trim();
  const statusLines = report.gitStatus.split('\n').map(line => line.trim()).filter(Boolean);
  report.workingTreeCleanAtGeneration = statusLines.slice(1).length === 0;
  addCheck('repo working tree clean at loop generation', report.workingTreeCleanAtGeneration, {
    status: report.gitStatus,
    note: 'Progress/evidence artifacts live in Hermes project SSOT; the application repo should have no dirty progress artifacts at loop generation.'
  });

  for (const [key, rel] of Object.entries(evidence)) {
    addCheck(`SSOT evidence exists: ${key}`, fileExists(rel), { path: join(evidenceRoot, rel) });
  }

  const eslint = run('npx', [
    'eslint',
    'src/api/apiClient.ts',
    'vite.config.ts',
    'src/pages/HomePage/HomePage.tsx',
    'src/components/common/NotificationIconWithBadge.tsx',
    'src/components/common/TabBar.tsx',
  ]);
  ensureCommandOk('scoped eslint', eslint);

  const build = run('npm', ['run', 'build']);
  ensureCommandOk('npm run build', build);

  const homeRanking = readJson(evidence.homeRanking);
  const rows = homeRanking?.data?.data || homeRanking?.data?.list || homeRanking?.data || [];
  const rowArray = Array.isArray(rows) ? rows : [];
  addCheck('home ranking API response has success meta and rows', Boolean(homeRanking?.meta?.success && rowArray.length >= 3), {
    meta: homeRanking?.meta,
    rowCount: rowArray.length,
    firstSymbol: rowArray[0]?.symbol || rowArray[0]?.tradeName || rowArray[0]?.name || null,
  });

  const top = readJson(evidence.homeTopRoute);
  const topResults = top.results || top;
  const topCases = Array.isArray(topResults) ? topResults : Object.values(topResults || {});
  addCheck('home top anonymous click smoke cases pass', topCases.length >= 4 && topCases.every(c => c.ok === true), {
    caseCount: topCases.length,
    cases: topCases.map(c => ({ name: c.name, ok: c.ok, url: c.after?.url || c.url || null })),
  });

  const tabbar = readJson(evidence.tabbarSafeArea);
  const tabbarResults = tabbar.results || [];
  addCheck('tabbar safe-area matrix passes 375/390/414', tabbarResults.length >= 3 && tabbarResults.every(r => r.ok === true && r.metrics?.navWithinViewport !== false && r.metrics?.lastButtonVisible !== false), {
    viewports: tabbarResults.map(r => ({ size: r.size, ok: r.ok, navRect: r.metrics?.navRect })),
  });

  const tabRoute = readJson(evidence.tabRoute);
  const tabRouteResults = tabRoute.results || [];
  const expectedTabs = new Map([
    ['首页', '/'],
    ['行情', '/market'],
    ['交易', '/trade'],
    ['合约', '/contract'],
    ['资产', '/Login'],
  ]);
  const tabRoutePass = [...expectedTabs.entries()].every(([name, routePath]) => {
    const item = tabRouteResults.find(r => r.name === name);
    return item?.ok === true && String(item.after?.url || '').includes(routePath) && (item.after?.errorText || []).length === 0;
  });
  addCheck('bottom tab anonymous route smoke passes', tabRoutePass, {
    cases: tabRouteResults.map(r => ({ name: r.name, ok: r.ok, expectedPath: r.expectedPath, url: r.after?.url, errors: r.after?.errorText || [] })),
  });

  const bannerRuntime = readJson(evidence.bannerRuntime);
  addCheck('banner current-payload runtime smoke passes with no token leaks', bannerRuntime.ok === true && (bannerRuntime.networkSummary?.tokenLeakUrls || []).length === 0, {
    boundary: bannerRuntime.boundary,
    tokenLeakUrls: bannerRuntime.networkSummary?.tokenLeakUrls || [],
    afterUrl: bannerRuntime.after?.url,
  });

  const bannerFixture = readJson(evidence.bannerFixture);
  addCheck('banner redirect fixture smoke passes', bannerFixture.ok === true && Array.isArray(bannerFixture.results) && bannerFixture.results.every(r => r.ok === true && r.tokenLeak === false), {
    cases: (bannerFixture.results || []).map(r => ({ name: r.name, ok: r.ok, tokenLeak: r.tokenLeak })),
  });

  report.ok = report.blockers.length === 0;
  report.nextCertificationGate = report.ok
    ? 'L3 requires independent verifier APPROVE or resolved AMEND readback; L4/L5 require human authority/device/session/deploy gates.'
    : 'Resolve blockers, rerun node <ssot>/scripts/certification/uaec-h5-certified-loop.mjs <repoRoot>.';
} catch (error) {
  report.ok = false;
  report.blockers.push({ name: 'uncaught exception', details: { message: error.message, stack: error.stack } });
}

writeFileSync(timestampPath, JSON.stringify(report, null, 2));
copyFileSync(timestampPath, latestPath);
console.log(JSON.stringify({ ok: report.ok, blockers: report.blockers.length, report: latestPath, timestampedReport: timestampPath, level: report.certificationLevel }, null, 2));
process.exit(report.ok ? 0 : 1);
