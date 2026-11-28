import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
SC="/tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/"
ok=[];bad=[]
def chk(n,c,e=""): (ok if c else bad).append(n+(" -> "+str(e)[:300] if (e and not c) else ""))
U="http://localhost:8782/"
FAKE=open(SC+"fake_sb.js").read()
ST={"onb":True,"at":5,"items":[{"id":"ex1","g":"sub","t":"sub","n":"Netflix","p":50,"c":"m","d":"2030-01-01","ex":True}],"cars":[],"saved":[],"credits":0,"used":0,"photos":0,"theme":"auto","nt":{"d":7,"h":"09:00","rep":False,"n":3,"i":7,"day":False,"wk":False}}
async def mk(b,st=ST,url=U,w=390,dark=False):
    c=await b.new_context(viewport={"width":w,"height":850},color_scheme="dark" if dark else "light",permissions=["notifications"])
    async def h(r): await r.fulfill(status=200,content_type="application/javascript",body=FAKE)
    await c.route("**/cdn.jsdelivr.net/**",h)
    await c.add_init_script("if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);localStorage.setItem('buzunar.v2',%s)}"%(json.dumps(json.dumps({"mon":{"free":True},"news":{"on":True,"title":"Noutate test","body":"Text","audience":"all","at":"2026-11-28T10:00:00Z"}})),json.dumps(json.dumps(st))))
    await c.add_init_script("try{Object.defineProperty(Notification,'permission',{get:()=>'default'})}catch(e){}")
    await c.add_init_script("window.__rpc={get_my_access:async()=>({pro:true,source:'free',free_mode:true}),am_i_admin:async()=>false,set_reminders:async(a)=>{window.__rem=a.p;return a.p.length}};")
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(url);await p.wait_for_timeout(2500)
    return c,p,errs
