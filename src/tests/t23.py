import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
SC="/tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/"
ok=[];bad=[]
def chk(n,c,e=""): (ok if c else bad).append(n+(" -> "+str(e)[:300] if (e and not c) else ""))
U="http://localhost:8770/"
FAKE=open(SC+"fake_sb.js").read()
CFG={"mon":{"free":True,"control":False,"sparks":False,"invites":False,"referrals":False}}
async def mk(b,signed=True,cnt=None,rpl=None,stats=True):
    c=await b.new_context(viewport={"width":390,"height":800},service_workers="block")
    async def h(r): await r.fulfill(status=200,content_type="application/javascript",body=FAKE)
    await c.route("**/cdn.jsdelivr.net/**",h);await c.route("**/fonts.googleapis.com/**",lambda r:r.abort())
    st={"onb":True,"at":5,"items":[{"id":"a","g":"sub","t":"sub","n":"Netflix secret","p":40,"c":"m","d":"2027-01-10"}],"cars":[],"saved":[],"credits":0,"used":0,"photos":0,"theme":"auto","stats":stats,"st":{"first":"2026-11-01","days":{"2026-11-26":1,"2026-11-27":1},"adds":3,"reads":1,"taps":{"budget":2}},"acct":{"p":"email","e":"ana@test.ro","v":True} if signed else None,"ch":{"on":True,"m":{}}}
    init="if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);localStorage.setItem('buzunar.v2',%s);"%(json.dumps(json.dumps(CFG)),json.dumps(json.dumps(st)))
    if cnt: init+="localStorage.setItem('fake.cnt',%s);"%json.dumps(json.dumps(cnt))
    if rpl: init+="localStorage.setItem('fake.rpl',%s);"%json.dumps(json.dumps(rpl))
    if signed: init+="localStorage.setItem('latimp.auth',JSON.stringify({user:{id:'u1',email:'ana@test.ro'},access_token:'t'}));"
    init+="}window.__rpc={get_my_access:async()=>({pro:true,source:'free'}),am_i_admin:async()=>false,set_reminders:async()=>0};"
    await c.add_init_script(init)
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(2500)
    return c,p,errs
