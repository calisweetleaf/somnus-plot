#!/usr/bin/env node
// Somnus Plot v0.7 host bootstrap: inspect -> plan -> acquire -> verify -> activate.
// An acquired capability, never part of main.js. Installs are user-local under
// <root>/.grave/host/<tool>-<ver>-<plat>-<arch>-XXXXXX; .plot-host.json is written last.
import * as f from 'node:fs';
import * as p from 'node:path';
import os from 'node:os';
import {spawnSync} from 'node:child_process';
import {fileURLToPath as u} from 'node:url';
import {createGunzip,createInflateRaw,crc32} from 'node:zlib';
import {createHash,randomBytes} from 'node:crypto';
const join=p.join,exists=f.existsSync,here=p.dirname(u(import.meta.url));
class BootError extends Error{constructor(code,message,detail={}){super(message);this.code=code;this.detail=detail}}
const fail=(code,m,d)=>{throw new BootError(code,m,d)},read=x=>JSON.parse(f.readFileSync(x,'utf8'));
const stable=x=>JSON.stringify(x,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
const inside=(r,x)=>{let q=p.relative(r,x);return q===''||(q.split(p.sep)[0]!=='..'&&!p.isAbsolute(q))};
const sleep=ms=>new Promise(r=>setTimeout(r,ms)),now=()=>Number(process.hrtime.bigint()/1000000n);
const say=(o,m)=>{if(!o.quiet)process.stderr.write('[bootstrap] '+m+'\n')};
function fsyncDir(d){if(process.platform==='win32')return;let fd=f.openSync(d,'r');try{f.fsyncSync(fd)}finally{f.closeSync(fd)}}
function atom(x,v){let t=x+'.'+process.pid+'.'+randomBytes(3).toString('hex'),d=f.openSync(t,'wx',0o600);try{f.writeFileSync(d,typeof v==='string'?v:JSON.stringify(v));f.fsyncSync(d);f.closeSync(d);d=null;f.renameSync(t,x);fsyncDir(p.dirname(x))}finally{if(d!==null)f.closeSync(d);f.rmSync(t,{force:true})}}
function once(x,v){let d=f.openSync(x,'wx',0o600);try{f.writeFileSync(d,JSON.stringify(v));f.fsyncSync(d)}finally{f.closeSync(d)}fsyncDir(p.dirname(x))}
const mkdir=(d,mode=0o700)=>(f.mkdirSync(d,{recursive:true,mode}),d);
function birth(pid){try{return f.readFileSync('/proc/sys/kernel/random/boot_id','utf8').trim()+':'+f.readFileSync(`/proc/${pid}/stat`,'utf8').split(') ').pop().split(' ')[19]}catch{return null}}
// absent | other (pid reused) | same | unknown (alive, identity unprovable)
function owner(o){if(!Number.isInteger(o?.pid))return 'absent';try{process.kill(o.pid,0)}catch(e){if(e.code==='ESRCH')return 'absent'}let b=birth(o.pid);return o.birth&&b?(b===o.birth?'same':'other'):'unknown'}
async function sha256(file){let h=createHash('sha256');for await(let b of f.createReadStream(file))h.update(b);return h.digest('hex')}
const hostDir=root=>join(root,'.grave','host');

// ---- host description
function musl(){try{return f.readdirSync('/lib').some(n=>n.startsWith('ld-musl-'))}catch{return false}}
export function detect(target){
 if(target){let [platform,arch,libc]=String(target).split('-');if(!/^(linux|darwin|win32|android)$/.test(platform)||!/^(x64|arm64)$/.test(arch||''))fail('bad-target','target must be <linux|darwin|win32|android>-<x64|arm64>[-glibc|-musl]',{target});return {platform,arch,libc:platform==='linux'?(libc||'glibc'):null,glibc:null,target:true}}
 let platform=process.platform,arch=process.arch,libc=null,glibc=null;
 if(platform==='linux'&&/com\.termux/.test(process.env.PREFIX||''))platform='android';
 if(platform==='linux'){process.report.excludeNetwork=true;glibc=process.report.getReport().header.glibcVersionRuntime||null;libc=glibc?'glibc':musl()?'musl':'unknown'}
 return {platform,arch,libc,glibc,target:false};
}
const slot=(t,v,h)=>`${t}-${v}-${h.platform}${h.libc==='musl'?'_musl':''}-${h.arch}`;
const vcmp=(a,b)=>{let x=String(a).split('.').map(Number),y=String(b).split('.').map(Number);for(let i=0;i<Math.max(x.length,y.length);i++){let d=(x[i]||0)-(y[i]||0);if(d)return Math.sign(d)}return 0};
function which(name,PATH=process.env.PATH||''){let ext=process.platform==='win32'?(process.env.PATHEXT||'.EXE;.CMD;.BAT').split(';').concat(['']):[''];for(let d of PATH.split(p.delimiter).filter(Boolean))for(let e of ext){let x=join(d,name+e);try{let s=f.statSync(x);if(s.isFile()&&(process.platform==='win32'||s.mode&0o111))return x}catch{}}return null}
const versionArgs={node:['--version'],python3:['--version'],python:['--version'],git:['--version'],curl:['--version'],wget:['--version'],tar:['--version'],gzip:['--version'],xz:['--version'],unzip:['-v'],zstd:['--version'],cc:['--version'],gcc:['--version'],clang:['--version'],make:['--version'],sh:null,sha256sum:['--version'],shasum:['--version'],pwsh:['--version'],powershell:null};
function tool(name){let x=which(name);if(!x)return null;let a=versionArgs[name],v=null;if(a){let r=spawnSync(x,a,{encoding:'utf8',timeout:5000,stdio:['ignore','pipe','pipe']});v=((r.stdout||'')+(r.stderr||'')).split('\n').find(l=>l.trim())?.trim().slice(0,160)||null}return {path:x,version:v}}
function freeBytes(d){while(!exists(d)&&p.dirname(d)!==d)d=p.dirname(d);try{let s=f.statfsSync(d);return s.bavail*s.bsize}catch{return null}}
function writable(d){let x=d;while(!exists(x)&&p.dirname(x)!==x)x=p.dirname(x);try{f.accessSync(x,f.constants.W_OK);return true}catch{return false}}
async function online(o){if(o.offline)return {mode:'offline',probe:null,reason:'--offline'};let url=o.probeUrl||'https://nodejs.org/dist/',t=now();try{let r=await fetch(url,{method:'HEAD',signal:AbortSignal.timeout(5000)});return {mode:r.ok?'online':'offline',probe:{url,status:r.status,ms:now()-t}}}catch(e){return {mode:'offline',probe:{url,error:String(e.cause?.code||e.message),ms:now()-t}}}}
export async function inspect(o={}){
 let root=resolveRoot(o),h=detect(),executables=Object.fromEntries(Object.keys(versionArgs).map(n=>[n,tool(n)])),kit=o.kit?loadKit(o.kit):null;
 return {schema:'plot.bootstrap-inspect/1',root,host:{...h,os:os.type(),release:os.release(),termux:h.platform==='android'},
  node:{version:process.version,execPath:process.execPath,role:'entry A runtime (bootstrap itself runs on it)'},
  roots:[[hostDir(root),'install'],[os.tmpdir(),'temp'],[os.homedir(),'home']].map(([d,role])=>({path:d,role,exists:exists(d),writable:writable(d),freeBytes:freeBytes(d)})),
  executables,transports:{fetch:typeof fetch==='function',curl:executables.curl?.path||null,wget:executables.wget?.path||null},
  extractors:{'node:zlib-gzip':true,'builtin-ustar':true,'builtin-zip':true,tar:executables.tar?.path||null,gzip:executables.gzip?.path||null,xz:executables.xz?.path||null,unzip:executables.unzip?.path||null},
  network:await online(o),kit:kit&&{dir:kit.dir,artifacts:kit.artifacts.length}};
}

// ---- recipes and kits
const hex=/^[0-9a-f]{64}$/,fileName=/^[A-Za-z0-9][A-Za-z0-9._+-]{0,200}$/;
function checkUrl(x){let q;try{q=new URL(x)}catch{fail('bad-recipe','invalid URL '+x)}if(q.protocol==='https:'||(q.protocol==='http:'&&/^(127\.0\.0\.1|localhost|\[::1\])$/.test(q.hostname)))return x;fail('bad-recipe','URL must be https (plain http only on loopback): '+x)}
function checkArtifact(a,where){if(!hex.test(a.sha256||''))fail('bad-recipe',where+': sha256 must be 64 lowercase hex');if(!fileName.test(a.file||''))fail('bad-recipe',where+': unsafe file name');if(!Number.isInteger(a.size)||a.size<=0)fail('bad-recipe',where+': size required');if(!['tar.gz','zip'].includes(a.kind))fail('bad-recipe',where+': kind must be tar.gz or zip');if(!['binary','source-build'].includes(a.route))fail('bad-recipe',where+': route');if(a.url)checkUrl(a.url);return a}
export function loadRecipes(dir=join(here,'..','bootstrap','recipes')){
 let out={};for(let n of f.readdirSync(dir).filter(n=>n.endsWith('.json')).sort()){let r=read(join(dir,n));
  if(r.schema!=='plot.host-recipe/1'||!/^[a-z][a-z0-9-]{0,30}$/.test(r.tool||'')||!r.version||!Array.isArray(r.artifacts))fail('bad-recipe',n+': schema plot.host-recipe/1 with tool, version, artifacts required');
  r.artifacts.forEach((a,i)=>checkArtifact(a,`${n}#${i}`));out[r.tool]=r}
 return out;
}
export function loadKit(dir){
 dir=p.resolve(dir);let k;try{k=read(join(dir,'kit.json'))}catch(e){fail('bad-kit',`kit ${dir}: kit.json unreadable (${e.code||e.message})`,{kit:dir})}
 if(k.schema!=='plot.kit/1'||!Array.isArray(k.artifacts))fail('bad-kit','kit.json must have schema plot.kit/1 and artifacts[]',{kit:dir});
 k.artifacts.forEach((a,i)=>{checkArtifact(a,'kit#'+i);if(!a.tool||!a.version)fail('bad-kit','kit#'+i+': tool and version required')});return {dir,artifacts:k.artifacts};
}
const has=(v,x)=>v==='*'||v===x||(Array.isArray(v)&&v.includes(x));
const fits=(a,h)=>has(a.platform,h.platform)&&has(a.arch,h.arch)&&(a.libc==null||a.libc===h.libc);
function pick(recipe,h,kit){
 let a=recipe?.artifacts.find(a=>fits(a,h));if(a)return {art:a,provenance:'pinned-recipe'};
 let k=kit?.artifacts.find(x=>x.tool===recipe?.tool&&x.route==='binary'&&fits(x,h));if(k)return {art:k,provenance:'kit-declared'};
 return null;
}
function locate(art,kit,mode){
 let k=kit?.artifacts.find(x=>x.file===art.file),conflict=null;
 if(k&&k.sha256!==art.sha256)conflict=`kit records ${art.file} with sha256 ${k.sha256}, pinned ${art.sha256}; refusing a different artifact`;
 else if(k&&exists(join(kit.dir,k.file)))return {kind:'kit',path:join(kit.dir,k.file),file:art.file,sha256:art.sha256,size:art.size};
 if(mode==='online'&&art.url)return {kind:'online',url:art.url,file:art.file,sha256:art.sha256,size:art.size};
 return {kind:'none',file:art.file,sha256:art.sha256,size:art.size,reason:conflict||(mode!=='online'?'offline and no kit carries '+art.file:'no URL and no kit carries '+art.file)};
}
const exeOf=(recipe,art,h)=>art.exe||recipe.exe?.[h.platform==='win32'?'win32':'posix'];
const binOf=(recipe,art,h)=>art.bin??recipe.bin?.[h.platform==='win32'?'win32':'posix']??null;

// ---- install records
const marker=d=>join(d,'.plot-host.json');
function validInstall(d,id,art,exe){try{let m=read(marker(d));return m.schema==='plot.host/1'&&m.id===id&&m.source?.sha256===art.sha256&&m.path===f.realpathSync(d)&&m.exe===exe&&exists(join(d,exe))?m:null}catch{return null}}
function installs(root,id){let d=hostDir(root),re=new RegExp('^'+id.replace(/[.+]/g,'\\$&')+'-[A-Za-z0-9]{6}$');try{return f.readdirSync(d).filter(n=>re.test(n)).sort().map(n=>join(d,n))}catch{return []}}
function current(root,id,art,exe){for(let d of installs(root,id)){let m=validInstall(d,id,art,exe);if(m)return {path:d,marker:m}}return null}
// Tree digest over the published tree. __pycache__/*.pyc are excluded because the
// acquired interpreter legitimately writes bytecode caches next to its stdlib.
export async function tree(dir){
 let h=createHash('sha256'),files=0,links=0,dirs=0,bytes=0;
 async function walk(rel){for(let n of f.readdirSync(join(dir,rel)).sort()){let r=rel?rel+'/'+n:n,x=join(dir,r),s=f.lstatSync(x);
  if(!rel&&n==='.plot-host.json'||n==='__pycache__'||n.endsWith('.pyc'))continue;
  if(s.isSymbolicLink()){links++;h.update(`L ${r} ${f.readlinkSync(x)}\n`)}else if(s.isDirectory()){dirs++;h.update(`D ${r}\n`);await walk(r)}else{files++;bytes+=s.size;h.update(`F ${r} ${(s.mode&0o111)?'x':'-'} ${s.size} ${await sha256(x)}\n`)}}}
 await walk('');return {files,links,dirs,bytes,sha256:h.digest('hex')};
}

// ---- plan
const resolveRoot=o=>{let r=p.resolve(o.root||process.env.PLOT_ROOT||join(here,'..'));if(!exists(r))fail('bad-root','root does not exist: '+r);return f.realpathSync(r)};
export async function plan(o={}){
 let root=resolveRoot(o),h=detect(o.target),recipes=o.recipes||loadRecipes(o.recipesDir),kit=o.kit?(typeof o.kit==='string'?loadKit(o.kit):o.kit):null,net=o.mode?{mode:o.mode}:await online(o),mode=net.mode;
 let want=o.tools?.length?o.tools:['node','python','git'],nodes=new Map(),order=[];
 function visit(t,stack=[]){if(stack.includes(t))fail('cycle','recipe cycle '+[...stack,t].join(' -> '));let r=recipes[t];if(!r)fail('unknown-tool','no recipe for '+t,{known:Object.keys(recipes)});
  let chosen=pick(r,h,kit),art=chosen?.art,version=chosen?.provenance==='kit-declared'?art.version:r.version,id=slot(t,version,h);if(nodes.has(id))return id;
  let needs=(art?.needs||[]).map(d=>visit(d,[...stack,t])),n={id,tool:t,version,role:r.role||'tool',status:'acquire',route:art?.route||null,needs,provenance:chosen?.provenance||null,unsupported:null};
  if(!art){let why=r.unsupported?.find(x=>has(x.platform,h.platform)&&(!x.arch||x.arch===h.arch))?.reason||'no recipe artifact for this host';n.status='unsupported';n.unsupported=`${h.platform}-${h.arch}${h.libc?'-'+h.libc:''}: ${why}`}
  else{let exe=exeOf(r,art,h),src=locate(art,kit,mode),req=art.requires||{},problems=[],system=(req.system||[]).map(name=>{let x=h.target?null:tool(name);return {name,found:x?.path||null,version:x?.version||null}});
   if(req.glibc&&h.libc==='glibc'){if(!h.glibc)problems.push('host glibc version unknown (target plan)');else if(vcmp(h.glibc,req.glibc)<0)problems.push(`host glibc ${h.glibc} < required ${req.glibc}`)}
   if(h.libc==='unknown')problems.push('Linux C library not identified');
   let missing=system.filter(s=>!s.found).map(s=>s.name),hit=h.target?null:current(root,id,art,exe);
   Object.assign(n,{exe,bin:binOf(r,art,h),source:{...src,publisher:art.publisher||null,checksums:art.checksums||null,verified:art.verified||null},
    compatibility:{ok:problems.some(x=>/<|not identified/.test(x))?false:problems.length?null:true,requires:req,host:{platform:h.platform,arch:h.arch,libc:h.libc,glibc:h.glibc},problems},system,
    destination:join(hostDir(root),id+'-XXXXXX'),installed:hit?.path||null,
    disk:{download:src.kind==='online'?art.size:0,install:art.installed||art.unpacked||null,scratch:art.route==='source-build'?(art.buildScratch||null):art.unpacked||null},
    network:{required:!hit&&src.kind==='online',bytes:!hit&&src.kind==='online'?art.size:0,hosts:src.kind==='online'?[new URL(src.url).hostname]:[]},
    hostAlternative:h.target?null:(x=>x&&{path:x.path,version:x.version,used:false})(tool(t==='python'?'python3':t))});
   if(hit)n.status='present';
   else if(n.compatibility.ok===false){n.status='unsupported';n.unsupported=problems.join('; ')}
   else if(missing.length&&!h.target){n.status='unsupported';n.unsupported=`requires host prerequisites missing from PATH: ${missing.join(', ')}; bootstrap never installs system packages (no sudo, no package manager)`}
   else if(src.kind==='none'){n.status='blocked';n.unsupported=src.reason}
   for(let d of needs){let dn=nodes.get(d);if(n.status==='acquire'&&dn&&!['present','acquire'].includes(dn.status)){n.status='blocked';n.unsupported='dependency '+d+' is '+dn.status}}}
  nodes.set(id,n);order.push(id);return id;
 }
 for(let t of want)visit(t);
 let list=[...nodes.values()];
 return {schema:'plot.bootstrap-plan/1',root,host:h,mode,network:net.probe??null,kit:kit?.dir||null,nodes:list,order,
  unsupported:list.filter(n=>!['present','acquire'].includes(n.status)).map(n=>({id:n.id,status:n.status,reason:n.unsupported})),
  totals:{download:list.reduce((a,n)=>a+(n.network?.bytes||0),0),install:list.reduce((a,n)=>a+(n.status==='acquire'?n.disk?.install||0:0),0)},
  ok:list.every(n=>['present','acquire'].includes(n.status))};
}

// ---- transport: resumable, pinned, retried
async function download(src,dir,o){
 let done=join(dir,src.sha256),part=done+'.part',start=exists(part)?f.statSync(part).size:0,attempts=[],resumedFrom=start;
 if(exists(done)){if(await sha256(done)===src.sha256)return {file:done,resumedFrom:0,cached:true,attempts};f.rmSync(done)}
 for(let i=0;i<(o.retries??4);i++){
  let have=exists(part)?f.statSync(part).size:0;if(have>src.size){f.truncateSync(part,0);have=0}
  if(have===src.size)break;
  let ac=new AbortController(),idle,arm=()=>{clearTimeout(idle);idle=setTimeout(()=>ac.abort(new Error('idle timeout')),o.idleMs??60000)},res,status=null;
  try{arm();res=await fetch(src.url,{headers:have?{range:`bytes=${have}-`}:{},redirect:'follow',signal:ac.signal});status=res.status;
   if([400,401,403,404,410].includes(res.status)){clearTimeout(idle);fail('source-unavailable',`${src.url} answered HTTP ${res.status}`,{url:src.url,status:res.status,attempts:[...attempts,{status}],hint:'the pinned URL is gone or forbidden; supply an offline kit (--kit) carrying '+src.file})}
   if(res.status===416&&have){attempts.push({status,have});f.truncateSync(part,0);continue}
   if(!res.ok)throw new Error('HTTP '+res.status);
   let append=res.status===206&&new RegExp(`^bytes ${have}-`).test(res.headers.get('content-range')||'');
   let fd=f.openSync(part,append?'a':'w',0o600),n=append?have:0;
   try{for await(let b of res.body){arm();n+=b.length;if(n>src.size)fail('size-exceeded',`${src.url} delivered more than the pinned ${src.size} bytes`,{url:src.url,size:src.size});f.writeSync(fd,b)}f.fsyncSync(fd)}finally{f.closeSync(fd);clearTimeout(idle)}
   attempts.push({status,from:append?have:0,to:n});if(n===src.size)break;throw new Error(`short body ${n}/${src.size}`);
  }catch(e){clearTimeout(idle);if(e instanceof BootError){if(e.code==='size-exceeded')f.rmSync(part,{force:true});throw e}
   attempts.push({status,error:String(e.cause?.code||e.message)});say(o,`${src.file}: transient ${attempts.at(-1).error}; retry ${i+1}`);
   await sleep(Math.min(30000,(o.backoffMs??500)*2**i)*(0.5+Math.random()))}
 }
 if(!exists(part)||f.statSync(part).size!==src.size)fail('source-unavailable',`${src.url} could not be fetched after ${attempts.length} attempts`,{url:src.url,attempts,partial:exists(part)?f.statSync(part).size:0,hint:'transient network failure; rerun to resume from the partial file, or use --kit'});
 let got=await sha256(part);if(got!==src.sha256){f.rmSync(part,{force:true});fail('sha256-mismatch',`${src.file}: sha256 ${got} does not match pinned ${src.sha256}`,{url:src.url,expected:src.sha256,actual:got,hint:'the source served a different artifact; it was discarded and nothing was installed'})}
 f.renameSync(part,done);fsyncDir(dir);return {file:done,resumedFrom,cached:false,attempts};
}

// ---- extraction: streaming ustar/pax/GNU tar.gz and zip, confined to dest
function entryPath(x,strip){x=x.replace(/\/+$/,'');if(!x||/[\\:\0]/.test(x)||p.posix.isAbsolute(x)||x.split('/').includes('..'))fail('unsafe-archive','archive path rejected: '+JSON.stringify(x));let c=p.posix.normalize(x).split('/').filter(s=>s&&s!=='.');return c.length>strip?c.slice(strip).join('/'):null}
function place(dest,rel,links){for(let a=p.posix.dirname(rel);a!=='.';a=p.posix.dirname(a))if(links.has(a))fail('unsafe-archive','entry below a symlink: '+rel);let x=join(dest,rel);f.mkdirSync(p.dirname(x),{recursive:true,mode:0o755});if(!inside(dest,f.realpathSync(p.dirname(x))))fail('unsafe-archive','entry escapes destination: '+rel);return x}
export async function untar(file,dest,{strip=0,limit=4294967296,maxEntries=200000}={}){
 dest=f.realpathSync(dest);let buf=Buffer.alloc(0),st='head',left=0,pad=0,fd=null,meta=null,cur=null,pax={},long={},names=new Set(),links=new Set(),total=0,count=0,ended=false;
 const str=(h,a,n)=>{let s=h.subarray(a,a+n),z=s.indexOf(0);return (z<0?s:s.subarray(0,z)).toString('utf8')};
 const oct=s=>{s=s.trim();if(!/^[0-7]*$/.test(s))fail('unsafe-archive','tar number field');return parseInt(s||'0',8)};
 function begin(h){
  let sum=0;for(let i=0;i<512;i++)sum+=i>=148&&i<156?32:h[i];if(sum!==oct(str(h,148,8)))fail('unsafe-archive','tar header checksum');
  let t=String.fromCharCode(h[156]||48),n=oct(str(h,124,12)),ustar=str(h,257,6).startsWith('ustar');
  if(++count>maxEntries)fail('unsafe-archive','tar entry limit');
  if('xgLK'.includes(t)){if(n>1048576)fail('unsafe-archive','tar metadata entry too large');meta={t,parts:[]};cur=null;return n}
  let name=pax.path??long.L??(ustar&&str(h,345,155)?str(h,345,155)+'/':'')+str(h,0,100),link=pax.linkpath??long.K??str(h,157,100);if(pax.size)n=Number(pax.size);pax={};long={};
  let mode=oct(str(h,100,8))&0o755,rel=entryPath(name,strip);meta=null;cur=null;
  if(rel===null){if(t==='5')return 0;if(n===0&&'012'.includes(t))return 0;fail('unsafe-archive','file entry above strip depth: '+name)}
  if(t==='5'){f.mkdirSync(place(dest,rel,links),{recursive:true,mode:mode|0o700});names.add(rel);return 0}
  if(names.has(rel))fail('unsafe-archive','duplicate archive entry: '+rel);names.add(rel);
  if(t==='2'){if(!link||p.posix.isAbsolute(link)||/[\\\0]/.test(link)||p.posix.normalize(p.posix.join(p.posix.dirname(rel),link)).split('/')[0]==='..')fail('unsafe-archive','symlink escapes destination: '+rel+' -> '+link);f.symlinkSync(link,place(dest,rel,links));links.add(rel);return 0}
  if(t==='1'){let target=entryPath(link,strip);if(!target||!names.has(target)||links.has(target))fail('unsafe-archive','hardlink target outside archive: '+rel+' -> '+link);f.linkSync(join(dest,target),place(dest,rel,links));return 0}
  if(!'07\0'.includes(t)&&t!=='0')fail('unsafe-archive',`unsupported tar entry type ${JSON.stringify(t)} for ${rel}`);
  total+=n;if(total>limit)fail('unsafe-archive','archive expands beyond limit '+limit);
  fd=f.openSync(place(dest,rel,links),'wx',mode|0o600);cur=rel;return n;
 }
 function close(){if(fd!==null){f.closeSync(fd);fd=null}if(meta){let b=Buffer.concat(meta.parts).toString('utf8');if(meta.t==='x'){for(let i=0;i<b.length;){let sp=b.indexOf(' ',i),len=parseInt(b.slice(i,sp),10);if(!(len>0))fail('unsafe-archive','pax record');let rec=b.slice(sp+1,i+len-1),eq=rec.indexOf('=');pax[rec.slice(0,eq)]=rec.slice(eq+1);i+=len}}else if(meta.t==='L'||meta.t==='K')long[meta.t]=b.replace(/\0+$/,'');meta=null}}
 function step(){
  if(st==='data'){let n=Math.min(left,buf.length);if(n){let c=buf.subarray(0,n);meta?meta.parts.push(Buffer.from(c)):fd!==null&&f.writeSync(fd,c);buf=buf.subarray(n);left-=n}if(left)return false;close();st='pad';return true}
  if(st==='pad'){let n=Math.min(pad,buf.length);buf=buf.subarray(n);pad-=n;if(pad)return false;st='head';return true}
  if(st==='end'||buf.length<512)return false;
  let h=buf.subarray(0,512);buf=buf.subarray(512);if(h.every(v=>v===0)){st='end';ended=true;return false}
  left=begin(h);pad=(512-left%512)%512;st='data';return true;
 }
 let gz=f.createReadStream(file).pipe(createGunzip());
 try{for await(let c of gz){buf=buf.length?Buffer.concat([buf,c]):c;while(step());}}finally{if(fd!==null)f.closeSync(fd)}
 if(st==='data'||st==='pad'||(!ended&&buf.length))fail('unsafe-archive','truncated tar stream'+(cur?' in '+cur:''));
 return {entries:count,bytes:total};
}
export async function unzip(file,dest,{strip=0,limit=4294967296}={}){
 dest=f.realpathSync(dest);let fd=f.openSync(file,'r');try{
  let size=f.fstatSync(fd).size,tl=Math.min(size,65557),tail=Buffer.alloc(tl);f.readSync(fd,tail,0,tl,size-tl);
  let e=-1;for(let i=tl-22;i>=0;i--)if(tail.readUInt32LE(i)===0x06054b50){e=i;break}if(e<0)fail('unsafe-archive','zip end record missing');
  let count=tail.readUInt16LE(e+10),cdSize=tail.readUInt32LE(e+12),cdOff=tail.readUInt32LE(e+16);if(count===0xffff||cdOff===0xffffffff)fail('unsafe-archive','zip64 archives are not supported');
  let cd=Buffer.alloc(cdSize);f.readSync(fd,cd,0,cdSize,cdOff);let names=new Set(),total=0,o=0;
  for(let k=0;k<count;k++){if(cd.readUInt32LE(o)!==0x02014b50)fail('unsafe-archive','zip central directory');
   let flags=cd.readUInt16LE(o+8),method=cd.readUInt16LE(o+10),crc=cd.readUInt32LE(o+16),cs=cd.readUInt32LE(o+20),us=cd.readUInt32LE(o+24),nl=cd.readUInt16LE(o+28),xl=cd.readUInt16LE(o+30),cl=cd.readUInt16LE(o+32),attr=cd.readUInt32LE(o+38),lho=cd.readUInt32LE(o+42),name=cd.subarray(o+46,o+46+nl).toString('utf8');o+=46+nl+xl+cl;
   if(flags&1)fail('unsafe-archive','encrypted zip entry '+name);if(((attr>>>16)&0o170000)===0o120000)fail('unsafe-archive','zip symlink entries are not supported: '+name);
   let rel=entryPath(name,strip);if(rel===null)continue;if(names.has(rel)&&!name.endsWith('/'))fail('unsafe-archive','duplicate archive entry: '+rel);names.add(rel);
   if(name.endsWith('/')){f.mkdirSync(place(dest,rel,new Set()),{recursive:true,mode:0o755});continue}
   if(![0,8].includes(method))fail('unsafe-archive',`zip method ${method} unsupported for ${name}`);total+=us;if(total>limit)fail('unsafe-archive','archive expands beyond limit');
   let lh=Buffer.alloc(30);f.readSync(fd,lh,0,30,lho);if(lh.readUInt32LE(0)!==0x04034b50)fail('unsafe-archive','zip local header');
   let at=lho+30+lh.readUInt16LE(26)+lh.readUInt16LE(28),mode=(attr>>>16)&0o755||0o644,out=f.openSync(place(dest,rel,new Set()),'wx',mode|0o600),c=0,n=0;
   try{let s=cs?f.createReadStream(null,{fd,start:at,end:at+cs-1,autoClose:false}):[];if(method===8&&cs)s=s.pipe(createInflateRaw());for await(let b of s){n+=b.length;if(n>us)fail('unsafe-archive','zip entry larger than declared: '+name);c=crc32(b,c);f.writeSync(out,b)}}finally{f.closeSync(out)}
   if(n!==us||(c>>>0)!==crc)fail('unsafe-archive','zip entry size/crc mismatch: '+name);
  }return {entries:count,bytes:total};
 }finally{f.closeSync(fd)}
}

// ---- locks: one per install slot; owner {pid,birth,attempt}; stale owners broken under a breaker dir
async function lock(root,id,info,o){
 let d=mkdir(join(hostDir(root),'.locks')),l=join(d,id),t=now(),waited=false,broke=[];
 for(;;){try{f.mkdirSync(l,{mode:0o700});once(join(l,'owner.json'),{...info,pid:process.pid,birth:birth(process.pid)});return {path:l,waited,broke}}catch(e){if(e.code!=='EEXIST')throw e}
  let own=null;try{own=read(join(l,'owner.json'))}catch{}
  let stale=own?['absent','other'].includes(owner(own)):(()=>{try{return Date.now()-f.statSync(l).mtimeMs>10000}catch{return false}})();
  if(stale){let b=join(d,id+'.break');try{f.mkdirSync(b)}catch(e){if(e.code!=='EEXIST')throw e;try{if(Date.now()-f.statSync(b).mtimeMs>30000)f.rmSync(b,{recursive:true,force:true})}catch{}await sleep(50);continue}
   try{let again=null;try{again=read(join(l,'owner.json'))}catch{}if(stable(again)===stable(own)){let dead=join(d,'.dead-'+id+'-'+randomBytes(4).toString('hex'));f.renameSync(l,dead);f.rmSync(dead,{recursive:true,force:true});broke.push(own||{owner:'unrecorded'})}}catch(e){if(e.code!=='ENOENT')throw e}finally{f.rmSync(b,{recursive:true,force:true})}continue}
  if(now()-t>(o.waitMs??1800000))fail('lock-timeout',`${id}: lock held by pid ${own?.pid} (attempt ${own?.attempt}) beyond ${o.waitMs??1800000} ms`,{lock:l,owner:own,hint:'another acquisition is still running; retry later'});
  if(!waited)say(o,`${id}: waiting for concurrent acquisition by pid ${own?.pid}`);waited=true;await sleep(150);
 }
}
const unlock=l=>{f.rmSync(join(l.path,'owner.json'),{force:true});f.rmdirSync(l.path)};
// Under the slot lock every unmarked directory for the slot belongs to a dead attempt.
function sweep(root,id){let out=[],H=hostDir(root);for(let d of installs(root,id))if(!exists(marker(d))){f.rmSync(d,{recursive:true,force:true});out.push(d)}
 for(let s of ['.stage','.build'])for(let n of (exists(join(H,s))?f.readdirSync(join(H,s)):[]))if(n.startsWith(id+'-')){f.rmSync(join(H,s,n),{recursive:true,force:true});out.push(join(H,s,n))}return out}
function expand(s,vars){return String(s).replace(/\$\{([a-z]+(?::[a-z0-9-]+)?)\}/g,(_,k)=>k in vars?vars[k]:fail('bad-recipe','unknown build variable '+k))}
function probeTool(r,dir,n,h){let exe=join(dir,n.exe),bin=n.bin!=null?join(dir,n.bin):p.dirname(exe);if(!r.probe)return {ok:exists(exe),output:exists(exe)?'present '+n.exe:'missing '+n.exe};
 let env={PATH:bin};if(h.platform==='win32')env.SystemRoot=process.env.SystemRoot;let x=spawnSync(exe,r.probe.args,{encoding:'utf8',timeout:60000,env,cwd:dir}),out=((x.stdout||'')+(x.stderr||'')).trim();
 return {ok:x.status===0&&(!r.probe.expect||new RegExp(r.probe.expect).test(out)),output:out.slice(0,400),status:x.status,error:x.error?.message}}

async function acquireOne(root,n,r,deps,o,h){
 let t0=now(),hit=!o.force&&current(root,n.id,{sha256:n.source.sha256},n.exe);if(hit)return {id:n.id,action:'reuse',path:hit.path,ms:now()-t0};
 let attempt=new Date().toISOString().replace(/\D/g,'').slice(0,14)+'-'+process.pid+'-'+randomBytes(3).toString('hex'),H=hostDir(root);
 let l=await lock(root,n.id,{attempt,source:{kind:n.source.kind,url:n.source.url,path:n.source.path,sha256:n.source.sha256}},o),stage=null,final=null,build=null,dl=null;
 try{
  hit=current(root,n.id,{sha256:n.source.sha256},n.exe);if(hit&&(!o.force||l.waited))return {id:n.id,action:l.waited?'shared':'reuse',path:hit.path,ms:now()-t0};
  let recovered=sweep(root,n.id),src=n.source;
  once(join(mkdir(join(H,'.attempts')),attempt+'.json'),{attempt,id:n.id,pid:process.pid,source:src,started:new Date().toISOString(),brokeLocks:l.broke});
  if(src.kind==='none')fail('no-source',`${n.id}: ${src.reason}`,{id:n.id,file:src.file,sha256:src.sha256,hint:'provide --kit <dir> with this artifact (node capabilities/bootstrap.mjs kit <dir> on a networked host) or run online'});
  let archive=src.path,t1=now();
  if(src.kind==='online'){say(o,`${n.id}: fetching ${src.url}`);dl=await download(src,mkdir(join(H,'.dl')),o);archive=dl.file}
  else{let got=await sha256(archive);if(got!==src.sha256)fail('sha256-mismatch',`${archive}: sha256 ${got} does not match pinned ${src.sha256}`,{path:archive,expected:src.sha256,actual:got,hint:'the kit file is corrupt or different; rebuild the kit'})}
  let fetchMs=now()-t1,t2=now();stage=f.mkdtempSync(join(mkdir(join(H,'.stage')),n.id+'-'));f.chmodSync(stage,0o755);
  let art={strip:n.strip??1};
  if(n.route==='source-build'){build=f.mkdtempSync(join(mkdir(join(H,'.build')),n.id+'-'));let src2=mkdir(join(build,'src'),0o755);await untar(archive,src2,{strip:n.strip});
   let logf=join(mkdir(join(H,'.logs')),attempt+'.log'),log=f.openSync(logf,'a',0o600),vars={out:stage,src:src2,jobs:String(o.jobs||os.availableParallelism?.()||2)};for(let d of n.needs)vars['dep:'+deps[d].tool]=deps[d].path;
   let env={...process.env,LC_ALL:'C'};delete env.MAKEFLAGS;delete env.MFLAGS;delete env.MAKELEVEL;
   try{for(let s of n.build){let cmd=expand(s.cmd,vars),args=(s.args||[]).map(a=>expand(a,vars));f.writeSync(log,`\n$ ${cmd} ${args.join(' ')}\n`);say(o,`${n.id}: ${cmd} ${args[0]||''}`);
    let x=spawnSync(cmd,args,{cwd:src2,env,stdio:['ignore',log,log],timeout:o.buildMs??3600000});
    if(x.error||x.status!==0){f.fsyncSync(log);let tail=f.readFileSync(logf,'utf8').slice(-2000);fail('build-failed',`${n.id}: ${cmd} ${args[0]||''} exited ${x.status??x.error?.code}`,{log:logf,tail,hint:'see the build log; the host toolchain (declared prerequisites) must be able to build this source'})}}}
   finally{f.closeSync(log)}
  }else if(n.kind==='zip')await unzip(archive,stage,{strip:n.strip});else await untar(archive,stage,{strip:n.strip,limit:Math.max(268435456,(n.unpacked||0)*2)});
  final=join(H,n.id+stage.slice(stage.lastIndexOf('-')));f.renameSync(stage,final);stage=null;fsyncDir(H);
  let pr=probeTool(r,final,n,h);if(!pr.ok)fail('probe-failed',`${n.id}: installed tool failed its probe`,{path:final,probe:pr,hint:'artifact is incompatible with this host (see plan compatibility) or a system library is missing'});
  let tr=await tree(final),m={schema:'plot.host/1',id:n.id,tool:n.tool,version:n.version,platform:h.platform,arch:h.arch,libc:h.libc,route:n.route,provenance:n.provenance,
   source:{kind:src.kind,file:src.file,url:src.url||null,path:src.path||null,sha256:src.sha256,size:src.size,publisher:src.publisher},inputs:n.route==='source-build'?{deps:Object.fromEntries(n.needs.map(d=>[d,{path:deps[d].path,sha256:deps[d].sha256}])),toolchain:n.system}:null,
   path:f.realpathSync(final),exe:n.exe,bin:n.bin,probe:{args:r.probe?.args||null,output:pr.output},tree:tr,writer:'bootstrap.mjs',attempt,at:new Date().toISOString()};
  atom(marker(final),m);
  if(dl&&!o.keepArchives)f.rmSync(dl.file,{force:true});
  return {id:n.id,action:'acquired',path:final,source:src.kind,resumedFrom:dl?.resumedFrom||0,attempts:dl?.attempts||[],recovered,brokeLocks:l.broke,bytes:tr.bytes,files:tr.files,ms:now()-t0,fetchMs,installMs:now()-t2};
 }catch(e){if(stage)f.rmSync(stage,{recursive:true,force:true});if(final&&!exists(marker(final)))f.rmSync(final,{recursive:true,force:true});throw e}
 finally{if(build)f.rmSync(build,{recursive:true,force:true});unlock(l)}
}
export async function acquire(o={}){
 let pl=await plan(o),root=pl.root,h=pl.host,recipes=o.recipes||loadRecipes(o.recipesDir),done={},results=[];if(h.target)fail('bad-target','acquire installs for the running host only');
 for(let id of pl.order){let n=pl.nodes.find(x=>x.id===id),r=recipes[n.tool];
  if(!['present','acquire'].includes(n.status))fail(n.status==='blocked'&&n.source?.kind==='none'?'no-source':'unsupported',`${id}: ${n.unsupported}`,{id,status:n.status,results,hint:n.status==='unsupported'?'see plan unsupported reasons':'provide --kit or go online'});
  let art=pick(r,h,o.kit?(typeof o.kit==='string'?loadKit(o.kit):o.kit):null).art;Object.assign(n,{kind:art.kind,strip:art.strip,build:art.build,unpacked:art.unpacked});
  let x=await acquireOne(root,n,r,done,o,h);results.push(x);done[id]={path:x.path,tool:n.tool,sha256:n.source.sha256};say(o,`${id}: ${x.action} ${x.path} (${x.ms} ms)`)}
 return {schema:'plot.bootstrap-acquire/1',root,host:h,mode:pl.mode,results,ok:true};
}
export async function verify(o={}){
 let pl=await plan({...o,mode:'offline'}),recipes=o.recipes||loadRecipes(o.recipesDir),tools=[];
 for(let n of pl.nodes){if(!n.installed){tools.push({id:n.id,installed:false});continue}
  let m=read(marker(n.installed)),pr=probeTool(recipes[n.tool],n.installed,n,pl.host),tr=m.tree?await tree(n.installed):null;
  tools.push({id:n.id,installed:true,path:n.installed,writer:m.writer,source:m.source,probe:pr,tree:m.tree?(tr.sha256===m.tree.sha256?'match':'mismatch'):'unrecorded',...(tr&&tr.sha256!==m.tree.sha256?{expected:m.tree,actual:tr}:{})})}
 let req=o.tools?.length?o.tools:null;
 return {schema:'plot.bootstrap-verify/1',root:pl.root,tools,ok:tools.filter(t=>!req||req.some(q=>t.id.startsWith(q+'-'))).every(t=>t.installed&&t.probe.ok&&t.tree!=='mismatch')};
}
export async function activate(o={}){
 let pl=await plan({...o,mode:'offline'}),tools={},missing=[],bins=[];
 for(let n of pl.nodes){if(n.role==='build-dependency')continue;if(!n.installed){missing.push(n.id);continue}let bin=join(n.installed,n.bin??p.dirname(n.exe));bins.push(bin);tools[n.tool]={id:n.id,path:n.installed,exe:join(n.installed,n.exe),bin}}
 let PATH=[...bins,process.env.PATH||''].filter(Boolean).join(p.delimiter),env={PATH,...Object.fromEntries(Object.entries(tools).map(([t,x])=>['PLOT_HOST_'+t.toUpperCase(),x.exe]))};
 return {schema:'plot.bootstrap-activate/1',root:pl.root,tools,env,missing,ok:!missing.length};
}
export async function kit(o={}){
 if(!o.dir)fail('usage','kit <dir> is required');let dir=mkdir(p.resolve(o.dir),0o755),recipes=o.recipes||loadRecipes(o.recipesDir),want=o.tools?.length?o.tools:Object.keys(recipes);
 let hosts=(o.hosts||'linux-x64').split(',').map(detect),records=[],net=await online(o);
 for(let t of want){let r=recipes[t]||fail('unknown-tool','no recipe for '+t);for(let a of r.artifacts){if(!hosts.some(h=>fits(a,h))||records.some(x=>x.file===a.file))continue;
  let dest=join(dir,a.file),src=o.from&&join(o.from,a.file);
  if(!(exists(dest)&&await sha256(dest)===a.sha256)){if(src&&exists(src)&&await sha256(src)===a.sha256)f.copyFileSync(src,dest);
   else if(net.mode==='online'){let d=await download({url:a.url,file:a.file,sha256:a.sha256,size:a.size},mkdir(join(dir,'.dl')),o);f.renameSync(d.file,dest)}
   else fail('no-source',`kit: ${a.file} not in --from and offline`,{file:a.file})}
  records.push({tool:t,version:a.version||r.version,...a})}}
 f.rmSync(join(dir,'.dl'),{recursive:true,force:true});
 let old=exists(join(dir,'kit.json'))?read(join(dir,'kit.json')).artifacts.filter(x=>!records.some(y=>y.file===x.file)&&exists(join(dir,x.file))):[],all=[...old,...records].sort((a,b)=>a.file<b.file?-1:1);
 atom(join(dir,'kit.json'),JSON.stringify({schema:'plot.kit/1',created:new Date().toISOString(),artifacts:all},null,1)+'\n');
 atom(join(dir,'SHA256SUMS'),all.map(a=>`${a.sha256}  ${a.file}\n`).join(''));
 return {schema:'plot.bootstrap-kit/1',dir,artifacts:all.map(a=>({tool:a.tool,file:a.file,size:a.size,platform:a.platform,arch:a.arch,libc:a.libc}))};
}

// ---- CLI
const shq=s=>"'"+String(s).replace(/'/g,"'\\''")+"'";
export async function cli(argv){
 let o={tools:[]},cmd=argv[0],flags={'--root':'root','--kit':'kit','--recipes':'recipesDir','--wait-ms':'waitMs','--jobs':'jobs','--target':'target','--format':'format','--hosts':'hosts','--from':'from','--idle-ms':'idleMs','--retries':'retries','--backoff-ms':'backoffMs','--probe-url':'probeUrl'};
 for(let i=1;i<argv.length;i++){let a=argv[i];if(flags[a]){if(i+1>=argv.length)fail('usage',a+' needs a value');o[flags[a]]=argv[++i]}else if(a==='--offline')o.offline=true;else if(a==='--force')o.force=true;else if(a==='--keep-archives')o.keepArchives=true;else if(a==='--quiet')o.quiet=true;else if(a.startsWith('--'))fail('usage','unknown flag '+a);else if(cmd==='kit'&&!o.dir)o.dir=a;else o.tools.push(...a.split(',').filter(Boolean))}
 for(let k of ['waitMs','jobs','idleMs','retries','backoffMs'])if(o[k]!=null){o[k]=Number(o[k]);if(!Number.isInteger(o[k])||o[k]<0)fail('usage',k+' must be a non-negative integer')}
 if(o.kit)o.kit=loadKit(o.kit);
 let fn={inspect,plan,acquire,verify,activate,kit}[cmd];if(!fn)fail('usage','usage: bootstrap.mjs inspect|plan|acquire|verify|activate|kit [tools...] [--root R] [--kit DIR] [--offline] [--target plat-arch[-libc]] [--force] [--format json|sh]');
 let r=await fn(o);
 if(cmd==='activate'&&o.format==='sh')return {text:Object.entries(r.env).map(([k,v])=>`${k}=${shq(v)}; export ${k}`).join('\n')+'\n',ok:r.ok};
 return {text:JSON.stringify(r)+'\n',ok:r.ok!==false};
}
if(process.argv[1]&&f.realpathSync(process.argv[1])===u(import.meta.url)){
 try{let r=await cli(process.argv.slice(2));process.stdout.write(r.text);if(!r.ok)process.exitCode=1}
 catch(e){let err=e instanceof BootError?{code:e.code,message:e.message,...e.detail}:{code:e.code||'internal',message:e.message};process.stdout.write(JSON.stringify({ok:false,error:err})+'\n');process.stderr.write(`[bootstrap] ${err.code}: ${err.message}\n`);process.exitCode=1}
}
