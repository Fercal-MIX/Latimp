import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
SC="/tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/"
ok=[];bad=[]
def chk(n,c,e=""): (ok if c else bad).append(n+(" -> "+str(e)[:300] if (e and not c) else ""))
U="http://localhost:8771/"
FAKE=open(SC+"fake_sb.js").read()
CFG={"mon":{"free":True,"control":False,"sparks":False,"invites":False,"referrals":False}}
RPC="""window.__rpcs=[];window.__rpc={get_my_access:async()=>({pro:true,source:'free'}),am_i_admin:async()=>false,set_reminders:async()=>0,
 open_poll:async(a)=>{__rpcs.push(['open',a]);return{code:'ABCD2345'}},
 find_poll:async(a)=>{__rpcs.push(['find',a]);return a.p_code=='MYNE2345'?{code:a.p_code,options:['X','Y'],times:[],mine:true}:a.p_code=='WXYZ2345'?{code:a.p_code,options:['Bowling','Film','Picnic'],times:['Vineri seara','Duminică'],mine:false}:null},
 vote_poll:async(a)=>{__rpcs.push(['vote',a]);return{ok:true}}};"""
async def mk(b,signed=True):
    c=await b.new_context(viewport={"width":390,"height":800},service_workers="block")
    async def h(r): await r.fulfill(status=200,content_type="application/javascript",body=FAKE)
    await c.route("**/cdn.jsdelivr.net/**",h);await c.route("**/fonts.googleapis.com/**",lambda r:r.abort())
    st={"onb":True,"at":5,"items":[{"id":"a","g":"per","t":"zi","n":"Ziua Anei","d":"2027-02-10","sh":True},{"id":"b","g":"sub","t":"sub","n":"Netflix","p":40,"c":"m","d":"2027-01-10","sh":True}],"cars":[],"saved":[{"t":"Bowling"},{"t":"Film"},{"t":"Picnic"}],"credits":0,"used":0,"photos":0,"theme":"auto","acct":{"p":"email","e":"ana@test.ro","v":True} if signed else None}
    init="if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);localStorage.setItem('buzunar.v2',%s);"%(json.dumps(json.dumps(CFG)),json.dumps(json.dumps(st)))
    if signed: init+="localStorage.setItem('latimp.auth',JSON.stringify({user:{id:'u1',email:'ana@test.ro'},access_token:'t'}));"
    init+="}"+RPC
    await c.add_init_script(init)
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(2500)
    return c,p,errs
