// LaTimp: calendarul la care se abonează Google Calendar, calendarul de pe iPhone sau Outlook.
// Linkul conține un cod secret; aici se caută doar amprenta lui (SHA-256). Fără cont sau token de utilizator.
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const EMPTY = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//LaTimp//RO\r\nX-WR-CALNAME:LaTimp\r\nEND:VCALENDAR\r\n";
const hex = (b: ArrayBuffer) => Array.from(new Uint8Array(b), (x) => x.toString(16).padStart(2, "0")).join("");

Deno.serve(async (req) => {
  if (req.method !== "GET" && req.method !== "HEAD") return new Response("method", { status: 405 });
  const t = new URL(req.url).searchParams.get("t") || "";
  if (!/^[0-9a-f]{48}$/.test(t)) return new Response("not found", { status: 404 });
  const url = Deno.env.get("SUPABASE_URL"), sk = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !sk) return new Response("config", { status: 500 });
  const db = createClient(url, sk, { auth: { persistSession: false, autoRefreshToken: false } });
  const h = hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t)));
  const { data, error } = await db.from("calendar_feeds").select("user_id,ics,fetched_at").eq("token_hash", h).maybeSingle();
  if (error) return new Response("error", { status: 500 });
  if (!data) return new Response("not found", { status: 404 });
  const last = data.fetched_at ? Date.parse(data.fetched_at) : 0;
  if (Date.now() - last > 3600_000) await db.from("calendar_feeds").update({ fetched_at: new Date().toISOString() }).eq("user_id", data.user_id);
  return new Response(req.method === "HEAD" ? null : (data.ics || EMPTY), {
    headers: {
      "Content-Type": "text/calendar; charset=utf-8",
      "Content-Disposition": 'inline; filename="latimp.ics"',
      "Cache-Control": "private, max-age=900",
    },
  });
});
