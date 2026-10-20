// Deterministic development-only compaction. No bundler dependency at runtime.
// Strings, regex literals and template literals are copied without modification.
// Only the listed private identifiers are shortened; property names stay intact.
import {readFileSync,writeFileSync,statSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
const names=['str','oct','sum','fd','tar','cmd','resolve','lock','stamp','sig','exec','py','bin','info','fail','stable','inside','probe','chunks','length','entries','names','off','pending','grave','envs','objects','ledger','manifest','allowed','definitions','wanted','stages','changes','expand','acquire','untar','runner','root','requested','options','order','active','assets','stage','identity','provision','state','view','plan','run','args','steps','name','spec','target','resolved','limit','dest','src','token','done','visit','read','atom','valid','key','old','host','code','next','path','links','seen','exists','mkdir','join','proc','sync','syncdir','create','nest','pins','pin','paths','reject','dep','plot','runSync','gunzip','digest','real','rm','pkgcap','dflt'];
const source=readFileSync(new URL('src/plot.mjs',import.meta.url),'utf8');
names.sort((a,b)=>(source.match(new RegExp('\\b'+b+'\\b','g'))||[]).length-(source.match(new RegExp('\\b'+a+'\\b','g'))||[]).length||a.localeCompare(b));
// Short names come from a fixed alphabet minus every identifier the source already uses, so a rename never captures a binding.
const used=new Set(source.match(/[A-Za-z_$][\w$]*/g)),head='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$_',pool=[...head].filter(n=>!used.has(n));
for(let a of head)for(let b of head+'0123456789')if(!used.has(a+b)&&!['do','if','in','of','as'].includes(a+b))pool.push(a+b);
const rename=new Map(names.map((n,i)=>[n,pool[i]]));
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
tokens=tokens.map(t=>t==='const'?'let':t==='true'?'!0':t==='false'?'!1':t==='undefined'?'void 0':/^[1-9]\d*000+$/.test(t)?t.replace(/0+$/,'')+'e'+/0+$/.exec(t)[0].length:/^0o[0-7]+$/.test(t)?String(parseInt(t.slice(2),8)):t);
// Per brace frame: drop ';' before '}', and join adjacent let statements ('a;let b' -> 'a,b') when the frame's statement began with let outside parentheses.
{let out=[],frames=[{paren:0,let:false}];for(let i=0;i<tokens.length;i++){let t=tokens[i],top=frames.at(-1),prev=out.at(-1);
 if(t==='('||t==='[')top.paren++;else if(t===')'||t===']')top.paren--;else if(t==='{')frames.push({paren:0,let:false});else if(t==='}')frames.pop();
 else if(t==='let'&&!top.paren&&[';','{','}',undefined].includes(prev))top.let=true;
 else if(t===';'&&!top.paren){if(tokens[i+1]==='}')continue;if(top.let&&tokens[i+1]==='let'){out.push(',');i++;continue}top.let=false}
 out.push(t)}tokens=out}
let output='';for(let token of tokens){let last=output.at(-1)||'';if(/[\w$]/.test(last)&&/^[\w$]/.test(token)||last==='+'&&token[0]==='+'||last==='-'&&token[0]==='-')output+=' ';output+=token}
writeFileSync(new URL('main.js',import.meta.url),output+'\n');
const check=spawnSync(process.execPath,['--check',new URL('main.js',import.meta.url).pathname],{encoding:'utf8'});if(check.status)throw Error(check.stderr);
const bytes=statSync(new URL('main.js',import.meta.url)).size;
console.log(JSON.stringify({core_bytes:bytes,ceiling_bytes:9063}));if(bytes>9063)throw Error('core size ceiling exceeded');
