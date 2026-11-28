# Panoul de administrare ca pagină web (admin.html lângă aplicație): aceeași interfață ca artefactul,
# dar datele trec prin public.admin_call (doar administratori, PIN verificat pe server), cu contul LaTimp.
import sys, re
SRC, OUT = sys.argv[1], sys.argv[2]
h = open(SRC, encoding="utf-8").read()

def must(old, new, count=1):
    global h
    if h.count(old) != count:
        raise SystemExit("nu găsesc exact %d× : %r" % (count, old[:80]))
    h = h.replace(old, new)

# 1. antet: fără indexare, biblioteca Supabase (aceeași versiune ca aplicația), pictograma aplicației
must('<title>LaTimp Admin</title>',
     '<title>LaTimp Admin</title>\n<meta name="robots" content="noindex,nofollow">\n<link rel="icon" href="icons/favicon.svg" type="image/svg+xml">\n'
     '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js"></script>')

# 2. ecranul de conectare și stilurile lui
LOGIN_CSS = """
#login{position:fixed;inset:0;z-index:60;background:var(--bg);display:none;place-items:center;padding:24px max(16px,env(safe-area-inset-left,0px))}
#login.on{display:grid}
#login .lg{width:100%;max-width:400px;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:24px}
#login h2{margin:0 0 4px;font-size:24px;font-weight:800}
#login p{margin:0 0 14px;color:var(--mut)}
#login label{display:block;font-weight:700;margin:12px 0 6px}
#login input{width:100%;font:inherit;padding:12px 14px;border:1px solid var(--line);border-radius:12px;background:var(--bg);color:var(--ink)}
#login .go{margin-top:16px;width:100%;font:inherit;font-weight:700;padding:13px;border:0;border-radius:12px;background:var(--g);color:#fff;cursor:pointer}
#login .go:disabled{opacity:.6}
#login .ln{background:none;border:0;color:var(--g);font:inherit;font-weight:700;padding:10px 0;cursor:pointer}
#login .e{color:var(--a);margin-top:10px;min-height:1.2em}
#who{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:8px;font-size:14px;opacity:.9}
#who button,#who a{background:#ffffff22;color:inherit;border:0;border-radius:99px;padding:6px 12px;font:inherit;font-weight:700;cursor:pointer;text-decoration:none}
"""
must('</style>', LOGIN_CSS + '</style>', 1) if h.count('</style>') == 1 else None
if LOGIN_CSS not in h:
    i = h.find('</style>'); h = h[:i] + LOGIN_CSS + h[i:]

LOGIN_HTML = """<div id="login" role="dialog" aria-modal="true" aria-labelledby="lg_t"><div class="lg">
<h2 id="lg_t">LaTimp Admin</h2><p id="lg_p">Intră cu contul de administrator din LaTimp. Îți trimitem un cod pe e-mail.</p>
<div id="lg_1"><label for="lg_e">Adresa de e-mail</label><input id="lg_e" type="email" autocomplete="email" maxlength="254"><button class="go" id="lg_send">Trimite codul</button></div>
<div id="lg_2" hidden><label for="lg_c">Codul din e-mail</label><input id="lg_c" inputmode="numeric" autocomplete="one-time-code" maxlength="10" placeholder="123456"><button class="go" id="lg_ok">Intră</button><button class="ln" id="lg_back">Altă adresă</button></div>
<div id="lg_3" hidden><button class="go" id="lg_out">Ieși din cont</button></div>
<div class="e" id="lg_err" role="alert"></div></div></div>
"""
must('<header><h1>LaTimp Admin</h1><p id="sub">Panou privat · conectat la baza de date latimp (Supabase)</p></header>',
     LOGIN_HTML + '<header><h1>LaTimp Admin</h1><p id="sub">Panou privat · conectat la baza de date latimp (Supabase)</p><div id="who" hidden><span id="who_e"></span><a href="./">Deschide aplicația</a><button id="who_out">Ieși</button></div></header>')

