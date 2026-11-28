import asyncio
from playwright.async_api import async_playwright
from web import *
OL="(el=>{const c=getComputedStyle(el);return c.outlineStyle=='none'||parseFloat(c.outlineWidth)==0?'none':c.outlineStyle+' '+c.outlineWidth})"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(**p.devices["Pixel 7"]);pg=await ctx.new_page();errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.add_init_script(path=SC+"mock.js")
        await pg.goto("file:///mnt/user-data/outputs/buzunar.html");await pg.wait_for_selector("#sheet button:has-text('Sări peste')",timeout=15000);await pg.wait_for_timeout(500)
        h=await pg.evaluate("(()=>{const a=document.activeElement;return a.tagName})()")
        chk("onboarding title focused for screen readers",h=="H2",h)
        chk("no ring on programmatically focused sheet title",await pg.evaluate(OL+"(document.activeElement)")=="none",await pg.evaluate(OL+"(document.activeElement)"))
        await pg.tap("#sheet button:has-text('Sări peste')");await pg.wait_for_timeout(900)
        await pg.tap("#t-free");await pg.wait_for_timeout(900)
        # simulează Android: butonul atins primește focus vizibil
        await pg.evaluate("document.getElementById('t-free').focus({focusVisible:true})")
        fv=await pg.evaluate("document.getElementById('t-free').matches(':focus-visible')")
        chk("tapped nav button shows no frame",await pg.evaluate(OL+"(document.getElementById('t-free'))")=="none",(fv,await pg.evaluate(OL+"(document.getElementById('t-free'))")))
        th=await pg.evaluate("getComputedStyle(document.getElementById('t-agenda')).webkitTapHighlightColor")
        chk("no tap highlight box on buttons",th in ("rgba(0, 0, 0, 0)","transparent"),th)
        seg=await pg.evaluate("(()=>{const b=document.querySelector('.seg.full button');return b?getComputedStyle(b).webkitTapHighlightColor:''})()")
        chk("no tap highlight on menu segments",seg in ("rgba(0, 0, 0, 0)","transparent"),seg)
        # tastatura păstrează inelul de focus
        await pg.keyboard.press("Tab");await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('t-more').focus({focusVisible:true})")
        chk("keyboard users still see focus ring",await pg.evaluate(OL+"(document.getElementById('t-more'))")!="none",await pg.evaluate(OL+"(document.getElementById('t-more'))"))
        chk("no page errors",not errs,errs)
        await b.close()
    done()
asyncio.run(main())
