#!/usr/bin/env node
// Somnus Plot adapter CLI (adapters/, v0.1.0). An extension surface, never part of the seed:
// it adds no bytes to main.js and changes nothing under src/ or capabilities/.
// One front door over the v0.7 seed and capabilities, plus a global manager that keeps a
// registry of plot roots: one shared global root and any number of per-project roots.
// Node standard library only (Law 5). Output is JSON on stdout; errors are JSON on stderr.
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { randomUUID } from 'node:crypto';

export const VERSION = '0.1.0';
const self = fs.realpathSync(fileURLToPath(import.meta.url));
// The Plot distribution this adapter fronts: the directory holding main.js and capabilities/.
export const DIST = process.env.PLOT_DIST ? path.resolve(process.env.PLOT_DIST) : path.resolve(path.dirname(self), '..', '..');
const CORE = path.join(DIST, 'main.js');
const CAP = name => path.join(DIST, 'capabilities', name + '.mjs');
const CEILING = 9063;
const PROJECT_DIR = '.plot';

export class PlotCliError extends Error {
  constructor(message, detail = {}) { super(message); this.detail = detail; }
}
const fail = (message, detail) => { throw new PlotCliError(message, detail); };

// ---------- manager home and registry ----------

export function managerHome(env = process.env) {
  return path.resolve(env.PLOT_HOME || path.join(os.homedir(), '.plot'));
}
const registryPath = home => path.join(home, 'registry.json');
const globalRoot = home => path.join(home, 'global');

