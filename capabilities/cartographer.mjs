// Somnus Plot v0.7 dependency cartographer: a pure, offline planner over a local npm corpus.
// It reads package.json documents and USTAR members only. Package code, lifecycle scripts
// and the network are never touched, and the planner writes nothing (contracts §10).
import * as f from 'node:fs';
import * as p from 'node:path';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {fileURLToPath as u} from 'node:url';
const LIMIT={archive:268435456,entries:100000,manifest:4194304,depth:8,bundle:32};
const FAIL=new Set(['cycle','missing','range-unsatisfied','peer-unsatisfied']);
const GRAMMAR='supported grammar: exact, ^, ~, x/*, comparators >= <= > < =, hyphen ranges, ||';
const cmp=(a,b)=>a<b?-1:a>b?1:0,isObj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x),join=p.join;
const stable=x=>JSON.stringify(x,(_,v)=>isObj(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
const NAME=/^(?:@[A-Za-z0-9~-][A-Za-z0-9._~-]*\/)?[A-Za-z0-9~-][A-Za-z0-9._~-]*$/;
const validName=n=>typeof n==='string'&&n.length<=214&&NAME.test(n)&&n.split('/').pop()!=='node_modules';

// ---- semver: node-semver semantics for the frozen grammar; anything else is unsupported.
const N='0|[1-9]\\d*',X='0|[1-9]\\d*|[xX*]',PRE='(?:-([0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*))?',BUILD='(?:\\+[0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*)?';
const FULL=new RegExp(`^(${N})\\.(${N})\\.(${N})${PRE}${BUILD}$`),PART=new RegExp(`^v?(${X})(?:\\.(${X})(?:\\.(${X})${PRE}${BUILD})?)?$`);
const ver=(M,m,pt,pre=[])=>({major:M,minor:m,patch:pt,pre});
export function parseVersion(s){let m=typeof s==='string'&&FULL.exec(s);return m?ver(+m[1],+m[2],+m[3],m[4]?m[4].split('.'):[]):null}
export function compareVersions(a,b){
 if(typeof a==='string')a=parseVersion(a);if(typeof b==='string')b=parseVersion(b);
 for(let k of ['major','minor','patch'])if(a[k]!==b[k])return a[k]<b[k]?-1:1;
 if(!a.pre.length||!b.pre.length)return a.pre.length===b.pre.length?0:a.pre.length?-1:1;
 for(let i=0;i<Math.max(a.pre.length,b.pre.length);i++){let x=a.pre[i],y=b.pre[i];if(x===undefined)return -1;if(y===undefined)return 1;
  let nx=/^\d+$/.test(x),ny=/^\d+$/.test(y);if(nx&&ny){if(+x!==+y)return +x<+y?-1:1}else if(nx!==ny)return nx?-1:1;else if(x!==y)return x<y?-1:1}
 return 0;
}
const c=(op,v)=>({op,v}),any=[c('>=',ver(0,0,0))],none=[c('<',ver(0,0,0,['0']))];
function partial(s){let m=PART.exec(s);if(!m)return null;let x=v=>v===undefined||/^[xX*]$/.test(v)?null:+v,M=x(m[1]),mi=M===null?null:x(m[2]),pt=mi===null?null:x(m[3]);
 if(m[4]&&pt===null)return null;return {M,m:mi,p:pt,pre:m[4]?m[4].split('.'):[]}}
function comparators(op,q){let {M,m,p:pt,pre}=q,full=pt!==null,v=full?ver(M,m,pt,pre):null;
 if(M===null)return op===''||op==='='||op==='>='||op==='<='||op==='^'||op==='~'?any:none;
 switch(op){
  case '':case '=':return full?[c('=',v)]:m===null?[c('>=',ver(M,0,0)),c('<',ver(M+1,0,0,['0']))]:[c('>=',ver(M,m,0)),c('<',ver(M,m+1,0,['0']))];
  case '~':return m===null?[c('>=',ver(M,0,0)),c('<',ver(M+1,0,0,['0']))]:[c('>=',full?v:ver(M,m,0)),c('<',ver(M,m+1,0,['0']))];
  case '^':if(m===null)return [c('>=',ver(M,0,0)),c('<',ver(M+1,0,0,['0']))];
   if(!full)return M>0?[c('>=',ver(M,m,0)),c('<',ver(M+1,0,0,['0']))]:[c('>=',ver(0,m,0)),c('<',ver(0,m+1,0,['0']))];
   return [c('>=',v),c('<',M>0?ver(M+1,0,0,['0']):m>0?ver(0,m+1,0,['0']):ver(0,0,pt+1,['0']))];
  case '>':return full?[c('>',v)]:m===null?[c('>=',ver(M+1,0,0))]:[c('>=',ver(M,m+1,0))];
  case '>=':return [c('>=',full?v:ver(M,m??0,0))];
  case '<':return full?[c('<',v)]:[c('<',ver(M,m??0,0,['0']))];
  case '<=':return full?[c('<=',v)]:m===null?[c('<',ver(M+1,0,0,['0']))]:[c('<',ver(M,m+1,0,['0']))];
 }
}
// Returns an array of comparator sets (|| alternatives), or null for a form outside the grammar.
export function parseRange(r){
 if(typeof r!=='string'||r.length>1024)return null;let sets=[];
 for(let s of r.trim().split(/\s*\|\|\s*/)){s=s.trim();if(!s){sets.push(any);continue}
  let h=/^(\S+)\s+-\s+(\S+)$/.exec(s);
  if(h){let a=partial(h[1]),b=partial(h[2]);if(!a||!b)return null;let lo=a.M===null?any:[c('>=',ver(a.M,a.m??0,a.p??0,a.p===null?[]:a.pre))];
   let hi=b.M===null?[]:b.p!==null?[c('<=',ver(b.M,b.m,b.p,b.pre))]:b.m===null?[c('<',ver(b.M+1,0,0,['0']))]:[c('<',ver(b.M,b.m+1,0,['0']))];sets.push([...lo,...hi]);continue}
  let set=[];for(let t of s.replace(/(>=|<=|>|<|=|\^|~)\s+/g,'$1').split(/\s+/)){let m=/^(>=|<=|>|<|=|\^|~)?(.+)$/.exec(t),q=m&&partial(m[2]);if(!q)return null;set.push(...comparators(m[1]||'',q))}
  sets.push(set);
 }
 return sets;
}
const test=(v,{op,v:w})=>{let k=compareVersions(v,w);return op==='='?k===0:op==='>'?k>0:op==='>='?k>=0:op==='<'?k<0:k<=0};
export function satisfies(v,range){
 if(typeof v==='string')v=parseVersion(v);if(typeof range==='string')range=parseRange(range);if(!v||!range)return false;
 return range.some(set=>set.every(x=>test(v,x))&&(!v.pre.length||set.some(({v:w})=>w.pre.length&&w.major===v.major&&w.minor===v.minor&&w.patch===v.patch)));
}

// ---- USTAR reader (gzip-wrapped). Builds an in-memory member table; never writes or links.
function readTar(buf){
 let files=new Map(),seen=new Set(),off=0,pax=null,long=null,count=0;
 const str=(h,a,n)=>{let s=h.subarray(a,a+n),z=s.indexOf(0);return (z<0?s:s.subarray(0,z)).toString('utf8')};
 const num=(h,a,n)=>{if(h[a]&0x80)throw Error('base-256 tar number');let s=str(h,a,n).trim();if(!/^[0-7]*$/.test(s))throw Error('tar number');return s?parseInt(s,8):0};
 const paxOf=d=>{let o={},i=0;while(i<d.length){let sp=d.indexOf(32,i),len=sp<0?NaN:+d.subarray(i,sp).toString();if(!(len>0)||i+len>d.length)throw Error('pax record');
  let rec=d.subarray(sp+1,i+len-1).toString('utf8'),eq=rec.indexOf('=');if(eq<1)throw Error('pax record');o[rec.slice(0,eq)]=rec.slice(eq+1);i+=len}return o};
 while(off+512<=buf.length){let h=buf.subarray(off,off+512);if(h.every(b=>b===0))return files;
  let sum=0;for(let i=0;i<512;i++)sum+=i>=148&&i<156?32:h[i];if(sum!==num(h,148,8))throw Error('tar checksum');
  let size=num(h,124,12),t=String.fromCharCode(h[156]),a=off+512,next=a+Math.ceil(size/512)*512;if(next>buf.length)throw Error('truncated tar');
  let data=buf.subarray(a,a+size);off=next;if(++count>LIMIT.entries)throw Error('tar entry limit');
  if(t==='x'){pax=paxOf(data);continue}if(t==='g')continue;if(t==='L'){long=str(data,0,data.length);continue}if(t==='K')continue;
  let magic=str(h,257,6),raw=pax?.path??long??(magic==='ustar'&&str(h,345,155)?str(h,345,155)+'/':'')+str(h,0,100);pax=long=null;
  if(!raw||/[\\\0]/.test(raw)||raw.startsWith('/')||raw.split('/').includes('..'))throw Error('tar path '+JSON.stringify(raw));
  let name=p.posix.normalize(raw).replace(/^\.\//,'').replace(/\/$/,'');if(!'0\x00712356'.includes(t))throw Error('tar type '+JSON.stringify(t));
  if(name==='.'||t==='5')continue;if(seen.has(name))throw Error('tar duplicate '+name);seen.add(name);
  if((t==='0'||t==='\0'||t==='7')&&/(^|\/)package\.json$/.test(name)){if(size>LIMIT.manifest)throw Error('manifest limit');files.set(name,Buffer.from(data))}
 }
 throw Error('incomplete tar');
}

// ---- corpus
function manifestOf(text,where,unsupported){
 let m;try{m=JSON.parse(text)}catch(e){unsupported.push({where,form:'manifest',reason:'package.json is not JSON: '+e.message});return null}
 if(!isObj(m)){unsupported.push({where,form:'manifest',reason:'package.json is not an object'});return null}
 if(!validName(m.name)){unsupported.push({where,form:'name',reason:'invalid or missing package name '+JSON.stringify(m.name)});return null}
 if(!parseVersion(m.version)){unsupported.push({where,form:'version',reason:'invalid or missing semver version '+JSON.stringify(m.version)});return null}
 return m;
}
const bundleNames=m=>{let b=m.bundleDependencies??m.bundledDependencies;return b===true?Object.keys(isObj(m.dependencies)?m.dependencies:{}):Array.isArray(b)?b.filter(x=>typeof x==='string'):[]};
function scanBundle(dir,rel,depth,out,unsupported){
 let nm=join(dir,'node_modules');if(depth>LIMIT.bundle||!f.existsSync(nm)||!f.lstatSync(nm).isDirectory())return;
 const add=(d,name)=>{let st=f.lstatSync(d);if(!st.isDirectory()||!f.existsSync(join(d,'package.json')))return;
  let where=join(d,'package.json'),m=manifestOf(f.readFileSync(where,'utf8'),where,unsupported);
  if(m){let r=rel+'node_modules/'+name;out[r]={name:m.name,version:m.version,manifest:m,source:{kind:'dir',path:d,integrity:null}};scanBundle(d,r+'/',depth+1,out,unsupported)}};
 for(let e of f.readdirSync(nm).sort(cmp)){let d=join(nm,e);if(e.startsWith('@')&&f.lstatSync(d).isDirectory()){for(let s of f.readdirSync(d).sort(cmp))add(join(d,s),e+'/'+s)}else if(!e.startsWith('.'))add(d,e)}
}
export function inspectCorpus(dir){
 if(typeof dir!=='string'||!dir)throw TypeError('inspectCorpus: corpus directory path required');
 let root;try{root=f.realpathSync(dir)}catch(e){throw Error(`inspectCorpus: corpus ${dir} unreadable (${e.code||e.message})`)}
 if(!f.statSync(root).isDirectory())throw Error(`inspectCorpus: corpus ${root} is not a directory`);
 let found=[],unsupported=[];
 function fromDir(d){let where=join(d,'package.json'),st=f.statSync(where);if(st.size>LIMIT.manifest){unsupported.push({where,form:'manifest',reason:'package.json exceeds limit'});return}
  let m=manifestOf(f.readFileSync(where,'utf8'),where,unsupported);if(!m)return;let bundle={};if(bundleNames(m).length)scanBundle(d,'',0,bundle,unsupported);
  found.push({name:m.name,version:m.version,manifest:m,source:{kind:'dir',path:d,integrity:null},bundle})}
 function fromTgz(x){
  let data,files;try{if(f.statSync(x).size>LIMIT.archive)throw Error('archive limit');data=f.readFileSync(x);files=readTar(gunzipSync(data,{maxOutputLength:LIMIT.archive}))}
  catch(e){if(e.code&&!/^(Z_|ERR_BUFFER|ERR_OUT_OF_RANGE)/.test(e.code)&&e.code!=='ENOENT')throw e;unsupported.push({where:x,form:'archive',reason:e.message});return}
  let tops=[...files.keys()].filter(k=>/^[^/]+\/package\.json$/.test(k));
  if(tops.length!==1){unsupported.push({where:x,form:'archive',reason:`expected exactly one <top>/package.json, found ${tops.length}`});return}
  let top=tops[0].slice(0,-'/package.json'.length),integrity='sha256-'+createHash('sha256').update(data).digest('base64');
  let m=manifestOf(files.get(tops[0]).toString('utf8'),x+'!'+tops[0],unsupported);if(!m)return;let bundle={};
  for(let [k,b] of [...files].sort((a,b)=>cmp(a[0],b[0]))){let r=k.startsWith(top+'/')&&/^((?:node_modules\/(?:@[^/]+\/)?[^/]+\/)+)package\.json$/.exec(k.slice(top.length+1));if(!r)continue;
   let rel=r[1].slice(0,-1),bm=manifestOf(b.toString('utf8'),x+'!'+k,unsupported);if(bm)bundle[rel]={name:bm.name,version:bm.version,manifest:bm,source:{kind:'tgz',path:x,integrity,member:top+'/'+rel}}}
  found.push({name:m.name,version:m.version,manifest:m,source:{kind:'tgz',path:x,integrity,member:top},bundle});
 }
 (function walk(d,depth){
  if(f.existsSync(join(d,'package.json')))return fromDir(d);
  for(let e of f.readdirSync(d).sort(cmp)){let x=join(d,e),st=f.lstatSync(x);
   if(st.isSymbolicLink())unsupported.push({where:x,form:'symlink',reason:'corpus symlinks are not followed'});
   else if(st.isDirectory()){if(e==='node_modules'||e.startsWith('.'))continue;if(depth>=LIMIT.depth)unsupported.push({where:x,form:'depth',reason:'corpus nesting exceeds '+LIMIT.depth});else walk(x,depth+1)}
   else if(st.isFile()&&e.endsWith('.tgz'))fromTgz(x)}
 })(root,0);
 found.sort((a,b)=>cmp(a.name,b.name)||compareVersions(a.version,b.version)||cmp(a.source.kind,b.source.kind)||cmp(a.source.path,b.source.path));
 let packages=[],last=null;
 for(let r of found){if(last&&last.name===r.name&&last.version===r.version){unsupported.push({where:r.name+'@'+r.version,form:'duplicate',reason:`also at ${r.source.path}; using ${last.source.path}`});continue}packages.push(last=r)}
 return {schema:'plot.corpus/1',root,packages,unsupported};
}

// ---- entrypoints: Node conditional exports/imports evaluated in manifest key order.
const INVALID=Symbol('invalid');
const badSegment=s=>s.split(/[\\/]/).some(x=>/^(\.|%2e){1,2}$/i.test(x)||/^node_modules$/i.test(decodeURIComponentSafe(x)));
function decodeURIComponentSafe(s){try{return decodeURIComponent(s)}catch{return s}}
function entryOf(m,id,conds,unsup){
 const target=(v,where,imports,quiet)=>{
  if(typeof v==='string'){
   if(!v.startsWith('./')){if(imports&&!/^(\.\.?\/|\/)/.test(v)&&!/^[a-z][a-z0-9+.-]*:/i.test(v)&&!v.startsWith('#'))return v;if(!quiet)unsup(where,'invalid-target',`target ${JSON.stringify(v)} must start with "./"`);return INVALID}
   if(badSegment(v.slice(2))){if(!quiet)unsup(where,'invalid-target',`target ${JSON.stringify(v)} contains ".", ".." or node_modules segments`);return INVALID}return v}
  if(v===null)return null;
  if(Array.isArray(v)){if(!v.length)return null;let sawNull=false;for(let x of v){let r=target(x,where,imports,true);if(r===INVALID||r===undefined)continue;if(r===null){sawNull=true;continue}return r}return sawNull?null:undefined}
  if(isObj(v)){let ks=Object.keys(v);if(ks.some(k=>/^(0|[1-9]\d*)$/.test(k))){unsup(where,'numeric-key','condition objects cannot carry numeric keys (JSON key order is not preserved for them)');return INVALID}
   for(let k of ks)if(k==='default'||conds.includes(k)){let r=target(v[k],where,imports,quiet);if(r===undefined)continue;return r}return undefined}
  if(!quiet)unsup(where,'invalid-target',`target of type ${typeof v}`);return INVALID;
 };
 const map=(x,field,prefix)=>{let out={},src,where=`${id}#${field}`;
  if(typeof x==='string'||Array.isArray(x)){if(field==='imports'){unsup(where,'invalid-shape','imports must be an object');return out}src=[['.',x]]}
  else if(isObj(x)){let ks=Object.keys(x),keyed=ks.filter(k=>k.startsWith(prefix));
   if(keyed.length&&keyed.length!==ks.length){unsup(where,'mixed-keys','subpath keys mixed with condition names');return out}
   if(!keyed.length&&field==='imports'){if(ks.length)unsup(where,'invalid-key','imports keys must start with "#"');return out}src=keyed.length?ks.map(k=>[k,x[k]]):[['.',x]]}
  else{unsup(where,'invalid-shape',`${field} of type ${typeof x}`);return out}
  for(let [k,v] of src){let w=`${where}[${k}]`;
   if(field==='exports'&&k!=='.'&&!k.startsWith('./')||field==='imports'&&(k==='#'||k.startsWith('#/'))){unsup(w,'invalid-key','invalid subpath key');continue}
   if(k.split('*').length>2){unsup(w,'multiple-wildcards','subpath patterns allow one "*"');continue}
   if(k.endsWith('/')){unsup(w,'folder-mapping','trailing-slash folder mappings were removed from Node');continue}
   let r=target(v,w,field==='imports',false);out[k]=r===INVALID||r===undefined?null:r}
  return out};
 let bin={},raw=m.bin;
 const binPath=(k,v)=>{let w=`${id}#bin[${k}]`;if(typeof v!=='string'||!/^[^/\\\0]+$/.test(k)||k==='.'||k==='..'){unsup(w,'invalid-bin','bin entries map a plain command name to a relative file');return}
  let q=p.posix.normalize(v.replace(/^\.\//,''));if(!q||q==='.'||q.startsWith('/')||q.split('/').includes('..')||v.includes('\\')){unsup(w,'invalid-bin',`bin target ${JSON.stringify(v)} leaves the package`);return}bin[k]=q};
 if(typeof raw==='string')binPath(m.name.split('/').pop(),raw);else if(isObj(raw))for(let k of Object.keys(raw))binPath(k,raw[k]);
 else if(raw!==undefined)unsup(`${id}#bin`,'invalid-bin','bin must be a string or object');
 if(raw===undefined&&isObj(m.directories)&&m.directories.bin!==undefined)unsup(`${id}#directories.bin`,'directories.bin','directory-listed bins are not enumerated');
 let e={main:typeof m.main==='string'?m.main:null,exports:m.exports===undefined||m.exports===null?null:map(m.exports,'exports','.'),bin};
 if(m.imports!==undefined&&m.imports!==null)e.imports=map(m.imports,'imports','#');
 return e;
}

// ---- presence: a node is present only when a complete object's canonical Plot key names it.
// Key = stable([recipe, [platform, arch], needPaths]); recipe.component must equal
// {ecosystem:'npm', name, version} and the host pair must equal the plan target.
function presence(root,target){
 let index=new Map();if(root===null||root===undefined)return index;
 let real;try{real=f.realpathSync(root)}catch(e){throw Error(`planClosure: plot root ${root} unreadable (${e.code||e.message})`)}
 let grave=join(real,'.grave'),objects=join(grave,'objects'),objReal;if(!f.existsSync(objects))return index;objReal=f.realpathSync(objects);
 const soft=e=>e instanceof SyntaxError||['ENOENT','ENOTDIR','EACCES','ELOOP','EISDIR'].includes(e.code);
 const check=v=>{try{
  if(!isObj(v)||typeof v.key!=='string'||typeof v.path!=='string')return;let at=f.realpathSync(v.path);if(p.dirname(at)!==objReal)return;
  if(stable(JSON.parse(f.readFileSync(join(at,'.plot.json'),'utf8')))!==stable(v)||v.python&&!f.existsSync(v.python))return;
  if(f.existsSync(join(grave,'tombstones',p.basename(at)+'.json')))return;
  let k=JSON.parse(v.key),cpt=Array.isArray(k)&&k.length===3&&isObj(k[0])?k[0].component:null;
  if(!isObj(cpt)||cpt.ecosystem!=='npm'||!validName(cpt.name)||!parseVersion(cpt.version)||stable(k[1])!==stable([target.platform,target.arch]))return;
  let id=cpt.name+'@'+cpt.version;if(!index.has(id))index.set(id,{object:at,key:v.key});
 }catch(e){if(!soft(e))throw e}};
 let ledger=join(real,'data.json');
 if(f.existsSync(ledger)){let d;try{d=JSON.parse(f.readFileSync(ledger,'utf8'))}catch(e){if(!soft(e))throw e}if(isObj(d?.assets))for(let k of Object.keys(d.assets).sort(cmp))check(d.assets[k])}
 for(let e of f.readdirSync(objects).sort(cmp)){let d=join(objects,e),v;try{if(!f.lstatSync(d).isDirectory())continue;v=JSON.parse(f.readFileSync(join(d,'.plot.json'),'utf8'));if(typeof v?.path!=='string'||f.realpathSync(v.path)!==f.realpathSync(d))continue}catch(err){if(soft(err))continue;throw err}check(v)}
 return index;
}

function hostLibc(platform){
 if(platform!=='linux'||process.platform!=='linux')return null;
 try{return process.report.getReport().header.glibcVersionRuntime?'glibc':'musl'}catch{return null}
}
const excludes=(vals,value)=>{let a=typeof vals==='string'?[vals]:Array.isArray(vals)?vals.filter(x=>typeof x==='string'):[];if(!a.length)return false;
 let neg=a.filter(x=>x.startsWith('!')).map(x=>x.slice(1)),pos=a.filter(x=>!x.startsWith('!'));return neg.includes(value)||pos.length>0&&!pos.includes(value)};

// ---- canonical serialization: keys sorted except order-significant manifest maps.
function canon(x,path=[]){
 if(Array.isArray(x))return x.map(v=>canon(v,path));if(!isObj(x))return x;
 let keep=path.length>=2&&path[path.length-2]==='entry'&&(path[path.length-1]==='exports'||path[path.length-1]==='imports');
 return Object.fromEntries((keep?Object.keys(x):Object.keys(x).sort(cmp)).map(k=>[k,canon(x[k],[...path,k])]));
}
export const serialize=x=>JSON.stringify(canon(x),null,2)+'\n';

export function planClosure(options){
 if(!isObj(options))throw TypeError('planClosure: options object required');
 let {corpus,root=null,requested,conditions,target:t={}}=options;
 if(typeof corpus==='string')corpus=inspectCorpus(corpus);else if(corpus?.schema!=='plot.corpus/1'||!Array.isArray(corpus.packages))throw TypeError('planClosure: corpus must be a directory path or an inspectCorpus() result');
 if(!Array.isArray(requested)||!requested.length||!requested.every(s=>typeof s==='string'&&s.trim()))throw TypeError('planClosure: requested must be a non-empty array of package specs');
 if(!isObj(t))throw TypeError('planClosure: target must be an object');
 conditions=conditions??t.conditions??['node','import'];
 if(!Array.isArray(conditions)||!conditions.every(x=>typeof x==='string'&&/^[^\s,]{1,64}$/.test(x)))throw TypeError('planClosure: conditions must be an array of condition names');
 let platform=t.platform??process.platform,arch=t.arch??process.arch,libc=t.libc!==undefined?t.libc:hostLibc(platform),node=t.node===undefined?process.versions.node:t.node;
 if(typeof platform!=='string'||!platform||typeof arch!=='string'||!arch)throw TypeError('planClosure: target platform/arch must be non-empty strings');
 if(![null,'glibc','musl'].includes(libc))throw TypeError('planClosure: target libc must be "glibc", "musl" or null');
 if(node!==null&&!parseVersion(node))throw TypeError(`planClosure: target node ${JSON.stringify(node)} is not a semver version`);
 let conds=[...new Set(conditions)],target={platform,arch,libc,node,conditions:conds,python:t.python??null};
 let byName=new Map(),unsupported=[...corpus.unsupported],diagnostics=[],pruned=new Map(),nodes=[],ids=new Set(),placed=new Map(),regions=[],resolutions=new Map(),queue=[];
 for(let r of corpus.packages){if(!byName.has(r.name))byName.set(r.name,[]);byName.get(r.name).push(r)}
 for(let l of byName.values())l.sort((a,b)=>compareVersions(b.version,a.version));
 const unsup=(where,form,reason)=>unsupported.push({where,form,reason}),diag=(code,detail)=>diagnostics.push({code,detail}),prune=(id,reason)=>pruned.set(id+'\0'+reason,{id,reason});
 const levelsOf=loc=>{let L=[];for(let x=loc;x;){L.push(x+'/node_modules');let i=x.lastIndexOf('/node_modules/');x=i<0?'':x.slice(0,i)}L.push('node_modules');return [...new Set(L)]};
 const occupant=(level,name)=>{let n=placed.get(level+'/'+name);if(n)return {node:n};
  let b=regions.filter(r=>level===r.region||level.startsWith(r.region+'/')).sort((a,b)=>b.region.length-a.region.length)[0];
  let mem=b&&b.bundle['node_modules'+level.slice(b.region.length)+'/'+name];return mem?{member:mem}:null};
 function make(rec,placement){
  let id=rec.name+'@'+rec.version;if(ids.has(id))id+=':'+placement;ids.add(id);
  let n={id,ecosystem:'npm',name:rec.name,version:rec.version,source:rec.source,placement,deps:[],entry:entryOf(rec.manifest,id,conds,unsup),present:{object:null,key:null},manifest:rec.manifest};
  if(rec.bundle&&Object.keys(rec.bundle).length)regions.push({region:placement+'/node_modules',bundle:rec.bundle});
  nodes.push(n);placed.set(placement,n);queue.push(n);return n;
 }
 const lookup=(levels,name)=>{for(let i=0;i<levels.length;i++){let o=occupant(levels[i],name);if(o)return {node:o.node||make(o.member,levels[i]+'/'+name),i}}return null};
 const record=(from,name,at)=>{if(!resolutions.has(name))resolutions.set(name,[]);resolutions.get(name).push({from,at})};
 const shadows=(level,name)=>{let owner=level==='node_modules'?'':level.slice(0,-'/node_modules'.length);
  return (resolutions.get(name)||[]).some(r=>(owner===''||r.from===owner||r.from.startsWith(owner+'/'))&&r.at.length-name.length-1<level.length)};
 const excluded=rec=>{let m=rec.manifest,id=rec.name+'@'+rec.version;
  if(excludes(m.os,platform))return 'os';if(excludes(m.cpu,arch))return 'cpu';if(libc&&excludes(m.libc,libc))return 'libc';
  if(node&&isObj(m.engines)&&typeof m.engines.node==='string'){let r=parseRange(m.engines.node);if(!r)unsup(id+'#engines.node',m.engines.node,'engines range outside '+GRAMMAR+'; treated as advisory');else if(!satisfies(node,r))return 'engines'}
  return null};
 function select(name,range){let all=byName.get(name)||[],sat=all.filter(r=>satisfies(r.version,range)),skipped=[];
  if(!all.length)return {why:'absent'};if(!sat.length)return {why:'range',versions:all.map(r=>r.version)};
  for(let r of sat){let x=excluded(r);if(!x)return {rec:r,skipped};skipped.push([r,x])}return {why:'host',skipped}}
 // Edge resolution follows Node's upward node_modules lookup; new nodes go as high as
 // the first conflicting occupant allows without shadowing an earlier resolution.
 function resolve(from,e){
  let {name,range:spec,kind,where,optional}=e,range=parseRange(spec),dep={name,range:spec,kind,resolved:null},who=from.id||'requested';
  if(!range)unsup(where,spec,'range form outside '+GRAMMAR);
  const done=n=>{dep.resolved=n.id;record(from.placement,name,n.placement);return dep};
  if(kind==='bundled'){let o=lookup([levelsOf(from.placement)[0]],name);
   if(!o)diag('missing',`bundled dependency ${name} declared by ${who} is absent from its package (${from.source.path})`);
   else{if(range&&!satisfies(o.node.version,range))diag('range-unsatisfied',`bundled ${o.node.id} does not satisfy ${name}@${spec} declared by ${who}`);done(o.node)}return dep}
  let levels=kind==='peer'?levelsOf(from.placement).slice(1):levelsOf(from.placement),found=lookup(levels,name);
  if(found&&range&&satisfies(found.node.version,range))return done(found.node);
  if(kind==='peer'){if(!range&&optional)return dep;if(found){diag('peer-unsatisfied',`${who} peers ${name}@${spec} but ${found.node.id} is visible at ${found.node.placement}`);return dep}if(optional)return dep}
  if(!range){if(kind==='optional')prune(name+'@'+spec,'optional-incompatible');else diag(kind==='peer'?'peer-unsatisfied':'range-unsatisfied',`${name}@${spec} required by ${who}: unsupported range form`);return dep}
  let s=select(name,range);for(let [r,why] of s.skipped||[])prune(r.name+'@'+r.version,why);
  if(!s.rec){
   if(kind==='optional'){if(s.why!=='host')prune(name+'@'+spec,s.why==='absent'?'optional-absent':'optional-incompatible')}
   else if(kind==='peer')diag('peer-unsatisfied',`${who} peers ${name}@${spec}: ${s.why==='absent'?'not in corpus':s.why==='range'?'no corpus version satisfies':'no host-compatible version'}`);
   else if(s.why==='absent')diag('missing',`${name}@${spec} required by ${who}: no package named ${name} in corpus`);
   else diag('range-unsatisfied',`${name}@${spec} required by ${who}: `+(s.why==='range'?'available '+s.versions.join(', '):'no host-compatible candidate ('+s.skipped.map(([r,w])=>r.version+' '+w).join(', ')+')'));
   return dep}
  let limit=found?found.i:levels.length,at=-1;for(let i=limit-1;i>=0;i--)if(!shadows(levels[i],name)){at=i;break}
  if(at<0&&kind!=='peer'&&limit>0)at=0;
  if(at<0){if(kind==='optional')prune(s.rec.name+'@'+s.rec.version,'optional-incompatible');else diag(kind==='peer'?'peer-unsatisfied':'range-unsatisfied',`${name}@${spec} required by ${who}: ${found?found.node.id+' occupies '+found.node.placement:'no placement'} and no nested placement is available`);return dep}
  return done(make(s.rec,levels[at]+'/'+name));
 }
 function edges(n){let m=n.manifest,obj=x=>isObj(x)?x:{},meta=obj(m.peerDependenciesMeta),map=new Map();
  for(let [field,kind] of [['peerDependencies','peer'],['dependencies','prod'],['optionalDependencies','optional']])
   for(let [name,range] of Object.entries(obj(m[field]))){let where=`${n.id}#${field}.${name}`;
    if(!validName(name)){unsup(where,'name','invalid dependency name');continue}if(typeof range!=='string'){unsup(where,'range','range must be a string');continue}
    map.set(name,{name,range,kind,where,optional:kind==='peer'&&meta[name]?.optional===true})}
  let bundled=[];for(let name of bundleNames(m)){if(!validName(name)){unsup(`${n.id}#bundleDependencies`,'name','invalid bundled name '+JSON.stringify(name));continue}
   let e=map.get(name);bundled.push({name,range:e?.range??'*',kind:'bundled',where:`${n.id}#bundleDependencies.${name}`});map.delete(name)}
  return [...bundled.sort((a,b)=>cmp(a.name,b.name)),...[...map.values()].sort((a,b)=>cmp(a.name,b.name))]}
 let root0={id:null,placement:'',source:{path:corpus.root}},specs=[...new Set(requested.map(s=>s.trim()))].sort(cmp);
 for(let s of specs){let m=/^(@[^@/]+\/[^@/]+|[^@/][^@]*)(?:@(.*))?$/.exec(s);
  if(!m||!validName(m[1])){unsup('requested#'+s,s,'invalid package spec');diag('missing',`requested ${s}: invalid package spec`);continue}
  resolve(root0,{name:m[1],range:m[2]??'*',kind:'prod',where:'requested#'+s})}
 while(queue.length){let n=queue.shift();let es=edges(n);for(let e of es)n.deps.push(resolve(n,e))}
 for(let n of nodes)n.deps.sort((a,b)=>cmp(a.name,b.name));
 let have=presence(root,target);for(let n of nodes){let h=have.get(n.name+'@'+n.version);if(h)n.present=h}
 // Deterministic Kahn order (dependencies first, ties by id); leftovers are cycle members or their dependents.
 let deps=new Map(nodes.map(n=>[n.id,[...new Set(n.deps.map(d=>d.resolved).filter(Boolean))].sort(cmp)]));
 let indeg=new Map(),users=new Map(nodes.map(n=>[n.id,[]])),order=[],ready=[];
 for(let [id,ds] of deps){indeg.set(id,ds.length);for(let d of ds)users.get(d).push(id)}
 const insert=id=>{let lo=0,hi=ready.length;while(lo<hi){let mid=lo+hi>>1;if(ready[mid]<id)lo=mid+1;else hi=mid}ready.splice(lo,0,id)};
 for(let [id,k] of indeg)if(!k)insert(id);
 while(ready.length){let id=ready.shift();order.push(id);for(let x of users.get(id)){indeg.set(x,indeg.get(x)-1);if(!indeg.get(x))insert(x)}}
 let placedIds=new Set(order),rest=new Set(nodes.map(n=>n.id).filter(id=>!placedIds.has(id)));
 if(rest.size){let index=new Map(),low=new Map(),stack=[],on=new Set(),k=0,sccs=[];
  const strong=v=>{index.set(v,k);low.set(v,k++);stack.push(v);on.add(v);
   for(let w of deps.get(v)){if(!rest.has(w))continue;if(!index.has(w)){strong(w);low.set(v,Math.min(low.get(v),low.get(w)))}else if(on.has(w))low.set(v,Math.min(low.get(v),index.get(w)))}
   if(low.get(v)===index.get(v)){let s=[],w;do{w=stack.pop();on.delete(w);s.push(w)}while(w!==v);sccs.push(s)}};
  for(let v of [...rest].sort(cmp))if(!index.has(v))strong(v);
  for(let s of sccs){let set=new Set(s);if(s.length<2&&!deps.get(s[0]).includes(s[0]))continue;
   let cur=[...s].sort(cmp)[0],seen=[];while(!seen.includes(cur)){seen.push(cur);cur=deps.get(cur).filter(d=>set.has(d))[0]}
   diag('cycle',[...seen.slice(seen.indexOf(cur)),cur].join(' -> '))}
  order.push(...[...rest].sort(cmp))}
 const uniq=(list,key)=>[...new Map(list.map(x=>[key(x),x])).values()].sort((a,b)=>cmp(key(a),key(b)));
 diagnostics=uniq(diagnostics,d=>d.code+'\0'+d.detail);
 let plan={schema:'plot.closure/1',target,requested:specs,
  nodes:nodes.map(({manifest,...n})=>n).sort((a,b)=>cmp(a.id,b.id)),order,
  pruned:[...pruned.values()].sort((a,b)=>cmp(a.id,b.id)||cmp(a.reason,b.reason)),
  unsupported:uniq(unsupported,x=>x.where+'\0'+x.form+'\0'+x.reason),diagnostics,ok:!diagnostics.some(d=>FAIL.has(d.code))};
 return JSON.parse(serialize(plan));
}

if(process.argv[1]&&f.realpathSync(process.argv[1])===u(import.meta.url)){
 const usage='usage: cartographer.mjs plan --corpus <dir> [--root <plotRoot>] [--conditions node,import] [--platform P --arch A --libc glibc|musl|null --node V] <specs...>\n       cartographer.mjs inspect --corpus <dir>';
 let a=process.argv.slice(2),cmd=a.shift(),o={requested:[],target:{}};
 try{
  while(a.length){let x=a.shift();if(!x.startsWith('--')){o.requested.push(x);continue}let v=a.shift();if(v===undefined)throw Error(x+' needs a value\n'+usage);
   if(x==='--corpus')o.corpus=v;else if(x==='--root')o.root=v;else if(x==='--conditions')o.conditions=v.split(',').filter(Boolean);
   else if(['--platform','--arch','--node'].includes(x))o.target[x.slice(2)]=v;else if(x==='--libc')o.target.libc=v==='null'?null:v;else throw Error('unknown option '+x+'\n'+usage)}
  if(!o.corpus)throw Error('--corpus required\n'+usage);
  if(cmd==='plan'){let plan=planClosure(o);process.stdout.write(serialize(plan));process.exitCode=plan.ok?0:1}
  else if(cmd==='inspect'){let c=inspectCorpus(o.corpus);process.stdout.write(serialize({...c,packages:c.packages.map(r=>({name:r.name,version:r.version,source:r.source,bundled:Object.keys(r.bundle)}))}))}
  else throw Error(usage);
 }catch(e){console.error('[cartographer] '+e.message);process.exitCode=2}
}
