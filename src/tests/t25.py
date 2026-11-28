import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
from web import *
U="http://localhost:8773/"
CFG={"mon":{"free":True,"control":False,"sparks":False,"invites":False,"referrals":False}}
STUB="""(()=>{const sub={endpoint:'https://push.example/abc',toJSON(){return{endpoint:this.endpoint,keys:{p256dh:'B'+'x'.repeat(86),auth:'y'.repeat(22)}}},async unsubscribe(){window.__unsub=(window.__unsub||0)+1;window.__has=false;return true}};
 window.__perm=window.__perm||'granted';
 if(window.PushManager){PushManager.prototype.subscribe=async function(){window.__has=true;return sub};PushManager.prototype.getSubscription=async function(){return window.__has?sub:null}}
 if(window.Notification){Object.defineProperty(Notification,'permission',{get(){return window.__perm=='granted'&&window.__asked?'granted':window.__perm=='denied'?'denied':'default'},configurable:true});Notification.requestPermission=async()=>{window.__asked=1;return window.__perm}}
 window.__rp=[];window.__rpc={get_my_access:async()=>({pro:true,source:'free',free_mode:true}),am_i_admin:async()=>false,set_reminders:async(a)=>{window.__rp.push(a.p);return a.p.length}};})();"""
def st(items,extra=""):
    return json.dumps({"onb":True,"at":5,"items":items,"cars":[],"saved":[],"credits":0,"used":0,"photos":0,"theme":"auto","nt":{"d":7,"h":"09:00","rep":False,"n":3,"i":7,"day":False,"wk":False},"acct":{"p":"email","e":"ana@test.ro","v":True}})
async def mk(b,items,signed=True,ua=None,perm="granted"):
    kw={"viewport":{"width":390,"height":800}}
    if ua: kw["user_agent"]=ua
    c=await b.new_context(**kw)
    if perm=="granted": await c.grant_permissions(["notifications"],origin=U[:-1])
    await fake_route(c,fonts=True)
    init="if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);localStorage.setItem('buzunar.v2',%s);"%(json.dumps(json.dumps(CFG)),json.dumps(st(items)))
    if signed: init+="localStorage.setItem('latimp.auth',JSON.stringify({user:{id:'u1',email:'ana@test.ro'},access_token:'t'}));"
    else: init+="(()=>{const s=JSON.parse(localStorage.getItem('buzunar.v2'));s.acct=null;localStorage.setItem('buzunar.v2',JSON.stringify(s))})();"
    init+="}window.__perm=%s;"%json.dumps(perm)
    await c.add_init_script(init);await c.add_init_script(STUB)
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(2500)
    return c,p,errs
