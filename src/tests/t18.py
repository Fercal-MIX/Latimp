import asyncio,subprocess,json,time,os
from playwright.async_api import async_playwright
SC="/tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/"
ok=[];bad=[]
def chk(n,c,e=""): (ok if c else bad).append(n+(" -> "+str(e)[:300] if (e and not c) else ""))
U="http://localhost:8765/"
async def skip(pg):
    for t in ["Sări peste","Mai târziu"]:
        if await pg.locator(f"#sheet button:has-text('{t}')").count() and await pg.evaluate("$('ov').classList.contains('on')"):
            await pg.click(f"#sheet button:has-text('{t}')");await pg.wait_for_timeout(800)
async def main():
    srv=subprocess.Popen(["python3","-m","http.server","8765","-d",SC+"web"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            ctx=await b.new_context(viewport={"width":390,"height":800},accept_downloads=True)
            pg=await ctx.new_page();errs=[]
            pg.on("pageerror",lambda e:errs.append(str(e)))
            await pg.goto(U);await pg.wait_for_timeout(3000)
            chk("doctype + lang",await pg.evaluate("document.doctype&&document.doctype.name")=="html" and await pg.evaluate("document.documentElement.lang")=="ro")
            chk("title",await pg.title()=="LaTimp")
            man=await pg.evaluate("fetch(document.querySelector('link[rel=manifest]').href).then(r=>r.json())")
            chk("manifest name + standalone",man["name"]=="LaTimp" and man["display"]=="standalone")
            for ic in man["icons"]:
                st=await pg.evaluate(f"fetch('{ic['src']}').then(r=>r.status)");chk("icon "+ic["src"],st==200,st)
            chk("maskable icon",any(i.get("purpose")=="maskable" for i in man["icons"]))
            chk("apple touch icon",await pg.evaluate("fetch(document.querySelector('link[rel=apple-touch-icon]').href).then(r=>r.status)")==200)
            chk("web mode on",await pg.evaluate("WEB===true"))
            await pg.evaluate("navigator.serviceWorker.ready");await pg.reload();await pg.wait_for_timeout(2500)
            chk("service worker controls page",await pg.evaluate("!!navigator.serviceWorker.controller"))
            # prima pornire
            await skip(pg)
            chk("agenda renders",await pg.locator("#main h1").inner_text()=="Agendă")
            await pg.click("#t-more");await pg.wait_for_timeout(900)
            t=await pg.inner_text("#main")
            chk("install card in More","Instalează LaTimp pe telefon" in t,t[:200])
            chk("footer says test version","versiune de test 1.19" in t)
            await pg.click("#main .ins button:has-text('Instalează')");await pg.wait_for_timeout(700)
            chk("install steps sheet",await pg.evaluate("$('sheet').dataset.k")=="inst" and "Instalează LaTimp" in await pg.inner_text("#sheet"))
            await pg.evaluate("closeSheet()");await pg.wait_for_timeout(400)
            async with pg.expect_download() as di:
                await pg.evaluate("exportCsv()")
            d=await di.value;chk("CSV download works in browser",d.suggested_filename=="latimp-agenda.csv",d.suggested_filename)
            await pg.click("#main .ins .x");await pg.wait_for_timeout(500)
            chk("install card can be hidden","Instalează LaTimp pe telefon" not in await pg.inner_text("#main"))
            await pg.evaluate("lsSet('latimp.cfg',{mon:{free:true}});CFGW=lsGet('latimp.cfg');tab('agenda')");await pg.wait_for_timeout(1500)
            t=await pg.inner_text("#main")
            chk("no widget/calendar-sync on web","Widget pe ecranul telefonului" not in t and "Sincronizare cu calendarul" not in t and "Calendar și widget" not in t)
            chk("calendar file still offered","Alerte în calendarul telefonului" in t)
            tc=await pg.evaluate("document.querySelector('meta[name=theme-color]').content")
            chk("theme-color follows background",tc==await pg.evaluate("getComputedStyle(document.body).backgroundColor"),tc)
            # fără internet
            await ctx.set_offline(True);await pg.reload();await pg.wait_for_timeout(2500)
            chk("works offline",await pg.locator("#main h1").count()==1 and await pg.evaluate("S.pro===true"))
            await ctx.set_offline(False)
            # engleză
            await pg.evaluate("S.lang='en';save();langApply();tab('more')");await pg.wait_for_timeout(1200)
            t=await pg.inner_text("#main");chk("EN footer","test version 1.19" in t,t[-120:])
            chk("no page errors",not errs,errs)
            await ctx.close()
            for w in [320,360,560]:
                for sc in ["light","dark"]:
                    c2=await b.new_context(viewport={"width":w,"height":760},color_scheme=sc);p2=await c2.new_page()
                    await p2.goto(U);await p2.wait_for_timeout(2600)
                    await skip(p2)
                    for tb in ["more","agenda","free"]:
                        await p2.click("#t-"+tb);await p2.wait_for_timeout(800)
                        ow=await p2.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth+1")
                        chk(f"{w} {sc} {tb} no overflow",not ow)
                    if w==360:await p2.click("#t-more");await p2.wait_for_timeout(800);await p2.screenshot(path=SC+f"w_{sc}_more.png")
                    await c2.close()
            await b.close()
    finally:
        srv.terminate()
    print("OK",len(ok));print("FAIL",len(bad))
    for x in bad:print(" -",x)
asyncio.run(main())
