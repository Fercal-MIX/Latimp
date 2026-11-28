import asyncio
from playwright.async_api import async_playwright
from web import *
URL="file:///mnt/user-data/outputs/buzunar.html"
SPL="(()=>{const e=document.getElementById('spl');if(!e)return 'gone';const s=getComputedStyle(e);return s.display=='none'?'hidden':'shown'})()"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();c=await b.new_context();errs=[]
        await c.add_init_script(path=SC+"mock.js")
        pg=await c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(URL);await pg.wait_for_timeout(150)
        chk("first open shows the launch screen",await pg.evaluate(SPL)=="shown")
        await pg.wait_for_timeout(3000)
        chk("launch screen goes away",await pg.evaluate(SPL)=="gone")
        # reîmprospătare
        await pg.reload(wait_until="commit")
        await pg.wait_for_function("document.getElementById('main')")
        s1=await pg.evaluate(SPL)
        chk("refresh: no launch screen, even before the page finishes loading",s1 in("gone","hidden"),s1)
        await pg.wait_for_timeout(250)
        h=await pg.evaluate("document.getElementById('main').innerText.length")
        chk("refresh: the agenda shows right away",h>20,h)
        await pg.wait_for_timeout(2600)
        chk("refresh: app works and transitions are on",await pg.evaluate("document.documentElement.dataset.rdy=='1'&&typeof render=='function'"))
        # a doua reîmprospătare, repede
        await pg.reload();await pg.wait_for_timeout(120)
        chk("second refresh: still no launch screen",await pg.evaluate(SPL) in("gone","hidden"))
        # deschiderea dintr-o notificare, în aceeași filă
        await pg.goto(URL+"?x=1");await pg.wait_for_timeout(120)
        chk("opening a link in the same tab: no launch screen",await pg.evaluate(SPL) in("gone","hidden"))
        # o filă nouă = o pornire nouă: ecranul scurt
        p2=await c.new_page();await p2.goto(URL);await p2.wait_for_timeout(120)
        r=await p2.evaluate("(()=>{const e=document.getElementById('spl');return e?[getComputedStyle(e).display,e.classList.contains('q')]:null})()")
        chk("new launch: short launch screen again",r and r[0]!="none" and r[1],r)
        await p2.wait_for_timeout(1800)
        chk("new launch: short launch screen is gone in under 2 s",await p2.evaluate(SPL)=="gone")
        chk("no errors",not errs,errs)
        await b.close()
    done()
asyncio.run(main())
