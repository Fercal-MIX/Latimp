import asyncio, json
from playwright.async_api import async_playwright
SC="/tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/"
URL="file:///mnt/user-data/outputs/buzunar.html"
ok=[];bad=[]
def chk(n,c,e=""): (ok if c else bad).append(n+(" -> "+str(e)[:300] if (e and not c) else ""))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={"width":360,"height":820});pg=await ctx.new_page();errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.add_init_script(path=SC+"mock.js")
        await pg.goto(URL);await pg.wait_for_timeout(3000)
        await pg.evaluate("obSkip&&obSkip();closeSheet()");await pg.wait_for_timeout(500)
        await pg.evaluate("openPlan('free')");await pg.wait_for_timeout(300)
        t=await pg.inner_text("#sheet")
        chk("no unproven 'most chosen' label","Cel mai ales" not in t,t[:300])
        chk("factual best price label","Cel mai mic preț pe scânteie" in t)
        chk("pack prices in lei","lei" in t)
        await pg.evaluate("closeSheet();openPlan('agenda')");await pg.wait_for_timeout(300)
        t=await pg.inner_text("#sheet")
        chk("yearly plan label factual","Cel mai ales" not in t and "Mai ieftin pe lună" in t,t[:300])
        await pg.evaluate("PLAN='y';setPro(true)");await pg.wait_for_timeout(300)
        await pg.evaluate("openPlan('agenda')");await pg.wait_for_timeout(300)
        t=await pg.inner_text("#sheet")
        chk("rights shown next to subscription","Anulezi reînnoirea oricând" in t and "Retragere din contract (14 zile)" in t,t[:500])
        await pg.click("button:text-is('Retragere din contract (14 zile)')");await pg.wait_for_timeout(300)
        t=await pg.inner_text("#sheet")
        chk("withdrawal sheet explains 14 days","14 zile" in t and "Google Play" in t)
        await pg.click("button:text-is('Retrage-te din contract')");await pg.wait_for_timeout(400)
        chk("withdrawal opens prefilled report",await pg.evaluate("RK")=="Retragere din contract" and "retrag" in (await pg.evaluate("($('rt')||{}).value||''")))
        await pg.evaluate("closeSheet();S.sub.ren=plus(30);S.sub.auto=true;S.sub.pl='y';save()")
        r=await pg.evaluate("remPlan().filter(x=>/^lt-ren-/.test(x.tag)).length")
        chk("yearly renewal reminder 14 days before",r==1,r)
        chk("no errors",not errs,errs)
        await b.close()
    print("OK",len(ok),"FAIL",len(bad))
    for x in bad: print(" -",x)
asyncio.run(main())
