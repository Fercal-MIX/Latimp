import asyncio, json, re
from playwright.async_api import async_playwright
SC="/tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/"
URL="file:///mnt/user-data/outputs/buzunar.html"
ok=[];bad=[]
def chk(n,c,e=""): (ok if c else bad).append(n+(" -> "+str(e)[:300] if (e and not c) else ""))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={"width":390,"height":820}); pg=await ctx.new_page(); errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.add_init_script(path=SC+"mock.js"); await pg.goto(URL); await pg.wait_for_timeout(3000)
        await pg.click("#sheet button:has-text('Sări peste')"); await pg.wait_for_timeout(500)
        ev=pg.evaluate; M=lambda: pg.inner_text("#main")
        await ev("S.nt.d=30;S.items=[{id:'s1',g:'sub',t:'sub',e:'🎬',n:'Netflix',p:40,c:'m',d:plus(40)},{id:'r1',g:'auto',t:'rca',n:'Logan',car:'c1',d:plus(3),rep:12},{id:'r2',g:'auto',t:'itp',n:'Logan',car:'c1',d:plus(20),rep:24}];S.cars=[{id:'c1',n:'Logan'}];save();FIL='all';CALV='list';render()"); await pg.wait_for_timeout(400)
        # 5
        t=await pg.inner_text("#c_s1")
        chk("subscription card: Detalii first, cancelling is secondary","Detalii" in t and "Marchează de anulat" in t and "Editează" not in t and "Vreau să-l anulez" not in t,t)
        await pg.click("#c_s1 >> text=Marchează de anulat"); await pg.wait_for_timeout(200)
        chk("mark toggles",await ev("S.items.find(x=>x.id=='s1').k===true") and "Îl păstrez" in await pg.inner_text("#c_s1"))
        await pg.click("#c_s1 >> text=Detalii"); await pg.wait_for_timeout(200)
        chk("Detalii opens the editor",await ev("$('sheet').dataset.k")=="item")
        await ev("closeSheet()")
        # 6
        chk("near suggestion stays open",await ev("!document.querySelector('#c_r1 details.sgd')&&!!document.querySelector('#c_r1 .sg')"))
        chk("far suggestion is collapsed",await ev("!!document.querySelector('#c_r2 details.sgd:not([open])')") and "ITP de făcut" in await pg.inner_text("#c_r2"))
        # 7
        await pg.click("#main .hd >> button.pill"); await pg.wait_for_timeout(300)
        chk("focus moves into the sheet",await ev("!!document.activeElement.closest('#sheet')"))
        chk("background is inert while the sheet is open",await ev("document.querySelector('.w').inert&&document.querySelector('.nav').inert"))
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(300)
        chk("focus returns to the button that opened it",await ev("document.activeElement&&document.activeElement.classList.contains('pill')"))
        chk("background active again",await ev("!document.querySelector('.w').inert"))
        await ev("tab('more')"); await pg.wait_for_timeout(600)
        hit=await ev("(()=>{const s=document.querySelector('#main .sw');s.scrollIntoView({block:'center'});const r=s.getBoundingClientRect();const e1=document.elementFromPoint(r.left+r.width/2,r.top-6),e2=document.elementFromPoint(r.left+r.width/2,r.bottom+6);return [e1===s,e2===s,Math.round(r.height)]})()")
        chk("switches have a 44px touch area",hit[0] and hit[1],hit)
        # 8
        await ev("S.pro=true;S.items=[];for(let i=0;i<150;i++)S.items.push({id:'p'+i,g:'per',t:'prog',n:'P'+i,d:plus(i+1),rep:0});save();FIL='all';LIM=60;tab('agenda')"); await pg.wait_for_timeout(700)
        chk("long list shows 60 and a button",await ev("document.querySelectorAll('#main .lg .li').length")==60 and "Arată încă 60 din 90" in await M())
        await pg.click("#main >> text=Arată încă 60 din 90"); await pg.wait_for_timeout(300)
        chk("button shows more",await ev("document.querySelectorAll('#main .lg .li').length")==120)
        await ev("S.items=[];for(let i=0;i<500;i++)S.items.push({id:'q'+i,g:'per',t:'prog',n:'Q'+i,d:plus(i%400),rep:0});LIM=60;save()")
        ms=await ev("(()=>{const t=performance.now();render();return Math.round(performance.now()-t)})()")
        chk("500 dates render fast (<120 ms)",ms<120,ms)
        chk("long weekends computed once per day",await ev("breaks()===breaks()"))
        # 9
        r=json.loads(await ev("JSON.stringify(qaParse('ziua lui Ion 29 februarie'))"))
        chk("29 February goes to the next leap year",r["d"]=="2028-02-29",r)
        # 10
        await ev("S.items=[{id:'d1',g:'per',t:'zi',n:'Ana',d:plus(5),rep:12,auto:true},{id:'d2',g:'per',t:'zi',n:'ana',d:plus(50),rep:12,auto:true}];save();pOpen('ana')"); await pg.wait_for_timeout(200)
        chk("same name twice: the profile explains how to separate them","schimbă numele unuia" in await pg.inner_text("#sheet"))
        await ev("closeSheet()")
        # 12
        await ev("window.__aifail=true;S.lang='en';save();langApply();FSEG='ideas';CAT='home';SIT='h1';tab('free')"); await pg.wait_for_timeout(700)
        await pg.click("#main >> button:text-is('Give me ideas')"); await pg.wait_for_timeout(1500)
        t=await M()
        chk("fallback ideas in English","Blanket fort in the living room" in t or "Pizza workshop at home" in t,t[-600:])
        await ev("S.lang='ro';langApply();window.__aifail=false")
        chk("no page errors",not errs,errs)
        await ctx.close(); await b.close()
    print("OK",len(ok),"FAIL",len(bad))
    for x in bad: print("  FAIL:",x)
asyncio.run(main())
