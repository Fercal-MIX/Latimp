import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
SC="/tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/"
ok=[];bad=[]
def chk(n,c,e=""): (ok if c else bad).append(n+(" -> "+str(e)[:300] if (e and not c) else ""))
U="http://localhost:8783/"
FAKE=open(SC+"fake_sb.js").read()
ST={"onb":True,"at":5,"items":[{"id":"ex1","g":"sub","t":"sub","n":"Netflix","p":50,"c":"m","d":"2030-01-01","ex":True}],"cars":[{"id":"c1","n":"B 1 ABC","eu":"e6"}],"saved":[],"credits":0,"used":0,"photos":0,"theme":"auto","nt":{"d":7,"h":"09:00","rep":False,"n":3,"i":7,"day":False,"wk":False}}
# prognoza simulată: azi ploaie, sâmbătă senin
WX="""(()=>{const f=n=>{const d=new Date();d.setHours(0,0,0,0);d.setDate(d.getDate()+n);return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')};
 const days=[0,1,2,3,4,5,6].map(n=>({d:f(n),mn:8,mx:14,pr:0,wet:0,sy:'clearsky_day'}));days[0]={d:f(0),mn:6,mx:11,pr:4.2,wet:6,sy:'rain'};
 window.__wxCalls=0;window.__wxDays=days.slice(0,4);
 const sat=(6-new Date().getDay()+7)%7;if(sat>0&&sat<4)window.__wxDays[sat]={d:f(sat),mn:10,mx:18,pr:0,wet:0,sy:'clearsky_day'};
 return {wx_start:async(a)=>{window.__wxCalls++;window.__wxArgs=a;return {status:'wait'}},wx_poll:async()=>({status:'ok',data:{now:{tp:9,sy:'rain'},days:window.__wxDays,src:'MET Norway'}})}})()"""
async def mk(b,lang="ro",geo=True):
    c=await b.new_context(viewport={"width":390,"height":850},permissions=["geolocation"] if geo else [],geolocation={"latitude":44.4268,"longitude":26.1025})
    async def h(r): await r.fulfill(status=200,content_type="application/javascript",body=FAKE)
    await c.route("**/cdn.jsdelivr.net/**",h)
    st=dict(ST);st["lang"]=lang
    await c.add_init_script("if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);localStorage.setItem('buzunar.v2',%s)}"%(json.dumps(json.dumps({"mon":{"free":True}})),json.dumps(json.dumps(st))))
    await c.add_init_script("window.__rpc=Object.assign({get_my_access:async()=>({pro:true,source:'free',free_mode:true}),am_i_admin:async()=>false},"+WX+");")
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(2500)
    return c,p,errs
