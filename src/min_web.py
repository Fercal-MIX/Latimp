# Micșorează versiunea web: dicționarul englez separat (se încarcă doar în engleză), scripturile și stilurile minificate cu esbuild.
import re, subprocess, sys, os
W = sys.argv[1]
ESB = "/opt/npm-tools/node_modules/esbuild/bin/esbuild"
p = os.path.join(W, "index.html")
h = open(p, encoding="utf-8").read()
before = len(h.encode())

def esb(code, loader):
    r = subprocess.run([ESB, "--loader=" + loader, "--minify", "--target=es2020" if loader == "js" else "--log-level=error", "--charset=utf8", "--log-level=error"],
                       input=code.encode(), capture_output=True)
    if r.returncode:
        sys.stderr.write(r.stderr.decode()[:800]); raise SystemExit("esbuild a eșuat (" + loader + ")")
    return r.stdout.decode().strip()

# 1. dicționarul englez într-un fișier separat
m = re.search(r"<script>\n/\* dicționar RO → EN.*?</script>", h, re.S)
if not m: raise SystemExit("nu am găsit dicționarul")
dict_js = m.group(0)[len("<script>"):-len("</script>")]
open(os.path.join(W, "i18n-en.js"), "w", encoding="utf-8").write(esb(dict_js, "js") + "\n")
loader = """<script>
/* dicționarul englez vine separat: se încarcă la pornire doar dacă limba e engleza, altfel când o alegi */
window.LT_EN=function(cb){if(LT_EN.ok){cb&&cb();return}if(LT_EN.q){LT_EN.q.push(cb);return}LT_EN.q=[cb];const s=document.createElement("script");s.src="i18n-en.js";s.onload=function(){LT_EN.ok=1;const q=LT_EN.q;LT_EN.q=null;q.forEach(f=>f&&f())};s.onerror=function(){const q=LT_EN.q;LT_EN.q=null;q.forEach(f=>f&&f())};document.head.appendChild(s)};
try{const v=JSON.parse(localStorage.getItem("buzunar.v2")||"{}");if(v&&v.lang=="en"){document.write('<script src="i18n-en.js"><\\/script>');LT_EN.ok=1}}catch(e){}
{const la0=langApply;langApply=function(){if(isEn()&&!LT_EN.ok){LT_EN(function(){la0();try{render()}catch(e){}});return}la0()}}
</script>"""
h = h[:m.start()] + loader + h[m.end():]

# 2. scripturile din pagină (fără src) și stilurile, minificate
def js_sub(mm):
    code = mm.group(1)
    if not code.strip(): return mm.group(0)
    return "<script>" + esb(code, "js") + "</script>"
h = re.sub(r"<script>(.*?)</script>", js_sub, h, flags=re.S)
def css_sub(mm):
    return mm.group(1) + esb(mm.group(2), "css") + "</style>"
h = re.sub(r"(<style[^>]*>)(.*?)</style>", css_sub, h, flags=re.S)
open(p, "w", encoding="utf-8").write(h)
print("index.html: %d → %d bytes; i18n-en.js: %d bytes" % (before, len(h.encode()), os.path.getsize(os.path.join(W, "i18n-en.js"))))
