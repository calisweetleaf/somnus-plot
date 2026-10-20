// Optional Plot offline layer assembler. Acquired under .grave/objects, never a core dependency.
// Installs PEP 427 wheels and plot.closure/1 npm nodes from local files only: no pip, ensurepip,
// npm or network. planWheels emits plot.closure/1 wheel nodes from a bank. Supported ZIP subset: stored + deflate, no zip64, no encryption, no multi-disk.
// PLOT_ASSEMBLER_CRASH=staged SIGKILLs the writer after staging and before .plot.json (crash tests).
import * as fs from 'node:fs';
import * as path from 'node:path';
import zlib from 'node:zlib';
import {spawnSync} from 'node:child_process';
import {createHash,randomUUID,randomBytes} from 'node:crypto';
import {fileURLToPath} from 'node:url';

const self=fileURLToPath(import.meta.url);
export const LIMITS=Object.freeze({archiveBytes:268435456,entries:100000,fileBytes:268435456,totalBytes:1073741824});
export class AssemblyError extends Error{constructor(code,message,extra={}){super(message);this.name='AssemblyError';this.code=code;this.retryable=false;Object.assign(this,extra)}}
const fail=(code,message,extra)=>{throw new AssemblyError(code,message,extra)};
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const stable=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.keys(x).sort().map(k=>[k,x[k]])):x);
const sig=()=>[process.platform,process.arch];
const inside=(r,x)=>{let q=path.relative(r,x);return !!q&&q.split(path.sep)[0]!=='..'&&!path.isAbsolute(q)};
const within=(r,x)=>x===r||inside(r,x);
const canon=s=>String(s).toLowerCase().replace(/[-_.]+/g,'_');
const validId=x=>typeof x==='string'&&/^[A-Za-z0-9_-]{1,64}$/.test(x)?x:fail('USAGE','invalid assembly id '+JSON.stringify(x));
const sha256=b=>createHash('sha256').update(b).digest('hex');
function syncDir(d){if(process.platform==='win32')return;let fd=fs.openSync(d,'r');try{fs.fsyncSync(fd)}finally{fs.closeSync(fd)}}
function atom(p,v){const t=p+'.'+randomUUID(),fd=fs.openSync(t,'wx',0o600);try{fs.writeFileSync(fd,JSON.stringify(v));fs.fsyncSync(fd)}finally{fs.closeSync(fd)}try{fs.renameSync(t,p);syncDir(path.dirname(p))}finally{fs.rmSync(t,{force:true})}}
function once(p,v){const fd=fs.openSync(p,'wx',0o600);try{fs.writeFileSync(fd,JSON.stringify(v));fs.fsyncSync(fd)}finally{fs.closeSync(fd)}syncDir(path.dirname(p))}
const directory=p=>{fs.mkdirSync(p,{recursive:true,mode:0o700});if(fs.lstatSync(p).isSymbolicLink())fail('PATH','owned directory is a symlink: '+p);return p};
// Boot ID + Linux start ticks distinguish a reused PID; elsewhere a live PID is deliberately unknown.
function birth(pid){try{const s=fs.readFileSync(`/proc/${pid}/stat`,'utf8');return fs.readFileSync('/proc/sys/kernel/random/boot_id','utf8').trim()+':'+s.slice(s.lastIndexOf(')')+2).split(' ')[19]}catch{return null}}
function identity(o){if(!o||!Number.isSafeInteger(o.pid)||o.pid<1)return 'unknown';try{process.kill(o.pid,0)}catch(e){return e.code==='ESRCH'?'absent':'unknown'}let b=birth(o.pid);return b&&o.birth?(b===o.birth?'same':'other'):'unknown'}
const crc32=zlib.crc32||(()=>{let t=new Int32Array(256);for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;t[n]=c}return b=>{let c=-1;for(let i=0;i<b.length;i++)c=t[(c^b[i])&255]^(c>>>8);return (c^-1)>>>0}})();
function clean(name,label){let x=String(name).replace(/\/$/,'');if(!x||x.length>4096||/[\\:\0]/.test(x)||x.startsWith('/')||x.split('/').some(c=>!c||c==='.'||c==='..'))fail('PATH',`${label}: unsafe path ${JSON.stringify(name)}`);return x}
function limitsOf(l){let o={...LIMITS,...l};for(let k of Object.keys(LIMITS))if(!Number.isSafeInteger(o[k])||o[k]<0)fail('USAGE','invalid limit '+k);return o}

// Whole-archive read bounded by archiveBytes; entries decompress on demand with declared-size caps.
export function readZip(file,limits){
 let L=limitsOf(limits),label=path.basename(file),size=fs.statSync(file).size;
 if(size>L.archiveBytes)fail('LIMIT',`${label}: archive ${size} bytes exceeds limit ${L.archiveBytes}`);
 let b=fs.readFileSync(file),e=-1;
 for(let i=b.length-22;i>=Math.max(0,b.length-65557);i--)if(b.readUInt32LE(i)===0x06054b50&&i+22+b.readUInt16LE(i+20)===b.length){e=i;break}
 if(e<0)fail('ZIP',label+': end of central directory not found');
 if(e>=20&&b.readUInt32LE(e-20)===0x07064b50)fail('ZIP',label+': zip64 unsupported');
 let count=b.readUInt16LE(e+10),cdSize=b.readUInt32LE(e+12),cdOff=b.readUInt32LE(e+16);
 if(count===0xffff||cdSize===0xffffffff||cdOff===0xffffffff)fail('ZIP',label+': zip64 unsupported');
 if(b.readUInt16LE(e+4)||b.readUInt16LE(e+6)||b.readUInt16LE(e+8)!==count)fail('ZIP',label+': multi-disk archive unsupported');
 if(cdOff+cdSize!==e)fail('ZIP',label+': central directory bounds');
 if(count>L.entries)fail('LIMIT',`${label}: ${count} entries exceeds limit ${L.entries}`);
 let out=[],names=new Set(),ranges=[],total=0,o=cdOff;
 for(let n=0;n<count;n++){
  if(o+46>e||b.readUInt32LE(o)!==0x02014b50)fail('ZIP',`${label}: central header ${n} corrupt`);
  let made=b.readUInt16LE(o+4),flags=b.readUInt16LE(o+8),method=b.readUInt16LE(o+10),crc=b.readUInt32LE(o+16),csize=b.readUInt32LE(o+20),usize=b.readUInt32LE(o+24),nl=b.readUInt16LE(o+28),attr=b.readUInt32LE(o+38),lho=b.readUInt32LE(o+42);
  let raw=b.subarray(o+46,o+46+nl);o+=46+nl+b.readUInt16LE(o+30)+b.readUInt16LE(o+32);if(o>e)fail('ZIP',label+': central directory overrun');
  if(csize===0xffffffff||usize===0xffffffff||lho===0xffffffff)fail('ZIP',label+': zip64 unsupported');
  if(flags&0x41)fail('ZIP',label+': encrypted entry unsupported');
  let name;if(flags&0x800){try{name=new TextDecoder('utf-8',{fatal:true}).decode(raw)}catch{fail('ZIP',label+': invalid UTF-8 entry name')}}else{if(raw.some(c=>c>127))fail('ZIP',label+': non-ASCII name without UTF-8 flag');name=raw.toString('latin1')}
  if(names.has(name))fail('PATH',`${label}: duplicate zip entry ${name}`);names.add(name);
  let mode=[3,19].includes(made>>8)?attr>>>16:0,type=mode&0o170000,dir=name.endsWith('/')||type===0o040000||(!mode&&!!(attr&0x10));
  if(type===0o120000)fail('PATH',`${label}: symlink entry ${name} rejected`);
  if(type&&type!==0o100000&&type!==0o040000)fail('PATH',`${label}: special file entry ${name} rejected`);
  if(method!==0&&method!==8)fail('ZIP',`${label}: compression method ${method} unsupported for ${name}`);
  if(method===0&&csize!==usize)fail('ZIP',`${label}: stored size mismatch for ${name}`);
  if(dir&&usize)fail('ZIP',`${label}: directory entry ${name} carries data`);
  if(usize>L.fileBytes)fail('LIMIT',`${label}: ${name} ${usize} bytes exceeds file limit ${L.fileBytes}`);
  if((total+=usize)>L.totalBytes)fail('LIMIT',`${label}: expanded size exceeds limit ${L.totalBytes}`);
  if(lho+30>cdOff||b.readUInt32LE(lho)!==0x04034b50)fail('ZIP',`${label}: local header for ${name} corrupt`);
  let ln=b.readUInt16LE(lho+26),start=lho+30+ln+b.readUInt16LE(lho+28),end=start+csize;
  if(end>cdOff||!b.subarray(lho+30,lho+30+ln).equals(raw))fail('ZIP',`${label}: local header for ${name} disagrees with central directory`);
  ranges.push([lho,end]);
  out.push({name,dir,exec:!!(mode&0o111),size:usize,read(){let d;
   if(method===0)d=b.subarray(start,end);else try{d=zlib.inflateRawSync(b.subarray(start,end),{maxOutputLength:Math.max(usize,1)})}catch(x){fail('ZIP',`${label}: ${name} inflate failed (${x.code==='ERR_BUFFER_TOO_LARGE'?'expands beyond declared size':x.message})`)}
   if(d.length!==usize)fail('ZIP',`${label}: ${name} size disagrees with central directory`);if(crc32(d)!==crc)fail('ZIP',`${label}: ${name} CRC mismatch`);return d}});
 }
 if(o!==e)fail('ZIP',label+': central directory size mismatch');
 ranges.sort((x,y)=>x[0]-y[0]);for(let i=1;i<ranges.length;i++)if(ranges[i][0]<ranges[i-1][1])fail('ZIP',label+': overlapping entries');
 return out;
}

