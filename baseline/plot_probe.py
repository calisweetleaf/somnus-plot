#!/usr/bin/env python3
"""Somnus Plot v0.4 behavior probe. All writes in a disposable temp directory.
Usage: python3 plot_probe.py path/to/somnus-plot-v0.4.zip
Requires Node.js and host Python venv module. Offline and no pip installs.
The deep-rite fixture uses a shell script that *mimics* Python for bootstrap testing.
It is NOT a standalone-Python distribution validation.
"""
import hashlib, io, json, pathlib, shutil, subprocess, sys, tarfile, tempfile, zipfile

if len(sys.argv) != 2:
    raise SystemExit('usage: python3 plot_probe.py /path/to/somnus-plot-v0.4.zip')
archive_path = pathlib.Path(sys.argv[1]).resolve()
if not shutil.which('node'):
    raise SystemExit('node is required')
results = []

def check(name, condition, details=''):
    results.append({'test': name, 'passed': bool(condition), 'details': details[:500]})
    print(('PASS' if condition else 'FAIL'), name)

def runner(directory):
    try:
        result = subprocess.run(['node', 'main.js'], cwd=directory, capture_output=True,
                                text=True, timeout=35)
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 124, 'timed out'

def make_manifest(directory, **overrides):
    manifest = json.loads((directory / 'manifest.json').read_text())
    manifest.update(overrides)
    (directory / 'manifest.json').write_text(json.dumps(manifest))

def build_tar(path, entries):
    with tarfile.open(path, 'w:gz', format=tarfile.USTAR_FORMAT) as tf:
        for name, data, kind in entries:
            header = tarfile.TarInfo(name)
            if kind == 'symlink':
                header.type = tarfile.SYMTYPE
                header.linkname = data
                tf.addfile(header)
            else:
                header.mode = 0o755 if '/bin/' in name else 0o644
                header.size = len(data)
                tf.addfile(header, io.BytesIO(data))

with tempfile.TemporaryDirectory(prefix='somnus-plot-probe-') as tmp:
    root = pathlib.Path(tmp)
    original = root / 'original'
    original.mkdir()
    with zipfile.ZipFile(archive_path) as z:
        for m in z.infolist():
            parts = pathlib.PurePosixPath(m.filename)
            if parts.is_absolute() or '..' in parts.parts:
                raise SystemExit('archive path traversal rejected')
        z.extractall(original)
    for required in ['main.js', 'manifest.json']:
        if not (original / required).exists():
            raise SystemExit(f'missing {required}')

    def fresh(name):
        d = root / name
        d.mkdir()
        for fn in ['main.js','manifest.json']:
            shutil.copy2(original/fn,d/fn)
        return d

    p=fresh('shallow');code,out=runner(p)
    check('shallow Python bootstrap', code==0 and 'tenant alive:' in out, out)
    code,out=runner(p)
    check('Python tenant idempotence', code==0 and 'grave already occupied' in out, out)
    p=fresh('host');make_manifest(p,hosts=['webview'],tenants={})
    code,out=runner(p)
    check('Node host declaration enforced',code!=0 and 'does not support' in out,out)
    p=fresh('stop');make_manifest(p,tenants={},steps=[
        {'cmd':'node','args':['-e','process.exit(7)']},
        {'cmd':'node','args':['-e','console.log("BAD_REACHED")']}
    ])
    code,out=runner(p)
    check('halt on nonzero step',code==7 and 'BAD_REACHED' not in out,out)

    p=fresh('spawn-deny');make_manifest(p,tenants={},permissions={'spawn':False,'fs':[]},
        steps=[{'cmd':'node','args':['-e','console.log("SPAWN_ALLOWED")']}])
    code,out=runner(p)
    check('Node permission bypass reproduced',code==0 and 'SPAWN_ALLOWED' in out,out)
    sentinel=root/'outside-plot-sentinel.txt';sentinel.write_text('READ_ME')
    p=fresh('fs-deny');make_manifest(p,tenants={},permissions={'spawn':True,'fs':[]},
        steps=[{'cmd':'node','args':['-e',f'console.log(require("node:fs").readFileSync({json.dumps(str(sentinel))},"utf8"))']}])
    code,out=runner(p)
    check('Node filesystem scope bypass reproduced',code==0 and 'READ_ME' in out,out)
    p=fresh('args');make_manifest(p,tenants={},steps=[{'cmd':'node','args':[
        '-e','console.log(process.argv[1])','$(echo SHELL_SHOULD_NOT_RUN)']}])
    code,out=runner(p)
    check('step args stay literal',code==0 and '$(echo SHELL_SHOULD_NOT_RUN)' in out,out)

    tgz=root/'valid.tar.gz'
    build_tar(tgz,[('python/bin/python3',b'#!/bin/sh\necho "Python 3.13.9"\n','file'),
                   ('python/bin/pip',b'#!/bin/sh\necho "pip fixture"\n','file'),
                   ('python/share/x.txt',b'fixture file','file')])
    digest=hashlib.sha256(tgz.read_bytes()).hexdigest()
    p=fresh('deep');make_manifest(p,tenants={'python':{'depth':'deep','url':str(tgz),'sha256':digest}},
        steps=[{'cmd':'.grave/py/bin/python3','args':['--version']}])
    code,out=runner(p)
    check('deep offline pinned fixture',code==0 and 'sha256 verified' in out and (p/'.grave/py/share/x.txt').exists(),out)
    p=fresh('bad-pin');make_manifest(p,tenants={'python':{'depth':'deep','url':str(tgz),'sha256':'f'*64}},steps=[])
    code,out=runner(p)
    check('incorrect pin rejected',code!=0 and 'sha256 mismatch' in out,out)
    p=fresh('traversal');traversal=root/'traversal.tar.gz'
    build_tar(traversal,[('../escape.txt',b'local','file')])
    make_manifest(p,tenants={'python':{'depth':'deep','url':str(traversal),
        'sha256':hashlib.sha256(traversal.read_bytes()).hexdigest()}},steps=[])
    code,out=runner(p)
    check('direct parent traversal rejected',code!=0 and 'tar entry escapes destination' in out,out)

    p=fresh('pivot');pivot=root/'symlink-chain.tar.gz'
    build_tar(pivot,[('a','.','symlink'),('a/up','..','symlink'),
                     ('a/up/sentinel.txt',b'POINTER_ESCAPED_EXTRACTION_ROOT','file')])
    make_manifest(p,tenants={'python':{'depth':'deep','url':str(pivot),
        'sha256':hashlib.sha256(pivot.read_bytes()).hexdigest()}},steps=[])
    code,out=runner(p)
    check('chained symlink escapes extraction root REPRODUCED',
          (p/'.grave/sentinel.txt').exists() and not (p/'.grave/py/sentinel.txt').exists(),out)

    # Reuse preexisting shallow tenant after changing desired deployment depth.
    make_manifest(root/'shallow',tenants={'python':{'depth':'deep','url':str(tgz),'sha256':'f'*64}})
    code,out=runner(root/'shallow')
    check('requested Python depth change ignored REPRODUCED',
          code==0 and 'grave already occupied' in out and
          json.loads((root/'shallow/data.json').read_text())['tenant']['depth']=='shallow',out)

summary = {'checks':len(results),'confirmed':sum(v['passed'] for v in results), 'results':results}
print(f"\n{summary['confirmed']}/{summary['checks']} behavior assertions confirmed")
print('NOTE: some PASS entries intentionally confirm security or correctness DEFECTS.')
(pathlib.Path.cwd()/'somnus-plot-probe-results.json').write_text(json.dumps(summary,indent=2))
