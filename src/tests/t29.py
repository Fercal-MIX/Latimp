import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
SC="/tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/"
ok=[];bad=[]
def chk(n,c,e=""): (ok if c else bad).append(n+(" -> "+str(e)[:300] if (e and not c) else ""))
U="http://localhost:8779/admin.html"
FAKE=open(SC+"fake_sb.js").read()
OV={"users":2,"new7":2,"new30":2,"paid":0,"bonus":0,"polls":0,"admins":1,"manual":0,"active7":1,"invited":0,"synced7":1,"referrals":0,"reports_new":0,"config_at":"2026-11-27T18:28:33Z",
 "signups":[{"d":"2026-11-%02d"%d,"n":d%3} for d in range(15,29)],
 "config":{"mon":{"free":True,"sparks":False,"control":False,"invites":False,"referrals":False},"ai":{"on":False,"day_eur":2,"user_day":20,"cost_call":0.01,"month_eur":20},"goal":{"users":1000},"maint":{"on":False,"msg":"x"},"prices":{"currency":"RON","month":"","year":"","trial_days":0,"promo":None},"ref":{"max":12,"days":30,"new_days":30},"min_ver":{"ios":"","android":"","msg":""},"plans":{"tiers":[],"groups":{},"limits":{},"features":{}}}}
RPC="""
window.__calls=[];window.__pin=%s;window.__open=!window.__pin||sessionStorage.getItem('open')=='1';
window.__rpc={am_i_admin:async(a,s)=>!!(s&&s.user&&/admin/.test(s.user.email)),
 admin_call:async(a)=>{__calls.push(a.p_fn+':'+JSON.stringify(a.p_args));
  if(a.p_fn=='pin_status')return {set:!!__pin,locked_until:null};
  if(a.p_fn=='pin_check'){if(a.p_args[0]=='1234'){__open=true;sessionStorage.setItem('open','1');return {ok:true}}return {ok:false,left:4}}
  if(__pin&&!__open)return {__err:'pin_required'};
  if(a.p_fn=='overview')return %s;
  if(['users','reports','invites','errors','testers','history','schedule_list','presets_list','export'].includes(a.p_fn))return [];
  return {};}};
"""
async def mk(b,sess=None,pin=False,w=390,dark=False):
    c=await b.new_context(viewport={"width":w,"height":850},color_scheme="dark" if dark else "light")
    async def h(r): await r.fulfill(status=200,content_type="application/javascript",body=FAKE)
    await c.route("**/cdn.jsdelivr.net/**",h)
    await c.route("**/fonts.googleapis.com/**",lambda r:r.abort())
    if sess: await c.add_init_script("if(!sessionStorage.getItem('s1')){sessionStorage.setItem('s1','1');localStorage.setItem('latimp.auth',%s)}"%json.dumps(json.dumps({"user":{"id":"u1","email":sess},"access_token":"t"})))
    await c.add_init_script(RPC%("true" if pin else "false",json.dumps(OV)))
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(1500)
    return c,p,errs
