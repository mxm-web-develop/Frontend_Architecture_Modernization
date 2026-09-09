#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { chromium } from 'playwright';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';

function cliArg(name) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
}
const command = process.argv[2];
const configPath = cliArg('--config');
if (!command || !configPath) {
  console.error('Usage: node visual_harness.mjs <doctor|capture-legacy|capture-target|compare|all> --config <config.json>');
  process.exit(2);
}
const cfg = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const configDir = path.dirname(path.resolve(configPath));
const projectRoot = path.resolve(configDir, cfg.project_root ?? '.');
const outputDir = path.resolve(projectRoot, cfg.output_dir);
fs.mkdirSync(outputDir, { recursive: true });

function resolveMaybe(file) { return file ? path.resolve(projectRoot, file) : undefined; }
function authStorageState(source) {
  if (source.auth?.strategy === 'storage-state') return resolveMaybe(source.auth.path);
  return resolveMaybe(source.storage_state);
}
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function waitHealthy(url, timeoutMs = 60000) {
  const start = Date.now();
  let lastError = null;
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url, { redirect: 'manual' });
      if (res.status < 500) return;
    } catch (e) { lastError = e; }
    await sleep(500);
  }
  throw new Error(`Health check timed out: ${url}. ${lastError ?? ''}`);
}

async function startServer(side) {
  const server = cfg[side]?.server;
  if (!server?.command) return null;
  const cwd = resolveMaybe(server.cwd ?? '.');
  const child = spawn(server.command, {
    cwd,
    shell: true,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, ...(server.env ?? {}) },
    detached: process.platform !== 'win32',
  });
  child.stdout?.on('data', d => process.stdout.write(`[${side}] ${d}`));
  child.stderr?.on('data', d => process.stderr.write(`[${side}] ${d}`));
  const health = server.health_url ?? cfg[side].base_url;
  try {
    await waitHealthy(health, server.timeout_ms ?? 60000);
  } catch (e) {
    stopServer(child);
    throw e;
  }
  console.log(`server ready ${side}: ${health}`);
  return child;
}
function stopServer(child) {
  if (!child || child.killed) return;
  try {
    if (process.platform !== 'win32') process.kill(-child.pid, 'SIGTERM');
    else child.kill('SIGTERM');
  } catch {}
}
async function withServers(fn) {
  const children = [];
  try {
    if (cfg.legacy?.server?.command) children.push(await startServer('legacy'));
    if (cfg.target?.server?.command) children.push(await startServer('target'));
    return await fn();
  } finally {
    for (const child of children.reverse()) stopServer(child);
  }
}

async function applyAuth(context, page, side) {
  const source = cfg[side];
  const auth = source.auth;
  if (!auth || auth.strategy === 'none' || auth.strategy === 'storage-state') return;
  if (auth.strategy === 'cookies') {
    await context.addCookies(auth.cookies ?? []);
    return;
  }
  if (auth.strategy === 'local-storage') {
    await page.addInitScript(items => {
      for (const [k, v] of Object.entries(items)) localStorage.setItem(k, String(v));
    }, auth.items ?? {});
    return;
  }
  if (auth.strategy === 'script') {
    const mod = await import(pathToFileURL(resolveMaybe(auth.script)).href);
    if (typeof mod.prepare !== 'function') throw new Error(`Auth script must export prepare(): ${auth.script}`);
    await mod.prepare({ context, page, side, source, config: cfg });
    return;
  }
  throw new Error(`Unsupported auth strategy: ${auth.strategy}`);
}

async function installMocks(page, scenario, side) {
  const mocks = side === 'legacy' ? (scenario.legacy_mocks ?? scenario.mocks ?? []) : (scenario.target_mocks ?? scenario.mocks ?? []);
  for (const mock of mocks) {
    await page.route(mock.url, async route => {
      if (mock.method && route.request().method().toUpperCase() !== mock.method.toUpperCase()) return route.continue();
      let body;
      if (mock.body_file) body = fs.readFileSync(resolveMaybe(mock.body_file), 'utf8');
      else body = JSON.stringify(mock.body ?? {});
      await route.fulfill({ status: mock.status ?? 200, contentType: mock.content_type ?? 'application/json', body });
    });
  }
}
async function runActions(page, actions = []) {
  for (const action of actions) {
    if (action.type === 'click') await page.locator(action.selector).click();
    else if (action.type === 'fill') await page.locator(action.selector).fill(action.value ?? '');
    else if (action.type === 'press') await page.locator(action.selector).press(action.key);
    else if (action.type === 'wait') await page.waitForTimeout(action.ms ?? 100);
    else if (action.type === 'select') await page.locator(action.selector).selectOption(action.value);
    else if (action.type === 'check') await page.locator(action.selector).check();
    else throw new Error(`Unsupported action type: ${action.type}`);
  }
}
async function createContext(browser, side) {
  const source = cfg[side];
  const state = authStorageState(source);
  if (state && !fs.existsSync(state)) throw new Error(`storage state missing for ${side}: ${state}`);
  return browser.newContext({
    viewport: cfg.environment.viewport,
    locale: cfg.environment.locale,
    timezoneId: cfg.environment.timezone,
    colorScheme: cfg.environment.color_scheme,
    deviceScaleFactor: cfg.environment.device_scale_factor ?? 1,
    storageState: state,
  });
}

