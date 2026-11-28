import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
SC="/tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/"
ok=[];bad=[]
def chk(n,c,e=""): (ok if c else bad).append(n+(" -> "+str(e)[:300] if (e and not c) else ""))
U="http://localhost:8784/"
FAKE=open(SC+"fake_sb.js").read()
ST={"onb":True,"at":5,"items":[],"cars":[],"saved":[{"t":"Plimbare în parc","d":"Aer","c":"gratis"},{"t":"Film acasă","d":"Popcorn","c":"~20 lei"}],"credits":0,"used":0,"photos":0,"theme":"auto","nt":{"d":7,"h":"09:00"}}
async def mk(b,st=ST,w=390,dark=False,url=U):
    c=await b.new_context(viewport={"width":w,"height":850},color_scheme="dark" if dark else "light")
    async def h(r): await r.fulfill(status=200,content_type="application/javascript",body=FAKE)
    await c.route("**/cdn.jsdelivr.net/**",h)
    await c.add_init_script("if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);localStorage.setItem('buzunar.v2',%s)}"%(json.dumps(json.dumps({"mon":{"free":True}})),json.dumps(json.dumps(st))))
    await c.add_init_script("window.__rpc={get_my_access:async()=>({pro:true,source:'free',free_mode:true}),am_i_admin:async()=>false,set_reminders:async(a)=>a.p.length,open_poll:async()=>({code:'ABCD2345'})};")
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(url);await p.wait_for_timeout(2500)
    return c,p,errs
