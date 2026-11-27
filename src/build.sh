#!/bin/bash
set -e
cd /tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad/
cat q1.html q2.html q3a.html q3b.html q3c.html q4a1.html q4a2.html q4b.html q4c.html q5a.html q5a2.html q5c.html q5d.html q5e.html q5f.html q5g.html q5h.html q5i.html q5j.html q7w.html q7s.html q7a.html q7p.html q7c.html q7f.html q7l.html q7x.html q7y.html q6.html q6d.html q5b.html > new.html
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
cp new.html /mnt/user-data/outputs/buzunar.html
echo built $(wc -c < new.html) bytes
