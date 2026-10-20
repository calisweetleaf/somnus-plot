// Somnus Plot v0.6: owned acquisitions, transactional views, literal native steps.
// Native execution is trusted code. Manifest fs fields do not confine children.
import * as f from 'node:fs';
import * as p from 'node:path';
import {spawnSync as runSync,spawn} from 'node:child_process';
import {fileURLToPath as u} from 'node:url';
import {createGunzip as gunzip} from 'node:zlib';
import {createHash as digest} from 'node:crypto';
const exists=f.existsSync,join=p.join,real=f.realpathSync,proc=process,mkdir=x=>f.mkdirSync(x,{recursive:true}),rm=x=>f.rmSync(x,{recursive:true,force:true});
const pkgcap='python-packages',dflt='default';
const fail=s=>{throw Error(s)},read=x=>JSON.parse(f.readFileSync(x));
const stable=x=>JSON.stringify(x,(_,v)=>v&&typeof v=='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
const id=x=>typeof x=='string'&&/^[a-zA-Z0-9_-]{1,64}$/.test(x)?x:fail('invalid name');
const inside=(r,x)=>{let q=p.relative(r,x);return q.split(p.sep)[0]!=='..'&&!p.isAbsolute(q)};
const sync=d=>{try{f.fsyncSync(d)}finally{f.closeSync(d)}};
// A create or rename is durable only after its directory is synced; Windows cannot open directories.
const syncdir=x=>proc.platform!=='win32'&&sync(f.openSync(p.dirname(x),'r'));
const create=(x,v)=>{let d=f.openSync(x,'wx',0o600);try{f.writeFileSync(d,JSON.stringify(v))}finally{sync(d)}};
const atom=(x,v)=>{let t=x+'.'+proc.pid;try{create(t,v);f.renameSync(t,x)}finally{rm(t)}syncdir(x)};
const exec=(cmd,args=[],options={})=>{let r=runSync(cmd,args,{encoding:'utf8',...options});if(r.error||r.status!==0)fail('exec '+cmd+': '+(r.error?.message||r.stderr||r.stdout||r.status));return r.stdout.trim()};
const info='import sys,sysconfig,json;print(json.dumps([sys.executable,sys.version,sysconfig.get_config_var("SOABI"),sys.platform]))';
const probe=(bin,args=[])=>JSON.parse(exec(bin,[...args,'-I','-c',info]));
const sig=()=>[proc.platform,proc.arch];
// Stream gzip; collect a bounded TAR, validate before writing any link.
const untar=async (src,dest,limit=2**28)=>{
 let chunks=[],length=0,g=f.createReadStream(src).pipe(gunzip());
 for await(let b of g){length+=b.length;if(length>limit){g.destroy();fail('archive limit')}chunks.push(b)}
 let b=Buffer.concat(chunks),entries=[],names=new Set(),off=0;
 const str=(h,a,n)=>h.subarray(a,a+n).toString().split('\0')[0];
 const oct=s=>{if(!/^[\s\0]*[0-7]*[\s\0]*$/.test(s))fail('tar number');return parseInt(s.trim(),8)||0};
 const path=x=>{if(!x||/[\\:]/.test(x)||p.posix.isAbsolute(x)||x.split('/').includes('..'))fail('tar path');return p.posix.normalize(x).replace(/\/$/,'')};
 while(off+512<=b.length){let h=b.subarray(off,off+512);if(h.every(v=>v===0))break;
  let sum=0;for(let i=0;i<512;i++)sum+=i>=148&&i<156?32:h[i];if(sum!==oct(str(h,148,8)))fail('tar checksum');
  let n=oct(str(h,124,12)),a=off+512,next=a+Math.ceil(n/512)*512,t=String.fromCharCode(h[156]);if(next>b.length)fail('truncated tar');
  {let name=path([str(h,345,155),str(h,0,100)].filter(Boolean).join('/'));
   if(name!=='.'){if(names.has(name))fail('tar duplicate');names.add(name);if(!'025\0'.includes(t))fail('tar type');entries.push({name:name,t,n,a,mode:oct(str(h,100,8))&0o777,target:str(h,157,100)})}}
  off=next;if(entries.length>100000)fail('tar limit');
 }
 if(off+512>b.length)fail('incomplete tar');
 let links=new Set(entries.filter(e=>e.t==='2').map(e=>e.name));
 for(let e of entries){for(let a=p.posix.dirname(e.name);a!=='.';a=p.posix.dirname(a))if(links.has(a))fail('tar link ancestor');
  if(e.t==='2')path(e.target);
 }
 // Stable sort: every link is created after all regular files and directories.
 for(let e of entries.sort((a,b)=>(a.t==='2')-(b.t==='2'))){let x=join(dest,e.name);mkdir(p.dirname(x));e.t==='5'?mkdir(x):e.t==='2'?f.symlinkSync(e.target,x):f.writeFileSync(x,b.subarray(e.a,e.a+e.n),{flag:'wx',mode:e.mode})}
};
// Python's isolated startup excludes user/host site-packages. The view supplies
// exactly one resolved package layer; scripts, modules and console entrypoints work.
const runner='import sys,os,runpy;d,k,s,m,*a=sys.argv[1:];sys.path[:0]=[d]+[k]*(k>"");os.environ.update(PLOT_STATE=s,PYTHONPATH=k,PYTHONNOUSERSITE="1");sys.argv=["-c",*a[1:]] if m=="-c" else a if m in("-m","--entry") else [m,*a];exec(a[0]) if m=="-c" else runpy.run_module(a[0],run_name="__main__",alter_sys=True) if m=="-m" else sys.exit(next(e for e in __import__("importlib.metadata").metadata.entry_points(group="console_scripts") if e.name==a[0]).load()()) if m=="--entry" else runpy.run_path(m,run_name="__main__")';
export function openPlot(root){
 root=real(root);let grave=join(root,'.grave'),envs=join(grave,'envs'),objects=join(grave,'objects'),ledger=join(root,'data.json');
 const manifest=spec=>{let m=read(join(root,'manifest.json'));if(spec?.python)m={...m,tenants:{...m.tenants,python:{...m.tenants?.python,...spec.python}}};if(m.hosts&&!m.hosts.includes('node'))fail('host unsupported');return m};
 const allowed=m=>{if(m.execution!=='trusted'||m.permissions?.spawn!==true)fail('requires trusted, spawn: true')};
 // A package-less tenant's runtime is created without pip; the flag is in the recipe so the two kinds never share a key.
 const definitions=m=>{let d={...m.capabilities},py=m.tenants?.python;if(py){if(d.python||d[pkgcap])fail('reserved capability');d.python={python:{...py,packages:undefined,pip:py.packages?.length?undefined:false}};d[pkgcap]={needs:['python'],packages:py.packages||[],pip:py.pip||[]}}return d};
 const plan=(m,requested)=>{let d=definitions(m),done=new Set(),active=new Set(),order=[];
  const visit=k=>{id(k);if(done.has(k))return;if(active.has(k))fail('cycle');let c=d[k];if(!c)fail('missing capability '+k);if(c.on)c={...c,...(c.on[sig().join('/')]||c.on[proc.platform]||c.on['*']||fail('host recipe')),on:undefined};active.add(k);for(let dep of c.needs||[])visit(dep);active.delete(k);done.add(k);order.push([k,c])};
  for(let k of requested)visit(k);return order;
 };
 const wanted=(m,s)=>s?.use||m.environment?.use||(m.tenants?.python?[pkgcap]:Object.keys(m.capabilities||{}));
 const state=()=>exists(ledger)?read(ledger):{};
 const valid=(v,key)=>{try{return v?.key===key&&inside(objects,real(v.path))&&stable(read(join(v.path,'.plot.json')))===stable(v)&&(!v.python||exists(v.python))}catch{return false}};
 const expand=(s,stage,assets)=>String(s).replace(/\$\{(root|stage|cap:[a-zA-Z0-9_-]+)\}/g,(_,k)=>k==='root'?root:k==='stage'?stage:assets[k.slice(4)]?.path||fail('missing expansion '+k));
 const acquire=async (c,stage,assets)=>{
  if(c.python){let py=c.python,bin;
   if((py.depth||'shallow')==='deep'){if(!py.url)fail('runtime URL required');let tar=join(stage,'.dig.tgz');
    if(/^https:/.test(py.url)){let r=await fetch(py.url,{signal:AbortSignal.timeout(120000)});if(!r.ok||!r.body)fail('download error');let fd=f.openSync(tar,'wx'),n=0;try{for await(let b of r.body){n+=b.length;if(n>2**28)fail('download limit');f.writeSync(fd,b)}}finally{f.closeSync(fd)}}
    else f.copyFileSync(py.url.startsWith('file:')?u(py.url):p.resolve(root,py.url),tar);
    if(py.sha256&&digest('sha256').update(f.readFileSync(tar)).digest('hex')!==py.sha256.toLowerCase())fail('sha256 mismatch');
    await untar(tar,stage);rm(tar);let nest=join(stage,'python');if(exists(nest)){for(let k of f.readdirSync(nest))f.renameSync(join(nest,k),join(stage,k));f.rmdirSync(nest)}
   }else if(py.depth&&py.depth!=='shallow')fail('invalid depth');
   else{let host;for(let [cmd,args] of py.command?[[py.command,[]]]:[['python3',[]],['python',[]],['py',['-3']]]){try{probe(cmd,args);host=[cmd,args];break}catch{}}if(!host)fail('no Python');exec(host[0],[...host[1],'-m','venv',stage,...py.pip===false?['--without-pip']:[]])}
   bin=join(stage,proc.platform==='win32'?'Scripts/python.exe':'bin/python3');let identity=probe(bin);if(py.version&&!identity[1].startsWith(py.version))fail('Python version mismatch');return {python:bin,identity:identity};
  }
  if(c.packages){let bin=assets.python.python;if(c.packages.length)exec(bin,['-I','-m','pip','--isolated','install','--target',stage,...c.pip,...c.packages]);return {}}
  if(!c.install?.length)fail('no install');
  for(let s of [...c.install,...(c.check||[])])exec(expand(s.cmd,stage,assets),(s.args||[]).map(x=>expand(x,stage,assets)),{cwd:stage,env:{...proc.env,...s.env}});
  return {};
 };
 const provision=async (name=dflt,spec)=>{
  id(name);let m=manifest(spec),order=plan(m,wanted(m,spec));allowed(m);
  mkdir(envs);mkdir(objects);let lock=join(grave,'.lock');try{if(exists(join(grave,'.recovery')))fail();f.mkdirSync(lock)}catch{fail('busy: inspect .grave/.lock')}
  let stages=[];const stamp=()=>atom(join(lock,'owner.json'),{pid:proc.pid,stages:stages});stamp();try{let old=state(),assets={},changes=false;
   for(let [k,c] of order){let key=stable([c,sig(),(c.needs||[]).map(n=>assets[n].path)]),v=old.assets?.[k];
    // Only a stamped .plot.json marks a complete object, so unstamped stages are never adopted.
    if(!valid(v,key)){changes=true;v=f.readdirSync(objects).map(x=>{try{return x.startsWith(k+'-')&&read(join(objects,x,'.plot.json'))}catch{}}).find(x=>valid(x,key));
     if(!v){let stage=f.mkdtempSync(join(objects,k+'-'));stages.push(stage);stamp();v={key:key,path:stage,...await acquire(c,stage,assets)};atom(join(stage,'.plot.json'),v)}}assets[k]=v;
   }
   let view={schema:1,host:sig(),assets:assets,python:assets.python?.python,packages:assets[pkgcap]?.path,state:join(grave,'work',name)};
   mkdir(view.state);if(changes)atom(ledger,{...old,assets:{...old.assets,...assets}});stages=[];
   atom(join(envs,name+'.json'),view);return view;
  }finally{for(let x of stages)rm(x);rm(join(lock,'owner.json'));f.rmdirSync(lock)}
 };
 const view=name=>{id(name);let v=read(join(envs,name+'.json'));if(stable(v.host)!==stable(sig()))fail('host changed');for(let a of Object.values(v.assets))if(!valid(a,a.key))fail('asset missing');return v};
 const resolve=(name,steps)=>{let m=manifest();allowed(m);let v=view(name);return {view:v,steps:(steps||m.steps||[]).map(s=>{let cmd=expand(s.cmd,'',v.assets),args=(s.args||[]).map(x=>expand(x,'',v.assets)),options={cwd:s.cwd?p.resolve(root,s.cwd):root,env:{...proc.env,...s.env,PLOT_STATE:v.state}};
   if(cmd==='python'||cmd==='.grave/py/bin/python3'){if(!v.python||!args.length)fail('Python view/args missing');cmd=v.python;if(args[0]!=='--version')args=['-I','-S','-c',runner,options.cwd,v.packages||'',v.state,...args]}
   return {cmd:cmd,args:args,options:options};})};};
 // Pin-then-validate: the pin precedes resolve(), whose view() check fails the run if an object vanished.
 const run=async (name=dflt,steps)=>{let paths=Object.values(read(join(envs,id(name)+'.json')).assets).map(a=>a.path),pins=join(grave,'pins'),pin=join(pins,'foreground-'+proc.pid+'-'+Math.random().toString(36).slice(2)+'.json');
  mkdir(pins);try{create(pin,{schema:1,kind:'foreground',owner:{pid:proc.pid,birth:null},ref:'fg',paths:paths,created:new Date().toISOString()});syncdir(pin);
   for(let s of resolve(name,steps).steps){let code=await new Promise((resolve,reject)=>{let c=spawn(s.cmd,s.args,{...s.options,stdio:'inherit'});c.on('error',reject);c.on('close',n=>resolve(n??1))});if(code)return code;}return 0}finally{rm(pin)}};

 return {plan:spec=>plan(manifest(spec),wanted(manifest(spec),spec)).map(([id,recipe])=>({id,recipe})),provision:provision,run:run,view:view,resolve:resolve};
}
if(proc.argv[1]&&real(proc.argv[1])===u(import.meta.url)){
 let a=proc.argv.slice(2),root=p.dirname(u(import.meta.url));if(a[0]==='--root'){root=p.resolve(a[1]);a.splice(0,2)}
 try{let plot=openPlot(root),cmd=a.shift()||'run',name=a.shift()||dflt;if(cmd==='run'){if(name===dflt||!exists(join(root,'.grave','envs',name+'.json')))await plot.provision(name);proc.exitCode=await plot.run(name,a.length?[{cmd:a.shift(),args:a}]:undefined)}else console.log(JSON.stringify(cmd==='plan'?plot.plan():cmd==='provision'?await plot.provision(name):fail('unknown command')))}catch(e){console.error('[plot] '+e.message);proc.exitCode=1}
}