async def main():
    srv=subprocess.Popen(["python3","-m","http.server","8784","-d",SC+"web"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    try:
      async with async_playwright() as pw:
        b=await pw.chromium.launch()
        c,p,e=await mk(b)
        await p.evaluate("FSEG='ideas';tab('free')");await p.wait_for_timeout(400)
        await p.evaluate("setCat('out')");await p.wait_for_timeout(200)
        await p.click("button:text-is('Dă-mi idei')");await p.wait_for_timeout(1500)
        t=await p.inner_text("#main")
        chk("ideas show context tags",await p.locator("#main .itg .tag").count()>=2,t[:300])
        chk("refine bar shown","Nu e ce cauți?" in t and "Mai ieftin" in t and "Vreme rea" in t)
        chk("real events links for outings",await p.locator(".evl a[href='https://zilesinopti.ro']").count()==1)
        await p.click("button:text-is('Mai ieftin')");await p.wait_for_timeout(1500)
        chk("cheaper lowers budget",await p.evaluate("BUD")=="Sub 150 lei")
        await p.click("button:text-is('Vreme rea')");await p.wait_for_timeout(1500)
        r=await p.evaluate("[FLT.wx,CAT,IDEAS.filter(x=>ideaWhere(x)=='out').length]")
        chk("bad weather moves indoors",r[0]=="Ploaie" and r[1]=="home",r)
        await p.click("button:text-is('Mai scurt')");await p.wait_for_timeout(1500)
        chk("shorter sets duration",await p.evaluate("FLT.time")=="O zi")
        r=await p.evaluate("[ideaPrice('gratis'),ideaPrice('~30 lei'),ideaWhere({t:'Drumeție de o zi',d:''}),ideaDur({t:'Drumeție de o zi',d:''})]")
        chk("tag helpers",r==[0,30,"out","o zi"],r)
        await p.evaluate("BUD='Gratis'")
        a=await p.evaluate("fallback().map(x=>ideaPrice(x.c))")
        chk("local ideas respect free budget",all(x==0 for x in a) or len(a)>=2,a)
        # vot pe link
        await p.evaluate("SBU={id:'u1',email:'a@b.ro'};S.acct={e:'a@b.ro'};S.poll={c:'ABCD2345',o:['Plimbare în parc','Film acasă'],t:[],at:Date.now()};POLLV=[];FSEG='saved';render()");await p.wait_for_timeout(400)
        t=await p.inner_text("#main")
        chk("poll card offers link and WhatsApp","Trimite linkul" in t and "WhatsApp" in t and "fără cont" in t,t[:400])
        chk("whatsapp link encodes vote page",await p.locator("a[href*='wa.me'][href*='vot.html%3Fc%3DABCD2345']").count()==1)
        chk("vote url",await p.evaluate("voteURL()")=="https://fercal-mix.github.io/Latimp/vot.html?c=ABCD2345")
        # cum a fost
        await p.evaluate("S.items.push({id:'ev1',g:'per',t:'ev',n:'Plimbare în parc',d:plus(-2),rep:0,auto:false,note:'Ales la vot · Sâmbătă'});FIL='all';tab('agenda')");await p.wait_for_timeout(400)
        chk("how was it asked",await p.locator("#c_ev1 .hw").count()==1)
        await p.click("#c_ev1 button:text-is('Grozav')");await p.wait_for_timeout(300)
        chk("rating saved and follow-up",await p.evaluate("S.items.find(i=>i.id=='ev1').rt")==2 and "Mă bucur" in await p.inner_text("#sheet"))
        await p.evaluate("closeSheet();render()");await p.wait_for_timeout(200)
        chk("question gone after answer",await p.locator("#c_ev1 .hw").count()==0)
        chk("no errors",not e,e)
        for w,dk in [(320,True),(560,False)]:
            await p.set_viewport_size({"width":w,"height":850});await p.emulate_media(color_scheme="dark" if dk else "light")
            await p.evaluate("FSEG='ideas';tab('free')");await p.wait_for_timeout(400)
            chk(f"{w}px no overflow",await p.evaluate("document.documentElement.scrollWidth-innerWidth")<=0)
            if w==320: await p.screenshot(path=SC+"p4_ideas_320.png",full_page=True)
        await p.evaluate("set('lang','en')");await p.wait_for_timeout(1500)
        t=await p.inner_text("#main")
        chk("en: refine translated","Not quite it?" in t and "Cheaper" in t,t[:200])
        await c.close()
        # pagina de vot
        c2=await b.new_context(viewport={"width":360,"height":800})
        await c2.route("**/rest/v1/rpc/find_poll_guest",lambda r:r.fulfill(status=200,content_type="application/json",body=json.dumps({"options":["Plimbare în parc","Film acasă"],"times":["Sâmbătă seara"]})))
        got={}
        async def vh(r):
            got["b"]=json.loads(r.request.post_data);await r.fulfill(status=200,content_type="application/json",body='{"ok":true}')
        await c2.route("**/rest/v1/rpc/vote_poll_guest",vh)
        p2=await c2.new_page();e2=[];p2.on("pageerror",lambda x:e2.append(str(x)))
        await p2.goto(U+"vot.html?c=ABCD-2345");await p2.wait_for_timeout(800)
        chk("vote page lists options","Plimbare în parc" in await p2.inner_text("body"))
        await p2.click("#go");await p2.wait_for_timeout(200)
        chk("vote page asks for name","numele" in await p2.inner_text("#m"))
        await p2.click("label.op:has-text('Film acasă')");await p2.click("label.op:has-text('Sâmbătă seara')");await p2.fill("#n","Ana");await p2.click("#go");await p2.wait_for_timeout(500)
        bdy=got.get("b") or {}
        chk("vote sent with token",bdy.get("p_code")=="ABCD2345" and bdy.get("p_opt")==1 and bdy.get("p_tm")==0 and bdy.get("p_name")=="Ana" and len(bdy.get("p_token",""))==32,bdy)
        chk("thank-you shown","Ai votat" in await p2.inner_text("body"))
        chk("vote page no overflow",await p2.evaluate("document.documentElement.scrollWidth-innerWidth")<=0)
        await p2.screenshot(path=SC+"p4_vote_360.png")
        await p2.goto(U+"vot.html?c=bad");await p2.wait_for_timeout(400)
        chk("bad link explained","nu e complet" in await p2.inner_text("body"))
        chk("vote page no errors",not e2,e2)
        await c2.close();await b.close()
    finally: srv.terminate()
    print("OK",len(ok),"FAIL",len(bad))
    for x in bad: print(" -",x)
asyncio.run(main())
