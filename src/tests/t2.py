import asyncio, datetime
from playwright.async_api import async_playwright
SC="/tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/"
def d(n): return (datetime.date.today()+datetime.timedelta(days=n)).isoformat()
ok=[];bad=[]
def chk(n,c,e=""): (ok if c else bad).append(n+(" -> "+str(e) if (e and not c) else ""))
async def run(b,init,name,fn,w=360,scheme="light"):
    ctx=await b.new_context(viewport={"width":w,"height":780},color_scheme=scheme)
    page=await ctx.new_page();errs=[]
    page.on("pageerror",lambda e:errs.append(str(e)))
    await page.add_init_script(path=SC+"mock.js")
    if init: await page.add_init_script(init)
    await page.goto("file:///mnt/user-data/outputs/buzunar.html")
    await page.wait_for_timeout(3000)
    await fn(page)
    ow=await page.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth+1")
    chk(name+": no horizontal overflow",not ow)
    chk(name+": no page errors",not errs,errs)
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # 1. no capabilities at all (signed out / opened outside viewer)
        async def f1(page):
            t=await page.inner_text("body")
            chk("nocaps: onboarding still opens","Ce să ținem minte" in await page.inner_text("#sheet"))
            await page.click("#sheet button:has-text('Sări peste')")
            t=await page.inner_text("body")
            chk("nocaps: examples visible","Netflix" in t)
            chk("nocaps: no photo button","Din poză" not in t)
            await page.click("#t-more"); await page.wait_for_timeout(500)
            t=await page.inner_text("body")
            chk("nocaps: local only text","Doar pe acest dispozitiv" in t)
            chk("nocaps: no csv","Exportă agenda" not in t)
            await page.wait_for_timeout(200)
            chk("nocaps: dev refused",("Opțiuni dezvoltator" not in await page.inner_text(".grp >> nth=-1")) )
            await page.click("text=Raportează o problemă")
            chk("nocaps: report send disabled",await page.is_disabled("#sheet >> text=Trimite raportul"))
        await run(b,"window.__nocaps=true","nocaps",f1)
        # 2. non-admin signed in
        async def f2(page):
            await page.click("#sheet button:has-text('Sări peste')")
            await page.click("#t-more")
            await page.wait_for_timeout(200)
            t=await page.inner_text("body")
            chk("nonadmin: no dev group","Dezvoltator" not in t)
            chk("nonadmin: sync ok","Copie salvată" in t or "Se verifică" in t,t[:200])
        await run(b,"window.__admin=false","nonadmin",f2)
        # 3. AI failing -> local fallbacks, nothing consumed
        async def f3(page):
            await page.click("#sheet button:has-text('Sări peste')")
            await page.click("#t-free"); await page.wait_for_timeout(500); await page.click("#main >> button:text-is('Dă-mi idei')"); await page.wait_for_timeout(600)
            t=await page.inner_text("body")
            chk("aifail: local ideas","Cort din pături" in t and "nu s-a consumat nimic" in t)
            chk("aifail: quota intact","3 din 3 gratuite rămase azi" in t,t[:400])
            await page.click(".seg.full >> text=Cadouri"); await page.wait_for_timeout(500); await page.click("text=Dă-mi idei de cadouri"); await page.wait_for_timeout(600)
            t=await page.inner_text("body")
            chk("aifail: gift fallback","O experiență împreună" in t)
        await run(b,"window.__aifail=true","aifail",f3)
        # 4. photo failure -> manual message; free photo limit
        async def f4(page):
            await page.click("#sheet button:has-text('Sări peste')")
            await page.click("text=Din poză")
            await page.click("#sheet >> text=Sunt de acord")
            await page.set_input_files("#ph",files=[{"name":"x.txt","mimeType":"image/jpeg","buffer":b"not an image"}])
            await page.wait_for_timeout(800)
            chk("badphoto: message","Nu am putut citi poza" in await page.inner_text("#phs"))
            await page.evaluate("S.photos=3;save()"); await page.click("#sheet >> text=Renunță"); await page.click("text=Din poză")
            chk("photo limit opens Control","Control" in await page.inner_text("#sheet"))
        await run(b,"","photo-fail",f4)
        # 5. limit of free items
        async def f5(page):
            await page.click("#sheet button:has-text('Sări peste')")
            await page.evaluate("S.items=S.items.filter(x=>!x.ex);for(let i=0;i<FREE_ITEMS;i++)S.items.push({id:'q'+i,g:'per',t:'prog',n:'P'+i,d:plus(40+i),rep:0});save();render()")
            await page.click("#main >> button.btn:text-is('Adaugă')")
            chk("limit: Control sheet",("nelimitate" in await page.inner_text("#sheet") and "Control" in await page.inner_text("#sheet")))
            await page.click("#sheet >> text=Activează Control"); await page.click("#main >> button.btn:text-is('Adaugă')")
            chk("pro: add sheet opens","Termen nou" in await page.inner_text("#sheet"))
        await run(b,"","limit",f5)
        # 6. overdue + roll + dark theme screenshot
        async def f6(page):
            await page.click("#sheet button:has-text('Sări peste')")
            await page.evaluate("S.items=[{id:'o1',g:'auto',t:'rca',n:'B 1 ABC',d:plus(-3),rep:12},{id:'o2',g:'per',t:'zi',n:'Ana',d:plus(-10),rep:12,auto:true},{id:'o3',g:'sub',t:'sub',e:'🎬',n:'Netflix',p:40,c:'m',d:plus(-2)},{id:'o4',g:'auto',t:'ulei',n:'',d:plus(1),rep:12}];save();render()")
            t=await page.inner_text("body")
            chk("overdue label","expirat de 3 zile" in t,t[:600])
            chk("birthday rolled to future","Ana" in t and "a trecut de" not in t)
            chk("sub rolled","Netflix" in t and "expirat de 2" not in t)
            await page.click("text=Am reînnoit >> nth=0"); await page.wait_for_timeout(200)
            t=await page.inner_text("body")
            chk("renew moves date","expirat de 3 zile" not in t)
            await page.screenshot(path=SC+"s_dark.png")
        await run(b,"","overdue",f6,scheme="dark")
        await b.close()
    print("OK",len(ok));print("FAIL",len(bad))
    for x in bad:print(" -",x)
asyncio.run(main())
