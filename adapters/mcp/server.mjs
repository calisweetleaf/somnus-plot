#!/usr/bin/env node
// Somnus Plot MCP server (adapters/mcp, v0.1.0). Model Context Protocol over stdio,
// newline-delimited JSON-RPC 2.0, Node standard library only.
// Every tool shells out to the `plot` CLI (adapters/cli/plot.mjs) so agents and humans
// drive exactly the same verbs, roots and safety rules. Nothing here touches the seed.
import * as path from 'node:path';
import * as fs from 'node:fs';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createInterface } from 'node:readline';

export const VERSION = '0.1.0';
const PROTOCOL = '2025-06-18';
const self = fs.realpathSync(fileURLToPath(import.meta.url));
const CLI = path.resolve(path.dirname(self), '..', 'cli', 'plot.mjs');
const OUTPUT_CAP = 256 * 1024;

const rootProps = {
  root: { type: 'string', description: 'Absolute plot root directory. Omit to resolve from cwd (nearest .plot/, else global).' },
  global: { type: 'boolean', description: 'Use the shared global root.' },
  cwd: { type: 'string', description: 'Directory to resolve the root from (defaults to the server cwd).' },
};
const obj = (props = {}, required = []) => ({ type: 'object', properties: { ...rootProps, ...props }, required, additionalProperties: false });
const str = description => ({ type: 'string', description });
const strs = description => ({ type: 'array', items: { type: 'string' }, description });