// Target Python identity: probed with -I -c, or taken from a record. Explicit tags are authoritative.
const PROBE='import sys,sysconfig,json,os\ntry: g=os.confstr("CS_GNU_LIBC_VERSION")\nexcept (ValueError,OSError,AttributeError): g=None\nprint(json.dumps({"implementation":sys.implementation.name,"version":"%d.%d.%d"%sys.version_info[:3],"soabi":sysconfig.get_config_var("SOABI"),"abiflags":getattr(sys,"abiflags",""),"platform":sysconfig.get_platform(),"bits":64 if sys.maxsize>2**32 else 32,"glibc":g}))';
function probe(exe){let r=spawnSync(exe,['-I','-c',PROBE],{encoding:'utf8',timeout:30000});if(r.error||r.status!==0)fail('TARGET',`cannot probe target python ${exe}: ${r.error?.message||r.stderr||r.status}`);try{return JSON.parse(r.stdout)}catch{fail('TARGET','target python probe returned no identity: '+exe)}}
function platformsOf(t){if(!t.platform)return [];let p=t.platform.replace(/[-.]/g,'_');if(p==='linux_x86_64'&&t.bits===32)p='linux_i686';
 let m=/^linux_(.+)$/.exec(p),g=/^glibc (\d+)\.(\d+)/.exec(t.glibc||''),out=[];
 if(m&&g&&g[1]==='2'){let a=m[1],legacy=['x86_64','i686'].includes(a);for(let v=+g[2];v>=(legacy?5:17);v--){out.push(`manylinux_2_${v}_${a}`);if(v===17&&['x86_64','i686','aarch64','armv7l','ppc64','ppc64le','s390x'].includes(a))out.push('manylinux2014_'+a);if(v===12&&legacy)out.push('manylinux2010_'+a);if(v===5&&legacy)out.push('manylinux1_'+a)}}
 out.push(p);return out}
export function compatibleTags(t){
 let [maj,min]=t.version.split('.').map(Number),py=''+maj+min,cp=t.implementation==='cpython'&&!!t.abi,interp='cp'+py,abi3=cp&&!/t$/.test(t.abi),plats=t.platforms,out=[];
 const add=(...x)=>{let s=x.join('-');if(!out.includes(s))out.push(s)};
 if(cp){for(let p of plats)add(interp,t.abi,p);if(abi3)for(let p of plats)add(interp,'abi3',p);for(let p of plats)add(interp,'none',p);if(abi3)for(let m=min-1;m>=2;m--)for(let p of plats)add('cp'+maj+m,'abi3',p)}
 for(let p of plats){add('py'+py,'none',p);add('py'+maj,'none',p);for(let m=min-1;m>=0;m--)add('py'+maj+m,'none',p)}
 if(cp)add(interp,'none','any');add('py'+py,'none','any');add('py'+maj,'none','any');for(let m=min-1;m>=0;m--)add('py'+maj+m,'none','any');
 return out}
function normalize(v,label){
 if(typeof v.version!=='string'||!/^\d+\.\d+(\.\d+)?/.test(v.version))fail('TARGET',label+': target python version missing');
 let soabi=v.soabi||null,s=/^cpython-(\d+)([a-z]*)(?:-([^-]+)-([a-z]+))?/.exec(soabi||''),implementation=v.implementation||(s?'cpython':null);
 let t={identity:'plot.python/1',executable:v.executable?path.resolve(v.executable):null,implementation,version:v.version,soabi,abi:v.abi||(s?'cp'+s[1]+(v.abiflags??s[2]):null),platform:v.platform||(s&&s[3]?s[4]+'_'+s[3]:null),bits:v.bits||null,glibc:v.glibc||null};
 t.platforms=v.platforms||platformsOf(t);t.tags=Array.isArray(v.tags)&&v.tags.length?[...v.tags]:compatibleTags(t);t.explicitTags=Array.isArray(v.tags)&&v.tags.length>0;return t}
export function targetIdentity(target){
 if(typeof target==='string'){let t=path.resolve(target),j=path.basename(t)==='.plot.json'?t:fs.existsSync(path.join(t,'.plot.json'))?path.join(t,'.plot.json'):null;return j?targetIdentity(read(j)):normalize({...probe(t),executable:t},t)}
 if(!target||typeof target!=='object')fail('TARGET','target python identity required');
 if(target.identity==='plot.python/1')return target;
 if(target.schema==='plot.closure/1')return targetIdentity(target.target?.python||fail('TARGET','closure plan has no python target'));
 if(typeof target.python==='string'){let p=probe(target.python);if(Array.isArray(target.identity)&&typeof target.identity[1]==='string'&&!target.identity[1].startsWith(p.version))fail('TARGET',`runtime identity changed: recorded ${target.identity[1].split(' ')[0]}, probed ${p.version}`);return normalize({...p,executable:target.python},target.python)}
 if(target.python&&typeof target.python==='object')return targetIdentity(target.python);
 return normalize(target,'target');
}

export function parseWheelName(file){
 let base=path.basename(file),m=base.endsWith('.whl')?base.slice(0,-4).split('-'):[];
 if(m.length!==5&&m.length!==6||m.some(x=>!x)||m.length===6&&!/^\d/.test(m[2]))fail('NAME','invalid wheel filename '+base);
 let [py,abi,plat]=m.slice(-3),tags=[];for(let a of py.split('.'))for(let b of abi.split('.'))for(let c of plat.split('.'))tags.push(a+'-'+b+'-'+c);
 return {file:base,dist:m[0],version:m[1],build:m.length===6?m[2]:null,tags}}
function headers(text){let h={},last=null;for(let l of text.split(/\r?\n/)){if(!l)break;if(/^[ \t]/.test(l)&&last){let a=h[last];a[a.length-1]+='\n'+l.trim();continue}let i=l.indexOf(':');if(i<1)continue;last=l.slice(0,i).trim().toLowerCase();(h[last]||=[]).push(l.slice(i+1).trim())}return h}
function csv(text,label){let rows=[],row=[],f='',q=false,after=false;
 const end=()=>{row.push(f);f='';after=false};
 for(let i=0;i<text.length;i++){let c=text[i];
  if(q){if(c==='"'){if(text[i+1]==='"'){f+='"';i++}else{q=false;after=true}}else f+=c;continue}
  if(c===','){end();continue}if(c==='\n'||c==='\r'){if(c==='\r'&&text[i+1]==='\n')i++;end();if(row.length>1||row[0]!=='')rows.push(row);row=[];continue}
  if(after)fail('RECORD',label+': malformed RECORD quoting');if(c==='"'&&f===''){q=true;continue}f+=c}
 if(q)fail('RECORD',label+': unterminated RECORD quote');if(f!==''||row.length){end();rows.push(row)}return rows}
