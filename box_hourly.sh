#!/usr/bin/env bash
# Box-side hourly job: fetch pump.fun graduated coins (box IP isn't blocked), push data/pumpfun_raw.json, trigger update.yml.
# Needs env GITHUB_TOKEN (repo + actions:write). Usage: bash box_hourly.sh
set -uo pipefail
R=tdawg2026/pumpfun-graduations; cd "$(dirname "$0")"
die(){ echo "box_hourly FAILED: $*" >&2; exit 1; }
retry(){ local n=$1; shift; local i; for i in $(seq "$n"); do "$@" && return 0; [ "$i" -lt "$n" ] && sleep $((i*i*5)); done; return 1; }  # backoff 5,20,45,80s
export GIT_HTTP_LOW_SPEED_LIMIT=1000 GIT_HTTP_LOW_SPEED_TIME=30
pull(){ git pull -q --rebase "$URL" main >/dev/null 2>&1 || { git rebase --abort >/dev/null 2>&1; return 1; }; }
dispatch(){ c=$(curl -s -m 30 -o /dev/null -w '%{http_code}' -X POST -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$R/actions/workflows/update.yml/dispatches" -d '{"ref":"main"}'); [ "$c" = 204 ]; }
[ -n "${GITHUB_TOKEN:-}" ] || die "GITHUB_TOKEN not set"
URL="https://x-access-token:${GITHUB_TOKEN}@github.com/$R.git"
retry 5 pull || die "git pull --rebase failed after 5 tries (network?)"
python3 fetch.py --pump-only || die "pump.fun fetch (see above)"
# FOMO whale-alert collector watchdog (long-running WS process; 0 credits) + hourly aggregate
FD=$HOME/.local/share/fomo; mkdir -p "$FD"
hb=$(cat "$FD/heartbeat" 2>/dev/null || echo 0)
if ! pgrep -f "python3 .*fomo_ws.py" >/dev/null || [ $(( $(date +%s) - hb )) -gt 900 ]; then
  pkill -f "python3 .*fomo_ws.py"; echo "fomo_ws (re)started"; (setsid nohup python3 "$PWD/fomo_ws.py" >> "$FD/ws.log" 2>&1 &)
fi
[ -s "$HOME/.config/fomoapi_key" ] && { python3 fomo_agg.py || echo "WARNING fomo_agg failed (continuing)"; }
git add data/pumpfun_raw.json data/fomo_flow.json
if git diff --cached --quiet; then echo "no change"; else
  git -c user.name=box -c user.email=box@localhost commit -qm "box pump.fun raw $(date -u +%FT%H:%MZ)" || die "commit failed"
  ok=; for i in 1 2 3 4 5; do
    git push -q "$URL" HEAD:main >/dev/null 2>&1 && { ok=1; break; }
    sleep $((i*i*5)); git pull -q --rebase -X theirs "$URL" main >/dev/null 2>&1 || git rebase --abort >/dev/null 2>&1
  done; [ -n "$ok" ] || die "git push failed after 5 tries"
fi
retry 5 dispatch || die "workflow_dispatch failed after 5 tries (last HTTP $c)"
echo "box_hourly ok: pushed raw + dispatched update.yml"
