// LaTimp: „Lângă mine” — parcuri, locuri de joacă, muzee, cinematografe, teatre, piscine și altele din OpenStreetMap.
// Rezerva pentru telefon: primește doar o poziție rotunjită (aprox. 1 km), nu știe cine întreabă; rezultatele se păstrează 7 zile pe zonă.
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (b: unknown, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { ...CORS, "Content-Type": "application/json" } });
const GROUPS = [["leisure:park", "leisure:garden", "leisure:playground"], ["tourism:museum", "tourism:gallery", "amenity:cinema", "amenity:theatre", "tourism:zoo", "leisure:water_park", "leisure:swimming_pool", "tourism:viewpoint", "amenity:library"]];
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

  // Photon (komoot), date OpenStreetMap: două cereri, locurile cele mai apropiate de poziția rotunjită.
  const raw: { elements: { tags: Tags; lat: number; lon: number }[] } = { elements: [] };
  let okCalls = 0;
  for (const tags of GROUPS) {
    try {
      const u = `https://photon.komoot.io/reverse?lat=${la}&lon=${lo}&radius=4&limit=40&` + tags.map((t) => "osm_tag=" + encodeURIComponent(t)).join("&");
      const r = await fetch(u, { headers: { "User-Agent": "LaTimp/1.0 (+https://github.com/Fercal-MIX/Latimp)", "Accept": "application/json" }, signal: AbortSignal.timeout(12000) });
      if (r.ok) {
        okCalls++;
        const j = await r.json() as { features?: { properties?: Record<string, string>; geometry?: { coordinates?: number[] } }[] };
        for (const f of j.features || []) {
          const p = f.properties || {}, g = f.geometry?.coordinates;
          if (!g || g.length < 2 || !p.osm_key) continue;
          const t: Tags = { [p.osm_key]: String(p.osm_value || "") };
          if (p.name) t.name = p.name;
          raw.elements.push({ tags: t, lat: Number(g[1]), lon: Number(g[0]) });
        }
      } else console.error("photon", r.status);
    } catch (e) { console.error("photon", String(e).slice(0, 120)); }
  }
  if (!okCalls) return json({ err: "upstream" }, 502);

  const seen = new Set<string>();
  const items = (raw.elements || []).map((e) => {
    const t = e.tags || {}, c = cat(t), p = isFinite(e.lat) && isFinite(e.lon) ? { lat: e.lat, lon: e.lon } : null;
    if (!c || !p) return null;
    if (t.leisure === "sports_centre" && !/swim/.test(t.sport || "")) return null;
    if ((t.leisure === "garden" || t.leisure === "swimming_pool") && /^(private|customers|no)$/.test(t.access || "")) return null;
    if (c !== "play" && !t.name && !t["name:ro"]) return null;
    const n = (t["name:ro"] || t.name || (c === "play" ? "Loc de joacă" : "")).trim().slice(0, 80);
    if (!n) return null;
    const w = /^https:\/\//.test(t.website || "") ? t.website.slice(0, 200) : "";
    return { n, c, la: Math.round(p.lat * 1e5) / 1e5, lo: Math.round(p.lon * 1e5) / 1e5, m: dist(la, lo, p.lat, p.lon), w, o: (t.opening_hours || "").slice(0, 80) };
  }).filter((x): x is NonNullable<typeof x> => {
    if (!x || x.m > 4000) return false;
    const k = x.c + "|" + x.n.toLowerCase() + "|" + Math.round(x.la * 500) + "," + Math.round(x.lo * 500);
    if (seen.has(k)) return false; seen.add(k); return true;
  }).sort((a, b) => a.m - b.m);
  const per: Record<string, number> = {};
  const out = items.filter((x) => (per[x.c] = (per[x.c] || 0) + 1) <= (x.c === "play" ? 8 : 12));
  const data = { at: new Date().toISOString(), area, items: out };
  if (out.length) await db.rpc("near_put", { p_area: area, p_data: data });
  return json(data);
});
