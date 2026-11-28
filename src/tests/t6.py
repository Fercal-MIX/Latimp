import asyncio
from playwright.async_api import async_playwright
from web import *
async def tok(page,n): return await page.evaluate(f"getComputedStyle(document.documentElement).getPropertyValue('{n}').trim()")
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for scheme in ["light","dark"]:
            ctx=await b.new_context(viewport={"width":390,"height":800},color_scheme=scheme)
            page=await ctx.new_page();errs=[]
            page.on("pageerror",lambda e:errs.append(str(e)))
            await page.add_init_script(path=SC+"mock.js")
            await page.goto("file:///mnt/user-data/outputs/buzunar.html");await page.wait_for_timeout(3000)
            await page.click("#sheet button:has-text('Sări peste')");await page.wait_for_timeout(1000)
            chk(scheme+": title LaTimp",await page.title()=="LaTimp")
            fr={"light":("rgb(58, 75, 94)","rgb(138, 88, 0)","rgb(239, 241, 242)"),"dark":("rgb(169, 189, 211)","rgb(230, 181, 96)","rgb(15, 18, 21)")}[scheme]
            exp={"light":("rgb(23, 102, 74)","rgb(176, 61, 11)","rgb(244, 242, 234)"),"dark":("rgb(116, 211, 163)","rgb(242, 154, 110)","rgb(14, 17, 11)")}[scheme]
            chk(scheme+": free plan marked",await page.evaluate("document.documentElement.dataset.plan")=="free")
            chk(scheme+": free = Grafit și Ocru",await tok(page,"--a1")==fr[0] and await tok(page,"--a2")==fr[1],(await tok(page,"--a1"),await tok(page,"--a2")))
            chk(scheme+": free background",await page.evaluate("getComputedStyle(document.body).backgroundColor")==fr[2],await page.evaluate("getComputedStyle(document.body).backgroundColor"))
            sp=await page.evaluate("(()=>{let d=document.getElementById('spl'),t=!d;if(t){d=document.createElement('div');d.id='spl';document.body.append(d)}const v=getComputedStyle(d).backgroundImage;if(t)d.remove();return v})()")
            chk(scheme+": splash keeps brand forest","17, 82, 58" in sp or "13, 74, 51" in sp,sp)
            await page.evaluate("openPlan('agenda')");await page.wait_for_timeout(700)
            sa=await page.evaluate("getComputedStyle(document.getElementById('sheet')).getPropertyValue('--a1').trim()")
            chk(scheme+": Control sheet shown in forest to free users",sa==exp[0],sa)
            chk(scheme+": compare row for colours","Culorile aplicației" in await page.inner_text("#sheet"))
            await page.evaluate("openPlan('free')");await page.wait_for_timeout(500)
            sb=await page.evaluate("getComputedStyle(document.getElementById('sheet')).getPropertyValue('--a1').trim()")
            chk(scheme+": sparks sheet keeps free colours",sb==fr[0],sb)
            await page.evaluate("closeSheet()");await page.wait_for_timeout(500)
            await page.screenshot(path=SC+f"g_{scheme}_a.png")
            await page.evaluate("S.pro=true;save();render()");await page.wait_for_timeout(1400)
            chk(scheme+": Control marked",await page.evaluate("document.documentElement.dataset.plan")=="ctl")
            chk(scheme+": Pădure & Teracotă tokens",await tok(page,"--a1")==exp[0] and await tok(page,"--a2")==exp[1],(await tok(page,"--a1"),await tok(page,"--a2")))
            chk(scheme+": body background",await page.evaluate("getComputedStyle(document.body).backgroundColor")==exp[2],await page.evaluate("getComputedStyle(document.body).backgroundColor"))
            chk(scheme+": no data-pal attribute",await page.evaluate("document.documentElement.getAttribute('data-pal')")is None)
            await page.click("#t-more");await page.wait_for_timeout(800)
            t=await page.inner_text("#main")
            chk(scheme+": no palette picker left","Paletă de culori" not in t and "Smarald" not in t)
            chk(scheme+": footer LaTimp","LaTimp, versiune prototip" in t)
            chk(scheme+": theme setting still there","Temă" in t)
            await page.screenshot(path=SC+f"f_{scheme}_m.png")
            await page.click("#t-agenda");await page.wait_for_timeout(900);await page.evaluate("scrollTo(0,0)");await page.wait_for_timeout(200);await page.screenshot(path=SC+f"f_{scheme}_a.png")
            await page.click("#t-free");await page.wait_for_timeout(900);await page.evaluate("scrollTo(0,0)");await page.wait_for_timeout(200);await page.screenshot(path=SC+f"f_{scheme}_f.png")
            ow=await page.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth+1")
            chk(scheme+": no overflow",not ow);chk(scheme+": no page errors",not errs,errs)
            await ctx.close()
        # an old saved state that still carries pal:"cob" must not break anything
        ctx=await b.new_context(viewport={"width":390,"height":800})
        page=await ctx.new_page();errs=[]
        page.on("pageerror",lambda e:errs.append(str(e)))
        await page.add_init_script(path=SC+"mock.js")
        await page.add_init_script("localStorage.setItem('buzunar.v2',JSON.stringify({pal:'cob',items:[],onb:true,at:1,credits:0,used:0,photos:0,theme:'auto',warn:30,cars:[],saved:[]}))")
        await page.goto("file:///mnt/user-data/outputs/buzunar.html");await page.wait_for_timeout(2500)
        chk("old pal key ignored",await tok(page,"--a1")=="rgb(58, 75, 94)" and not errs,errs)
        await ctx.close();await b.close()
    done()
asyncio.run(main())