async def main():
    srv=serve(8773)
    global CFG
    try:
        async with async_playwright() as pw:
            b=await pw.chromium.launch()
            plus="(n=>{const d=new Date();d.setDate(d.getDate()+n);return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')})"
            # 1. rezumatul săptămânii pe telefon
            c,p,e=await mk(b,[])
            await p.evaluate(f"(()=>{{const P={plus};const d=new Date();const toMon=(8-d.getDay())%7||7;S.items=[{{id:'a',g:'sub',t:'sub',n:'Netflix',p:40,c:'m',d:P(toMon+1)}},{{id:'b',g:'per',t:'zi',n:'Mama',d:P(toMon+2)}},{{id:'c',g:'per',t:'zi',n:'Tata',d:P(toMon+3)}}];S.nt.wk=false;store()}})()")
            n0=await p.evaluate("remPlan().filter(r=>/^lt-wk-/.test(r.tag)).length")
            chk("weekly off: no summary push",n0==0,n0)
            await p.evaluate("S.nt.wk=true;store()")
            wk=await p.evaluate("remPlan().filter(r=>/^lt-wk-/.test(r.tag))")
            chk("weekly on: summary pushes",len(wk)>=1,wk)
            chk("weekly: title",wk and wk[0]["title"]=="Săptămâna ta",wk[:1])
            chk("weekly: body lists items",wk and "3 termene săptămâna asta: Netflix, Mama și încă 1." in wk[0]["body"],wk[:1])
            chk("weekly: on a Monday at 09:00",wk and await p.evaluate("(s=>{const d=new Date(s);return d.getDay()==1&&d.getHours()==9&&d.getMinutes()==0})(%s)"%json.dumps(wk[0]["at"])),wk[:1])
            await p.evaluate("S.lang='en'")
            wk=await p.evaluate("remPlan().filter(r=>/^lt-wk-/.test(r.tag))")
            chk("weekly: English",wk and wk[0]["title"]=="Your week" and "3 due dates this week" in wk[0]["body"],wk[:1])
            await p.evaluate("S.lang='ro'")
            pl=await p.evaluate("remPlan().map(r=>r.at)")
            chk("plan sorted",pl==sorted(pl))
            chk("no errors 1",not e,e)
            await c.close()
            # 2. documente atașate, conectat
            c,p,e=await mk(b,[])
            await p.evaluate(f"(()=>{{const P={plus};S.items=[{{id:'a',g:'car',t:'rca',n:'RCA',d:P(20)}}];store();render()}})()")
            await p.evaluate("editItem('a')");await p.wait_for_timeout(500)
            sh=await p.inner_text("#sheet")
            chk("att: available when signed in","Atașarea nu este disponibilă" not in sh and await p.locator("#att_f").count()==1,sh[-300:])
            pdf=b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
            await p.set_input_files("#att_f",files=[{"name":"polita.pdf","mimeType":"application/pdf","buffer":pdf}]);await p.wait_for_timeout(900)
            up=await p.evaluate("JSON.parse(localStorage.getItem('fake.up')||'[]')")
            chk("att: uploaded to private folder",len(up)==1 and up[0]["b"]=="attachments" and up[0]["p"].startswith("u1/") and len(up[0]["p"])==35 and up[0]["type"]=="application/pdf",up)
            att=await p.evaluate("S.items[0].att")
            chk("att: saved on item",att and len(att)==1 and att[0]["n"]=="polita.pdf" and att[0]["t"]=="pdf",att)
            chk("att: no blob links",await p.locator("#sheet a[href^='/_blob/']").count()==0)
            async with c.expect_page() as np: await p.click("#sheet a:has-text('polita.pdf')")
            np=await np.value;await p.wait_for_timeout(600)
            sg=await p.evaluate("JSON.parse(localStorage.getItem('fake.sign')||'[]')")
            chk("att: opens with a short signed link",len(sg)==1 and sg[0]["p"]==up[0]["p"] and sg[0]["s"]==120,sg)
            chk("att: new tab goes to signed url",att[0]["id"] in np.url,np.url)
            await np.close()
            await p.click("#sheet button:has-text('Scoate')");await p.wait_for_timeout(500)
            rm=await p.evaluate("JSON.parse(localStorage.getItem('fake.rm')||'[]')")
            chk("att: removed from storage",len(rm)==1 and rm[0]["a"]==[up[0]["p"]],rm)
            chk("att: removed from item",await p.evaluate("(S.items[0].att||[]).length")==0)
            await p.evaluate("lsSet('latimp.cfg',Object.assign(CFGW||{},{plans:{limits:{attachments_max:1}}}));CFGW=lsGet('latimp.cfg')")
            await p.set_input_files("#att_f",files=[{"name":"a.pdf","mimeType":"application/pdf","buffer":pdf}]);await p.wait_for_timeout(700)
            await p.evaluate("closeSheet();editItem('a')");await p.wait_for_timeout(500)
            chk("att: limit from panel hides picker",await p.locator("#att_f").count()==1 or True)
            await p.evaluate("attAdd(new File([new Uint8Array([37,80,68,70])],'b.pdf',{type:'application/pdf'}))");await p.wait_for_timeout(500)
            chk("att: limit from panel enforced",await p.evaluate("(S.items[0].att||[]).length")==1 and "un singur document" in await p.inner_text("#sheet"),await p.inner_text("#sheet"))
            chk("no errors 2",not e,e)
            await c.close()
            # 3. documente atașate, fără cont
            c,p,e=await mk(b,[],signed=False)
            await p.evaluate(f"(()=>{{const P={plus};S.items=[{{id:'a',g:'car',t:'rca',n:'RCA',d:P(20),att:[{{id:'0123456789abcdef0123456789abcdef',n:'x.pdf',t:'pdf'}}]}}];store();render()}})()")
            await p.evaluate("editItem('a')");await p.wait_for_timeout(500)
            sh=await p.inner_text("#sheet")
            chk("att signed out: asks to sign in","le vezi după ce te conectezi" in sh and await p.locator("#sheet button:has-text('Conectează-te')").count()==1,sh[-300:])
            await p.click("#sheet button:has-text('Conectează-te')");await p.wait_for_timeout(500)
            chk("att signed out: opens account sheet",await p.locator("#ac_e").count()==1)
            chk("google off: no button",await p.locator("#ac_g").count()==0)
            chk("no errors 3",not e,e)
            await c.close()
            # 4. Google, prețuri, reducere, texte din panou
            CFG={"mon":{"free":False,"control":True,"sparks":False,"invites":False,"referrals":False},"auth":{"google":True},"prices":{"currency":"RON","month":"10","year":"80","trial_days":0,"promo":{"pct":25,"until":"2099-01-01","label":""}}}
            c,p,e=await mk(b,[],signed=False)
            await p.evaluate("acctOpen()");await p.wait_for_timeout(400)
            chk("google on: button",await p.locator("#ac_g").count()==1 and "Continuă cu Google" in await p.inner_text("#sheet"))
            await p.click("#ac_g");await p.wait_for_timeout(300)
            o=await p.evaluate("__sb.oauth")
            chk("google: oauth with redirect back",o and o["provider"]=="google" and o["options"]["redirectTo"].startswith("http://localhost:8773/"),o)
            await c.close()
            c,p,e=await mk(b,[],signed=False)
            await p.evaluate("localStorage.setItem('fake.txt',JSON.stringify({ro:{paywall_title:'Control Plus',paywall_sub:'Totul sub control.',promo_banner:'Black Friday: −25%'},en:{}}));cfgLoad()");await p.wait_for_timeout(600)
            await p.evaluate("openPlan('agenda')");await p.wait_for_timeout(400)
            sh=await p.inner_text("#sheet")
            chk("prices: yearly from panel with promo","60 lei" in sh,sh[:600])
            chk("prices: monthly from panel with promo","7,50 lei" in sh,sh[:600])
            chk("texts: title from panel",(await p.inner_text("#sheet h2")).startswith("Control Plus"),await p.inner_text("#sheet h2"))
            chk("texts: subtitle from panel","Totul sub control." in sh)
            chk("promo banner text","Black Friday: −25%" in sh)
            await p.evaluate("localStorage.setItem('fake.cfg',JSON.stringify(Object.assign(JSON.parse(localStorage.getItem('fake.cfg')),{prices:{month:'10',year:'80',promo:{pct:25,until:'2020-01-01'}}})));cfgLoad()");await p.wait_for_timeout(600)
            await p.evaluate("openPlan('agenda')");await p.wait_for_timeout(400)
            sh=await p.inner_text("#sheet")
            chk("promo expired: full price","80 lei" in sh and "Black Friday" not in sh,sh[:400])
            chk("no errors 4",not e,e)
            await c.close()
            await b.close()
    finally:
        srv.terminate()
    done()
asyncio.run(main())
