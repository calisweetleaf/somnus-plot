# Mixed-runtime Plot demo

This is a separate disposable demo using the original bundled `main.js`.

With Node.js and Python 3 installed, run `node main.js` in this folder. No npm install. The plot will create its own `.grave/py` and `data.json`, write `samples.json` with Node, analyze it using its Python tenant, then read `result.json` back in Node. It does not exercise the security isolation claims; all steps are trusted.

Expected result: `{ "count": 4, "total": 114, "average": 28.5 }`.
