import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
from web import *
U="http://localhost:8784/"
ST={"onb":True,"at":5,"items":[{"id":"a1","g":"fac","t":"cur","n":"PPC","p":200,"d":"2030-01-10","rep":1}],"cars":[],"saved":[],"credits":0,"used":0,"photos":0,"theme":"auto","nt":{"d":7,"h":"09:00","rep":False,"n":3,"i":7,"day":False,"wk":False}}
CFG={"mon":{"free":False,"control":True},"prices":{"currency":"RON","month":"9,99","year":"79,99","trial_days":7}}
def acc(src=None,until=None,trial=None,founder=None,pro=None):
    return {"pro":bool(src) if pro is None else pro,"source":src,"until":until,"free_mode":False,"trial":trial or {"on":True,"days":7,"used":False,"until":None},"founder":founder}
async def mk(b,a,rpc_extra="",lang="ro",signed=True):
    c=await b.new_context(viewport={"width":390,"height":850},service_workers="block")
    await fake_route(c,fonts=True)
    st=dict(ST);st["lang"]=lang
    init="if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);localStorage.setItem('buzunar.v2',%s);"%(json.dumps(json.dumps(CFG)),json.dumps(json.dumps(st)))
    if signed: init+="localStorage.setItem('latimp.auth',JSON.stringify({user:{id:'u1',email:'ana@test.ro'},access_token:'t'}));"
    init+="}"
    await c.add_init_script(init)
    await c.add_init_script("window.__acc=%s;window.__rpc=Object.assign({get_my_access:async()=>window.__acc,am_i_admin:async()=>false,set_reminders:async(a)=>{window.__rem=a.p;return a.p.length}},{%s});"%(json.dumps(a),rpc_extra))
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(2400)
    return c,p,errs
