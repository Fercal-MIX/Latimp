import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
from web import *
U="http://localhost:8777/"
CFG={"mon":{"free":True,"control":False,"sparks":False,"invites":False,"referrals":False}}
STUB="""(()=>{const sub={endpoint:'https://push.example/abc',toJSON(){return{endpoint:this.endpoint,keys:{p256dh:'B'+'x'.repeat(86),auth:'y'.repeat(22)}}},async unsubscribe(){window.__unsub=(window.__unsub||0)+1;window.__has=false;return true}};
 window.__perm=window.__perm||'granted';
 if(window.PushManager){PushManager.prototype.subscribe=async function(){window.__has=true;return sub};PushManager.prototype.getSubscription=async function(){return window.__has?sub:null}}
 if(window.Notification){Object.defineProperty(Notification,'permission',{get(){return window.__perm=='granted'&&window.__asked?'granted':window.__perm=='denied'?'denied':'default'},configurable:true});Notification.requestPermission=async()=>{window.__asked=1;return window.__perm}}
 window.__rp=[];window.__rpc={get_my_access:async()=>({pro:true,source:'free',free_mode:true}),am_i_admin:async()=>false,set_reminders:async(a)=>{window.__rp.push(a.p);return a.p.length}};})();"""
def st(items,extra=""):
    return json.dumps({"onb":True,"at":5,"items":items,"cars":[],"saved":[],"credits":0,"used":0,"photos":0,"theme":"auto","nt":{"d":7,"h":"09:00","rep":False,"n":3,"i":7,"day":False,"wk":False},"acct":{"p":"email","e":"ana@test.ro","v":True}})
async def mk(b,items,signed=True,pre="",geo=None):
    kw={"viewport":{"width":390,"height":800}}
    if geo: kw["geolocation"]=geo;kw["permissions"]=["geolocation"]
    c=await b.new_context(**kw)
    await fake_route(c,fonts=True)
    init="if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);localStorage.setItem('buzunar.v2',%s);"%(json.dumps(json.dumps(CFG)),json.dumps(st(items)))
    if signed: init+="localStorage.setItem('latimp.auth',JSON.stringify({user:{id:'u1',email:'ana@test.ro'},access_token:'t'}));"
    else: init+="(()=>{const s=JSON.parse(localStorage.getItem('buzunar.v2'));s.acct=null;localStorage.setItem('buzunar.v2',JSON.stringify(s))})();"
    init+="}"
    await c.add_init_script(init);await c.add_init_script(STUB)
    await c.add_init_script("window.__fnb=[];window.__fn={ai:async(b)=>{__fnb.push(b);if(b.kind=='status')return{ready:!!window.__aiready,images:['image/jpeg','image/png']};if(window.__aicap)throw new Error('user_cap');if(b.kind=='photo')return{text:JSON.stringify({tip:'rca',nume:'Asigurator X',nr:'B 12 ABC',data:'2027-03-10',pret:null,perioada:null})};return{text:JSON.stringify([{t:'Atelier de olărit',d:'Două ore cu lut, pentru toată familia.',c:'cultura',m:'acasa'},{t:'Picnic în parc',d:'Pătură, sandvișuri și un joc de cărți.',c:'natura',m:'afara'},{t:'Seară de jocuri',d:'Trei jocuri de masă scurte.',c:'acasa',m:'acasa'},{t:'Muzeu interactiv',d:'Expoziții pe care le atingi.',c:'cultura',m:'oras'}])}}};"+pre)
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(2500)
    return c,p,errs
async def main():
    global CFG
    srv=serve(8777)
    try:
        async with async_playwright() as pw:
            b=await pw.chromium.launch()
            CFG={"mon":{"free":True}}
            # 1. română: dicționarul englez nu se descarcă
            reqs=[]
            c,p,e=await mk(b,[])
            p.on("request",lambda r:reqs.append(r.url))
            await p.reload();await p.wait_for_timeout(2500)
            chk("ro: English dictionary not downloaded",not any("i18n-en.js" in u for u in reqs),[u for u in reqs if "i18n" in u])
            chk("ro: interface in Romanian","Mai mult" in await p.inner_text("nav") if await p.locator("nav").count() else "Mai mult" in await p.inner_text("body"))
            # 2. schimbarea în engleză încarcă dicționarul și traduce
            await p.evaluate("tab('more')");await p.wait_for_timeout(500)
            await p.click("button:text-is('English')");await p.wait_for_timeout(1500)
            t=await p.inner_text("body")
            chk("switch to en: dictionary loaded",any("i18n-en.js" in u for u in reqs) and await p.evaluate("!!(window.LT_EN&&LT_EN.ok)"))
            chk("switch to en: interface translated","More" in t and "Free time" in t and "Timp liber" not in t,t[:300])
            chk("no errors 1",not e,e)
            await c.close()
            # 3. pornire direct în engleză: textele în engleză de la prima afișare
            c,p,e=await mk(b,[])
            await p.evaluate("S.lang='en';store()")
            reqs=[];p.on("request",lambda r:reqs.append(r.url))
            await p.reload();await p.wait_for_timeout(2500)
            t=await p.inner_text("body")
            chk("start in en: dictionary loaded at start",any("i18n-en.js" in u for u in reqs))
            chk("start in en: English interface","Free time" in t and "Timp liber" not in t,t[:300])
            await p.evaluate("tab('more')");await p.wait_for_timeout(400)
            await p.click("button:text-is('Română')");await p.wait_for_timeout(800)
            chk("back to ro","Timp liber" in await p.inner_text("body"))
            chk("no errors 2",not e,e)
            await c.close()
            # 4. fișierul e păstrat pentru folosirea fără internet
            sw=open(SC+"web/sw.js").read()
            chk("offline copy includes the dictionary",'"i18n-en.js"' in sw)
            await b.close()
    finally: srv.terminate()
    done()
asyncio.run(main())
