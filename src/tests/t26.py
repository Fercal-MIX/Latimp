import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
SC="/tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/"
ok=[];bad=[]
def chk(n,c,e=""): (ok if c else bad).append(n+(" -> "+str(e)[:300] if (e and not c) else ""))
U="http://localhost:8775/"
FAKE=open(SC+"fake_sb.js").read()
CFG={"mon":{"free":True,"control":False,"sparks":False,"invites":False,"referrals":False}}
STUB="""(()=>{const sub={endpoint:'https://push.example/abc',toJSON(){return{endpoint:this.endpoint,keys:{p256dh:'B'+'x'.repeat(86),auth:'y'.repeat(22)}}},async unsubscribe(){window.__unsub=(window.__unsub||0)+1;window.__has=false;return true}};
 window.__perm=window.__perm||'granted';
 if(window.PushManager){PushManager.prototype.subscribe=async function(){window.__has=true;return sub};PushManager.prototype.getSubscription=async function(){return window.__has?sub:null}}
 if(window.Notification){Object.defineProperty(Notification,'permission',{get(){return window.__perm=='granted'&&window.__asked?'granted':window.__perm=='denied'?'denied':'default'},configurable:true});Notification.requestPermission=async()=>{window.__asked=1;return window.__perm}}
 window.__rp=[];window.__rpc={get_my_access:async()=>({pro:true,source:'free',free_mode:true}),am_i_admin:async()=>false,set_reminders:async(a)=>{window.__rp.push(a.p);return a.p.length}};})();"""
def st(items,extra=""):
    return json.dumps({"onb":True,"at":5,"items":items,"cars":[],"saved":[],"credits":0,"used":0,"photos":0,"theme":"auto","nt":{"d":7,"h":"09:00","rep":False,"n":3,"i":7,"day":False,"wk":False},"acct":{"p":"email","e":"ana@test.ro","v":True}})
async def mk(b,items,signed=True,pre="",geo=None):
    kw={"viewport":{"width":390,"height":800}}
    if geo: kw["geolocation"]=geo;kw["permissions"]=["geolocation"]
    c=await b.new_context(**kw)
    async def h(r): await r.fulfill(status=200,content_type="application/javascript",body=FAKE)
    await c.route("**/cdn.jsdelivr.net/**",h);await c.route("**/fonts.googleapis.com/**",lambda r:r.abort())
    init="if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);localStorage.setItem('buzunar.v2',%s);"%(json.dumps(json.dumps(CFG)),json.dumps(st(items)))
    if signed: init+="localStorage.setItem('latimp.auth',JSON.stringify({user:{id:'u1',email:'ana@test.ro'},access_token:'t'}));"
    else: init+="(()=>{const s=JSON.parse(localStorage.getItem('buzunar.v2'));s.acct=null;localStorage.setItem('buzunar.v2',JSON.stringify(s))})();"
    init+="}"
    await c.add_init_script(init);await c.add_init_script(STUB)
    await c.add_init_script("window.__fnb=[];window.__fn={ai:async(b)=>{__fnb.push(b);if(b.kind=='status')return{ready:!!window.__aiready,images:['image/jpeg','image/png']};if(window.__aicap)throw new Error('user_cap');if(b.kind=='photo')return{text:JSON.stringify({tip:'rca',nume:'Asigurator X',nr:'B 12 ABC',data:'2027-03-10',pret:null,perioada:null})};return{text:JSON.stringify([{t:'Atelier de olărit',d:'Două ore cu lut, pentru toată familia.',c:'cultura',m:'acasa'},{t:'Picnic în parc',d:'Pătură, sandvișuri și un joc de cărți.',c:'natura',m:'afara'},{t:'Seară de jocuri',d:'Trei jocuri de masă scurte.',c:'acasa',m:'acasa'},{t:'Muzeu interactiv',d:'Expoziții pe care le atingi.',c:'cultura',m:'oras'}])}}};"+pre)
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(2500)
    return c,p,errs
def _f(n,k,v,la,lo):
    p={"osm_key":k,"osm_value":v}
    if n: p["name"]=n
    return {"type":"Feature","properties":p,"geometry":{"type":"Point","coordinates":[lo,la]}}