# 3. legătura web: conectare, poarta admin_call, descărcări din browser
WEB_JS = r"""<script>
/* ---------- versiunea web a panoului: contul LaTimp + poarta public.admin_call ---------- */
window.LT_SB={url:"https://jzcwmucmxxedvwbtzrvp.supabase.co",key:"sb_publishable_qZDRrfEWVRhr9xeDBmME9A_y_7wIg5k"};
(function(){
 const dl={save:async function(o){const t=/\.csv$/.test(o.filename)?"text/csv":/\.json$/.test(o.filename)?"application/json":"application/octet-stream";const b=o.data instanceof Blob?o.data:new Blob([o.data],{type:t+";charset=utf-8"});const u=URL.createObjectURL(b),a=document.createElement("a");a.href=u;a.download=o.filename;document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(u)},4000)}};
 if(!window.claude)window.claude={use:async function(n){return n=="downloads"?dl:null}};
 const $=id=>document.getElementById(id);
 let SB=null;
 try{SB=supabase.createClient(LT_SB.url,LT_SB.key,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true,flowType:"implicit",storageKey:"latimp.auth"}})}catch(e){SB=null}
 const ADM=window.ADM={SB};
 /* „select admin.nume(argumente) as r” → nume + valori (șirurile, numerele, true/false/null din panou) */
 ADM.parse=function(sql){
  const m=String(sql).match(/^\s*select\s+admin\.([a-z_]+)\(([\s\S]*)\)(?:\s+as\s+r)?\s*$/i);
  if(!m)throw {code:"web_sql",message:"Cerere nerecunoscută"};
  const s=m[2],out=[];let i=0;
  const ws=()=>{while(i<s.length&&/\s/.test(s[i]))i++};
  while(true){ws();if(i>=s.length)break;
   let v;
   if(s[i]=="'"){i++;let t="";while(i<s.length){if(s[i]=="'"){if(s[i+1]=="'"){t+="'";i+=2;continue}i++;break}t+=s[i++]}v=t}
   else{const k=s.slice(i).match(/^(null|true|false|-?\d+(?:\.\d+)?)/i);if(!k)throw {code:"web_sql",message:"Argument nerecunoscut"};i+=k[0].length;const w=k[0].toLowerCase();v=w=="null"?null:w=="true"?true:w=="false"?false:Number(w)}
   ws();const c=s.slice(i).match(/^::[a-z ]+?(?=\s*(,|$))/i);if(c)i+=c[0].length;
   out.push(v);ws();if(s[i]==",")i++;else if(i<s.length)throw {code:"web_sql",message:"Argumente nerecunoscute"}}
  return {fn:m[1].toLowerCase(),args:out}};
 ADM.call=async function(sql){
  if(!SB)throw {code:"web_off",message:"Fără conexiune"};
  const p=ADM.parse(sql);
  const {data,error}=await SB.rpc("admin_call",{p_fn:p.fn,p_args:p.args});
  if(error){const m=String(error.message||"");throw {code:m=="pin_required"?"pin_required":m=="not_admin"?"not_admin":"tool_error",message:m=="pin_required"||m=="not_admin"?m:"ERROR: "+m}}
  return [{r:data}]};
 /* conectarea */
 let EM="";
 const err=t=>{$("lg_err").textContent=t||""};
 const step=n=>{["lg_1","lg_2","lg_3"].forEach((k,j)=>$(k).hidden=j!=n-1)};
 ADM.ready=function(){return new Promise(async res=>{
  if(!SB){$("login").classList.add("on");$("lg_p").textContent="Nu pot ajunge la server. Verifică internetul și reîncarcă pagina.";step(0);["lg_1","lg_2","lg_3"].forEach(k=>$(k).hidden=true);return}
  const check=async()=>{
   const {data}=await SB.auth.getSession();const u=data&&data.session&&data.session.user;
   if(!u){$("login").classList.add("on");step(1);$("lg_p").textContent="Intră cu contul de administrator din LaTimp. Îți trimitem un cod pe e-mail.";setTimeout(()=>$("lg_e").focus(),50);return}
   let ok=false;try{const r=await SB.rpc("am_i_admin");ok=r.data===true}catch(e){}
   if(!ok){$("login").classList.add("on");step(3);$("lg_p").textContent="Contul "+(u.email||"")+" nu este administrator. Ieși și intră cu contul potrivit.";return}
   $("login").classList.remove("on");$("who").hidden=false;$("who_e").textContent=u.email||"";$("sub").textContent="Panou privat · contul tău de administrator LaTimp";res(true)};
  $("lg_send").onclick=async()=>{const e=$("lg_e").value.trim();if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)){err("Scrie o adresă de e-mail validă.");return}
   $("lg_send").disabled=true;err("");
   try{const {error}=await SB.auth.signInWithOtp({email:e,options:{shouldCreateUser:false,emailRedirectTo:location.origin+location.pathname}});
    if(error){err(/signups not allowed|not found/i.test(error.message)?"Nu există un cont LaTimp cu această adresă.":/rate|seconds/i.test(error.message)?"Ai cerut prea multe coduri. Încearcă din nou peste un minut.":"Nu am putut trimite codul: "+error.message);return}
    EM=e;step(2);$("lg_p").textContent="Ți-am trimis un cod la "+e+". Poți apăsa și pe linkul din e-mail.";setTimeout(()=>$("lg_c").focus(),50)}
   finally{$("lg_send").disabled=false}};
  $("lg_e").onkeydown=ev=>{if(ev.key=="Enter")$("lg_send").click()};
  $("lg_ok").onclick=async()=>{const t=$("lg_c").value.replace(/\D/g,"");if(t.length<6){err("Scrie codul din e-mail.");return}
   $("lg_ok").disabled=true;err("");
   try{const {error}=await SB.auth.verifyOtp({email:EM,token:t,type:"email"});if(error){err("Codul nu e bun sau a expirat. Cere altul.");return}await check()}
   finally{$("lg_ok").disabled=false}};
  $("lg_c").onkeydown=ev=>{if(ev.key=="Enter")$("lg_ok").click()};
  $("lg_back").onclick=()=>{step(1);err("")};
  const out=async()=>{try{await SB.auth.signOut({scope:"local"})}catch(e){}location.reload()};
  $("lg_out").onclick=out;$("who_out").onclick=out;
  SB.auth.onAuthStateChange((ev)=>{if(ev=="SIGNED_IN"&&$("login").classList.contains("on"))check();if(ev=="SIGNED_OUT")location.reload()});
  await check()})};
})();
</script>
"""
must("<script>\n{\nconst PID='jzcwmucmxxedvwbtzrvp', SRV='Supabase';", WEB_JS + "<script>\n{\nconst PID='jzcwmucmxxedvwbtzrvp', SRV='Supabase';")

