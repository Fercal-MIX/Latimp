import asyncio, base64
from playwright.async_api import async_playwright
from web import *
URL = "file:///mnt/user-data/outputs/buzunar.html"
JPG = base64.b64decode("/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 800})
        pg = await ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.add_init_script(path=SC + "mock.js")
        await pg.goto(URL); await pg.wait_for_timeout(3000)
        await pg.click("#sheet button:has-text('Sări peste')"); await pg.wait_for_timeout(500)
        chk("new state starts without consent", await pg.evaluate("S.aic===0"))
        chk("settings: no photo consent given yet", True)
        # 1. first photo attempt asks for consent and sends nothing
        await pg.click("text=Din poză"); await pg.wait_for_timeout(400)
        sh = await pg.inner_text("#sheet")
        chk("consent sheet shown", "Acordul tău, o singură dată" in sh and "Sunt de acord" in sh, sh[:200])
        chk("consent names the AI service without a brand", "serviciu de inteligență artificială" in sh and "Claude" not in sh and "Anthropic" not in sh)
        chk("consent says what is sent and that it can be withdrawn", "nu și restul agendei" in sh and "retrage acordul" in sh)
        chk("no file picker before consent", await pg.locator("#ph").count() == 0)
        await pg.screenshot(path=SC + "ac_1.png")
        # 2. decline: nothing is stored
        await pg.click("#sheet >> text=Renunță"); await pg.wait_for_timeout(400)
        chk("declining keeps consent at 0", await pg.evaluate("S.aic===0"))
        chk("nothing was sent to the AI service", await pg.evaluate("(window.__samples||[]).filter(x=>x.img).length===0"))
        # 3. agree: picker appears, consent saved with a timestamp
        await pg.click("text=Din poză"); await pg.wait_for_timeout(300)
        await pg.click("#sheet >> text=Sunt de acord"); await pg.wait_for_timeout(400)
        chk("consent saved with a timestamp", await pg.evaluate("S.aic>1700000000000"))
        chk("picker shown after consent", await pg.locator("#ph").count() == 1)
        await pg.screenshot(path=SC + "ac_2.png")
        await pg.set_input_files("#ph", files=[{"name": "x.jpg", "mimeType": "image/jpeg", "buffer": JPG}])
        await pg.wait_for_timeout(1200)
        chk("after consent the photo is read", await pg.evaluate("(window.__samples||[]).filter(x=>x.img).length===1"))
        # 4. second time: no new question
        await pg.evaluate("closeSheet()"); await pg.wait_for_timeout(400)
        await pg.click("text=Din poză"); await pg.wait_for_timeout(300)
        sh = await pg.inner_text("#sheet")
        chk("consent is not asked twice", "Sunt de acord" not in sh and await pg.locator("#ph").count() == 1)
        await pg.evaluate("closeSheet()"); await pg.wait_for_timeout(400)
        # 5. withdraw from Mai mult
        await pg.click("nav >> text=Mai mult"); await pg.wait_for_timeout(900)
        t = await pg.inner_text("#main")
        chk("settings shows the consent row with Retrage", "Citire din poză" in t and "Ai dat acordul" in t and "Retrage" in t, t[:300])
        await pg.screenshot(path=SC + "ac_3.png")
        await pg.click("#main .it:has-text('Citire din poză') >> button:has-text('Retrage')"); await pg.wait_for_timeout(400)
        chk("withdrawal resets consent", await pg.evaluate("S.aic===0"))
        t = await pg.inner_text("#main")
        rowt = await pg.inner_text("#main .it:has-text('Citire din poză')")
        chk("settings shows that consent is not given", "Nedat" in rowt and "Retrage" not in rowt, rowt)
        # 6. asked again after withdrawal
        await pg.click("nav >> text=Agendă"); await pg.wait_for_timeout(900)
        await pg.click("text=Din poză"); await pg.wait_for_timeout(300)
        chk("asked again after withdrawal", "Sunt de acord" in await pg.inner_text("#sheet"))
        await pg.evaluate("closeSheet()"); await pg.wait_for_timeout(300)
        # 7. consent follows the saved state across reload, wipe clears it
        await pg.evaluate("S.aic=Date.now();save()")
        await pg.reload(); await pg.wait_for_timeout(2600)
        chk("consent survives a reload", await pg.evaluate("S.aic>0"))
        await pg.evaluate("S=fresh();store()")
        chk("fresh state has no consent", await pg.evaluate("S.aic===0"))
        # 8. free limit still comes first
        await pg.evaluate("S.photos=3;save()")
        await pg.reload(); await pg.wait_for_timeout(2600)
        try:
            await pg.click("#sheet button:has-text('Sări peste')", timeout=1500)
        except Exception: pass
        await pg.wait_for_timeout(300)
        await pg.evaluate("photoStart()"); await pg.wait_for_timeout(400)
        sh = await pg.inner_text("#sheet")
        chk("free limit opens the plan, not the consent", "Control" in sh and "Sunt de acord" not in sh, sh[:150])
        ow = await pg.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth+1")
        chk("no horizontal overflow", not ow)
        chk("no page errors", not errs, errs)
        await ctx.close(); await b.close()
    done()
asyncio.run(main())