const field=s=>/[",\r\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;
const DIGESTS={sha224:'sha224',sha256:'sha256',sha384:'sha384',sha512:'sha512',sha3_224:'sha3-224',sha3_256:'sha3-256',sha3_384:'sha3-384',sha3_512:'sha3-512',blake2b:'blake2b512',blake2s:'blake2s256'};
function entryPoints(text,label){let out=[],sec=null;for(let raw of text.split(/\r?\n/)){let l=raw.trim();if(!l||l[0]==='#'||l[0]===';')continue;let m=/^\[([^\]]+)\]$/.exec(l);if(m){sec=m[1].trim();continue}if(sec!=='console_scripts'&&sec!=='gui_scripts')continue;
 let i=l.indexOf('='),name=l.slice(0,i).trim(),r=/^([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*:\s*([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)$/.exec(l.slice(i+1).trim().replace(/\s*\[[^\]]*\]$/,''));
 if(i<1||!/^[A-Za-z0-9][A-Za-z0-9._+-]*$/.test(name)||!r)fail('ENTRY',`${label}: invalid entry point ${JSON.stringify(l)}`);out.push({name,module:r[1],attr:r[2],gui:sec==='gui_scripts'})}return out}
// Interpreter paths with whitespace or beyond the kernel shebang limit use the sh/python polyglot trampoline.
function shebang(exe,flags){let line=exe+(flags?' '+flags:'');return /\s/.test(exe)||line.length>125?`#!/bin/sh\n'''exec' "${exe.replace(/([\\"$`])/g,'\\$1')}"${flags?' '+flags:''} "$0" "$@"\n' '''\n`:'#!'+line+'\n'}

// Every check runs before any byte is written. Tags precede reading the archive; RECORD digests
// are verified before WHEEL, METADATA or entry_points.txt are interpreted.
function inspectWheel(file,target,opts={}){
 let t=targetIdentity(target),n=parseWheelName(file),label=n.file,ranks=n.tags.map(x=>t.tags.indexOf(x)).filter(i=>i>=0);
 if(!ranks.length)fail('INCOMPATIBLE',`${label}: tags ${n.tags.join(',')} incompatible with target ${t.implementation} ${t.version} ${t.abi||'-'} ${t.platforms.join('|')||'any'}`);
 let rank=Math.min(...ranks),files=new Map();
 for(let e of readZip(file,opts.limits)){let x=clean(e.name,label);if(!e.dir){if(files.has(x))fail('PATH',`${label}: duplicate zip entry ${x}`);files.set(x,e)}}
 let infos=[...new Set([...files.keys()].map(k=>k.split('/')[0]).filter(k=>k.endsWith('.dist-info')))];
 if(infos.length!==1)fail('METADATA',`${label}: expected one .dist-info directory, found ${infos.length}`);
 let di=infos[0],stem=di.slice(0,-10),cut=stem.lastIndexOf('-');
 if(cut<1||canon(stem.slice(0,cut))!==canon(n.dist)||canon(stem.slice(cut+1))!==canon(n.version))fail('METADATA',`${label}: ${di} does not match filename`);
 const text=k=>{let e=files.get(di+'/'+k);return e?e.read().toString('utf8'):null};
 let record=di+'/RECORD',sigs=[di+'/RECORD.jws',di+'/RECORD.p7s'],listed=new Map(),unhashed=[],digests=0;
 for(let r of csv(text('RECORD')??fail('RECORD',label+': RECORD missing'),label)){if(r.length!==3)fail('RECORD',`${label}: RECORD row with ${r.length} fields`);let x=clean(r[0],label+' RECORD');if(listed.has(x))fail('RECORD',`${label}: duplicate RECORD row ${x}`);listed.set(x,{h:r[1],s:r[2]})}
 for(let [x,e] of files){if(x===record||sigs.includes(x))continue;let r=listed.get(x);
  if(!r)fail('RECORD',`${label}: ${x} not listed in RECORD`);
  if(r.s!==''&&!/^\d+$/.test(r.s))fail('RECORD',`${label}: malformed RECORD size for ${x}`);
  if(!r.h){if(!opts.allowUnhashed)fail('RECORD',`${label}: ${x} has no RECORD digest (policy requires digests; allowUnhashed accepts them)`);unhashed.push(x)}
  let d=e.read();if(r.s!==''&&+r.s!==d.length)fail('RECORD',`${label}: ${x} size ${d.length} disagrees with RECORD ${r.s}`);
  if(r.h){let i=r.h.indexOf('='),alg=r.h.slice(0,i),val=r.h.slice(i+1).replace(/=+$/,'');
   if(i<1||!/^[A-Za-z0-9_-]+$/.test(val))fail('RECORD',`${label}: malformed RECORD digest for ${x}`);
   if(alg==='md5'||alg==='sha1')fail('RECORD',`${label}: weak RECORD digest ${alg} rejected for ${x}`);
   if(!DIGESTS[alg])fail('RECORD',`${label}: unsupported RECORD digest ${alg} for ${x}`);
   if(createHash(DIGESTS[alg]).update(d).digest('base64url')!==val)fail('RECORD',`${label}: ${x} ${alg} digest mismatch`);digests++}}
 for(let x of listed.keys())if(!files.has(x)&&x!==record&&!sigs.includes(x))fail('RECORD',`${label}: RECORD lists absent file ${x}`);
 let wm=headers(text('WHEEL')??fail('METADATA',label+': WHEEL missing')),meta=headers(text('METADATA')??fail('METADATA',label+': METADATA missing'));
 let wv=wm['wheel-version']?.[0];if(!/^1\.\d+$/.test(wv||''))fail('METADATA',`${label}: Wheel-Version ${wv} unsupported`);
 let name=meta.name?.[0],version=meta.version?.[0];if(!name||canon(name)!==canon(n.dist)||canon(version)!==canon(n.version))fail('METADATA',`${label}: METADATA identity ${name} ${version} does not match filename`);
 let wtags=wm.tag||[];if(!wtags.length||wtags.some(x=>!n.tags.includes(x)))fail('METADATA',`${label}: WHEEL Tag lines disagree with filename tags`);
 let data=stem+'.data',map=[],eps=text('entry_points.txt'),entries=eps?entryPoints(eps,label):[];
 for(let [x,e] of files){if(x===record||sigs.includes(x))continue;let top=x.split('/')[0];
  if(top===data){let [,scheme,...r]=x.split('/'),rel=r.join('/');if(!rel)fail('PATH',`${label}: bare .data entry ${x}`);
   let dest={purelib:rel,platlib:rel,scripts:'bin/'+rel,data:'data/'+rel,headers:'include/'+canon(n.dist)+'/'+rel}[scheme];
   if(!dest)fail('PATH',`${label}: unknown .data scheme ${scheme}`);if(scheme==='scripts'&&r.length>1)fail('PATH',`${label}: nested script ${x}`);
   map.push({from:x,dest,script:scheme==='scripts',mode:scheme==='scripts'||e.exec?0o755:0o644,e})}
  else if(top!==di&&/\.(data|dist-info)$/.test(top))fail('METADATA',`${label}: unexpected metadata directory ${top}`);
  else map.push({from:x,dest:x,mode:e.exec?0o755:0o644,e})}
 for(let ep of entries)map.push({from:'entry_points.txt#'+ep.name,dest:'bin/'+ep.name,mode:0o755,entry:ep});
 if(!files.has(di+'/INSTALLER'))map.push({from:'generated',dest:di+'/INSTALLER',mode:0o644,content:Buffer.from('plot-assembler\n')});
 if(map.some(m=>m.script||m.entry)&&!t.executable)fail('TARGET',`${label}: scripts need a target interpreter path`);
 let summary={file:path.resolve(file),filename:label,name,version,build:n.build,tags:n.tags,selected:n.tags.find(x=>t.tags.indexOf(x)===rank),rank,purelib:/^true$/i.test(wm['root-is-purelib']?.[0]||''),distInfo:di,
  files:files.size,bytes:[...files.values()].reduce((a,e)=>a+e.size,0),digests,unhashed,signatures:sigs.filter(x=>files.has(x)).map(x=>({file:x,state:'present-unverified',installed:false})),
  entrypoints:entries.map(e=>({name:e.name,value:e.module+':'+e.attr,gui:e.gui})),scripts:map.filter(m=>m.script).map(m=>m.dest),sha256:sha256(fs.readFileSync(file))};
 return {summary,map,record,target:t};
}
export function verifyWheel(file,target,opts={}){return inspectWheel(file,target,opts).summary}