# 4. cererile: prin conector în claude.ai, prin poartă pe web; PIN-ul cerut de server deschide fereastra de PIN
must("""async function q(sql){
  if(!mcp)throw {code:'capability_disabled',message:'Pagina nu are acces la conectori aici. Deschide-o în claude.ai.'};""",
"""async function q(sql){
  if(!mcp&&window.ADM){
    try{return await ADM.call(sql)}
    catch(e){if(e&&e.code==='pin_required'&&!/admin\\.pin_(check|status)\\(/.test(sql)&&!locked){pinOn=true;pinUI();if(await pinPrompt('Introdu PIN-ul ca să continui.',true))return await ADM.call(sql)}throw e}
  }
  if(!mcp)throw {code:'capability_disabled',message:'Pagina nu are acces la conectori aici. Deschide-o în claude.ai.'};""")

must("""function errText(e){
  const c=e&&e.code;""", """function errText(e){
  const c=e&&e.code;
  if(c==='not_admin')return 'Contul tău nu este administrator.';
  if(c==='pin_required')return 'Introdu PIN-ul ca să continui.';
  if(c==='web_off')return 'Nu pot ajunge la server. Verifică internetul.';""")

must("""  if(!mcp){showErr('Pagina nu poate ajunge la Supabase aici. Deschide-o în claude.ai sau în aplicația Claude, cu conectorul Supabase conectat.');$('monState').textContent='Neconectat';return}""",
"""  if(!mcp&&window.ADM){await ADM.ready()}
  else if(!mcp){showErr('Pagina nu poate ajunge la Supabase aici. Deschide-o în claude.ai sau în aplicația Claude, cu conectorul Supabase conectat.');$('monState').textContent='Neconectat';return}""")

# 5. reîncărcarea paginii: dacă serverul încă ține panoul deschis (PIN corect în ultimele 10 minute), nu mai cere PIN-ul
must("if(pinOn)await pinPrompt(ps.locked_until?", "if(pinOn&&!(window.ADM&&!mcp&&!ps.locked_until&&await ADM.open()))await pinPrompt(ps.locked_until?")
must("ADM.call=async function(sql){", """ADM.open=async function(){try{await ADM.call("select admin.pin_status() as r");const {error}=await SB.rpc("admin_call",{p_fn:"health",p_args:[]});return !error}catch(e){return false}};
 ADM.call=async function(sql){""")