async def main():
    srv=subprocess.Popen(["python3","-m","http.server","8771","-d",SC+"web"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    try:
        async with async_playwright() as pw:
            b=await pw.chromium.launch()
            c,p,e=await mk(b)
            await p.evaluate("tab('free')");await p.wait_for_timeout(700);await p.evaluate("FSEG='saved';render()");await p.wait_for_timeout(600)
            await p.click("#main button:has-text('Pornește un vot')");await p.wait_for_timeout(500)
            await p.check("#sheet .pt[value='0']");await p.click("#pm_go");await p.wait_for_timeout(900)
            r=await p.evaluate("__rpcs.find(x=>x[0]=='open')")
            chk("vote created on server",r and r[1]["p_options"]==["Bowling","Film"] and r[1]["p_times"]==["Vineri seara"],r)
            chk("vote code shown",await p.evaluate("S.poll&&S.poll.c=='ABCD2345'") and "ABCD-2345" in await p.inner_text("#main"))
            await p.evaluate("localStorage.setItem('fake.pv',JSON.stringify([{opt:1,tm:0,name:'Ion'},{opt:1,tm:null,name:'Maria'}]));pvLoad()");await p.wait_for_timeout(700)
            t=await p.inner_text("#main")
            chk("votes counted with names","2 voturi" in t and "Ion" in t and "Maria" in t,t[:500])
            await p.click("#main button:has-text('Pune câștigătorul în agendă')");await p.wait_for_timeout(600)
            chk("winner can go to agenda",await p.evaluate("$('ov').classList.contains('on')||S.items.some(x=>/Film/.test(x.n||''))"))
            await p.evaluate("closeSheet();pollEnd()");await p.wait_for_timeout(500)
            chk("vote closed on server",await p.evaluate("__sb.pollDel==1&&!S.poll"))
            # alăturare
            await p.evaluate("pollJoin()");await p.wait_for_timeout(300);await p.fill("#pj_c","nope-0000");await p.click("#sheet button:has-text('Caută votul')");await p.wait_for_timeout(300)
            chk("bad code format refused","8 caractere" in await p.inner_text("#sheet"))
            await p.fill("#pj_c","QQQQ-2345");await p.click("#sheet button:has-text('Caută votul')");await p.wait_for_timeout(500)
            chk("unknown code","Nu am găsit" in await p.inner_text("#sheet"))
            await p.fill("#pj_c","wxyz-2345");await p.click("#sheet button:has-text('Caută votul')");await p.wait_for_timeout(500)
            chk("ballot shows ideas and times","Picnic" in await p.inner_text("#sheet") and "Duminică" in await p.inner_text("#sheet"))
            await p.click("#sheet .chips button:text-is('Picnic')");await p.wait_for_timeout(200);await p.click("#sheet .chips button:text-is('Duminică')");await p.wait_for_timeout(200)
            await p.fill("#pj_n","Ana");await p.click("#sheet button:has-text('Trimite votul')");await p.wait_for_timeout(600)
            v=await p.evaluate("__rpcs.find(x=>x[0]=='vote')")
            chk("vote sent",v and v[1]=={"p_code":"WXYZ2345","p_opt":2,"p_tm":1,"p_name":"Ana"},v)
            await p.wait_for_timeout(800);await p.evaluate("pollJoin()");await p.wait_for_timeout(700);await p.fill("#pj_c","MYNE-2345");await p.click("#sheet button:has-text('Caută votul')");await p.wait_for_timeout(700)
            tt=await p.inner_text("#toast");chk("own vote recognised","Este votul tău" in tt,[tt,await p.evaluate("[$('sheet').dataset.k,$('pj_c')&&$('pj_c').value,__rpcs.filter(x=>x[0]=='find').length]")])
            # familie
            await p.evaluate("tab('agenda')");await p.wait_for_timeout(600)
            await p.evaluate("famOpen()");await p.wait_for_timeout(400)
            await p.fill("#fw","Ana");await p.click("#sheet button:has-text('Creează codul de familie')");await p.wait_for_timeout(4500)
            fam=await p.evaluate("JSON.parse(localStorage.getItem('fake.fam')||'[]')")
            chk("family package saved, encrypted",len(fam)==1 and fam[0]["user_id"]=="u1" and len(fam[0]["group_hash"])==64 and "Ziua Anei" not in fam[0]["blob"],fam[:1])
            await p.evaluate("(async()=>{const k=FKEY;const b=await encr(k,{w:'Tata',it:[{n:'RCA',d:plus(5),t:'rca',g:'auto',rep:12,a:0}],gc:[]});const a=JSON.parse(localStorage.getItem('fake.fam'));a.push({user_id:'u2',group_hash:FH,blob:b});localStorage.setItem('fake.fam',JSON.stringify(a));await famPull()})()");await p.wait_for_timeout(800)
            chk("other member's dates appear",await p.evaluate("FAMV.length==1&&FAMV[0].w=='Tata'&&FAMV[0].it[0].n=='RCA'"))
            await p.evaluate("closeSheet();render()");await p.wait_for_timeout(500)
            chk("family card in Agenda","Tata · RCA" in await p.inner_text("#main"))
            await p.evaluate("famOpen()");await p.wait_for_timeout(400)
            await p.click("#sheet button:has-text('Ieși din familie')");await p.wait_for_timeout(200);await p.click("#sheet button:has-text('Apasă din nou ca să ieși')");await p.wait_for_timeout(800)
            chk("leaving removes own package",await p.evaluate("!S.fam&&!JSON.parse(localStorage.getItem('fake.fam')).some(x=>x.user_id=='u1')"))
            chk("A no errors",not e,e);await c.close()
            c,p,e=await mk(b,signed=False)
            await p.evaluate("tab('free')");await p.wait_for_timeout(600);await p.evaluate("FSEG='saved';render();pollNew()");await p.wait_for_timeout(500)
            chk("vote needs account",await p.evaluate("$('sheet').dataset.k")=="acct")
            await p.evaluate("closeSheet();famOpen()");await p.wait_for_timeout(500)
            chk("family needs account",await p.evaluate("$('sheet').dataset.k")=="acct")
            chk("B no errors",not e,e)
            await c.close();await b.close()
    finally: srv.terminate()
    print("OK",len(ok));print("FAIL",len(bad))
    for x in bad:print(" -",x)
asyncio.run(main())
