// LaTimp: ștergerea contului cerută de utilizator (GDPR, regulile magazinelor).
// Verifică utilizatorul din tokenul lui, refuză dacă are abonament activ cu reînnoire (în magazin sau pe web),
// șterge fișierele lui din Storage, apoi contul (tabelele se șterg în cascadă; plățile și retragerile rămân, fără legătură cu contul).
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (b: unknown, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { ...CORS, "Content-Type": "application/json" } });

async function removeFolder(admin: ReturnType<typeof createClient>, bucket: string, prefix: string) {
  let removed = 0;
  for (let round = 0; round < 20; round++) {
    const { data, error } = await admin.storage.from(bucket).list(prefix, { limit: 1000 });
    if (error || !data || !data.length) break;
    const files = data.filter((f) => f.id).map((f) => `${prefix}/${f.name}`);
    const dirs = data.filter((f) => !f.id).map((f) => `${prefix}/${f.name}`);
    for (const d of dirs) removed += await removeFolder(admin, bucket, d);
    if (!files.length) break;
    const { error: re } = await admin.storage.from(bucket).remove(files);
    if (re) break;
    removed += files.length;
  }
  return removed;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "method" }, 405);
  const url = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) return json({ error: "config" }, 500);
  const token = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  if (!token) return json({ error: "unauthorized" }, 401);
  const admin = createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data: ud, error: ue } = await admin.auth.getUser(token);
  const user = ud?.user;
  if (ue || !user) return json({ error: "unauthorized" }, 401);

  // un abonament care se reînnoiește ar continua să fie plătit după ștergere: întâi se anulează reînnoirea
  const { data: ent } = await admin.from("entitlements").select("pro_until,auto_renew,store").eq("user_id", user.id).maybeSingle();
  if (ent && ent.auto_renew && ent.pro_until && new Date(ent.pro_until) > new Date()) {
    if (ent.store === "apple" || ent.store === "google") return json({ error: "active_subscription" }, 409);
    if (ent.store === "web") return json({ error: "active_subscription_web" }, 409);
  }

  let files = 0;
  for (const b of ["attachments", "report-shots"]) files += await removeFolder(admin, b, user.id);

  try { await admin.auth.admin.signOut(token, "global"); } catch (_) { /* tokenul poate fi deja invalid */ }
  const { error: de } = await admin.auth.admin.deleteUser(user.id);
  if (de) return json({ error: "delete_failed" }, 500);
  return json({ ok: true, files });
});