OVP={"type":"FeatureCollection","features":[_f("Parcul Test","leisure","park",44.4371,26.1027),_f("Cinema Lumina","amenity","cinema",44.4400,26.1100),_f(None,"leisure","playground",44.4362,26.1030),_f("Bar X","amenity","bar",44.45,26.12),_f("Cinema Lumina","amenity","cinema",44.4400,26.1100)]}
async def main():
    global CFG
    srv=subprocess.Popen(["python3","-m","http.server","8775","-d",SC+"web"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    try:
        async with async_playwright() as pw:
            b=await pw.chromium.launch()
            plus="(n=>{const d=new Date();d.setDate(d.getDate()+n);return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')})"
            CFG={"mon":{"free":True}}
            # 1. zile libere calculate, parteneri doar reali
            c,p,e=await mk(b,[])
            h=await p.evaluate("Object.fromEntries(holYear(2028).map(x=>[x[1],x[0]]))")
            chk("holidays: Orthodox Easter 2028",h.get("Paștele")=="2028-04-16",h)
            chk("holidays: Good Friday and Pentecost 2028",h.get("Vinerea Mare")=="2028-04-14" and h.get("Rusaliile")=="2028-06-04",h)
            h=await p.evaluate("Object.fromEntries(holYear(2026).map(x=>[x[1],x[0]]))")
            chk("holidays: Easter 2026",h.get("Paștele")=="2026-04-12" and h.get("A doua zi de Rusalii")=="2026-06-01",h)
            y=await p.evaluate("new Date().getFullYear()")
            chk("holidays: covers two years ahead",await p.evaluate(f"HOL.some(x=>x[0]=='{y+2}-12-25')"))
            chk("holidays: shared date merged",await p.evaluate("HOL.filter(x=>x[0]=='2026-06-01').length==1 && HOL.find(x=>x[0]=='2026-06-01')[1].includes('Ziua Copilului')"))
            await p.evaluate(f"S.items=[{{id:'r1',g:'auto',t:'rca',n:'B 1 ABC',d:{plus}(5)}}];store()")
            sg=await p.evaluate("sugg(S.items[0],true)")
            chk("sponsor: no placeholder without partner","Exemplu" not in sg and "Partenerul tău" not in sg and "Opțiuni dezvoltator" not in sg,sg)
            sp=await p.evaluate("(()=>{const o=S.pro;S.pro=false;FIL='all';const h=agenda();S.pro=o;return h})()")
            chk("sponsor card hidden without partner","Exemplu" not in sp and "Vezi alternative" not in sp)
            await p.evaluate("CFGW=Object.assign(CFGW||{},{f:{rca_n:'Broker Bun',rca_u:'https://broker.example/rca',ad_n:'Comparator',ad_u:'https://compara.example',ad_t:'Compară abonamentele'},flags:{gifts:false}});cfgApply()")
            sg=await p.evaluate("sugg(S.items[0],true)")
            chk("sponsor: partner from panel","Broker Bun" in sg and "https://broker.example/rca" in sg and "Sponsorizat" in sg,sg)
            sp=await p.evaluate("(()=>{const o=S.pro;S.pro=false;FIL='all';const h=agenda();S.pro=o;return h})()")
            chk("sponsor card from panel","Compară abonamentele" in sp and "https://compara.example" in sp and "Exemplu" not in sp,sp[-500:])
            chk("flags from panel",await p.evaluate("CFG.flags.gifts===false&&CFG.flags.photo===true"))
            await p.evaluate("CFGW.f={rca_n:'Rău',rca_u:'http://nesigur.example'};cfgApply()")
            chk("panel: http partner rejected",await p.evaluate("CFG.f.rca_u===''"))
            chk("no errors 1",not e,e)
            await c.close()
            # 2. AI prin server
            c,p,e=await mk(b,[],pre="window.__aiready=false;")
            await p.wait_for_timeout(500)
            chk("ai off: no AI, no photo",await p.evaluate("AI===null&&PH===false"))
            await p.evaluate("window.__aiready=true;aiStatus(true)");await p.wait_for_timeout(400)
            chk("ai on: AI and photo ready",await p.evaluate("typeof AI=='function'&&PH===true"))
            r=await p.evaluate("aiCall('Ești un organizator. Dă idei. Detalii: test')")
            chk("ai: ideas parsed",isinstance(r,list) and r[0]["t"]=="Atelier de olărit",r)
            fb=await p.evaluate("__fnb.filter(x=>x.kind!='status')")
            chk("ai: kind ideas sent",fb and fb[-1]["kind"]=="ideas" and "Detalii: test" in fb[-1]["prompt"],fb)
            await p.evaluate("aiCall('Ești un consultant de cadouri. Răspunde.')")
            chk("ai: gift kind",await p.evaluate("__fnb[__fnb.length-1].kind")=="gift")
            await p.evaluate("closeSheet();tab('free');FSEG='ideas';render()");await p.wait_for_timeout(400)
            await p.evaluate("S.aiq=0;askIdeas()");await p.wait_for_timeout(500)
            chk("ai: consent asked before first AI idea","Înainte de prima idee" in await p.inner_text("#sheet"))
            await p.click("#sheet button:has-text('Sunt de acord')");await p.wait_for_timeout(1500)
            t=await p.inner_text("#main")
            chk("ai: ideas shown in Free time","Atelier de olărit" in t,str(await p.evaluate("[SRC,IDEAS.length,JSON.stringify(__fnb.slice(-1)).slice(0,300),typeof AI]")))
            png=b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7V\xbd\xfa\x00\x00\x00\x00IEND\xaeB`\x82"
            await p.evaluate("S.aic=Date.now();tab('agenda');photoStart()");await p.wait_for_timeout(400)
            await p.set_input_files("#ph",files=[{"name":"rca.png","mimeType":"image/png","buffer":png}]);await p.wait_for_timeout(1200)
            fb=await p.evaluate("__fnb[__fnb.length-1]")
            chk("ai: photo sent as image",fb["kind"]=="photo" and len(fb.get("image",""))>50 and fb["media"]=="image/jpeg",{k:(v if k!="image" else len(v)) for k,v in fb.items()} if fb else fb)
            chk("ai: photo fills the form",await p.evaluate("cur&&cur.t=='rca'&&cur.d=='2027-03-10'&&cur.n=='B 12 ABC'"),await p.evaluate("JSON.stringify(cur)"))
            await p.evaluate("closeSheet();window.__aicap=true;window.__T=[];const t0=toast;toast=m=>{__T.push(m);t0(m)}")
            r=await p.evaluate("aiCall('Ești un organizator. Dă idei. Detalii: x')")
            chk("ai: daily cap -> null and message",r is None and await p.evaluate("__T.some(x=>/cererile de azi/.test(x))"))
            await p.evaluate("acctOut()");await p.wait_for_timeout(300)
            await p.evaluate("acctOut()");await p.wait_for_timeout(800)
            chk("ai: off after sign out",await p.evaluate("AI===null&&PH===false"))
            await p.evaluate("closeSheet();S.aiq=0;IDEAS=[];tab('free');FSEG='ideas';render();askIdeas()");await p.wait_for_timeout(800)
            chk("ai off: local ideas without AI consent",await p.evaluate("S.aiq===0&&IDEAS.length>0&&SRC=='local'")and "Înainte de prima idee" not in await p.inner_text("body"))
            chk("no errors 2",not e,e)
            await c.close()
            # 3. calendarul care se actualizează singur
            c,p,e=await mk(b,[])
            await p.evaluate(f"S.items=[{{id:'k1',g:'auto',t:'itp',n:'B 9 XYZ',d:{plus}(20),rep:12}}];store();render()")
            tc=await p.evaluate("FIL='all';toolsCard()")
            chk("cal: row in tools","Calendar care se actualizează singur" in tc and "(demo)" not in tc,tc[:300])
            await p.evaluate("calOpen()");await p.wait_for_timeout(300)
            chk("cal: intro sheet","Creează linkul" in await p.inner_text("#sheet"))
            await p.click("#cf_go");await p.wait_for_timeout(800)
            cf=await p.evaluate("JSON.parse(localStorage.getItem('fake.calf')||'null')")
            tok=await p.evaluate("S.calf&&S.calf.t")
            import re as _re, hashlib
            chk("cal: token 48 hex",bool(tok) and _re.fullmatch(r"[0-9a-f]{48}",tok) is not None,tok)
            chk("cal: only hash on server",cf and cf["token_hash"]==hashlib.sha256(tok.encode()).hexdigest() and tok not in json.dumps(cf),cf and cf.get("token_hash"))
            chk("cal: calendar file",cf and "BEGIN:VCALENDAR" in cf["ics"] and "X-WR-CALNAME:LaTimp" in cf["ics"] and "B 9 XYZ" in cf["ics"],cf and cf["ics"][:300])
            sh=await p.inner_html("#sheet")
            chk("cal: Google link with webcal",("calendar.google.com/calendar/render?cid=webcal%3A%2F%2F" in sh) and tok in sh,sh[:500])
            chk("cal: phone link",('href="webcal://' in sh))
            await p.evaluate(f"closeSheet();S.items.push({{id:'k2',g:'per',t:'zi',n:'Bunica',d:{plus}(30),rep:12}});save()");await p.wait_for_timeout(3500)
            cf=await p.evaluate("JSON.parse(localStorage.getItem('fake.calf')||'null')")
            chk("cal: updates on save",cf and "Bunica" in cf["ics"],cf and cf["ics"][-300:])
            await p.evaluate("calOpen()");await p.wait_for_timeout(300)
            await p.click("#sheet button:has-text('Oprește linkul')");await p.wait_for_timeout(200)
            chk("cal: stop asks twice","Apasă din nou" in await p.inner_text("#sheet"))
            await p.click("#sheet button:has-text('Apasă din nou')");await p.wait_for_timeout(600)
            chk("cal: stopped",await p.evaluate("S.calf===null&&localStorage.getItem('fake.calf')===null"))
            chk("no errors 3",not e,e)
            await c.close()
            c,p,e=await mk(b,[],signed=False)
            await p.evaluate("calOpen()");await p.wait_for_timeout(400)
            chk("cal: signed out asks for account",await p.locator("#ac_e").count()==1)
            await c.close()
            # 4. deblocare cu amprenta
            BIO="(()=>{window.PublicKeyCredential=window.PublicKeyCredential||function(){};PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable=async()=>true;window.__bio={c:0,g:0,fail:false};Object.defineProperty(navigator,'credentials',{value:{create:async(o)=>{__bio.c++;__bio.copt=o;return{rawId:new Uint8Array([1,2,3]).buffer}},get:async(o)=>{__bio.g++;__bio.gopt=o;if(__bio.fail)throw new Error('x');return{id:'x'}}},configurable:true})})();"
            c,p,e=await mk(b,[],pre=BIO)
            await p.evaluate("lockPut({s:'a'.repeat(32),h:'b'.repeat(64),b:false,t:0});VIEW='main';tab('more')");await p.wait_for_timeout(300)
            chk("bio: real sensor text",await p.evaluate("lockRows().includes('Folosește senzorul telefonului')&&!lockRows().includes('prototip')"))
            await p.evaluate("lockOpt('b')");await p.wait_for_timeout(400)
            o=await p.evaluate("lockGet()")
            chk("bio: enabled with credential",o and o["b"] is True and o.get("cid")=="AQID",o)
            chk("bio: platform authenticator, verification required",await p.evaluate("__bio.copt.publicKey.authenticatorSelection.authenticatorAttachment=='platform'&&__bio.copt.publicKey.authenticatorSelection.userVerification=='required'"))
            await p.evaluate("lockPut({s:'c'.repeat(32),h:'d'.repeat(64),b:true,t:0})")
            chk("bio: PIN change keeps credential",await p.evaluate("lockGet().cid")=="AQID")
            await p.evaluate("__bio.fail=true;__bio.g=0;lockShow('lock')");await p.wait_for_timeout(800)
            chk("bio: asks the sensor by itself when locked",await p.evaluate("__bio.g")==1)
            chk("bio: button on lock screen",await p.locator("#lk button:has-text('Amprentă sau față')").count()==1)
            await p.evaluate("__bio.fail=true");await p.click("#lk button:has-text('Amprentă')");await p.wait_for_timeout(300)
            chk("bio: failure keeps lock",await p.locator("#lk").count()==1 and "Scrie PIN-ul" in await p.inner_text("#lk"))
            await p.evaluate("__bio.fail=false");await p.click("#lk button:has-text('Amprentă')");await p.wait_for_timeout(300)
            chk("bio: success unlocks",await p.locator("#lk").count()==0)
            chk("bio: asks for the saved credential",await p.evaluate("__bio.gopt.publicKey.allowCredentials[0].id.length==3&&__bio.gopt.publicKey.userVerification=='required'"))
            await p.evaluate("lockOpt('b')")
            chk("bio: turn off removes credential",await p.evaluate("lockGet().b===false&&!lockGet().cid"))
            chk("no errors 4",not e,e)
            await c.close()
            # 5. Lângă mine
            c,p,e=await mk(b,[],geo={"latitude":44.4361,"longitude":26.1027})
            seen=[]
            async def ovp(r):
                seen.append(r.request.url)
                await r.fulfill(status=200,content_type="application/json",headers={"Access-Control-Allow-Origin":"*"},body=json.dumps(OVP))
            await c.route("**/photon.komoot.io/**",ovp)
            await p.evaluate("tab('free');FSEG='near';render()");await p.wait_for_timeout(300)
            t=await p.inner_text("#main")
            chk("near: no placeholder","Nu este disponibil încă" not in t and "Folosește locația mea" in t,t[:300])
            chk("near: map links",await p.locator("#main a.chip").count()==8)
            await p.click("#main button:has-text('Folosește locația mea')");await p.wait_for_timeout(1500)
            t=await p.inner_text("#main")
            chk("near: places listed","Parcul Test" in t and "Cinema Lumina" in t and "Loc de joacă" in t,t[:600])
            chk("near: unknown kinds dropped","Bar X" not in t)
            chk("near: duplicates merged",t.count("Cinema Lumina")==1)
            qq=__import__("urllib.parse").parse.unquote_plus(seen[0]) if seen else ""
            chk("near: rounded position sent","lat=44.44&lon=26.1&" in qq and "44.4361" not in qq and "osm_tag=leisure:park" in qq,qq[:200])
            chk("near: attribution","OpenStreetMap" in t)
            chk("near: distance shown",("m" in t) and ("110 m" in t or "100 m" in t or "150 m" in t),t[:400])
            await p.click("#main .chips button:has-text('Cinematografe')");await p.wait_for_timeout(300)
            t=await p.inner_text("#main")
            chk("near: filter","Cinema Lumina" in t and "Parcul Test" not in t)
            await p.click("#main .grp button:has-text('Salvează')");await p.wait_for_timeout(300)
            chk("near: saved to Saved",await p.evaluate("S.saved.some(x=>x.t=='Cinema Lumina'&&/Cinematograf/.test(x.d))"))
            await c.unroute("**/photon.komoot.io/**");await c.route("**/photon.komoot.io/**",lambda r:r.abort())
            await p.evaluate("window.__rpc.near_start=async(a)=>{window.__ns=a;return{status:'wait'}};window.__rpc.near_poll=async()=>({status:'ok',data:{at:'2026-11-27',items:[{n:'Muzeul Server',c:'museum',la:44.44,lo:26.1,m:500,o:'',w:''}]}})")
            await p.click("#main button:has-text('Caută din nou de aici')");await p.wait_for_timeout(3500)
            chk("near: server fallback","Muzeul Server" in await p.inner_text("#main"))
            chk("near: server gets rounded position",await p.evaluate("window.__ns&&__ns.p_lat==44.44&&__ns.p_lon==26.1"))
            await p.evaluate("delete window.__rpc.near_start;delete window.__rpc.near_poll");await p.evaluate("NEAR=null;render()")
            await p.click("#main button:has-text('Folosește locația mea')");await p.wait_for_timeout(1500)
            t=await p.inner_text("#main")
            chk("near: clear error when all fail","Nu am putut încărca locurile" in t,t[:400])
            chk("no errors 5",not e,e)
            await c.close()
            # 6. memento-uri pe e-mail
            CFG={"mon":{"free":True}}
            c,p,e=await mk(b,[])
            await p.evaluate(f"S.items=[{{id:'m1',g:'per',t:'zi',n:'Tata',d:{plus}(20)}}];store();notifGo()");await p.wait_for_timeout(600)
            t=await p.inner_text("#main")
            chk("mail off: no row, no 'soon'","Pe e-mail" not in t and "în curând" not in t,t[-400:])
            await p.evaluate("CFGW=Object.assign(CFGW||{},{mail_rem:{on:true}});render()");await p.wait_for_timeout(300)
            t=await p.inner_text("#main")
            chk("mail on: row with address","Pe e-mail" in t and "ana@test.ro" in t)
            await p.click("#main button[aria-label='Memento-uri pe e-mail']");await p.wait_for_timeout(2600)
            rp=await p.evaluate("window.__rp")
            chk("mail: schedule sent with mail flag",await p.evaluate("S.nt.mail===true") and rp and rp[-1] and all(x.get("mail") is True for x in rp[-1]) and len(rp[-1])>0,rp[-1:] if rp else rp)
            await p.evaluate(f"S.items=[{{id:'c1',g:'auto',t:'itp',n:'B 1 XYZ',d:{plus}(1)}}];S.nt.d=7;S.nt.day=false;store()")
            cu=await p.evaluate("remPlan()")
            chk("reminder: catch-up when the early reminder already passed",len(cu)==1 and ("mâine" in cu[0]["body"] or "azi" in cu[0]["body"]) and await p.evaluate("(s=>new Date(s)>new Date())(%s)"%json.dumps(cu[0]["at"])),cu)
            await p.evaluate(f"S.items=[{{id:'c2',g:'auto',t:'itp',n:'B 2 XYZ',d:{plus}(30)}}];store()")
            cu=await p.evaluate("remPlan()")
            chk("reminder: normal 7 days before, no extra",len(cu)==1 and "7 zile" in cu[0]["body"],cu)
            chk("no errors 6",not e,e)
            await c.close()
            await b.close()
    finally:
        srv.terminate()
    print("OK",len(ok));print("FAIL",len(bad))
    for x in bad:print(" -",x)
asyncio.run(main())
