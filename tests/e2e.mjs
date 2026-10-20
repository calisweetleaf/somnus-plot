// P07-07 end-to-end composition on real processes: bootstrap (offline kit) -> owned Python and Node under
// .grave/host -> cartographer npm plan + assembler wheel plan -> seed recipes assemble both layers into
// .grave/objects -> resident jobs and environments consume them. Crash injection at seed publication,
// standby claim, environment activation, turn completion and prune. Every Python import in this suite
// runs on the owned runtime; the host python3 is never used. Writes evidence/e2e.json.
import * as fs from 'node:fs';
import * as path from 'node:path';
import os from 'node:os';
import assert from 'node:assert/strict';
import {spawn,spawnSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {planClosure} from '../capabilities/cartographer.mjs';
import {tar} from './helpers.mjs';
const base=path.resolve(new URL('..',import.meta.url).pathname),tmp=fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),'plot-e2e-'))),checks=[],notRun=[],facts={timings:{}},started=new Date().toISOString(),services=new Set();
const WHEELS="import zipfile,hashlib,base64,sys,sysconfig,pathlib\nout=pathlib.Path(sys.argv[1]);so=pathlib.Path(sys.argv[2])\ndef h(b):return 'sha256='+base64.urlsafe_b64encode(hashlib.sha256(b).digest()).rstrip(b'=').decode()\ndef wheel(name,ver,tag,files,purelib,requires=()):\n dist=name.replace('-','_');di=dist+'-'+ver+'.dist-info';files=dict(files)\n files[di+'/METADATA']=('Metadata-Version: 2.1\\nName: '+name+'\\nVersion: '+ver+'\\n'+''.join('Requires-Dist: '+r+'\\n' for r in requires)).encode()\n files[di+'/WHEEL']=('Wheel-Version: 1.0\\nGenerator: plot-e2e\\nRoot-Is-Purelib: '+purelib+'\\nTag: '+tag+'\\n').encode()\n rec=''.join(k+','+h(v)+','+str(len(v))+'\\n' for k,v in files.items())+di+'/RECORD,,\\n'\n with zipfile.ZipFile(out/(dist+'-'+ver+'-'+tag+'.whl'),'w',zipfile.ZIP_DEFLATED) as z:\n  for k,v in files.items():z.writestr(k,v)\n  z.writestr(di+'/RECORD',rec)\ncp='cp%d%d'%sys.version_info[:2]\nwheel('plot-native','1.0',cp+'-'+cp+'-'+sysconfig.get_platform().replace('-','_').replace('.','_'),{so.name:so.read_bytes()},'false')\nwheel('plot-e2e','1.0','py3-none-any',{'plot_e2e/__init__.py':b\"VERSION='1.0'\\nimport plot_native\\ndef total():\\n return plot_native.value()+5\\n\"},'true',['plot-native'])";
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),optional=p=>{try{return read(p)}catch{return null}},sleep=ms=>new Promise(r=>setTimeout(r,ms)),ms=t=>+(performance.now()-t).toFixed(1);
const alive=pid=>{try{process.kill(pid,0);return true}catch{return false}};
async function until(fn,limit=20000){const end=Date.now()+limit;let last;while(Date.now()<end){try{const r=await fn();if(r)return r}catch(e){last=e}await sleep(15)}throw last||Error('condition deadline')}
const test=async(name,fn)=>{const t=performance.now();try{const evidence=await fn();checks.push({name,passed:true,ms:ms(t),runtime:'owned',...(evidence?{evidence}:{})});console.log('PASS '+name+' [runtime owned]')}catch(e){checks.push({name,passed:false,runtime:'owned',error:e.stack});console.error('FAIL '+name+'\n'+e.stack)}};
const sh=(cmd,args,o={})=>{const r=spawnSync(cmd,args,{encoding:'utf8',timeout:120000,cwd:away,...o});if(r.error||r.status!==0)throw Error(`${cmd} ${args.slice(0,3).join(' ')}: exit ${r.status} ${r.signal||''}\n${r.stdout}\n${r.stderr}`);return r.stdout.trim()};
const away=fs.mkdirSync(path.join(tmp,'elsewhere'),{recursive:true})||path.join(tmp,'elsewhere');
let request,recover;