# 6. Conținut → „Reguli pentru termene” (content.rules): durate, linkuri oficiale, memento-uri recomandate, sfaturi, cursuri de rezervă
import subprocess as _sp, json as _json, os as _os
_q8 = open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "q8a.html"), encoding="utf-8").read() if _os.path.exists(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "q8a.html")) else open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "parts", "q8a.html"), encoding="utf-8").read()
_m = re.search(r"const RULES0=(\{.*?\n\});", _q8, re.S)
if not _m: raise SystemExit("nu găsesc RULES0 în q8a.html")
_def = _sp.run(["node", "-e", "process.stdout.write(JSON.stringify(" + _m.group(1) + ",null,1))"], capture_output=True, text=True, check=True).stdout
must('<div class="savebar"><button class="b" id="cc_save">',
 '<h3 style="margin-top:22px">Reguli pentru termene</h3><p class="mut">Durate, linkuri oficiale, memento-uri recomandate și sfaturi pentru termenele românești. Gol = regulile din aplicație. Scrii doar ce schimbi (de exemplu prețurile rovinietei), restul rămâne implicit. Linkurile trebuie să înceapă cu https://.</p>'
 '<textarea id="cc_rules" rows="10" spellcheck="false" style="font-family:ui-monospace,monospace;font-size:13px" placeholder="{ }"></textarea>'
 '<div class="row" style="margin-top:6px"><button class="b g sm" id="cc_rules_def" type="button">Pune regulile implicite</button><span class="mut" id="cc_rules_e"></span></div>'
 '<div class="savebar"><button class="b" id="cc_save">')
must("$('cc_ideas').value=(content.fallback_ideas||[])", "$('cc_rules').value=content.rules&&Object.keys(content.rules).length?JSON.stringify(content.rules,null,1):'';$('cc_ideas').value=(content.fallback_ideas||[])")
must("  const next={...content,challenge:", "  let rules=null;const rt=$('cc_rules').value.trim();if(rt){try{rules=JSON.parse(rt)}catch(x){throw new Error('Regulile nu sunt JSON valid: '+x.message)}if(!rules||typeof rules!=='object'||Array.isArray(rules))throw new Error('Regulile trebuie să fie un obiect JSON: { ... }.')}\n  const next={...content,challenge:")
must("try_lists:readLists()};", "try_lists:readLists()};if(rules)next.rules=rules;else delete next.rules;")
must("$('cc_ideas').oninput=ideasN;", "$('cc_ideas').oninput=ideasN;\n$('cc_rules_def').onclick=()=>{$('cc_rules').value=JSON.stringify(" + _def.replace("\n"," ").replace("</","<\\/") + ",null,1);$('cc_rules_e').textContent='Regulile implicite. Schimbă ce vrei, apoi salvează.'};")

# 7. Statistici → „Activare și primul memento” (admin.activation)
must('<div class="card"><h3>Cât revin utilizatorii</h3><div id="st_ret"></div></div>',
 '<div class="card"><h3>Activare și primul memento</h3><p class="mut">Activ = are cel puțin un memento programat: un termen cu dată și notificări sau e-mail pornite. Numărate pe server, fără date din agendă.</p><div id="st_act"></div></div><div class="card"><h3>Cât revin utilizatorii</h3><div id="st_ret"></div></div>')
must("statistici:loadStats", "statistici:()=>{loadStats();loadAct()}")
must("$('st_ref').onclick=()=>loadStats();", """$('st_ref').onclick=()=>{loadStats();loadAct()};
async function loadAct(){try{const a=await fn('admin.activation()');const P=(x,y)=>y?Math.round(x/y*100)+'%':'—';
 const R=[['Conturi active (cu memento programat)',a.activated,a.users],['Cu notificări pe telefon',a.push,a.users],['Cu memento-uri pe e-mail',a.mail,a.users],['Au primit cel puțin un memento',a.delivered,a.users],['Revin a doua zi',a.ret1,a.cohort1]];
 $('st_act').innerHTML=R.map(([l,x,y])=>'<div class="hb"><b>'+esc(l)+'</b><div class="meter"><i style="width:'+(y?x/y*100:0)+'%"></i></div><span>'+esc(P(x,y))+' <span class="mut">('+esc(x)+' din '+esc(y)+')</span></span></div>').join('')+
  '<p class="mut">'+(a.hours_to_first!=null?'Primul memento ajunge, la jumătate dintre conturi, în '+esc(a.hours_to_first)+' ore de la creare.':'Încă nu a ajuns niciun memento numărat (se numără de la 28.11.2026).')+'</p>'}catch(e){$('st_act').innerHTML='<div class="empty">'+esc(errText(e))+'</div>'}}""")

