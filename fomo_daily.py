#!/usr/bin/env python3
"""Box-only: roll ~/.local/share/fomo/events.jsonl into permanent daily FOMO summaries (UTC+7 days).
data/history/fomo_daily.json + .csv. Idempotent: a day is recomputed from raw events while they exist (8-day retention);
a stored day is only replaced by a recomputation with >= as many events, so pruned days stay frozen."""
import json,os,statistics,datetime as dt,csv
D=os.path.dirname(os.path.abspath(__file__)); OUT=f'{D}/data/history/fomo_daily.json'; CSV=OUT[:-4]+'csv'
EV=os.path.expanduser('~/.local/share/fomo/events.jsonl'); TZ=dt.timezone(dt.timedelta(hours=7))
old={r['day']:r for r in (json.load(open(OUT)) if os.path.exists(OUT) else [])}
E={}
for l in open(EV):
    try: e=json.loads(l); E[e['id']]=e
    except Exception: pass
by={}
for e in E.values():
    if isinstance(e.get('ts'),(int,float)): by.setdefault(dt.datetime.fromtimestamp(e['ts']/1000,TZ).strftime('%F'),[]).append(e)
today=dt.datetime.now(TZ).strftime('%F')
def agg(es):
    b=[e for e in es if e['side']=='buy']; s=[e for e in es if e['side']=='sell']
    fu=[e['fill'] for e in b if isinstance(e.get('fill'),(int,float))]; pn=[e['pnl'] for e in s if isinstance(e.get('pnl'),(int,float))]
    return {'buys':len(b),'sells':len(s),'buy_usd':round(sum(fu)),'buy_usd_n':len(fu),
            'pnl_med':round(statistics.median(pn),1) if pn else None,'profit_share':round(sum(1 for x in pn if x>0)/len(pn),3) if pn else None}
for day,es in by.items():
    ts=sorted(e['ts'] for e in es); cov=round(min(24,(ts[-1]-ts[0])/3.6e6),1)
    r={'day':day,'n':len(es),'coverage_h':cov,'partial':day==today or cov<22,'all':agg(es),'solana':agg([e for e in es if e.get('chain')=='solana'])}
    if day not in old or r['n']>=old[day]['n']: old[day]=r
rows=[old[k] for k in sorted(old)]
json.dump(rows,open(OUT+'.tmp','w'),indent=0); os.replace(OUT+'.tmp',OUT)
K=['buys','sells','buy_usd','buy_usd_n','pnl_med','profit_share']
with open(CSV,'w',newline='') as f:
    w=csv.writer(f); w.writerow(['day','n','coverage_h','partial']+[f'{c}_{k}' for c in('all','solana') for k in K])
    for r in rows: w.writerow([r['day'],r['n'],r['coverage_h'],int(r['partial'])]+[r[c][k] for c in('all','solana') for k in K])
print('fomo_daily',len(rows),'days; last',rows[-1]['day'] if rows else None)
