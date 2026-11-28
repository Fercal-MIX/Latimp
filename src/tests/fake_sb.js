(function(){
 const L=k=>{try{return JSON.parse(localStorage.getItem(k)||"null")}catch(e){return null}},P=(k,v)=>localStorage.setItem(k,JSON.stringify(v));
 window.__sb={sent:[],invoked:[],signedOut:0,upserts:0};
 function createClient(url,key,opt){
  const sk=(opt&&opt.auth&&opt.auth.storageKey)||"sb";let subs=[];
  const sess=()=>L(sk);
  if(opt&&opt.auth&&opt.auth.detectSessionInUrl&&/access_token=/.test(location.hash)){const m=location.hash.match(/email=([^&]+)/);const em=decodeURIComponent(m?m[1]:"x@test.ro");P(sk,{user:{id:"u-"+em,email:em},access_token:"t"})}
  const auth={
   onAuthStateChange(fn){subs.push(fn);return{data:{subscription:{unsubscribe(){}}}}},
   async getSession(){return{data:{session:sess()},error:null}},
   async signInWithOtp(o){__sb.redirect=o.options&&o.options.emailRedirectTo;if(o.email=="limit@test.ro")return{data:null,error:{status:429,message:"rate"}};__sb.sent.push(o.email);return{data:{user:null,session:null},error:null}},
   async verifyOtp(o){if(o.token!="123456")return{data:{user:null,session:null},error:{status:403,message:"bad"}};const u={id:"u-"+o.email,email:o.email},s={user:u,access_token:"t"};P(sk,s);subs.forEach(f=>f("SIGNED_IN",s));return{data:{user:u,session:s},error:null}},
   async signInWithOAuth(o){__sb.oauth=o;return{data:{},error:null}},
   async signOut(){__sb.signedOut++;localStorage.removeItem(sk);subs.forEach(f=>f("SIGNED_OUT",null));return{error:null}}};
  function from(t){if(t=="app_config"){const q={_k:"app",select(){return q},eq(c,v){q._k=v;return q},async maybeSingle(){if(q._k=="fx")return{data:window.__fx?{value:window.__fx}:null,error:null};const c=L(q._k=="content"?"fake.cnt":q._k=="texts"?"fake.txt":"fake.cfg");return{data:c?{value:c}:null,error:null}}};return q}
   const rec=(k,v)=>{const a=L(k)||[];a.push(v);P(k,a)};
   if(t=="poll_votes"){const q={select(){return q},async eq(){return{data:L("fake.pv")||[],error:null}}};return q}
   if(t=="polls")return{delete(){return{async eq(){__sb.pollDel=(__sb.pollDel||0)+1;return{error:null}}}}};
   if(t=="family_blobs"){const q={select(){return q},async eq(c,v){return{data:(L("fake.fam")||[]).filter(r=>r.group_hash==v),error:null}},async upsert(r){const a=(L("fake.fam")||[]).filter(x=>x.user_id!=r.user_id);a.push(r);P("fake.fam",a);return{error:null}},delete(){return{async eq(c,v){P("fake.fam",(L("fake.fam")||[]).filter(x=>x[c]!=v));return{error:null}}}}};return q}
   if(t=="calendar_feeds")return{async upsert(r){P("fake.calf",r);return{error:null}},delete(){return{async eq(){localStorage.removeItem("fake.calf");return{error:null}}}}};
   if(t=="app_errors")return{async insert(r){rec("fake.err",r);return{error:null}}};
   if(t=="reports"){const q={async insert(r){rec("fake.rep",r);return{error:null}},select(){return q},not(){return q},order(){return q},async limit(){return{data:L("fake.rpl")||[],error:null}}};return q}
   if(t=="usage_stats")return{async upsert(r){P("fake.ust",r);return{error:null}},delete(){return{async eq(){localStorage.removeItem("fake.ust");return{error:null}}}}};
   if(t=="push_subs"){const q={async upsert(row){const a=(L("fake.push")||[]).filter(x=>x.endpoint!=row.endpoint);a.push(row);P("fake.push",a);return{error:null}},delete(){return{async eq(c,v){P("fake.push",(L("fake.push")||[]).filter(x=>x[c]!=v));return{error:null}}}}};return q}
   if(t=="referral_uses"){const q={_c:null,_v:null,_o:null,select(a,o){q._o=o;return q},eq(c,v){q._c=c;q._v=v;return q},then(res){const u=L("fake.ru")||[];res({count:u.filter(x=>x[q._c]==q._v).length,data:null,error:null})},async maybeSingle(){const u=L("fake.ru")||[];return{data:u.find(x=>x[q._c]==q._v)||null,error:null}}};return q}
   const q={_eq:null,select(){return q},eq(c,v){q._eq=v;return q},async maybeSingle(){const db=L("fake.db")||{};return{data:db[q._eq]||null,error:null}},
   async upsert(row){const db=L("fake.db")||{};db[row.user_id]={state:row.state,updated_at:new Date().toISOString()};P("fake.db",db);__sb.upserts++;return{error:null}}};return q}
  const functions={async invoke(n,o){__sb.invoked.push(n);const fh=(window.__fn||{})[n];if(fh){try{return{data:await fh(o&&o.body,sess()),error:null}}catch(x){return{data:null,error:{context:{json:async()=>({err:String(x&&x.message||x)})}}}}}const s=sess();if(n=="delete-account"&&s){const db=L("fake.db")||{};delete db[s.user.id];P("fake.db",db);return{data:{ok:true},error:null}}return{data:null,error:{context:{json:async()=>({error:"x"})}}}}};
  async function rpc(n,a){__sb.rpcs=(__sb.rpcs||[]).concat(n);const h=(window.__rpc||{})[n];if(h){const v=await h(a,sess());if(v&&v.__err)return{data:null,error:{message:v.__err}};return{data:v,error:null}}return{data:null,error:{message:"no rpc "+n}}}
  const storage={from(b){return{async upload(p,blob,o){rec2("fake.up",{b,p,type:o&&o.contentType,size:blob&&blob.size});return{data:{path:p},error:null}},async remove(a){rec2("fake.rm",{b,a});return{data:a,error:null}},async createSignedUrl(p,s){rec2("fake.sign",{b,p,s});return{data:{signedUrl:location.origin+"/termeni.html#"+p},error:null}}}}};
  function rec2(k,v){const a=L(k)||[];a.push(v);P(k,a)}
  return{auth,from,functions,rpc,storage}}
 window.supabase={createClient};
})();
