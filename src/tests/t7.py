import asyncio
from playwright.async_api import async_playwright
from web import *
URL = "file:///mnt/user-data/outputs/buzunar.html"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 1. first launch: full animation, then gone, flag saved, onboarding after it
        ctx = await b.new_context(viewport={"width": 390, "height": 800})
        pg = await ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.add_init_script(path=SC + "mock.js")
        await pg.goto(URL, wait_until="commit")
        await pg.wait_for_selector("#spl", state="attached")
        await pg.wait_for_timeout(250); await pg.screenshot(path=SC + "sp_1.png")
        await pg.wait_for_timeout(550); await pg.screenshot(path=SC + "sp_2.png")
        await pg.wait_for_timeout(500); await pg.screenshot(path=SC + "sp_3.png")
        st = await pg.evaluate("""()=>{const e=document.getElementById('spl');if(!e)return null;const c=getComputedStyle(e);
          return {ah:e.getAttribute('aria-hidden'),pe:c.pointerEvents,pos:c.position,z:c.zIndex,q:e.classList.contains('q'),
                  bg:c.backgroundImage.slice(0,40),paths:e.querySelectorAll('.d').length,dots:e.querySelectorAll('.pp').length}}""")
        chk("splash present at start", st is not None, st)
        if st:
            chk("splash aria-hidden", st["ah"] == "true")
            chk("splash does not block taps", st["pe"] == "none")
            chk("splash covers the page", st["pos"] == "fixed" and int(st["z"]) >= 100)
            chk("first launch uses full animation", st["q"] is False)
            chk("splash has gradient background", "gradient" in st["bg"], st["bg"])
            chk("logo parts drawn (ring, arc, L, letters)", st["paths"] >= 10 and st["dots"] >= 2, st)
        txt = await pg.evaluate("document.getElementById('spl')?document.getElementById('spl').innerText:''")
        chk("splash has no text (logo is drawn)", txt.strip() == "")
        await pg.wait_for_timeout(2300)
        gone = await pg.evaluate("!document.getElementById('spl')")
        chk("splash removed after boot", gone)
        flag = await pg.evaluate("localStorage.getItem('latimp.sp')")
        chk("returning-user flag saved", flag == "1", flag)
        chk("onboarding opens after splash", "Ce să ținem minte" in await pg.inner_text("#sheet"))
        chk("no page errors (first launch)", not errs, errs)
        await pg.screenshot(path=SC + "sp_4.png")
        # 2. second launch (same storage): quick mode
        # (1.22: o reîmprospătare nu mai arată ecranul; o pornire nouă = o filă nouă, cu aceleași date)
        pg = await ctx.new_page()
        await pg.goto(URL, wait_until="commit")
        await pg.wait_for_selector("#spl", state="attached")
        try:
            await pg.wait_for_function("document.getElementById('spl')&&document.getElementById('spl').classList.contains('q')", timeout=1500)
            q = True
        except Exception as e:
            q = False
        chk("second launch uses quick mode", q is True, q)
        await pg.wait_for_timeout(300); await pg.screenshot(path=SC + "sp_q.png")
        await pg.wait_for_timeout(1900)
        chk("quick splash is gone within ~2s", await pg.evaluate("!document.getElementById('spl')"))
        await ctx.close()

        # 3. reduced motion: logo fully visible, short
        ctx = await b.new_context(viewport={"width": 390, "height": 800}, reduced_motion="reduce")
        pg = await ctx.new_page()
        await pg.add_init_script(path=SC + "mock.js")
        await pg.goto(URL, wait_until="commit")
        await pg.wait_for_selector("#spl", state="attached")
        await pg.wait_for_timeout(100)
        r = await pg.evaluate("""()=>{const d=[...document.querySelectorAll('#spl .d')].map(e=>getComputedStyle(e).strokeDashoffset);
          const p=[...document.querySelectorAll('#spl .pp')].map(e=>getComputedStyle(e).transform);return {d:[...new Set(d)],p:[...new Set(p)]}}""")
        chk("reduced motion: strokes already drawn", r["d"] == ["0px"], r)
        chk("reduced motion: dots not scaled to zero", all(x in ("none", "matrix(1, 0, 0, 1, 0, 0)") for x in r["p"]), r)
        await pg.screenshot(path=SC + "sp_rm.png")
        await pg.wait_for_timeout(1800)
        chk("reduced motion: splash gone quickly", await pg.evaluate("!document.getElementById('spl')"))
        await ctx.close()

        # 4. dark scheme + narrow phone: no overflow, gradient uses dark hero tokens
        ctx = await b.new_context(viewport={"width": 320, "height": 640}, color_scheme="dark")
        pg = await ctx.new_page()
        await pg.add_init_script(path=SC + "mock.js")
        await pg.goto(URL, wait_until="commit")
        await pg.wait_for_selector("#spl", state="attached")
        await pg.wait_for_timeout(1300); await pg.screenshot(path=SC + "sp_dark.png")
        ow = await pg.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth+1")
        chk("dark 320px: no horizontal overflow during splash", not ow)
        box = await pg.evaluate("(()=>{const r=document.querySelector('#spl .spw').getBoundingClientRect();return [r.left,r.right]})()")
        chk("dark 320px: logo inside the screen", box[0] >= 0 and box[1] <= 320, box)
        await ctx.close()

        # 5. no capabilities at all (mock missing): splash still leaves
        ctx = await b.new_context(viewport={"width": 390, "height": 800})
        pg = await ctx.new_page()
        await pg.goto(URL)
        await pg.wait_for_timeout(4800)
        chk("without capabilities the splash still leaves", await pg.evaluate("!document.getElementById('spl')"))
        txt = await pg.inner_text("body")
        chk("without capabilities the app is usable", "Agendă" in txt or "Agenda" in txt, txt[:120])
        await ctx.close()
        await b.close()
    done()
asyncio.run(main())
