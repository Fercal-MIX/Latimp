/* LaTimp: funcționare fără internet. Pagina vine de pe rețea când se poate (ca să primești versiunea nouă), altfel din copia salvată. */
const V="latimp-__VER__";
const CORE=["./","index.html","manifest.webmanifest","icons/icon-192.png","icons/icon-512.png","icons/icon-maskable-512.png","icons/apple-touch-icon-180.png","icons/favicon.svg","icons/favicon-32.png","fonts/plus-jakarta-sans.woff","i18n-en.js"];
const FONTS=/^https:\/\/(fonts\.(googleapis|gstatic)\.com|cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@)/;
self.addEventListener("install",e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith("latimp-")&&k!=V&&k!="latimp-fonts").map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{
 const r=e.request;if(r.method!="GET")return;
 const u=new URL(r.url);
 if(FONTS.test(r.url)){e.respondWith(caches.open("latimp-fonts").then(async c=>{const hit=await c.match(r);const net=fetch(r).then(res=>{if(res.ok||res.type=="opaque")c.put(r,res.clone());return res}).catch(()=>hit);return hit||net}));return}
 if(u.origin!=location.origin)return;
 if(r.mode=="navigate"||u.pathname.endsWith("/")||u.pathname.endsWith(".html")){
  /* doar aplicația se păstrează ca „index.html”; paginile publice (prezentare, termeni) nu o înlocuiesc */
  const app=u.pathname.endsWith("/")||u.pathname.endsWith("/index.html");
  e.respondWith(fetch(r).then(res=>{if(res.ok&&app){const cp=res.clone();caches.open(V).then(c=>c.put("index.html",cp))}return res}).catch(async()=>(app?(await caches.match("index.html"))||(await caches.match("./")):await caches.match(r))||Response.error()));return}
 e.respondWith(caches.match(r).then(hit=>hit||fetch(r).then(res=>{if(res.ok){const cp=res.clone();caches.open(V).then(c=>c.put(r,cp))}return res})))});

/* memento-uri trimise de server */
self.addEventListener("push",e=>{let d={};try{d=e.data?e.data.json():{}}catch(x){d={title:"LaTimp",body:e.data?e.data.text():""}}
 const n=d.notification||{},o={body:d.body||n.body||"",tag:d.tag||n.tag||undefined,icon:"icons/icon-192.png",badge:"icons/icon-192.png",data:{url:d.url||n.navigate||"./",it:d.it||""}};
 if(Array.isArray(d.actions)&&d.actions.length)o.actions=d.actions.slice(0,2);
 e.waitUntil(self.registration.showNotification(d.title||n.title||"LaTimp",o))});
self.addEventListener("notificationclick",e=>{e.notification.close();const dt=e.notification.data||{},done=e.action=="done";
 let u=new URL(dt.url||"./",self.registration.scope);if(done&&dt.it)u.searchParams.set("done","1");u=u.href;
 const msg={lt:"open",it:dt.it||"",done:done};
 e.waitUntil(self.clients.matchAll({type:"window",includeUncontrolled:true}).then(cs=>{for(const c of cs){if(c.url.startsWith(self.registration.scope)&&"focus" in c){try{c.postMessage(msg)}catch(x){}return c.focus()}}return self.clients.openWindow(u)}))});
