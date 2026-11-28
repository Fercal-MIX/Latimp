#!/bin/bash
set -e
D="$(cd "$(dirname "$0")" && pwd)"
P=$D; [ -d $D/parts ] && [ ! -f $D/q1.html ] && P=$D/parts
B=${LT_ICONS:-/mnt/user-data/outputs/latimp-brand/icons}
cd $D && bash build.sh >/dev/null
W=$D/web; rm -rf $W; mkdir -p $W/icons
if [ -d $B/pwa ]; then cp $B/pwa/icon-192.png $B/pwa/icon-512.png $B/pwa/icon-maskable-512.png $B/pwa/apple-touch-icon-180.png $B/favicon/favicon.svg $B/favicon/favicon-32.png $B/favicon/favicon.ico $W/icons/; else cp $D/../icons/* $W/icons/; fi
VER=$(grep -o 'const VER="[^"]*"' $P/q2.html | cut -d'"' -f2)
python3 - "$W" "$VER" "$D" <<'PY'
import sys,json
W,VER,D=sys.argv[1],sys.argv[2],sys.argv[3]
body=open(D+"/new.html").read()
body=body.replace('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap">','<style>@font-face{font-family:"Plus Jakarta Sans";src:url("fonts/plus-jakarta-sans.woff") format("woff");font-weight:200 800;font-style:normal;font-display:swap}</style>').replace('<title>LaTimp</title>\n','').replace('<meta name="claude:viewport-fit-sides" content="cover">\n','')
head=f'''<!doctype html><html lang="ro"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>LaTimp</title>
<meta name="description" content="Termenele, plățile și zilele importante la timp, plus idei pentru timpul liber.">
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#eff1f2">
<link rel="icon" href="icons/favicon.svg" type="image/svg+xml"><link rel="icon" href="icons/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon-180.png">
<meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="LaTimp"><meta name="apple-mobile-web-app-status-bar-style" content="default">
<style>:root{{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}html{{scroll-padding-top:env(safe-area-inset-top,0px)}}body{{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif}}img{{max-width:100%}}[hidden]:not([hidden=until-found i]){{display:none!important}}</style>
<script>
window.LT_WEB=true;
window.LT_SB={{url:"https://jzcwmucmxxedvwbtzrvp.supabase.co",key:"sb_publishable_qZDRrfEWVRhr9xeDBmME9A_y_7wIg5k"}};
/* descărcări în browser: aceeași interfață ca în prototip */
(function(){{const dl={{save:async function(o){{const t=/\\.json$/.test(o.filename)?"application/json":/\\.csv$/.test(o.filename)?"text/csv":/\\.ics$/.test(o.filename)?"text/calendar":"application/octet-stream";const b=o.data instanceof Blob?o.data:new Blob([o.data],{{type:t+";charset=utf-8"}});const u=URL.createObjectURL(b),a=document.createElement("a");a.href=u;a.download=o.filename;document.body.appendChild(a);a.click();a.remove();setTimeout(function(){{URL.revokeObjectURL(u)}},4000)}}}};
window.claude={{use:async function(n){{return n=="downloads"?dl:null}}}};}})();
if("serviceWorker" in navigator)addEventListener("load",function(){{navigator.serviceWorker.register("sw.js").catch(function(){{}})}});
</script>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js" async onload="window.sbReady&&sbReady()"></script>
</head><body>
'''
open(W+"/index.html","w").write(head+body+"\n</body></html>\n")
m={"name":"LaTimp","short_name":"LaTimp","description":"Termenele, plățile și zilele importante la timp, plus idei pentru timpul liber.","lang":"ro","dir":"ltr","id":"./","start_url":"./","scope":"./","display":"standalone","orientation":"portrait","background_color":"#11523a","theme_color":"#eff1f2","categories":["productivity","lifestyle","finance"],
"icons":[{"src":"icons/icon-192.png","sizes":"192x192","type":"image/png","purpose":"any"},{"src":"icons/icon-512.png","sizes":"512x512","type":"image/png","purpose":"any"},{"src":"icons/icon-maskable-512.png","sizes":"512x512","type":"image/png","purpose":"maskable"}]}
json.dump(m,open(W+"/manifest.webmanifest","w"),ensure_ascii=False,indent=1)
sw=open(D+"/sw.tpl.js").read().replace("__VER__",VER)
open(W+"/sw.js","w").write(sw)
open(W+"/.nojekyll","w").write("")
open(W+"/404.html","w").write('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=./"><title>LaTimp</title>')
PY
cp $D/site/prezentare.html $D/site/vot.html $D/site/*.webp $D/site/logo-*.svg $W/
mkdir -p $W/fonts && cp $D/fonts/plus-jakarta-sans.woff $D/fonts/OFL.txt $W/fonts/
python3 - $W/prezentare.html <<'PY2'
import sys
p=sys.argv[1];s=open(p).read()
s=s.replace('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n','')
s=s.replace('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap">','<style>@font-face{font-family:\"Plus Jakarta Sans\";src:url(\"fonts/plus-jakarta-sans.woff\") format(\"woff\");font-weight:200 800;font-style:normal;font-display:swap}</style>')
assert 'fonts.g' not in s
open(p,'w').write(s)
PY2
node $D/site/gen_legal.js $P/q7l.html $W
python3 $D/min_web.py $W
python3 $D/build_admin.py $D/admin_panel.html $W/admin.html
node --check $W/sw.js
echo web built: $(ls $W) VER=$VER
