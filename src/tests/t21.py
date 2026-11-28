import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
from web import *
U="http://localhost:8768/"
FREE={"mon":{"free":True,"control":False,"sparks":False,"invites":False,"referrals":False},"ref":{"days":30,"max":12},"maint":{"on":False,"msg":""}}
PAID={"mon":{"free":False,"control":True,"sparks":True,"invites":True,"referrals":True},"ref":{"days":30,"max":12},"maint":{"on":False,"msg":""}}
ST=json.dumps({"onb":True,"at":5,"items":[{"id":"a1","g":"sub","t":"sub","n":"Netflix","p":40,"c":"m","d":"2027-01-10"}],"cars":[],"saved":[],"credits":0,"used":0,"photos":0,"theme":"auto","inv":{"h":"old","exp":"2020-01-01","was":True},"sub":{"pl":"m","ren":"2020-01-01"}})
async def mk(b,cfg,signed=False,rpc="",extra=""):
    c=await b.new_context(viewport={"width":390,"height":800},service_workers="block")
    await fake_route(c,fonts=True)
    init="if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);localStorage.setItem('buzunar.v2',%s);"%(json.dumps(json.dumps(cfg)),json.dumps(ST))
    if signed: init+="localStorage.setItem('latimp.auth',JSON.stringify({user:{id:'u1',email:'ana@test.ro'},access_token:'t'}));"
    init+=extra+"}"
    await c.add_init_script(init)
    if rpc: await c.add_init_script(rpc)
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(2200)
    return c,p,errs
async def main():
    srv=serve(8768)
    try:
        async with async_playwright() as pw:
            b=await pw.chromium.launch()
            # A. totul gratuit, fără cont
            c,p,e=await mk(b,FREE)
            chk("free mode: full access without account",await p.evaluate("S.pro===true&&document.documentElement.dataset.plan=='ctl'"))
            chk("free mode: no Control button in header",await p.evaluate("[...document.querySelectorAll('#main .hd .pill')].every(x=>x.hidden||!/openPlan/.test(x.getAttribute('onclick')||''))"))
            await p.evaluate("openPlan('agenda')");await p.wait_for_timeout(400)
            chk("free mode: plan sheet says everything is free","Totul e gratuit acum" in await p.inner_text("#sheet"))
            await p.evaluate("closeSheet();tab('more')");await p.wait_for_timeout(800)
            t=await p.inner_text("#main")
            chk("invites/referrals hidden when off","Ai un cod de invitație" not in t and "Invită un prieten" not in t)
            chk("old demo invite/subscription ignored",await p.evaluate("!invOn()&&!S.sub"))
            chk("A no errors",not e,e);await c.close()
            # B. planuri pornite, fără cont
            c,p,e=await mk(b,PAID)
            chk("paid config: free user is not pro",await p.evaluate("S.pro===false&&document.documentElement.dataset.plan=='free'"))
            await p.evaluate("openPlan('agenda')");await p.wait_for_timeout(400)
            chk("paid config: Control offer shown","Control" in await p.inner_text("#sheet") and "Totul e gratuit" not in await p.inner_text("#sheet"))
            await p.evaluate("setPro(true)");await p.wait_for_timeout(300)
            chk("no demo activation on web",await p.evaluate("S.pro===false") and "nu este disponibilă" in await p.inner_text("#toast"))
            await p.evaluate("closeSheet();tab('more')");await p.wait_for_timeout(800)
            t=await p.inner_text("#main")
            chk("invites/referrals shown when on","Ai un cod de invitație" in t and "Invită un prieten" in t)
            chk("B no errors",not e,e);await c.close()
            # C+D. cont, cod de invitație pe server
            RPC="""window.__rpc={get_my_access:async()=>window.__acc||{pro:false,source:null},am_i_admin:async()=>false,
              redeem_invite:async(a)=>{if(a.p_code=='LTFULL234567')return{ok:false,err:'full'};window.__acc={pro:true,source:'invite',until:'2027-02-01'};return{ok:true,access:window.__acc}},
              get_my_referral_code:async()=>'RABCD234',redeem_referral:async(a)=>a.p_code=='RABCD234'?{ok:false,err:'self'}:{ok:true,days:30,access:{pro:true,source:'bonus',bonus_until:'2027-01-05'}}};"""
            c,p,e=await mk(b,PAID,signed=True,rpc=RPC,extra="localStorage.setItem('fake.ru',JSON.stringify([{user_id:'x1',referrer:'u1'},{user_id:'x2',referrer:'u1'}]));")
            chk("signed in, server says not pro",await p.evaluate("!!SBU&&S.pro===false"))
            await p.evaluate("invOpen()");await p.wait_for_timeout(400)
            await p.fill("#ivc","LT-FULL2-34567");await p.click("#ivb");await p.wait_for_timeout(600)
            chk("invite error from server","numărul maxim" in await p.inner_text("#sheet"))
            await p.fill("#ivc","LT-ABCDE-FGHJK");await p.click("#ivb");await p.wait_for_timeout(800)
            chk("invite activates server access",await p.evaluate("S.pro===true&&invOn()&&ACC.source=='invite'"))
            await p.evaluate("openPlan('agenda')");await p.wait_for_timeout(400)
            sh=await p.inner_html("#sb")
            chk("invite note, no demo leave button","Acces complet prin invitație" in await p.inner_text("#sheet") and "invEnd(" not in sh)
            await p.evaluate("closeSheet();window.__acc=null;refOpen()");await p.wait_for_timeout(700)
            t=await p.inner_text("#sheet")
            chk("referral code from server","RABC-D234" in t and "2 prieteni" in t,t[:200])
            await p.fill("#rf_c","RABC-D234");await p.click("#sheet button:has-text('Folosește codul')");await p.wait_for_timeout(700)
            chk("referral: own code refused","Acesta este codul tău" in await p.inner_text("#sheet"))
            await p.fill("#rf_c","RXYZ-W234");await p.click("#sheet button:has-text('Folosește codul')");await p.wait_for_timeout(800)
            chk("referral gives bonus access",await p.evaluate("ACC.source=='bonus'&&S.pro===true"))
            chk("C no errors",not e,e);await c.close()
            # F. mentenanță
            M=dict(FREE);M["maint"]={"on":True,"msg":"Revenim la ora 10."}
            c,p,e=await mk(b,M)
            chk("maintenance screen",await p.evaluate("!!document.getElementById('mnt')") and "Revenim la ora 10." in await p.inner_text("#mnt"))
            await c.close()
            c,p,e=await mk(b,M,signed=True,rpc="window.__rpc={get_my_access:async()=>({pro:true,source:'free'}),am_i_admin:async()=>true};")
            await p.wait_for_timeout(600)
            chk("admins skip maintenance",await p.evaluate("!document.getElementById('mnt')"))
            await c.close()
            # G. anunț
            N=dict(FREE);N["news"]={"on":True,"title":"Noutate","body":"Am adăugat contul.","audience":"all","at":"2026-11-27T10:00:00Z"}
            c,p,e=await mk(b,N)
            chk("news card from admin panel","Am adăugat contul." in await p.inner_text("#main"))
            N["news"]["audience"]="paid"
            await c.close()
            c,p,e=await mk(b,N)
            chk("news hidden for other audience","Am adăugat contul." not in await p.inner_text("#main"))
            chk("G no errors",not e,e)
            await p.evaluate("S.lang='en';save();langApply();openPlan('agenda')");await p.wait_for_timeout(500)
            chk("EN free sheet","Everything is free right now" in await p.inner_text("#sheet"))
            await c.close();await b.close()
    finally: srv.terminate()
    done()
asyncio.run(main())
