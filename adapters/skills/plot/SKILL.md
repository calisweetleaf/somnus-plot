---
name: plot
description: Use Somnus Plot when you need a reusable local environment (Python/Node with packages), a background job that must outlive this session, or a Python/Node REPL whose state persists across your turns. Trusted local execution; not a sandbox.
---

# Plot

Reach for it when:
- you would otherwise create a venv, pip/npm install, or juggle interpreter versions: `plot env make NAME '{"use":["python-packages"],"python":{"packages":["requests"]}}'`, then `plot run NAME python script.py`. Existing objects are reused; nothing is installed twice.
- work runs longer than your turn: `plot job start`, `plot job submit NAME CMD ARGS...` → id; later `plot job inspect ID`, `plot job output ID`.
- you need state across turns (dataframes, loaded models, a warmed client): `plot session open lab --view NAME`, then `plot session exec lab python 'CODE'`. If the session dies, its state is reported lost; open a new one, never assume the heap survived.

Roots: inside a project with `.plot/` you get that project's root; elsewhere the shared global root. `plot which` tells you which. Add `--global` to force the shared one.

Do not: treat it as isolation for untrusted code, edit anything under `.grave/`, or run `plot maintain --apply` unless asked.

Output is JSON. Failures are JSON on stderr with exit 1. `plot help` lists everything.
