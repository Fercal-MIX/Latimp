# Pornirea comună a testelor: verificările, serverul local cu versiunea web și serverul Supabase simulat.
import subprocess, time
SC = "/tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/"
FAKE = open(SC + "fake_sb.js").read()
ok = []; bad = []
def chk(n, c, e=""): (ok if c else bad).append(n + (" -> " + str(e)[:300] if (e and not c) else ""))
def serve(port):
    p = subprocess.Popen(["python3", "-m", "http.server", str(port), "-d", SC + "web"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1); return p
async def fake_route(c, fonts=False):
    async def h(r): await r.fulfill(status=200, content_type="application/javascript", body=FAKE)
    await c.route("**/cdn.jsdelivr.net/**", h)
    if fonts: await c.route("**/fonts.googleapis.com/**", lambda r: r.abort())
def done():
    print("OK", len(ok), "FAIL", len(bad))
    for x in bad: print(" -", x)