def iso(days):
    import datetime;return (datetime.datetime.now(datetime.UTC).replace(tzinfo=None)+datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
async def main():
    srv=serve(8784)
    try:
      async with async_playwright() as pw:
        b=await pw.chromium.launch()
        # 1. proba: disponibilă, fără card, pornită din foaia Control
        START="start_trial:async()=>{window.__started=1;window.__acc=Object.assign({},window.__acc,{pro:true,source:'trial',until:'%s',trial:{on:true,days:7,used:true,until:'%s'}});return {ok:true,until:'%s',access:window.__acc}}"%(iso(7),iso(7),iso(7))
        c,p,e=await mk(b,acc(),START)
        await p.evaluate("openPlan('agenda')");await p.wait_for_timeout(300)
        t=await p.inner_text("#sheet")
        chk("Control sheet offers the free trial","Încearcă Control 7 zile gratuit" in t,t[:600])
        chk("trial says: no card, nothing charged automatically","Fără card" in t and "nu plătești nimic" in t)
        await p.click("#sheet button:text-is('Încearcă Control 7 zile gratuit')");await p.wait_for_timeout(500)
        t=await p.inner_text("#sheet")
        chk("trial started: confirmation explains it stops by itself","Proba Control a pornit" in t and "se oprește singur" in t,t[:400])
        chk("server asked once",await p.evaluate("window.__started")==1)
        chk("access now from the trial",await p.evaluate("accNow().source")=="trial")
        chk("no errors (trial)",not e,e)
        await c.close()
        # 2. proba folosită: butonul nu mai apare
        c,p,e=await mk(b,acc(trial={"on":True,"days":7,"used":True,"until":iso(-3)}))
        await p.evaluate("openPlan('agenda')");await p.wait_for_timeout(300)
        chk("used trial: no trial button","Încearcă Control" not in await p.inner_text("#sheet"))
        await c.close()
        # 3. plățile oprite (gratuit pentru toți): nimic despre probă
        c,p,e=await mk(b,acc(trial={"on":False,"days":0,"used":False,"until":None}))
        await p.evaluate("openPlan('agenda')");await p.wait_for_timeout(300)
        chk("payments off: no trial button","Încearcă Control" not in await p.inner_text("#sheet"))
        await c.close()
        # 4. ultimele zile din probă: cardul și memento-urile
        c,p,e=await mk(b,acc("trial",iso(1.5),{"on":True,"days":7,"used":True,"until":iso(1.5)}))
        await p.evaluate("FIL='all';tab('agenda')");await p.wait_for_timeout(400)
        t=await p.inner_text("#main")
        chk("Agenda card: trial ends soon, nothing charged automatically","Proba Control se termină" in t and "Nu se plătește nimic automat" in t,t[:500])
        await p.click("#main button:text-is('Am înțeles')");await p.wait_for_timeout(300)
        chk("card can be dismissed for today","Proba Control se termină" not in await p.inner_text("#main"))
        plan=await p.evaluate("remPlan().filter(x=>/^lt-trial-/.test(x.tag)).map(x=>x.body)")
        chk("trial reminder scheduled (before the end)",len(plan)>=1 and all("Nu se plătește nimic" in x for x in plan),plan)
        chk("no errors (trial card)",not e,e)
        await c.close()
        # 5. mulțumirea pentru primii utilizatori
        c,p,e=await mk(b,acc("bonus",iso(90),founder={"months":3,"until":iso(90)}))
        await p.evaluate("FIL='all';tab('agenda')");await p.wait_for_timeout(400)
        t=await p.inner_text("#main")
        chk("founders card: 3 months of free Control, no card","Mulțumim că ai fost printre primii" in t and "3 luni de Control gratuit" in t and "card" in t,t[:500])
        await p.click("#main button:text-is('Mulțumesc')");await p.wait_for_timeout(300)
        chk("founders card shown once",await p.evaluate("S.fdk")==1 and "printre primii" not in await p.inner_text("#main"))
        await c.close()
        # 6. retragerea legată de plata reală
        PUR="my_purchases:async()=>[{id:'ev1',product:'control_m',store:'web',price:9.99,currency:'RON',at:'%s',deadline:'%s',can_withdraw:true,withdrawal:null},{id:'ev2',product:'control_y',store:'web',price:79.99,currency:'RON',at:'%s',deadline:'%s',can_withdraw:false,withdrawal:null}],request_withdrawal:async(a)=>{window.__wd=a;return {ok:true,ref:'R7'}}"%(iso(-2),iso(12),iso(-30),iso(-16))
        c,p,e=await mk(b,acc("sub",iso(28)),PUR)
        await p.evaluate("wdOpen()");await p.wait_for_timeout(600)
        t=await p.inner_text("#sheet")
        chk("withdrawal lists the real web payments with deadlines","Control lunar, 9.99 RON" in t and "Te poți retrage până pe" in t and "Termenul de 14 zile a trecut" in t,t[:700])
        btns=await p.evaluate("[...document.querySelectorAll('#sheet button')].filter(b=>b.innerText=='Retrage-te').length")
        chk("only the eligible payment has a Withdraw button",btns==1,btns)
        await p.click("#sheet button:text-is('Retrage-te')");await p.wait_for_timeout(300)
        chk("asks for confirmation first","Te retragi din contract?" in await p.inner_text("#sheet"))
        await p.click("#sheet button:text-is('Da, trimite cererea')");await p.wait_for_timeout(500)
        t=await p.inner_text("#sheet")
        chk("request registered with a number and the refund deadline","R7" in t and "14 zile" in t,t[:400])
        chk("server got the right payment",await p.evaluate("window.__wd")=={"p_event":"ev1"})
        chk("no errors (withdrawal)",not e,e)
        await c.close()
        # 7. retragere refuzată (plata din magazin) + engleză
        PUR2="my_purchases:async()=>[{id:'ev3',product:'control_m',store:'web',price:9.99,currency:'RON',at:'%s',deadline:'%s',can_withdraw:true,withdrawal:null}],request_withdrawal:async()=>({ok:false,why:'late'})"%(iso(-2),iso(12))
        c,p,e=await mk(b,acc("sub",iso(28)),PUR2,lang="en")
        await p.evaluate("wdSend('ev3')");await p.wait_for_timeout(500)
        t=await p.inner_text("#sheet")
        chk("refusal explained (English)","We can't send the request" in t and "More than 14 days" in t,t[:300])
        await p.evaluate("openPlan('agenda')");await p.wait_for_timeout(300)
        await p.evaluate("closeSheet()")
        await c.close()
        c,p,e=await mk(b,acc(),START,lang="en")
        await p.evaluate("openPlan('agenda')");await p.wait_for_timeout(300)
        t=await p.inner_text("#sheet")
        chk("English: trial button and note","Try Control free for 7 days" in t and "No card" in t,t[:600])
        sw=await p.evaluate("document.documentElement.scrollWidth")
        chk("no horizontal overflow",sw<=390,sw)
        chk("no errors (English)",not e,e)
        await c.close()
        await b.close()
    finally:
        srv.terminate()
    done()
asyncio.run(main())