function destinations(items){let seen=new Map(),dirs=new Set();
 for(let it of items){let d=clean(it.dest,'destination');if(d==='.plot.json'||d==='.plot-assembly.json')fail('PATH','reserved destination '+d);if(seen.has(d))fail('PATH',`duplicate destination ${d} (${seen.get(d)} and ${it.origin})`);seen.set(d,it.origin);let a=d.split('/');for(let i=1;i<a.length;i++)dirs.add(a.slice(0,i).join('/'))}
 for(let d of seen.keys())if(dirs.has(d))fail('PATH',`destination ${d} is both a file and a directory`)}
function writeTree(stage,files){let made=new Set([stage]),written=new Map();
 for(let f of files){let x=path.join(stage,...f.dest.split('/')),cur=stage;
  for(let c of path.relative(stage,path.dirname(x)).split(path.sep).filter(Boolean)){cur=path.join(cur,c);if(made.has(cur))continue;try{fs.mkdirSync(cur,{mode:0o700})}catch(e){if(e.code!=='EEXIST')throw e}if(!fs.lstatSync(cur).isDirectory())fail('PATH','stage path is not a directory: '+cur);made.add(cur)}
  let data=typeof f.data==='function'?f.data(written):f.data,fd=fs.openSync(x,'wx',f.mode);try{fs.writeFileSync(fd,data);fs.fsyncSync(fd)}finally{fs.closeSync(fd)}fs.chmodSync(x,f.mode);written.set(f.dest,data)}
 for(let d of [...made].sort((a,b)=>b.length-a.length))syncDir(d);return written}
