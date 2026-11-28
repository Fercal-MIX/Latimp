import asyncio,json,time
from playwright.async_api import async_playwright
from web import *
# Sincronizarea între două telefoane: versiunea de pe server (rev) decide, nu ceasul; schimbările se unesc termen cu termen.
# Plus: cu semnal slab, aplicația pornește din copia salvată după cel mult câteva secunde.
U="http://localhost:8786/"
UID="u-ana@test.ro"
def it(i,n,d="2030-01-10"): return {"id":i,"g":"per","t":"zi","n":n,"d":d}
ST={"onb":True,"at":1000,"items":[it("a1","Ana"),it("b1","Bogdan")],"cars":[],"saved":[],"credits":0,"used":0,"photos":0,"theme":"auto","acct":{"p":"email","e":"ana@test.ro","n":"","at":1,"v":True}}
async def mk(b):
    c=await b.new_context(viewport={"width":390,"height":800},service_workers="block");await fake_route(c,fonts=True)
    # pe server: aceeași agendă, versiunea 5; telefonul știe deja versiunea 5 (sincronizat)
    init="if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('buzunar.v2',%s);localStorage.setItem('fake.cfg',%s);localStorage.setItem('latimp.auth',JSON.stringify({user:{id:'%s',email:'ana@test.ro'},access_token:'t'}));localStorage.setItem('fake.db',JSON.stringify({'%s':{state:%s,rev:5}}));localStorage.setItem('latimp.sbase:%s',JSON.stringify({rev:5,s:%s}))}"%(json.dumps(json.dumps(ST)),json.dumps(json.dumps({"mon":{"free":True}})),UID,UID,json.dumps(ST),UID,json.dumps(ST))
    await c.add_init_script(init)
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(2500)
    return c,p,errs