# 8. Monetizare → plăți pregătite: proba fără card, retragerile din contract, mulțumirea pentru primii utilizatori
must('<label class="f" for="p_trial">Zile de probă</label>', '<label class="f" for="p_trial" title="Proba nu cere card și nu devine plătită singură: la final accesul se oprește, iar utilizatorul alege dacă plătește.">Zile de probă (fără card)</label>')
must('  <button class="b" id="monSave">Salvează monetizarea și prețurile</button>\n</section>',
 '  <button class="b" id="monSave">Salvează monetizarea și prețurile</button>\n'
 '  <div class="card" style="margin-top:18px"><h3>Proba gratuită</h3><p class="mut">Pornește doar când „Abonamentul Control” e activ, aplicația nu mai e gratuită pentru toți și „Zile de probă” e peste 0. O singură probă pe cont, fără card. La final accesul se oprește singur; nu se plătește nimic automat. Utilizatorul primește un memento cu 2 zile înainte și în ultima zi.</p></div>\n'
 '  <div class="card"><h3>Retrageri din contract</h3><p class="mut">Cereri făcute din aplicație pentru plățile pe web din ultimele 14 zile. Rambursarea o faci din procesatorul de plăți, în cel mult 14 zile de la cerere; aici notezi starea. Cererea apare și în Rapoarte, unde îi poți răspunde.</p><div id="pay_wd"><div class="empty">Se încarcă…</div></div></div>\n'
 '  <div class="card"><h3>Mulțumire pentru primii utilizatori</h3><p class="mut">Când pornești plățile, cei care au cont de dinainte primesc Control gratuit câteva luni, fără cod și fără card. Se acordă o singură dată pe cont; cine are deja acces primește lunile în plus.</p>'
 '<div class="grid2"><div><label class="f" for="fd_m">Luni gratuite</label><select id="fd_m"><option value="1">1 lună</option><option value="3" selected>3 luni</option><option value="6">6 luni</option><option value="12">12 luni</option></select></div><div><label class="f" for="fd_b">Conturi create înainte de</label><input type="text" id="fd_b" placeholder="AAAA-LL-ZZ (gol = acum)"></div></div>'
 '<div class="row" style="margin-top:8px"><button class="b g sm" id="fd_prev" type="button">Câte conturi sunt?</button><button class="b sm" id="fd_go" type="button">Acordă mulțumirea</button></div><p class="mut" id="fd_out"></p></div>\n'
 '</section>')
must("lansari:loadLaunch,", "lansari:loadLaunch,monetizare:loadPay,")
must("async function loadAct(){", """
const WDS=['cerută','aprobată','rambursată','respinsă'];
async function loadPay(){try{const a=await fn('admin.withdrawals()')||[];
 $('pay_wd').innerHTML=a.length?a.map(w=>'<div class="hb" style="flex-wrap:wrap;gap:8px"><b>'+esc(w.ref)+'</b><span>'+esc(w.email||'—')+' · '+esc(w.amount)+' '+esc(w.currency||'')+' · cumpărat '+esc(String(w.bought_at||'').slice(0,10))+' · cerut '+esc(String(w.requested_at||'').slice(0,10))+'</span><select data-ref="'+esc(w.ref)+'" aria-label="Starea cererii '+esc(w.ref)+'">'+WDS.map(s=>'<option'+(s==w.status?' selected':'')+'>'+s+'</option>').join('')+'</select></div>').join(''):'<div class="empty">Nicio cerere de retragere.</div>';
 $('pay_wd').querySelectorAll('select').forEach(sel=>sel.onchange=()=>act(null,async()=>{await fn("admin.withdrawal_set("+sqlq(sel.dataset.ref)+","+sqlq(sel.value)+",'')");toast('Starea a fost salvată')}))}catch(e){$('pay_wd').innerHTML='<div class="empty">'+esc(errText(e))+'</div>'}}
const sqlq=v=>"'"+String(v).replace(/'/g,"''")+"'";
const fdB=()=>{const v=$('fd_b').value.trim();if(v&&!/^\\d{4}-\\d{2}-\\d{2}$/.test(v))throw new Error('Data trebuie scrisă AAAA-LL-ZZ.');return v?sqlq(v)+'::timestamptz':'now()'};
$('fd_prev').onclick=e=>act(e.target,async()=>{const r=await fn('admin.founders_preview('+fdB()+')');$('fd_out').textContent=r.users+' conturi create înainte de data aleasă; '+r.already+' au primit deja mulțumirea.'});
$('fd_go').onclick=e=>{if(!sure(e.target,'Acordă mulțumirea'))return;act(e.target,async()=>{const m=parseInt($('fd_m').value,10)||3;const g=await fn('admin.founders_grant('+m+','+fdB()+')');$('fd_out').textContent='Gata: '+g.granted+' conturi au primit '+g.months+' luni de Control gratuit.';toast('Mulțumirea a fost acordată')})};
async function loadAct(){""")

open(OUT, "w", encoding="utf-8").write(h)
print("admin.html:", len(h.encode()), "bytes")
