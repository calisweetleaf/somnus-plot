// sandbox.ts
import { spawn, spawnSync } from "node:child_process";
import { readFileSync, writeFileSync as writeFileSync2, existsSync as existsSync2, mkdirSync as mkdirSync2, rmSync, createWriteStream, copyFileSync } from "node:fs";
import { join as join2, dirname as dirname2 } from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { Readable as Readable2 } from "node:stream";
import { pipeline } from "node:stream/promises";

// untar.ts
import { createGunzip } from "node:zlib";
import { createReadStream, mkdirSync, writeFileSync, chmodSync, symlinkSync, linkSync, readdirSync, rmdirSync, renameSync, existsSync, statSync } from "node:fs";
import { dirname, join, resolve, relative, sep, isAbsolute } from "node:path";
import { Readable } from "node:stream";
var cstr = (b, off, len) => b.subarray(off, off + len).toString("utf8").split("\0")[0];
var oct = (s) => parseInt(s.replace(/[^0-7]/g, ""), 8) || 0;
var clean = (p) => p.replace(/^\.?\//, "");
var hdrPath = (h) => {
  const p = cstr(h, 345, 155), n = cstr(h, 0, 100);
  return p ? `${p}/${n}` : n;
};
var inside = (root, p) => p === root || p.startsWith(root + sep);
function safeJoin(dest, rel) {
  const root = resolve(dest), p = resolve(root, rel);
  if (!inside(root, p)) throw new Error(`tar entry escapes destination: ${rel}`);
  return p;
}
async function extractTarGz(archive, dest) {
  const web = Readable.toWeb(createReadStream(archive).pipe(createGunzip()));
  const chunks = [];
  for await (const c of web) chunks.push(Buffer.from(c));
  const buf = Buffer.concat(chunks);
  let off = 0, pending = null;
  const hard = [];
  while (off + 512 <= buf.length) {
    const h = buf.subarray(off, off + 512);
    if (h[0] === 0) break;
    const size = oct(cstr(h, 124, 12).trim());
    const type = String.fromCharCode(h[156]);
    const body = off + 512, next = body + Math.ceil(size / 512) * 512;
    if (type === "g") {
    } else if (type === "x") {
      const m2 = /(?:^|\n)\d+ path=([^\n]+)/.exec(buf.subarray(body, body + size).toString());
      if (m2) pending = clean(m2[1]);
    } else if (type === "L") {
      pending = clean(buf.subarray(body, body + size).toString().replace(/\0+$/, ""));
    } else {
      const rel = clean(pending ?? hdrPath(h));
      pending = null;
      if (type === "5") mkdirSync(safeJoin(dest, rel), { recursive: true });
      else if (type === "2" || type === "1") {
        if (!rel) {
          off = next;
          continue;
        }
        const tgt = cstr(h, 157, 100);
        const p = safeJoin(dest, rel);
        mkdirSync(dirname(p), { recursive: true });
        if (type === "2") {
          if (isAbsolute(tgt) || !inside(resolve(dest), resolve(dirname(p), tgt)))
            throw new Error(`symlink escapes destination: ${rel} -> ${tgt}`);
          symlinkSync(tgt, p);
        } else {
          safeJoin(dest, clean(tgt));
          hard.push([rel, clean(tgt)]);
        }
      } else if (rel) {
        const full = safeJoin(dest, rel);
        mkdirSync(dirname(full), { recursive: true });
        writeFileSync(full, buf.subarray(body, body + size));
        chmodSync(full, oct(cstr(h, 100, 8)) & 511);
      }
    }
    off = next;
  }
  for (const [rel, tgt] of hard) {
    const a = safeJoin(dest, tgt), b = safeJoin(dest, rel);
    try {
      linkSync(a, b);
    } catch {
      symlinkSync(relative(dirname(b), a), b);
    }
  }
}
function flattenIfSingleRoot(grave, rootName = "python") {
  const inner = join(grave, rootName);
  if (!existsSync(inner)) return;
  mergeMove(inner, grave);
  rmdirSync(inner);
}
function mergeMove(src, dst) {
  for (const child of readdirSync(src)) {
    const from = join(src, child), to = join(dst, child);
    if (existsSync(to) && statSync(from).isDirectory() && statSync(to).isDirectory()) {
      mergeMove(from, to);
    } else {
      renameSync(from, to);
    }
  }
}

// sandbox.ts
var say = (s) => console.log(`[somnus] ${s}`);
var out = (cmd, args) => {
  const r = spawnSync(cmd, args, { encoding: "utf8" });
  if (r.error) throw new Error(`exec failed: ${cmd} \u2014 ${r.error.message}`);
  return (r.stdout ?? "").trim();
};
var run = (s) => new Promise((resolve2, reject) => {
  const p = spawn(s.cmd, s.args ?? [], {
    stdio: "inherit",
    cwd: s.cwd,
    env: s.env ? { ...process.env, ...s.env } : process.env
  });
  p.on("error", reject);
  p.on("exit", (c) => resolve2(c ?? 1));
});
async function fetchToFile(url, dest) {
  for (let attempt = 1; attempt <= 2; attempt++) {
    try {
      const res = await fetch(url);
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
      await pipeline(Readable2.fromWeb(res.body), createWriteStream(dest));
      return;
    } catch (e) {
      say(`fetch attempt ${attempt} failed (${e.message})`);
    }
  }
  say("borrowing host curl for the dig");
  const c = spawnSync("curl", ["-fSL", "--retry", "3", "-o", dest, url], { stdio: "inherit" });
  if (c.status !== 0) throw new Error("all fetch rites failed");
}
async function resolveStandaloneUrl() {
  const arch = { x64: "x86_64", arm64: "aarch64" }[process.arch] ?? process.arch;
  const plat = { linux: "unknown-linux-gnu", darwin: "apple-darwin" }[process.platform] ?? null;
  if (!plat) throw new Error(`no standalone rite for ${process.platform} yet (windows ships .zip \u2014 separate shovel)`);
  const res = await fetch("https://api.github.com/repos/astral-sh/python-build-standalone/releases/latest");
  const rel = await res.json();
  const want = new RegExp(`cpython-3\\.(13|12)\\.\\d+\\+.*-${arch}-${plat}-install_only\\.tar\\.gz$`);
  const asset = rel.assets?.find((a) => want.test(a.browser_download_url));
  if (!asset) throw new Error(`no standalone asset for ${arch}-${plat}`);
  return asset.browser_download_url;
}
process.chdir(dirname2(fileURLToPath(import.meta.url)));
var m = JSON.parse(readFileSync("manifest.json", "utf8"));
if (m.hosts && !m.hosts.includes("node")) throw new Error(`pack ${m.id} does not support the node host (hosts: ${m.hosts.join(",")})`);
say(`land deed: ${m.id} v${m.version}`);
var ledgerPath = "data.json";
var ledger = existsSync2(ledgerPath) ? JSON.parse(readFileSync(ledgerPath, "utf8")) : null;
var py = m.tenants?.python;
var pyBin = ".grave/py/bin/python3";
if (py) {
  const grave = ".grave/py";
  const healthy = ledger?.tenant?.kind === "python" && existsSync2(pyBin) && out(pyBin, ["--version"]).startsWith("Python");
  if (healthy) {
    say(`grave already occupied (dug ${ledger.dug_at}, ${ledger.tenant.depth}) \u2014 skipping rite`);
  } else {
    mkdirSync2(".grave", { recursive: true });
    const depth = py.depth ?? "shallow";
    if (depth === "deep") {
      const url = py.url ?? await resolveStandaloneUrl();
      say(`rite: deep dig \u2014 plot takes ownership`);
      say(`fetching ${url}`);
      const tgz = join2(grave, ".dig.tgz");
      mkdirSync2(grave, { recursive: true });
      if (url.startsWith("file://") || existsSync2(url)) {
        copyFileSync(url.replace(/^file:\/\//, ""), tgz);
        say("dig source: local mirror");
      } else await fetchToFile(url, tgz);
      const got = createHash("sha256").update(readFileSync(tgz)).digest("hex");
      if (py.sha256) {
        if (got !== py.sha256.toLowerCase()) {
          rmSync(tgz);
          throw new Error(`sha256 mismatch: want ${py.sha256} got ${got}`);
        }
        say("sha256 verified");
      } else say(`WARNING: unpinned dig \u2014 pin in manifest: sha256 ${got}`);
      say("extracting with the land's own untar (no host tar/xz needed)");
      await extractTarGz(tgz, grave);
      flattenIfSingleRoot(grave);
      rmSync(tgz);
      say(`dug: ${out(pyBin, ["--version"])}`);
    } else {
      const host = out("which", ["python3"]);
      if (!host) throw new Error("no host python to bury (use depth: deep)");
      say(`rite: shallow dig \u2014 venv over host python (${out("python3", ["--version"])})`);
      const v = spawnSync("python3", ["-m", "venv", grave], { stdio: "inherit" });
      if (v.status !== 0) throw new Error("venv burial failed");
    }
    writeFileSync2(ledgerPath, JSON.stringify({
      dug_at: (/* @__PURE__ */ new Date()).toISOString(),
      tenant: { kind: "python", version: out(pyBin, ["--version"]), depth },
      host: { platform: process.platform, arch: process.arch, runtime: `node ${process.version}` }
    }, null, 2));
    say(`ledger written: ${ledgerPath}`);
  }
  const pip = ".grave/py/bin/pip";
  for (const pkg of py.packages ?? []) {
    say(`furnishing tenant: pip install ${pkg}`);
    const r = spawnSync(pip, ["install", "--quiet", pkg], { stdio: "inherit" });
    if (r.status !== 0) throw new Error(`pip install ${pkg} failed`);
  }
}
var last = 0;
for (const [i, s] of (m.steps ?? []).entries()) {
  console.log(`
\u25B6 [${i + 1}/${m.steps?.length}] ${s.cmd} ${(s.args ?? []).join(" ")}`);
  const code = await run(s);
  if (code !== 0) {
    say(`exit ${code} at step ${i + 1} \u2014 halting`);
    last = code;
    break;
  }
}
process.exit(last);