# „alt telefon” scrie pe server: rev crește, ceasul lui poate fi în urmă (at mic)
def other(fn,at=500): return "(()=>{const d=JSON.parse(localStorage.getItem('fake.db'));const r=d['%s'];const s=r.state;%s;s.at=%d;r.rev=(r.rev||1)+1;localStorage.setItem('fake.db',JSON.stringify(d))})()"%(UID,fn,at)
SRV="JSON.parse(localStorage.getItem('fake.db'))['%s']"%UID
async def main():
    srv=serve(8786)
    try:
      async with async_playwright() as pw:
        b=await pw.chromium.launch()
        # 1. fără internet aici se adaugă X; între timp, pe alt telefon (cu ceasul în urmă) se adaugă Y
        c,p,e=await mk(b)
        await p.evaluate("S.items.push({id:'x1',g:'per',t:'zi',n:'Xenia',d:'2030-02-01'});S.at=Date.now();store()")
        await p.evaluate(other("s.items.push({id:'y1',g:'per',t:'zi',n:'Yvonne',d:'2030-03-01'})"))
        await p.evaluate("sbPull()");await p.wait_for_timeout(2600)
        names=await p.evaluate("S.items.map(x=>x.n).sort()")
        chk("offline add + other phone's add: both kept on this phone",names==["Ana","Bogdan","Xenia","Yvonne"],names)
        s=await p.evaluate(SRV)
        chk("merged agenda saved to the account",sorted(x["n"] for x in s["state"]["items"])==["Ana","Bogdan","Xenia","Yvonne"],s["state"]["items"])
        # 2. ceasul în urmă pe celălalt telefon nu mai pierde schimbarea lui
        w0=await p.evaluate("__sb.upserts")
        await p.evaluate(other("s.items.find(x=>x.id=='a1').n='Ana Maria'",at=1))
        await p.evaluate("sbPull()");await p.wait_for_timeout(1000)
        chk("change from a phone with a slow clock is taken, not overwritten",await p.evaluate("S.items.find(x=>x.id=='a1').n")=="Ana Maria")
        chk("no extra write when nothing changed here",await p.evaluate("__sb.upserts")==w0)
        # 3. ștergere pe celălalt telefon, nimic schimbat aici: dispare și aici
        await p.evaluate(other("s.items=s.items.filter(x=>x.id!='b1')"))
        await p.evaluate("sbPull()");await p.wait_for_timeout(1000)
        chk("deleted elsewhere: deleted here too",not await p.evaluate("S.items.some(x=>x.id=='b1')"))
        # 4. aici se șterge un termen, acolo se adaugă altul: rezultatul le are pe amândouă schimbările
        await p.evaluate("S.items=S.items.filter(x=>x.id!='x1');S.at=Date.now();store()")
        await p.evaluate(other("s.items.push({id:'z1',g:'per',t:'zi',n:'Zoe',d:'2030-04-01'})"))
        await p.evaluate("sbPull()");await p.wait_for_timeout(2600)
        names=await p.evaluate("S.items.map(x=>x.n).sort()")
        chk("delete here + add there: deletion kept, addition kept",names==["Ana Maria","Yvonne","Zoe"],names)
        chk("server has the same result",sorted(x["n"] for x in (await p.evaluate(SRV))["state"]["items"])==["Ana Maria","Yvonne","Zoe"])
        # 5. salvare aici în timp ce serverul s-a schimbat: scrierea e refuzată, apoi se unește și se scrie din nou
        await p.evaluate(other("s.items.push({id:'w1',g:'per',t:'zi',n:'Wanda',d:'2030-05-01'})"))
        await p.evaluate("S.items.push({id:'v1',g:'per',t:'zi',n:'Vlad',d:'2030-06-01'});save()");await p.wait_for_timeout(3500)
        srvn=sorted(x["n"] for x in (await p.evaluate(SRV))["state"]["items"])
        chk("save over a newer server version: nothing lost",srvn==["Ana Maria","Vlad","Wanda","Yvonne","Zoe"],srvn)
        chk("phone shows the same",await p.evaluate("S.items.map(x=>x.n).sort()")==srvn)
        chk("sync status ok",await p.evaluate("SY.ok===true"))
        chk("no page errors",not e,e)
        await c.close()
        # 7. prima conectare, „Păstrează agenda de pe telefon”: agenda din cont se înlocuiește, nu se amestecă
        c=await b.new_context(viewport={"width":390,"height":800},service_workers="block");await fake_route(c,fonts=True)
        await c.add_init_script("if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.db',JSON.stringify({'%s':{state:{onb:true,at:9,items:[{id:'t1',g:'per',t:'zi',n:'Tata',d:'2030-01-01'}],cars:[],saved:[]},rev:3}}));localStorage.setItem('buzunar.v2',JSON.stringify({onb:true,at:5,items:[{id:'p1',g:'per',t:'zi',n:'Vecin',d:'2030-03-01'}],cars:[],saved:[],credits:0,used:0,photos:0,theme:'auto'}))}"%UID)
        p=await c.new_page();await p.goto(U);await p.wait_for_timeout(1800)
        await p.evaluate("acctOpen()");await p.wait_for_timeout(500)
        await p.fill("#ac_e","ana@test.ro");await p.click("#ac_go");await p.wait_for_timeout(500)
        await p.fill("#ac_c","123456");await p.click("#ac_go");await p.wait_for_timeout(1200)
        await p.click("#sheet button:has-text('Păstrează agenda de pe telefon')");await p.wait_for_timeout(3500)
        srvn=sorted(x["n"] for x in (await p.evaluate(SRV))["state"]["items"])
        chk("first sign-in, keep phone's agenda: account replaced, not mixed",srvn==["Vecin"] and await p.evaluate("S.items.map(x=>x.n)")==["Vecin"],srvn)
        await c.close()
        # 6. semnal slab: cu service worker activ, pagina vine din copia salvată după câteva secunde
        c=await b.new_context(viewport={"width":390,"height":800});await fake_route(c,fonts=True)
        p=await c.new_page();await p.goto(U);await p.wait_for_timeout(3500)
        await p.reload();await p.wait_for_timeout(1500)
        ctl=await p.evaluate("!!navigator.serviceWorker.controller")
        slow=[False]
        async def stall(r):
            if slow[0] and (r.request.url.rstrip("/")==U.rstrip("/") or r.request.url.endswith("index.html")):
                await asyncio.sleep(15);await r.continue_()
            else: await r.continue_()
        await c.route("**/*",stall);slow[0]=True
        t0=time.time();await p.goto(U,wait_until="commit",timeout=20000);await p.wait_for_function("document.getElementById('main')",timeout=20000);dt=time.time()-t0
        chk("service worker active",ctl)
        chk("slow network: app opens from the saved copy in under 6 s",dt<6,round(dt,1))
        await c.close()
        await b.close()
    finally:
        srv.terminate()
    done()
asyncio.run(main())
