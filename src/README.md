# Sursa LaTimp

Aplicația publicată (`index.html` din rădăcină) se construiește din părțile din `parts/`.

- `build.sh` lipește părțile în ordinea din script și verifică sintaxa fiecărui bloc de script (node). Rezultatul e și prototipul.
- `build_web.sh` face versiunea web: `index.html` cu antetul PWA, `manifest.webmanifest`, `sw.js` (din `sw.tpl.js`), pictogramele, paginile publice din `site/` și paginile legale (`site/gen_legal.js`, din textele din `parts/q7l.html`).
- Căile din scripturi sunt cele din sesiunea de lucru; se schimbă variabila `D` (și calea pictogramelor `B`) când se construiește în alt loc.
- `tests/`: testele automate (Playwright, Python). `fake_sb.js` simulează serverul Supabase; `runt.sh 1 2 3` rulează testele alese.
- `supabase/functions/`: funcțiile de pe server (`ai`, `calendar`, `near`, `send-reminders`). Cheile secrete nu sunt aici: stau în Supabase (Vault și Edge Functions → Secrets).

Regula: o schimbare se face în `parts/`, apoi build, teste, și abia apoi se copiază `web/` în rădăcina depozitului.
