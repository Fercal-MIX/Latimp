// LaTimp: trimite memento-urile ajunse la oră ca notificări push (web push, VAPID) și, dacă utilizatorul a ales, pe e-mail.
// Apelat la 5 minute de pg_cron, cu antetul x-cron-secret (cheia din Vault). Nu cere token de utilizator.
// E-mailul pornește doar cu secretele SMTP_USER și SMTP_PASS și cu app.mail_rem.on = true în panou.
import { createClient } from "npm:@supabase/supabase-js@2.45.4";
import webpush from "npm:web-push@3.6.7";
import nodemailer from "npm:nodemailer@6.9.16";

const json = (b: unknown, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { "Content-Type": "application/json" } });
const esc = (s: string) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!));

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ error: "method" }, 405);
  const url = Deno.env.get("SUPABASE_URL"), key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) return json({ error: "config" }, 500);
  const db = createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data: cfg, error: ce } = await db.rpc("push_config");
  if (ce || !cfg?.priv || !cfg?.pub || !cfg?.cron) return json({ error: "keys" }, 500);
  if (req.headers.get("x-cron-secret") !== cfg.cron) return json({ error: "unauthorized" }, 401);
  webpush.setVapidDetails("https://fercal-mix.github.io/Latimp/", cfg.pub, cfg.priv);

  const now = new Date();
  const since = new Date(now.getTime() - 24 * 3600 * 1000).toISOString();
  const { data: due, error: de } = await db.from("reminders").select("id,user_id,title,body,tag,mail")
    .is("sent_at", null).lte("at", now.toISOString()).gte("at", since).order("at").limit(500);
  if (de) return json({ error: "query" }, 500);
  if (!due?.length) return json({ ok: true, due: 0, sent: 0 });

  const users = [...new Set(due.map((r) => r.user_id))];
  const { data: subs } = await db.from("push_subs").select("id,user_id,endpoint,p256dh,auth,fails").in("user_id", users);
  let sent = 0, gone = 0, mailed = 0;
  const done: number[] = [];
  for (const r of due) {
    const mine = (subs || []).filter((s) => s.user_id === r.user_id);
    const payload = JSON.stringify({ title: r.title, body: r.body, tag: r.tag || ("r" + r.id), url: "./?from=push" });
    for (const s of mine) {
      try {
        await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, payload, { TTL: 6 * 3600, urgency: "normal" });
        sent++;
        await db.from("push_subs").update({ last_ok: now.toISOString(), fails: 0 }).eq("id", s.id);
      } catch (e) {
        const code = (e as { statusCode?: number }).statusCode || 0;
        if (code === 404 || code === 410) { gone++; await db.from("push_subs").delete().eq("id", s.id); }
        else await db.from("push_subs").update({ fails: (s.fails || 0) + 1 }).eq("id", s.id);
      }
    }
    done.push(r.id);
  }

  // e-mail: un singur mesaj pe utilizator la fiecare rulare, cu toate memento-urile lui ajunse la oră
  const su = Deno.env.get("SMTP_USER"), sp = Deno.env.get("SMTP_PASS");
  const { data: appRow } = await db.from("app_config").select("value").eq("key", "app").maybeSingle();
  const mailOn = !!su && !!sp && (appRow?.value as { mail_rem?: { on?: boolean } } | null)?.mail_rem?.on === true;
  const toMail = due.filter((r) => r.mail);
  if (mailOn && toMail.length) {
    const tr = nodemailer.createTransport({
      host: Deno.env.get("SMTP_HOST") || "smtp.gmail.com", port: Number(Deno.env.get("SMTP_PORT") || 465), secure: true,
      auth: { user: su, pass: sp },
    });
    const by = new Map<string, typeof toMail>();
    for (const r of toMail) by.set(r.user_id, [...(by.get(r.user_id) || []), r]);
    for (const [uid, list] of by) {
      try {
        const { data: u } = await db.auth.admin.getUserById(uid);
        const to = u?.user?.email;
        if (!to) continue;
        const subject = list.length === 1 ? `${list[0].title}: ${list[0].body}`.slice(0, 140) : `LaTimp: ${list.length} memento-uri`;
        const text = list.map((r) => `${r.title}\n${r.body}`).join("\n\n") +
          "\n\nDeschide LaTimp: https://fercal-mix.github.io/Latimp/\nOprești memento-urile pe e-mail din aplicație: Mai mult → Notificări.";
        const html = `<div style="font-family:system-ui,sans-serif;font-size:16px;line-height:1.5;color:#1b1f16">` +
          list.map((r) => `<p style="margin:0 0 14px"><b>${esc(r.title)}</b><br>${esc(r.body)}</p>`).join("") +
          `<p style="margin:18px 0 0"><a href="https://fercal-mix.github.io/Latimp/" style="color:#11523a;font-weight:700">Deschide LaTimp</a></p>` +
          `<p style="margin:14px 0 0;font-size:13px;color:#5c6253">Oprești memento-urile pe e-mail din aplicație: Mai mult → Notificări.</p></div>`;
        await tr.sendMail({ from: { name: "LaTimp", address: su! }, to, subject, text, html });
        mailed++;
      } catch (e) { console.error("mail", String(e).slice(0, 200)); }
    }
  }
  // marcate ca trimise chiar dacă utilizatorul nu are abonare: nu se trimit mai târziu, întârziat
  for (let i = 0; i < done.length; i += 200) await db.from("reminders").update({ sent_at: now.toISOString() }).in("id", done.slice(i, i + 200));
  return json({ ok: true, due: due.length, sent, gone, mailed });
});