function readJson(p, fallback) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) { if (e.code === 'ENOENT') return fallback; throw e; }
}
// Same discipline as the seed: private temp file, fsync, rename. The registry is a convenience
// index, so a lost write is recoverable with `plot adopt`; it is never an authority over a root.
function writeJson(p, value) {
  fs.mkdirSync(path.dirname(p), { recursive: true, mode: 0o700 });
  const tmp = p + '.' + randomUUID() + '.tmp';
  const fd = fs.openSync(tmp, 'wx', 0o600);
  try { fs.writeSync(fd, JSON.stringify(value, null, 2) + '\n'); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
  fs.renameSync(tmp, p);
}

export function loadRegistry(home) {
  const r = readJson(registryPath(home), null);
  if (!r) return { schema: 'plot.registry/1', roots: [] };
  if (r.schema !== 'plot.registry/1' || !Array.isArray(r.roots)) fail('registry unreadable', { path: registryPath(home) });
  return r;
}
const saveRegistry = (home, r) => writeJson(registryPath(home), r);

function register(home, entry) {
  const r = loadRegistry(home);
  const i = r.roots.findIndex(x => x.path === entry.path);
  const now = new Date().toISOString();
  if (i >= 0) r.roots[i] = { ...r.roots[i], ...entry, lastUsed: now };
  else {
    if (r.roots.some(x => x.name === entry.name)) fail('root name taken', { name: entry.name });
    r.roots.push({ ...entry, created: now, lastUsed: now });
  }
  saveRegistry(home, r);
  return r.roots.find(x => x.path === entry.path);
}

function touch(home, root) {
  const r = loadRegistry(home);
  const e = r.roots.find(x => x.path === root);
  if (e) { e.lastUsed = new Date().toISOString(); saveRegistry(home, r); }
}

const validName = n => /^[A-Za-z0-9_-]{1,64}$/.test(n) || fail('invalid name (use [A-Za-z0-9_-]{1,64})', { name: n });

// ---------- roots ----------

// A managed root's manifest. It names the resident recipe by absolute path to this
// distribution, because `${root}` inside a managed root is the root, not the distribution.
export function defaultManifest(id, python = 'shallow') {
  return {
    id,
    version: '0.7.0',
    hosts: ['node'],
    execution: 'trusted',
    permissions: { spawn: true },
    tenants: { python: { depth: python, packages: [] } },
    capabilities: {
      resident: {
        install: [{ cmd: 'node', args: ['-e', "require('node:fs').copyFileSync(process.argv[1],'resident.mjs')", CAP('resident')] }],
      },
    },
    environment: { use: [] },
  };
}

function initRoot(root, id, python) {
  fs.mkdirSync(root, { recursive: true, mode: 0o700 });
  const m = path.join(root, 'manifest.json');
  if (!fs.existsSync(m)) writeJson(m, defaultManifest(id, python));
  return root;
}

const isRoot = dir => fs.existsSync(path.join(dir, 'manifest.json'));

function nearestProject(start) {
  for (let d = path.resolve(start); ; d = path.dirname(d)) {
    const c = path.join(d, PROJECT_DIR);
    if (isRoot(c)) return c;
    if (path.dirname(d) === d) return null;
  }
}

// Resolution order: --root, --global, PLOT_ROOT, nearest <ancestor>/.plot, then the global root.
export function resolveRoot(flags, { home, cwd = process.cwd(), env = process.env, create = true } = {}) {
  home ??= managerHome(env);
  if (flags.root) {
    const r = path.resolve(cwd, flags.root);
    isRoot(r) || fail('not a plot root (no manifest.json)', { root: r });
    return { root: fs.realpathSync(r), via: '--root' };
  }
  if (!flags.global) {
    if (env.PLOT_ROOT && isRoot(env.PLOT_ROOT)) return { root: fs.realpathSync(env.PLOT_ROOT), via: 'PLOT_ROOT' };
    const p = nearestProject(cwd);
    if (p) return { root: fs.realpathSync(p), via: 'project' };
  }
  const g = globalRoot(home);
  if (!isRoot(g)) {
    if (!create) fail('global root not initialized; run `plot init --global`', { root: g });
    initRoot(g, 'global', 'shallow');
    register(home, { name: 'global', path: fs.realpathSync(g), scope: 'global' });
  }
  return { root: fs.realpathSync(g), via: 'global' };
}

function rootStatus(root) {
  const grave = path.join(root, '.grave');
  const count = d => { try { return fs.readdirSync(d).length; } catch { return 0; } };
  const envs = (() => { try { return fs.readdirSync(path.join(grave, 'envs')).filter(n => n.endsWith('.json')).map(n => n.slice(0, -5)); } catch { return []; } })();
  return {
    exists: isRoot(root),
    objects: count(path.join(grave, 'objects')),
    views: envs,
    jobs: count(path.join(grave, 'resident', 'jobs')),
    sessions: count(path.join(grave, 'resident', 'envs')),
    supervisorRecord: fs.existsSync(path.join(grave, 'resident', 'service.json')),
  };
}

// ---------- process helpers ----------

function passthrough(script, args, envExtra = {}) {
  const r = spawnSync(process.execPath, [script, ...args], { stdio: 'inherit', env: { ...process.env, ...envExtra } });
  if (r.error) throw r.error;
  return r.status ?? 1;
}

function captureJson(script, args, input) {
  const r = spawnSync(process.execPath, [script, ...args], { input, encoding: 'utf8', maxBuffer: 64 << 20 });
  if (r.error) throw r.error;
  let out = null;
  try { out = JSON.parse(r.stdout.trim().split('\n').pop()); } catch {}
  if (r.status !== 0 || out === null) fail((r.stderr || r.stdout || 'command failed').trim(), { status: r.status });
  return out;
}

const resident = (root, body) => captureJson(CAP('resident'), ['--root', root, 'request'], JSON.stringify(body));
const loadCore = async () => import(pathToFileURL(CORE).href);

function currentIncarnation(root, name) {
  return readJson(path.join(root, '.grave', 'resident', 'envs', name, 'current.json'), null)?.incarnation ?? null;
}

// ---------- argument parsing ----------

const GLOBAL_FLAGS = new Set(['--root', '--global', '--json']);
export function parseArgs(argv) {
  const flags = {}, rest = [];
  let i = 0;
  for (; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--root') { flags.root = argv[++i] ?? fail('--root needs a directory'); continue; }
    if (a === '--global') { flags.global = true; continue; }
    if (GLOBAL_FLAGS.has(a)) continue;
    break;
  }
  rest.push(...argv.slice(i));
  return { flags, cmd: rest.shift() || 'help', args: rest };
}

function take(args, name) {
  const i = args.indexOf(name);
  if (i < 0) return undefined;
  const v = args[i + 1];
  args.splice(i, 2);
  return v;
}
function has(args, name) {
  const i = args.indexOf(name);
  if (i < 0) return false;
  args.splice(i, 1);
  return true;
}
const parseSpec = s => { if (s === undefined) return undefined; try { return JSON.parse(s); } catch { fail('spec must be JSON', { spec: s }); } };

// ---------- commands ----------

const HELP = `plot ${VERSION} — Somnus Plot adapter (fronts ${DIST})

Root selection (before the command):  --root DIR | --global
  default: PLOT_ROOT, else nearest ./.plot up the tree, else the global root (${'$'}PLOT_HOME/global)

Manager
  plot init [DIR] [--name N] [--python shallow|deep]   make DIR/.plot a project root (default cwd)
  plot init --global                                    make the shared global root
  plot adopt DIR [--name N]                             register an existing plot root
  plot roots                                            list managed roots with status
  plot which                                            which root this directory resolves to, and why
  plot forget NAME|DIR                                  unregister (never deletes files)
  plot maintain [--apply] [--max-age-days N] [--jobs-days N]   prune every managed root (dry run by default)
  plot doctor                                           check node, seed, registry

Environments (seed)
  plot env list | plot env show NAME
  plot env make NAME [SPEC]          provision a named view; SPEC e.g. '{"use":["python-packages"],"python":{"packages":["requests"]}}'
  plot run [NAME] [CMD ARGS...]      run in a view (provisions NAME on first use)
  plot plan

Resident
  plot job start|stop|list|recover
  plot job submit NAME CMD ARGS...   plot job inspect|cancel ID   plot job output ID [stdout|stderr] [OFF] [LEN]
  plot job prune [JSON]               plot job request   (JSON on stdin)
  plot session open NAME [--view V] [--runtimes python,node]
  plot session exec NAME python|node CODE [--rid R] [--timeout-ms N]
  plot session inspect NAME | plot session close NAME

Capabilities (passthrough; --root is added for you where it applies)
  plot cart  plan|inspect ...         dependency cartographer
  plot asm   ...                      offline assembler / Seed Bank
  plot host  inspect|plan|acquire|verify|activate|kit ...   host bootstrap
`;

export async function main(argv, { home = managerHome(), cwd = process.cwd(), out = v => process.stdout.write(JSON.stringify(v, null, 2) + '\n') } = {}) {
  const { flags, cmd, args } = parseArgs(argv);
  const root = (create = true) => { const r = resolveRoot(flags, { home, cwd, create }); touch(home, r.root); return r; };

  switch (cmd) {
    case 'help': case '--help': case '-h': process.stdout.write(HELP); return 0;
    case 'version': case '--version': out({ cli: VERSION, dist: DIST, seed: readJson(path.join(DIST, 'package.json'), {}).version }); return 0;

    case 'init': {
      const name = take(args, '--name'), python = take(args, '--python') ?? 'shallow';
      ['shallow', 'deep'].includes(python) || fail('--python must be shallow or deep');
      if (flags.global || has(args, '--global')) {
        const g = initRoot(globalRoot(home), 'global', python);
        out(register(home, { name: 'global', path: fs.realpathSync(g), scope: 'global' })); return 0;
      }
      const dir = path.resolve(cwd, args[0] ?? '.');
      const n = name ?? path.basename(dir).replace(/[^A-Za-z0-9_-]/g, '-').slice(0, 64);
      validName(n);
      const r = initRoot(path.join(dir, PROJECT_DIR), n, python);
      out(register(home, { name: n, path: fs.realpathSync(r), scope: 'project', project: dir })); return 0;
    }

    case 'adopt': {
      const dir = path.resolve(cwd, args[0] ?? fail('adopt needs a directory'));
      const r = isRoot(dir) ? dir : isRoot(path.join(dir, PROJECT_DIR)) ? path.join(dir, PROJECT_DIR) : fail('not a plot root', { dir });
      const n = take(args, '--name') ?? path.basename(path.dirname(r) === dir ? dir : r).replace(/[^A-Za-z0-9_-]/g, '-').slice(0, 64);
      validName(n);
      out(register(home, { name: n, path: fs.realpathSync(r), scope: 'project' })); return 0;
    }

    case 'roots': {
      const r = loadRegistry(home);
      let here = null; try { here = resolveRoot(flags, { home, cwd, create: false }).root; } catch {}
      out({ home, roots: r.roots.map(e => ({ ...e, current: e.path === here, ...rootStatus(e.path) })) }); return 0;
    }

    case 'which': { const r = resolveRoot(flags, { home, cwd, create: false }); out({ ...r, ...rootStatus(r.root) }); return 0; }

    case 'forget': {
      const key = args[0] ?? fail('forget needs a name or directory');
      const r = loadRegistry(home), abs = path.resolve(cwd, key);
      const keep = r.roots.filter(e => !(e.name === key || e.path === abs || e.path === path.join(abs, PROJECT_DIR)));
      keep.length === r.roots.length && fail('no such managed root', { key });
      saveRegistry(home, { ...r, roots: keep });
      out({ forgotten: r.roots.length - keep.length, filesDeleted: false }); return 0;
    }

    case 'maintain': {
      const apply = has(args, '--apply'), age = take(args, '--max-age-days'), jobs = take(args, '--jobs-days');
      const opts = { apply, cache: age === undefined ? {} : { maxAgeDays: Number(age) }, ...(jobs === undefined ? {} : { includeJobs: { maxAgeDays: Number(jobs) } }) };
      const results = [];
      for (const e of loadRegistry(home).roots) {
        if (!isRoot(e.path)) { results.push({ name: e.name, path: e.path, skipped: 'missing' }); continue; }
        try { results.push({ name: e.name, path: e.path, result: captureJson(CAP('resident'), ['--root', e.path, 'prune', JSON.stringify(opts)]) }); }
        catch (err) { results.push({ name: e.name, path: e.path, error: err.message }); }
      }
      out({ apply, results }); return results.some(x => x.error) ? 1 : 0;
    }

    case 'doctor': {
      const [maj] = process.versions.node.split('.').map(Number);
      const core = fs.existsSync(CORE) ? fs.statSync(CORE).size : null;
      const reg = loadRegistry(home);
      const checks = {
        node: { version: process.versions.node, ok: maj >= 20 },
        dist: { path: DIST, ok: fs.existsSync(CORE) && ['resident', 'cartographer', 'assembler', 'bootstrap'].every(c => fs.existsSync(CAP(c))) },
        seed: { bytes: core, ceiling: CEILING, ok: core !== null && core <= CEILING },
        registry: { path: registryPath(home), roots: reg.roots.length, missing: reg.roots.filter(e => !isRoot(e.path)).map(e => e.name) },
        host: { platform: process.platform, arch: process.arch },
      };
      checks.registry.ok = checks.registry.missing.length === 0;
      const ok = Object.values(checks).every(c => c.ok !== false);
      out({ ok, checks }); return ok ? 0 : 1;
    }

    case 'env': {
      const sub = args.shift() ?? 'list', { root: r } = root();
      if (sub === 'list') { out({ root: r, views: rootStatus(r).views }); return 0; }
      if (sub === 'show') { const n = args[0] ?? fail('env show needs a name'); out(readJson(path.join(r, '.grave', 'envs', n + '.json'), null) ?? fail('no such view', { name: n })); return 0; }
      if (sub === 'make') {
        const n = args.shift() ?? fail('env make needs a name'); validName(n);
        const { openPlot } = await loadCore();
        out(await openPlot(r).provision(n, parseSpec(args.join(' ') || undefined))); return 0;
      }
      fail('unknown env command', { sub });
    }

    case 'run': return passthrough(CORE, ['--root', root().root, 'run', ...args]);
    case 'plan': return passthrough(CORE, ['--root', root().root, 'plan']);

    case 'job': {
      const sub = args[0] ?? 'list';
      ['start', 'stop', 'list', 'recover', 'submit', 'inspect', 'cancel', 'output', 'prune', 'request', 'provision'].includes(sub) || fail('unknown job command', { sub });
      return passthrough(CAP('resident'), ['--root', root().root, ...args]);
    }

    case 'session': {
      const sub = args.shift(), n = args.shift() ?? fail('session needs a name'), { root: r } = root();
      validName(n);
      if (sub === 'open') {
        const view = take(args, '--view'), rt = take(args, '--runtimes');
        out(resident(r, { op: 'activate', name: n, ...(view ? { view } : {}), ...(rt ? { runtimes: rt.split(',') } : {}) })); return 0;
      }
      if (sub === 'exec') {
        const rid = take(args, '--rid'), t = take(args, '--timeout-ms');
        const runtime = args.shift(); ['python', 'node'].includes(runtime) || fail('runtime must be python or node');
        const code = args.join(' ') || fs.readFileSync(0, 'utf8');
        const inc = currentIncarnation(r, n) ?? fail('session not open', { name: n });
        out(resident(r, { op: 'interact', name: n, expectIncarnation: inc, runtime, code, rid: rid ?? randomUUID(), ...(t ? { timeoutMs: Number(t) } : {}) })); return 0;
      }
      if (sub === 'inspect') { out(resident(r, { op: 'env_inspect', name: n })); return 0; }
      if (sub === 'close') { out(resident(r, { op: 'deactivate', name: n })); return 0; }
      fail('unknown session command', { sub });
    }

    case 'cart': {
      const a = [...args];
      if (!a.includes('--root') && a[0] === 'plan') a.push('--root', root().root);
      return passthrough(CAP('cartographer'), a);
    }
    case 'asm': return passthrough(CAP('assembler'), args);
    case 'host': {
      const r = root().root, a = [...args];
      if (!a.includes('--root')) a.push('--root', r);
      return passthrough(CAP('bootstrap'), a, { PLOT_ROOT: r });
    }

    default: fail('unknown command; run `plot help`', { cmd });
  }
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === self) {
  try { process.exitCode = await main(process.argv.slice(2)); }
  catch (e) { process.stderr.write(JSON.stringify({ error: e.message, ...(e.detail ? { detail: e.detail } : {}) }) + '\n'); process.exitCode = 1; }
}
