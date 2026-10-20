import * as fs from 'node:fs';
import * as path from 'node:path';
import os from 'node:os';
import {spawnSync} from 'node:child_process';
import {gzipSync} from 'node:zlib';
export const base=path.resolve(new URL('..',import.meta.url).pathname);
export const python=spawnSync('python3',['-c','import sys;print(sys.executable)'],{encoding:'utf8'}).stdout.trim();
export const defaults={id:'test-plot',version:'0.5.0',hosts:['node'],execution:'trusted',permissions:{spawn:true},steps:[]};
export function scratch(){return fs.mkdtempSync(path.join(os.tmpdir(),'plot-stage1-'))}
export function manifest(root,m={}){fs.writeFileSync(path.join(root,'manifest.json'),JSON.stringify({...defaults,...m}))}
export function fixture(parent,name,m={}){let root=path.join(parent,name);fs.mkdirSync(root);manifest(root,m);return root}
export function cli(root,args=[],options={}){return spawnSync(process.execPath,[path.join(base,'main.js'),'--root',root,...args],{encoding:'utf8',timeout:90000,...options})}
export function must(r){if(r.error||r.status!==0)throw Error(r.error?.message||r.stderr||r.stdout);return r}
export function command(cmd,args,options={}){return must(spawnSync(cmd,args,{encoding:'utf8',timeout:90000,...options})).stdout.trim()}
export function tar(entries){
 let parts=[];
 for(let e of entries){let h=Buffer.alloc(512),data=Buffer.from(e.data||'');
  let text=(offset,width,value)=>h.write(value,offset,width,'ascii');
  let oct=(offset,width,value)=>text(offset,width,value.toString(8).padStart(width-1,'0')+'\0');
  text(0,100,e.name);oct(100,8,e.mode||0o644);oct(108,8,0);oct(116,8,0);oct(124,12,data.length);oct(136,12,0);h.fill(32,148,156);h[156]=(e.type||'0').charCodeAt(0);text(157,100,e.target||'');text(257,6,'ustar\0');text(263,2,'00');let sum=h.reduce((a,b)=>a+b,0);text(148,8,sum.toString(8).padStart(6,'0')+'\0 ');parts.push(h,data,Buffer.alloc((512-data.length%512)%512));
 }parts.push(Buffer.alloc(1024));return gzipSync(Buffer.concat(parts));
}
// Build real, pip-installable offline distributions and a real CPython C extension.
// These fixtures contain no downloaded code, mock interpreters or training data.
export function wheels(root){
 let include=command(python,['-c','import sysconfig;print(sysconfig.get_path("include"))']);
 let suffix=command(python,['-c','import sysconfig;print(sysconfig.get_config_var("EXT_SUFFIX"))']);
 let c=path.join(root,'native.c'),so=path.join(root,'plot_native'+suffix);
 fs.writeFileSync(c,'#include <Python.h>\nstatic PyObject *value(PyObject*s,PyObject*a){return PyLong_FromLong(37);}\nstatic PyMethodDef methods[]={{"value",value,METH_NOARGS,"real fixture"},{NULL,NULL,0,NULL}};\nstatic struct PyModuleDef module={PyModuleDef_HEAD_INIT,"plot_native",NULL,-1,methods};\nPyMODINIT_FUNC PyInit_plot_native(void){return PyModule_Create(&module);}\n');
 command('cc',['-shared','-fPIC','-I'+include,c,'-o',so]);
 const script=`import zipfile,pathlib,sys,sysconfig
root=pathlib.Path(sys.argv[1]); native=pathlib.Path(sys.argv[2])
for version in ('1.0','2.0'):
 d='plot_sample-'+version+'.dist-info'
 files={'plot_sample/__init__.py':'VERSION='+repr(version)+'\\ndef main():\\n print(VERSION)\\n return 0\\n', 'plot_sample/__main__.py':'from . import main\\nmain()\\n', 'plot_sample/payload.txt':'actual package resource', d+'/METADATA':'Metadata-Version: 2.1\\nName: plot-sample\\nVersion: '+version+'\\n', d+'/WHEEL':'Wheel-Version: 1.0\\nGenerator: plot-test\\nRoot-Is-Purelib: true\\nTag: py3-none-any\\n', d+'/entry_points.txt':'[console_scripts]\\nplot-sample = plot_sample:main\\n'}
 files[d+'/RECORD']=''.join(k+',,\\n' for k in files)
 with zipfile.ZipFile(root/('plot_sample-'+version+'-py3-none-any.whl'),'w') as z:
  for k,v in files.items(): z.writestr(k,v)
d='plot_native-1.0.dist-info'
cp='cp'+str(sys.version_info.major)+str(sys.version_info.minor)
tag=cp+'-'+cp+'-'+sysconfig.get_platform().replace('-','_').replace('.','_')
files={d+'/METADATA':'Metadata-Version: 2.1\\nName: plot-native\\nVersion: 1.0\\n',d+'/WHEEL':'Wheel-Version: 1.0\\nRoot-Is-Purelib: false\\nTag: '+tag+'\\n'}
files[d+'/RECORD']=''.join(k+',,\\n' for k in [*files,native.name])
filename='plot_native-1.0-'+tag+'.whl'
with zipfile.ZipFile(root/filename,'w') as z:
 for k,v in files.items(): z.writestr(k,v)
 z.write(native,native.name)
print(filename)
`;
 let nativeName=command(python,['-c',script,root,so]);
 return {one:path.join(root,'plot_sample-1.0-py3-none-any.whl'),two:path.join(root,'plot_sample-2.0-py3-none-any.whl'),native:path.join(root,nativeName)};
}
