// Construiește paginile publice (RO + EN) din aceleași texte pe care le arată aplicația (q7l.html).
const fs = require("fs"), vm = require("vm"), path = require("path");
const [, , src, out] = process.argv;
const html = fs.readFileSync(src, "utf8");
const js = html.slice(html.indexOf("<script>") + 8, html.indexOf("</script>"));
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const ctx = { esc, S: { lang: "ro" }, legalTxt: null, legal: null, window: {}, CFG: { f: {} } };
vm.createContext(ctx);
vm.runInContext(js, ctx);
const LJ = [path.join(__dirname, "legal.json"), path.join(path.dirname(src), "site/legal.json")].find((f) => fs.existsSync(f));
const cfg = LJ ? JSON.parse(fs.readFileSync(LJ, "utf8")) : {};
vm.runInContext("var CFGW={legal:" + JSON.stringify(cfg) + "}", ctx);
const P = {
  priv: { ro: ["confidentialitate.html", "Politica de confidențialitate"], en: ["privacy.html", "Privacy policy"] },
  terms: { ro: ["termeni.html", "Termeni și condiții"], en: ["terms.html", "Terms and conditions"] }
};
const other = { ro: "en", en: "ro" };
for (const k of ["priv", "terms"]) for (const lg of ["ro", "en"]) {
  const v = vm.runInContext("legalVals(" + JSON.stringify(lg) + ")", ctx);
  const body = vm.runInContext("legalHtml(" + JSON.stringify(k) + "," + JSON.stringify(lg) + "," + JSON.stringify(v) + ",'h2')", ctx);
  const [file, title] = P[k][lg], [ofile, otitle] = P[k][other[lg]];
  const sib = k == "priv" ? P.terms[lg] : P.priv[lg];
  const page = `<!doctype html>
<html lang="${lg}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>${title} – LaTimp</title>
<meta name="description" content="${lg == "en" ? title + " for the LaTimp app." : title + " pentru aplicația LaTimp."}">
<link rel="icon" href="icons/favicon.svg" type="image/svg+xml">
<link rel="alternate" hreflang="${other[lg]}" href="${ofile}">
<style>
:root{--bg:#f4f2ea;--paper:#fff;--ink:#1b1f16;--mu:#5c6253;--ln:#e2ddcc;--ac:#11523a;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#0e110b;--paper:#171b12;--ink:#f0f1e8;--mu:#a4a995;--ln:#2a2f22;--ac:#74d3a3;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:400 17px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.w{max-width:720px;margin:0 auto;padding:28px max(20px,env(safe-area-inset-left,0px)) 64px max(20px,env(safe-area-inset-right,0px))}
nav{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:15px;margin-bottom:28px}
a{color:var(--ac);font-weight:600}
h1{font-size:clamp(30px,5vw,40px);line-height:1.15;letter-spacing:-.02em;margin:0 0 6px}
.d{color:var(--mu);margin:0 0 28px;font-size:15px}
h2{font-size:21px;margin:32px 0 8px;line-height:1.3}
p,li{max-width:66ch}
ul{padding-left:22px;margin:8px 0}li{margin:6px 0}
footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--ln);color:var(--mu);font-size:15px}
</style>
</head>
<body><div class="w">
<nav><a href="prezentare.html">LaTimp</a><a href="./">${lg == "en" ? "Open the app" : "Deschide aplicația"}</a><a href="${sib[0]}">${sib[1]}</a><a href="${ofile}" hreflang="${other[lg]}">${lg == "en" ? "Română" : "English"}</a></nav>
<h1>${title}</h1>
<p class="d">${lg == "en" ? "Last updated: 27 November 2026" : "Ultima actualizare: 27 noiembrie 2026"}</p>
${body}
<footer>${lg == "en" ? "The same text is available in the app, in More." : "Același text îl găsești și în aplicație, în Mai mult."}</footer>
</div></body>
</html>
`;
  fs.writeFileSync(path.join(out, file), page);
}
console.log("legal pages ok");