function wheelFiles(w,t){let s=w.summary,exe=t.executable,out=[];
 for(let m of w.map){let origin=s.filename+':'+m.from,data;
  if(m.entry)data=Buffer.from(shebang(exe,'-IS')+`import os,sys\nsys.path.insert(0,os.path.dirname(os.path.dirname(os.path.realpath(__file__))))\nfrom ${m.entry.module} import ${m.entry.attr.split('.')[0]}\nif __name__=='__main__':\n    sys.argv[0]=os.path.basename(sys.argv[0])\n    sys.exit(${m.entry.attr}())\n`);
  else if(m.content)data=m.content;
  else if(m.script)data=()=>{let b=m.e.read(),nl=b.indexOf(10),line=(nl<0?b:b.subarray(0,nl)).toString('utf8').replace(/\r$/,''),r=/^#!pythonw?(.*)$/.exec(line);return r?Buffer.concat([Buffer.from(shebang(exe,r[1].trim())),nl<0?Buffer.alloc(0):b.subarray(nl+1)]):b};
  else data=()=>m.e.read();
  out.push({dest:m.dest,mode:m.mode,data,origin})}
 // The installed RECORD lists installed paths and the digests of the bytes actually written.
 out.push({dest:w.record,mode:0o644,origin:s.filename+':RECORD',data:written=>Buffer.from(out.filter(f=>f.dest!==w.record).map(f=>{let d=written.get(f.dest);return `${field(f.dest)},sha256=${createHash('sha256').update(d).digest('base64url')},${d.length}\n`}).join('')+field(w.record)+',,\n')});
 return out}

function untgz(file,L,label,member){let raw=fs.readFileSync(file),b;if(raw.length>L.archiveBytes)fail('LIMIT',label+': archive exceeds limit');
 try{b=zlib.gunzipSync(raw,{maxOutputLength:Math.max(L.totalBytes,1)})}catch(e){fail(e.code==='ERR_BUFFER_TOO_LARGE'?'LIMIT':'ZIP',`${label}: gzip ${e.code==='ERR_BUFFER_TOO_LARGE'?'expands beyond limit':e.message}`)}
 const str=(h,a,n)=>h.subarray(a,a+n).toString().split('\0')[0],oct=(h,a,n)=>{let s=str(h,a,n);if(!/^[\s\0]*[0-7]*[\s\0]*$/.test(s))fail('ZIP',label+': tar number');return parseInt(s.trim(),8)||0};
 let pre=member?clean(member,label)+'/':null,off=0,out=[],pax=null,long=null,top=null,total=0;
 while(off+512<=b.length){let h=b.subarray(off,off+512);if(h.every(v=>!v))break;let sum=0;for(let i=0;i<512;i++)sum+=i>=148&&i<156?32:h[i];if(sum!==oct(h,148,8))fail('ZIP',label+': tar checksum');
  let size=oct(h,124,12),type=String.fromCharCode(h[156]),start=off+512;off=start+Math.ceil(size/512)*512;if(off>b.length)fail('ZIP',label+': truncated tar');let body=b.subarray(start,start+size);
  if(type==='x'){pax={};let s=body.toString('utf8'),i=0;while(i<s.length){let sp=s.indexOf(' ',i),len=parseInt(s.slice(i,sp),10);if(!(len>0))fail('ZIP',label+': pax record');let rec=s.slice(sp+1,i+len-1),eq=rec.indexOf('=');pax[rec.slice(0,eq)]=rec.slice(eq+1);i+=len}if(pax.size)fail('ZIP',label+': pax size override unsupported');continue}
  if(type==='g')continue;if(type==='L'){long=body.toString('utf8').replace(/\0+$/,'');continue}
  let name=pax?.path??long??[str(h,345,155),str(h,0,100)].filter(Boolean).join('/');pax=long=null;if(type==='5')continue;
  if(!['0','\0','7'].includes(type))fail('PATH',`${label}: tar entry type ${JSON.stringify(type)} rejected: ${name}`);
  let x=clean(name,label),rel;
  // A member selects one package inside the archive (contracts v1.3 source.member), e.g. a bundled dependency.
  if(pre){if(!x.startsWith(pre))continue;rel=x.slice(pre.length)}else{let parts=x.split('/');if(parts.length<2||(top??=parts[0])!==parts[0])fail('PATH',`${label}: tar entry outside package root: ${name}`);rel=parts.slice(1).join('/')}
  if(rel.split('/')[0]==='node_modules')continue;
  if(out.length>=L.entries)fail('LIMIT',label+': entry limit');if(size>L.fileBytes||(total+=size)>L.totalBytes)fail('LIMIT',label+': size limit');
  out.push({rel,mode:oct(h,100,8)&0o111?0o755:0o644,data:body})}
 return out}
function walk(dir,L,label,skip){let out=[],total=0;(function rec(d,rel){for(let e of fs.readdirSync(d,{withFileTypes:true}).sort((a,b)=>a.name<b.name?-1:1)){let r=rel?rel+'/'+e.name:e.name,x=path.join(d,e.name);if(!rel&&skip.includes(e.name))continue;
  if(e.isSymbolicLink())fail('PATH',`${label}: symlink in source rejected: ${r}`);if(e.isDirectory()){rec(x,r);continue}if(!e.isFile())fail('PATH',`${label}: special file rejected: ${r}`);
  let st=fs.statSync(x);if(out.length>=L.entries)fail('LIMIT',label+': entry limit');if(st.size>L.fileBytes||(total+=st.size)>L.totalBytes)fail('LIMIT',label+': size limit');out.push({rel:r,mode:st.mode&0o111?0o755:0o644,data:()=>fs.readFileSync(x)})}})(dir,'');return out}
function integrity(file,spec,label){if(!spec)return null;let m=/^(sha256|sha384|sha512)-([A-Za-z0-9+/]+={0,2})$/.exec(spec);if(!m)fail('INTEGRITY',`${label}: unsupported integrity ${spec}`);if(createHash(m[1]).update(fs.readFileSync(file)).digest('base64')!==m[2])fail('INTEGRITY',`${label}: integrity mismatch`);return spec}
const placementRe=/^node_modules\/(?:@[a-z0-9][\w.~-]*\/)?[a-z0-9_.~][\w.~-]*(?:\/node_modules\/(?:@[a-z0-9][\w.~-]*\/)?[a-z0-9_.~][\w.~-]*)*$/i;
const sourceFiles=(src,L,label)=>src.kind==='tgz'?untgz(src.path,L,label,src.member):walk(src.path,L,label,src.kind==='object'?['.plot.json','node_modules']:['node_modules','.git']);
// Content digest of package files, independent of container (dir, tgz member or component object).
function digestFiles(files){let h=createHash('sha256');for(let f of [...files].sort((a,b)=>a.dest<b.dest?-1:1)){let d=typeof f.data==='function'?f.data():f.data;h.update(`${f.dest}\0${f.mode.toString(8)}\0${sha256(d)}\n`)}return h.digest('hex')}
function npmFiles(n,src,L,prefix){let node=n.node,label=node.id;if(src.kind==='tgz')integrity(src.path,n.integrity,label);let files=sourceFiles(src,L,label);
 let pj=files.find(f=>f.rel==='package.json');let m=pj&&JSON.parse((typeof pj.data==='function'?pj.data():pj.data).toString('utf8'));
 if(!m||m.name!==node.name||m.version!==node.version)fail('METADATA',`${label}: package.json identity ${m?.name}@${m?.version} does not match plan`);
 return files.map(f=>({dest:(prefix?prefix+'/':'')+f.rel,mode:f.mode,data:f.data,origin:label+':'+f.rel}))}

// Publication: L1 (.grave/.lock) held for reuse scan, staging and stamping; stale lock reclaimed under L0.
function lock(grave){let l=path.join(grave,'.lock'),rec=path.join(grave,'.recovery'),busy=m=>fail('BUSY',m,{retryable:true});
 const take=()=>{if(fs.existsSync(rec))busy('busy: recovery in progress; inspect '+rec);fs.mkdirSync(l,{mode:0o700})};
 try{take()}catch(e){if(e.code!=='EEXIST')throw e;let o;try{o=read(path.join(l,'owner.json'))}catch{busy('busy or incomplete lock; inspect '+l)}
  let s=identity(o);if(!['absent','other'].includes(s))busy(`busy: ${l} held by pid ${o.pid} (${s})`);
  try{fs.mkdirSync(rec,{mode:0o700})}catch(x){if(x.code==='EEXIST')busy('busy: recovery in progress');throw x}
  try{let again;try{again=read(path.join(l,'owner.json'))}catch{busy('lock changed during recovery')}if(stable(again)!==stable(o))busy('lock changed during recovery');let into=directory(path.join(grave,'interrupted'));fs.renameSync(l,path.join(into,'acquisition-'+randomUUID()));syncDir(grave);syncDir(into)}finally{fs.rmdirSync(rec)}
  take()}
 let stages=[],stamp=()=>atom(path.join(l,'owner.json'),{pid:process.pid,birth:birth(process.pid),writer:'assembler',stages});stamp();
 return {stage(s){stages.push(s);stamp()},release(){fs.rmSync(path.join(l,'owner.json'),{force:true});fs.rmdirSync(l)}}}
const tombstoned=(grave,x)=>{let t=path.join(grave,'tombstones',path.basename(x));return fs.existsSync(t+'.json')||fs.existsSync(t)};
function historical(grave,objects,id,key){if(!fs.existsSync(objects))return null;for(let n of fs.readdirSync(objects).sort()){if(!n.startsWith(id+'-'))continue;let x=path.join(objects,n);try{let v=read(path.join(x,'.plot.json'));if(v.key===key&&v.path===fs.realpathSync(x)&&inside(objects,v.path)&&!tombstoned(grave,x))return v}catch{}}return null}
function objectOf(objects,x){let r;try{r=path.join(fs.realpathSync(path.dirname(x)),path.basename(x))}catch{return null}if(!inside(objects,r))return null;return path.join(objects,path.relative(objects,r).split(path.sep)[0])}
function closure(objects,tops){let seen=new Set(),todo=[...tops];while(todo.length){let x=todo.pop();if(seen.has(x))continue;seen.add(x);try{for(let d of JSON.parse(read(path.join(x,'.plot.json')).key)[2]||[])if(typeof d==='string'&&inside(objects,d))todo.push(path.join(objects,path.relative(objects,d).split(path.sep)[0]))}catch{}}return [...seen].sort()}
// Pin-then-validate (contracts §4): the pin exists before any consumed object is read.
function pin(root,id,paths){if(!paths.length)return ()=>{};let grave=path.join(root,'.grave'),objects=path.join(grave,'objects'),dir=directory(path.join(grave,'pins')),file=path.join(dir,`acquisition-${id}-${randomBytes(6).toString('hex')}.json`);
 once(file,{schema:1,kind:'acquisition',owner:{pid:process.pid,birth:birth(process.pid)},ref:id,paths,created:new Date().toISOString()});
 const release=()=>{fs.rmSync(file,{force:true});syncDir(dir)};
 for(let x of paths){let ok=false;try{ok=path.dirname(x)===objects&&fs.realpathSync(x)===x&&read(path.join(x,'.plot.json')).path===x&&!tombstoned(grave,x)}catch{}if(!ok){release();fail('PIN','consumed object unavailable or tombstoned: '+x,{retryable:true})}}
 return release}
// Reuse of a historical object re-verifies its recorded input digests: changed bank bytes under an
// unchanged name refuse with BANK_CHANGED instead of returning a layer built from other bytes.
function publish({root,id,key,consumed,prepare,meta,inputs=()=>[]}){
 let grave=path.join(root,'.grave'),objects=path.join(grave,'objects'),memo,current=()=>memo??=inputs(),unpin=pin(root,id,closure(objects,consumed));
 const reuse=v=>{let now=new Map(current().map(x=>[x.ref,x.sha256])),was=new Map((Array.isArray(v.inputs)?v.inputs:[]).map(x=>[x.ref,x.sha256])),changed=[];
  for(let ref of new Set([...now.keys(),...was.keys()]))if(now.get(ref)!==was.get(ref))changed.push({ref,recorded:was.get(ref)??null,current:now.get(ref)??null});
  if(!Array.isArray(v.inputs))changed.push({ref:'.plot.json#inputs',recorded:null,current:null});
  if(changed.length)fail('BANK_CHANGED',`bank material changed since ${v.path} was published: ${changed.map(c=>c.ref).join(', ')}`,{object:v.path,changed});return {...v,reused:true}};
 try{let hit=historical(grave,objects,id,key);if(hit)return reuse(hit);
  let files=prepare();destinations(files);directory(objects);let L1=lock(grave),stage=null;
  try{let again=historical(grave,objects,id,key);if(again)return reuse(again);
   stage=fs.mkdtempSync(path.join(objects,id+'-'));L1.stage(stage);syncDir(objects);writeTree(stage,files);
   if(process.env.PLOT_ASSEMBLER_CRASH==='staged')process.kill(process.pid,'SIGKILL');
   let real=fs.realpathSync(stage),v={key,path:real,kind:'layer',assembler:1,inputs:current(),...meta(real)};atom(path.join(stage,'.plot.json'),v);stage=null;return {...v,reused:false}}
  finally{if(stage)fs.rmSync(stage,{recursive:true,force:true});L1.release()}}
 finally{unpin()}}
function targetMeta(t){return {implementation:t.implementation,version:t.version,abi:t.abi,soabi:t.soabi,platforms:t.platforms,executable:t.executable,...(t.explicitTags?{tags:t.tags}:{})}}
function layerMeta(stage,wheels,npm,t,components){let bin=path.join(stage,'bin');return {site:stage,bin:fs.existsSync(bin)?bin:null,target:t?targetMeta(t):null,
 wheels:wheels.map(w=>({file:w.summary.filename,name:w.summary.name,version:w.summary.version,tag:w.summary.selected,sha256:w.summary.sha256,files:w.summary.files,entrypoints:w.summary.entrypoints.map(e=>e.name),unhashed:w.summary.unhashed.length,signatures:w.summary.signatures.map(x=>x.file)})),
 npm:npm.map(n=>({id:n.node.id,name:n.node.name,version:n.node.version,placement:n.node.placement,source:n.src.kind,integrity:n.integrity,component:components?.get(nv(n))??null})),created:new Date().toISOString()}}
function compose(o,t,wheels,npm){let files=[];for(let w of wheels())files.push(...wheelFiles(w,t));for(let n of npm())files.push(...npmFiles(n,n.use||n.src,o.L,n.node.placement));return files}
function runtimeOf(objects,t){return t?.executable?objectOf(objects,t.executable):null}
const nv=n=>n.node.name+'@'+n.node.version;
const wheelInputs=files=>()=>files.map(f=>({ref:'wheel:'+path.basename(f),sha256:sha256(fs.readFileSync(f))}));

export function installWheels({root,wheels,target,id,limits,allowUnhashed=false}){
 validId(id);if(!Array.isArray(wheels)||!wheels.length)fail('USAGE','wheels required');root=fs.realpathSync(root);
 let t=targetIdentity(target),objects=path.join(root,'.grave','objects'),L=limitsOf(limits),names=wheels.map(w=>parseWheelName(w));
 for(let n of names)if(!n.tags.some(x=>t.tags.includes(x)))fail('INCOMPATIBLE',`${n.file}: tags ${n.tags.join(',')} incompatible with target ${t.implementation} ${t.version} ${t.abi||'-'}`);
 let dup=names.map(n=>canon(n.dist)).find((x,i,a)=>a.indexOf(x)!==i);if(dup)fail('CONFLICT','one layer cannot hold two versions of '+dup);
 let rt=runtimeOf(objects,t),key=stable([{assembler:1,wheels:names.map(n=>n.file),target:targetMeta(t),allowUnhashed:!!allowUnhashed},sig(),rt?[rt]:[]]),verified;
 let consumed=[...new Set([rt,...wheels.map(w=>objectOf(objects,path.resolve(w)))].filter(Boolean))];
 return publish({root,id,key,consumed,inputs:wheelInputs(wheels),prepare:()=>compose({L},t,()=>verified=wheels.map(w=>inspectWheel(w,t,{limits:L,allowUnhashed})),()=>[]),meta:s=>layerMeta(s,verified,[],t)})}

const REQ=/^([A-Za-z0-9][A-Za-z0-9._-]*)\s*==\s*([A-Za-z0-9._+!-]+)$/;
function bankWheels(bank,bad){let out=[];(function rec(d,depth){if(depth>4)return;for(let e of fs.readdirSync(d,{withFileTypes:true}).sort((a,b)=>a.name<b.name?-1:1)){let x=path.join(d,e.name);if(e.isDirectory())rec(x,depth+1);else if(e.isFile()&&e.name.endsWith('.whl')){try{out.push({path:x,...parseWheelName(x)})}catch(err){bad?.push({where:x,form:'filename',reason:err.message})}}if(out.length>100000)fail('LIMIT','bank wheel index limit')}})(bank,0);return out}
function pick(index,name,version,t,bank){let all=index.filter(w=>canon(w.dist)===canon(name)&&canon(w.version)===canon(version)),ok=all.map(w=>({w,r:Math.min(...w.tags.map(x=>t.tags.indexOf(x)).filter(i=>i>=0))})).filter(x=>isFinite(x.r)).sort((a,b)=>a.r-b.r||(a.w.file<b.w.file?-1:1));
 if(!ok.length){let requirement={kind:'wheel',name,version,reason:all.length?'no compatible wheel in bank':'not in bank',bank,candidates:all.map(w=>w.file),target:targetMeta(t),sourceBuild:false};fail('ACQUISITION_REQUIRED',`acquisition required: ${name}==${version} (${requirement.reason})`,{requirement})}
 return ok[0].w.path}
function resolveBank({root,bank,plan,target,limits}){
 bank=fs.realpathSync(bank);if(!fs.statSync(bank).isDirectory())fail('USAGE','bank must be a directory');
 let grave=path.join(root,'.grave'),objects=path.join(grave,'objects');
 if(within(bank,grave)||within(grave,bank)&&!objectOf(objects,bank))fail('USAGE','bank must not contain the plot .grave nor live in it outside .grave/objects; bank material is immutable');
 if(typeof plan==='string')plan=read(path.resolve(plan));if(!plan||typeof plan!=='object')fail('PLAN','plan required');
 let L=limitsOf(limits),wheelSel=[],npm=[],closurePlan=plan.schema==='plot.closure/1',index=null,t=null;
 const python=()=>t??=targetIdentity(target??(closurePlan&&plan.target?.python)??fail('TARGET','wheel nodes need a target python identity'));
 const inBank=(p,label)=>{let r=fs.realpathSync(p);if(!within(bank,r))fail('PLAN',`${label}: source outside bank: ${p}`);return r};
 if(closurePlan){
  if(plan.ok!==true)fail('PLAN','closure plan is not ok; refusing to assemble',{diagnostics:plan.diagnostics||[]});
  if(plan.target&&(plan.target.platform!==process.platform||plan.target.arch!==process.arch))fail('PLAN',`closure target ${plan.target.platform}/${plan.target.arch} is not this host ${process.platform}/${process.arch}`);
  if(target&&plan.target?.python){let a=python(),b=targetIdentity(plan.target.python);if(a.version!==b.version||a.soabi!==b.soabi)fail('TARGET',`target ${a.version} ${a.soabi} disagrees with closure python ${b.version} ${b.soabi}`)}
  let byId=new Map((plan.nodes||[]).map(n=>[n.id,n])),order=plan.order?.length?plan.order:[...byId.keys()];
  for(let k of order){let n=byId.get(k)??fail('PLAN','order names unknown node '+k),s=n.source||{};
   if(n.ecosystem==='wheel'){let file=s.kind==='whl'?inBank(s.path,n.id):s.kind==='bank'||!s.kind?pick(index??=bankWheels(bank),n.name,n.version,python(),bank):fail('PLAN',`${n.id}: wheel source kind ${s.kind} unsupported`);wheelSel.push({file,integrity:s.integrity||null,id:n.id})}
   else if(n.ecosystem==='npm'){if(typeof n.placement!=='string'||!placementRe.test(n.placement))fail('PLAN',`${n.id}: invalid placement ${n.placement}`);clean(n.placement,n.id);
    if(s.kind!=='dir'&&s.kind!=='tgz')fail('PLAN',`${n.id}: npm source kind ${s.kind} unsupported`);let p=inBank(s.path,n.id),st=fs.statSync(p);if(s.kind==='dir'?!st.isDirectory():!st.isFile())fail('PLAN',`${n.id}: source is not a ${s.kind}`);
    if(s.kind==='dir'&&s.integrity)fail('INTEGRITY',`${n.id}: integrity for a directory source is not verifiable`);if(s.member!=null&&(s.kind!=='tgz'||typeof s.member!=='string'))fail('PLAN',`${n.id}: member applies only to tgz sources`);
    npm.push({node:n,src:{kind:s.kind,path:p,...(s.member?{member:s.member}:{})},integrity:s.integrity||null})}
   else fail('PLAN',`${n.id}: ecosystem ${n.ecosystem} unsupported by the assembler`)}}
 else{let reqs=Array.isArray(plan)?plan:plan.packages||plan.wheels||fail('PLAN','plan needs packages, wheels, or schema plot.closure/1');
  for(let r of reqs){if(typeof r!=='string')fail('PLAN','requirement must be a string');let m=REQ.exec(r.trim());
   if(m)wheelSel.push({file:pick(index??=bankWheels(bank),m[1],m[2],python(),bank),integrity:null,id:r});else if(r.endsWith('.whl'))wheelSel.push({file:inBank(path.join(bank,r),r),integrity:null,id:r});else fail('PLAN',`unsupported requirement ${JSON.stringify(r)}: exact name==version pins or bank wheel filenames only`)}}
 if(wheelSel.length)python();
 let names=wheelSel.map(w=>parseWheelName(w.file));for(let n of names)if(!n.tags.some(x=>t.tags.includes(x)))fail('INCOMPATIBLE',`${n.file}: tags ${n.tags.join(',')} incompatible with target ${t.implementation} ${t.version} ${t.abi||'-'}`);
 let dup=names.map(n=>canon(n.dist)).find((x,i,a)=>a.indexOf(x)!==i);if(dup)fail('CONFLICT','one layer cannot hold two versions of '+dup);
 return {root,bank,objects,L,t,wheelSel,names,npm,rt:runtimeOf(objects,t),bankObj:objectOf(objects,bank)}}
function layerJob(r,id,allowUnhashed,components){
 let comps=components?[...new Set(components.values())].sort():[],verified=[];
 let key=stable([{assembler:1,wheels:r.names.map(n=>n.file),npm:r.npm.map(n=>components?[n.node.id,n.node.placement]:[n.node.id,n.node.placement,n.src.kind,path.basename(n.src.path),n.src.member||null]),target:r.t?targetMeta(r.t):null,allowUnhashed:!!allowUnhashed},sig(),[...(r.rt?[r.rt]:[]),...comps]]);
 let prepare=()=>compose({L:r.L},r.t,()=>verified=r.verified??r.wheelSel.map(w=>{integrity(w.file,w.integrity,w.id);return inspectWheel(w.file,r.t,{limits:r.L,allowUnhashed})}),()=>r.npm.map(n=>components?{...n,use:{kind:'object',path:components.get(nv(n))}}:n));
 return {root:r.root,id,key,consumed:[...new Set([r.rt,r.bankObj,...comps].filter(Boolean))],prepare,inputs:wheelInputs(r.wheelSel.map(w=>w.file)),meta:s=>layerMeta(s,verified,r.npm,r.t,components)}}
// Contracts v1.3 presence: one complete object per distinct npm name@version, keyed by
// {component:{ecosystem:'npm',name,version}}, so the cartographer can mark it present. Layers
// compose copies of these objects and name them as key dependencies.
const compId=name=>('npm-'+name.replace(/^@/,'').replace(/[^A-Za-z0-9_-]/g,'_')).slice(0,57);
function componentOf(r,n,digest){let {name,version}=n.node,key=stable([{component:{ecosystem:'npm',name,version},assembler:1},sig(),[]]);
 return publish({root:r.root,id:compId(name),key,consumed:r.bankObj?[r.bankObj]:[],inputs:()=>[{ref:'npm:'+name+'@'+version,sha256:digest}],prepare:()=>npmFiles(n,n.src,r.L,''),
  meta:()=>({kind:'component',component:{ecosystem:'npm',name,version},source:{kind:n.src.kind,file:path.basename(n.src.path),member:n.src.member||null,integrity:n.integrity}})}).path}
export function assembleFromBank({root,bank,plan,target,id='assembled',limits,allowUnhashed=false}){
 validId(id);root=fs.realpathSync(root);let r=resolveBank({root,bank,plan,target,limits}),comps=new Map(),digests=new Map(),unpin=pin(root,id,closure(r.objects,[r.rt,r.bankObj].filter(Boolean)));
 // Every wheel and npm source is verified before the first component object is published.
 try{r.verified=r.wheelSel.map(w=>{integrity(w.file,w.integrity,w.id);return inspectWheel(w.file,r.t,{limits:r.L,allowUnhashed})});
  let firsts=[];for(let n of r.npm){let k=nv(n),d=digestFiles(npmFiles(n,n.src,r.L,''));if(digests.has(k)){if(digests.get(k)!==d)fail('CONFLICT',`${k} appears with differing content in one plan (${n.node.id})`);continue}digests.set(k,d);firsts.push(n)}
  if(r.npm.length||r.wheelSel.length)destinations([...r.verified.flatMap(w=>wheelFiles(w,r.t)),...r.npm.flatMap(n=>npmFiles(n,n.src,r.L,n.node.placement))]);
  for(let n of firsts)comps.set(nv(n),componentOf(r,n,digests.get(nv(n))));
  return publish(layerJob(r,id,allowUnhashed,comps))}finally{unpin()}}

// Seed-recipe mode: fill the seed's own stage. The seed holds L1 and writes .plot.json, so no component
// objects are published here; npm content is copied straight from the bank. Consumed objects are pinned.
export function assembleInto({into,bank,plan,target,id='layer',limits,allowUnhashed=false}){
 into=fs.realpathSync(into);if(!fs.statSync(into).isDirectory()||fs.readdirSync(into).length)fail('USAGE','target directory must be an existing empty directory: '+into);validId(id);
 let objects=path.dirname(into),root=path.basename(objects)==='objects'&&path.basename(path.dirname(objects))==='.grave'?path.dirname(path.dirname(objects)):path.dirname(into);
 let job=layerJob(resolveBank({root,bank,plan,target,limits}),id,allowUnhashed,null),unpin=pin(root,id,closure(objects,job.consumed));
 try{let files=job.prepare();destinations(files);writeTree(into,files);let v={kind:'layer',assembler:1,inputs:job.inputs(),...job.meta(into)};atom(path.join(into,'.plot-assembly.json'),v);return v}finally{unpin()}}

// PEP 440 subset: release segments, a|b|rc pre, post, dev; local labels ignored in ordering.
function pyver(s){let m=/^v?(\d+(?:\.\d+)*)(?:[-_.]?(a|b|c|rc|alpha|beta|pre|preview)[-_.]?(\d*))?(?:[-_.]?(post|rev|r)[-_.]?(\d*)|-(\d+))?(?:[-_.]?dev[-_.]?(\d*))?(?:\+[a-z0-9]+(?:[-_.][a-z0-9]+)*)?$/i.exec(String(s).trim());
 if(!m)return null;let pre=m[2]&&{a:'a',alpha:'a',b:'b',beta:'b',c:'rc',rc:'rc',pre:'rc',preview:'rc'}[m[2].toLowerCase()];
 return {release:m[1].split('.').map(Number),pre:pre?[{a:0,b:1,rc:2}[pre],+(m[3]||0)]:null,post:m[4]||m[6]!==undefined?+(m[5]||m[6]||0):null,dev:m[7]!==undefined?+(m[7]||0):null}}
function cmpv(a,b){for(let i=0;i<Math.max(a.release.length,b.release.length);i++){let d=(a.release[i]||0)-(b.release[i]||0);if(d)return d}
 const pk=v=>v.pre||(v.dev!==null&&v.post===null?[-1,0]:[3,0]);let x=pk(a),y=pk(b);if(x[0]!==y[0])return x[0]-y[0];if(x[1]!==y[1])return x[1]-y[1];
 let p=(a.post??-1)-(b.post??-1);if(p)return p;return (a.dev??Infinity)-(b.dev??Infinity)||0}
const isPre=v=>!!(v.pre||v.dev!==null);
// name, name==X, and comma-joined == != >= <= > < comparators. Extras, markers, ~=, === and wildcards are unsupported.
function specifier(text){let s=text.trim().replace(/^\((.*)\)$/,'$1').trim();if(!s)return [];let out=[];
 for(let part of s.split(',')){let m=/^(==|!=|>=|<=|>|<)\s*([^\s,*]+)$/.exec(part.trim()),v=m&&pyver(m[2]);if(!v)return null;out.push({op:m[1],v})}return out}
function matches(v,spec){return spec.every(({op,v:w})=>{let c=cmpv(v,w);return op==='=='?c===0:op==='!='?c!==0:op==='>='?c>=0:op==='<='?c<=0:op==='>'?c>0:c<0})&&(!isPre(v)||spec.some(x=>isPre(x.v)))}
function requirement(raw){let m=/^\s*([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)\s*([^;]*?)\s*(?:;\s*(.*))?$/.exec(raw);if(!m)return null;let spec=m[2].startsWith('[')?null:specifier(m[2]);return spec?{name:m[1],spec,marker:m[3]?.trim()||null,raw:raw.trim()}:null}
export function planWheels({bank,target,requirements,limits}){
 if(!Array.isArray(requirements)||!requirements.length||!requirements.every(x=>typeof x==='string'&&x.trim()))fail('USAGE','requirements must be a non-empty array of strings');
 bank=fs.realpathSync(bank);let t=targetIdentity(target),L=limitsOf(limits),unsupported=[],diagnostics=[],nodes=new Map(),byName=new Map(),index=bankWheels(bank,unsupported),queue=[];
 for(let raw of requirements){let r=requirement(raw);if(!r||r.marker){unsupported.push({where:'requested',form:raw,reason:'supported: name, name==X, comparators == != >= <= > < joined by commas; no extras, markers, ~=, === or wildcards'});diagnostics.push({code:'range-unsatisfied',detail:`unsupported requirement ${raw}`})}else queue.push({r,from:null})}
 while(queue.length){let {r,from}=queue.shift(),cn=canon(r.name),dep=from&&{kind:'prod',name:r.name,range:r.raw.replace(/^\s*[A-Za-z0-9._-]+\s*/,'')||'*',resolved:null};if(dep)from.deps.push(dep);
  let have=byName.get(cn);if(have){if(matches(have.v,r.spec)){if(dep)dep.resolved=have.node.id}else diagnostics.push({code:'range-unsatisfied',detail:`${r.raw}${from?' (from '+from.id+')':''} conflicts with selected ${have.node.id}`});continue}
  let all=index.filter(w=>canon(w.dist)===cn).map(w=>({w,v:pyver(w.version)})),fits=all.filter(x=>x.v&&matches(x.v,r.spec)),compat=fits.map(x=>({...x,rank:Math.min(...x.w.tags.map(y=>t.tags.indexOf(y)).filter(i=>i>=0))})).filter(x=>isFinite(x.rank));
  if(!compat.length){diagnostics.push({code:all.length&&!fits.length?'range-unsatisfied':'missing',detail:`${r.raw}${from?' (from '+from.id+')':''}: ${!all.length?'not in bank':!fits.length?'no bank version satisfies; versions '+[...new Set(all.map(x=>x.w.version))].join(', '):'no wheel compatible with target '+t.version+' '+(t.abi||'-')+'; candidates '+fits.map(x=>x.w.file).join(', ')}`});continue}
  compat.sort((a,b)=>cmpv(b.v,a.v)||a.rank-b.rank||(a.w.file<b.w.file?-1:1));let best=compat[0],meta,eps=[];
  try{let zip=readZip(best.w.path,L),infos=zip.filter(e=>!e.dir&&/^[^/]+\.dist-info\/METADATA$/.test(e.name));if(infos.length!==1)fail('METADATA','expected one .dist-info/METADATA');meta=headers(infos[0].read().toString('utf8'));let ep=zip.find(e=>e.name===infos[0].name.replace(/METADATA$/,'entry_points.txt'));if(ep)eps=entryPoints(ep.read().toString('utf8'),best.w.file)}
  catch(e){diagnostics.push({code:'missing',detail:`${best.w.file}: unreadable wheel (${e.message})`});continue}
  let name=meta.name?.[0]||best.w.dist,version=meta.version?.[0]||best.w.version;
  if(canon(name)!==cn||canon(version)!==canon(best.w.version)){diagnostics.push({code:'missing',detail:`${best.w.file}: METADATA identity ${name} ${version} does not match filename`});continue}
  let node={id:name+'@'+version,ecosystem:'wheel',name,version,source:{kind:'whl',path:best.w.path,integrity:'sha256-'+createHash('sha256').update(fs.readFileSync(best.w.path)).digest('base64')},placement:'.',deps:[],
   entry:{main:null,exports:null,bin:Object.fromEntries(eps.map(e=>[e.name,'bin/'+e.name]))},present:{object:null,key:null}};
  nodes.set(node.id,node);byName.set(cn,{node,v:best.v});if(dep)dep.resolved=node.id;
  for(let d of meta['requires-dist']||[]){let q=requirement(d);
   if(q?.marker&&/^extra\s*==\s*(['"])[^'"]+\1$/.test(q.marker))continue;
   if(!q||q.marker){unsupported.push({where:node.id+'#Requires-Dist',form:d,reason:q?'environment markers are not evaluated':'unsupported requirement form'});continue}
   queue.push({r:q,from:node})}}
 let order=[],done=new Set(),list=[...nodes.values()].sort((a,b)=>a.id<b.id?-1:1);
 while(order.length<list.length){let next=list.find(n=>!done.has(n.id)&&n.deps.every(d=>!d.resolved||done.has(d.resolved)||d.resolved===n.id));if(!next)break;done.add(next.id);order.push(next.id)}
 if(order.length<list.length){diagnostics.push({code:'cycle',detail:'Requires-Dist cycle among '+list.filter(n=>!done.has(n.id)).map(n=>n.id).join(', ')});for(let n of list)if(!done.has(n.id))order.push(n.id)}
 for(let n of list)n.deps.sort((a,b)=>a.name<b.name?-1:1);
 let plan={schema:'plot.closure/1',target:{platform:process.platform,arch:process.arch,libc:/^glibc/.test(t.glibc||'')?'glibc':null,node:null,conditions:[],python:{version:t.version,soabi:t.soabi,tags:t.tags}},
  requested:requirements,nodes:list,order,pruned:[],unsupported,diagnostics,ok:!diagnostics.some(d=>['cycle','missing','range-unsatisfied','peer-unsatisfied'].includes(d.code))};
 return JSON.parse(stable(plan))}

async function cli(a){let o={_:[]};for(let i=0;i<a.length;i++){let k=a[i];if(k==='--allow-unhashed')o.allowUnhashed=true;else if(k.startsWith('--')){if(i+1>=a.length)fail('USAGE','missing value for '+k);o[k.slice(2)]=a[++i]}else o._.push(k)}
 let cmd=o._.shift(),json=s=>s&&(/^\s*[[{]/.test(s)?JSON.parse(s):read(path.resolve(s))),target=o.python||json(o.target),limits=json(o.limits),r;
 if(cmd==='plan-wheels'){let plan=planWheels({bank:o.bank||fail('USAGE','--bank required'),target,requirements:o._,limits});process.stdout.write(JSON.stringify(plan,null,2)+'\n');process.exitCode=plan.ok?0:1;return}
 if(cmd==='identity')r=targetIdentity(target);
 else if(cmd==='verify')r=o._.map(w=>verifyWheel(w,target,{limits,allowUnhashed:o.allowUnhashed}));
 else if(cmd==='install')r=installWheels({root:o.root||fail('USAGE','--root required'),id:o.id||fail('USAGE','--id required'),wheels:o._,target,limits,allowUnhashed:o.allowUnhashed});
 else if(cmd==='assemble'){let plan=json(o.plan||fail('USAGE','--plan required'));r=o.into?assembleInto({into:o.into,bank:o.bank,plan,target,limits,allowUnhashed:o.allowUnhashed}):assembleFromBank({root:o.root||fail('USAGE','--root required'),bank:o.bank||fail('USAGE','--bank required'),plan,target,id:o.id,limits,allowUnhashed:o.allowUnhashed})}
 else fail('USAGE','usage: assembler.mjs identity|verify|install|assemble|plan-wheels [--root R] [--id ID] [--bank B] [--plan P] [--into DIR] (--python EXE|--target JSON) [--limits JSON] [--allow-unhashed] [wheel...]');
 console.log(JSON.stringify(r))}
if(process.argv[1]&&fs.realpathSync(process.argv[1])===self){try{await cli(process.argv.slice(2))}catch(e){console.log(JSON.stringify({error:e.message,code:e.code||'ERROR',retryable:!!e.retryable,...(e.requirement?{requirement:e.requirement}:{})}));console.error('[plot assembler] '+e.message);process.exitCode=e.retryable?75:1}}
