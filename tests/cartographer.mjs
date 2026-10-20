import * as fs from 'node:fs';
import * as path from 'node:path';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';
import {planClosure,inspectCorpus,serialize,satisfies,parseRange} from '../capabilities/cartographer.mjs';
import {base,scratch,tar} from './helpers.mjs';
// Fixtures are real package.json documents and real gzip/USTAR archives written to disk.
// The planner is expected to read them only; nothing in them is ever executed.
const tmp=scratch(),checks=[],tool=path.join(base,'capabilities/cartographer.mjs');
const test=async(name,fn)=>{let t=performance.now();try{await fn();checks.push({name,passed:true,ms:performance.now()-t});console.log('PASS '+name)}catch(e){checks.push({name,passed:false,error:e.stack});console.error('FAIL '+name+'\n'+e.stack)}};
const T={platform:'linux',arch:'x64',libc:'glibc',node:'24.22.0'};
const stable=x=>JSON.stringify(x,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
const write=(file,data)=>{fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,typeof data==='string'||Buffer.isBuffer(data)?data:JSON.stringify(data,null,1))};
const pkg=(dir,m,files={})=>{write(path.join(dir,'package.json'),m);for(let [k,v] of Object.entries(files))write(path.join(dir,k),v);return dir};
const P=(name,version,more={})=>({name,version,...more});
const corpus=(name,list,at=tmp)=>{let d=path.join(at,name);fs.mkdirSync(d,{recursive:true});for(let x of list){let [m,files]=Array.isArray(x)?x:[x,{}];pkg(path.join(d,m.name.replace('/','+')+'-'+m.version),m,files)}return d};
const plan=(c,requested,o={})=>planClosure({corpus:c,requested,target:T,...o});
const node=(pl,id)=>pl.nodes.find(n=>n.id===id)||assert.fail(`no node ${id} in [${pl.nodes.map(n=>n.id)}]`);
const dep=(n,name)=>n.deps.find(d=>d.name===name)||assert.fail(`no dep ${name} on ${n.id}`);
const codes=pl=>pl.diagnostics.map(d=>d.code);
const cli=(args,o={})=>spawnSync(process.execPath,[tool,...args],{encoding:'utf8',timeout:60000,...o});
const listing=d=>{let out=[];(function walk(x){for(let e of fs.readdirSync(x).sort()){let y=path.join(x,e);out.push(path.relative(d,y));if(fs.lstatSync(y).isDirectory())walk(y)}})(d);return out};
const paxRec=(k,v)=>{let body=` ${k}=${v}\n`,n=body.length+1;while(String(n).length+body.length!==n)n=String(n).length+body.length;return n+body};
const sri=file=>'sha256-'+createHash('sha256').update(fs.readFileSync(file)).digest('base64');
const tflags=['--platform',T.platform,'--arch',T.arch,'--libc',T.libc,'--node',T.node];
const peerCorpus=at=>[
 P('app','1.0.0',{dependencies:{plugin:'^1',bund:'^1'}}),
 P('plugin','1.0.0',{peerDependencies:{host:'^2',opt:'*'},peerDependenciesMeta:{opt:{optional:true}}}),
 P('host','1.0.0'),P('host','2.1.0'),P('opt','1.0.0'),P('z','1.0.0'),P('w','9.0.0'),
 [P('bund','1.0.0',{dependencies:{z:'^3'},bundleDependencies:['z']}),{'node_modules/z/package.json':P('z','3.0.0',{dependencies:{w:'^1'}}),'node_modules/w/package.json':P('w','1.0.0'),'node_modules/z/index.js':'module.exports=3'}]];
