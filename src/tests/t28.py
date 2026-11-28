import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
from web import *
U="http://localhost:8778/"
CFG={"mon":{"free":True}}
async def mk(b,state=None,w=390,dark=False):
    c=await b.new_context(viewport={"width":w,"height":800},color_scheme="dark" if dark else "light")
    await fake_route(c)
    init="if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);"%json.dumps(json.dumps(CFG))
    if state: init+="localStorage.setItem('buzunar.v2',%s);"%json.dumps(json.dumps(state))
    init+="}"
    await c.add_init_script(init)
    await c.add_init_script("window.__rpc={get_my_access:async()=>({pro:true,source:'free',free_mode:true}),am_i_admin:async()=>false,set_reminders:async(a)=>a.p.length};")
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(3000)
    return c,p,errs
async def card(p): return await p.evaluate("(()=>{const e=document.querySelector('#main .fs');return e?e.innerText:''})()")
async def main():
    srv=serve(8778)
    try:
        async with async_playwright() as pw:
            b=await pw.chromium.launch()
            # 1. utilizator nou: întrebările de început, apoi cardul cu primii pași
            c,p,e=await mk(b)
            chk("new user: first-run questions shown",await p.evaluate("$('sheet').dataset.k")=="onb")
            await p.click("#sheet button:text-is('Sări peste')");await p.wait_for_timeout(900)
            if await p.evaluate("$('ov').classList.contains('on')"):
                await p.evaluate("closeSheet()");await p.wait_for_timeout(500)
            t=await card(p)
            chk("card shown after first run","Primii pași" in t,t)
            chk("progress 0 of 4","0 din 4 gata" in t,t)
            chk("four steps listed",all(s in t for s in ["Adaugă primul termen","Instalează aplicația","Pornește memento-urile","Cere o idee de timp liber"]),t)
            chk("examples explained","doar exemple" in t,t)
            chk("progress bar accessible",await p.evaluate("(()=>{const e=document.querySelector('.fs [role=progressbar]');return !!e&&e.getAttribute('aria-valuenow')=='0'&&e.getAttribute('aria-valuemax')=='4'})()"))
            # 2. adăugarea unui termen bifează primul pas
            await p.click(".fs button:text-is('Adaugă')");await p.wait_for_timeout(600)
            chk("Adaugă opens the item form",await p.evaluate("$('ov').classList.contains('on')"))
            await p.evaluate("closeSheet()");await p.wait_for_timeout(400)
            await p.evaluate("S.items.push({id:uid(),g:'auto',t:'rca',n:'B 01 ABC',d:fmt(new Date(Date.now()+20*DAY)),rep:12,note:''});save();render()");await p.wait_for_timeout(500)
            t=await card(p)
            chk("real item ticks step 1","1 din 4 gata" in t and await p.evaluate("document.querySelectorAll('.fs li.dn').length")==1,t)
            # 3. o idee din Timp liber
            await p.click(".fs button:text-is('Încearcă')");await p.wait_for_timeout(700)
            chk("Încearcă opens Free time ideas",await p.evaluate("TAB=='free'&&FSEG=='ideas'"))
            await p.click("button:text-is('Dă-mi idei')");await p.wait_for_timeout(2500)
            chk("ideas appear",await p.evaluate("IDEAS.length>0"))
            await p.evaluate("render()");await p.wait_for_timeout(200)
            chk("idea flag set",await p.evaluate("!!S.fs.idea"))
            await p.evaluate("tab('agenda')");await p.wait_for_timeout(700)
            t=await card(p);chk("2 of 4 after an idea","2 din 4 gata" in t,t)
            # 4. memento-urile: butonul duce la Notificări, pasul se bifează doar când merg
            await p.click(".fs button:text-is('Pornește')");await p.wait_for_timeout(800)
            chk("Pornește opens Notifications",await p.evaluate("TAB=='more'&&VIEW=='notif'"))
            await p.evaluate("VIEW='main';tab('agenda')");await p.wait_for_timeout(600)
            t=await card(p);chk("opening Notifications alone does not tick reminders on web","2 din 4 gata" in t,t)
            await p.evaluate("S.nt.mail=true;save();render()");await p.wait_for_timeout(300)
            t=await card(p);chk("reminders on ticks step","3 din 4 gata" in t,t)
            # 5. instalarea
            await p.evaluate("dispatchEvent(new Event('appinstalled'))");await p.wait_for_timeout(300)
            await p.evaluate("render()");await p.wait_for_timeout(300)
            t=await card(p)
            chk("all done message","Gata, LaTimp e pregătită" in t and "Primii pași" not in t,t)
            await p.click(".fs .acts button:text-is('Închide')");await p.wait_for_timeout(600)
            chk("closing hides the card",await card(p)=="" and await p.evaluate("S.fs.hide==1"))
            chk("toast says where it went","Mai mult" in await p.evaluate("(document.querySelector('.toast')||{}).innerText||''"))
            # 6. se redeschide din Mai mult → Ajutor
            await p.evaluate("tab('more')");await p.wait_for_timeout(600)
            chk("Help has First steps row",await p.locator("#main button.it:has-text('Primii pași')").count()==1)
            await p.click("#main button.it:has-text('Primii pași')");await p.wait_for_timeout(900)
            chk("row reopens card in Agenda",await p.evaluate("TAB")=="agenda" and "Gata, LaTimp e pregătită" in await card(p))
            # 7. doar în „Toate”
            await p.evaluate("FIL='sub';render()");await p.wait_for_timeout(300)
            chk("hidden in other filters",await card(p)=="")
            await p.evaluate("FIL='all';render()")
            # 8. engleză
            await p.evaluate("S.fs={at:'x'};S.nt.mail=false;save();set('lang','en')");await p.wait_for_timeout(1800)
            await p.evaluate("tab('agenda')");await p.wait_for_timeout(700)
            t=await card(p)
            chk("en: card translated","First steps" in t and ("1 of 3 done" in t or "1 of 4 done" in t) and "Turn on reminders" in t and "Primii" not in t,t)
            await p.evaluate("tab('more')");await p.wait_for_timeout(500)
            chk("no admin link for normal users",await p.locator("a[href='admin.html']").count()==0)
            await p.evaluate("ISADM=true;render()");await p.wait_for_timeout(300)
            chk("admins see the admin panel link",await p.locator("a[href='admin.html']").count()==1)
            await p.evaluate("ISADM=false;tab('agenda')")
            chk("no errors (new user)",not e,e)
            await c.close()
            # 9. utilizator vechi: fără card
            old={"onb":True,"at":5,"items":[],"cars":[],"saved":[],"credits":0,"used":0,"photos":0,"theme":"auto","nt":{"d":7,"h":"09:00","rep":False,"n":3,"i":7,"day":False,"wk":False}}
            c,p,e=await mk(b,old)
            chk("existing user: no card",await card(p)=="")
            chk("existing user: no first-run sheet",not await p.evaluate("$('ov').classList.contains('on')&&$('sheet').dataset.k=='onb'"))
            await c.close()
            # 10. 320 px, noapte: fără depășiri
            st=dict(old);st["fs"]={"at":"x"}
            for w,dk in [(320,True),(360,False),(560,True)]:
                c,p,e=await mk(b,st,w,dk)
                t=await card(p)
                ov=await p.evaluate("document.documentElement.scrollWidth-innerWidth")
                chk(f"{w}px {'dark' if dk else 'light'}: card visible, no overflow","Primii pași" in t and ov<=0,ov)
                if w==320: await p.screenshot(path=SC+"fs_320_dark.png",full_page=False)
                if w==360: await p.screenshot(path=SC+"fs_360_light.png",full_page=False)
                chk(f"{w}px no errors",not e,e)
                await c.close()
            await b.close()
    finally:
        srv.terminate()
    done()
asyncio.run(main())
