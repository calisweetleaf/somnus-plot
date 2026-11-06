// Real-process checks for the adapter CLI. Each check runs the installed entry point against
// a throwaway PLOT_HOME and project tree; no mocks. Resident supervisors are stopped at the end.
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const cli = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'cli', 'plot.mjs');
const tmp = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'plot-cli-')));
const home = path.join(tmp, 'home'), proj = path.join(tmp, 'proj'), deep = path.join(proj, 'src', 'deep');
fs.mkdirSync(deep, { recursive: true });
const env = { ...process.env, PLOT_HOME: home }; delete env.PLOT_ROOT;
const plot = (args, cwd = tmp, input) => {
  const r = spawnSync(process.execPath, [cli, ...args], { cwd, env, input, encoding: 'utf8' });
  let json = null; try { json = JSON.parse(r.stdout); } catch {}
  return { code: r.status, out: r.stdout, err: r.stderr, json };
};
let pass = 0, failed = 0;
const check = (name, fn) => { try { fn(); pass++; console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } };
const assert = (c, m) => { if (!c) throw Error(m); };
const roots = [];

try {
  check('doctor reports a healthy distribution', () => { const r = plot(['doctor']); assert(r.json?.checks.dist.ok && r.json.checks.seed.ok, r.out + r.err); });
  check('which fails cleanly before any root exists', () => { const r = plot(['which']); assert(r.code === 1 && /global root not initialized/.test(r.err), r.err); });
  check('init --global creates and registers the global root', () => {
    const r = plot(['init', '--global']); assert(r.code === 0 && r.json.scope === 'global', r.out + r.err);
    assert(fs.existsSync(path.join(home, 'global', 'manifest.json')), 'manifest missing'); roots.push(r.json.path);
  });
  check('init in a project creates .plot and registers it', () => {
    const r = plot(['init', '--name', 'proj'], proj); assert(r.code === 0 && r.json.scope === 'project' && r.json.name === 'proj', r.out + r.err); roots.push(r.json.path);
  });
  check('init is idempotent', () => { const r = plot(['init', '--name', 'proj'], proj); assert(r.code === 0, r.err); assert(plot(['roots']).json.roots.length === 2, 'duplicate registry entry'); });
  check('which resolves the nearest project from a subdirectory', () => { const r = plot(['which'], deep); assert(r.json.via === 'project' && r.json.root === path.join(proj, '.plot'), r.out); });
  check('--global overrides the project', () => { const r = plot(['--global', 'which'], deep); assert(r.json.via === 'global', r.out); });
  check('outside any project resolves to global', () => { const r = plot(['which'], tmp); assert(r.json.via === 'global', r.out); });
  check('env make provisions a named view in the project root', () => {
    const r = plot(['env', 'make', 'tools', '{"use":[]}'], deep); assert(r.code === 0 && r.json.schema === 1, r.out + r.err);
    assert(plot(['env', 'list'], deep).json.views.includes('tools'), 'view not listed');
  });
  check('run executes in the view with PLOT_STATE set', () => {
    const r = plot(['run', 'tools', 'node', '-e', 'process.stdout.write(process.env.PLOT_STATE)'], deep);
    assert(r.code === 0 && r.out.endsWith(path.join('.plot', '.grave', 'work', 'tools')), r.out + r.err);
  });
  check('global and project roots keep separate graves', () => { assert(!plot(['--global', 'env', 'list']).json.views.includes('tools'), 'view leaked into global'); });
  check('resident job submit and inspect through the adapter', () => {
    const s = plot(['job', 'start'], deep); assert(s.code === 0, s.out + s.err);
    const j = plot(['job', 'submit', 'tools', 'node', '-e', 'console.log("hi")'], deep); assert(j.code === 0 && j.json?.id, j.out + j.err);
    let st; for (let i = 0; i < 100; i++) { st = plot(['job', 'inspect', j.json.id], deep).json; if (st?.state === 'succeeded') break; spawnSync('sleep', ['0.05']); }
    assert(st?.state === 'succeeded', JSON.stringify(st));
    const o = plot(['job', 'output', j.json.id], deep); assert(/hi/.test(o.out), o.out);
  });
  check('session keeps a Node heap across turns', () => {
    const a = plot(['session', 'open', 'lab', '--view', 'tools', '--runtimes', 'node'], deep); assert(a.json?.state === 'active', a.out + a.err);
    plot(['session', 'exec', 'lab', 'node', 'globalThis.x = 41'], deep);
    const b = plot(['session', 'exec', 'lab', 'node', 'x + 1'], deep); assert(/42/.test(b.out), b.out + b.err);
    const c = plot(['session', 'close', 'lab'], deep); assert(c.code === 0, c.err);
  });
  check('maintain dry-runs prune across every managed root', () => {
    const r = plot(['maintain']); assert(r.code === 0 && r.json.apply === false && r.json.results.length === 2 && r.json.results.every(x => x.result), r.out + r.err);
  });
  check('forget unregisters without deleting files', () => {
    const r = plot(['forget', 'proj']); assert(r.code === 0 && r.json.filesDeleted === false, r.err);
    assert(fs.existsSync(path.join(proj, '.plot', 'manifest.json')), 'files deleted');
    assert(plot(['which'], deep).json.via === 'project', 'project resolution should not depend on the registry');
  });
  check('adopt re-registers an existing root', () => { const r = plot(['adopt', proj, '--name', 'proj']); assert(r.code === 0 && r.json.path === path.join(proj, '.plot'), r.out + r.err); });
  check('unknown command fails with JSON error', () => { const r = plot(['nope']); assert(r.code === 1 && JSON.parse(r.err).error, r.err); });
} finally {
  for (const r of [path.join(proj, '.plot'), path.join(home, 'global')]) spawnSync(process.execPath, [cli, '--root', r, 'job', 'stop'], { env, encoding: 'utf8' });
  fs.rmSync(tmp, { recursive: true, force: true });
}
console.log(`\n${pass}/${pass + failed} adapter checks`);
process.exitCode = failed ? 1 : 0;
