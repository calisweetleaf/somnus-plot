// v0.7 benchmark workloads, frozen in docs/V07-CONTRACTS.md section 12 before tuning. Real sockets, standby
// workers, Environment Hosts, tenants and child processes; every sample is kept (nearest-rank percentiles,
// no trimming). Writes evidence/v07-benchmark.json. Frozen 6 ms gates are recorded as PASS/FAIL in the
// evidence; the process fails only on correctness failures or an invalid run, so an unmet gate stays visible
// as an open gate instead of blocking the evidence that shows it.
import * as fs from 'node:fs';
import * as path from 'node:path';
import os from 'node:os';
import cp from 'node:child_process';
import {syncBuiltinESMExports} from 'node:module';
import assert from 'node:assert/strict';
import {openPlot} from '../main.js';
import {request} from '../capabilities/resident.mjs';
import {python,wheels,command} from './helpers.mjs';
const base=path.resolve(new URL('..',import.meta.url).pathname),core=path.join(base,'main.js'),module=path.join(base,'capabilities/resident.mjs'),node=process.execPath;
const tmp=fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),'plot-v07-bench-'))),started=new Date().toISOString(),services=new Set(),failures=[],notRun=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms)),read=p=>JSON.parse(fs.readFileSync(p,'utf8')),now=()=>Number(process.hrtime.bigint())/1e6;
const QUICK=process.env.PLOT_BENCH_QUICK==='1';// smoke the harness only; QUICK evidence is marked invalid
const stats=a=>{const s=a.slice().sort((x,y)=>x-y),q=p=>s.length?s[Math.ceil(p*s.length)-1]:null;return {n:s.length,p50_ms:q(.5),p95_ms:q(.95),p99_ms:q(.99),max_ms:s.length?s.at(-1):null,mean_ms:s.length?s.reduce((x,y)=>x+y,0)/s.length:null}};
const series=a=>({summary:stats(a),samples_ms:a});
async function until(fn,limit=30000,step=2){const end=Date.now()+limit;let last;while(Date.now()<end){try{const r=await fn();if(r)return r}catch(e){last=e}await sleep(step)}throw last||Error('condition deadline')}
function mulberry32(a){return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296}}
function poisson(seed,rate,seconds,minCount=0){const r=mulberry32(seed),out=[];let t=0;for(;;){t+=-Math.log(1-r())/rate*1000;if(t>=seconds*1000&&out.length>=minCount)break;out.push(t)}return out}
const pkg={install:[{cmd:node,args:['-e',"const fs=require('node:fs');fs.writeFileSync('package.json',JSON.stringify({name:'plot-acquired',version:'1.0.0',main:'index.js'}));fs.writeFileSync('index.js','module.exports={add:(a,b)=>a+b,version:\"1.0.0\"}')"]}]};
async function server(root,env={}){const c=cp.spawn(node,[module,'--serve',root,core],{stdio:['ignore','ignore','pipe'],env:{...process.env,...env}});let err='';c.stderr.on('data',b=>err+=b);const done=new Promise(r=>c.once('close',()=>r(err)));const s={c,done};services.add(s);
 s.e=await until(async()=>{const e=read(path.join(root,'.grave/resident/service.json'));await request(e,{op:'ping'},300);return e},20000,20);return s}
