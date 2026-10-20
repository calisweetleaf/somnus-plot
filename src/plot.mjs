// Somnus Plot v0.6: owned acquisitions, transactional views, literal native steps.
// Native execution is trusted code. Manifest fs fields do not confine children.
import * as f from 'node:fs';
import * as p from 'node:path';
import {spawnSync,spawn} from 'node:child_process';
import {fileURLToPath as u} from 'node:url';
import {createGunzip} from 'node:zlib';
import {createHash} from 'node:crypto';
const exists=f.existsSync,mkdir=f.mkdirSync,join=p.join;
const fail=s=>{throw Error(s)},read=x=>JSON.parse(f.readFileSync(x,'utf8'));
const stable=x=>JSON.stringify(x,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
const id=x=>typeof x==='string'&&/^[a-zA-Z0-9_-]{1,64}$/.test(x)?x:fail('invalid name');
const inside=(r,x)=>{let q=p.relative(r,x);return q.split(p.sep)[0]!=='..'&&!p.isAbsolute(q)};
function atom(x,v){let t=x+'.'+process.pid;let d=f.openSync(t,'wx',0o600);try{f.writeFileSync(d,JSON.stringify(v));f.fsyncSync(d);f.closeSync(d);d=null;f.renameSync(t,x)}finally{if(d!==null)f.closeSync(d);f.rmSync(t,{force:true})}}
function exec(cmd,args=[],options={}){let r=spawnSync(cmd,args,{encoding:'utf8',...options});if(r.error||r.status!==0)fail('exec '+cmd+': '+(r.error?.message||r.stderr||r.status));return r.stdout.trim()}
const info='import sys,sysconfig,json;print(json.dumps([sys.executable,sys.version,sysconfig.get_config_var("SOABI"),sys.platform]))';
function probe(bin,args=[]){return JSON.parse(exec(bin,[...args,'-I','-c',info]))}
const sig=()=>[process.platform,process.arch];
// Stream gzip; collect a bounded TAR, validate before writing any link.
async function untar(src,dest,limit=268435456){
 let chunks=[],length=0,g=f.createReadStream(src).pipe(createGunzip());
 for await(let b of g){length+=b.length;if(length>limit){g.destroy();fail('archive limit')}chunks.push(b)}
 let b=Buffer.concat(chunks),entries=[],names=new Set(),off=0;
 const str=(h,a,n)=>h.subarray(a,a+n).toString().split('\0')[0];
 const oct=s=>{if(!/^[\s\0]*[0-7]*[\s\0]*$/.test(s))fail('tar number');return parseInt(s.trim(),8)||0};
 const path=x=>{if(!x||/[\\:]/.test(x)||p.posix.isAbsolute(x)||x.split('/').includes('..'))fail('tar path');return p.posix.normalize(x).replace(/\/$/,'')};
 while(off+512<=b.length){let h=b.subarray(off,off+512);if(h.every(v=>v===0))break;
  let sum=0;for(let i=0;i<512;i++)sum+=i>=148&&i<156?32:h[i];if(sum!==oct(str(h,148,8)))fail('tar checksum');
  let n=oct(str(h,124,12)),a=off+512,next=a+Math.ceil(n/512)*512,t=String.fromCharCode(h[156]);if(next>b.length)fail('truncated tar');
  {let name=path([str(h,345,155),str(h,0,100)].filter(Boolean).join('/'));
   if(name!=='.'){if(names.has(name))fail('tar duplicate');names.add(name);if(!['0','\0','2','5'].includes(t))fail('tar type');entries.push({name:name,t,n,a,mode:oct(str(h,100,8))&0o777,target:str(h,157,100)})}}
  off=next;if(entries.length>100000)fail('tar limit');
 }
 if(off+512>b.length)fail('incomplete tar');
 let links=new Set(entries.filter(e=>e.t==='2').map(e=>e.name));
 for(let e of entries){for(let a=p.posix.dirname(e.name);a!=='.';a=p.posix.dirname(a))if(links.has(a))fail('tar link ancestor');
  if(e.t==='2')path(e.target);
 }
 for(let e of entries.filter(e=>e.t==='5'||e.t==='0'||e.t==='\0')){let x=join(dest,e.name);mkdir(p.dirname(x),{recursive:true});if(e.t==='5')mkdir(x,{recursive:true});else f.writeFileSync(x,b.subarray(e.a,e.a+e.n),{flag:'wx',mode:e.mode})}
 for(let e of entries.filter(e=>e.t==='2')){let x=join(dest,e.name);mkdir(p.dirname(x),{recursive:true});f.symlinkSync(e.target,x)}
}
// Python's isolated startup excludes user/host site-packages. The view supplies
// exactly one resolved package layer; scripts, modules and console entrypoints work.
const runner='import sys,os,runpy;d,pk,s=sys.argv[1:4];sys.path[:0]=[d]+([pk] if pk else []);os.environ.update(PLOT_STATE=s,PYTHONPATH=pk,PYTHONNOUSERSITE="1");a=sys.argv[4:];sys.argv=a[1:] if a[0] in ["-m","--entry"] else (["-c"]+a[2:] if a[0]=="-c" else a);exec(a[1]) if a[0]=="-c" else (runpy.run_module(a[1],run_name="__main__",alter_sys=True) if a[0]=="-m" else (sys.exit(next(e for e in __import__("importlib.metadata").metadata.entry_points(group="console_scripts") if e.name==a[1]).load()()) if a[0]=="--entry" else runpy.run_path(a[0],run_name="__main__")))';
export function openPlot(root){
 root=f.realpathSync(root);let grave=join(root,'.grave'),envs=join(grave,'envs'),objects=join(grave,'objects'),ledger=join(root,'data.json');
 const manifest=spec=>{let m=read(join(root,'manifest.json'));if(spec?.python)m={...m,tenants:{...m.tenants,python:{...m.tenants?.python,...spec.python}}};if(m.hosts&&!m.hosts.includes('node'))fail('host unsupported');return m};
 function allowed(m){if(m.execution!=='trusted'||m.permissions?.spawn!==true)fail('requires trusted, spawn: true')}
 function definitions(m){let d={...m.capabilities},py=m.tenants?.python;if(py){if(d.python||d['python-packages'])fail('reserved capability');d.python={python:{...py,packages:undefined,pip:undefined}};d['python-packages']={needs:['python'],packages:py.packages||[],pip:py.pip||[]}}return d}
 function plan(m,requested){let d=definitions(m),done=new Set(),active=new Set(),order=[];
  function visit(k){id(k);if(done.has(k))return;if(active.has(k))fail('cycle');let c=d[k];if(!c)fail('missing capability '+k);if(c.on)c={...c,...(c.on[sig().join('/')]||c.on[process.platform]||c.on['*']||fail('host recipe')),on:undefined};active.add(k);for(let dep of c.needs||[])visit(dep);active.delete(k);done.add(k);order.push([k,c])}
  for(let k of requested)visit(k);return order;
 }
 const wanted=(m,s)=>s?.use||m.environment?.use||(m.tenants?.python?['python-packages']:Object.keys(m.capabilities||{}));
 const state=()=>exists(ledger)?read(ledger):{};
 function valid(v,key){try{return v?.key===key&&inside(objects,f.realpathSync(v.path))&&stable(read(join(v.path,'.plot.json')))===stable(v)&&(!v.python||exists(v.python))}catch{return false}}
 function expand(s,stage,assets){return String(s).replace(/\$\{(root|stage|cap:[a-zA-Z0-9_-]+)\}/g,(_,k)=>k==='root'?root:k==='stage'?stage:assets[k.slice(4)]?.path||fail('missing expansion '+k))}
 async function acquire(c,stage,assets){
  if(c.python){let py=c.python,bin;
   if((py.depth||'shallow')==='deep'){if(!py.url)fail('runtime URL required');let tar=join(stage,'.dig.tgz');
    if(/^https:/.test(py.url)){let r=await fetch(py.url,{signal:AbortSignal.timeout(120000)});if(!r.ok||!r.body)fail('download error');let fd=f.openSync(tar,'wx'),n=0;try{for await(let b of r.body){n+=b.length;if(n>268435456)fail('download limit');f.writeSync(fd,b)}}finally{f.closeSync(fd)}}
    else f.copyFileSync(py.url.startsWith('file:')?u(py.url):p.resolve(root,py.url),tar);
    if(py.sha256&&createHash('sha256').update(f.readFileSync(tar)).digest('hex')!==py.sha256.toLowerCase())fail('sha256 mismatch');
    await untar(tar,stage);f.rmSync(tar);if(exists(join(stage,'python'))){for(let k of f.readdirSync(join(stage,'python')))f.renameSync(join(stage,'python',k),join(stage,k));f.rmdirSync(join(stage,'python'))}
   }else if(py.depth&&py.depth!=='shallow')fail('invalid depth');
   else{let host;for(let [cmd,args] of py.command?[[py.command,[]]]:[['python3',[]],['python',[]],['py',['-3']]]){try{probe(cmd,args);host=[cmd,args];break}catch{}}if(!host)fail('no Python');exec(host[0],[...host[1],'-m','venv',stage])}
   bin=join(stage,process.platform==='win32'?'Scripts/python.exe':'bin/python3');let identity=probe(bin);if(py.version&&!identity[1].startsWith(py.version))fail('Python version mismatch');return {python:bin,identity:identity};
  }
  if(c.packages){let bin=assets.python.python;if(c.packages.length)exec(bin,['-I','-m','pip','--isolated','install','--target',stage,...c.pip,...c.packages]);return {}}
  if(!c.install?.length)fail('no install');
  for(let s of [...c.install,...(c.check||[])])exec(expand(s.cmd,stage,assets),(s.args||[]).map(x=>expand(x,stage,assets)),{cwd:stage,env:{...process.env,...s.env}});
  return {};
 }
 async function provision(name='default',spec){
  id(name);let m=manifest(spec),order=plan(m,wanted(m,spec));allowed(m);
  mkdir(envs,{recursive:true});mkdir(objects,{recursive:true});let lock=join(grave,'.lock');try{if(exists(join(grave,'.recovery')))fail();mkdir(lock)}catch{fail('busy: inspect .grave/.lock')}
  let stages=[];const stamp=()=>atom(join(lock,'owner.json'),{pid:process.pid,stages:stages});stamp();try{let old=state(),assets={},changes=false;
   for(let [k,c] of order){let key=stable([c,sig(),(c.needs||[]).map(n=>assets[n].path)]),v=old.assets?.[k];
    if(!valid(v,key)){changes=true;let stage=f.mkdtempSync(join(objects,k+'-'));stages.push(stage);stamp();v={key:key,path:stage,...await acquire(c,stage,assets)};atom(join(stage,'.plot.json'),v)}assets[k]=v;
   }
   let view={schema:1,host:sig(),assets:assets,python:assets.python?.python,packages:assets['python-packages']?.path,state:join(grave,'work',name)};
   mkdir(view.state,{recursive:true});if(changes)atom(ledger,{...old,assets:{...old.assets,...assets}});stages=[];
   atom(join(envs,name+'.json'),view);return view;
  }finally{for(let x of stages)f.rmSync(x,{recursive:true,force:true});f.rmSync(join(lock,'owner.json'),{force:true});f.rmdirSync(lock)}
 }
 function view(name){id(name);let v=read(join(envs,name+'.json'));if(stable(v.host)!==stable(sig()))fail('host changed');for(let a of Object.values(v.assets))if(!valid(a,a.key))fail('asset missing');return v}
 function resolve(name,steps){let m=manifest();allowed(m);let v=view(name);return {view:v,steps:(steps||m.steps||[]).map(s=>{let cmd=expand(s.cmd,'',v.assets),args=(s.args||[]).map(x=>expand(x,'',v.assets)),options={cwd:s.cwd?p.resolve(root,s.cwd):root,env:{...process.env,...s.env,PLOT_STATE:v.state}};
   if(cmd==='python'||cmd==='.grave/py/bin/python3'){if(!v.python||!args.length)fail('Python view/args missing');cmd=v.python;if(args[0]!=='--version')args=['-I','-S','-c',runner,options.cwd,v.packages||'',v.state,...args]}
   return {cmd:cmd,args:args,options:options};})};}
 async function run(name='default',steps){for(let s of resolve(name,steps).steps){let code=await new Promise((resolve,reject)=>{let c=spawn(s.cmd,s.args,{...s.options,stdio:'inherit'});c.on('error',reject);c.on('close',n=>resolve(n??1))});if(code)return code;}return 0;}

 return {plan:spec=>plan(manifest(spec),wanted(manifest(spec),spec)).map(([id,recipe])=>({id,recipe})),provision:provision,run:run,view:view,resolve:resolve};
}
if(process.argv[1]&&f.realpathSync(process.argv[1])===u(import.meta.url)){
 let a=process.argv.slice(2),root=p.dirname(u(import.meta.url));if(a[0]==='--root'){root=p.resolve(a[1]);a.splice(0,2)}
 try{let plot=openPlot(root),cmd=a.shift()||'run',name=a.shift()||'default';if(cmd==='run'){if(name==='default'||!exists(join(root,'.grave','envs',name+'.json')))await plot.provision(name);process.exitCode=await plot.run(name,a.length?[{cmd:a.shift(),args:a}]:undefined)}else console.log(JSON.stringify(cmd==='plan'?plot.plan():cmd==='provision'?await plot.provision(name):fail('unknown command')))}catch(e){console.error('[plot] '+e.message);process.exitCode=1}
}
