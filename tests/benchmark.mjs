// Persisted provisioning of executable views, with acquisition, CLI startup,
// and interpreter invocation reported as separate operations.
import * as fs from 'node:fs';
import * as path from 'node:path';
import os from 'node:os';
import assert from 'node:assert/strict';
import {openPlot} from '../main.js';
import {base,python,scratch,fixture,cli,must,command,wheels} from './helpers.mjs';
const tmp=scratch(),started=new Date().toISOString();
function stats(ms){let s=ms.slice().sort((a,b)=>a-b);let q=n=>s[Math.min(s.length-1,Math.ceil(s.length*n)-1)];return {n:s.length,p50_ms:q(.5),p95_ms:q(.95),p99_ms:q(.99),max_ms:s.at(-1),mean_ms:s.reduce((a,b)=>a+b,0)/s.length}}
async function measure(n,fn){let values=[];for(let i=0;i<n;i++){let t=performance.now();await fn(i);values.push(performance.now()-t)}return {summary:stats(values),samples_ms:values}}
try{
 let wheelDir=path.join(tmp,'wheels');fs.mkdirSync(wheelDir);let dist=wheels(wheelDir);
 let root=fixture(tmp,'bench',{tenants:{python:{command:python,depth:'shallow',packages:[dist.one,dist.native],pip:['--no-index']}},capabilities:{dataset:{install:[{cmd:process.execPath,args:['-e',"require('node:fs').writeFileSync('values.json',JSON.stringify([11,23,37,43]))"]}]},analysis:{needs:['dataset','python-packages'],install:[{cmd:process.execPath,args:['-e',"require('node:fs').writeFileSync('ready.txt','ready')"]}]}},environment:{use:['analysis']}}),plot=openPlot(root);
 let t=performance.now(),first=await plot.provision('seed'),cold=performance.now()-t;
 const verify=name=>plot.run(name,[{cmd:'python',args:['-c',`import plot_sample,plot_native,importlib.metadata as m,json,pathlib,os;assert plot_sample.VERSION=='1.0';assert plot_native.value()==37;assert m.version('plot-sample')=='1.0';v=json.loads(pathlib.Path(r'\${cap:dataset}/values.json').read_text());assert sum(v)==114;pathlib.Path(os.environ['PLOT_STATE'],'verified').write_text('yes')`]}]);
 assert.equal(await verify('seed'),0);
 for(let i=0;i<30;i++)await plot.provision('warmup-'+i);
 const rssBefore=process.memoryUsage().rss;
 let newViews=await measure(1000,i=>plot.provision('view-'+i));
 const rssAfter=process.memoryUsage().rss;
 let reuse=await measure(300,()=>plot.provision('seed'));
 let lookup=await measure(1000,()=>plot.view('seed'));
 // Execute representative measured views after timing. Timing includes manifest
 // read, graph selection, asset availability checks, lock, state mkdir, descriptor
 // serialization, file fsync and atomic rename. No child is started in that path.
 for(let i of [0,499,999]){assert.equal(await verify('view-'+i),0);let v=plot.view('view-'+i);assert.equal(v.python,first.python);assert.equal(v.packages,first.packages)}
 let cliWarm=await measure(60,i=>must(cli(root,['provision','cli-'+i])));
 let pythonInvoke=await measure(60,()=>must(cli(root,['run','seed','python','-c','import plot_sample,plot_native;assert plot_native.value()==37'])));
 let rawPython=await measure(60,()=>command(first.python,['-I','-S','-c','pass']));
 // Runtime-only empty venv baseline. This lacks the benchmark's two packages,
 // dataset, dependency validation and runnable composed analysis environment.
 let venv=await measure(20,i=>command(python,['-m','venv','--without-pip',path.join(tmp,'empty-'+i)]));
 let files=fs.readdirSync(path.join(root,'.grave/envs')).map(name=>fs.statSync(path.join(root,'.grave/envs',name)).size);
 let result={started_at:started,finished_at:new Date().toISOString(),environment:{os:os.platform(),release:os.release(),arch:process.arch,node:process.version,python:command(python,['--version']),cpu:os.cpus()[0]?.model,cpu_count:os.cpus().length,filesystem:'container scratch; locally warm filesystem cache',core_bytes:fs.statSync(path.join(base,'main.js')).size},workload:{capabilities:plot.plan().map(v=>v.id),wheels:['plot-sample==1.0','plot-native==1.0 (real compiled extension)'],new_views:1000,assets_before_and_after:fs.readdirSync(path.join(root,'.grave/objects')).length,descriptor_bytes_min:Math.min(...files),descriptor_bytes_max:Math.max(...files),rss_before:rssBefore,rss_after:rssAfter,correctness:'seed and views 0/499/999 execute real Python, native extension, distribution metadata, dependency dataset and separate writable output'},cold_first_acquisition_ms:cold,metrics:{new_persisted_cached_asset_view:newViews,cached_reprovision:reuse,view_lookup:lookup,cli_warm_provision:cliWarm,cli_python_package_execution:pythonInvoke,raw_python_startup:rawPython,empty_venv_without_pip:venv},gates:{core_under_9063_bytes:fs.statSync(path.join(base,'main.js')).size<=9063,new_persisted_cached_asset_view_p95_under_6_ms:newViews.summary.p95_ms<6},limits:['Single Linux/x64 container measurement; not a device-wide guarantee.','Warm acquired and validated assets; no resolver, download, pip install, or interpreter launch included in provisioning.','File fsync is included; parent directory fsync/power-loss durability is not implemented.','Empty venv baseline is runtime-only and is not an equivalent package environment.','Raw sample times retained; results are not portable performance constants.']};
 fs.writeFileSync(path.join(base,'evidence/benchmark.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({cold_first_acquisition_ms:cold,metrics:Object.fromEntries(Object.entries(result.metrics).map(([k,v])=>[k,v.summary])),gates:result.gates},null,2));
 if(!Object.values(result.gates).every(Boolean))process.exitCode=1;
}finally{fs.rmSync(tmp,{recursive:true,force:true})}
