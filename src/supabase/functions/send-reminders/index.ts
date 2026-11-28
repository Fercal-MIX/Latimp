// LaTimp: trimite memento-urile ajunse la oră ca notificări push (web push, VAPID) și, dacă utilizatorul a ales, pe e-mail.
// Apelat la 5 minute de pg_cron, cu antetul x-cron-secret (cheia din Vault). Nu cere token de utilizator.
// E-mailul pornește doar cu secretele SMTP_USER și SMTP_PASS și cu app.mail_rem.on = true în panou.
import { createClient } from "npm:@supabase/supabase-js@2.45.4";
import webpush from "npm:web-push@3.6.7";
import nodemailer from "npm:nodemailer@6.9.16";

const json = (b: unknown, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { "Content-Type": "application/json" } });
const BASE = "https://fercal-mix.github.io/Latimp/";
const ACT_RO: Record<string, string> = { p: "Am plătit", r: "Am reînnoit", f: "Am făcut", g: "Gata" };
const ACT_EN: Record<string, string> = { p: "Paid", r: "Renewed", f: "Done", g: "Done" };
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
  // rândurile sunt marcate ca trimise când sunt luate: o rulare oprită la mijloc nu le mai retrimite, două rulări nu iau același rând
  const { data: due, error: de } = await db.rpc("claim_reminders", { p_limit: 300 });
  if (de) return json({ error: "query" }, 500);
  if (!due?.length) return json({ ok: true, due: 0, sent: 0 });

  const users = [...new Set(due.map((r) => r.user_id))];
  const { data: subs } = await db.from("push_subs").select("id,user_id,endpoint,p256dh,auth,fails,lang").in("user_id", users);
  let sent = 0, gone = 0, mailed = 0;
  const okIds: number[] = [], okSubs: number[] = [], goneSubs: number[] = [], failSubs: { id: number; fails: number }[] = [];
  const jobs: (() => Promise<void>)[] = [];
  for (const r of due) {
    // eticheta „lt-<timp>~<id termen>~<p|r|f|g>” spune ce termen deschide notificarea și ce buton are („Am plătit” etc.)
    const m = /~([A-Za-z0-9_-]{3,40})(?:~([prfg]))?$/.exec(r.tag || "");
    const it = m?.[1] || "", act = m?.[2] || "";
    const link = BASE + "?from=push" + (it ? "&it=" + encodeURIComponent(it) : "");
    for (const s of (subs || []).filter((s) => s.user_id === r.user_id)) {
      const en = s.lang === "en";
      const actions = act ? [{ action: "done", title: (en ? ACT_EN : ACT_RO)[act] }] : [];
      // câmpurile de sus le citește service worker-ul; „notification” e formatul declarativ (Safari 18.4+), care se afișează și fără service worker
      const payload = JSON.stringify({ title: r.title, body: r.body, tag: r.tag || ("r" + r.id), url: link, it, actions,
        web_push: 8030, notification: { title: r.title, body: r.body, navigate: link, tag: r.tag || ("r" + r.id), lang: en ? "en" : "ro" } });
      jobs.push(async () => {
        try {
          await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, payload, { TTL: 6 * 3600, urgency: "normal" });
          sent++; okIds.push(r.id); okSubs.push(s.id);
        } catch (e) {
          const code = (e as { statusCode?: number }).statusCode || 0;
          if (code === 404 || code === 410) { gone++; goneSubs.push(s.id); } else failSubs.push({ id: s.id, fails: (s.fails || 0) + 1 });
        }
      });
    }
  }
  for (let i = 0; i < jobs.length; i += 20) await Promise.all(jobs.slice(i, i + 20).map((f) => f()));
  const uniq = <T>(a: T[]) => [...new Set(a)];
  if (okSubs.length) await db.from("push_subs").update({ last_ok: now.toISOString(), fails: 0 }).in("id", uniq(okSubs));
  if (goneSubs.length) await db.from("push_subs").delete().in("id", uniq(goneSubs));
  for (const f of failSubs) await db.from("push_subs").update({ fails: f.fails }).eq("id", f.id);

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
        for (const r of list) okIds.push(r.id);
      } catch (e) { console.error("mail", String(e).slice(0, 200)); }
    }
  }
  // ajuns pe cel puțin un telefon: folosit în panou (timpul până la primul memento livrat)
  const del = uniq(okIds);
  for (let i = 0; i < del.length; i += 200) await db.from("reminders").update({ delivered: true }).in("id", del.slice(i, i + 200));
  if (del.length) await db.rpc("note_delivered", { p_users: uniq(due.filter((r) => del.includes(r.id)).map((r) => r.user_id)) });
  return json({ ok: true, due: due.length, sent, gone, mailed });
});
