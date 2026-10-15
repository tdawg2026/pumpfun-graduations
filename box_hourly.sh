#!/usr/bin/env bash
# Box-side hourly job: fetch pump.fun graduated coins (box IP isn't blocked), push data/pumpfun_raw.json, trigger update.yml.
# Needs env GITHUB_TOKEN (repo + actions:write). Usage: bash box_hourly.sh
set -uo pipefail
R=tdawg2026/pumpfun-graduations; cd "$(dirname "$0")"
die(){ echo "box_hourly FAILED: $*" >&2; exit 1; }
[ -n "${GITHUB_TOKEN:-}" ] || die "GITHUB_TOKEN not set"
URL="https://x-access-token:${GITHUB_TOKEN}@github.com/$R.git"
git pull -q --rebase "$URL" main >/dev/null 2>&1 || die "git pull --rebase failed"
python3 fetch.py --pump-only || die "pump.fun fetch (see above)"
git add data/pumpfun_raw.json
if git diff --cached --quiet; then echo "no change"; else
  git -c user.name=box -c user.email=box@localhost commit -qm "box pump.fun raw $(date -u +%FT%H:%MZ)" || die "commit failed"
  ok=; for i in 1 2 3 4 5; do
    git push -q "$URL" HEAD:main >/dev/null 2>&1 && { ok=1; break; }
    git pull -q --rebase -X theirs "$URL" main >/dev/null 2>&1; sleep $((i*3))
  done; [ -n "$ok" ] || die "git push failed after 5 tries"
fi
c=$(curl -s -o /dev/null -w '%{http_code}' -X POST -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$R/actions/workflows/update.yml/dispatches" -d '{"ref":"main"}')
[ "$c" = 204 ] || die "workflow_dispatch HTTP $c"
echo "box_hourly ok: pushed raw + dispatched update.yml"
