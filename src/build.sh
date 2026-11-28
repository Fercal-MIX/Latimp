#!/bin/bash
set -e
# merge din dosarul lui (în depozit: src/, cu părțile în src/parts/)
D="$(cd "$(dirname "$0")" && pwd)"; cd "$D"
P=.; [ -d parts ] && [ ! -f q1.html ] && P=parts
cat $P/q1.html $P/q2.html $P/q3a.html $P/q3b.html $P/q3c.html $P/q4a1.html $P/q4a2.html $P/q4b.html $P/q4c.html $P/q5a.html $P/q5a2.html $P/q5c.html $P/q5d.html $P/q5e.html $P/q5f.html $P/q5g.html $P/q5h.html $P/q5i.html $P/q5j.html $P/q7w.html $P/q7s.html $P/q7a.html $P/q7p.html $P/q7c.html $P/q7f.html $P/q7l.html $P/q7x.html $P/q7y.html $P/q7z.html $P/q8a.html $P/q8b.html $P/q8c.html $P/q8d.html $P/q8e.html $P/q8f.html $P/q6.html $P/q6d.html $P/q5b.html > new.html
python3 - <<'PY'
import re,subprocess
s=open("new.html").read()
blocks=re.findall(r"<script>(.*?)</script>",s,re.S)
print("script blocks:",len(blocks))
for i,b in enumerate(blocks):
    open(f"blk{i}.js","w").write(b)
    r=subprocess.run(["node","--check",f"blk{i}.js"],capture_output=True,text=True)
    if r.returncode: print("SYNTAX ERR in block",i,r.stderr[:400]); raise SystemExit(1)
print("syntax ok")
PY
if [ -d /mnt/user-data/outputs ]; then cp new.html /mnt/user-data/outputs/buzunar.html; fi
echo built $(wc -c < new.html) bytes
