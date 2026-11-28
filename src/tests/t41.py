import asyncio,re
from playwright.async_api import async_playwright
from web import *
def txt(f): return re.sub(r"<[^>]+>"," ",open(SC+"web/"+f,encoding="utf-8").read())
pr,pe,tr,te=txt("confidentialitate.html"),txt("privacy.html"),txt("termeni.html"),txt("terms.html")
chk("privacy RO: automatic weather, ~10 km, kept on the phone","Vremea automată" in pr and "10 km" in pr and "rămân doar pe telefon" in pr)
chk("privacy RO: MET Norway as recipient, without IP, CC BY 4.0","MET Norway" in pr and "Nu primește adresa ta IP" in pr and "CC BY 4.0" in pr)
chk("privacy RO: payments data, no card details","Datele cardului nu ajung la noi" in pr)
chk("privacy RO: weekly backups kept 35 days, removed with the account","35 de zile" in pr and "se șterg și din ele" in pr)
chk("privacy RO: legal obligation for payment records","obligație legală" in pr)
chk("privacy EN mirrors RO","Automatic weather" in pe and "MET Norway" in pe and "35 days" in pe and "Card details never reach us" in pe and "legal obligation" in pe)
chk("terms RO: trial without card, never converts by itself","nu cere card și nu se transformă singură" in tr)
chk("terms RO: renewal notice, price change only next period","14 zile înainte de reînnoire" in tr and "următoarea perioadă" in tr)
chk("terms RO: 14-day withdrawal with request number","Dreptul de retragere" in tr and "număr de cerere" in tr)
chk("terms RO: no discontinued EU ODR platform; ADR via ANPC","soluționare online a litigiilor" not in tr and "SAL" in tr)
chk("terms EN mirrors RO","needs no card" in te and "Right of withdrawal" in te and "online dispute resolution platform" not in te and "ADR" in te)
for t,n in ((pr,"privacy RO"),(pe,"privacy EN"),(tr,"terms RO"),(te,"terms EN")):
    chk(n+": updated 28 November 2026","28 noiembrie 2026" in t or "28 November 2026" in t)
    chk(n+": operator filled in, no placeholders","Fercal Marius" in t and "{op}" not in t and "[numele" not in t and "{ml}" not in t)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.add_init_script(path=SC+"mock.js")
        await pg.goto("file:///mnt/user-data/outputs/buzunar.html");await pg.wait_for_timeout(2500)
        h=await pg.evaluate("legalHtml('priv','ro',legalVals('ro'),'h3')")
        chk("in-app privacy has the same new sections","MET Norway" in h and "35 de zile" in h)
        h=await pg.evaluate("legalHtml('terms','en',legalVals('en'),'h3')")
        chk("in-app terms (English) has the new payment rules","needs no card" in h and "Right of withdrawal" in h)
        chk("no page errors",not errs,errs)
        await b.close()
asyncio.run(main())
done()
