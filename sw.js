/* LaTimp: funcționare fără internet. Pagina vine de pe rețea când se poate (ca să primești versiunea nouă), altfel din copia salvată. */
const V="latimp-1.8";
const CORE=["./","index.html","manifest.webmanifest","icons/icon-192.png","icons/icon-512.png","icons/icon-maskable-512.png","icons/apple-touch-icon-180.png","icons/favicon.svg","icons/favicon-32.png"];
const FONTS=/^https:\/\/(fonts\.(googleapis|gstatic)\.com|cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@)/;
self.addEventListener("install",e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith("latimp-")&&k!=V&&k!="latimp-fonts").map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{
 const r=e.request;if(r.method!="GET")return;
 const u=new URL(r.url);
 if(FONTS.test(r.url)){e.respondWith(caches.open("latimp-fonts").then(async c=>{const hit=await c.match(r);const net=fetch(r).then(res=>{if(res.ok||res.type=="opaque")c.put(r,res.clone());return res}).catch(()=>hit);return hit||net}));return}
 if(u.origin!=location.origin)return;
 if(r.mode=="navigate"||u.pathname.endsWith("/")||u.pathname.endsWith(".html")){
  e.respondWith(fetch(r).then(res=>{if(res.ok){const cp=res.clone();caches.open(V).then(c=>c.put("index.html",cp))}return res}).catch(async()=>(await caches.match("index.html"))||(await caches.match("./"))||Response.error()));return}
 e.respondWith(caches.match(r).then(hit=>hit||fetch(r).then(res=>{if(res.ok){const cp=res.clone();caches.open(V).then(c=>c.put(r,cp))}return res})))});
