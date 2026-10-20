# Somnus Plot v0.6

Persistent native execution with an optional acquired supervisor and independent
job workers. Node standard library only; no npm install. The foreground core stays
within the original 9,063-byte ceiling.

```sh
node capabilities/resident.mjs start
node capabilities/resident.mjs provision native '{"use":[]}'
node capabilities/resident.mjs submit native node -e 'console.log("started");setTimeout(()=>console.log("finished"),1000)'
node capabilities/resident.mjs list
```

Exit the client, then use `inspect JOB_ID` and `output JOB_ID` from a new client.
`stop` stops the supervisor and leaves independent workers running. `start`
reconnects; `cancel JOB_ID` requires authenticated live worker control.

Read [PERSISTENT-NATIVE.md](PERSISTENT-NATIVE.md) for the command/API surface,
resource ownership, recovery semantics, limits and reproduction commands.
Read [evidence/RESULTS.md](evidence/RESULTS.md) for measured behavior and explicit
unimplemented/unverified boundaries. Original acquisition/view details remain in
[STAGE-1.md](STAGE-1.md). The original foreground mixed-runtime demo still runs
with `node main.js` when host Python is available.