async def main():
    srv=subprocess.Popen(["python3","-m","http.server","8782","-d",SC+"web"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    try:
      async with async_playwright() as pw:
        b=await pw.chromium.launch()
        c,p,e=await mk(b)
        # 1. primul termen adevărat → întrebarea despre memento-uri
        await p.evaluate("FIL='auto';editItem()");await p.wait_for_timeout(300)
        t=await p.inner_text("#sheet")
        chk("form shows reminder path","Memento:" in t and "doar când deschizi aplicația" in t,t[-400:])
        await p.fill("#f_n","B 1 XYZ");await p.fill("#f_d",await p.evaluate("plus(20)"))
        await p.click("#sheet button:text-is('Salvează')");await p.wait_for_timeout(1000)
        t=await p.inner_text("#sheet")
        chk("priming sheet after first real item","Vrei să-ți amintim la timp?" in t and "Da, trimite-mi notificări" in t,t[:600]+" STATE="+str(await p.evaluate("pushState()+'|'+Notification.permission+'|'+pushOk()")))
        chk("priming names the item and time","ITP" in t and "09:00" in t,t[:300])
        await p.click("#sheet button:text-is('Mai târziu')");await p.wait_for_timeout(300)
        chk("asked only once",await p.evaluate("!!S.nt.ask"))
        await p.evaluate("FIL='auto';editItem()");await p.wait_for_timeout(200)
        await p.evaluate("setCar('new')");await p.fill("#f_n","B 2 XYZ");await p.fill("#f_d",await p.evaluate("plus(25)"))
        await p.click("#sheet button:text-is('Salvează')");await p.wait_for_timeout(900)
        chk("no second priming",await p.evaluate("$('sheet').dataset.k")!="prime")
        await p.evaluate("closeSheet();S.items.push({id:'soon',g:'auto',t:'rca',n:'B 3',d:plus(4),rep:12,note:''});FIL='all';render()");await p.wait_for_timeout(300)
        chk("card warns when no channel",await p.locator(".tag:text-is('memento doar în aplicație')").count()>=1)
        # 2. eticheta notificării: termenul și butonul
        await p.evaluate("S.nt.mail=true;save()")
        tags=await p.evaluate("remPlan().map(r=>r.tag)")
        chk("reminder tag carries item and action",any(__import__('re').match(r"^lt-\d+~[a-z0-9]+~r$",t) for t in tags),tags[:3])
        await p.evaluate("render()");await p.wait_for_timeout(200)
        chk("no warning with a channel",await p.locator(".tag:text-is('memento doar în aplicație')").count()==0)
        # 3. memento de test peste o oră
        await p.evaluate("notifGo()");await p.wait_for_timeout(500)
        t=await p.inner_text("#main")
        chk("notifications: important documents toggle","Memento din timp pentru actele importante" in t)
        chk("notifications: other messages group","Alte mesaje, nu memento-uri" in t and "Anunțuri LaTimp" in t,t[-500:])
        await p.click("button:text-is('Programează')");await p.wait_for_timeout(400)
        r=await p.evaluate("remPlan()[0]")
        chk("test reminder planned in one hour",r["tag"].startswith("lt-test-") and abs(__import__('datetime').datetime.fromisoformat(r["at"].replace("Z","+00:00")).timestamp()-time.time()-3600)<120,r)
        chk("test reminder status shown","Programat la" in await p.inner_text("#main"))
        await p.click("button:text-is('Anulează')");await p.wait_for_timeout(300)
        chk("test reminder cancelled",not await p.evaluate("remPlan().some(r=>/^lt-test/.test(r.tag))"))
        # 4. anunțurile se pot opri
        await p.evaluate("VIEW='main';tab('agenda')");await p.wait_for_timeout(400)
        n1=await p.evaluate("newsCard().length")
        await p.evaluate("newsTg()")
        chk("news can be turned off",n1>0 and await p.evaluate("newsCard()")=="",n1)
        await p.evaluate("newsTg()")
        # 5. memento timpuriu oprit
        await p.evaluate("S.items.push({id:'rc1',g:'auto',t:'rca',n:'B 1 XYZ',d:plus(50),rep:12,note:''});S.nt.smart=false;save()")
        chk("early reminder can be turned off",30 not in await p.evaluate("remDays(S.items.find(i=>i.id=='rc1'))"))
        await p.evaluate("S.nt.smart=true;save()")
        chk("no errors (1)",not e,e)
        await c.close()
        # 6. notificarea deschide termenul și „Am reînnoit”
        st=dict(ST);st["items"]=[{"id":"it1","g":"auto","t":"itp","n":"B 1 XYZ","d":"2026-12-10","rep":24,"note":""}]
        c,p,e=await mk(b,st,U+"?from=push&it=it1&done=1")
        await p.wait_for_timeout(1500)
        t=await p.inner_text("#sheet")
        chk("push link opens confirm sheet","Am reînnoit?" in t and "B 1 XYZ" in t,t[:200])
        chk("URL cleaned",await p.evaluate("location.search")=="")
        await p.click("#sheet button:text-is('Am reînnoit')");await p.wait_for_timeout(500)
        chk("renewed after confirm",await p.evaluate("S.items[0].d")=="2028-12-10")
        chk("no errors (2)",not e,e)
        await c.close()
        # 7. service worker
        sw=open(SC+"web/sw.js").read()
        chk("sw shows actions and posts item to app","o.actions=d.actions" in sw and "postMessage" in sw and 'searchParams.set("done","1")' in sw)
        # 8. engleză + ecrane mici
        c,p,e=await mk(b,dict(ST,lang="en"))
        await p.evaluate("notifGo()");await p.wait_for_timeout(800)
        t=await p.inner_text("#main")
        chk("en: notifications translated","Other messages, not reminders" in t and "Test reminder in an hour" in t,t[-400:])
        for w in [320,560]:
            await p.set_viewport_size({"width":w,"height":850});await p.wait_for_timeout(200)
            chk(f"{w}px no overflow",await p.evaluate("document.documentElement.scrollWidth-innerWidth")<=0)
        await p.set_viewport_size({"width":320,"height":850});await p.evaluate("set('lang','ro');S.nt.ask='';closeSheet();primeOpen&&S.items.push({id:'z',g:'auto',t:'rca',n:'B 9',d:plus(9),rep:12,note:''});primeOpen()");await p.wait_for_timeout(400)
        await p.screenshot(path=SC+"p2_prime_320.png")
        chk("no errors (3)",not e,e)
        await c.close();await b.close()
    finally: srv.terminate()
    print("OK",len(ok),"FAIL",len(bad))
    for x in bad: print(" -",x)
asyncio.run(main())