try{
 await test('supported range grammar follows npm semver semantics; other forms are unsupported',()=>{
  for(let [v,r,want] of [['1.2.3','1.2.3',true],['1.2.4','=1.2.3',false],['1.2.3','v1.2.3',true],['1.9.9','^1.2.3',true],['2.0.0','^1.2.3',false],['0.2.9','^0.2.3',true],['0.3.0','^0.2.3',false],
   ['0.0.3','^0.0.3',true],['0.0.4','^0.0.3',false],['0.0.9','^0.0',true],['0.1.0','^0.0',false],['1.2.9','~1.2.3',true],['1.3.0','~1.2.3',false],['1.9.0','~1',true],['1.5.0','1.x',true],['2.0.0','1.x',false],
   ['3.1.4','*',true],['3.1.4','',true],['1.2.7','1.2.X',true],['1.2.3','>=1.2.3 <2',true],['2.0.0','>=1.2.3 <2',false],['2.0.0','>1',true],['1.9.9','>1',false],['1.2.9','<=1.2',true],['1.3.0','<=1.2',false],
   ['1.1.9','<1.2',true],['1.2.0','<1.2',false],['2.3.9','1.2 - 2.3',true],['2.4.0','1.2 - 2.3',false],['1.1.9','1.2 - 2.3',false],['2.3.4','1.2.3 - 2.3.4',true],['2.3.5','1.2.3 - 2.3.4',false],
   ['3.0.0','^1 || ^3',true],['2.0.0','^1 || ^3',false],['1.5.0','>= 1.2.3 < 2.0.0',true],['2.0.0-beta.1','^1.0.0',false],['1.2.4-rc.1','^1.2.3',false],['1.2.3-rc.2','>=1.2.3-rc.1 <1.3.0',true],
   ['1.2.3-rc.1','>=1.2.3-rc.2',false],['1.2.3-alpha','<1.2.3',false],['1.2.3-rc.10','~1.2.3-rc.2',true],['1.2.3-rc.10','>1.2.3-rc.9',true]])
   assert.equal(satisfies(v,r),want,`${v} in ${JSON.stringify(r)}`);
  for(let r of ['latest','git+https://example.invalid/y.git','npm:x@^1','file:../x','~>1.2','1.2.3.4','workspace:*','user/repo','>=1 ||| 2','https://example.invalid/x.tgz','1.2.3-'])assert.equal(parseRange(r),null,r);
 });
 await test('diamond A->B,C->D collapses to one D in topological order and D is marked present from .grave',()=>{
  let c=corpus('diamond',[P('a','1.0.0',{dependencies:{b:'^1',c:'^1'}}),P('b','1.0.0',{dependencies:{d:'^1'}}),P('c','1.0.0',{dependencies:{d:'~1.0.0'}}),P('d','1.0.0'),P('d','1.0.1'),P('d','2.0.0')]);
  let root=path.join(tmp,'plot-diamond'),objects=path.join(root,'.grave','objects');fs.mkdirSync(objects,{recursive:true});root=fs.realpathSync(root);
  const stamp=(name,component,host=['linux','x64'],extra={})=>{let d=path.join(fs.realpathSync(objects),name);fs.mkdirSync(d);let v={key:stable([{component,files:'npm-layer'},host,[]]),path:d,...extra};write(path.join(d,'.plot.json'),v);return v};
  let good=stamp('d-Ab12',{ecosystem:'npm',name:'d',version:'1.0.1'});
  stamp('a-Tomb',{ecosystem:'npm',name:'a',version:'1.0.0'});write(path.join(root,'.grave','tombstones','a-Tomb.json'),{path:'x',reason:'test',at:'now'});
  let copy=stamp('b-Copy',{ecosystem:'npm',name:'b',version:'1.0.0'});write(path.join(objects,'b-Copy','.plot.json'),{...copy,path:path.join(objects,'elsewhere')});
  fs.mkdirSync(path.join(objects,'c-Unstamped'));stamp('c-Win',{ecosystem:'npm',name:'c',version:'1.0.0'},['win32','x64']);
  write(path.join(root,'data.json'),{assets:{'npm-d':good}});
  let pl=plan(c,['a@^1'],{root});
  assert.equal(pl.ok,true,JSON.stringify(pl.diagnostics));assert.deepEqual(pl.nodes.map(n=>n.id),['a@1.0.0','b@1.0.0','c@1.0.0','d@1.0.1']);
  assert.deepEqual(pl.order,['d@1.0.1','b@1.0.0','c@1.0.0','a@1.0.0']);
  assert.equal(dep(node(pl,'b@1.0.0'),'d').resolved,'d@1.0.1');assert.equal(dep(node(pl,'c@1.0.0'),'d').resolved,'d@1.0.1');assert.equal(node(pl,'d@1.0.1').placement,'node_modules/d');
  assert.deepEqual(node(pl,'d@1.0.1').present,{object:good.path,key:good.key});
  for(let id of ['a@1.0.0','b@1.0.0','c@1.0.0'])assert.deepEqual(node(pl,id).present,{object:null,key:null},id);
  assert.deepEqual(plan(c,['a@^1'],{root,target:{...T,platform:'darwin'}}).nodes.find(n=>n.name==='d').present,{object:null,key:null});
  fs.rmSync(path.join(root,'data.json'));assert.equal(plan(c,['a@^1'],{root}).nodes.find(n=>n.name==='d').present.object,good.path,'directory scan finds stamped object without ledger');
 });
 await test('conflicting ranges keep distinct versions with nested placement and no shadowing',()=>{
  let c=corpus('conflict',[P('a','1.0.0',{dependencies:{b:'^1',c:'^1',e:'^1'}}),P('b','1.0.0',{dependencies:{d:'1.x'}}),P('c','1.0.0',{dependencies:{d:'^2'}}),P('e','1.0.0',{dependencies:{d:'^2'}}),P('d','1.4.0'),P('d','2.1.0'),
   P('r','1.0.0',{dependencies:{x:'^1',p:'^1',q:'^1',z:'^1'}}),P('x','1.0.0',{dependencies:{p:'^2',q:'^2'}}),P('p','1.0.0'),P('p','2.0.0',{dependencies:{z:'^1'}}),P('q','1.0.0'),P('q','2.0.0',{dependencies:{z:'^2'}}),P('z','1.0.0'),P('z','2.0.0')]);
  let pl=plan(c,['a']);assert.equal(pl.ok,true,JSON.stringify(pl.diagnostics));
  assert.equal(node(pl,'d@1.4.0').placement,'node_modules/d');assert.equal(node(pl,'d@2.1.0').placement,'node_modules/c/node_modules/d');
  let dup=node(pl,'d@2.1.0:node_modules/e/node_modules/d');assert.equal(dup.version,'2.1.0');
  assert.equal(dep(node(pl,'b@1.0.0'),'d').resolved,'d@1.4.0');assert.equal(dep(node(pl,'c@1.0.0'),'d').resolved,'d@2.1.0');assert.equal(dep(node(pl,'e@1.0.0'),'d').resolved,dup.id);
  assert.ok(pl.order.indexOf('d@2.1.0')<pl.order.indexOf('c@1.0.0')&&pl.order.indexOf(dup.id)<pl.order.indexOf('e@1.0.0'));
  let s=plan(c,['r']);assert.equal(s.ok,true);
  assert.equal(node(s,'p@2.0.0').placement,'node_modules/x/node_modules/p');assert.equal(dep(node(s,'p@2.0.0'),'z').resolved,'z@1.0.0');
  assert.equal(node(s,'z@2.0.0').placement,'node_modules/x/node_modules/q/node_modules/z','z@2 must not shadow the z@1 that p@2 already resolved');
  let bad=plan(c,['d@^1','d@^2']);assert.equal(bad.ok,false);assert.deepEqual(codes(bad),['range-unsatisfied']);
 });
 await test('peer dependencies resolve as siblings and bundled dependencies come from the package itself',()=>{
  let c=corpus('peer',peerCorpus()),pl=plan(c,['app']);assert.equal(pl.ok,true,JSON.stringify(pl.diagnostics));
  let plug=node(pl,'plugin@1.0.0');assert.deepEqual(dep(plug,'host'),{kind:'peer',name:'host',range:'^2',resolved:'host@2.1.0'});assert.deepEqual(dep(plug,'opt'),{kind:'peer',name:'opt',range:'*',resolved:null});
  assert.equal(node(pl,'host@2.1.0').placement,'node_modules/host');assert.ok(!pl.nodes.some(n=>n.name==='opt'),'optional peer is not auto-installed');
  let z=node(pl,'z@3.0.0'),w=node(pl,'w@1.0.0'),bund=node(pl,'bund@1.0.0');
  assert.deepEqual(dep(bund,'z'),{kind:'bundled',name:'z',range:'^3',resolved:'z@3.0.0'});
  assert.equal(z.placement,'node_modules/bund/node_modules/z');assert.deepEqual(z.source,{kind:'dir',path:path.join(bund.source.path,'node_modules','z'),integrity:null});
  assert.equal(w.placement,'node_modules/bund/node_modules/w');assert.equal(dep(z,'w').resolved,'w@1.0.0');
  assert.ok(!pl.nodes.some(n=>n.id==='z@1.0.0'||n.id==='w@9.0.0'),'corpus copies of bundled names are not used');
  assert.ok(pl.order.indexOf('host@2.1.0')<pl.order.indexOf('plugin@1.0.0'));
  let conflict=plan(c,['host@^1','plugin']);assert.equal(conflict.ok,false);assert.deepEqual(codes(conflict),['peer-unsatisfied']);assert.match(conflict.diagnostics[0].detail,/host@1\.0\.0/);
  let m=corpus('bund-miss',[P('q','1.0.0',{dependencies:{gone:'^1'},bundleDependencies:['gone']}),P('gone','1.0.0')]),miss=plan(m,['q']);
  assert.equal(miss.ok,false);assert.deepEqual(codes(miss),['missing']);assert.match(miss.diagnostics[0].detail,/bundled dependency gone/);
 });
 await test('conditional exports/imports resolve in manifest key order for import vs require',()=>{
  let exp={'./z':'./z.js','.':{node:{import:'./node.mjs',require:'./node.cjs'},import:'./esm.mjs',require:'./cjs.cjs',default:'./fallback.js'},'./feature':{require:'./f.cjs',import:'./f.mjs'},
   './a':[{worker:'./w.js'},'./a.js'],'./private/*':null,'./pat/*':'./src/*.js','./bad':'../escape.js'};
  let c=corpus('exports',[P('cond','1.0.0',{main:'cjs.cjs',exports:exp,imports:{'#dep':{node:'dep-pkg',default:'./poly.js'},'#int':'./internal.js'},bin:{'cond-cli':'./bin/cli.js'}}),
   P('ord-a','1.0.0',{exports:{import:'./i.mjs',node:'./n.js'}}),P('ord-b','1.0.0',{exports:{node:'./n.js',import:'./i.mjs'}}),
   P('num','1.0.0',{exports:{'.':{'1':'./one.js',default:'./d.js'}}}),P('mixed','1.0.0',{exports:{'.':'./x.js',import:'./y.mjs'}}),P('legacy','1.0.0',{main:'lib/index.js'})]);
  const ex=(conditions,id='cond@1.0.0')=>node(plan(c,['cond','ord-a','ord-b','num','mixed','legacy'],{conditions}),id).entry;
  let imp=ex(['node','import']);
  assert.deepEqual(Object.keys(imp.exports),Object.keys(exp),'subpath order is source order, not sorted');
  assert.deepEqual(imp.exports,{'./z':'./z.js','.':'./node.mjs','./feature':'./f.mjs','./a':'./a.js','./private/*':null,'./pat/*':'./src/*.js','./bad':null});
  assert.deepEqual(imp.imports,{'#dep':'dep-pkg','#int':'./internal.js'});assert.deepEqual(imp.bin,{'cond-cli':'bin/cli.js'});assert.equal(imp.main,'cjs.cjs');
  let req=ex(['node','require']);assert.equal(req.exports['.'],'./node.cjs');assert.equal(req.exports['./feature'],'./f.cjs');
  assert.equal(ex(['import']).exports['.'],'./esm.mjs');let br=ex(['browser']);assert.equal(br.exports['.'],'./fallback.js');assert.equal(br.exports['./feature'],null);assert.equal(br.imports['#dep'],'./poly.js');
  assert.equal(ex(['node','import'],'ord-a@1.0.0').exports['.'],'./i.mjs');assert.equal(ex(['node','import'],'ord-b@1.0.0').exports['.'],'./n.js');
  assert.equal(ex(['node','import'],'legacy@1.0.0').exports,null);assert.equal(ex(['node','import'],'legacy@1.0.0').main,'lib/index.js');
  let pl=plan(c,['cond','num','mixed'],{conditions:['node','import']}),text=serialize(pl),again=JSON.parse(text);
  assert.deepEqual(Object.keys(node(again,'cond@1.0.0').entry.exports),Object.keys(exp),'serialization preserves exports order');assert.equal(serialize(again),text);
  assert.equal(node(pl,'num@1.0.0').entry.exports['.'],null);assert.deepEqual(node(pl,'mixed@1.0.0').entry.exports,{});
  let forms=pl.unsupported.map(u=>u.where+' '+u.form);
  for(let x of ['cond@1.0.0#exports[./bad] invalid-target','num@1.0.0#exports[.] numeric-key','mixed@1.0.0#exports mixed-keys'])assert.ok(forms.includes(x),x+' in '+forms);
 });
 await test('os/cpu/libc/engines constraints prune host-incompatible branches with exact reasons',()=>{
  let c=corpus('host',[P('r','1.0.0',{dependencies:{native:'^1 || ^2',eng:'>=2',any:'^1',lib:'^1'},optionalDependencies:{fsevents:'^2',winonly:'^1'}}),
   P('native','2.0.0',{cpu:['arm64']}),P('native','1.5.0',{cpu:['x64','arm64']}),P('eng','3.0.0',{engines:{node:'>=99'}}),P('eng','2.0.0',{engines:{node:'>=18 <30',npm:'>=99'}}),
   P('any','1.0.0',{os:['!win32']}),P('lib','1.1.0',{libc:['musl']}),P('lib','1.0.0',{libc:['glibc']}),P('fsevents','2.3.3',{os:['darwin']}),P('winonly','1.0.0',{os:['win32'],cpu:['x64']}),P('only-arm','1.0.0',{cpu:['arm64']})]);
  let pl=plan(c,['r']);assert.equal(pl.ok,true,JSON.stringify(pl.diagnostics));
  assert.deepEqual(pl.nodes.map(n=>n.id),['any@1.0.0','eng@2.0.0','lib@1.0.0','native@1.5.0','r@1.0.0']);
  assert.deepEqual(pl.pruned,[{id:'eng@3.0.0',reason:'engines'},{id:'fsevents@2.3.3',reason:'os'},{id:'lib@1.1.0',reason:'libc'},{id:'native@2.0.0',reason:'cpu'},{id:'winonly@1.0.0',reason:'os'}]);
  assert.equal(dep(node(pl,'r@1.0.0'),'fsevents').resolved,null);
  let mac=plan(c,['r'],{target:{platform:'darwin',arch:'arm64',libc:null,node:'24.22.0'}});assert.equal(mac.ok,true);
  assert.deepEqual(mac.nodes.map(n=>n.id),['any@1.0.0','eng@2.0.0','fsevents@2.3.3','lib@1.1.0','native@2.0.0','r@1.0.0']);assert.deepEqual(mac.pruned,[{id:'eng@3.0.0',reason:'engines'},{id:'winonly@1.0.0',reason:'os'}]);
  let old=plan(c,['eng'],{target:{...T,node:'16.0.0'}});assert.equal(old.ok,false);assert.deepEqual(codes(old),['range-unsatisfied']);
  let arm=plan(c,['only-arm']);assert.equal(arm.ok,false);assert.match(arm.diagnostics[0].detail,/no host-compatible candidate \(1\.0\.0 cpu\)/);assert.deepEqual(arm.pruned,[{id:'only-arm@1.0.0',reason:'cpu'}]);
 });
 await test('absent or incompatible optional dependencies are pruned without failing the plan',()=>{
  let c=corpus('optional',[P('o','1.0.0',{dependencies:{present:'^1'},optionalDependencies:{ghost:'^1',old:'^5',weird:'github:u/r'}}),P('old','1.0.0'),P('present','1.0.0'),P('weird','1.0.0')]);
  let pl=plan(c,['o']);assert.equal(pl.ok,true,JSON.stringify(pl.diagnostics));assert.deepEqual(pl.diagnostics,[]);
  assert.deepEqual(pl.pruned,[{id:'ghost@^1',reason:'optional-absent'},{id:'old@^5',reason:'optional-incompatible'},{id:'weird@github:u/r',reason:'optional-incompatible'}]);
  assert.deepEqual(pl.nodes.map(n=>n.id),['o@1.0.0','present@1.0.0']);
  assert.deepEqual(dep(node(pl,'o@1.0.0'),'ghost'),{kind:'optional',name:'ghost',range:'^1',resolved:null});
  assert.ok(pl.unsupported.some(u=>u.where==='o@1.0.0#optionalDependencies.weird'&&u.form==='github:u/r'));
 });
 await test('.tgz corpus archives are read through gzip+USTAR (pax, scoped, bundled) without execution or extraction',()=>{
  let d=path.join(tmp,'tgz');fs.mkdirSync(path.join(d,'scope'),{recursive:true});let marker=path.join(tmp,'PWNED');
  let evil=`require('node:fs').writeFileSync(${JSON.stringify(marker)},'ran')`;
  write(path.join(d,'t-a-1.0.0.tgz'),tar([{name:'package/package.json',data:JSON.stringify(P('t-a','1.0.0',{dependencies:{'t-b':'^2','t-in':'^0.1'},bundleDependencies:['t-in'],scripts:{preinstall:'node -e "'+evil+'"',postinstall:'node -e "'+evil+'"'},main:'index.js'}))},
   {name:'package/index.js',data:evil},{name:'package/node_modules/t-in/package.json',data:JSON.stringify(P('t-in','0.1.0'))}]));
  write(path.join(d,'t-b-2.0.0.tgz'),tar([{name:'PaxHeader/t-b',type:'x',data:paxRec('path','package/package.json')},{name:'short-ustar-name',data:JSON.stringify(P('t-b','2.0.0',{dependencies:{'@s/t-c':'1'}}))}]));
  write(path.join(d,'scope','s-t-c-1.0.0.tgz'),tar([{name:'package/package.json',data:JSON.stringify(P('@s/t-c','1.0.0',{bin:'cli.js'}))}]));
  write(path.join(d,'corrupt.tgz'),Buffer.from('not a gzip stream at all'));write(path.join(d,'notar.tgz'),gzipSync('hello'));
  write(path.join(d,'evil.tgz'),tar([{name:'package/package.json',data:JSON.stringify(P('evil','1.0.0'))},{name:'package/../../escape',data:'x'}]));
  let before=listing(d),pl=plan(d,['t-a']);assert.equal(pl.ok,true,JSON.stringify(pl.diagnostics));
  let a=node(pl,'t-a@1.0.0'),file=path.join(fs.realpathSync(d),'t-a-1.0.0.tgz');
  assert.deepEqual(a.source,{kind:'tgz',path:file,integrity:sri(file),member:'package'});
  assert.deepEqual(node(pl,'t-in@0.1.0').source,{kind:'tgz',path:file,integrity:sri(file),member:'package/node_modules/t-in'});assert.equal(node(pl,'t-in@0.1.0').placement,'node_modules/t-a/node_modules/t-in');
  assert.equal(node(pl,'t-b@2.0.0').source.kind,'tgz');let sc=node(pl,'@s/t-c@1.0.0');assert.equal(sc.placement,'node_modules/@s/t-c');assert.deepEqual(sc.entry.bin,{'t-c':'cli.js'});
  assert.deepEqual(pl.order,['@s/t-c@1.0.0','t-b@2.0.0','t-in@0.1.0','t-a@1.0.0']);
  let bad=pl.unsupported.filter(u=>u.form==='archive').map(u=>path.basename(u.where)).sort();assert.deepEqual(bad,['corrupt.tgz','evil.tgz','notar.tgz']);
  assert.ok(!fs.existsSync(marker),'package code or lifecycle script executed');assert.deepEqual(listing(d),before,'planner wrote into the corpus');
  assert.deepEqual(inspectCorpus(d).packages.map(r=>r.name+'@'+r.version),['@s/t-c@1.0.0','t-a@1.0.0','t-b@2.0.0']);
 });
 await test('dependency cycles and missing mandatory dependencies fail closed with structured diagnostics',()=>{
  let c=corpus('cycle',[P('cy-a','1.0.0',{dependencies:{'cy-b':'^1'}}),P('cy-b','1.0.0',{dependencies:{'cy-a':'^1'}}),P('selfie','1.0.0',{dependencies:{selfie:'*'}}),
   P('m','1.0.0',{dependencies:{ghost:'^1',gone:'1.x'}}),P('m2','1.0.0',{dependencies:{'cy-b':'^9'}}),P('top','1.0.0',{dependencies:{'cy-a':'^1',leaf:'^1'}}),P('leaf','1.0.0')]);
  let cy=plan(c,['top']);assert.equal(cy.ok,false);assert.deepEqual(cy.diagnostics,[{code:'cycle',detail:'cy-a@1.0.0 -> cy-b@1.0.0 -> cy-a@1.0.0'}]);
  assert.deepEqual(cy.order,['leaf@1.0.0','cy-a@1.0.0','cy-b@1.0.0','top@1.0.0'],'acyclic prefix first, cycle remainder by id');
  assert.deepEqual(plan(c,['selfie']).diagnostics,[{code:'cycle',detail:'selfie@1.0.0 -> selfie@1.0.0'}]);
  let m=plan(c,['m','nope@^1']);assert.equal(m.ok,false);
  assert.deepEqual(m.diagnostics,[{code:'missing',detail:'ghost@^1 required by m@1.0.0: no package named ghost in corpus'},{code:'missing',detail:'gone@1.x required by m@1.0.0: no package named gone in corpus'},{code:'missing',detail:'nope@^1 required by requested: no package named nope in corpus'}]);
  assert.deepEqual(plan(c,['m2']).diagnostics,[{code:'range-unsatisfied',detail:'cy-b@^9 required by m2@1.0.0: available 1.0.0'}]);
 });
 await test('unsupported range forms are reported and never guessed',()=>{
  let forms={x:'latest',y:'git+https://example.invalid/y.git',z:'npm:x@^1',w:'~>1.2',v:'file:../v'};
  let c=corpus('unsup',[P('u','1.0.0',{dependencies:forms}),...Object.keys(forms).map(n=>P(n,'1.0.0'))]),pl=plan(c,['u','x@workspace:*']);
  assert.equal(pl.ok,false);assert.deepEqual(pl.nodes.map(n=>n.id),['u@1.0.0']);
  for(let [n,r] of Object.entries(forms)){assert.ok(pl.unsupported.some(u=>u.where===`u@1.0.0#dependencies.${n}`&&u.form===r&&/outside supported grammar/.test(u.reason)),n);assert.equal(dep(node(pl,'u@1.0.0'),n).resolved,null)}
  assert.ok(pl.unsupported.some(u=>u.where==='requested#x@workspace:*'));
  assert.equal(pl.diagnostics.filter(d=>d.code==='range-unsatisfied'&&/unsupported range form/.test(d.detail)).length,6);
 });
 await test('CLI and API output is byte-identical across repeated runs and corpus creation order',()=>{
  let c=path.join(tmp,'stable'),list=peerCorpus();corpus('stable',list);let root=path.join(tmp,'plot-diamond');
  let args=['plan','--corpus',c,'--root',root,'--conditions','node,import',...tflags,'app@^1'],one=cli(args),two=cli(args);
  assert.equal(one.status,0,one.stderr);assert.equal(one.stdout,two.stdout);
  assert.equal(one.stdout,serialize(planClosure({corpus:c,root,requested:['app@^1'],conditions:['node','import'],target:T})));
  fs.rmSync(c,{recursive:true});corpus('stable',[...list].reverse());assert.equal(cli(args).stdout,one.stdout,'readdir/creation order changed output');
  let pl=JSON.parse(one.stdout);assert.equal(pl.schema,'plot.closure/1');assert.deepEqual(Object.keys(pl),['diagnostics','nodes','ok','order','pruned','requested','schema','target','unsupported']);
  assert.deepEqual(pl.target,{arch:'x64',conditions:['node','import'],libc:'glibc',node:'24.22.0',platform:'linux',python:null});
  let fail=cli(['plan','--corpus',c,...tflags,'host@^1','plugin']);assert.equal(fail.status,1);assert.equal(JSON.parse(fail.stdout).ok,false);
  let usage=cli(['plan','--corpus',c,'--bogus','x']);assert.equal(usage.status,2);assert.match(usage.stderr,/unknown option --bogus/);
  let ins=cli(['inspect','--corpus',c]);assert.equal(ins.status,0,ins.stderr);assert.ok(JSON.parse(ins.stdout).packages.some(r=>r.name==='bund'&&r.bundled.includes('node_modules/z')));
 });
 await test('sample plan fixture for the assembler is generated from a real corpus',()=>{
  let dir=path.join(base,'tests','fixtures','closure');fs.rmSync(path.join(dir,'corpus'),{recursive:true,force:true});
  let c=corpus('corpus',[...peerCorpus(),P('app','1.0.0',{dependencies:{plugin:'^1',bund:'^1',left:'^1',right:'^1',lodashish:'^4'},optionalDependencies:{fsevents:'^2'},bin:{app:'./bin/app.js'},exports:{'.':{import:'./index.mjs',require:'./index.cjs'},'./package.json':'./package.json'}}),
   P('left','1.0.0',{dependencies:{shared:'^1'}}),P('right','1.0.0',{dependencies:{shared:'^2'}}),P('shared','1.2.0'),P('shared','2.0.1'),P('fsevents','2.3.3',{os:['darwin']})].filter(x=>!(x.name==='app'&&!x.bin)),dir);
  write(path.join(c,'lodashish-4.17.21.tgz'),tar([{name:'package/package.json',data:JSON.stringify(P('lodashish','4.17.21',{main:'lodash.js'}))},{name:'package/lodash.js',data:'module.exports={}'}]));
  let pl=plan(c,['app@^1']),file=path.join(dir,'sample-plan.json');write(file,serialize(pl));
  assert.equal(pl.ok,true,JSON.stringify(pl.diagnostics));assert.equal(node(pl,'shared@2.0.1').placement,'node_modules/right/node_modules/shared');
  assert.equal(node(pl,'lodashish@4.17.21').source.kind,'tgz');assert.deepEqual(pl.pruned,[{id:'fsevents@2.3.3',reason:'os'}]);
  assert.equal(fs.readFileSync(file,'utf8'),serialize(plan(c,['app@^1'])));
 });
}finally{
 let passed=checks.filter(x=>x.passed).length;console.log(`${passed}/${checks.length} cartographer checks`);fs.rmSync(tmp,{recursive:true,force:true});if(passed!==checks.length)process.exitCode=1;
}