async def main():
    srv=subprocess.Popen(["python3","-m","http.server","8783","-d",SC+"web"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    try:
      async with async_playwright() as pw:
        b=await pw.chromium.launch()
        c,p,e=await mk(b)
        # ---- reguli verificate ----
        r=await p.evaluate("(()=>{const R=RL();return [R.rov.p12.e6,R.rov.p[1].ev,R.rov.p[30].e45,R.rov.p[60].e03,R.v]})()")
        chk("vignette tariffs from 1 Oct 2026 (12 months, 1 day, 30 days, 60 days)",r[:4]==[254,20,55,99],r)
        await p.evaluate("FIL='auto';tab('agenda');editItem();setT('rov')");await p.wait_for_timeout(300)
        await p.select_option("#f_dur","30");await p.wait_for_timeout(300)
        t=await p.inner_text("#sheet")
        chk("vignette form shows the price for the chosen duration and Euro norm","Pentru 30 de zile: 48 lei" in t and "1 octombrie 2026" in t,t[-500:])
        chk("vignette note lists all official channels","etoll.ro" in t and "TollRo" in t and "SMS" in t and "doar de pe" not in t)
        await p.select_option("#f_dur","365");await p.wait_for_timeout(300)
        t=await p.inner_text("#sheet")
        chk("12 months price: 254 lei for Euro 6","Pentru 12 luni: 254 lei" in t,t[-300:])
        tips=await p.evaluate("RL().tips")
        chk("RCA tip: registration certificate and plates kept","certificatul de înmatriculare și plăcuțele" in tips["rca"])
        chk("PAD tip: renewal continues next day, fine 100–500 lei","ziua următoare" in tips["pad"] and "100–500" in tips["pad"])
        chk("gas tip: no unverified fine amounts","2.000–4.000" not in tips["igz"] and "opri gazul" in tips["igz"])
        chk("tax return tip: the 3% bonus is not promised for every year","verifică pe ANAF" in tips["du"])
        chk("ID tip: CEI price and the 3 August 2031 limit","70 de lei" in tips["ci"] and "cel mult până la 3 august 2031" in tips["ci"] and "Din 1 august 2026" not in tips["ci"])
        await p.evaluate("closeSheet();FIL='doc';editItem();setT('ci')");await p.wait_for_timeout(200)
        await p.check("#f_old");await p.evaluate("grab();cur.old=true;drawItem(false)");await p.wait_for_timeout(200)
        t=await p.inner_text("#sheet")
        chk("old ID note: valid at most until 3 August 2031","cel mult până la 3 august 2031" in t,t[-300:])
        await p.evaluate("closeSheet()")
        # ---- vremea automată ----
        await p.evaluate("FSEG='ideas';tab('free')");await p.wait_for_timeout(600)
        t=await p.inner_text("#main")
        chk("weather offer appears in Free time","Vremea automată" in t and "cam 10 km" in t,t[:600])
        await p.click("#main button:text-is('Pornește')");await p.wait_for_timeout(2600)
        t=await p.inner_text("#main")
        chk("forecast shown: today's range and words","Azi: 6…11°, ploaie" in t and "Acum 9°" in t,t[:700])
        chk("MET Norway credited with a link",await p.evaluate("!!document.querySelector('#main a[href=\"https://www.met.no/en\"]')"))
        chk("ideas filter set automatically to Rain",await p.evaluate("FLT.wx")=="Ploaie")
        chk("card says the ideas take it into account","Ideile țin cont de asta: „Ploaie”" in t)
        a=await p.evaluate("window.__wxArgs")
        chk("only the rounded location (0.1°) goes to the server",a=={"p_lat":44.4,"p_lon":26.1},a)
        st=await p.evaluate("localStorage.getItem('buzunar.v2')")
        chk("location is not stored in the synced agenda","44.4" not in st and "26.1" not in st)
        # alegerea manuală câștigă
        await p.evaluate("tg('wx','Senin')");await p.wait_for_timeout(300)
        chk("manual choice wins over automatic",await p.evaluate("FLT.wx")=="Senin" and await p.evaluate("WXA")==False)
        await p.evaluate("render()");await p.wait_for_timeout(200)
        chk("manual choice kept after redraw",await p.evaluate("FLT.wx")=="Senin")
        # cache 1 oră: fără cerere nouă la redeschidere
        n0=await p.evaluate("window.__wxCalls");await p.evaluate("tab('agenda')");await p.evaluate("tab('free')");await p.wait_for_timeout(800)
        chk("forecast is reused for an hour (no new request)",await p.evaluate("window.__wxCalls")==n0)
        # ideile locale respectă vremea automată
        await p.evaluate("tg('wx','Senin');WXA=false;FLT.wx='';WXA=false;render()");await p.wait_for_timeout(300)
        chk("clearing the manual choice brings the automatic one back",await p.evaluate("FLT.wx")=="Ploaie")
        await p.evaluate("askIdeas()");await p.wait_for_timeout(1500)
        ideas=await p.evaluate("IDEAS.map(x=>ideaWhere(x))")
        chk("rainy day: no outdoor ideas",ideas and all(w!="out" for w in ideas),ideas)
        # oprire
        await p.click("#main .wxs button");await p.wait_for_timeout(300)
        t=await p.inner_text("#main")
        chk("turning it off removes the card and the automatic filter","Azi:" not in t and "Vremea automată" not in t and await p.evaluate("FLT.wx")=="",t[:300])
        chk("turned off is remembered",await p.evaluate("JSON.parse(localStorage.getItem('latimp.wx')).no===1"))
        sw=await p.evaluate("document.documentElement.scrollWidth")
        chk("no horizontal overflow at 390",sw<=390,sw)
        chk("no page errors",not e,e)
        await c.close()
        # ---- engleză + locație refuzată ----
        c,p,e=await mk(b,"en",geo=False)
        await p.evaluate("FSEG='ideas';tab('free')");await p.wait_for_timeout(600)
        t=await p.inner_text("#main")
        chk("English: weather offer translated","Automatic weather" in t and "about 10 km" in t,t[:500])
        await p.evaluate("wxPut({on:1,la:44.4,lo:26.1});wxLoad(true)");await p.wait_for_timeout(2600)
        t=await p.inner_text("#main")
        chk("English: forecast line translated","Today: 6…11°, rain" in t and "Now 9°" in t and "“Rain”" in t,t[:600])
        await p.evaluate("wxPut(null);render()")
        await p.evaluate("void(navigator.geolocation.getCurrentPosition=(ok,no)=>no({code:1}))")
        await p.wait_for_timeout(300);bt=await p.evaluate("[...document.querySelectorAll('#main .card button')].map(b=>b.innerText).slice(0,4)")
        chk("English: Start button on the weather card",any(x.strip()=="Turn on" for x in bt),bt)
        await p.evaluate("[...document.querySelectorAll('#main .card button')].find(b=>/wxOn/.test(b.getAttribute('onclick')||'')).click()");await p.wait_for_timeout(600)
        t=await p.inner_text("body")
        chk("denied location: clear message, nothing saved","location" in t.lower() and await p.evaluate("!(JSON.parse(localStorage.getItem('latimp.wx')||'{}').on)"),t[-300:])
        chk("no page errors (English)",not e,e)
        await c.close()
        # ---- prototipul (fără server): fără card de vreme ----
        c=await b.new_context(viewport={"width":390,"height":850});await c.add_init_script(path=SC+"mock.js")
        p=await c.new_page();await p.goto("file:///mnt/user-data/outputs/buzunar.html");await p.wait_for_timeout(2500)
        await p.evaluate("S.onb=true;FSEG='ideas';tab('free')");await p.wait_for_timeout(400)
        chk("prototype without server: no weather card","Vremea automată" not in await p.inner_text("#main"))
        await c.close()
        await b.close()
    finally:
        srv.terminate()
    print("OK",len(ok),"FAIL",len(bad))
    for x in bad: print(" -",x)
asyncio.run(main())
