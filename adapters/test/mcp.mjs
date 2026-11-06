// Real-process MCP checks: spawn the stdio server, speak JSON-RPC, drive real roots, jobs and sessions.
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createInterface } from 'node:readline';

const here = path.dirname(fileURLToPath(import.meta.url));
const server = path.resolve(here, '..', 'mcp', 'server.mjs'), cli = path.resolve(here, '..', 'cli', 'plot.mjs');
const tmp = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'plot-mcp-')));
const home = path.join(tmp, 'home'), proj = path.join(tmp, 'proj');
fs.mkdirSync(proj, { recursive: true });
const env = { ...process.env, PLOT_HOME: home }; delete env.PLOT_ROOT;
const s = spawn(process.execPath, [server], { cwd: tmp, env, stdio: ['pipe', 'pipe', 'inherit'] });
const waiting = new Map(); let next = 1;
createInterface({ input: s.stdout }).on('line', l => { const m = JSON.parse(l); waiting.get(m.id)?.(m); waiting.delete(m.id); });
const rpc = (method, params) => new Promise(r => { const id = next++; waiting.set(id, r); s.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n'); });
const call = async (name, args) => (await rpc('tools/call', { name, arguments: args })).result;
let pass = 0, failed = 0;
const check = async (name, fn) => { try { await fn(); pass++; console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } };
const assert = (c, m) => { if (!c) throw Error(m); };

try {
  await check('initialize negotiates protocol and names the server', async () => { const r = (await rpc('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 't', version: '0' } })).result; assert(r.serverInfo.name === 'somnus-plot' && r.capabilities.tools, JSON.stringify(r)); });
  s.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
  await check('tools/list exposes the plot verbs with schemas', async () => { const t = (await rpc('tools/list')).result.tools; assert(t.length >= 18 && t.every(x => x.inputSchema?.type === 'object'), String(t.length)); assert(t.find(x => x.name === 'plot_maintain').annotations.destructiveHint, 'maintain not destructive'); });
  await check('unknown method is a JSON-RPC error', async () => { const r = await rpc('nope/nope'); assert(r.error?.code === -32601, JSON.stringify(r)); });
  await check('plot_init creates a project root', async () => { const r = await call('plot_init', { dir: proj, name: 'proj' }); assert(!r.isError && r.structuredContent.scope === 'project', r.content[0].text); });
  await check('plot_env_make provisions a view in that root', async () => { const r = await call('plot_env_make', { cwd: proj, name: 'tools', spec: { use: [] } }); assert(!r.isError && r.structuredContent.schema === 1, r.content[0].text); });
  await check('plot_run returns foreground output', async () => { const r = await call('plot_run', { cwd: proj, view: 'tools', cmd: 'node', args: ['-e', 'console.log(6*7)'] }); assert(!r.isError && /42/.test(r.content[0].text), r.content[0].text); });
  await check('plot_run failure is isError, not a protocol error', async () => { const r = await call('plot_run', { cwd: proj, view: 'tools', cmd: 'node', args: ['-e', 'process.exit(3)'] }); assert(r.isError === true, JSON.stringify(r)); });
  await check('durable job through MCP', async () => {
    assert(!(await call('plot_resident', { cwd: proj, action: 'start' })).isError, 'start failed');
    const j = await call('plot_job_submit', { cwd: proj, view: 'tools', cmd: 'node', args: ['-e', 'console.log("mcp-job")'] }); assert(j.structuredContent?.id, j.content[0].text);
    let st; for (let i = 0; i < 100; i++) { st = (await call('plot_job_inspect', { cwd: proj, id: j.structuredContent.id })).structuredContent; if (st?.state === 'succeeded') break; await new Promise(r => setTimeout(r, 50)); }
    assert(st?.state === 'succeeded', JSON.stringify(st));
    const o = await call('plot_job_output', { cwd: proj, id: j.structuredContent.id }); assert(/mcp-job/.test(o.content[0].text), o.content[0].text);
  });
  await check('session heap persists across MCP calls; code with quotes and newlines survives', async () => {
    const a = await call('plot_session_open', { cwd: proj, name: 'lab', view: 'tools', runtimes: ['node'] }); assert(a.structuredContent?.state === 'active', a.content[0].text);
    await call('plot_session_exec', { cwd: proj, name: 'lab', runtime: 'node', code: 'globalThis.msg = "it\'s"\nglobalThis.n = 41' });
    const b = await call('plot_session_exec', { cwd: proj, name: 'lab', runtime: 'node', code: 'msg + " " + (n + 1)' }); assert(/it's 42/.test(b.content[0].text), b.content[0].text);
    assert(!(await call('plot_session_close', { cwd: proj, name: 'lab' })).isError, 'close failed');
  });
  await check('plot_roots and plot_maintain (dry run) see the project', async () => {
    const r = await call('plot_roots', {}); assert(r.structuredContent.roots.some(x => x.name === 'proj'), r.content[0].text);
    const m = await call('plot_maintain', {}); assert(!m.isError && m.structuredContent.apply === false, m.content[0].text);
  });
} finally {
  spawnSync(process.execPath, [cli, '--root', path.join(proj, '.plot'), 'job', 'stop'], { env });
  s.stdin.end(); s.kill();
  fs.rmSync(tmp, { recursive: true, force: true });
}
console.log(`\n${pass}/${pass + failed} MCP checks`);
process.exitCode = failed ? 1 : 0;