async function stop(s){try{await request(s.e,{op:'stop'})}catch{}await s.done;services.delete(s)}
const ping=async e=>(await request(e,{op:'ping'})).pool;
const terminal=st=>['succeeded','failed','cancelled','timed_out','interrupted'].includes(st);
const okJob=[{cmd:node,args:['-e',"process.stdout.write('ok')"]}];
function root(name,m){const r=path.join(tmp,name);fs.mkdirSync(r);fs.writeFileSync(path.join(r,'manifest.json'),JSON.stringify({hosts:['node'],execution:'trusted',permissions:{spawn:true},...m}));return r}
const metrics={},gates={},facts={};
try{
 // ---- multi_version_switch: v1 and v2 package layers both acquired; spawn count measured, must be 0.
 {const wd=path.join(tmp,'wheels');fs.mkdirSync(wd);const dist=wheels(wd),r=root('switch',{tenants:{python:{command:python,packages:[dist.one],pip:['--no-index']}},capabilities:{},environment:{use:['python-packages']},steps:[]}),plot=openPlot(r);
  const v1={python:{packages:[dist.one]}},v2={python:{packages:[dist.two]}};await plot.provision('v1',v1);await plot.provision('v2',v2);
  const real={};let spawned=0;for(const k of ['spawn','spawnSync','exec','execSync','execFile','execFileSync','fork']){real[k]=cp[k];cp[k]=(...a)=>{spawned++;return real[k](...a)}}syncBuiltinESMExports();
  let lat=[],control;try{await plot.provision('control-'+Date.now(),{python:{packages:[dist.native]}});control=spawned;spawned=0;
   for(let i=0;i<(QUICK?30:300);i++){const t=now();await plot.provision('switch',i%2?v2:v1);lat.push(now()-t)}}finally{Object.assign(cp,real);syncBuiltinESMExports()}
  assert.ok(control>0,'spawn counter positive control');const last=plot.view('switch');const ver=command(last.python,['-I','-S','-c','import sys;sys.path.insert(0,sys.argv[1]);import plot_sample;print(plot_sample.VERSION)',last.packages]);assert.equal(ver,(lat.length-1)%2?'2.0':'1.0');metrics.multi_version_switch={...series(lat),child_spawns:spawned,control_spawns:control,runtime:'shallow-host'};gates.multi_version_switch_p95_under_6_ms=stats(lat).p95_ms<6&&spawned===0;if(spawned!==0)failures.push('multi_version_switch spawned '+spawned)}

 // ---- cold_acquisition: distinct capabilities, real installer child + publication each.
 {const n=QUICK?5:40,caps=Object.fromEntries(Array.from({length:n},(_,i)=>['cold'+i,{install:[{cmd:node,args:['-e',`require('node:fs').writeFileSync('v','${i}')`]}]}])),r=root('cold',{capabilities:caps,environment:{use:[]},steps:[]}),plot=openPlot(r),lat=[];
  for(let i=0;i<n;i++){const t=now();const v=await plot.provision('c'+i,{use:['cold'+i]});lat.push(now()-t);assert.equal(fs.readFileSync(path.join(v.assets['cold'+i].path,'v'),'utf8'),String(i))}metrics.cold_acquisition=series(lat)}

 // ---- resident rows on one root with the default pool (ready 2, maxStarting 2).
 const R=root('resident',{capabilities:{pkg},environment:{use:[]},steps:[]});await openPlot(R).provision('native',{use:[]});
 let s=await server(R);
 {const reply=[],ctrl=[],answer=[],paths={};const n=QUICK?30:300;
  for(let i=0;i<n;i++){await until(async()=>{const p=await ping(s.e);return p.idle>=2&&p.starting===0},20000,5);const t=now(),j=await request(s.e,{op:'submit',name:'native',rid:'dsc-'+i,steps:[{cmd:node,args:['-e','setTimeout(()=>{},300)']}]}),t1=now();
   const c=read(path.join(R,'.grave/resident/jobs',j.id,'claimed.json'));assert.ok(c.port&&c.token);const t2=now();await request({port:c.port,token:c.token},{op:'inspect',id:j.id},2000);const t3=now();paths[j.path]=(paths[j.path]||0)+1;if(j.path==='standby'){reply.push(t1-t);ctrl.push(t2-t);answer.push(t3-t)}}
  metrics.durable_submit_and_claim={reply:series(reply),control_ready:series(ctrl),control_answer:series(answer),paths,scope:'Warm = pool at ready 2 with nothing starting before each sample (waits outside the timed window); only standby-path samples are in the series. reply: request start -> durable claimed reply. control_ready: request start -> the job worker control endpoint record (claimed.json port+token, written before the reply) read by the client; v0.6 defined control readiness as this private endpoint record. control_answer (no gate): request start -> first authenticated inspect answered by the worker, one extra RPC while the worker spawns its child.'};
  gates.durable_submit_and_claim_p95_under_6_ms=stats(reply).p95_ms<6&&stats(ctrl).p95_ms<6}
 {const out={};for(const b of [2,8,16,32]){await until(async()=>{const p=await ping(s.e);return p.idle>=2&&p.starting===0},20000,10);const before=await ping(s.e);const t=now();
   const rs=await Promise.allSettled(Array.from({length:b},(_,i)=>{const t0=now();return request(s.e,{op:'submit',name:'native',rid:`burst-${b}-${i}`,steps:okJob}).then(j=>({j,ms:now()-t0}))}));const after=await ping(s.e);
   const ok=rs.filter(x=>x.status==='fulfilled').map(x=>x.value),rej=rs.filter(x=>x.status==='rejected').map(x=>x.reason);
   for(const {j} of ok){const f=await until(async()=>{const x=await request(s.e,{op:'inspect',id:j.id});return terminal(x.state)&&x},30000,10);if(f.state!=='succeeded'||(await request(s.e,{op:'output',id:j.id})).text!=='ok')failures.push('burst '+b+' job '+j.id+' '+f.state)}
   out[b]={offered:b,accepted:ok.length,rejected:rej.length,rejected_retryable:rej.filter(e=>e.retryable).length,rejections:[...new Set(rej.map(e=>e.message))],paths:ok.reduce((a,{j})=>(a[j.path]=(a[j.path]||0)+1,a),{}),accepted_latency:stats(ok.map(x=>x.ms)),wall_ms:now()-t,peakStarting:after.peakStarting,maxStarting:after.maxStarting,emptyDelta:after.empty-before.empty};
   if(ok.length+rej.length!==b||after.peakStarting>after.maxStarting)failures.push('burst '+b+' unaccounted or unbounded')}metrics.burst_submit=out;gates.burst_submit_accounted_bounded=!failures.some(f=>f.startsWith('burst'))}
 {const lat=[];for(let i=0;i<(QUICK?5:40);i++){await until(async()=>{const p=await ping(s.e);return p.idle>=2&&p.starting===0},20000,5);await request(s.e,{op:'submit',name:'native',rid:'rep-'+i,steps:okJob});const t=now();await until(async()=>(await ping(s.e)).idle>=2,20000,2);lat.push(now()-t)}metrics.replenish={...series(lat),scope:'claimed reply -> pool idle back at ready=2, observed by ping polling every 2 ms'}}
 {const lat=[];for(let i=0;i<(QUICK?5:40);i++){await until(async()=>(await ping(s.e)).idle>=1,20000,5);const t=now(),j=await request(s.e,{op:'submit',name:'native',rid:'cij-'+i,steps:okJob});const f=await until(async()=>{const x=await request(s.e,{op:'inspect',id:j.id});return terminal(x.state)&&x},30000,2);lat.push(now()-t);if(f.state!=='succeeded'||(await request(s.e,{op:'output',id:j.id})).text!=='ok')failures.push('complete job '+j.id)}metrics.complete_isolated_job={...series(lat),scope:'request start -> terminal succeeded observed by inspect polling every 2 ms; job = node -e process.stdout.write(ok)'}}
 await stop(s);
 {s=await server(R,{PLOT_RESIDENT_READY:'0'});const lat=[],paths={};for(let i=0;i<(QUICK?5:40);i++){await until(async()=>(await ping(s.e)).starting===0,20000,5);const t=now(),j=await request(s.e,{op:'submit',name:'native',rid:'cold-'+i,steps:okJob});lat.push(now()-t);paths[j.path]=(paths[j.path]||0)+1}metrics.cold_worker_spawn={...series(lat),paths,scope:'PLOT_RESIDENT_READY=0: request start -> reply after a worker is spawned for this job and claims it'};await stop(s)}

 // ---- sustained_submit: open-loop Poisson 10/s for 120 s (>=1,200 offered), seed 0x5eed07, empty-pool start.
 async function openLoop(e,offsets,tag){const out=new Array(offsets.length),inflight=[],lag=[];const t0=now();
  for(let i=0;i<offsets.length;i++){const due=t0+offsets[i],w=due-now();if(w>1)await sleep(w-1);while(now()<due);lag.push(now()-due);const ts=now();
   inflight.push(request(e,{op:'submit',name:'native',rid:`${tag}-${i}`,steps:okJob},60000).then(j=>{out[i]={ok:true,ms:now()-ts,id:j.id,path:j.path}},x=>{out[i]={ok:false,ms:now()-ts,error:x.message,retryable:!!x.retryable}}))}
  await Promise.all(inflight);return {out,lag,wall:now()-t0}}
 async function verify(e,out,limit=120000){let bad=0;const end=Date.now()+limit;for(const o of out.filter(x=>x.ok)){let f;while(Date.now()<end){f=await request(e,{op:'inspect',id:o.id});if(terminal(f.state))break;await sleep(20)}if(f?.state!=='succeeded'||(await request(e,{op:'output',id:o.id})).text!=='ok'){bad++;o.final=f?.state||'unknown'}}return bad}
 {const S=root('sustained',{environment:{use:[]},steps:[]});await openPlot(S).provision('native',{use:[]});const offsets=poisson(0x5eed07,10,QUICK?10:120,QUICK?0:1200);
  s=await server(S);const p0=await ping(s.e),emptyAtStart=p0.idle===0;const obs=[];let sampling=true;const sampler=(async()=>{while(sampling){try{const p=await ping(s.e);obs.push({t:now(),idle:p.idle,starting:p.starting,waiting:p.waiting})}catch{}await sleep(250)}})();
  const run=await openLoop(s.e,offsets,'sus');sampling=false;await sampler;const p1=await ping(s.e),bad=await verify(s.e,run.out);
  const ok=run.out.filter(x=>x.ok),acc=ok.length/run.out.length,empties=p1.empty-p0.empty,idleZero=obs.filter(o=>o.idle===0).length;
  metrics.sustained_submit={offered:run.out.length,accepted:ok.length,acceptance:acc,rejected:run.out.length-ok.length,rejections:run.out.filter(x=>!x.ok).reduce((a,x)=>(a[x.error]=(a[x.error]||0)+1,a),{}),correctness_failures:bad,successful:series(ok.map(x=>x.ms)),paths:ok.reduce((a,x)=>(a[x.path]=(a[x.path]||0)+1,a),{}),
   schedule:{seed:'0x5eed07',rate_per_s:10,duration_s:+(offsets.at(-1)/1000).toFixed(3),wall_ms:run.wall,dispatch_lag:stats(run.lag)},pool_empty:{at_start:emptyAtStart,lease_found_no_idle:empties,sampled_idle_zero:idleZero,samples:obs.length},valid:empties>0&&!QUICK};
  if(!(empties>0))failures.push('sustained_submit invalid: default pool never observed empty');if(bad)failures.push('sustained_submit correctness failures '+bad);
  gates.sustained_submit={successful_p95_under_6_ms:stats(ok.map(x=>x.ms)).p95_ms<6,acceptance_at_least_99_pct:acc>=0.99,zero_correctness_failures:bad===0,valid:empties>0};
  // ---- saturation: ramp 5 -> 40/s, step 5/s, 30 s each, then drain; same supervisor, fresh rids.
  const steps=[];for(let rate=5;rate<=40;rate+=5){const off=poisson(0x5eed07+rate,rate,QUICK?3:30);const p=await ping(s.e),r=await openLoop(s.e,off,'sat'+rate),q=await ping(s.e);const okr=r.out.filter(x=>x.ok);
   steps.push({rate_per_s:rate,offered:r.out.length,accepted:okr.length,acceptance:okr.length/r.out.length,successful:stats(okr.map(x=>x.ms)),paths:okr.reduce((a,x)=>(a[x.path]=(a[x.path]||0)+1,a),{}),emptyDelta:q.empty-p.empty,dispatch_lag_p95_ms:stats(r.lag).p95_ms,out:r.out})}
  const drainT=now();for(const st of steps){st.correctness_failures=await verify(s.e,st.out,180000);delete st.out}const drain=now()-drainT;
  let maxStable=null;for(const st of steps){if(st.acceptance>=0.99&&st.correctness_failures===0)maxStable=st.rate_per_s;else break}
  metrics.saturation={steps,drain_ms:drain,max_stable_rate_per_s:maxStable,stable_rule:'highest step R such that every step <= R had acceptance >= 99% and zero correctness failures after drain'};
  if(steps.some(st=>st.correctness_failures))failures.push('saturation correctness failures');await stop(s)}

 // ---- warm_env_interact: Python native call and Node session + acquired package, one incarnation.
 {const wd=path.join(tmp,'wheels-env');fs.mkdirSync(wd);const dist=wheels(wd),E=root('envs',{tenants:{python:{command:python,packages:[dist.one,dist.native],pip:['--no-index']}},capabilities:{pkg},environment:{use:[]},steps:[]});
  await openPlot(E).provision('one',{use:['python-packages','pkg']});s=await server(E);const env=await request(s.e,{op:'activate',name:'bench',view:'one'},60000);
  for(const [rt,code,want] of [['python','import plot_native\nplot_native.value()','37'],['node',"(globalThis.__plot_session__.n=(globalThis.__plot_session__.n||0)+1,require(__plot_assets__.pkg+'/index.js').add(2,3))",'5']]){const lat=[];
   for(let i=0;i<(QUICK?30:320);i++){const t=now(),r=await request(s.e,{op:'interact',name:'bench',expectIncarnation:env.incarnation,runtime:rt,code});const ms=now()-t;if(r.state!=='succeeded'||r.result!==want)failures.push('env '+rt+' '+r.state+' '+r.result);if(i>=20)lat.push(ms)}
   metrics['warm_env_interact_'+rt]={...series(lat),warmup_discarded:20,runtime:rt==='python'?'shallow-host':'node',scope:'request start -> turn outcome over a fresh authenticated supervisor socket, proxied to the Environment Host'};gates['warm_env_interact_'+rt+'_p95_under_6_ms']=stats(lat).p95_ms<6}
  const asset=fs.realpathSync((await openPlot(E).view('one')).assets.pkg.path);assert.ok(asset.startsWith(fs.realpathSync(path.join(E,'.grave/objects'))));
  await request(s.e,{op:'deactivate',name:'bench'});await stop(s)}

 // ---- bootstrap_cold: Node from the offline kit into a fresh root each time.
 {const kit=process.env.PLOT_KIT||path.join(os.tmpdir(),'plot-bootstrap-kit');if(!fs.existsSync(path.join(kit,'kit.json')))notRun.push({row:'bootstrap_cold',why:'no offline kit at '+kit+' (run tests/bootstrap.mjs once to build it)'});
  else{const lat=[];for(let i=0;i<(QUICK?3:40);i++){const r=path.join(tmp,'boot-'+i);fs.mkdirSync(r);const t=now(),x=cp.spawnSync(node,[path.join(base,'capabilities/bootstrap.mjs'),'acquire','node','--root',r,'--kit',kit,'--offline','--quiet'],{encoding:'utf8',timeout:120000});lat.push(now()-t);if(x.status!==0||JSON.parse(x.stdout).results[0].action!=='acquired')failures.push('bootstrap_cold '+i+': '+x.stderr);fs.rmSync(r,{recursive:true,force:true})}metrics.bootstrap_cold={...series(lat),scope:'fresh process: verify sha256, extract pinned Node archive into <root>/.grave/host, completion marker'}}}
}catch(e){failures.push('harness: '+e.stack)}
finally{
 for(const x of services){x.c.kill('SIGKILL');await x.done}
 const summary=Object.fromEntries(Object.entries(metrics).map(([k,v])=>[k,v.summary||(v.reply?{reply:v.reply.summary,control_ready:v.control_ready.summary,control_answer:v.control_answer.summary}:v.successful?{successful:v.successful.summary,acceptance:v.acceptance,offered:v.offered,pool_empty:v.pool_empty}:k==='saturation'?{max_stable_rate_per_s:v.max_stable_rate_per_s,steps:v.steps.map(s=>[s.rate_per_s,+s.acceptance.toFixed(4),s.successful.p95_ms])}:k==='burst_submit'?Object.fromEntries(Object.entries(v).map(([b,x])=>[b,[x.accepted,x.rejected,x.peakStarting]])):undefined)]));
 const report={started_at:started,finished_at:new Date().toISOString(),quick:QUICK,valid:!QUICK&&!failures.length,environment:{platform:process.platform,arch:process.arch,release:os.release(),node:process.version,cpu:os.cpus()[0]?.model,cpu_count:os.cpus().length,loadavg_at_start:os.loadavg(),core_bytes:fs.statSync(core).size,resident_bytes:fs.statSync(module).size},contract:'docs/V07-CONTRACTS.md section 12 (frozen)',percentiles:'nearest-rank over all successful samples, process.hrtime.bigint from client request initiation',metrics,gates,not_run:notRun,failures};
 if(!QUICK||process.env.PLOT_BENCH_WRITE==='1'){fs.mkdirSync(path.join(base,'evidence'),{recursive:true});fs.writeFileSync(path.join(base,'evidence/v07-benchmark.json'),JSON.stringify(report,null,1)+'\n')}
 console.log(JSON.stringify({summary,gates,not_run:notRun,failures},null,1));if(failures.length)process.exitCode=1;
 fs.rmSync(tmp,{recursive:true,force:true})}
