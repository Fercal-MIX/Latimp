import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
SC="/tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/"
ok=[];bad=[]
def chk(n,c,e=""): (ok if c else bad).append(n+(" -> "+str(e)[:300] if (e and not c) else ""))
U="http://localhost:8783/"
FAKE=open(SC+"fake_sb.js").read()
async def mk(b,st=None,ua=None):
    kw={"viewport":{"width":390,"height":850}}
    if ua: kw["user_agent"]=ua
    c=await b.new_context(**kw)
    async def h(r): await r.fulfill(status=200,content_type="application/javascript",body=FAKE)
    await c.route("**/cdn.jsdelivr.net/**",h)
    init="if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);"%json.dumps(json.dumps({"mon":{"free":True}}))
    if st: init+="localStorage.setItem('buzunar.v2',%s);"%json.dumps(json.dumps(st))
    await c.add_init_script(init+"}")
    await c.add_init_script("window.__rpc={get_my_access:async()=>({pro:true,source:'free',free_mode:true}),am_i_admin:async()=>false,set_reminders:async(a)=>a.p.length};")
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(3000)
    return c,p,errs
async def main():
    srv=subprocess.Popen(["python3","-m","http.server","8783","-d",SC+"web"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
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
    print("OK",len(ok),"FAIL",len(bad))
    for x in bad: print(" -",x)
asyncio.run(main())
