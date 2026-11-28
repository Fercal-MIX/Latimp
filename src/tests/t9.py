import asyncio, re, json
from playwright.async_api import async_playwright
from web import *
URL = "file:///mnt/user-data/outputs/buzunar.html"
CODE_RE = re.compile(r"^LT-[A-HJ-NP-Z2-9]{5}-[A-HJ-NP-Z2-9]{5}$")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 820})
        pg = await ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.add_init_script(path=SC + "mock.js")
        await pg.goto(URL); await pg.wait_for_timeout(3000)
        await pg.click("#sheet button:has-text('Sări peste')"); await pg.wait_for_timeout(500)
        toast = lambda: pg.inner_text("#toast")
        async def as_user(uid, admin=False, pro=False):
            await pg.evaluate("""([u,a,p])=>{closeSheet();UID=u;CAN_ADMIN=a;VIEW='main';S=fresh();S.onb=true;S.pro=p;IVT={n:0,t:0};IVCHK=0;IVB=false;save();render()}""", [uid, admin, pro])
            await pg.wait_for_timeout(250)
        async def redeem(txt):
            await pg.evaluate("invOpen()"); await pg.wait_for_timeout(250)
            await pg.fill("#ivc", txt); await pg.click("#ivb"); await pg.wait_for_timeout(1400)
        async def make(note="Ana", max_=None, days=None):
            # codes are created in the admin panel now: the app only reads the public fingerprint
            return await pg.evaluate("""async([m,d])=>{const c=invGen();const h=await invHash(c);const t=new Date();if(d)t.setDate(t.getDate()+d);__db.set('codes/'+h,{max:m||1,exp:d?fmt(t):'',at:Date.now(),t:'full'});return invFmt(c)}""", [max_, days])

        # ---------- A. a code exists (created in the admin panel) ----------
        c1 = await make("Ana", 1, 365)
        chk("generated code has the LT-XXXXX-XXXXX form", bool(CODE_RE.match(c1)), c1)
        plain = c1.replace("-", "")
        keys = await pg.evaluate("[...__db.keys()]")
        ck = [k for k in keys if k.startswith("codes/")]
        chk("exactly one public code document, keyed by a 40-hex fingerprint", len(ck) == 1 and re.fullmatch(r"codes/[0-9a-f]{40}", ck[0]) is not None, ck)
        doc = await pg.evaluate("__db.get(%s)" % json.dumps(ck[0])) if ck else {}
        chk("public document has limit and expiry but no code, no note", doc.get("max") == 1 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", doc.get("exp", "")) is not None and plain not in json.dumps(doc) and "Ana" not in json.dumps(doc), doc)
        dump = await pg.evaluate("[...__db.entries()].filter(([k])=>!k.startsWith('data/users/')).map(([k,v])=>k+JSON.stringify(v)).join('|')")
        chk("the plaintext code appears in no document id and in no public document", plain not in dump and c1 not in dump, dump[:200])

        # ---------- C. a user redeems ----------
        await as_user("u_b", False)
        await pg.evaluate("tab('more')"); await pg.wait_for_timeout(500)
        t = await pg.inner_text("#main")
        chk("Mai mult offers 'Ai un cod de invitație?'", "Ai un cod de invitație?" in t)
        chk("no inv, no pro before", await pg.evaluate("S.inv===null&&S.pro===false"))
        await pg.evaluate("invOpen()"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=SC + "iv_redeem.png")
        await pg.evaluate("closeSheet()")
        await redeem(c1.lower().replace("-", " "))
        chk("redeem with spaces and lowercase works", await pg.evaluate("S.pro===true&&!!S.inv&&S.inv.was===false"), await pg.evaluate("JSON.stringify(S.inv)"))
        chk("toast confirms", "Cod activat" in await toast())
        rd = await pg.evaluate("__db.get('redeemed/u_b')")
        chk("redemption recorded for the user", bool(rd) and re.fullmatch(r"[0-9a-f]{40}", rd.get("h", "")) is not None, rd)
        chk("the redemption points at the public code", ("codes/" + (rd or {}).get("h", "")) in ck)
        await pg.evaluate("tab('agenda')"); await pg.wait_for_timeout(700)
        chk("Agenda header shows Control ✓", "Control ✓" in await pg.inner_text("#main"))
        await pg.evaluate("tab('more')"); await pg.wait_for_timeout(600)
        t = await pg.inner_text("#main")
        chk("Mai mult shows active invitation with expiry year", "Acces prin invitație" in t and "Acces complet până la" in t, t[:400])
        await pg.screenshot(path=SC + "iv_more.png", full_page=True)
        await pg.evaluate("S.credits=0;S.day=fmt(td());S.used=3;save()")
        chk("ideas are unlimited while active", await pg.evaluate("canPay(1,true)&&canPay(2,false)"))
        before = await pg.evaluate("[S.credits,S.used]")
        await pg.evaluate("pay(1,true);pay(2,false)")
        chk("using ideas costs nothing while active", await pg.evaluate("[S.credits,S.used]") == before)
        await pg.evaluate("tab('free')"); await pg.wait_for_timeout(700)
        chk("Timp liber pill shows Invitație, no paywall", "Invitație" in await pg.inner_text("#main") and "Gata cu ideile gratuite" not in await pg.inner_text("#main"))
        await pg.evaluate("openPlan('free')"); await pg.wait_for_timeout(500)
        sh = await pg.inner_text("#sheet")
        chk("Scântei sheet shows the invitation note, no packs, no Control", "Acces complet prin invitație" in sh and "5 scântei" not in sh and "Control" not in sh and "invitație?" not in sh, sh[:300])
        await pg.evaluate("closeSheet()")
        await pg.evaluate("openPlan('agenda')"); await pg.wait_for_timeout(500)
        sh = await pg.inner_text("#sheet")
        chk("Control sheet shows the invitation note, no purchase buttons", "Acces complet prin invitație" in sh and "Activează Control" not in sh and "Revino la gratuit" not in sh, sh[-300:])
        await pg.evaluate("closeSheet()")

        # ---------- D. limit of uses ----------
        await as_user("u_c", False)
        await redeem(c1)
        chk("second person is refused when the limit is 1", "deja folosit de numărul maxim" in await pg.inner_text("#sheet") and await pg.evaluate("S.pro===false&&S.inv===null"), await pg.inner_text("#sheet"))
        chk("refused person leaves no redemption record", await pg.evaluate("__db.has('redeemed/u_c')") is False)
        await pg.screenshot(path=SC + "iv_err.png")

        # ---------- E. wrong, malformed, rate limit ----------
        await pg.evaluate("closeSheet()")
        await redeem("hello")
        chk("malformed code is explained", "nu arată corect" in await pg.inner_text("#sheet"))
        await redeem("LT-AAAAA-AAAAA")
        chk("unknown code gives one neutral message", "Cod invalid sau retras" in await pg.inner_text("#sheet"))
        for i in range(4):
            await redeem("LT-BBBBB-BBBB" + "ACDEF"[i])
        await redeem("LT-CCCCC-CCCCC")
        chk("after 5 wrong tries the app asks to wait", "Prea multe încercări" in await pg.inner_text("#sheet"), await pg.inner_text("#sheet"))
        chk("a wrong code never changes access", await pg.evaluate("S.pro===false&&S.inv===null"))

        # ---------- F. expired code ----------
        await as_user("u_d", False)
        old = await pg.evaluate("""(async()=>{const c='LT'+'ABCDE'+'FGHJK';const h=await invHash(c);const d=new Date();d.setDate(d.getDate()-2);window.__db.set('codes/'+h,{max:5,exp:fmt(d),at:1,t:'full'});return c})()""")
        await redeem(old)
        chk("expired code is refused", "Codul a expirat" in await pg.inner_text("#sheet") and await pg.evaluate("S.inv===null"))

        # ---------- G. multi-use code keeps the previous plan ----------
        await pg.evaluate("closeSheet()")
        c2 = await make("Echipa", 5, 0)
        doc2 = await pg.evaluate("[...__db.keys()].filter(k=>k.startsWith('codes/')).map(k=>__db.get(k))")
        chk("unlimited code stores an empty expiry", any(d.get("max") == 5 and d.get("exp") == "" for d in doc2), doc2)
        await as_user("u_f", False, True)
        await redeem(c2)
        chk("a user who already had a plan redeems fine and 'was' is remembered", await pg.evaluate("S.pro===true&&S.inv&&S.inv.was===true&&S.inv.exp===''"), await pg.evaluate("JSON.stringify(S.inv)"))
        await as_user("u_g", False)
        await redeem(c2)
        chk("a second person can use a multi-use code", await pg.evaluate("S.pro===true&&!!S.inv"))
        # ---------- H. giving up frees the slot of the 1-use code ----------
        await as_user("u_b", False)
        await pg.evaluate("S.inv={h:(__db.get('redeemed/u_b')||{}).h,exp:'',at:1,was:false};S.pro=true;save()")
        await pg.evaluate("invEnd('Ai renunțat la acces.')"); await pg.wait_for_timeout(500)
        chk("giving up restores the previous plan and deletes the record", await pg.evaluate("S.pro===false&&S.inv===null&&!__db.has('redeemed/u_b')"))
        await as_user("u_c", False)
        await redeem(c1)
        chk("the freed slot can be used by someone else", await pg.evaluate("S.pro===true&&!!S.inv"), await pg.inner_text("#sheet"))

        # ---------- I. local expiry ----------
        await pg.evaluate("S.inv.exp=(()=>{const d=new Date();d.setDate(d.getDate()-1);return fmt(d)})();save();render()"); await pg.wait_for_timeout(400)
        chk("access ends locally on the expiry date", await pg.evaluate("S.pro===false&&S.inv===null"))

        # ---------- J. revocation ----------
        await as_user("u_c", False)
        await redeem(c1)
        chk("u_c has access again", await pg.evaluate("S.pro===true&&!!S.inv"))
        await as_user("u_f", False, True)
        await redeem(c2)
        hrev = await pg.evaluate("invHash(%s)" % json.dumps(c1.replace("-", "")))
        await pg.evaluate("__db.delete('codes/%s')" % hrev)
        chk("revoked code is gone from the public collection", not await pg.evaluate("__db.has('codes/%s')" % hrev))
        # the holder notices at the next check; someone who had a plan before keeps it
        await pg.evaluate("UID='u_c';CAN_ADMIN=false;VIEW='main';S=fresh();S.onb=true;S.pro=true;S.inv={h:'%s',exp:'',at:1,was:false};IVCHK=0" % hrev)
        await pg.evaluate("invCheck()"); await pg.wait_for_timeout(700)
        chk("revoked access ends at the next check", await pg.evaluate("S.pro===false&&S.inv===null") and "retras" in await toast())
        await pg.evaluate("UID='u_f';S=fresh();S.onb=true;S.pro=true;S.inv={h:'%s',exp:'',at:1,was:true};IVCHK=0" % hrev)
        await pg.evaluate("invCheck()"); await pg.wait_for_timeout(700)
        chk("a holder who had paid before keeps that plan", await pg.evaluate("S.pro===true&&S.inv===null"))
        # a still-valid code is not touched by the check
        await pg.evaluate("UID='u_g';S=fresh();S.onb=true;S.pro=true;S.inv={h:(()=>{return [...__db.keys()].find(k=>k.startsWith('codes/')).slice(6)})(),exp:'',at:1,was:false};IVCHK=0")
        await pg.evaluate("invCheck()"); await pg.wait_for_timeout(500)
        chk("a valid code survives the check", await pg.evaluate("S.pro===true&&!!S.inv"))

        # ---------- K. entry points when not active, no brand ----------
        await as_user("u_h", False)
        await pg.evaluate("openPlan('agenda')"); await pg.wait_for_timeout(400)
        chk("Control sheet offers the invitation link", "Ai un cod de invitație?" in await pg.inner_text("#sheet"))
        await pg.evaluate("closeSheet();openPlan('free')"); await pg.wait_for_timeout(400)
        sh = await pg.inner_text("#sheet")
        chk("Scântei sheet offers the link and never names Control", "Ai un cod de invitație?" in sh and "Control" not in sh)
        await pg.evaluate("closeSheet();invOpen()"); await pg.wait_for_timeout(300)
        sh = await pg.inner_text("#sheet")
        chk("no brand in the redeem sheet", "Claude" not in sh and "Anthropic" not in sh)
        # offline: no db -> clear message
        await pg.evaluate("DBOFF=true"); await pg.fill("#ivc", c2); await pg.click("#ivb"); await pg.wait_for_timeout(400)
        chk("without a connection the app says so", "nu poate fi verificat" in await pg.inner_text("#sheet") and await pg.evaluate("S.inv===null"))
        await pg.evaluate("DBOFF=false")
        # wipe removes the redemption record
        await as_user("u_f", False, False)
        await redeem(c2)
        await pg.evaluate("wipe()"); await pg.evaluate("wipe()"); await pg.wait_for_timeout(900)
        chk("'Șterge toate datele' also removes the redemption record", not await pg.evaluate("__db.has('redeemed/u_f')"))
        chk("no page errors", not errs, errs)
        await b.close()
    done()
asyncio.run(main())
