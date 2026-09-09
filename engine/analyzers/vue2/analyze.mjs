#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

function arg(name) { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : null; }
const legacyArg = arg('--legacy');
const outputArg = arg('--output');
if (!legacyArg || !outputArg) {
  console.error('Usage: node analyze.mjs --legacy <repo> --output <dir>');
  process.exit(2);
}
const root = path.resolve(legacyArg);
const output = path.resolve(outputArg);
fs.mkdirSync(output, { recursive: true });

async function loadTypeScript() {
  const candidates = [];
  if (process.env.TYPESCRIPT_PATH) candidates.push(process.env.TYPESCRIPT_PATH);
  candidates.push(path.join(path.dirname(new URL(import.meta.url).pathname), 'node_modules/typescript/lib/typescript.js'));
  candidates.push(path.join(root, 'node_modules/typescript/lib/typescript.js'));
  try {
    const globalRoot = execFileSync('npm', ['root', '-g'], { encoding: 'utf8' }).trim();
    candidates.push(path.join(globalRoot, 'typescript/lib/typescript.js'));
  } catch {}
  for (const candidate of candidates) {
    if (!candidate || !fs.existsSync(candidate)) continue;
    const mod = await import(pathToFileURL(candidate).href);
    return mod.default ?? mod;
  }
  throw new Error('TypeScript AST engine not found. Run `modernize install-engine --analyzer` or set TYPESCRIPT_PATH.');
}
const ts = await loadTypeScript();

const EXT = new Set(['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue']);
const SKIP = new Set(['node_modules', 'dist', 'build', '.git', 'coverage', '.next']);
function walk(dir, out = []) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    if (SKIP.has(ent.name)) continue;
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(p, out);
    else if (EXT.has(path.extname(ent.name).toLowerCase())) out.push(p);
  }
  return out;
}
function rel(p) { return path.relative(root, p).split(path.sep).join('/'); }
function write(name, data) { fs.writeFileSync(path.join(output, name), JSON.stringify(data, null, 2) + '\n'); }
function extractVueScript(content) {
  const m = /<script\b[^>]*>([\s\S]*?)<\/script>/i.exec(content);
  if (!m) return { code: '', lineOffset: 0 };
  const beforeBody = content.slice(0, m.index) + m[0].slice(0, m[0].indexOf(m[1]));
  return { code: m[1], lineOffset: (beforeBody.match(/\n/g) || []).length };
}
function scriptKind(file) {
  if (/\.tsx$|\.vue$/i.test(file)) return ts.ScriptKind.TSX;
  if (/\.jsx$/i.test(file)) return ts.ScriptKind.JSX;
  if (/\.ts$/i.test(file)) return ts.ScriptKind.TS;
  return ts.ScriptKind.JS;
}
function stringValue(node) {
  if (!node) return null;
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return node.text;
  return null;
}
function propertyName(node) {
  const n = node?.name;
  if (!n) return null;
  if (ts.isIdentifier(n) || ts.isStringLiteral(n) || ts.isNumericLiteral(n)) return String(n.text);
  return null;
}
function objectProperties(obj) {
  const m = new Map();
  for (const p of obj.properties) {
    const k = propertyName(p);
    if (k) m.set(k, p);
  }
  return m;
}
function propertyInitializer(prop) {
  return prop && 'initializer' in prop ? prop.initializer : null;
}
function sourceInfo(sf, node, file, lineOffset = 0, level = 'STATIC_CONFIRMED', confidence = 1.0) {
  const start = sf.getLineAndCharacterOfPosition(node.getStart(sf));
  const end = sf.getLineAndCharacterOfPosition(node.getEnd());
  return {
    source: { file, start_line: start.line + 1 + lineOffset, end_line: end.line + 1 + lineOffset },
    extraction: { method: 'ast-typescript', confidence, level }
  };
}
function componentSummary(node) {
  if (!node) return null;
  if (ts.isIdentifier(node)) return node.text;
  if (ts.isStringLiteral(node)) return node.text;
  if (ts.isArrowFunction(node) || ts.isFunctionExpression(node)) return '<function>';
  if (ts.isCallExpression(node)) return '<call-expression>';
  return `<${ts.SyntaxKind[node.kind] ?? node.kind}>`;
}
function callName(expr) {
  if (ts.isIdentifier(expr)) return expr.text;
  if (ts.isPropertyAccessExpression(expr)) return expr.name.text;
  return null;
}

const routes = [], imports = [], apis = [], stateUses = [], warnings = [], parsedFiles = [];
let routeId = 0;