// name -> { description, inputSchema, argv(input) -> plot CLI args, timeoutMs?, readOnly? }
export const TOOLS = {
  plot_doctor: { description: 'Check node version, the Plot distribution, seed byte ceiling and the root registry.', inputSchema: obj(), argv: () => ['doctor'], readOnly: true },
  plot_roots: { description: 'List every managed plot root (global and per-project) with objects, views, jobs and sessions.', inputSchema: obj(), argv: () => ['roots'], readOnly: true },
  plot_which: { description: 'Show which plot root a directory resolves to and why.', inputSchema: obj(), argv: () => ['which'], readOnly: true },
  plot_init: {
    description: 'Create and register a plot root: a project root at DIR/.plot, or the shared global root.',
    inputSchema: obj({ dir: str('Project directory (absolute). Ignored with global.'), name: str('Registry name'), python: { type: 'string', enum: ['shallow', 'deep'] } }),
    argv: i => ['init', ...(i.global ? ['--global'] : i.dir ? [i.dir] : []), ...(i.name ? ['--name', i.name] : []), ...(i.python ? ['--python', i.python] : [])],
  },
  plot_env_list: { description: 'List named views (environments) in the resolved root.', inputSchema: obj(), argv: () => ['env', 'list'], readOnly: true },
  plot_env_show: { description: 'Show one view: host, assets, interpreter, package layer, state dir.', inputSchema: obj({ name: str('View name') }, ['name']), argv: i => ['env', 'show', i.name], readOnly: true },
  plot_env_make: {
    description: 'Provision a named view. Reuses existing objects in the grave; acquires only what is missing. spec example: {"use":["python-packages"],"python":{"packages":["requests"]}}',
    inputSchema: obj({ name: str('View name [A-Za-z0-9_-]{1,64}'), spec: { type: 'object', description: 'Provision spec (use, python)' } }, ['name']),
    argv: i => ['env', 'make', i.name, ...(i.spec ? [JSON.stringify(i.spec)] : [])], timeoutMs: 600000,
  },
  plot_run: {
    description: 'Run one command in a view in the foreground and return its output. For long work use plot_job_submit.',
    inputSchema: obj({ view: str('View name'), cmd: str('Executable (python resolves to the view interpreter)'), args: strs('Arguments'), timeoutMs: { type: 'integer', minimum: 1, maximum: 3600000 } }, ['view', 'cmd']),
    argv: i => ['run', i.view, i.cmd, ...(i.args ?? [])], timeoutMs: i => i.timeoutMs ?? 120000, raw: true,
  },
  plot_resident: {
    description: 'Start, stop, list jobs of, or recover the resident supervisor for the resolved root.',
    inputSchema: obj({ action: { type: 'string', enum: ['start', 'stop', 'list', 'recover'] } }, ['action']),
    argv: i => ['job', i.action], timeoutMs: 60000,
  },
  plot_job_submit: {
    description: 'Submit a durable background job in a view. Returns a job id once an independent worker owns it; survives this client.',
    inputSchema: obj({ view: str('View name'), cmd: str('Executable'), args: strs('Arguments') }, ['view', 'cmd']),
    argv: i => ['job', 'submit', i.view, i.cmd, ...(i.args ?? [])], timeoutMs: 60000,
  },
  plot_job_inspect: { description: 'Inspect a job: state, exit, timings.', inputSchema: obj({ id: str('Job id') }, ['id']), argv: i => ['job', 'inspect', i.id], readOnly: true },
  plot_job_output: {
    description: 'Read captured job output by byte offset (max 256 KiB per read).',
    inputSchema: obj({ id: str('Job id'), stream: { type: 'string', enum: ['stdout', 'stderr'] }, offset: { type: 'integer', minimum: 0 }, bytes: { type: 'integer', minimum: 1, maximum: 262144 } }, ['id']),
    argv: i => ['job', 'output', i.id, i.stream ?? 'stdout', String(i.offset ?? 0), String(i.bytes ?? 65536)], readOnly: true,
  },
  plot_job_cancel: { description: 'Cancel a job through its live worker (signals only its own child).', inputSchema: obj({ id: str('Job id') }, ['id']), argv: i => ['job', 'cancel', i.id] },
  plot_session_open: {
    description: 'Activate a persistent session (Python and/or Node heap that survives across turns) over a view.',
    inputSchema: obj({ name: str('Session name'), view: str('View name (defaults to session name)'), runtimes: { type: 'array', items: { type: 'string', enum: ['python', 'node'] } } }, ['name']),
    argv: i => ['session', 'open', i.name, ...(i.view ? ['--view', i.view] : []), ...(i.runtimes ? ['--runtimes', i.runtimes.join(',')] : [])], timeoutMs: 60000,
  },
  plot_session_exec: {
    description: 'Run code in a live session; state persists between calls. Reusing rid returns the recorded turn instead of running twice.',
    inputSchema: obj({ name: str('Session name'), runtime: { type: 'string', enum: ['python', 'node'] }, code: str('Code to run'), rid: str('Request id for retry safety'), timeoutMs: { type: 'integer', minimum: 1, maximum: 3600000 } }, ['name', 'runtime', 'code']),
    argv: i => ['session', 'exec', i.name, i.runtime, ...(i.rid ? ['--rid', i.rid] : []), ...(i.timeoutMs ? ['--timeout-ms', String(i.timeoutMs)] : [])],
    stdin: i => i.code, timeoutMs: i => (i.timeoutMs ?? 30000) + 10000,
  },
  plot_session_inspect: { description: 'Inspect a session: incarnation, tenants, state.', inputSchema: obj({ name: str('Session name') }, ['name']), argv: i => ['session', 'inspect', i.name], readOnly: true },
  plot_session_close: { description: 'Deactivate a session (its heap ends).', inputSchema: obj({ name: str('Session name') }, ['name']), argv: i => ['session', 'close', i.name] },
  plot_plan_closure: {
    description: 'Plan the smallest npm capability closure from a local corpus (offline, executes nothing, writes nothing).',
    inputSchema: obj({ corpus: str('Directory of package dirs or .tgz archives'), specs: strs('Requested name@range specs') }, ['corpus', 'specs']),
    argv: i => ['cart', 'plan', '--corpus', i.corpus, ...i.specs], readOnly: true, raw: true,
  },
  plot_maintain: {
    description: 'Prune unpinned, unreferenced objects across every managed root. Dry run unless apply is true.',
    inputSchema: obj({ apply: { type: 'boolean' }, maxAgeDays: { type: 'number', minimum: 0 }, jobsDays: { type: 'number', minimum: 0 } }),
    argv: i => ['maintain', ...(i.apply ? ['--apply'] : []), ...(i.maxAgeDays !== undefined ? ['--max-age-days', String(i.maxAgeDays)] : []), ...(i.jobsDays !== undefined ? ['--jobs-days', String(i.jobsDays)] : [])],
    timeoutMs: 600000,
  },
};

const cap = s => (s.length > OUTPUT_CAP ? s.slice(0, OUTPUT_CAP) + `\n…[truncated ${s.length - OUTPUT_CAP} chars]` : s);

