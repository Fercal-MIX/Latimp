// LaTimp: „Lângă mine” — parcuri, locuri de joacă, muzee, cinematografe, teatre, piscine și altele din OpenStreetMap.
// Primește doar o poziție rotunjită (aprox. 1 km); nu știe cine întreabă. Rezultatele se păstrează 7 zile pe zonă.
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (b: unknown, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { ...CORS, "Content-Type": "application/json" } });
const EP = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter", "https://overpass-api.de/api/interpreter"];
type Tags = Record<string, string>;
const cat = (t: Tags): string | null => {
  if (t.leisure === "playground") return "play";
  if (t.leisure === "park" || t.leisure === "garden") return "park";
  if (t.tourism === "museum" || t.tourism === "gallery") return "museum";
  if (t.amenity === "cinema") return "cinema";
  if (t.amenity === "theatre") return "theatre";
  if (t.tourism === "zoo" || t.leisure === "water_park") return "zoo";
  if (t.leisure === "swimming_pool" || t.leisure === "sports_centre") return "pool";
  if (t.tourism === "viewpoint") return "view";
  if (t.amenity === "library") return "library";
  return null;
};
const R = (m: number) => m;
const q = (la: number, lo: number) => {
  const a = (r: number) => `(around:${R(r)},${la},${lo})`;
  return `[out:json][timeout:25];(` +
    `nwr["leisure"="park"]["name"]${a(3000)};nwr["leisure"="garden"]["name"]["access"!~"private"]${a(3000)};` +
    `nwr["leisure"="playground"]${a(1500)};` +
    `nwr["tourism"~"^(museum|gallery)$"]["name"]${a(6000)};` +
    `nwr["amenity"~"^(cinema|theatre)$"]["name"]${a(6000)};` +
    `nwr["tourism"="zoo"]["name"]${a(15000)};nwr["leisure"="water_park"]["name"]${a(15000)};` +
    `nwr["leisure"="swimming_pool"]["name"]["access"!~"private|customers|no"]${a(6000)};` +
    `nwr["leisure"="sports_centre"]["sport"~"swimming"]["name"]${a(6000)};` +
    `nwr["tourism"="viewpoint"]["name"]${a(8000)};nwr["amenity"="library"]["name"]${a(3000)};` +
    `);out center tags 400;`;
};
const dist = (a: number, b: number, c: number, d: number) => {
  const r = Math.PI / 180, x = (d - b) * r * Math.cos(((a + c) / 2) * r), y = (c - a) * r;
  return Math.round(Math.sqrt(x * x + y * y) * 6371000);
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ err: "method" }, 405);
  let b: { lat?: number; lon?: number };
  try { b = await req.json(); } catch { return json({ err: "body" }, 400); }
  const lat = Number(b.lat), lon = Number(b.lon);
  if (!isFinite(lat) || !isFinite(lon) || Math.abs(lat) > 85 || Math.abs(lon) > 180) return json({ err: "pos" }, 400);
  const la = Math.round(lat * 100) / 100, lo = Math.round(lon * 100) / 100, area = `${la.toFixed(2)},${lo.toFixed(2)}`;
  const url = Deno.env.get("SUPABASE_URL"), sk = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !sk) return json({ err: "config" }, 500);
  const db = createClient(url, sk, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data: hit } = await db.rpc("near_get", { p_area: area });
  if (hit) return json({ ...hit, cached: true });

  let raw: { elements?: { tags?: Tags; lat?: number; lon?: number; center?: { lat: number; lon: number }; id: number; type: string }[] } | null = null;
  for (let i = 0; i < EP.length; i++) {
    const ep = EP[i];
    if (i) await new Promise((r) => setTimeout(r, 1500 * i));
    try {
      const r = await fetch(ep, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json", "User-Agent": "LaTimp/1.0 (+https://github.com/Fercal-MIX/Latimp)", "Referer": "https://fercal-mix.github.io/Latimp/" },
        body: "data=" + encodeURIComponent(q(la, lo)),
        signal: AbortSignal.timeout(35000),
      });
      if (r.ok) { raw = await r.json(); break; }
      console.error("overpass", ep, r.status);
    } catch (e) { console.error("overpass", ep, String(e).slice(0, 120)); }
  }
  if (!raw) return json({ err: "upstream" }, 502);

  const seen = new Set<string>();
  const items = (raw.elements || []).map((e) => {
    const t = e.tags || {}, c = cat(t), p = e.center || (e.lat != null ? { lat: e.lat!, lon: e.lon! } : null);
    if (!c || !p) return null;
    const n = (t["name:ro"] || t.name || (c === "play" ? "Loc de joacă" : "")).trim().slice(0, 80);
    if (!n) return null;
    const w = /^https:\/\//.test(t.website || "") ? t.website.slice(0, 200) : "";
    return { n, c, la: Math.round(p.lat * 1e5) / 1e5, lo: Math.round(p.lon * 1e5) / 1e5, m: dist(la, lo, p.lat, p.lon), w, o: (t.opening_hours || "").slice(0, 80) };
  }).filter((x): x is NonNullable<typeof x> => {
    if (!x) return false;
    const k = x.c + "|" + x.n.toLowerCase() + "|" + Math.round(x.la * 500) + "," + Math.round(x.lo * 500);
    if (seen.has(k)) return false; seen.add(k); return true;
  }).sort((a, b) => a.m - b.m);
  const per: Record<string, number> = {};
  const out = items.filter((x) => (per[x.c] = (per[x.c] || 0) + 1) <= (x.c === "play" ? 8 : 12));
  const data = { at: new Date().toISOString(), area, items: out };
  await db.rpc("near_put", { p_area: area, p_data: data });
  return json(data);
});