for (const filePath of walk(root)) {
  const file = rel(filePath);
  const original = fs.readFileSync(filePath, 'utf8');
  let code = original, lineOffset = 0;
  if (file.endsWith('.vue')) ({ code, lineOffset } = extractVueScript(original));
  if (!code.trim()) continue;
  let sf;
  try {
    sf = ts.createSourceFile(file, code, ts.ScriptTarget.Latest, true, scriptKind(file));
  } catch (e) {
    warnings.push({ file, warning: String(e.message || e), status: 'NEEDS_SOURCE_REVIEW' });
    continue;
  }
  parsedFiles.push(file);
  const routeFileHint = /(^|\/)(router|routers|routes)(\/|\.|$)/i.test(file);

  function visit(node) {
    if (ts.isImportDeclaration(node) && node.moduleSpecifier) {
      const spec = stringValue(node.moduleSpecifier);
      if (spec) imports.push({ kind: 'import', specifier: spec, ...sourceInfo(sf, node, file, lineOffset) });
      if (spec === 'vuex') {
        const clause = node.importClause;
        const symbols = [];
        if (clause?.namedBindings && ts.isNamedImports(clause.namedBindings)) {
          for (const el of clause.namedBindings.elements) symbols.push(el.name.text);
        }
        stateUses.push({ kind: 'vuex-import', symbols, ...sourceInfo(sf, node, file, lineOffset) });
      }
    }
    if (ts.isCallExpression(node)) {
      const cname = callName(node.expression);
      const first = node.arguments[0];
      const firstUrl = stringValue(first);
      if (ts.isIdentifier(node.expression) && node.expression.text === 'require' && firstUrl) {
        imports.push({ kind: 'require', specifier: firstUrl, ...sourceInfo(sf, node, file, lineOffset) });
      }
      if (node.expression.kind === ts.SyntaxKind.ImportKeyword && firstUrl) {
        imports.push({ kind: 'dynamic-import', specifier: firstUrl, ...sourceInfo(sf, node, file, lineOffset) });
      }
      if (cname === 'fetch' && firstUrl) {
        apis.push({ method: 'UNKNOWN', url: firstUrl, kind: 'fetch', ...sourceInfo(sf, node, file, lineOffset) });
      }
      if (ts.isPropertyAccessExpression(node.expression)) {
        const method = node.expression.name.text.toUpperCase();
        if (['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && firstUrl && /^(\/|https?:)/.test(firstUrl)) {
          apis.push({ method, url: firstUrl, kind: 'member-call', ...sourceInfo(sf, node, file, lineOffset) });
        }
        if (['DISPATCH', 'COMMIT'].includes(method)) stateUses.push({ kind: `store-${method.toLowerCase()}`, ...sourceInfo(sf, node, file, lineOffset) });
      }
      if (['mapState', 'mapGetters', 'mapActions', 'mapMutations'].includes(cname)) {
        stateUses.push({ kind: cname, ...sourceInfo(sf, node, file, lineOffset) });
      }
      if (first && ts.isObjectLiteralExpression(first)) {
        const pm = objectProperties(first);
        const url = stringValue(propertyInitializer(pm.get('url')));
        const method = (stringValue(propertyInitializer(pm.get('method'))) || 'UNKNOWN').toUpperCase();
        if (url && /^(\/|https?:)/.test(url)) apis.push({ method, url, kind: 'request-config', ...sourceInfo(sf, node, file, lineOffset) });
      }
    }
    if (ts.isPropertyAccessExpression(node) && node.name.text === '$store') {
      stateUses.push({ kind: 'this.$store', ...sourceInfo(sf, node, file, lineOffset) });
    }
    if (ts.isObjectLiteralExpression(node)) {
      const pm = objectProperties(node);
      if (pm.has('path')) {
        const structuralHint = ['component', 'children', 'redirect', 'beforeEnter', 'meta'].some(k => pm.has(k));
        if (routeFileHint || structuralHint) {
          const pathNode = propertyInitializer(pm.get('path'));
          const routePath = stringValue(pathNode);
          const level = routePath === null ? 'STATIC_INFERRED' : 'STATIC_CONFIRMED';
          routes.push({
            id: `RAW-ROUTE-${String(++routeId).padStart(5, '0')}`,
            path: routePath,
            name: stringValue(propertyInitializer(pm.get('name'))),
            redirect: stringValue(propertyInitializer(pm.get('redirect'))),
            component: componentSummary(propertyInitializer(pm.get('component'))),
            dynamic: routePath === null,
            review: routePath === null ? 'NEEDS_RUNTIME_EVIDENCE' : null,
            ...sourceInfo(sf, node, file, lineOffset, level, routePath === null ? 0.85 : 1.0)
          });
        }
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(sf);
}

let pkg = {};
try { pkg = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8')); } catch {}
const deps = { ...(pkg.dependencies || {}), ...(pkg.devDependencies || {}) };
const project = {
  root,
  name: pkg.name || path.basename(root),
  framework: { vue: deps.vue || null, vue_router: deps['vue-router'] || null, vuex: deps.vuex || null, typescript: deps.typescript || null },
  build: { webpack: deps.webpack || null, vite: deps.vite || null, vue_cli: deps['@vue/cli-service'] || null },
  scripts: pkg.scripts || {}
};
const manifest = {
  schema_version: '1', adapter: 'vue2-ast', adapter_version: '1.3.0', engine: 'typescript-compiler-api',
  parsed_files: parsedFiles.length, warnings,
  evidence_levels: ['STATIC_CONFIRMED', 'STATIC_INFERRED', 'HEURISTIC', 'RUNTIME_CONFIRMED', 'UNKNOWN']
};
write('analysis-manifest.json', manifest);
write('project.json', project);
write('routes.json', { count: routes.length, routes });
write('imports.json', { count: imports.length, edges: imports });
write('apis.json', { count: apis.length, apis });
write('state.json', { count: stateUses.length, uses: stateUses });
write('inventory.json', { manifest, project, routes, imports, apis, state: stateUses });
console.log(`PASS vue2-ast: files=${parsedFiles.length} routes=${routes.length} apis=${apis.length} imports=${imports.length}`);
