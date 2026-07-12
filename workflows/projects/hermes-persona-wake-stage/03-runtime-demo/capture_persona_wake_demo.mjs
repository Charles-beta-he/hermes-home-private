#!/usr/bin/env node
import { chromium } from '/Users/charles/Desktop/folder/hermes-control-console/node_modules/playwright/index.mjs'
import { resolve, dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { mkdirSync, writeFileSync } from 'node:fs'

const root = dirname(fileURLToPath(import.meta.url))
const outDir = join(root, 'artifacts', 'browser-readback-20260707T085200Z')
mkdirSync(outDir, { recursive: true })
const url = `file://${join(root, 'persona-wake-local.html')}`
const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } })
const consoleEvents = []
const pageErrors = []
page.on('console', (msg) => consoleEvents.push({ type: msg.type(), text: msg.text() }))
page.on('pageerror', (err) => pageErrors.push({ message: err.message }))
await page.goto(url, { waitUntil: 'domcontentloaded' })
await page.screenshot({ path: join(outDir, 'initial.png'), fullPage: true })
await page.getByRole('button', { name: 'Wake local stage' }).click()
await page.screenshot({ path: join(outDir, 'after-wake.png'), fullPage: true })
const readback = await page.evaluate(() => ({
  title: document.title,
  headline: document.querySelector('h1')?.textContent,
  boundaryCopy: document.body.innerText,
  status: document.querySelector('[role="status"]')?.textContent,
  runtime: window.__PERSONA_WAKE_DEMO__ || null,
}))
await browser.close()
const summary = {
  status: consoleEvents.some((e) => e.type === 'error') || pageErrors.length ? 'FAIL' : 'PASS',
  url,
  outDir,
  consoleEvents,
  pageErrors,
  readback,
  screenshots: [join(outDir, 'initial.png'), join(outDir, 'after-wake.png')],
  negativeAuthority: {
    externalSend: readback.runtime?.externalSend === false,
    voice: readback.runtime?.voice === false,
    blocked: readback.runtime?.blocked || [],
    statusNoSideEffects: readback.status === 'Local wake acknowledged. No external side effects were invoked.',
  }
}
writeFileSync(join(outDir, 'summary.json'), JSON.stringify(summary, null, 2) + '\n')
console.log(JSON.stringify({ status: summary.status, outDir, negativeAuthority: summary.negativeAuthority }, null, 2))
if (summary.status !== 'PASS') process.exit(1)