LS=lambda k:"JSON.parse(localStorage.getItem('%s')||'null')"%k
async def main():
    srv=subprocess.Popen(["python3","-m","http.server","8770","-d",SC+"web"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    try:
        async with async_playwright() as pw:
            b=await pw.chromium.launch()
            mk_=await pw.chromium.launch()
            # statistici
            c,p,e=await mk(b)
            await p.evaluate("save()");await p.wait_for_timeout(9500)
            u=await p.evaluate(LS("fake.ust"))
            chk("usage stats sent with consent",u and u["user_id"]=="u1" and u["data"]["items"]==1 and u["data"]["days"]==2 and u["data"].get("budget")==2,u)
            chk("stats carry no agenda content",u and "Netflix" not in json.dumps(u))
            await p.evaluate("S.stats=false;save()");await p.wait_for_timeout(9500)
            chk("stats removed when consent withdrawn",await p.evaluate(LS("fake.ust")) is None)
            # erori
            await p.evaluate("setTimeout(()=>{throw new Error('Test boom pentru ana@test.ro')},10)");await p.wait_for_timeout(1200)
            er=await p.evaluate(LS("fake.err")) or []
            chk("uncaught error reported",any("Test boom" in x["message"] for x in er),er)
            chk("e-mail removed from error",all("ana@test.ro" not in x["message"] for x in er))
            chk("error has version and platform",er and er[-1]["ver"]==await p.evaluate("VER") and er[-1]["platform"].startswith("web-"))
            # raport cu captură
            await p.evaluate("reportOpen()");await p.wait_for_timeout(400)
            await p.click("#sheet .chips button:text-is('Idee')");await p.fill("#rt","Ar fi bine să pot sorta după preț.")
            await p.set_input_files("#rs",SC+"shot_test.png");await p.wait_for_timeout(800)
            await p.click("#sheet button:has-text('Trimite raportul')");await p.wait_for_timeout(1200)
            rp=(await p.evaluate(LS("fake.rep")) or [])
            up=(await p.evaluate(LS("fake.up")) or [])
            chk("report sent to panel",rp and rp[-1]["kind"]=="idea" and "sorta" in rp[-1]["body"] and rp[-1]["user_id"]=="u1",rp)
            chk("screenshot uploaded in own folder",up and up[-1]["b"]=="report-shots" and up[-1]["p"].startswith("u1/") and rp and rp[-1]["shot_path"]==up[-1]["p"],(up,rp))
            chk("report has no status or reply fields",rp and "status" not in rp[-1] and "reply" not in rp[-1])
            chk("A no errors",[x for x in e if "Test boom" not in x]==[],e);await c.close()
            # fără cont: raportul cere conectare
            c,p,e=await mk(b,signed=False)
            await p.evaluate("reportOpen()");await p.wait_for_timeout(400)
            t=await p.inner_text("#sheet");chk("report asks to sign in","conectează-te la cont" in t and "Trimite raportul" not in t,t[:200])
            await c.close()
            # răspunsuri
            c,p,e=await mk(b,rpl=[{"id":"r1","kind":"bug","body":"Nu merge X","reply":"Am reparat, mulțumim!","replied_at":"2026-11-27T10:00:00Z","created_at":"2026-11-26T10:00:00Z"}])
            try: await p.wait_for_function("RPL.length>0",timeout=8000)
            except Exception: print("DBG",await p.evaluate("[RPL.length,!!SBU,!!SB,ACC&&ACC.source,typeof window.supabase]"))
            await p.evaluate("tab('more')");await p.wait_for_timeout(900)
            chk("new reply shown in More","Ai un răspuns nou" in await p.inner_text("#main"),(await p.inner_text("#main"))[:300]+str(await p.evaluate("[RPL.length,!!SBU,typeof rplLoad]")))
            await p.evaluate("rplOpen()");await p.wait_for_timeout(500)
            chk("reply sheet","Am reparat, mulțumim!" in await p.inner_text("#sheet") and "Nu merge X" in await p.inner_text("#sheet"))
            await p.evaluate("closeSheet();render()");await p.wait_for_timeout(500)
            chk("reply marked as seen","Răspunsuri la rapoarte" in await p.inner_text("#main") and "răspuns nou" not in await p.inner_text("#main"))
            await c.close()
            # conținut din panou
            mk0=await p.evaluate("1") if False else None
            CNT={"challenge":{"month":"__M__","title":"Un muzeu nou","text":"Alege un muzeu în care n-ai fost.","steps":["Caută programul","Mergi cu un prieten"]},"fallback_ideas":["Plimbare în parc",{"title":"Seară de jocuri","text":"Scoate jocurile de societate."}],"try_lists":[{"name":"Filme de iarnă","items":["Home Alone","Klaus"]}]}
            c,p,e=await mk(b,cnt=CNT)
            m=await p.evaluate("mKey()");CNT["challenge"]["month"]=m
            await p.evaluate("localStorage.setItem('fake.cnt',%s);cntLoad()"%json.dumps(json.dumps(CNT)));await p.wait_for_timeout(700)
            await p.evaluate("tab('free')");await p.wait_for_timeout(900)
            await p.evaluate("FSEG='ideas';render()");await p.wait_for_timeout(600)
            t=await p.inner_text("#main")
            chk("challenge of the month from panel","Un muzeu nou" in t and "Caută programul" in t,t[-500:])
            await p.evaluate("FSEG='saved';render()");await p.wait_for_timeout(600)
            t=await p.inner_text("#main")
            chk("list suggestions shown","Propuneri pentru liste" in t and "+ Klaus" in t)
            await p.click("#main button:has-text('+ Klaus')");await p.wait_for_timeout(500)
            chk("suggestion added to open list",await p.evaluate("S.tl.some(x=>x.n=='Klaus')") and "+ Klaus" not in await p.inner_text("#main"))
            fb=await p.evaluate("fallback().map(x=>x.t)")
            chk("fallback ideas from panel",set(fb)=={"Plimbare în parc","Seară de jocuri"},fb)
            chk("content kept for offline",(await p.evaluate(LS("latimp.cnt")))["challenge"]["title"]=="Un muzeu nou")
            await p.evaluate("S.lang='en';save();langApply();tab('more')");await p.wait_for_timeout(600)
            chk("C no errors",not e,e)
            await c.close();await b.close();await mk_.close()
    finally: srv.terminate()
    print("OK",len(ok));print("FAIL",len(bad))
    for x in bad:print(" -",x)
asyncio.run(main())
