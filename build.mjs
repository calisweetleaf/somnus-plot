// Deterministic development-only compaction. No bundler dependency at runtime.
// Strings, regex literals and template literals are copied without modification.
// Only the listed private identifiers are shortened; property names stay intact.
import {readFileSync,writeFileSync,statSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
const names=['str','oct','sum','fd','tar','cmd','resolve','lock','stamp','sig','exec','py','bin','info','fail','stable','inside','probe','chunks','length','entries','names','off','pending','grave','envs','objects','ledger','manifest','allowed','definitions','wanted','stages','changes','expand','acquire','untar','runner','root','requested','options','order','active','assets','stage','identity','provision','state','view','plan','run','args','steps','name','spec','target','resolved','limit','dest','src','token','done','visit','read','atom','valid','key','old','host','code','next','path','links','seen','exists','mkdir','join'];
const source=readFileSync(new URL('src/plot.mjs',import.meta.url),'utf8');
names.sort((a,b)=>(source.match(new RegExp('\\b'+b+'\\b','g'))||[]).length-(source.match(new RegExp('\\b'+a+'\\b','g'))||[]).length||a.localeCompare(b));
const rename=new Map(names.map((n,i)=>[n,i<26?String.fromCharCode(65+i):'$'+(i-26).toString(36)]));
let tokens=[],i=0,previous='';
while(i<source.length){
 let c=source[i];if(/\s/.test(c)){i++;continue}
 if(source.startsWith('//',i)){i=source.indexOf('\n',i);if(i<0)break;continue}
 if(source.startsWith('/*',i)){let end=source.indexOf('*/',i+2);if(end<0)throw Error('comment');i=end+2;continue}
 let start=i;
 if(c==='"'||c==="'"||c==='`'){
  i++;while(i<source.length){if(source[i]==='\\'){i+=2;continue}if(source[i++]===c)break}
 }else if(c==='/'&&['(','=',',',':','!','&&','||'].includes(previous)){
  i++;let bracket=false;while(i<source.length){let q=source[i++];if(q==='\\'){i++;continue}if(q==='[')bracket=true;if(q===']')bracket=false;if(q==='/'&&!bracket)break}while(/[a-z]/i.test(source[i]||'0'))i++;
 }else if(/[A-Za-z_$]/.test(c)){while(/[A-Za-z0-9_$]/.test(source[++i]||' ')){};
 }else if(/[0-9]/.test(c)){while(/[0-9.a-fxo]/i.test(source[++i]||' ')){};
 }else{let op=['===','!==','=>','?.','??','||','&&','...','++','+=','<=','>=','==','!='].find(s=>source.startsWith(s,i));i+=op?.length||1}
 let token=source.slice(start,i),original=token,tail=source.slice(i).trimStart();
 if(previous!=='.'&&previous!=='?.'&&rename.has(token)&&!((previous==='{'||previous===',')&&tail.startsWith(':')))token=rename.get(token);
 tokens.push(token);previous=original;
}
tokens=tokens.map(t=>t==='const'?'let':t==='true'?'!0':t==='false'?'!1':t==='undefined'?'void 0':t);let output='';for(let token of tokens){let last=output.at(-1)||'';if(/[\w$]/.test(last)&&/^[\w$]/.test(token)||last==='+'&&token[0]==='+'||last==='-'&&token[0]==='-')output+=' ';output+=token}
writeFileSync(new URL('main.js',import.meta.url),output+'\n');
const check=spawnSync(process.execPath,['--check',new URL('main.js',import.meta.url).pathname],{encoding:'utf8'});if(check.status)throw Error(check.stderr);
const bytes=statSync(new URL('main.js',import.meta.url)).size;
console.log(JSON.stringify({core_bytes:bytes,ceiling_bytes:9063}));if(bytes>9063)throw Error('core size ceiling exceeded');
