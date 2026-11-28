import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
from web import *
# t31: planurile pe funcții din panou (Planuri): oprite, gratuite, Control, planuri create, lansare, fără catalog
U="http://localhost:8769/"
TIERS=[{"id":"free","name":"Gratuit","builtin":True},{"id":"control","name":"Control","builtin":True},{"id":"sparks","name":"Scântei","builtin":True,"kind":"use"},
       {"id":"familie","name":"Familie","color":"#2f6f9f","desc":"Agenda comună pentru toată familia","price_month":"14.99","includes":["control"],"sale":False}]
FEAT={"budget":{"name":"Bugetul lunii","group":"agenda","tier":"off"},"monthly_total":{"name":"Totalul lunar","group":"agenda","tier":"free"},
      "steps":{"name":"Pași pe termen","group":"agenda","tier":"free"},"cat_extra":{"name":"Categorii extra","group":"agenda","tier":"control"},
      "car_km":{"name":"Mașina pe kilometri","group":"agenda","tier":"control"},"family":{"name":"Agendă comună în familie","group":"family","tier":"familie"},
      "photo_read":{"name":"Citire din poză (AI)","group":"tools","tier":"off"},"reminders_extra":{"name":"Memento-uri multiple","group":"notif","tier":"off"},
      "weekly_summary":{"name":"Rezumat săptămânal","group":"notif","tier":"control"},"search":{"name":"Căutare","group":"tools","tier":"free","rollout":25},
      "export":{"name":"Copie în fișier","group":"account","tier":"control","fixed":"GDPR"}}
PLANS={"tiers":TIERS,"features":FEAT,"limits":{"free_items":0,"free_reminders":1}}
FREE={"mon":{"free":True,"control":False,"sparks":False,"invites":False,"referrals":False},"maint":{"on":False},"plans":PLANS}
PAID={"mon":{"free":False,"control":True,"sparks":True,"invites":True,"referrals":True},"maint":{"on":False},"plans":PLANS}
NOCAT={"mon":{"free":False,"control":True,"sparks":True,"invites":True,"referrals":True},"maint":{"on":False}}
ST=json.dumps({"onb":True,"at":5,"items":[{"id":"a1","g":"sub","t":"sub","n":"Netflix","p":40,"c":"m","d":"2027-01-10"},{"id":"a2","g":"auto","t":"ulei","n":"","car":"c1","d":"2027-03-01","rep":12,"kmi":15000,"kml":100000}],
  "cars":[{"id":"c1","n":"Mașina mea","km":105000}],"saved":[],"credits":0,"used":0,"photos":0,"theme":"auto","nt":{"d":7,"h":"09:00","rep":True,"n":3,"i":2,"day":True,"wk":True}})
async def mk(b,cfg,signed=False,rpc="",w=390):
    c=await b.new_context(viewport={"width":w,"height":800},service_workers="block")
    await fake_route(c,fonts=True)
    init="if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);localStorage.setItem('buzunar.v2',%s);"%(json.dumps(json.dumps(cfg)),json.dumps(ST))
    if signed: init+="localStorage.setItem('latimp.auth',JSON.stringify({user:{id:'u1',email:'ana@test.ro'},access_token:'t'}));"
    init+="}"
    await c.add_init_script(init)
    if rpc: await c.add_init_script(rpc)
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(2200)
    return c,p,errs
