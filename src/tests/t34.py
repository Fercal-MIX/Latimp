import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
from web import *
U="http://localhost:8783/"
async def mk(b,st=None,ua=None):
    kw={"viewport":{"width":390,"height":850}}
    if ua: kw["user_agent"]=ua
    c=await b.new_context(**kw)
    await fake_route(c)
    init="if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);"%json.dumps(json.dumps({"mon":{"free":True}}))
    if st: init+="localStorage.setItem('buzunar.v2',%s);"%json.dumps(json.dumps(st))
    await c.add_init_script(init+"}")
    await c.add_init_script("window.__rpc={get_my_access:async()=>({pro:true,source:'free',free_mode:true}),am_i_admin:async()=>false,set_reminders:async(a)=>a.p.length};")
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(3000)
    return c,p,errs
async def main():
    srv=serve(8783)
    try:
      async with async_playwright() as pw:
        b=await pw.chromium.launch()
        c,p,e=await mk(b)
        t=await p.inner_text("#sheet")
        chk("onboarding says no bank access","Nu cerem acces la contul tău bancar" in t,t[:300])
        await p.evaluate("drawOb()");await p.wait_for_timeout(300)
        chk("note survives redraw","Nu cerem acces" in await p.inner_text("#sheet"))
        await p.evaluate("obSkip()");await p.wait_for_timeout(800)
        await p.evaluate("closeSheet()");await p.wait_for_timeout(300)
        k=await p.evaluate("fsSteps().map(s=>s.k)")
        chk("first steps: item, reminders, install, idea (Android/desktop)",k==["add","nt","inst","idea"],k)
        # recapitulare lunară
        await p.evaluate("S.items.push({id:'a',g:'fis',t:'imp',n:'',d:fmt(new Date(td().getFullYear(),td().getMonth()+1,20)),rep:12,p:500,ad:20,note:''});S.nt.mail=true;save()")
        r=await p.evaluate("mrPlan()")
        chk("monthly recap planned on the 1st",len(r)>=1 and r[0]["title"]=="Luna ta" and "1 termen" not in r[0]["body"] and "un termen" in r[0]["body"] and "500" in r[0]["body"],r[:1])
        chk("monthly recap in reminders",await p.evaluate("remPlan().some(x=>/^lt-mr-/.test(x.tag))"))
        await p.evaluate("notifGo()");await p.wait_for_timeout(500)
        chk("recap toggle in other messages","Recapitulare lunară" in await p.inner_text("#main"))
        await p.evaluate("mrTg()")
        chk("recap can be turned off",await p.evaluate("mrPlan().length")==0)
        chk("no errors",not e,e);await c.close()
        c,p,e=await mk(b,None,"Mozilla/5.0 (iPhone; CPU iPhone OS 18_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Mobile/15E148 Safari/604.1")
        await p.evaluate("obSkip()");await p.wait_for_timeout(800);await p.evaluate("closeSheet()")
        k=await p.evaluate("fsSteps().map(s=>s.k)")
        chk("first steps on iPhone: install before reminders",k==["add","inst","nt","idea"],k)
        chk("no errors (iPhone)",not e,e);await c.close()
        await b.close()
    finally: srv.terminate()
    done()
asyncio.run(main())