export function callTool(name, input = {}, env = process.env) {
  const t = TOOLS[name];
  if (!t) return Promise.resolve({ isError: true, content: [{ type: 'text', text: `unknown tool ${name}` }] });
  const pre = [...(input.root ? ['--root', input.root] : []), ...(input.global ? ['--global'] : [])];
  let args;
  try { args = [...pre, ...t.argv(input)]; } catch (e) { return Promise.resolve({ isError: true, content: [{ type: 'text', text: e.message }] }); }
  const timeout = typeof t.timeoutMs === 'function' ? t.timeoutMs(input) : t.timeoutMs ?? 30000;
  return new Promise(resolve => {
    const c = spawn(process.execPath, [CLI, ...args], { cwd: input.cwd || process.cwd(), env, stdio: ['pipe', 'pipe', 'pipe'] });
    let out = '', err = '', timedOut = false;
    const timer = setTimeout(() => { timedOut = true; c.kill('SIGTERM'); }, timeout);
    c.stdout.on('data', b => { if (out.length < OUTPUT_CAP * 2) out += b; });
    c.stderr.on('data', b => { if (err.length < OUTPUT_CAP * 2) err += b; });
    c.on('error', e => { clearTimeout(timer); resolve({ isError: true, content: [{ type: 'text', text: e.message }] }); });
    c.on('close', code => {
      clearTimeout(timer);
      let structured;
      if (!t.raw) { try { structured = JSON.parse(out); } catch {} }
      const isError = timedOut || code !== 0;
      const text = timedOut ? `timed out after ${timeout} ms\n${cap(out)}${cap(err)}` : isError ? cap(err || out || `exit ${code}`) : cap(out || err);
      resolve({ isError, content: [{ type: 'text', text }], ...(structured && typeof structured === 'object' && !Array.isArray(structured) && !isError ? { structuredContent: structured } : {}) });
    });
    if (t.stdin) c.stdin.end(t.stdin(input)); else c.stdin.end();
  });
}

export function listTools() {
  return Object.entries(TOOLS).map(([name, t]) => ({
    name, description: t.description, inputSchema: t.inputSchema,
    annotations: { readOnlyHint: !!t.readOnly, destructiveHint: name === 'plot_maintain' || name === 'plot_job_cancel' || name === 'plot_session_close', openWorldHint: false },
  }));
}

async function handle(msg) {
  const { id, method, params } = msg;
  const reply = result => ({ jsonrpc: '2.0', id, result });
  const error = (code, message) => ({ jsonrpc: '2.0', id, error: { code, message } });
  switch (method) {
    case 'initialize':
      return reply({ protocolVersion: params?.protocolVersion === PROTOCOL ? PROTOCOL : PROTOCOL, capabilities: { tools: { listChanged: false } }, serverInfo: { name: 'somnus-plot', version: VERSION },
        instructions: 'Somnus Plot: build and reuse local execution environments (views), run durable background jobs, and keep persistent Python/Node sessions. Trusted native execution: this is not a sandbox. Roots resolve from cwd (nearest .plot/, else the global root) unless root or global is given.' });
    case 'ping': return reply({});
    case 'tools/list': return reply({ tools: listTools() });
    case 'tools/call': {
      if (!params?.name) return error(-32602, 'missing tool name');
      if (!TOOLS[params.name]) return error(-32602, `unknown tool ${params.name}`);
      return reply(await callTool(params.name, params.arguments ?? {}));
    }
    default:
      return id === undefined ? null : error(-32601, `method not found: ${method}`);
  }
}

export function serve(input = process.stdin, output = process.stdout) {
  const rl = createInterface({ input, crlfDelay: Infinity });
  const send = m => { if (m) output.write(JSON.stringify(m) + '\n'); };
  rl.on('line', async line => {
    if (!line.trim()) return;
    let msg;
    try { msg = JSON.parse(line); } catch { return send({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'parse error' } }); }
    if (Array.isArray(msg)) { const rs = (await Promise.all(msg.map(handle))).filter(Boolean); if (rs.length) send(rs); return; }
    try { send(await handle(msg)); } catch (e) { send({ jsonrpc: '2.0', id: msg.id ?? null, error: { code: -32603, message: e.message } }); }
  });
  return rl;
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === self) serve();
