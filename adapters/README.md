# Plot adapters

`adapters/` is the extension surface over Somnus Plot v0.7. It changes nothing in the seed:
no bytes in `main.js`, no edits under `src/` or `capabilities/`, no `package.json` dependency.
The order is fixed: **a full package CLI first**, then agent surfaces (skills, MCP) built on that CLI.

| Path | What it is | Status |
| --- | --- | --- |
| `package.json` | `somnus-plot-cli` 0.1.0, `bin: plot`, zero dependencies | Landed |
| `cli/plot.mjs` | The `plot` command: global manager + front door to seed, resident, cartographer, assembler, bootstrap | Landed, 17/17 checks |
| `test/cli.mjs` | Real-process checks (throwaway `PLOT_HOME`, real resident jobs and sessions) | Landed |
| `mcp/server.mjs` | MCP server (stdio, JSON-RPC 2.0, protocol 2025-06-18), 19 tools that shell out to the same `plot` CLI | Landed, 10/10 checks |
| `skills/plot/SKILL.md` | When-to-invoke note for coding agents | Landed |

## Install

```sh
npm install -g ./adapters        # from the distribution root; npm links the folder
plot doctor
```

A global install of a local folder is a symlink, so `plot` finds the distribution (`main.js`,
`capabilities/`) two levels up from `cli/plot.mjs`. To front a different distribution, set
`PLOT_DIST=/path/to/somnus-plot`. A packed tarball alone does not carry the seed; set `PLOT_DIST`
if you install that way.

## The manager

One registry, many roots. `PLOT_HOME` defaults to `~/.plot`.

```
~/.plot/
  registry.json        plot.registry/1 — {name, path, scope: global|project, project?, created, lastUsed}
  global/              the shared global root (manifest.json + .grave/)
<project>/.plot/       a per-project root (manifest.json + .grave/)
```

Root resolution, first match wins:

1. `--root DIR`
2. `--global`
3. `PLOT_ROOT`
4. the nearest `.plot/` walking up from the working directory
5. the global root (created and registered on first use)

Project resolution reads the filesystem, not the registry. Forgetting a root never breaks it,
and `plot adopt` puts it back. The registry is an index for `roots` and `maintain`; it is never
an authority over a root's grave.

**Global vs project.** Objects are reused within one root's `.grave`, never across roots. A shared
global root with one named view per project gets the most reuse (one CPython, one copy of each
wheel, zero-spawn switching). A project root keeps that project's objects, views, jobs and sessions
separate and portable with the repo. Both are first class; pick per project.

Managed roots get a minimal manifest: trusted execution, a shallow Python tenant declared but not
required, an empty default view, and the `resident` recipe pointed at this distribution's
`capabilities/resident.mjs` by absolute path (inside a managed root, `${root}` is the root).

## Commands

```
plot init [DIR] [--name N] [--python shallow|deep]    project root at DIR/.plot
plot init --global                                     shared global root
plot adopt DIR [--name N] · plot roots · plot which · plot forget NAME|DIR
plot maintain [--apply] [--max-age-days N] [--jobs-days N]    prune every managed root; dry run by default
plot doctor

plot env list · plot env show NAME · plot env make NAME [SPEC]
plot run [NAME] [CMD ARGS...] · plot plan

plot job start|stop|list|recover|submit|inspect|cancel|output|prune|request
plot session open NAME [--view V] [--runtimes python,node]
plot session exec NAME python|node CODE [--rid R] [--timeout-ms N]   (CODE from stdin if omitted)
plot session inspect NAME · plot session close NAME

plot cart plan|inspect ...    plot asm ...    plot host inspect|plan|acquire|verify|activate|kit ...
```

Output is JSON on stdout; failures are `{"error",...}` on stderr with exit 1. `session exec`
reads the live incarnation itself and sends a fresh `rid` unless you give one, so a retried call
with the same `--rid` returns the recorded turn instead of running it twice.

## Agents

MCP clients (Claude Code, Codex, OpenCode, anything that speaks stdio MCP):

```json
{ "mcpServers": { "plot": { "command": "plot-mcp" } } }
```

Tools: `plot_doctor`, `plot_roots`, `plot_which`, `plot_init`, `plot_env_list|show|make`, `plot_run`,
`plot_resident`, `plot_job_submit|inspect|output|cancel`, `plot_session_open|exec|inspect|close`,
`plot_plan_closure`, `plot_maintain`. Each takes optional `root`, `global`, `cwd`. Every tool runs the
`plot` CLI as a child, so agents and humans hit the same verbs and the same root rules. A failing
command comes back as `isError: true` with its stderr, never as a protocol error. Read-only tools
carry `readOnlyHint`; `plot_maintain`, `plot_job_cancel`, `plot_session_close` carry `destructiveHint`.

Agents without MCP get `skills/plot/SKILL.md`: when to reach for Plot and the five commands that
matter. It is a pointer to the machinery, not a procedure (the Flash rule: the intelligence lives in
the software).

## Limits (inherited, not new)

Everything in `ARCHITECTURE.md` §7–8 still holds through the adapter: trusted native execution,
no sandbox, no quotas, Linux-only verification, PEP 440 subset for wheel planning, and the
named exceptions O-11/O-12/O-13. `maintain --apply` deletes unpinned, unreferenced objects through
the resident prune contract (tombstone intents first); it never touches a pinned object.

## Verify

```sh
node adapters/test/cli.mjs     # 17/17 on Linux aarch64, Node v22.23.3 (2026-11-05)
node adapters/test/mcp.mjs     # 10/10, same host
```
