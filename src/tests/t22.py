import asyncio,subprocess,time,json
from playwright.async_api import async_playwright
from web import *
U="http://localhost:8769/"
CFG={"mon":{"free":True,"control":False,"sparks":False,"invites":False,"referrals":False}}
STUB="""(()=>{const sub={endpoint:'https://push.example/abc',toJSON(){return{endpoint:this.endpoint,keys:{p256dh:'B'+'x'.repeat(86),auth:'y'.repeat(22)}}},async unsubscribe(){window.__unsub=(window.__unsub||0)+1;window.__has=false;return true}};
 window.__perm=window.__perm||'granted';
 if(window.PushManager){PushManager.prototype.subscribe=async function(){window.__has=true;return sub};PushManager.prototype.getSubscription=async function(){return window.__has?sub:null}}
 if(window.Notification){Object.defineProperty(Notification,'permission',{get(){return window.__perm=='granted'&&window.__asked?'granted':window.__perm=='denied'?'denied':'default'},configurable:true});Notification.requestPermission=async()=>{window.__asked=1;return window.__perm}}
 window.__rp=[];window.__rpc={get_my_access:async()=>({pro:true,source:'free',free_mode:true}),am_i_admin:async()=>false,set_reminders:async(a)=>{window.__rp.push(a.p);return a.p.length}};})();"""
def st(items,extra=""):
    return json.dumps({"onb":True,"at":5,"items":items,"cars":[],"saved":[],"credits":0,"used":0,"photos":0,"theme":"auto","nt":{"d":7,"h":"09:00","rep":False,"n":3,"i":7,"day":False,"wk":False},"acct":{"p":"email","e":"ana@test.ro","v":True}})
async def mk(b,items,signed=True,ua=None,perm="granted"):
    kw={"viewport":{"width":390,"height":800}}
    if ua: kw["user_agent"]=ua
    c=await b.new_context(**kw)
    if perm=="granted": await c.grant_permissions(["notifications"],origin=U[:-1])
    await fake_route(c,fonts=True)
    init="if(!sessionStorage.getItem('i')){sessionStorage.setItem('i','1');localStorage.setItem('fake.cfg',%s);localStorage.setItem('buzunar.v2',%s);"%(json.dumps(json.dumps(CFG)),json.dumps(st(items)))
    if signed: init+="localStorage.setItem('latimp.auth',JSON.stringify({user:{id:'u1',email:'ana@test.ro'},access_token:'t'}));"
    else: init+="(()=>{const s=JSON.parse(localStorage.getItem('buzunar.v2'));s.acct=null;localStorage.setItem('buzunar.v2',JSON.stringify(s))})();"
    init+="}window.__perm=%s;"%json.dumps(perm)
    await c.add_init_script(init);await c.add_init_script(STUB)
    p=await c.new_page();errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
    await p.goto(U);await p.wait_for_timeout(2500)
    return c,p,errs
