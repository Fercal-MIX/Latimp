cd /tmp/claude-0/-home-claude/47db69b0-b487-5d18-a3d6-1f2f98c3be6e/scratchpad
for i in "$@"; do r=$(timeout 400 python3 t$i.py 2>&1); echo "t$i: $(echo "$r" | grep -E '^(OK|FAIL) ' | tr '\n' ' ') $(echo "$r" | grep -E '^ - |Error' | head -3 | tr '\n' ' ' | cut -c1-300)"; done
