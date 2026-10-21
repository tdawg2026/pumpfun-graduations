#!/usr/bin/env python3
"""Box-only hourly aggregation of FOMO whale alerts -> data/fomo_flow.json (committed; no secrets).
Fallback: if the WS collector wrote nothing in the last hour, poll /v2/alerts once (125 credits).
Daily (once per UTC day): /v2/leaderboard/24h (250 credits) -> aggregate PnL stats. Credits logged to ~/.local/share/fomo/credits.log.
Sentiment slot: idx = clip(50 * buy_count_24h / median(buy_count_24h over previous 7 days of hourly snapshots)); null until >=3 days of history."""
import json,os,time,urllib.request,statistics
from fomo_common import norm
D=os.path.dirname(os.path.abspath(__file__)); OUT=f'{D}/data/fomo_flow.json'
S=os.path.expanduser('~/.local/share/fomo'); os.makedirs(S,exist_ok=True); EV=f'{S}/events.jsonl'
KEY=open(os.path.expanduser('~/.config/fomoapi_key')).read().strip()
now=int(time.time()); F=json.load(open(OUT)) if os.path.exists(OUT) else {'hist':[],'lb':[]}
def api(path):
    r=urllib.request.urlopen(urllib.request.Request('https://api.fomoapi.io'+path,headers={'authorization':'Bearer '+KEY,'User-Agent':'pumpfun-graduations'}),timeout=60)
    cost=r.headers.get('x-credits-cost'); rem=r.headers.get('x-credits-remaining'); body=json.load(r)
    open(f'{S}/credits.log','a').write(f'{time.strftime("%FT%T%z")} {path.split("?")[0]} cost={cost} remaining={rem}\n')
    F['credits']={'remaining':int(rem) if rem and rem.isdigit() else rem,'at':now}; return body
E={}
if os.path.exists(EV):
    for l in open(EV):
        try: e=json.loads(l); E[e['id']]=e
        except Exception: pass
src='ws'
hb=int(open(f'{S}/heartbeat').read()) if os.path.exists(f'{S}/heartbeat') else 0
if now-hb>3600:  # collector dead/stalled -> REST fallback, <=1 call/hour
    src='rest'
    try:
        r=api('/v2/alerts?limit=500')
        with open(EV,'a') as f:
            for d in r.get('alerts') or []:
                e=norm(d)
                if e and e['id'] not in E: E[e['id']]=e; f.write(json.dumps(e)+'\n')
    except Exception as ex: print('fomo rest fallback failed',type(ex).__name__); src='none'
ev=[e for e in E.values() if isinstance(e.get('ts'),(int,float)) and e['ts']>=(now-86400)*1000]
def agg(es):
    b=[e for e in es if e['side']=='buy']; s=[e for e in es if e['side']=='sell']
    bu=sum(e.get('pos') or 0 for e in b); pn=[e['pnl'] for e in s if isinstance(e.get('pnl'),(int,float))]
    return {'buys':len(b),'sells':len(s),'net_count':len(b)-len(s),'ratio':round(len(b)/len(s),3) if s else None,'buy_usd':round(bu),
            'sell_pnl':round(sum(pn)),'sell_win':round(sum(1 for x in pn if x>0)/len(pn),3) if pn else None,
            'buyers':len({e['user'] for e in b if e.get('user')}),'sellers':len({e['user'] for e in s if e.get('user')})}
cov=min(24.0,(now-min([e['ts'] for e in E.values() if isinstance(e.get('ts'),(int,float))],default=now*1000)/1000)/3600)
chains={'all':agg(ev),'solana':agg([e for e in ev if e.get('chain')=='solana'])}
top={}
for e in ev: top[e.get('chain') or '?']=top.get(e.get('chain') or '?',0)+1
H=[h for h in F.get('hist',[]) if h[0]>=now-30*86400 and h[0]<now-1800]
prev=[h[1] for h in H if now-7*86400<=h[0]<now-3600 and h[5]>=23]
base=statistics.median(prev) if len(prev)>=72 else None
idx=round(max(0,min(100,50*chains['all']['buys']/base)),1) if base else None
# hist row: [ts, all buys, all buy_usd(position), all sells, all buyers, coverage_hours, sol buys, sol sells]
H.append([now,chains['all']['buys'],chains['all']['buy_usd'],chains['all']['sells'],chains['all']['buyers'],round(cov,1),chains['solana']['buys'],chains['solana']['sells']])
# daily leaderboard
LB=F.get('lb',[]); day=time.strftime('%F',time.gmtime(now))
if not LB or LB[-1]['day']!=day:
    try:
        r=api('/v2/leaderboard/24h'); p=[t['pnlUsd'] for t in r.get('traders',[]) if isinstance(t.get('pnlUsd'),(int,float))]
        if p: LB.append({'day':day,'n':len(p),'median_pnl':statistics.median(p),'profit_share':round(sum(1 for x in p if x>0)/len(p),3),'total_pnl':round(sum(p)),'captured':r.get('capturedAt')})
    except Exception as ex: print('fomo leaderboard failed',type(ex).__name__)
LB=LB[-90:]
F.update(updated=now,source=src,coverage_h=round(cov,1),window='24h',chains=chains,chain_n={k:round(v) for k,v in sorted(top.items(),key=lambda x:-x[1])[:6]},
         idx=idx,base_buys=round(base) if base else None,base_n=len(prev),hist=H,lb=LB,
         note='FOMO 平台 (fomo.family) app feed only, via unofficial fomoapi.io; LARGE_* alerts (~$3K+ position value); buy USD = post-buy position value (fill size not published); sells carry realized PnL, not size, so USD net flow is not available - net = buy count minus sell count')
json.dump(F,open(OUT+'.tmp','w'),separators=(',',':')); os.replace(OUT+'.tmp',OUT)
print('fomo',src,'24h',chains['all'],'cov_h',round(cov,1),'idx',idx,'credits',F.get('credits',{}).get('remaining'))