// ---- Stage 0: offline kit (from the pinned-upstream cache or an existing kit); no network required.
const cacheDir=path.join(os.tmpdir(),'plot-bootstrap-cache'),sharedKit=process.env.PLOT_KIT||path.join(os.tmpdir(),'plot-bootstrap-kit');
const kitHas=d=>{const k=optional(path.join(d,'kit.json'));return !!k&&['node','python'].every(t=>k.artifacts?.some(a=>a.tool===t&&a.platform===process.platform&&a.arch===process.arch&&fs.existsSync(path.join(d,a.file))))};
let kit=kitHas(sharedKit)?sharedKit:null;
if(!kit){const d=path.join(tmp,'kit'),r=spawnSync(process.execPath,[path.join(base,'capabilities/bootstrap.mjs'),'kit',d,'--hosts',`${process.platform}-${process.arch}`,'--quiet',...(fs.existsSync(cacheDir)?['--from',cacheDir]:[])],{encoding:'utf8',timeout:600000});if(r.status===0&&kitHas(d))kit=d}
const prereq={kit,cc:spawnSync('sh',['-c','command -v cc']).status===0,linux:process.platform==='linux'};
console.log('prerequisites '+JSON.stringify(prereq));
try{
if(!kit||!prereq.cc||!prereq.linux){notRun.push({what:'all e2e composition checks',why:!prereq.linux?'reference composition is Linux-only in v0.7 (other hosts: bootstrap/hosts/README.md)':!kit?'no offline kit: no network and no cache at '+cacheDir:'no C compiler for the native wheel fixture'});console.log('NOT RUN e2e: '+notRun[0].why)}
else{
 // ---- Stage 1: deploy the seed into a fresh root; every CLI below runs from a foreign cwd.
 const R=path.join(tmp,'root');fs.mkdirSync(path.join(R,'capabilities'),{recursive:true});
 for(const f of ['main.js','package.json','capabilities/resident.mjs','capabilities/assembler.mjs','capabilities/cartographer.mjs','capabilities/bootstrap.mjs'])fs.copyFileSync(path.join(base,f),path.join(R,f));
 fs.cpSync(path.join(base,'bootstrap'),path.join(R,'bootstrap'),{recursive:true});
 ({request,recover}=await import(pathToFileURL(path.join(R,'capabilities/resident.mjs'))));
 const cap=f=>path.join(R,'capabilities',f);let nodeBin,pyBase,acquired;
 await test('bootstrap acquires an owned Node and Python closure from the offline kit into <root>/.grave/host',async()=>{
  const t=performance.now();acquired=JSON.parse(sh(process.execPath,[cap('bootstrap.mjs'),'acquire','node','python','--root',R,'--kit',kit,'--offline','--quiet']));facts.timings.bootstrap_cold_ms=ms(t);
  const by=Object.fromEntries(acquired.results.map(x=>[x.id.split('-')[0],x]));for(const x of acquired.results){assert.equal(x.source,'kit');assert.ok(x.path.startsWith(path.join(R,'.grave/host')+path.sep),x.path)}
  nodeBin=path.join(by.node.path,'bin/node');pyBase=path.join(by.python.path,'bin/python3');
  assert.equal(sh(nodeBin,['-p','process.version']),'v'+by.node.id.split('-')[1]);
  const host=spawnSync('sh',['-c','command -v python3'],{encoding:'utf8'}).stdout.trim(),[exe,prefix]=JSON.parse(sh(pyBase,['-I','-c','import sys,json;print(json.dumps([sys.executable,sys.base_prefix]))']));
  assert.equal(fs.realpathSync(prefix),fs.realpathSync(by.python.path));if(host)assert.notEqual(fs.realpathSync(exe),fs.realpathSync(host),'owned runtime is not the host python3');
  return {node:nodeBin,python:pyBase,ms:facts.timings.bootstrap_cold_ms}});
 if(!nodeBin)throw Error('bootstrap failed; later stages need the owned runtime');

 // ---- Stage 2: banks and code-emitted plans (owned Python builds and targets the native wheel).
 const wheelBank=path.join(tmp,'bank/wheels'),corpus=path.join(tmp,'bank/npm'),plans=path.join(tmp,'plans');for(const d of [wheelBank,corpus,plans])fs.mkdirSync(d,{recursive:true});
 let wheelPlan=path.join(plans,'wheels.json'),npmPlan=path.join(plans,'npm.json');
 await test('cartographer and planWheels emit the closures; the native wheel is compiled against the owned runtime',async()=>{
  const [inc,suffix]=JSON.parse(sh(pyBase,['-I','-c','import sysconfig,json;print(json.dumps([sysconfig.get_path("include"),sysconfig.get_config_var("EXT_SUFFIX")]))']));
  assert.ok(fs.realpathSync(inc).startsWith(path.join(R,'.grave/host')),'headers come from the owned runtime');
  const c=path.join(tmp,'native.c'),so=path.join(tmp,'plot_native'+suffix);fs.writeFileSync(c,'#include <Python.h>\nstatic PyObject *value(PyObject*s,PyObject*a){return PyLong_FromLong(37);}\nstatic PyMethodDef methods[]={{"value",value,METH_NOARGS,"e2e fixture"},{NULL,NULL,0,NULL}};\nstatic struct PyModuleDef module={PyModuleDef_HEAD_INIT,"plot_native",NULL,-1,methods};\nPyMODINIT_FUNC PyInit_plot_native(void){return PyModule_Create(&module);}\n');
  sh('cc',['-shared','-fPIC','-I'+inc,c,'-o',so]);
  sh(pyBase,['-I','-c',WHEELS,wheelBank,so]);
  fs.writeFileSync(wheelPlan,sh(nodeBin,[cap('assembler.mjs'),'plan-wheels','--bank',wheelBank,'--python',pyBase,'plot-e2e']));const wp=read(wheelPlan);assert.equal(wp.ok,true);assert.deepEqual(wp.nodes.map(n=>n.name).sort(),['plot-e2e','plot-native']);
  const a=path.join(corpus,'a');fs.mkdirSync(a);fs.writeFileSync(path.join(a,'package.json'),JSON.stringify({name:'a',version:'1.2.0',main:'index.js',dependencies:{d:'^1'}}));fs.writeFileSync(path.join(a,'index.js'),"module.exports='a+'+require('d')\n");
  fs.writeFileSync(path.join(corpus,'d-1.0.1.tgz'),tar([{name:'package/package.json',data:JSON.stringify({name:'d',version:'1.0.1'})},{name:'package/index.js',data:"module.exports='d1'\n"}]));
  const np=planClosure({corpus,requested:['a@^1']});assert.equal(np.ok,true,JSON.stringify(np.diagnostics));fs.writeFileSync(npmPlan,JSON.stringify(np));
  return {wheels:wp.order,npm:np.order}});

 // ---- Stage 3: the seed assembles both layers through its own recipes.
 const asm=cap('assembler.mjs'),held={install:[{cmd:nodeBin,args:['-e',"const fs=require('node:fs');fs.writeFileSync('partial','1');if(process.env.E2E_HOLD){fs.writeFileSync(process.env.E2E_HOLD,'');setTimeout(()=>{},60000)}"]}]};
 const junk=v=>({install:[{cmd:nodeBin,args:['-e',`require('node:fs').writeFileSync('v','${v}')`]}]});
 const manifest=v=>fs.writeFileSync(path.join(R,'manifest.json'),JSON.stringify({id:'e2e',hosts:['node'],execution:'trusted',permissions:{spawn:true},tenants:{python:{command:pyBase,packages:[]}},
  capabilities:{wheels:{needs:['python'],install:[{cmd:nodeBin,args:[asm,'assemble','--into','${stage}','--bank',wheelBank,'--plan',wheelPlan,'--python','${cap:python}/bin/python3']}]},npm:{install:[{cmd:nodeBin,args:[asm,'assemble','--into','${stage}','--bank',corpus,'--plan',npmPlan]}]},held,junk:junk(v)},
  environment:{use:['python-packages','wheels','npm']},steps:[]}));
 manifest(1);const plot=(await import(pathToFileURL(path.join(R,'main.js')))).openPlot(R);let view;
 await test('seed recipes assemble the wheel and npm layers into .grave/objects over the owned venv (no pip)',async()=>{
  const t=performance.now();view=await plot.provision('default');facts.timings.seed_provision_ms=ms(t);const objects=path.join(R,'.grave/objects');
  for(const k of ['python','python-packages','wheels','npm'])assert.equal(path.dirname(view.assets[k].path),objects,k);
  assert.equal(fs.readdirSync(view.assets['python-packages'].path).filter(n=>n!=='.plot.json').length,0,'no pip-installed packages');
  const [base_,v]=JSON.parse(sh(view.python,['-I','-S','-c','import sys,json;sys.path.insert(0,sys.argv[1]);import plot_e2e;print(json.dumps([sys.base_prefix,plot_e2e.total()]))',view.assets.wheels.path]));
  assert.equal(v,42);assert.ok(fs.realpathSync(base_).startsWith(path.join(R,'.grave/host')));assert.ok(fs.existsSync(path.join(view.assets.wheels.path,'.plot-assembly.json')));
  assert.equal(sh(nodeBin,['-p',"require(process.argv[1]+'/node_modules/a')",view.assets.npm.path]),'a+d1');
  return {view:Object.fromEntries(Object.entries(view.assets).map(([k,a])=>[k,path.basename(a.path)])),ms:facts.timings.seed_provision_ms}});

 await test('crash at seed publication: SIGKILL mid-install leaves an unstamped stage that is archived by recovery and never adopted',async()=>{
  const mark=path.join(tmp,'mark-publication'),c=spawn(nodeBin,['--input-type=module','-e',`import {openPlot} from ${JSON.stringify(pathToFileURL(path.join(R,'main.js')).href)};await openPlot(${JSON.stringify(R)}).provision('crashy',{use:['held']})`],{cwd:away,detached:true,stdio:'ignore',env:{...process.env,E2E_HOLD:mark}});
  await until(()=>fs.existsSync(mark));const owner=read(path.join(R,'.grave/.lock/owner.json')),stage=owner.stages.at(-1);process.kill(-c.pid,'SIGKILL');await new Promise(r=>c.once('close',r));
  assert.ok(fs.existsSync(path.join(stage,'partial'))&&!fs.existsSync(path.join(stage,'.plot.json')));await assert.rejects(plot.provision('crashy',{use:['held']}),/busy/);
  const rec=recover(R);assert.equal(rec.state,'reconciled',JSON.stringify(rec));assert.ok(!fs.existsSync(path.join(R,'.grave/.lock')));
  const v=await plot.provision('crashy',{use:['held']});assert.notEqual(v.assets.held.path,stage);assert.ok(!fs.existsSync(path.join(stage,'.plot.json')),'stage stays unstamped');
  assert.equal(plot.view('default').assets.wheels.path,view.assets.wheels.path,'earlier view intact');return {stage:path.basename(stage),archived:path.basename(rec.archived)}});

 // ---- Stage 4: resident supervisor from the deployed copy under the owned Node, foreign cwd.
 const svcFile=path.join(R,'.grave/resident/service.json');
 async function server(env={}){const c=spawn(nodeBin,[cap('resident.mjs'),'--serve',R,path.join(R,'main.js')],{cwd:away,stdio:['ignore','ignore','pipe'],env:{...process.env,...env}});let err='';c.stderr.on('data',b=>err+=b);const done=new Promise(r=>c.once('close',(code,signal)=>r({code,signal,err})));const s={c,done};services.add(s);
  s.e=await until(async()=>{const e=read(svcFile);await request(e,{op:'ping'},300);return e});return s}
 async function kill(s){s.c.kill('SIGKILL');await s.done;services.delete(s)}
 async function stop(s){try{await request(s.e,{op:'stop'})}catch{}await s.done;services.delete(s)}
 const warm=async(e,n=2)=>until(async()=>(await request(e,{op:'ping'})).pool.idle>=n);
 const finish=(e,id)=>until(async()=>{const s=await request(e,{op:'inspect',id});return ['succeeded','failed','cancelled','timed_out','interrupted'].includes(s.state)&&s});
 const pyJob={cmd:'${cap:python}/bin/python3',args:['-I','-S','-c','import sys;sys.path.insert(0,sys.argv[1]);import plot_e2e;print(plot_e2e.total(),sys.base_prefix.startswith(sys.argv[2]))','${cap:wheels}',path.join(R,'.grave/host')]};
 const npmJob={cmd:nodeBin,args:['-e',"console.log(require(process.argv[1]+'/node_modules/a'))",'${cap:npm}']};
 let s=await server({PLOT_TEST_CLAIM_CRASH:'after-claimed:'+path.join(tmp,'mark-claim')}),e=s.e;
 await test('owned-runtime jobs: crash after the standby claim is adopted (interrupted, no output, no second worker); the next job runs both layers',async()=>{
  await warm(e);const j=await request(e,{op:'submit',name:'default',rid:'e2e-claim-1',steps:[pyJob]}),f=await finish(e,j.id);assert.equal(j.claimed,true);assert.equal(j.adopted,true);assert.equal(f.state,'interrupted');assert.ok(fs.existsSync(path.join(tmp,'mark-claim')));
  assert.equal((await request(e,{op:'output',id:j.id})).text,'');const pool=(await request(e,{op:'ping'})).pool;assert.equal(pool.adopted,1);assert.equal(pool.retried,0);assert.equal((await request(e,{op:'submit',name:'default',rid:'e2e-claim-1',steps:[pyJob]})).id,j.id,'rid retry never re-executes');
  await warm(e);const k=await request(e,{op:'submit',name:'default',rid:'e2e-claim-2',steps:[pyJob,npmJob]}),g=await finish(e,k.id);assert.equal(g.state,'succeeded',JSON.stringify(g));assert.equal((await request(e,{op:'output',id:k.id})).text,'42 True\na+d1\n');
  return {adopted:j.id,succeeded:k.id,path:k.path}});
 let lab;
 await test('environment over the assembled view: Python native wheel and Node npm layer in warm tenants; heap persists across turns',async()=>{
  lab=await request(e,{op:'activate',name:'lab',view:'default'},60000);assert.equal(lab.state,'active');assert.deepEqual(Object.keys(lab.tenants).sort(),['node','python']);
  const t=(rt,code,x={})=>request(e,{op:'interact',name:'lab',expectIncarnation:lab.incarnation,runtime:rt,code,...x},60000);
  const a=await t('python',`import sys\nsys.path.insert(0,${JSON.stringify(view.assets.wheels.path)})\nimport plot_e2e\nkept=plot_e2e.total()\nkept`);assert.equal(a.result,'42');assert.equal((await t('python','sys.base_prefix.startswith('+JSON.stringify(path.join(R,'.grave/host'))+')')).result,'True');
  const b=await t('node',"globalThis.__plot_session__.a=require(__plot_assets__.npm+'/node_modules/a')");assert.equal(b.result,"'a+d1'");assert.equal((await t('node','globalThis.__plot_session__.a')).result,"'a+d1'");
  return {incarnation:lab.incarnation}});
 await test('crash during activation: supervisor SIGKILL while the host starts; restart converges on one live host and the earlier heap survives',async()=>{
  const inc=path.join(R,'.grave/resident/envs/act/inc'),p=request(e,{op:'activate',name:'act',view:'default',runtimes:['node']},60000).catch(x=>x);
  await until(()=>fs.readdirSync(inc).some(n=>fs.existsSync(path.join(inc,n,'instance.json'))),20000);await kill(s);const first=await p;assert.ok(first instanceof Error,'activation reply cannot outlive its supervisor');
  s=await server({PLOT_TEST_TURN_CRASH:'after-record:'+path.join(tmp,'mark-turn-after')});e=s.e;
  const act=await request(e,{op:'activate',name:'act',view:'default',runtimes:['node']},60000);assert.equal(act.state,'active');
  const hosts=fs.readdirSync(inc).map(n=>optional(path.join(inc,n,'owner.json'))?.pid).filter(x=>x&&alive(x));assert.equal(hosts.length,1,'exactly one live host');
  assert.equal((await request(e,{op:'interact',name:'act',expectIncarnation:act.incarnation,runtime:'node',code:'1+1'})).result,'2');
  assert.equal((await request(e,{op:'interact',name:'lab',expectIncarnation:lab.incarnation,runtime:'python',code:'kept'})).result,'42','lab heap survived the supervisor crash');
  return {incarnations:fs.readdirSync(inc).length,existing:act.existing}});
 const effects=path.join(tmp,'effects');fs.mkdirSync(effects);
 await test('crash at turn completion after the record: the retried rid returns the recorded outcome; the effect ran once',async()=>{
  const tc=await request(e,{op:'activate',name:'tc1',view:'default',runtimes:['node']},60000),f=path.join(effects,'after');
  const body={op:'interact',name:'tc1',expectIncarnation:tc.incarnation,runtime:'node',rid:'e2e-turn-after',code:`require('node:fs').appendFileSync(${JSON.stringify(f)},'x');6*7`};
  await assert.rejects(request(e,body),/incarnation interrupted|unreachable/);const r=await request(e,body);assert.equal(r.retried,true);assert.equal(r.state,'succeeded');assert.equal(r.result,'42');assert.equal(fs.readFileSync(f,'utf8'),'x');
  await assert.rejects(request(e,{...body,code:'0'}),/request conflict/);const i=await request(e,{op:'env_inspect',name:'tc1'});assert.equal(i.state,'interrupted');return {turnId:r.turnId,state:i.state}});
 await kill(s);s=await server({PLOT_TEST_TURN_CRASH:'before-record:'+path.join(tmp,'mark-turn-before')});e=s.e;
 await test('crash at turn completion before the record: the retried rid reports interrupted/lost and never re-executes; reactivation is a new heap',async()=>{
  const tc=await request(e,{op:'activate',name:'tc2',view:'default',runtimes:['node']},60000),f=path.join(effects,'before');
  const body={op:'interact',name:'tc2',expectIncarnation:tc.incarnation,runtime:'node',rid:'e2e-turn-before',code:`globalThis.__plot_session__.n=1;require('node:fs').appendFileSync(${JSON.stringify(f)},'y');1`};
  await assert.rejects(request(e,body),/incarnation interrupted|unreachable/);let err;try{await request(e,body)}catch(x){err=x}assert.match(err?.message||'',/incarnation interrupted/);assert.equal(err.stateEffect,'lost');assert.ok(err.turnId);
  assert.equal(fs.readFileSync(f,'utf8'),'y');const n=await request(e,{op:'activate',name:'tc2',view:'default',runtimes:['node']},60000);assert.notEqual(n.incarnation,tc.incarnation);assert.equal(n.heap,'new');
  assert.equal((await request(e,{op:'interact',name:'tc2',expectIncarnation:n.incarnation,runtime:'node',code:'typeof globalThis.__plot_session__.n'})).result,"'undefined'");return {lost:err.turnId}});

 // ---- Stage 5: prune crashes. Stale objects come from rewritten junk recipes.
 const pruneArgs=['{"apply":true,"cache":{"maxAgeDays":0}}'],pinned=()=>fs.readdirSync(path.join(R,'.grave/pins')).map(n=>optional(path.join(R,'.grave/pins',n))).filter(x=>x?.kind==='env'&&x.ref==='lab.'+lab.incarnation);
 async function stale(v){manifest(v);const before=(await plot.provision('junk',{use:['junk']})).assets.junk.path;manifest(v+1);await plot.provision('junk',{use:['junk']});return before}
 for(const stage of ['moved','intents'])await test(`crash during prune (${stage}): recovery then prune ${stage==='moved'?'finishes the deletion':'withdraws the intent and deletes anew'}; pinned environment objects survive`,async()=>{
  const old=await stale(stage==='moved'?1:3),mark=path.join(tmp,'mark-prune-'+stage);
  const r=spawnSync(nodeBin,[cap('resident.mjs'),'--root',R,'prune',...pruneArgs],{cwd:away,encoding:'utf8',env:{...process.env,PLOT_TEST_PRUNE_CRASH:stage+':'+mark},timeout:60000});assert.equal(r.signal,'SIGKILL',r.stderr);assert.ok(fs.existsSync(mark));
  const tomb=path.join(R,'.grave/tombstones',path.basename(old));assert.ok(fs.existsSync(tomb+'.json'),'intent durable');assert.equal(fs.existsSync(tomb),stage==='moved');assert.equal(fs.existsSync(old),stage!=='moved');
  const rec=recover(R);assert.equal(rec.state,'reconciled',JSON.stringify(rec));
  const a=JSON.parse(sh(nodeBin,[cap('resident.mjs'),'--root',R,'prune',...pruneArgs]));
  assert.ok(a.recovered.some(x=>x.path===old&&x.action===(stage==='moved'?'finish-deletion':'intent-withdrawn')),JSON.stringify(a.recovered));assert.ok(a.deleted.includes(old));assert.ok(!fs.existsSync(old)&&!fs.existsSync(tomb)&&!fs.existsSync(tomb+'.json'));
  const pin=pinned();assert.equal(pin.length,1);for(const x of pin[0].paths)assert.ok(fs.existsSync(x),'pinned '+x);
  assert.equal((await request(e,{op:'interact',name:'lab',expectIncarnation:lab.incarnation,runtime:'python',code:'plot_e2e.total()'})).result,'42');
  return {deleted:a.deleted.length,recovered:a.recovered.filter(x=>x.path===old)}});

 await test('teardown: deactivate stops every host and tenant; supervisor stop is clean',async()=>{
  const pids=[];for(const n of ['lab','act','tc2']){const i=await request(e,{op:'env_inspect',name:n});const o=optional(i.paths.owner);if(o)pids.push(o.pid);for(const t of Object.values(i.tenants||{}))pids.push(t.pid);await request(e,{op:'deactivate',name:n})}
  await stop(s);await until(()=>pids.every(p=>!alive(p)));return {stopped:pids.length}});
}
}finally{
 for(const x of services){x.c.kill('SIGKILL');await x.done}
 const report={started_at:started,finished_at:new Date().toISOString(),node:process.version,platform:process.platform,arch:process.arch,runtime:'owned',kit,total:checks.length,passed:checks.filter(c=>c.passed).length,not_run:notRun,checks,facts};
 fs.mkdirSync(path.join(base,'evidence'),{recursive:true});fs.writeFileSync(path.join(base,'evidence/e2e.json'),JSON.stringify(report,null,2)+'\n');
 console.log(`${report.passed}/${report.total} e2e checks`+(notRun.length?` (NOT RUN: ${notRun.map(n=>n.what).join('; ')})`:''));if(report.passed!==report.total)process.exitCode=1;
 try{fs.rmSync(tmp,{recursive:true,force:true})}catch{}
}