async def main():
    srv=subprocess.Popen(["python3","-m","http.server","8779","-d",SC+"web"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    try:
      async with async_playwright() as pw:
        b=await pw.chromium.launch()
        # 1. fără cont: ecranul de conectare
        c,p,e=await mk(b)
        chk("login shown when signed out",await p.evaluate("$=id=>document.getElementById(id),$('login').classList.contains('on')&&!$('lg_1').hidden"))
        chk("no data requested before login",await p.evaluate("__calls.length")==0)
        await p.click("#lg_send");chk("invalid email message","validă" in await p.inner_text("#lg_err"))
        await p.fill("#lg_e","om@test.ro");await p.click("#lg_send");await p.wait_for_timeout(300)
        chk("code step after sending",await p.evaluate("!document.getElementById('lg_2').hidden"))
        chk("no new accounts from admin login",await p.evaluate("__sb.sent.includes('om@test.ro')"))
        await p.fill("#lg_c","000000");await p.click("#lg_ok");await p.wait_for_timeout(300)
        chk("wrong code message","expirat" in await p.inner_text("#lg_err"))
        await p.fill("#lg_c","123456");await p.click("#lg_ok");await p.wait_for_timeout(600)
        t=await p.inner_text("#login")
        chk("non-admin account is refused","nu este administrator" in t and await p.evaluate("!document.getElementById('lg_3').hidden"),t)
        chk("non-admin: no admin calls",await p.evaluate("__calls.length")==0)
        # parserul cererilor din panou
        r=await p.evaluate("""[ADM.parse("select admin.users('o''brien', 100) as r"),ADM.parse("select admin.set_config('{\\"a\\":1}'::jsonb) as r"),
          ADM.parse("select admin.grant_access('0b9f7c8e-1111-4222-8333-944455556666'::uuid, null)"),ADM.parse("select admin.errors(true) as r"),ADM.parse("select admin.overview() as r"),
          ADM.parse("select admin.schedule_add('2026-12-01T10:00:00.000Z'::timestamptz, 'x, y', null, 3)")]""")
        chk("parse: quotes and numbers",r[0]=={"fn":"users","args":["o'brien",100]},r[0])
        chk("parse: jsonb stays text",r[1]=={"fn":"set_config","args":['{"a":1}']},r[1])
        chk("parse: uuid + null",r[2]["args"]==["0b9f7c8e-1111-4222-8333-944455556666",None],r[2])
        chk("parse: boolean / no args",r[3]["args"]==[True] and r[4]=={"fn":"overview","args":[]})
        chk("parse: commas inside strings",r[5]["args"]==["2026-12-01T10:00:00.000Z","x, y",None,3],r[5])
        bad_sql=await p.evaluate("(()=>{try{ADM.parse(\"select * from auth.users\");return 'no'}catch(e){return e.code}})()")
        chk("parse: other SQL rejected",bad_sql=="web_sql")
        chk("no page errors (login)",not e,e);await c.close()
        # 2. administrator: panoul se încarcă prin poartă
        for w,dk in [(390,False),(900,True),(320,True)]:
            c,p,e=await mk(b,"admin@test.ro",False,w,dk)
            chk(f"{w}: admin sees panel",await p.evaluate("!document.getElementById('login').classList.contains('on')&&!document.getElementById('who').hidden"))
            calls=await p.evaluate("__calls")
            chk(f"{w}: data through admin_call",any(x.startswith("overview:") for x in calls),calls)
            chk(f"{w}: account shown",await p.inner_text("#who_e")=="admin@test.ro")
            chk(f"{w}: download button on web",await p.evaluate("!document.getElementById('x_dl').hidden"))
            errshown=await p.evaluate("(()=>{const x=document.getElementById('err');return x.style.display=='block'?x.textContent:''})()")
            chk(f"{w}: no error banner",errshown=="",errshown)
            for tb in ["monetizare","utilizatori","rapoarte","configurare","rezumat"]:
                if await p.locator(f"#tabs button[data-t={tb}]").count():
                    await p.click(f"#tabs button[data-t={tb}]");await p.wait_for_timeout(250)
            ov=await p.evaluate("document.documentElement.scrollWidth-innerWidth")
            chk(f"{w}: no horizontal overflow",ov<=0,ov)
            if w==390: await p.screenshot(path=SC+"adm_390.png")
            chk(f"{w}: no page errors",not e,e);await c.close()
        # 3. PIN cerut de server: fereastra de PIN, apoi cererea se reia
        c,p,e=await mk(b,"admin@test.ro",True)
        chk("PIN dialog at start",await p.evaluate("document.getElementById('lock').classList.contains('on')"))
        await p.fill("#lk_pin","0000");await p.click("#lk_go");await p.wait_for_timeout(300)
        chk("wrong PIN message","greșit" in await p.inner_text("#lk_e"))
        await p.fill("#lk_pin","1234");await p.click("#lk_go");await p.wait_for_timeout(800)
        chk("PIN unlocks and data loads",await p.evaluate("!document.getElementById('lock').classList.contains('on')&&__calls.some(x=>x.startsWith('overview:'))"))
        await p.evaluate("__open=false");await p.click("#tabs button[data-t=utilizatori]");await p.wait_for_timeout(600)
        chk("server lock reopens PIN dialog",await p.evaluate("document.getElementById('lock').classList.contains('on')"))
        await p.fill("#lk_pin","1234");await p.click("#lk_go");await p.wait_for_timeout(800)
        chk("request retried after PIN",await p.evaluate("__calls.filter(x=>x.startsWith('users:')).length>=1"))
        await p.reload();await p.wait_for_timeout(1500)
        chk("reload while server keeps panel open: no PIN",await p.evaluate("!document.getElementById('lock').classList.contains('on')&&__calls.some(x=>x.startsWith('overview:'))"))
        await p.evaluate("sessionStorage.removeItem('open')");await p.reload();await p.wait_for_timeout(1500)
        chk("reload after server lock: PIN asked",await p.evaluate("document.getElementById('lock').classList.contains('on')"))
        await p.fill("#lk_pin","1234");await p.click("#lk_go");await p.wait_for_timeout(800)
        # ieșire
        await p.click("#who_out");await p.wait_for_timeout(1200)
        chk("sign out returns to login",await p.evaluate("document.getElementById('login').classList.contains('on')"))
        chk("no page errors (PIN)",not e,e);await c.close()
        await b.close()
    finally: srv.terminate()
    print("OK",len(ok),"FAIL",len(bad))
    for x in bad: print(" -",x)
asyncio.run(main())