async def main():
    srv=serve(8769)
    try:
        async with async_playwright() as pw:
            b=await pw.chromium.launch()
            # A. lansare gratuită, fără cont: totul deschis, în afară de ce e oprit
            c,p,e=await mk(b,FREE)
            chk("A free mode: Control features open",await p.evaluate("S.pro===true&&can('cat_extra')&&can('car_km')&&can('weekly_summary')"))
            chk("A free mode: custom plan feature open",await p.evaluate("can('family')"))
            chk("A off feature hidden even in free mode",await p.evaluate("!can('budget')&&fHid('budget')&&budCard()===''"))
            chk("A off photo reading: entry flag off",await p.evaluate("CFG.flags.photo===false&&CFG.flags.fam!==false"))
            chk("A rollout feature hidden without account",await p.evaluate("fHid('search')&&!can('search')"))
            chk("A fixed feature always free",await p.evaluate("can('export')&&!fHid('export')"))
            await p.evaluate("tab('more');VIEW='notif';render()");await p.wait_for_timeout(500)
            t=await p.inner_text("#main")
            chk("A notifications: repeat rows hidden when off","Repetă memento-ul" not in t and "Și în ziua termenului" not in t,t[:300])
            chk("A notifications: weekly summary still shown","Rezumat săptămânal" in t)
            chk("A reminders: off extra reminders not applied",await p.evaluate("remDays().length===1"))
            await p.evaluate("photoStart()");await p.wait_for_timeout(300)
            chk("A photo start refused when off","nu este disponibilă" in await p.inner_text("#toast"))
            chk("A no errors",not e,e);await c.close()
            # B. plăți pornite, fără cont: gratuit vs Control vs plan creat
            c,p,e=await mk(b,PAID)
            chk("B not pro",await p.evaluate("S.pro===false"))
            chk("B free-tier feature usable without Control",await p.evaluate("can('steps')&&can('monthly_total')&&moneyCard()!==''"))
            chk("B Control feature locked",await p.evaluate("!can('cat_extra')&&!can('car_km')&&kmLine(S.items[1])===''"))
            chk("B tag names the plan",await p.evaluate("ptag('car_km')===' (Control)'&&ptag('family')===' (Familie)'&&ptag('steps')===''"))
            await p.evaluate("setG('fac')");await p.wait_for_timeout(500)
            chk("B paid category opens Control sheet","Control" in await p.inner_text("#sheet"))
            await p.evaluate("closeSheet()");await p.wait_for_timeout(300)
            await p.evaluate("famOpen()");await p.wait_for_timeout(500)
            sh=await p.inner_text("#sheet")
            chk("B custom plan sheet: name, description, features, price","Familie" in sh and "Agenda comună pentru toată familia" in sh and "Agendă comună în familie" in sh and "14.99" in sh,sh[:300])
            chk("B custom plan not on sale: says not available yet","nu este disponibil încă" in sh)
            sw=await p.evaluate("document.documentElement.scrollWidth")
            chk("B sheet fits 390px",sw<=390,sw)
            await p.evaluate("closeSheet()");await p.wait_for_timeout(300)
            await p.evaluate("ntSet('wk')");await p.wait_for_timeout(600)
            chk("B weekly summary toggle goes to Control plan",await p.evaluate("S.nt.wk===true"))
            chk("B no errors",not e,e);await c.close()
            # C. cu cont: serverul decide (planuri, lansare)
            RPC="""window.__rpc={am_i_admin:async()=>false,get_my_access:async()=>({pro:false,source:null,tiers:['free','familie','control'],
              unlocked:['monthly_total','steps','cat_extra','car_km','family','weekly_summary','export']})};"""
            c,p,e=await mk(b,PAID,signed=True,rpc=RPC)
            chk("C plan with Control included: pro",await p.evaluate("S.pro===true"))
            chk("C server unlocks custom plan feature",await p.evaluate("can('family')&&can('cat_extra')"))
            chk("C rollout feature outside group hidden",await p.evaluate("fHid('search')&&!can('search')"))
            chk("C off feature stays hidden",await p.evaluate("fHid('budget')"))
            chk("C no errors",not e,e);await c.close()
            RPC2="""window.__rpc={am_i_admin:async()=>false,get_my_access:async()=>({pro:false,source:null,tiers:['free'],unlocked:['monthly_total','steps','export','search']})};"""
            c,p,e=await mk(b,PAID,signed=True,rpc=RPC2)
            chk("C2 free user: rollout feature shown when server unlocks it",await p.evaluate("can('search')&&!fHid('search')"))
            chk("C2 free user: plan feature locked, not hidden",await p.evaluate("!can('family')&&!fHid('family')"))
            await c.close()
            # D. fără catalog în panou: totul ca înainte (Control = abonament)
            c,p,e=await mk(b,NOCAT)
            chk("D no catalog: can follows Control",await p.evaluate("S.pro===false&&!can('steps')&&!can('anything')&&ptag('steps')===' (Control)'"))
            chk("D no catalog: budget card like before",await p.evaluate("budCard()===''&&!fHid('budget')"))
            chk("D no errors",not e,e);await c.close()
            # E. engleză
            c,p,e=await mk(b,PAID)
            await p.evaluate("new Promise(r=>LT_EN(()=>{S.lang='en';save();render();r()}))");await p.wait_for_timeout(800)
            await p.evaluate("famOpen()");await p.wait_for_timeout(600)
            sh=await p.inner_text("#sheet")
            chk("E English plan sheet","isn't available yet" in sh and "included" in sh,sh[:300])
            chk("E no errors",not e,e);await c.close()
            # F. 320 px
            c,p,e=await mk(b,PAID,w=320)
            await p.evaluate("famOpen()");await p.wait_for_timeout(500)
            sw=await p.evaluate("document.documentElement.scrollWidth")
            chk("F sheet fits 320px",sw<=320,sw)
            await c.close()
            await b.close()
    finally:
        srv.terminate()
    done()
asyncio.run(main())
