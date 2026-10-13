#!/usr/bin/env python3
"""Incremental pump.fun graduation collector. Sources: pump.fun frontend-api-v3 (graduated list, ATH/current mcap),
GeckoTerminal pools/multi (PumpSwap pool_created_at = graduation time). Stores data/tokens.json."""
import json,time,urllib.request,os,subprocess
D=os.path.dirname(os.path.abspath(__file__)); DB=f'{D}/data/tokens.json'
PF='https://frontend-api-v3.pump.fun/coins?offset={o}&limit=50&sort={s}&order=DESC&includeNsfw=true&complete=true'
GT='https://api.geckoterminal.com/api/v2/networks/solana/pools/multi/'
calls={'pump':0,'gecko':0}
def get(u,k):
    calls[k]+=1
    if k=='pump':
        for i in range(5):
            p=subprocess.run(['curl','-s','-m','30','-w','\n%{http_code}',u],capture_output=True,text=True)
            body,_,code=p.stdout.rpartition('\n')
            if code=='200': return json.loads(body)
            time.sleep(5*(i+1))
        raise SystemExit(f'pump.fun failed HTTP {code}')
    for i in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'}),timeout=30))
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(20); continue
            if i==3: raise
        except Exception:
            if i==3: raise
        time.sleep(3)
db=json.load(open(DB)) if os.path.exists(DB) else {}
now=int(time.time())
for s in ('created_timestamp','last_trade_timestamp'):
    for o in range(0,1000,50):
        rows=get(PF.format(o=o,s=s),'pump') or []
        for c in rows:
            if not c.get('complete'): continue
            m=c['mint']; t=db.setdefault(m,{'mint':m,'first_seen':now})
            t.update(name=c.get('name'),symbol=c.get('symbol'),pool=c.get('pump_swap_pool') or c.get('pool_address'),
                created=c['created_timestamp']//1000,ath_mcap=c.get('ath_market_cap'),
                ath_ts=(c.get('ath_market_cap_timestamp') or 0)//1000 or None,
                mcap=c.get('usd_market_cap'),tprog=c.get('token_program'),updated=now,source='pump.fun v3')
        if len(rows)<50: break
        time.sleep(1)
# graduation time via GeckoTerminal (only tokens missing it), 30 pools/call, <=28 calls/min
need=[t for t in db.values() if t.get('pool') and not t.get('grad') and not t.get('gt_miss',0)>=3]
for i in range(0,len(need),30):
    b=need[i:i+30]; r=get(GT+','.join(t['pool'] for t in b),'gecko') or {}
    got={p['attributes']['address']:p['attributes'] for p in r.get('data',[])}
    for t in b:
        a=got.get(t['pool'])
        if a and a.get('pool_created_at'):
            t['grad']=int(time.mktime(time.strptime(a['pool_created_at'],'%Y-%m-%dT%H:%M:%SZ')))-time.timezone
            t['gt_fdv']=float(a['fdv_usd']) if a.get('fdv_usd') else None
        else: t['gt_miss']=t.get('gt_miss',0)+1
    time.sleep(2.2)
# holders. Tiered refresh to stay in Helius free tier (~1M credits/month):
# graduated <6h: every run; 6-24h: every 2h; 1-7d: every 24h (dead tokens: holders_now<50 -> every 48h).
import holders as HL
calls['rpc']=0
def due(t):
    age=now-(t.get('grad') or t['created']); last=t.get('holders_at') or 0
    iv=3000 if age<6*3600 else 2*3600-600 if age<86400 else 86400-600
    if age>=86400 and (t.get('holders_now') or 0)<50 and last: iv=2*86400-600
    return now-last>=iv
order=sorted([t for t in db.values() if due(t)],key=lambda t:-(t.get('grad') or t['created']))
t0=time.time();fails=0;LIMIT=1600
for t in order[:LIMIT]:
    if time.time()-t0>900 or fails>=10:
        print('holders stopped early: fails',fails,'last',HL.LAST); break
    h=HL.holders(t['mint'],t.get('tprog') or HL.PROG['2022']); calls['rpc']+=1
    if h is None: fails+=1; continue
    fails=0
    t['holders_now']=h; t['holders_at']=now
    if h>=(t.get('holders_max') or -1): t['holders_max']=h; t['holders_max_at']=now
    time.sleep(0.12 if HL.KEY else 0.15)
print('holders due',len(order),'checked',calls['rpc'],'helius credits',HL.CREDITS,'mode','helius' if HL.KEY else 'public')
cut=now-7*86400
db={m:t for m,t in db.items() if (t.get('grad') or t['created'])>=cut}
json.dump(db,open(DB+'.tmp','w')); os.replace(DB+'.tmp',DB)
json.dump({'updated':now,'calls':calls,'n':len(db)},open(f'{D}/data/meta.json','w'))
print('tokens',len(db),'with grad time',sum(1 for t in db.values() if t.get('grad')),'calls',calls)
