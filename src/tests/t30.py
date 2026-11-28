from web import *
# 1.16: interfața în relief și ecranul de pornire nou (versiunea web)
import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
U="http://localhost:8768/"
FR="""()=>new Promise(r=>{const t=[];let p=performance.now(),s=p;function f(n){t.push(n-p);p=n;if(n-s<%d)requestAnimationFrame(f);else r(t.slice(1))}requestAnimationFrame(f)})"""
async def route(ctx):
    await fake_route(ctx)
    await ctx.route("**/fonts.googleapis.com/**",lambda r:r.abort())
async def skip(pg):
    for t in ["Sări peste","Mai târziu"]:
        try:
            await pg.wait_for_selector(f"#sheet button:has-text('{t}')",timeout=5000)
            await pg.click(f"#sheet button:has-text('{t}')");await pg.wait_for_timeout(700)
        except Exception: pass
def slow(t): return sum(1 for x in t if x>20)
async def main():
    srv=serve(8768)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            # prima pornire, telefon încetinit de 4 ori
            c=await b.new_context(viewport={"width":390,"height":800},device_scale_factor=2,service_workers="block");await route(c)
            pg=await c.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
            cdp=await c.new_cdp_session(pg);await cdp.send("Emulation.setCPUThrottlingRate",{"rate":4})
            await pg.goto(U);await pg.wait_for_timeout(150)
            st=await pg.evaluate("(()=>{const e=document.getElementById('spl');return e?{q:e.classList.contains('q'),parts:['.spx','.spe','.spd','.shn','.sph','.spm'].every(s=>e.querySelector(s)),anim:getComputedStyle(e.querySelector('.spe')).animationName}:null})()")
            chk("pornire: emblema în relief și toate părțile ei",st and st["parts"],st)
            chk("pornire: prima dată, cu animația completă",st and not st["q"] and st["anim"]=="spr",st)
            chk("pornire: culorile nu trec prin tranziție (fără recalcularea paginii la fiecare cadru)",await pg.evaluate("!document.documentElement.dataset.rdy&&getComputedStyle(document.documentElement).transitionDuration.split(',').every(x=>parseFloat(x)==0)"))
            fr=await pg.evaluate(FR%1500)
            print("info: pornire, cadre peste 20 ms (procesor /4):",slow(fr))
            await pg.wait_for_timeout(1500)
            chk("pornire: ecranul dispare la final",await pg.evaluate("!document.getElementById('spl')"))
            chk("după pornire: tranziția culorilor revine pentru schimbarea planului",await pg.evaluate("document.documentElement.dataset.rdy=='1'&&getComputedStyle(document.documentElement).transitionDuration.split(',').some(x=>parseFloat(x)>0)"))
            an=await pg.evaluate("[...document.styleSheets].flatMap(s=>{try{return[...s.cssRules]}catch(e){return[]}}).filter(r=>r instanceof CSSKeyframesRule&&['spr','sph','shn','spm','in'].includes(r.name)).flatMap(r=>[...r.cssRules].flatMap(k=>[...k.style])).filter((v,i,a)=>a.indexOf(v)==i)")
            chk("animațiile noi folosesc doar transform și opacity (placa grafică)",an and all(x in("transform","opacity") for x in an),an)
            await skip(pg)
            await cdp.send("Emulation.setCPUThrottlingRate",{"rate":1})
            sh=await pg.evaluate("getComputedStyle(document.querySelector('.pn')).boxShadow")
            chk("bara de jos: umbre în straturi cu muchie luminată","inset" in sh and sh.count("rgba")>=3,sh)
            hs=await pg.evaluate("(()=>{const h=document.querySelector('.hero');return h?getComputedStyle(h).backgroundImage:''})()")
            chk("cardul principal: lumină și volum",hs.count("gradient")>=3,hs[:120])
            await cdp.send("Emulation.setCPUThrottlingRate",{"rate":4})
            frames=[]
            for t in ["free","more","agenda","free","agenda"]:
                pr=pg.evaluate(FR%650);await pg.click("#t-"+t);frames+=await pr
            print("info: schimbarea meniului, cadre peste 20 ms (procesor /4):",slow(frames))
            ind=await pg.evaluate("(()=>{const a=document.getElementById('ind').getAnimations();return getComputedStyle(document.getElementById('ind')).transitionProperty})()")
            chk("indicatorul barei alunecă doar prin transform",ind=="transform",ind)
            await cdp.send("Emulation.setCPUThrottlingRate",{"rate":1})
            chk("fără erori de script",not errs,errs)
            # a doua pornire: varianta scurtă
            pg2=await c.new_page();await pg2.goto(U);await pg2.wait_for_timeout(100)
            q=await pg2.evaluate("(()=>{const e=document.getElementById('spl');return e&&e.classList.contains('q')&&getComputedStyle(e.querySelector('.spe')).animationName=='none'})()")
            chk("revenire: pornire scurtă, fără animația emblemei",q)
            await pg2.wait_for_timeout(1200)
            chk("revenire: ecranul dispare repede",await pg2.evaluate("!document.getElementById('spl')"))
            await pg2.close();await c.close()
            # animații reduse: simbolul apare întreg, nu gol
            c=await b.new_context(viewport={"width":390,"height":800},reduced_motion="reduce",service_workers="block");await route(c)
            pg=await c.new_page();await pg.goto(U);await pg.wait_for_timeout(120)
            da=await pg.evaluate("(()=>{const d=document.querySelector('#spl .d');return d?getComputedStyle(d).strokeDasharray:'x'})()")
            chk("animații reduse: simbolul e desenat complet",da=="none",da)
            await c.close()
            # lățimi și teme
            for th in ["light","dark"]:
                for w in [320,360,390,560]:
                    c=await b.new_context(viewport={"width":w,"height":780},color_scheme=th,service_workers="block");await route(c)
                    pg=await c.new_page();e2=[];pg.on("pageerror",lambda e:e2.append(str(e)))
                    await pg.goto(U);await pg.wait_for_timeout(2300);await skip(pg)
                    o=[]
                    for t in ["agenda","free","more"]:
                        await pg.click("#t-"+t);await pg.wait_for_timeout(700)
                        o.append(await pg.evaluate("document.documentElement.scrollWidth>innerWidth+1"))
                    if w in (320,390): await pg.screenshot(path=SC+f"r16_{th}_{w}.png",full_page=False)
                    chk(f"{th} {w}px: fără depășire pe orizontală și fără erori",not any(o) and not e2,(o,e2))
                    await c.close()
            await b.close()
    finally:
        srv.terminate()
    done()
asyncio.run(main())
