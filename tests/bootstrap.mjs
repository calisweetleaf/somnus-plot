// P07-09 host bootstrap suite: inspect/plan schema, offline kit closure (Node, Python, Git), interruption
// and resume, competing acquisitions, source failure diagnostics, reuse, and the Node-absent launcher.
// Artifacts are the real pinned upstream archives, cached under the OS temp dir (never in git or evidence/).
import * as fs from 'node:fs';
import * as path from 'node:path';
import os from 'node:os';
import http from 'node:http';
import assert from 'node:assert/strict';
import {spawn,spawnSync} from 'node:child_process';
import {tar} from './helpers.mjs';
import {untar,unzip} from '../capabilities/bootstrap.mjs';
const base=path.resolve(new URL('..',import.meta.url).pathname),cap=path.join(base,'capabilities/bootstrap.mjs'),launcher=path.join(base,'bootstrap/plot.sh');
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'plot-bootstrap-test-')),kitDir=path.join(os.tmpdir(),'plot-bootstrap-kit'),cacheDir=path.join(os.tmpdir(),'plot-bootstrap-cache');
const recipes=Object.fromEntries(fs.readdirSync(path.join(base,'bootstrap/recipes')).map(n=>[n.replace(/\.json$/,''),JSON.parse(fs.readFileSync(path.join(base,'bootstrap/recipes',n)))]));
const checks=[],notRun=[],facts={timings:{},closure:{},libraries:{}};
const test=async(name,fn)=>{let t=performance.now();try{await fn();checks.push({name,passed:true,ms:Math.round(performance.now()-t)});console.log('PASS '+name)}catch(e){checks.push({name,passed:false,error:e.stack});console.error('FAIL '+name+'\n'+e.stack)}};
const skip=(name,reason)=>{notRun.push({name,reason});console.log('NOT RUN '+name+': '+reason)};
const run=(args,{env={},cwd=tmp,cmd=process.execPath,pre=[cap],clean=false}={})=>new Promise((resolve,reject)=>{let t=performance.now(),c=spawn(cmd,[...pre,...args],{cwd,env:clean?env:{...process.env,...env},stdio:['ignore','pipe','pipe']}),out='',err='';c.stdout.on('data',b=>out+=b);c.stderr.on('data',b=>err+=b);c.on('error',reject);c.on('close',code=>{let json=null;try{json=JSON.parse(out.trim().split('\n').at(-1))}catch{}resolve({code,out,err,json,ms:Math.round(performance.now()-t),child:c})});run.last=c});
const ok=r=>{if(r.code!==0)throw Error(`exit ${r.code}\n${r.out}\n${r.err}`);return r.json};
const root=n=>{let d=path.join(tmp,n);fs.mkdirSync(d,{recursive:true});return fs.realpathSync(d)};
const hostDir=r=>path.join(r,'.grave/host'),ls=d=>fs.existsSync(d)?fs.readdirSync(d).sort():[];
const art=(t,h={platform:'linux',arch:'x64',libc:'glibc'})=>recipes[t].artifacts.find(a=>[a.platform].flat().includes(h.platform)&&(a.arch==='*'||a.arch===h.arch)&&(a.libc==null||a.libc===h.libc));
const until=async(pred,ms=60000)=>{let t=Date.now();while(!pred()){if(Date.now()-t>ms)throw Error('timeout waiting');await new Promise(r=>setTimeout(r,10))}};
// Local mirror with byte ranges, throttling, flaky and corrupt modes.
let throttle=true;const served=[],flaky=new Set();
const server=http.createServer((req,res)=>{
 let [,mode,...rest]=req.url.split('/'),name=decodeURIComponent(rest.join('/')),file=path.join(kitDir,path.basename(name));served.push({mode,name:path.basename(name),range:req.headers.range||null});
 if(mode==='probe')return res.writeHead(200).end();if(mode==='missing'||!fs.existsSync(file))return res.writeHead(404).end('gone');
 let size=fs.statSync(file).size,m=/^bytes=(\d+)-$/.exec(req.headers.range||''),start=m?Number(m[1]):0;if(start>=size)return res.writeHead(416,{'content-range':`bytes */${size}`}).end();
 res.writeHead(m?206:200,{'content-length':size-start,'accept-ranges':'bytes',...(m?{'content-range':`bytes ${start}-${size-1}/${size}`}:{})});
 if(mode==='wrong'||mode==='wrongdist'){let b=fs.readFileSync(file);b[4096]^=0xff;return res.end(b.subarray(start))}
 if(mode==='flaky'&&!flaky.has(name)){flaky.add(name);let s=fs.createReadStream(file,{start,end:start+1048575});s.on('data',b=>res.write(b));s.on('end',()=>res.destroy());return}
 let s=fs.createReadStream(file,{start,highWaterMark:262144});if(mode==='slow'&&throttle){s.on('data',b=>{res.write(b);s.pause();setTimeout(()=>s.resume(),50)});s.on('end',()=>res.end())}else s.pipe(res);req.on('close',()=>s.destroy());
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const port=server.address().port,mirror=`http://127.0.0.1:${port}`,probe=['--probe-url',mirror+'/probe'];
function recipesWith(name,map){let d=path.join(tmp,'recipes-'+name);fs.mkdirSync(d);for(let [t,r] of Object.entries(recipes)){let c=structuredClone(r);for(let a of c.artifacts)if(map[t]&&a===c.artifacts[r.artifacts.indexOf(art(t))])a.url=map[t].startsWith('http')?map[t]:`${mirror}/${map[t]}/${encodeURIComponent(a.file)}`;fs.writeFileSync(path.join(d,t+'.json'),JSON.stringify(c))}return d}
const declared=['sh','mkdir','rmdir','mv','rm','cat','uname','dirname','ls','sleep','date','mktemp','cut','sed','grep','tr','wc','sync','tar','gzip','sha256sum','chmod'];
function maskedBin(name,extra=[]){let d=path.join(tmp,'bin-'+name);fs.mkdirSync(d);for(let t of [...declared,...extra]){let x=spawnSync('sh',['-c','command -v '+t],{encoding:'utf8'}).stdout.trim();if(!x)throw Error('declared prerequisite missing on this host: '+t);fs.symlinkSync(x,path.join(d,t))}return d}
function deploy(name,steps){let d=root(name);fs.mkdirSync(path.join(d,'capabilities'));for(let x of ['main.js','package.json'])fs.copyFileSync(path.join(base,x),path.join(d,x));fs.cpSync(path.join(base,'bootstrap'),path.join(d,'bootstrap'),{recursive:true});fs.copyFileSync(cap,path.join(d,'capabilities/bootstrap.mjs'));
 fs.writeFileSync(path.join(d,'manifest.json'),JSON.stringify({id:'launcher-proof',version:'0.7.0',hosts:['node'],execution:'trusted',permissions:{spawn:true},capabilities:{stamp:{install:[{cmd:'node',args:['-e',"require('fs').writeFileSync('stamp.txt',process.execPath)"]}]}},environment:{use:['stamp']},steps}));return d}
const nodeStep=[{cmd:'node',args:['-e','console.log(JSON.stringify({execPath:process.execPath,version:process.version}))']}];
const marker=d=>JSON.parse(fs.readFileSync(path.join(d,'.plot-host.json'),'utf8'));
const ldd=x=>{let r=spawnSync('ldd',[x],{encoding:'utf8'});return r.status===0?r.stdout.split('\n').map(l=>l.trim().split(' ')[0]).filter(l=>l&&!l.startsWith('linux-vdso')):'ldd unavailable'};
let kitReady=false,online=false;
try{
 let k=await run(['kit',kitDir,'--hosts','linux-x64,win32-x64','--quiet',...(fs.existsSync(cacheDir)?['--from',cacheDir]:[])]);
 kitReady=k.code===0;if(!kitReady)console.log('kit build failed (offline and no cache?): '+k.out+k.err);
 try{online=(await fetch('https://nodejs.org/dist/',{method:'HEAD',signal:AbortSignal.timeout(8000)})).ok}catch{}
 const kit=['--kit',kitDir];

 await test('inspect reports host, libc, roots, executables, transports, extractors and network mode',async()=>{
  let j=ok(await run(['inspect','--root',root('inspect'),'--quiet',...probe]));assert.equal(j.schema,'plot.bootstrap-inspect/1');assert.equal(j.host.platform,process.platform);assert.equal(j.host.arch,process.arch);
  let l=spawnSync('ldd',['--version'],{encoding:'utf8'}),txt=(l.stdout||'')+(l.stderr||'');if(/musl/i.test(txt))assert.equal(j.host.libc,'musl');else if(/GLIBC|GNU libc/i.test(txt)){assert.equal(j.host.libc,'glibc');assert.equal(j.host.glibc,/(\d+\.\d+)\s*$/m.exec(txt.split('\n')[0])[1])}
  for(let r of j.roots)assert.ok('writable' in r&&'freeBytes' in r);assert.ok(j.roots.find(r=>r.role==='install').writable);
  for(let t of ['node','tar','gzip','curl','wget','sh'])assert.ok(t in j.executables);assert.equal(j.transports.fetch,true);assert.equal(j.extractors['builtin-ustar'],true);assert.equal(j.network.mode,'online');assert.equal(j.network.probe.status,200);
  let off=ok(await run(['inspect','--offline','--quiet']));assert.equal(off.network.mode,'offline');
 });
 if(!kitReady)skip('kit-dependent checks','offline kit could not be built: no network and no cache at '+cacheDir);
 else{
 await test('plan emits a prerequisite DAG with source, provenance, compatibility, destination, disk and network needs',async()=>{
  let r=root('plan'),j=ok(await run(['plan','--root',r,...kit,'--offline','--quiet']));assert.equal(j.schema,'plot.bootstrap-plan/1');assert.equal(j.ok,true);
  let ids=j.order,z=ids.findIndex(x=>x.startsWith('zlib-')),g=ids.findIndex(x=>x.startsWith('git-'));assert.ok(z>=0&&z<g,'zlib precedes git');
  for(let n of j.nodes){for(let k of ['id','tool','version','route','status','needs','source','provenance','compatibility','destination','disk','network','system'])assert.ok(k in n,n.id+' lacks '+k);
   assert.equal(n.status,'acquire');assert.equal(n.source.kind,'kit');assert.equal(n.source.sha256,art(n.tool).sha256);assert.equal(n.network.required,false);assert.equal(n.compatibility.ok,true);assert.ok(n.destination.startsWith(path.join(r,'.grave/host/'+n.id+'-')))}
  let git=j.nodes.find(n=>n.tool==='git');assert.deepEqual(git.needs,[ids[z]]);assert.equal(git.route,'source-build');assert.deepEqual(git.system.map(s=>s.name),['sh','cc','make']);
  let none=await run(['plan','--root',r,'--offline','--quiet']);assert.equal(none.code,1);assert.equal(none.json.ok,false);assert.ok(none.json.unsupported.every(u=>u.status==='blocked'&&/offline and no kit carries/.test(u.reason)));
  let on=ok(await run(['plan','node','--root',r,'--quiet',...probe]));assert.equal(on.nodes[0].source.kind,'online');assert.equal(on.nodes[0].network.bytes,art('node').size);assert.deepEqual(on.nodes[0].network.hosts,['nodejs.org']);
 });
 await test('plan names unsupported routes and per-host sources for foreign targets without claiming them',async()=>{
  let r=root('targets'),a=await run(['plan','--root',r,'--target','android-arm64','--offline','--quiet']);assert.equal(a.json.ok,false);
  let un=Object.fromEntries(a.json.unsupported.map(u=>[u.id.split('-')[0],u]));assert.equal(un.node.status,'unsupported');assert.match(un.node.reason,/Android/);assert.match(un.node.reason,/PLOT_NODE/);assert.equal(un.python.status,'unsupported');
  let w=await run(['plan','--root',r,'--target','win32-x64',...kit,'--offline','--quiet']);let wn=Object.fromEntries(w.json.nodes.map(n=>[n.tool,n]));assert.equal(wn.git.route,'binary');assert.equal(wn.git.exe,'cmd/git.exe');assert.equal(wn.node.source.kind,'kit');assert.ok(!('zlib' in wn));
  let m=await run(['plan','node','--root',r,'--target','linux-x64-musl','--offline','--quiet']);assert.match(m.json.nodes[0].source.publisher,/unofficial/);assert.equal(m.json.nodes[0].id,'node-24.22.0-linux_musl-x64');
  let g=await run(['plan','node','--root',r,'--target','linux-x64-glibc','--offline','--quiet']);assert.equal(g.json.nodes[0].compatibility.ok,null);assert.match(g.json.nodes[0].compatibility.problems[0],/glibc version unknown/);
  let x=await run(['acquire','node','--root',r,'--target','win32-x64','--offline','--quiet']);assert.equal(x.code,1);assert.equal(x.json.error.code,'bad-target');
 });
 await test('launcher pins agree with recipes (plot.sh and plot.ps1)',()=>{
  let sh=fs.readFileSync(launcher,'utf8'),ps=fs.readFileSync(path.join(base,'bootstrap/plot.ps1'),'utf8'),v=recipes.node.version;assert.match(sh,new RegExp(`^NODE_VERSION=${v}$`,'m'));assert.match(ps,new RegExp(`NodeVersion = '${v}'`));
  let pins=[...sh.matchAll(/file=node-v\$NODE_VERSION-(\S+) sha=([0-9a-f]{64}) size=(\d+)/g)];assert.equal(pins.length,6);
  for(let [,t,sha,size] of pins){let a=recipes.node.artifacts.find(a=>a.file===`node-v${v}-${t}`);assert.ok(a,t);assert.equal(a.sha256,sha);assert.equal(a.size,Number(size))}
  let w=recipes.node.artifacts.find(a=>a.platform==='win32');assert.ok(ps.includes(`Sha256 = '${w.sha256}'; Size = ${w.size}`));assert.ok(ps.includes('File = "node-v$NodeVersion-win-x64.zip"'));
 });
 let A=root('kit-install');
 await test('offline kit installs the Node, Python and Git closure transactionally (cold)',async()=>{
  let j=ok(await run(['acquire','node','python','git','--root',A,...kit,'--offline','--quiet']));assert.deepEqual(j.results.map(r=>r.action),['acquired','acquired','acquired','acquired']);
  for(let x of j.results){assert.equal(x.source,'kit');let m=marker(x.path);assert.equal(m.id,x.id);assert.equal(m.path,x.path);assert.ok(m.tree.files>0);facts.timings['cold_kit_'+x.id]=x.ms;facts.closure[x.id]={bytes:m.tree.bytes,files:m.tree.files,links:m.tree.links,path:x.path}}
  let H=hostDir(A);assert.deepEqual(ls(path.join(H,'.stage')),[]);assert.deepEqual(ls(path.join(H,'.build')),[]);assert.deepEqual(ls(path.join(H,'.locks')),[]);assert.equal(ls(path.join(H,'.attempts')).length,4);
  for(let n of ls(H).filter(n=>!n.startsWith('.')))assert.ok(fs.existsSync(path.join(H,n,'.plot-host.json')),n+' marked');
 });
 const inst=t=>{let n=ls(hostDir(A)).find(n=>n.startsWith(t+'-'));return n&&path.join(hostDir(A),n)};
 await test('acquired Python runs real code with host PATH masked',()=>{
  let py=inst('python');assert.ok(py,'python installed');let r=spawnSync(path.join(py,'bin/python3'),['-I','-c','import sys,ssl,sqlite3,ctypes,zlib,json;print(json.dumps([sys.executable,sys.prefix,sys.version.split()[0],ssl.OPENSSL_VERSION,sqlite3.sqlite_version]))'],{encoding:'utf8',env:{PATH:'/nonexistent'}});
  assert.equal(r.status,0,r.stderr);let [exe,prefix,ver]=JSON.parse(r.stdout);assert.ok(exe.startsWith(py));assert.equal(fs.realpathSync(prefix),py);assert.equal(ver,recipes.python.version);facts.python=JSON.parse(r.stdout);facts.libraries.python=ldd(path.join(py,'bin/python3'));
 });
 await test('acquired Git performs a real init, commit, log and fsck on a local repository',()=>{
  let g=inst('git');assert.ok(g,'git installed');let git=path.join(g,'bin/git'),repo=root('git-repo'),env={PATH:path.join(g,'bin'),HOME:repo,GIT_CONFIG_NOSYSTEM:'1'};
  const G=(...a)=>{let r=spawnSync(git,a,{cwd:repo,encoding:'utf8',env});if(r.status!==0)throw Error(a.join(' ')+': '+r.stderr);return r.stdout.trim()};
  assert.match(G('--version'),/^git version 2\.56\.0/);assert.equal(fs.realpathSync(G('--exec-path')),path.join(g,'libexec/git-core'));
  G('init','-q','.');assert.ok(fs.existsSync(path.join(repo,'.git/hooks')),'templates resolved through RUNTIME_PREFIX');
  // Identity is repo-local to this scratch repository only.
  G('config','user.name','plot bootstrap test');G('config','user.email','bootstrap@plot.invalid');
  fs.writeFileSync(path.join(repo,'a.txt'),'seventh flash\n');G('add','a.txt');G('commit','-q','-m','acquired git commit');fs.appendFileSync(path.join(repo,'a.txt'),'second\n');G('commit','-q','-am','second');
  assert.deepEqual(G('log','--format=%s').split('\n'),['second','acquired git commit']);assert.equal(G('cat-file','-p','HEAD:a.txt'),'seventh flash\nsecond');G('fsck','--strict');
  facts.git={version:G('--version'),head:G('rev-parse','HEAD')};facts.libraries.git=ldd(git);facts.libraries.node=ldd(path.join(inst('node'),'bin/node'));
 });
 await test('reuse performs no fetch, extraction or build',async()=>{
  let before=ls(hostDir(A)).map(n=>[n,fs.existsSync(path.join(hostDir(A),n,'.plot-host.json'))?fs.statSync(path.join(hostDir(A),n,'.plot-host.json')).mtimeMs:0]);
  let j=ok(await run(['acquire','node','python','git','--root',A,...kit,'--offline','--quiet']));assert.ok(j.results.every(r=>r.action==='reuse'));facts.timings.reuse_closure_process_ms=(await run(['acquire','--root',A,...kit,'--offline','--quiet'])).ms;facts.timings.reuse_closure_internal_ms=j.results.reduce((a,r)=>a+r.ms,0);
  assert.deepEqual(ls(hostDir(A)).map(n=>[n,fs.existsSync(path.join(hostDir(A),n,'.plot-host.json'))?fs.statSync(path.join(hostDir(A),n,'.plot-host.json')).mtimeMs:0]),before);assert.equal(ls(path.join(hostDir(A),'.attempts')).length,4);
 });
 await test('verify detects tampering and activate exports the acquired tools',async()=>{
  let v=ok(await run(['verify','--root',A,'--quiet']));assert.ok(v.tools.every(t=>t.tree==='match'&&t.probe.ok));
  let h=path.join(inst('node'),'include/node/node_version.h'),orig=fs.readFileSync(h);fs.chmodSync(h,0o644);fs.appendFileSync(h,'// tampered\n');
  let bad=await run(['verify','node','--root',A,'--quiet']);assert.equal(bad.code,1);assert.equal(bad.json.tools.find(t=>t.id.startsWith('node')).tree,'mismatch');fs.writeFileSync(h,orig);ok(await run(['verify','node','--root',A,'--quiet']));
  let a=ok(await run(['activate','--root',A,'--quiet']));assert.ok(a.env.PATH.startsWith(path.join(inst('node'),'bin')));assert.deepEqual(Object.keys(a.tools).sort(),['git','node','python']);
  let s=await run(['activate','--root',A,'--format','sh','--quiet']),r=spawnSync('sh',['-c',s.out+'command -v node; command -v python3; command -v git'],{encoding:'utf8',env:{PATH:'/usr/bin:/bin'}});assert.deepEqual(r.stdout.trim().split('\n'),[path.join(inst('node'),'bin/node'),path.join(inst('python'),'bin/python3'),path.join(inst('git'),'bin/git')]);
 });
 await test('interrupted download is never adopted and resumes from the partial bytes',async()=>{
  let B=root('resume'),rec=recipesWith('resume',{python:'slow'}),a=art('python'),part=path.join(hostDir(B),'.dl',a.sha256+'.part');throttle=true;
  let p=run(['acquire','python','--root',B,'--recipes',rec,'--quiet',...probe]),child=run.last;await until(()=>fs.existsSync(part)&&fs.statSync(part).size>=8388608);child.kill('SIGKILL');await p;
  let have=fs.statSync(part).size;assert.ok(have>0&&have<a.size);assert.deepEqual(ls(hostDir(B)).filter(n=>!n.startsWith('.')),[]);assert.deepEqual(ls(path.join(hostDir(B),'.locks')),['python-3.12.15-linux-x64']);
  throttle=false;served.length=0;let j=ok(await run(['acquire','python','--root',B,'--recipes',rec,'--quiet',...probe])),x=j.results[0];
  assert.equal(x.action,'acquired');assert.equal(x.resumedFrom,have);assert.equal(x.brokeLocks.length,1);assert.ok(served.some(s=>s.range===`bytes=${have}-`),'Range request sent');assert.equal(marker(x.path).source.sha256,a.sha256);assert.ok(!fs.existsSync(part));
  ok(await run(['verify','python','--root',B,'--quiet']));facts.timings.resume_python_ms=x.ms;facts.resume={killedAtBytes:have,total:a.size};
 });
 await test('interrupted extraction is never adopted and is swept by the next attempt',async()=>{
  let C=root('extract-kill'),st=path.join(hostDir(C),'.stage');let p=run(['acquire','node','--root',C,...kit,'--offline','--quiet']),child=run.last;
  await until(()=>ls(st).some(n=>ls(path.join(st,n)).length>0)||ls(hostDir(C)).some(n=>n.startsWith('node-')));child.kill('SIGKILL');await p;
  assert.ok(!ls(hostDir(C)).some(n=>!n.startsWith('.')&&fs.existsSync(path.join(hostDir(C),n,'.plot-host.json'))),'no completed install');
  let j=ok(await run(['acquire','node','--root',C,...kit,'--offline','--quiet'])),x=j.results[0];assert.equal(x.action,'acquired');assert.ok(x.recovered.length>=1,'stale stage swept');assert.equal(x.brokeLocks.length,1);
  assert.deepEqual(ls(st),[]);assert.equal(ls(hostDir(C)).filter(n=>!n.startsWith('.')).length,1);ok(await run(['verify','node','--root',C,'--quiet']));
 });
 await test('competing acquisitions share one install through the slot lock',async()=>{
  let D=root('compete'),rs=await Promise.all([0,1,2,3].map(()=>run(['acquire','node','--root',D,...kit,'--offline','--quiet'])));
  let res=rs.map(r=>ok(r).results[0]);assert.equal(new Set(res.map(r=>r.path)).size,1);assert.equal(res.filter(r=>r.action==='acquired').length,1);assert.ok(res.every(r=>['acquired','shared','reuse'].includes(r.action)));
  assert.equal(ls(hostDir(D)).filter(n=>!n.startsWith('.')).length,1);assert.deepEqual(ls(path.join(hostDir(D),'.stage')),[]);assert.deepEqual(ls(path.join(hostDir(D),'.locks')),[]);facts.compete=res.map(r=>r.action);
 });
 await test('source failures return actionable diagnostics and install nothing',async()=>{
  let E=root('failures');
  let r404=await run(['acquire','node','--root',E,'--recipes',recipesWith('missing',{node:'missing'}),'--quiet',...probe]);assert.equal(r404.code,1);assert.equal(r404.json.error.code,'source-unavailable');assert.equal(r404.json.error.status,404);assert.match(r404.json.error.hint,/--kit/);
  let bad=await run(['acquire','node','--root',E,'--recipes',recipesWith('wrong',{node:'wrong'}),'--quiet',...probe]);assert.equal(bad.json.error.code,'sha256-mismatch');assert.equal(bad.json.error.expected,art('node').sha256);assert.notEqual(bad.json.error.actual,bad.json.error.expected);assert.deepEqual(ls(path.join(hostDir(E),'.dl')),[]);
  let dead=http.createServer();await new Promise(r=>dead.listen(0,'127.0.0.1',r));let dp=dead.address().port;await new Promise(r=>dead.close(r));
  let refused=await run(['acquire','node','--root',E,'--recipes',recipesWith('refused',{node:`http://127.0.0.1:${dp}/x/node.tar.gz`}),'--retries','2','--backoff-ms','10','--quiet',...probe]);assert.equal(refused.json.error.code,'source-unavailable');assert.equal(refused.json.error.attempts.length,2);assert.match(JSON.stringify(refused.json.error.attempts),/ECONNREFUSED/);
  let flaky=ok(await run(['acquire','zlib','--root',E,'--recipes',recipesWith('flaky',{zlib:'flaky'}),'--retries','4','--backoff-ms','10','--quiet',...probe])).results[0];assert.equal(flaky.action,'acquired');assert.ok(flaky.attempts.length>=2&&flaky.attempts.at(-1).from>0,'transient cut resumed by range');
  let off=await run(['acquire','python','--root',E,'--offline','--quiet']);assert.equal(off.json.error.code,'no-source');assert.match(off.json.error.message,/offline and no kit carries/);
  let fk=root('fake-kit');fs.writeFileSync(path.join(fk,'kit.json'),JSON.stringify({schema:'plot.kit/1',artifacts:[{...art('node'),tool:'node',version:'24.22.0',sha256:'0'.repeat(64)}]}));fs.writeFileSync(path.join(fk,art('node').file),'not node');
  let conf=await run(['plan','node','--root',E,'--kit',fk,'--offline','--quiet']);assert.match(conf.json.unsupported[0].reason,/refusing a different artifact/);
  assert.deepEqual(ls(hostDir(E)).filter(n=>!n.startsWith('.')&&!n.startsWith('zlib-')),[]);assert.deepEqual(ls(path.join(hostDir(E),'.stage')),[]);assert.deepEqual(ls(path.join(hostDir(E),'.locks')),[]);
 });
 await test('a failed forced re-acquisition preserves the prior install',async()=>{
  const installsOf=()=>ls(hostDir(A)).filter(x=>!x.startsWith('.'));let n=inst('node'),m=fs.readFileSync(path.join(n,'.plot-host.json')),before=installsOf();
  let r=await run(['acquire','node','--force','--root',A,'--recipes',recipesWith('force',{node:'missing'}),'--quiet',...probe]);assert.equal(r.code,1);assert.equal(r.json.error.code,'source-unavailable');
  assert.deepEqual(installsOf(),before);assert.deepEqual(ls(path.join(hostDir(A),'.dl')),[]);assert.deepEqual(fs.readFileSync(path.join(n,'.plot-host.json')),m);assert.deepEqual(ls(path.join(hostDir(A),'.stage')),[]);assert.deepEqual(ls(path.join(hostDir(A),'.locks')),[]);ok(await run(['verify','node','--root',A,'--quiet']));
 });
 await test('Node-absent launcher obtains Node from an offline kit and starts the same main.js',async()=>{
  let dep=deploy('launch-kit',nodeStep),bin=maskedBin('kit'),away=root('foreign-cwd'),env={PATH:bin,HOME:away,PLOT_KIT:kitDir};
  assert.notEqual(spawnSync('/bin/sh',['-c','command -v node'],{env:{PATH:bin}}).status,0,'node must be absent from the launcher PATH');
  let cold=await run([path.join(dep,'bootstrap/plot.sh'),'run'],{cmd:'/bin/sh',pre:[],env,cwd:away,clean:true});assert.equal(cold.code,0,cold.err);
  let out=JSON.parse(cold.out.trim().split('\n').at(-1)),H=hostDir(dep),nd=ls(H).filter(n=>n.startsWith('node-'));assert.equal(nd.length,1);assert.equal(out.execPath,path.join(H,nd[0],'bin/node'));assert.equal(out.version,'v'+recipes.node.version);
  assert.equal(fs.readFileSync(path.join(JSON.parse(fs.readFileSync(path.join(dep,'data.json'))).assets.stamp.path,'stamp.txt'),'utf8'),out.execPath);assert.equal(marker(path.join(H,nd[0])).writer,'plot.sh');assert.equal(marker(path.join(H,nd[0])).source.kind,'kit');
  let warm=await run([path.join(dep,'bootstrap/plot.sh'),'run'],{cmd:'/bin/sh',pre:[],env,cwd:away,clean:true});assert.equal(warm.code,0,warm.err);assert.doesNotMatch(warm.err,/acquired/);
  let v=await run([path.join(dep,'bootstrap/plot.sh'),'bootstrap','verify','node','--quiet'],{cmd:'/bin/sh',pre:[],env,cwd:away,clean:true});assert.equal(v.code,0,v.out+v.err);assert.equal(v.json.tools[0].tree,'unrecorded');assert.equal(v.json.tools[0].writer,'plot.sh');
  let pl=await run([path.join(dep,'bootstrap/plot.sh'),'bootstrap','plan','--offline','--quiet'],{cmd:'/bin/sh',pre:[],env:{...env,PLOT_KIT:''},cwd:away,clean:true});assert.equal(pl.json.nodes.find(n=>n.tool==='node').status,'present');
  facts.timings.launcher_kit_cold_ms=cold.ms;facts.timings.launcher_warm_ms=warm.ms;facts.launcherPath=declared;
 });
 await test('launcher wget transport resumes a partial download from a pinned mirror',async()=>{
  let dep=deploy('launch-wget',nodeStep),bin=maskedBin('wget',['wget']),a=art('node'),dl=path.join(hostDir(dep),'.dl');fs.mkdirSync(dl,{recursive:true});
  let src=fs.readFileSync(path.join(kitDir,a.file));fs.writeFileSync(path.join(dl,a.sha256+'.part'),src.subarray(0,10485760));served.length=0;
  let r=await run([path.join(dep,'bootstrap/plot.sh'),'run'],{cmd:'/bin/sh',pre:[],env:{PATH:bin,HOME:tmp,PLOT_NODE_MIRROR:mirror+'/dist'},clean:true});assert.equal(r.code,0,r.err);
  assert.ok(served.some(s=>s.mode==='dist'&&s.range==='bytes=10485760-'),'wget sent a Range request');assert.match(r.err,/resuming/);let m=marker(path.join(hostDir(dep),ls(hostDir(dep)).find(n=>n.startsWith('node-'))));assert.equal(m.source.kind,'online');assert.equal(m.source.url,`${mirror}/dist/v24.22.0/${a.file}`);assert.deepEqual(ls(dl),[]);
 });
 await test('launcher refuses a corrupt source and an unpinned host with actionable messages',async()=>{
  let dep=deploy('launch-bad',nodeStep),bin=maskedBin('bad',['wget']);
  let r=await run([path.join(dep,'bootstrap/plot.sh'),'run'],{cmd:'/bin/sh',pre:[],env:{PATH:bin,HOME:tmp,PLOT_NODE_MIRROR:mirror+'/wrongdist'},clean:true});assert.notEqual(r.code,0);assert.match(r.err,/sha256 mismatch/);assert.deepEqual(ls(hostDir(dep)).filter(n=>!n.startsWith('.')),[]);assert.deepEqual(ls(path.join(hostDir(dep),'.locks')),[]);
  // Shim uname to report Android; this exercises the refusal branch only and proves nothing about Termux.
  let sim=path.join(tmp,'bin-android');fs.cpSync(bin,sim,{recursive:true,verbatimSymlinks:true});fs.rmSync(path.join(sim,'uname'));fs.writeFileSync(path.join(sim,'uname'),'#!/bin/sh\ncase $1 in -s) echo Linux;; -m) echo aarch64;; -o) echo Android;; esac\n',{mode:0o755});
  let an=await run([path.join(dep,'bootstrap/plot.sh'),'run'],{cmd:'/bin/sh',pre:[],env:{PATH:sim,HOME:tmp},clean:true});assert.equal(an.code,1);assert.match(an.err,/android-arm64/);assert.match(an.err,/PLOT_NODE/);
  let off=await run([path.join(dep,'bootstrap/plot.sh'),'run'],{cmd:'/bin/sh',pre:[],env:{PATH:bin,HOME:tmp,PLOT_OFFLINE:'1'},clean:true});assert.equal(off.code,1);assert.match(off.err,/offline and no kit carries/);
 });
 await test('builtin zip extractor unpacks the pinned Windows Node archive exactly (extraction only, no Windows execution)',async()=>{
  let a=art('node',{platform:'win32',arch:'x64',libc:null}),d=root('zip');let x=await unzip(path.join(kitDir,a.file),d,{strip:1});assert.equal(x.bytes,a.unpacked);assert.ok(fs.statSync(path.join(d,'node.exe')).size>1e7);
 });
 }
 await test('builtin tar extractor rejects traversal, link escape, entries below links and duplicates',async()=>{
  let cases={traversal:[{name:'top/../../x',data:'x'}],abs:[{name:'/etc/x',data:'x'}],escape:[{name:'top/l',type:'2',target:'../../outside'}],below:[{name:'top/l',type:'2',target:'sub'},{name:'top/l/x',data:'x'}],duplicate:[{name:'top/a',data:'1'},{name:'top/a',data:'2'}],device:[{name:'top/dev',type:'3'}]};
  for(let [k,entries] of Object.entries(cases)){let d=root('tar-'+k),f=path.join(tmp,k+'.tgz');fs.writeFileSync(f,tar(entries));await assert.rejects(untar(f,d,{strip:1}),/archive|tar|symlink|duplicate|unsupported/,k);assert.ok(!fs.existsSync(path.join(tmp,'outside')));}
  let d=root('tar-good'),f=path.join(tmp,'good.tgz');fs.writeFileSync(f,tar([{name:'top/',type:'5'},{name:'top/bin/run',data:'#!/bin/sh\n',mode:0o755},{name:'top/run',type:'2',target:'bin/run'}]));await untar(f,d,{strip:1});assert.equal(fs.readlinkSync(path.join(d,'run')),'bin/run');assert.ok(fs.statSync(path.join(d,'bin/run')).mode&0o100);
 });
 if(!online)skip('online official sources','network unreachable (HEAD https://nodejs.org/dist/ failed)');
 else{
  await test('online official sources: bootstrap.mjs acquires pinned Python from python-build-standalone',async()=>{
   let F=root('online'),j=ok(await run(['acquire','python','--root',F,'--quiet'])),x=j.results[0];assert.equal(x.source,'online');assert.equal(marker(x.path).source.url,art('python').url);ok(await run(['verify','python','--root',F,'--quiet']));facts.timings.online_python_cold_ms=x.ms;facts.timings.online_python_fetch_ms=x.fetchMs;
  });
  await test('online official sources: Node-absent launcher fetches pinned Node from nodejs.org with curl',async()=>{
   let dep=deploy('launch-online',nodeStep),bin=maskedBin('curl',['curl']),r=await run([path.join(dep,'bootstrap/plot.sh'),'run'],{cmd:'/bin/sh',pre:[],env:{PATH:bin,HOME:tmp},clean:true});assert.equal(r.code,0,r.err);
   let m=marker(path.join(hostDir(dep),ls(hostDir(dep)).find(n=>n.startsWith('node-'))));assert.equal(m.source.url,art('node').url);assert.ok(JSON.parse(r.out.trim().split('\n').at(-1)).execPath.startsWith(hostDir(dep)));facts.timings.launcher_online_cold_ms=r.ms;
  });
 }
}finally{
 server.close();
 let passed=checks.filter(c=>c.passed).length;
 console.log(JSON.stringify({host:{platform:process.platform,arch:process.arch,node:process.version,tmp:os.tmpdir()},kit:kitReady?kitDir:null,online,notRun,facts},null,1));
 console.log(`${passed}/${checks.length} bootstrap checks`+(notRun.length?` (${notRun.length} NOT RUN)`:''));
 fs.rmSync(tmp,{recursive:true,force:true});if(passed!==checks.length)process.exitCode=1;
}
