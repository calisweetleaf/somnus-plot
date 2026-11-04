import * as fs from 'node:fs';
import * as path from 'node:path';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {openPlot} from '../main.js';
import {base,python,scratch,fixture,manifest,cli,must,command,tar,wheels,defaults} from './helpers.mjs';
const tmp=scratch(),checks=[],start=new Date().toISOString();
const test=async(name,fn)=>{let t=performance.now();try{await fn();checks.push({name,passed:true,ms:performance.now()-t});console.log('PASS '+name)}catch(e){checks.push({name,passed:false,error:e.stack});console.error('FAIL '+name+'\n'+e.stack)}};
const node=process.execPath;
const capability=value=>({install:[{cmd:node,args:['-e',`require('node:fs').writeFileSync('value.txt',${JSON.stringify(value)})`]}],check:[{cmd:node,args:['-e',`if(require('node:fs').readFileSync('value.txt','utf8')!==${JSON.stringify(value)})process.exit(2)`]}]});
try{
 await test('shipped core stays at or below original 9063 bytes',()=>assert.ok(fs.statSync(path.join(base,'main.js')).size<=9063));
 await test('real mixed Node/Python demo and module import parity',async()=>{
  const root=fixture(tmp,'demo',JSON.parse(fs.readFileSync(path.join(base,'manifest.json'))));let r=must(cli(root));assert.match(r.stdout,/114/);let plot=openPlot(root),a=plot.view('default');assert.equal(JSON.parse(fs.readFileSync(path.join(a.state,'result.json'))).average,28.5);
  const {openPlot:source}=await import('../src/plot.mjs');assert.deepEqual(source(root).plan(),plot.plan());assert.deepEqual(source(root).view('default'),plot.view('default'));
 });
 await test('default CLI is plot-relative when launched elsewhere',()=>{let root=fixture(tmp,'relative',{capabilities:{a:capability('native')},steps:[{cmd:node,args:['-e',`require('node:fs').writeFileSync('ran.txt',process.cwd())`]}]});must(cli(root,[],{cwd:'/tmp'}));assert.equal(fs.readFileSync(path.join(root,'ran.txt'),'utf8'),root)});
 await test('literal arguments, step cwd/env, and stop on child exit',()=>{let root=fixture(tmp,'steps',{steps:[{cmd:node,args:['-e','require("node:fs").writeFileSync("args.json",JSON.stringify([process.argv[1],process.env.MARK,process.cwd()]))','$(touch nope)'],env:{MARK:'right'},cwd:'.'},{cmd:node,args:['-e','process.exit(7)']},{cmd:node,args:['-e','require("node:fs").writeFileSync("BAD","")']}]});let r=cli(root);assert.equal(r.status,7);assert.deepEqual(JSON.parse(fs.readFileSync(path.join(root,'args.json'))),['$(touch nope)','right',root]);assert.ok(!fs.existsSync(path.join(root,'BAD')))});
 await test('spawn:false and missing trusted declaration fail before acquisition',()=>{for(let [name,over] of [['spawn',{permissions:{spawn:false}}],['trust',{execution:undefined}]]){let root=fixture(tmp,name,{...over,capabilities:{a:capability('bad')}});assert.notEqual(cli(root).status,0);assert.ok(!fs.existsSync(path.join(root,'.grave')))}});
 await test('host mismatch, invalid IDs, missing dependencies, cycles fail closed',async()=>{for(let [name,m] of [['host',{hosts:['webview']}],['missing',{capabilities:{a:{needs:['absent']}}}],['cycle',{capabilities:{a:{needs:['b']},b:{needs:['a']}}}]]){let root=fixture(tmp,name,m);assert.notEqual(cli(root).status,0);assert.ok(!fs.existsSync(path.join(root,'.grave')))}let root=fixture(tmp,'ids');await assert.rejects(openPlot(root).provision('../escape'),/invalid name/)});
 await test('host recipe precedence, wildcard fallback and optional unsupported DLC',async()=>{let root=fixture(tmp,'variants',{capabilities:{a:{on:{[process.platform+'/'+process.arch]:capability('exact'),[process.platform]:capability('platform'),'*':capability('fallback')}},b:{on:{'*':capability('wildcard')}},unused:{on:{imaginary:capability('never')}}},environment:{use:['a','b']}}),plot=openPlot(root),v=await plot.provision();assert.equal(fs.readFileSync(path.join(v.assets.a.path,'value.txt'),'utf8'),'exact');assert.equal(fs.readFileSync(path.join(v.assets.b.path,'value.txt'),'utf8'),'wildcard');await assert.rejects(plot.provision('bad',{use:['unused']}),/host recipe/)});
 await test('DAG order, reuse, dependency invalidation and frozen older views',async()=>{
  let root=fixture(tmp,'dag',{capabilities:{a:capability('v1'),b:{needs:['a'],install:[{cmd:node,args:['-e','require("node:fs").copyFileSync(process.argv[1],"copy.txt")','${cap:a}/value.txt']}]},unselected:{install:[{cmd:node,args:['-e','process.exit(9)']}]}},environment:{use:['b']}}),plot=openPlot(root);
  assert.deepEqual(plot.plan().map(x=>x.id),['a','b']);let a=await plot.provision('first'),b=await plot.provision('second');assert.deepEqual(a.assets,b.assets);let ledger=fs.statSync(path.join(root,'data.json')).mtimeMs;
  await plot.provision('third');assert.equal(fs.statSync(path.join(root,'data.json')).mtimeMs,ledger);
  manifest(root,{capabilities:{a:capability('v2'),b:{needs:['a'],install:[{cmd:node,args:['-e','require("node:fs").copyFileSync(process.argv[1],"copy.txt")','${cap:a}/value.txt']}]}},environment:{use:['b']}});
  let c=await plot.provision('fourth');assert.notEqual(c.assets.a.path,a.assets.a.path);assert.notEqual(c.assets.b.path,a.assets.b.path);assert.equal(fs.readFileSync(path.join(plot.view('first').assets.b.path,'copy.txt'),'utf8'),'v1');assert.equal(fs.readFileSync(path.join(c.assets.b.path,'copy.txt'),'utf8'),'v2');
 });
 await test('failed installer/check preserve active view, ledger, writable data',async()=>{
  let root=fixture(tmp,'rollback',{capabilities:{a:capability('stable')}}),plot=openPlot(root),v=await plot.provision('active');fs.writeFileSync(path.join(v.state,'keep.txt'),'persistent');let ledger=fs.readFileSync(path.join(root,'data.json')),view=fs.readFileSync(path.join(root,'.grave/envs/active.json')),objects=fs.readdirSync(path.join(root,'.grave/objects'));
  for(let where of ['install','check']){let bad=capability('changed');bad[where]=[{cmd:node,args:['-e','process.exit(19)']}];manifest(root,{capabilities:{a:bad}});await assert.rejects(plot.provision('active'));assert.deepEqual(fs.readFileSync(path.join(root,'data.json')),ledger);assert.deepEqual(fs.readFileSync(path.join(root,'.grave/envs/active.json')),view);assert.deepEqual(fs.readdirSync(path.join(root,'.grave/objects')),objects);assert.equal(fs.readFileSync(path.join(v.state,'keep.txt'),'utf8'),'persistent')}
 });
 await test('cross-process acquisition lock rejects racing writer',async()=>{
  let root=fixture(tmp,'race',{capabilities:{a:{install:[{cmd:node,args:['-e',`require('node:fs').writeFileSync(${JSON.stringify(path.join(tmp,'started'))},'1');setTimeout(()=>{},800)`]}]}}});let child=spawn(node,[path.join(base,'main.js'),'--root',root,'provision'],{stdio:'ignore'});let exit=new Promise((resolve,reject)=>{child.on('exit',resolve);child.on('error',reject)});let deadline=Date.now()+5000;while(!fs.existsSync(path.join(tmp,'started'))&&Date.now()<deadline)await new Promise(r=>setTimeout(r,10));assert.ok(fs.existsSync(path.join(tmp,'started')));let other=cli(root,['provision','racer']);assert.notEqual(other.status,0);assert.match(other.stderr,/busy/);assert.equal(await exit,0);assert.ok(!fs.existsSync(path.join(root,'.grave/.lock')));
 });
 await test('missing asset and cross-device view require reprovision',async()=>{let root=fixture(tmp,'missing-asset',{capabilities:{a:capability('a')}}),plot=openPlot(root),v=await plot.provision();fs.rmSync(path.join(v.assets.a.path,'.plot.json'));assert.throws(()=>plot.view('default'),/asset missing/);let next=await plot.provision();assert.notEqual(next.assets.a.path,v.assets.a.path);let file=path.join(root,'.grave/envs/default.json');let broken=JSON.parse(fs.readFileSync(file));broken.host=['different','host'];fs.writeFileSync(file,JSON.stringify(broken));assert.throws(()=>plot.view('default'),/host changed/)});
 await test('historical exact-key reuse: v1->v2->v1 capability switch spawns nothing',async()=>{
  let counter=path.join(tmp,'history-spawns.txt'),cap=(value,deps)=>({needs:deps,install:[{cmd:node,args:['-e',`const fs=require('node:fs');fs.appendFileSync(${JSON.stringify(counter)},'x');fs.writeFileSync('value.txt',${JSON.stringify(value)})`]}]}),spec=v=>({capabilities:{a:cap(v),b:cap(v,['a'])},environment:{use:['b']}});
  let root=fixture(tmp,'history',spec('v1')),plot=openPlot(root),one=await plot.provision('one');manifest(root,spec('v2'));let two=await plot.provision('two');assert.equal(fs.readFileSync(counter,'utf8'),'xxxx');assert.notEqual(two.assets.a.path,one.assets.a.path);
  let objects=fs.readdirSync(path.join(root,'.grave/objects')).sort();manifest(root,spec('v1'));let again=await plot.provision('again');
  assert.equal(fs.readFileSync(counter,'utf8'),'xxxx');assert.deepEqual(fs.readdirSync(path.join(root,'.grave/objects')).sort(),objects);assert.deepEqual(again.assets,one.assets);
  assert.deepEqual(JSON.parse(fs.readFileSync(path.join(root,'data.json'))).assets,one.assets);assert.equal(fs.readFileSync(path.join(plot.view('again').assets.b.path,'value.txt'),'utf8'),'v1');assert.deepEqual(plot.view('two').assets,two.assets);
 });
 await test('unstamped, interrupted or forged stages are never adopted',async()=>{
  let counter=path.join(tmp,'unstamped-spawns.txt'),cap=value=>({capabilities:{a:{install:[{cmd:node,args:['-e',`require('node:fs').appendFileSync(${JSON.stringify(counter)},'x');require('node:fs').writeFileSync('value.txt',${JSON.stringify(value)})`]}]}}});
  let root=fixture(tmp,'unstamped',cap('v1')),plot=openPlot(root),one=await plot.provision('one'),stamp=path.join(one.assets.a.path,'.plot.json'),record=fs.readFileSync(stamp);manifest(root,cap('v2'));await plot.provision('two');
  fs.renameSync(stamp,stamp+'.'+process.pid);let forged=path.join(root,'.grave/objects/a-forged');fs.mkdirSync(forged);fs.writeFileSync(path.join(forged,'.plot.json'),record);
  manifest(root,cap('v1'));let again=await plot.provision('again');assert.equal(fs.readFileSync(counter,'utf8'),'xxx');assert.notEqual(again.assets.a.path,one.assets.a.path);assert.notEqual(again.assets.a.path,forged);assert.equal(fs.readFileSync(path.join(again.assets.a.path,'value.txt'),'utf8'),'v1');
 });
 await test('stdout-only child diagnostic reaches the failure message',async()=>{let root=fixture(tmp,'stdout-diagnostic',{capabilities:{a:{install:[{cmd:node,args:['-e',`process.stdout.write('diagnostic only on stdout');process.exit(4)`]}]}}});await assert.rejects(openPlot(root).provision(),/diagnostic only on stdout/);assert.ok(!fs.existsSync(path.join(root,'data.json')))});
 await test('foreground pin names transitive objects during a run and is removed after',async()=>{
  let probe=`const fs=require('node:fs'),p=require('node:path'),d=p.join(process.argv[1],'.grave','pins');fs.writeFileSync(p.join(process.argv[1],'seen.json'),JSON.stringify(fs.readdirSync(d).map(x=>[x,fs.statSync(p.join(d,x)).mode&0o777,JSON.parse(fs.readFileSync(p.join(d,x),'utf8'))])))`;
  let root=fixture(tmp,'pins',{capabilities:{a:capability('pinned'),b:{needs:['a'],install:[{cmd:node,args:['-e','0']}]}},environment:{use:['b']},steps:[{cmd:node,args:['-e',probe,'${root}']}]});must(cli(root));
  let view=openPlot(root).view('default'),seen=JSON.parse(fs.readFileSync(path.join(root,'seen.json')));assert.equal(seen.length,1);let [name,mode,pin]=seen[0];
  assert.match(name,/^foreground-[0-9]+-[a-z0-9]+\.json$/);assert.equal(mode,0o600);assert.equal(pin.schema,1);assert.equal(pin.kind,'foreground');assert.equal(pin.ref,'fg');assert.equal(typeof pin.owner.pid,'number');assert.equal(pin.owner.birth,null);assert.ok(!Number.isNaN(Date.parse(pin.created)));
  assert.deepEqual(pin.paths.sort(),[view.assets.a.path,view.assets.b.path].sort());assert.deepEqual(fs.readdirSync(path.join(root,'.grave/pins')),[]);
  let plot=openPlot(root);assert.equal(await plot.run('default',[{cmd:node,args:['-e',probe,root]},{cmd:node,args:['-e','process.exit(3)']}]),3);assert.equal(JSON.parse(fs.readFileSync(path.join(root,'seen.json'))).length,1);assert.deepEqual(fs.readdirSync(path.join(root,'.grave/pins')),[]);
  await assert.rejects(plot.run('default',[{cmd:path.join(tmp,'absent-binary'),args:[]}]));assert.deepEqual(fs.readdirSync(path.join(root,'.grave/pins')),[]);
  let tombs=path.join(root,'.grave/tombstones'),intent=path.join(tombs,path.basename(view.assets.a.path)+'.json');fs.mkdirSync(tombs,{recursive:true});fs.writeFileSync(intent,JSON.stringify({path:view.assets.a.path,reason:'test',at:new Date().toISOString()}));fs.rmSync(path.join(root,'seen.json'));
  await assert.rejects(plot.run('default',[{cmd:node,args:['-e',probe,root]}]),/tombstoned/);assert.ok(!fs.existsSync(path.join(root,'seen.json')),'no step spawned against a tombstoned object');assert.deepEqual(fs.readdirSync(path.join(root,'.grave/pins')),[]);fs.rmSync(intent);
  fs.rmSync(path.join(view.assets.a.path,'.plot.json'));await assert.rejects(plot.run('default'),/asset missing/);assert.deepEqual(fs.readdirSync(path.join(root,'.grave/pins')),[]);
 });
 let wheelDir=path.join(tmp,'wheels');fs.mkdirSync(wheelDir);let dist=wheels(wheelDir),pkgRoot=fixture(tmp,'packages',{tenants:{python:{depth:'shallow',command:python,packages:[dist.one,dist.native],pip:['--no-index']}},steps:[]}),plot=openPlot(pkgRoot),one,two;
 await test('real pip target acquisition, shared interpreter and version conflicts',async()=>{
  one=await plot.provision('one');two=await plot.provision('two',{python:{packages:[dist.two,dist.native]}});assert.equal(one.python,two.python);assert.notEqual(one.packages,two.packages);assert.ok(!fs.existsSync(path.join(one.state,'pyvenv.cfg')));assert.ok(!fs.existsSync(path.join(two.packages,'pyvenv.cfg')));
  for(let [name,want] of [['one','1.0'],['two','2.0']])assert.equal(await plot.run(name,[{cmd:'python',args:['-c',`import plot_sample,plot_native,importlib.metadata as m;assert plot_sample.VERSION==${JSON.stringify(want)};assert m.version('plot-sample')==${JSON.stringify(want)};assert plot_native.value()==37`]}]),0);
 });
 await test('Python module, script, argv, metadata resources and console entrypoint',async()=>{
  let code=`import sys,plot_sample,importlib.resources as r;assert sys.argv==['-c','literal'];assert r.files('plot_sample').joinpath('payload.txt').read_text()=='actual package resource'`;
  assert.equal(await plot.run('one',[{cmd:'python',args:['-c',code,'literal']},{cmd:'python',args:['-m','plot_sample']},{cmd:'python',args:['--entry','plot-sample']}]),0);
  fs.writeFileSync(path.join(pkgRoot,'script.py'),`import plot_sample,sys\nassert plot_sample.VERSION=='2.0'\nassert sys.argv==['script.py','okay']\n`);assert.equal(await plot.run('two',[{cmd:'.grave/py/bin/python3',args:['script.py','okay']}]),0);
 });
 await test('subprocess package inheritance, host PYTHONPATH exclusion and writable isolation',async()=>{
  let poison=path.join(tmp,'poison');fs.mkdirSync(poison);fs.writeFileSync(path.join(poison,'plot_sample.py'),'raise RuntimeError("host leak")');
  for(let [name,want] of [['one','1.0'],['two','2.0']])assert.equal(await plot.run(name,[{cmd:'python',env:{PYTHONPATH:poison},args:['-c',`import subprocess,sys,os,pathlib,plot_sample;assert plot_sample.VERSION==${JSON.stringify(want)};out=subprocess.check_output([sys.executable,'-c','import plot_sample;print(plot_sample.VERSION)'],text=True).strip();assert out==${JSON.stringify(want)};pathlib.Path(os.environ['PLOT_STATE'],'own.txt').write_text(${JSON.stringify(want)})`]}]),0);
  assert.equal(fs.readFileSync(path.join(one.state,'own.txt'),'utf8'),'1.0');assert.equal(fs.readFileSync(path.join(two.state,'own.txt'),'utf8'),'2.0');assert.equal(await plot.run('one',[{cmd:'python',args:['-c','import importlib.util;assert importlib.util.find_spec("pip") is None']}]),0);
 });
 await test('package installation failure and requested depth/version drift fail without stale reuse',async()=>{
  let before=fs.readFileSync(path.join(pkgRoot,'.grave/envs/one.json'));await assert.rejects(plot.provision('one',{python:{packages:['not-present==1'],pip:['--no-index']}}));assert.deepEqual(fs.readFileSync(path.join(pkgRoot,'.grave/envs/one.json')),before);
  await assert.rejects(plot.provision('one',{python:{depth:'deep',url:'missing.tar.gz'}}));assert.deepEqual(fs.readFileSync(path.join(pkgRoot,'.grave/envs/one.json')),before);
  await assert.rejects(plot.provision('one',{python:{version:'99.0'}}),/version mismatch/);assert.deepEqual(fs.readFileSync(path.join(pkgRoot,'.grave/envs/one.json')),before);
 });
 await test('historical exact-key reuse: Python package switch v1->v2->v1 runs no pip',async()=>{
  assert.equal(JSON.parse(fs.readFileSync(path.join(pkgRoot,'data.json'))).assets['python-packages'].path,two.packages);let hidden=dist.one+'.hidden';fs.renameSync(dist.one,hidden);
  try{let again=await plot.provision('again',{python:{packages:[dist.one,dist.native]}});assert.equal(again.packages,one.packages);assert.equal(again.python,one.python);assert.equal(JSON.parse(fs.readFileSync(path.join(pkgRoot,'data.json'))).assets['python-packages'].path,one.packages);
   assert.equal(await plot.run('again',[{cmd:'python',args:['-c','import plot_sample,plot_native;assert plot_sample.VERSION=="1.0";assert plot_native.value()==37']}]),0)}finally{fs.renameSync(hidden,dist.one)}
 });
 await test('package-less shallow venv provisions without ensurepip; pip-bearing tenant reports stdout diagnostic',async()=>{
  let wrapper=path.join(tmp,'python-without-ensurepip'),calls=path.join(tmp,'venv-calls.txt');
  fs.writeFileSync(wrapper,`#!/bin/sh\ncase " $* " in *" -m venv "*) echo "$*" >> '${calls}'; case " $* " in *" --without-pip "*) ;; *) echo "Error: ensurepip is not available on this host"; exit 1;; esac;; esac\nexec '${python}' "$@"\n`,{mode:0o755});
  let root=fixture(tmp,'no-ensurepip',{tenants:{python:{depth:'shallow',command:wrapper,packages:[]}},steps:[{cmd:'python',args:['-c','import sys;print("bare", sys.version_info[0])']}]}),r=must(cli(root));assert.match(r.stdout,/bare 3/);
  assert.match(fs.readFileSync(calls,'utf8'),/--without-pip/);let v=openPlot(root).view('default');assert.equal(v.assets.python.key.includes('"pip":false'),true);
  assert.equal(command(v.python,['-c','import importlib.util;print(importlib.util.find_spec("pip") is None)']),'True');
  let need=fixture(tmp,'needs-pip',{tenants:{python:{depth:'shallow',command:wrapper,packages:[dist.one],pip:['--no-index']}}});await assert.rejects(openPlot(need).provision(),/ensurepip is not available/);assert.ok(!fs.existsSync(path.join(need,'data.json')));
 });
 await test('archive traversal, symlink pivots, hardlinks, PAX, duplicate paths, truncation rejected',async()=>{
  const cases=[
   [{name:'../escape.txt',data:'bad'}],
   [{name:'/absolute',data:'bad'}],
   [{name:'C:/escape',data:'bad'}],
   [{name:'a',type:'2',target:'.'},{name:'a/up',type:'2',target:'..'},{name:'a/up/sentinel.txt',data:'bad'}],
   [{name:'a',type:'2',target:'.'},{name:'b',type:'2',target:'a/..'}],
   [{name:'hard',type:'1',target:'regular'},{name:'regular',data:'x'}],
   [{name:'metadata',type:'x',data:'25 path=../escape.txt\n'}],
   [{name:'same',data:'a'},{name:'same',data:'b'}],
   [{name:'bad',type:'6'}]
  ];
  for(let i=0;i<cases.length;i++){let archive=path.join(tmp,`bad-${i}.tgz`);fs.writeFileSync(archive,tar(cases[i]));let root=fixture(tmp,`tar-${i}`,{tenants:{python:{depth:'deep',url:archive}}});await assert.rejects(openPlot(root).provision());assert.ok(!fs.existsSync(path.join(root,'data.json')));assert.ok(!fs.existsSync(path.join(root,'.grave/sentinel.txt')));assert.equal(fs.readdirSync(path.join(root,'.grave/objects')).length,0)}
  let archive=path.join(tmp,'truncated.tgz');fs.writeFileSync(archive,tar([{name:'file',data:'abc'}]).subarray(0,20));let root=fixture(tmp,'truncated',{tenants:{python:{depth:'deep',url:archive}}});await assert.rejects(openPlot(root).provision());
 });
 await test('bounded decompression aborts oversized archive without activation',async()=>{
  // Highly compressible input exercises decompression accounting, not host downloads.
  let archive=path.join(tmp,'too-large.tgz');fs.writeFileSync(archive,tar([{name:'bomb',data:Buffer.alloc(268435457)}]));let root=fixture(tmp,'oversized',{tenants:{python:{depth:'deep',url:archive}}});await assert.rejects(openPlot(root).provision(),/archive limit/);assert.ok(!fs.existsSync(path.join(root,'data.json')));
 });
 await test('real locally reconstructed CPython archive and legacy integrity check',async()=>{
  let archive=path.join(tmp,'real-python.tgz');
  // Real ELF interpreter + real standard library. Dynamic OS libraries remain host
  // dependencies: this is not evidence for a downloaded standalone distribution.
  command(python,['-c',`import sys,sysconfig,pathlib,tarfile,os
with tarfile.open(sys.argv[1],'w:gz',format=tarfile.USTAR_FORMAT,dereference=True) as t:
 t.add(sys.executable,arcname='python/bin/python3')
 lib=pathlib.Path(sysconfig.get_path('stdlib'))
 for root,dirs,files in os.walk(lib):
  dirs[:]=[d for d in dirs if d not in ('site-packages','__pycache__','test','tests','idlelib','tkinter','ensurepip')]
  for f in files:
   src=pathlib.Path(root)/f
   if not src.is_symlink():t.add(src,arcname='python/lib/python'+str(sys.version_info.major)+'.'+str(sys.version_info.minor)+'/'+str(src.relative_to(lib)),recursive=False)
`,archive]);
  let pin=createHash('sha256').update(fs.readFileSync(archive)).digest('hex'),root=fixture(tmp,'deep-real',{tenants:{python:{depth:'deep',url:archive,sha256:pin}},steps:[{cmd:'python',args:['-c','import sys,json,math;assert math.sqrt(81)==9;print(sys.version)']}]});must(cli(root));let old=fs.readFileSync(path.join(root,'.grave/envs/default.json'));manifest(root,{tenants:{python:{depth:'deep',url:archive,sha256:'0'.repeat(64)}}});await assert.rejects(openPlot(root).provision(),/sha256 mismatch/);assert.deepEqual(fs.readFileSync(path.join(root,'.grave/envs/default.json')),old);
 });
}finally{
 let report={started_at:start,finished_at:new Date().toISOString(),node:process.version,platform:process.platform,arch:process.arch,python:command(python,['--version']),core_bytes:fs.statSync(path.join(base,'main.js')).size,total:checks.length,passed:checks.filter(x=>x.passed).length,checks};fs.mkdirSync(path.join(base,'evidence'),{recursive:true});fs.writeFileSync(path.join(base,'evidence/integration.json'),JSON.stringify(report,null,2));console.log(`${report.passed}/${report.total} integration checks`);fs.rmSync(tmp,{recursive:true,force:true});if(report.passed!==report.total)process.exitCode=1;
}
