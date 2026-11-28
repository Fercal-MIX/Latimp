import asyncio
from playwright.async_api import async_playwright
from web import *
URL="file:///mnt/user-data/outputs/buzunar.html"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.add_init_script(path=SC+"mock.js")
        await pg.goto(URL);await pg.wait_for_timeout(2500)
        r=await pg.evaluate("""(()=>{const out=[];for(const l of ['ro','en']){S.lang=l;const L=LOC();
          out.push(nice('2026-12-05')===new Date(2026,11,5).toLocaleDateString(L,{day:'numeric',month:'short'}));
          out.push(money(12345.6)===(12345.6).toLocaleString(L,{maximumFractionDigits:0}));
          const m=new Date(2027,0,3).toLocaleDateString(L,{month:'long'});out.push(mlab({d:'2027-01-03'})===m.charAt(0).toUpperCase()+m.slice(1)+' 2027')}S.lang='ro';return out})()""")
        chk("cached formatters match the originals (ro, en)",all(r),r)
        r=await pg.evaluate("[left(plus(5)),left(plus(-3)),left(fmt(td()))]")
        chk("days left",r==[5,-3,0],r)
        r=await pg.evaluate("(()=>{const a=left(plus(5));LFC.d=-1;LFC.m.set(plus(5),99);const b=left(plus(5));return [a,b]})()")
        chk("days-left cache resets on a new day",r==[5,5],r)
        r=await pg.evaluate("(()=>{const t0=performance.now();for(let i=0;i<2000;i++){nice('2026-12-05');money(i)}return performance.now()-t0})()")
        chk("formatting is fast (2000 dates+sums under 150 ms)",r<150,r)
        wn=await pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--wn').trim()")
        chk("warning color has 4.5:1 contrast in light mode",wn.lower()=="#a35400",wn)
        chk("no errors",not errs,errs)
        await b.close()
    done()
asyncio.run(main())