async function doctor() {
  const result = { schema_version: '1', generated_at: new Date().toISOString(), status: 'PASS', checks: [] };
  const browser = await chromium.launch();
  result.browser_version = browser.version();
  for (const side of ['legacy', 'target']) {
    const source = cfg[side];
    try {
      const context = await createContext(browser, side);
      const page = await context.newPage();
      await applyAuth(context, page, side);
      await page.goto(source.base_url, { waitUntil: 'domcontentloaded' });
      await page.evaluate(() => document.fonts.ready);
      const requiredFonts = cfg.environment.required_fonts ?? [];
      const fontChecks = await page.evaluate(fonts => Object.fromEntries(fonts.map(f => [f, document.fonts.check(`12px "${f}"`)])), requiredFonts);
      const computedBodyFont = await page.evaluate(() => getComputedStyle(document.body).fontFamily);
      const ok = Object.values(fontChecks).every(Boolean);
      result.checks.push({ side, url: source.base_url, reachable: true, required_fonts: fontChecks, computed_body_font: computedBodyFont, status: ok ? 'PASS' : 'FAIL' });
      if (!ok) result.status = 'FAIL';
      await context.close();
    } catch (e) {
      result.status = 'FAIL';
      result.checks.push({ side, url: source.base_url, status: 'FAIL', error: String(e.message || e) });
    }
  }
  await browser.close();
  fs.writeFileSync(path.join(outputDir, 'environment.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result, null, 2));
  return result.status === 'PASS';
}

async function capture(side) {
  const source = cfg[side];
  const browser = await chromium.launch();
  const context = await createContext(browser, side);
  const sideDir = path.join(outputDir, side);
  fs.mkdirSync(sideDir, { recursive: true });
  for (const scenario of cfg.scenarios) {
    const page = await context.newPage();
    await applyAuth(context, page, side);
    await installMocks(page, scenario, side);
    const route = side === 'legacy' ? scenario.legacy_route : scenario.target_route;
    await page.goto(new URL(route, source.base_url).toString(), { waitUntil: 'domcontentloaded' });
    const actions = side === 'legacy' ? (scenario.legacy_actions ?? scenario.actions ?? []) : (scenario.target_actions ?? scenario.actions ?? []);
    await runActions(page, actions);
    const ready = side === 'legacy' ? (scenario.legacy_ready_selector ?? scenario.ready_selector) : (scenario.target_ready_selector ?? scenario.ready_selector);
    if (ready) await page.locator(ready).waitFor({ state: 'visible' });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(sideDir, `${scenario.id}.png`), fullPage: scenario.full_page ?? true, animations: 'disabled' });
    await page.close();
    console.log(`captured ${side}: ${scenario.id}`);
  }
  await context.close();
  await browser.close();
}

function sha256File(filePath) {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function compareScenario(scenario) {
  const legacyPath = path.join(outputDir, 'legacy', `${scenario.id}.png`);
  const targetPath = path.join(outputDir, 'target', `${scenario.id}.png`);
  if (!fs.existsSync(legacyPath) || !fs.existsSync(targetPath)) throw new Error(`Missing screenshot(s) for ${scenario.id}`);
  const legacy = PNG.sync.read(fs.readFileSync(legacyPath));
  const target = PNG.sync.read(fs.readFileSync(targetPath));
  const width = Math.max(legacy.width, target.width);
  const height = Math.max(legacy.height, target.height);
  const diff = new PNG({ width, height });
  let mismatchPixels;
  if (legacy.width !== target.width || legacy.height !== target.height) mismatchPixels = width * height;
  else mismatchPixels = pixelmatch(legacy.data, target.data, diff.data, width, height, { threshold: scenario.pixel_threshold ?? 0.1 });
  const diffDir = path.join(outputDir, 'diff');
  fs.mkdirSync(diffDir, { recursive: true });
  fs.writeFileSync(path.join(diffDir, `${scenario.id}.png`), PNG.sync.write(diff));
  const total = width * height;
  const ratio = total ? mismatchPixels / total : 0;
  const maxDiffPixels = scenario.max_diff_pixels ?? 0;
  const maxDiffRatio = scenario.max_diff_ratio ?? 0;
  const pass = mismatchPixels <= maxDiffPixels && ratio <= maxDiffRatio;
  return {
    id: scenario.id,
    capability: scenario.capability ?? null,
    policy: scenario.policy ?? 'STRICT_PRESERVE',
    mismatch_pixels: mismatchPixels,
    total_pixels: total,
    ratio,
    limits: { max_diff_pixels: maxDiffPixels, max_diff_ratio: maxDiffRatio },
    legacy_image: `legacy/${scenario.id}.png`,
    target_image: `target/${scenario.id}.png`,
    diff_image: `diff/${scenario.id}.png`,
    legacy_sha256: sha256File(legacyPath),
    target_sha256: sha256File(targetPath),
    diff_sha256: sha256File(path.join(diffDir, `${scenario.id}.png`)),
    status: pass ? 'PASS' : 'FAIL'
  };
}
function compareAll() {
  const results = cfg.scenarios.map(compareScenario);
  fs.writeFileSync(path.join(outputDir, 'result.json'), JSON.stringify({ schema_version: '1', generated_at: new Date().toISOString(), environment: cfg.environment, sources: { legacy: cfg.legacy.base_url, target: cfg.target.base_url }, results }, null, 2) + '\n');
  for (const r of results) console.log(`${r.status}: ${r.id} mismatch=${r.mismatch_pixels}`);
  return results.every(r => r.status === 'PASS');
}

let ok = true;
await withServers(async () => {
  if (command === 'doctor') ok = await doctor();
  else if (command === 'capture-legacy') await capture('legacy');
  else if (command === 'capture-target') await capture('target');
  else if (command === 'compare') ok = compareAll();
  else if (command === 'all') { ok = await doctor(); if (ok) { await capture('legacy'); await capture('target'); ok = compareAll(); } }
  else { console.error('Unknown command:', command); process.exit(2); }
});
process.exit(ok ? 0 : 1);
