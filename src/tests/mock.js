(function(){
const store=new Map(),subs=[];
const clone=o=>JSON.parse(JSON.stringify(o));
const merge=(a,b)=>{for(const k in b){if(b[k]&&typeof b[k]=="object"&&!Array.isArray(b[k])&&a[k]&&typeof a[k]=="object"&&!Array.isArray(a[k]))merge(a[k],b[k]);else a[k]=clone(b[k])}return a};
const snapDoc=(p)=>({id:p.split("/").pop(),exists:store.has(p),data:()=>store.has(p)?clone(store.get(p)):undefined,metadata:{fromCache:false,hasPendingWrites:false}});
const inColl=(c)=>[...store.keys()].filter(k=>{const s=k.split("/"),cs=c.split("/");return s.length==cs.length+1&&k.startsWith(c+"/")}).sort();
function notify(){subs.forEach(s=>s.fire())}
window.__db=store;window.__log=[];
const db={
 doc(path){return{id:path.split("/").pop(),path,
  async get(){return snapDoc(path)},
  async set(d){window.__log.push(["set",path]);store.set(path,clone(d));notify()},
  async update(d){window.__log.push(["update",path]);if(!store.has(path)){const e=new Error("nf");e.code="invalid_argument";throw e}merge(store.get(path),d);notify()},
  async delete(){window.__log.push(["delete",path]);store.delete(path);notify()},
  onSnapshot(next){const s={fire:()=>setTimeout(()=>next(snapDoc(path)),0)};subs.push(s);s.fire();return()=>{const i=subs.indexOf(s);if(i>=0)subs.splice(i,1)}}}},
 collection(path){
  const mk=(filters)=>({
   where(f,op,v){return mk(filters.concat([[f,op,v]]))},
   orderBy(){return mk(filters)},limit(){return mk(filters)},
   _docs(){return inColl(path).filter(k=>filters.every(([f,op,v])=>op=="=="?(store.get(k)||{})[f]===v:true)).map(snapDoc)},
   async get(){const docs=this._docs();return{docs,size:docs.length,empty:!docs.length,metadata:{}}},
   onSnapshot(next){const me=this;const s={fire:()=>setTimeout(()=>{const docs=me._docs();next({docs,size:docs.length,empty:!docs.length,metadata:{fromCache:false,hasPendingWrites:false},docChanges:()=>[]})},0)};subs.push(s);s.fire();return()=>{const i=subs.indexOf(s);if(i>=0)subs.splice(i,1)}},
   doc(id){return db.doc(path+"/"+(id||Math.random().toString(36).slice(2)))},
   async add(d){const r=db.doc(path+"/"+Math.random().toString(36).slice(2));await r.set(d);return r}});
  return mk([])}};
const user={async id(){return window.__uid===undefined?"u_test1":window.__uid},async canEdit(){return window.__admin!==false},async can(){return true},async isOwner(){return true}};
const sample=async(p,o)=>{window.__samples=(window.__samples||[]).concat([{p,img:!!(o&&o.images)}]);if(window.__aifail)throw {code:"rate_limited"};
 if(o&&o.images)return{text:'```json\n{"tip":"rca","nume":"Asigurator Test","nr":"B 123 ABC","data":"'+window.__phdate+'","pret":null,"perioada":null}\n```'};
 if(/cadou/i.test(p)&&/consultant/.test(p))return{text:'[{"t":"Set de pescuit","d":"Pentru pasiunea lui.","q":["lanseta telescopica","set carlige pescuit"]},{"t":"Cizme","d":"Utile la pescuit.","q":["cizme cauciuc <script>","cizme"]}]'};
 if(/plan pe ore/i.test(p))return{text:'[{"o":"10:00","t":"Plecați de acasă"},{"o":"12:30","t":"Prânz simplu"},{"o":"15:00","t":"Înghețată și drum înapoi"}]'};
 if(/asemănătoare/i.test(p))return{text:'[{"t":"Picnic în parc","d":"Pături și sandvișuri.","c":"gratis","m":"parc"},{"t":"Plimbare în parc","d":"Duplicat.","c":"gratis"},{"t":"Biciclete","d":"Un traseu ușor.","c":"~20 lei","m":"pistă biciclete"}]'};
 if(/formulări/i.test(p))return{text:'[{"t":"Scurt și cald","d":"Mulțumesc că te-ai gândit la mine, dar acum nu pot.","c":""},{"t":"Cu alternativă","d":"Joi seara pot să te ajut.","c":""}]'};
 return{text:'[{"t":"Plimbare în parc","d":"Simplu și relaxant.","c":"gratis","m":"parc <b>x</b>"},{"t":"Cafenea","d":"Cu jocuri.","c":"~50 lei","m":"cafenea jocuri"}]'}};
sample.limits=async()=>({maxPromptBytes:262144,images:{maxCount:1,maxInputBytes:5e6,mediaTypes:["image/jpeg","image/png","image/webp"]}});
const assets={async upload(b){window.__uploads=(window.__uploads||0)+1;return{id:"a".repeat(32),url:"/_blob/"+"a".repeat(32),sizeBytes:b.size,contentType:"image/jpeg"}}};
const downloads={async save(r){window.__saved=r;return{status:"saved"}}};
const caps={db,user,sample,assets,downloads};
window.claude={use:async n=>(window.__nocaps?null:(caps[n]||null))};
addEventListener('load',()=>{if(window.__noacct)return;try{if(!S.acct)S.acct={p:'google',e:'test@gmail.com',n:'',at:Date.now(),v:true};if(!window.__noai&&!S.aiq)S.aiq=Date.now();(0,eval)('store()')}catch(e){}});
})();