async def main():
    srv=serve(8769)
    try:
        async with async_playwright() as pw:
            b=await pw.chromium.launch()
            d10="(()=>{const d=new Date();d.setDate(d.getDate()+10);return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')})()"
            c,p,e=await mk(b,[])
            await p.evaluate(f"S.items=[{{id:'a',g:'sub',t:'sub',n:'Netflix',p:40,c:'m',d:{d10}}},{{id:'b',g:'per',t:'zi',n:'Mama',d:{d10}}},{{id:'x',g:'sub',t:'sub',n:'Exemplu',p:1,c:'m',d:{d10},ex:1}}];store()")
            await p.evaluate("notifGo()");await p.wait_for_timeout(900)
            t=await p.inner_text("#main")
            i=t.find("Pe telefon");chk("phone row offers turning on","Memento-urile vin ca notificări" in t[i:i+120] and "Pornește" in t[i:i+140] and "în curând" not in t[i:i+120],t[i:i+150])
            await p.click("#main button:text-is('Pornește')");await p.wait_for_timeout(2500)
            chk("subscription saved on server",await p.evaluate("(JSON.parse(localStorage.getItem('fake.push')||'[]')).some(x=>x.endpoint=='https://push.example/abc'&&x.user_id=='u1')"))
            chk("push marked on",await p.evaluate("S.nt.push===true&&pushState()=='on'"))
            t=await p.inner_text("#main");chk("row shows active","activ" in t and "Oprește" in t)
            plan=await p.evaluate("window.__rp[window.__rp.length-1].filter(x=>!/^lt-mr-/.test(x.tag))")
            chk("schedule sent to server",isinstance(plan,list) and len(plan)==1,plan)
            if plan:
                at=await p.evaluate("(a)=>{const d=new Date(a);return [d.getHours(),d.getMinutes(),Math.round((d-new Date(new Date().toDateString()))/864e5)]}",plan[0]["at"])
                chk("reminder 7 days before at 09:00",at[0]==9 and at[1]==0 and at[2]==3,at)
                chk("same-time items grouped, example skipped","Și încă 1 termen." in plan[0]["body"] and plan[0]["title"] in ("Netflix","Mama"),plan[0])
            await p.evaluate("S.items.push({id:'c',g:'per',t:'prog',n:'Dentist',d:plus(20)});save()");await p.wait_for_timeout(3000)
            last=await p.evaluate("window.__rp[window.__rp.length-1].filter(x=>!/^lt-mr-/.test(x.tag))")
            chk("new item updates the schedule",len(last)==2 and any(x["title"]=="Dentist" for x in last),last)
            await p.evaluate("S.np=plus(5);save()");await p.wait_for_timeout(3000)
            last=await p.evaluate("window.__rp[window.__rp.length-1].filter(x=>!/^lt-mr-/.test(x.tag))")
            chk("pause skips reminders inside it",len(last)==1 and last[0]["title"]=="Dentist",last)
            await p.evaluate("S.np='';S.lang='en';save()");await p.wait_for_timeout(3000)
            last=await p.evaluate("window.__rp[window.__rp.length-1].filter(x=>!/^lt-mr-/.test(x.tag))")
            chk("English reminder text",any("Due in 7 days" in x["body"] for x in last),last)
            await p.evaluate("S.lang='ro';save();render()")
            sw=await p.evaluate("fetch('sw.js').then(r=>r.text())")
            chk("service worker shows pushed reminders",'addEventListener("push"' in sw and "notificationclick" in sw)
            await p.click("#main button:text-is('Oprește')");await p.wait_for_timeout(1500)
            chk("turn off removes subscription and schedule",await p.evaluate("!S.nt.push&&(JSON.parse(localStorage.getItem('fake.push')||'[]')).length==0&&window.__rp[window.__rp.length-1].length==0"))
            chk("A no errors",not e,e);await c.close()
            # fără cont: cere contul
            c,p,e=await mk(b,[],signed=False)
            await p.evaluate("notifGo()");await p.wait_for_timeout(800)
            await p.click("#main button:text-is('Pornește')");await p.wait_for_timeout(800)
            chk("asks for an account first",await p.evaluate("$('sheet').dataset.k")=="acct")
            await c.close()
            # blocate în setări
            c,p,e=await mk(b,[],perm="denied")
            await p.evaluate("notifGo()");await p.wait_for_timeout(800)
            chk("blocked state explained","blocate pentru LaTimp" in await p.inner_text("#main"))
            await c.close()
            # iPhone fără instalare
            c,p,e=await mk(b,[],ua="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
            await p.evaluate("notifGo()");await p.wait_for_timeout(800)
            chk("iPhone: install first","Cum fac" in await p.inner_text("#main"))
            await p.click("#main button:text-is('Cum fac')");await p.wait_for_timeout(500)
            chk("iPhone steps sheet","ecranul principal" in await p.inner_text("#sheet"))
            chk("D no errors",not e,e)
            await c.close();await b.close()
    finally: srv.terminate()
    done()
asyncio.run(main())
