# Somnus Plot v0.7

A small seed that builds environments by composition. Optional acquired capabilities add a
resident supervisor with single-use standby workers and persistent execution environments,
a dependency cartographer, an offline layer assembler and a host bootstrap. Node standard
library only; no npm install. The foreground core stays within the original 9,063-byte ceiling.

```sh
node capabilities/resident.mjs start
node capabilities/resident.mjs provision native '{"use":[]}'
node capabilities/resident.mjs submit native node -e 'console.log("started");setTimeout(()=>console.log("finished"),1000)'
node capabilities/resident.mjs list
```

Exit the client, then use `inspect JOB_ID` and `output JOB_ID` from a new client.
`stop` stops the supervisor and leaves independent workers running. `start`
reconnects; `cancel JOB_ID` requires authenticated live worker control.

Without Node, `sh bootstrap/plot.sh` (or `bootstrap/plot.ps1` on Windows) obtains a pinned Node
into `.grave/host/` and runs the same seed. `node capabilities/bootstrap.mjs plan` shows what a host
needs before anything is written. Only Linux x64 has been run; see `bootstrap/hosts/README.md`.

Read [PERSISTENT-NATIVE.md](PERSISTENT-NATIVE.md) for the command/API surface,
resource ownership, recovery semantics, limits and reproduction commands.
Read [evidence/RESULTS.md](evidence/RESULTS.md) for measured behavior and explicit
unimplemented/unverified boundaries. Original acquisition/view details remain in
[STAGE-1.md](STAGE-1.md). The original foreground mixed-runtime demo still runs
with `node main.js` when host Python is available.
