"""Post-graduation performance tracking (kept forever): data/perf.json.
Per token: checkpoints +1h/+6h/+24h/+7d from GeckoTerminal hourly OHLCV (USD, base token; mcap = price x 1e9 supply).
cp[k] = [mcap, return vs graduation price, max drawdown from running peak, alive(0/1), liquidity USD or null]
Completed checkpoints are never refetched. Liquidity = GeckoTerminal reserve_in_usd, only recorded when the
checkpoint is filled within 2h of being due (otherwise null, since only the current pool reserve is available).
SAMPLED: only SPH tokens per graduation hour (lowest md5(mint) in that hour = deterministic random sample) get
checkpoints/liquidity; e["smp"]=1 marks them. ~1000 grads/day cannot all be fetched within GeckoTerminal free limits."""
import json,os,time,urllib.request,urllib.error,hashlib
D=os.path.dirname(os.path.abspath(__file__)); PP=f'{D}/data/perf.json'
SPH=3  # sampled tokens per graduation hour (~72/day)
CP=[('1h',3600),('6h',6*3600),('24h',86400),('7d',7*86400)]
GT='https://api.geckoterminal.com/api/v2/networks/solana/pools/'
def get(u):
    for i in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'}),timeout=30))
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(30); continue
            if e.code==404: return None
        except Exception: pass
        time.sleep(3)
    return None
def load(): return json.load(open(PP)) if os.path.exists(PP) else {}
def clean(gm):
    if not gm: return None
    v=lambda k:gm.get(k) if isinstance(gm.get(k),(int,float)) else 0
    return int(v('top_10_holder_rate')<0.3 and v('bundler_trader_amount_rate')<0.3 and v('rat_trader_amount_rate')<0.3 and v('top70_sniper_hold_rate')<0.3
               and v('dev_team_hold_rate')<0.1 and v('rug_ratio')<0.3 and not gm.get('is_wash_trading'))
def update(db,now,budget=480,maxcalls=200):
    P=load(); t0=time.time(); calls=0
    for m,t in db.items():
        if not t.get('pool') or not t.get('grad'): continue
        e=P.setdefault(m,{'s':t.get('symbol'),'p':t['pool'],'g':t['grad'],'cp':{}})
        e['c']=clean(t.get('gm')); e['sm']=int((t.get('gm') or {}).get('smart_degen_count') or 0)>0 if t.get('gm') else None
        if t.get('ath_mcap'):
            # pump.fun ATH incl. bonding curve; if it happened before graduation it is the pre-grad ATH
            if (t.get('ath_ts') or 0)<=t['grad']+120: e['pre']=round(t['ath_mcap'])
            else: e['ath_pf']=round(t['ath_mcap'])
        if t.get('mcap'): e['now']=round(t['mcap'])
    B={}
    for m,e in P.items(): B.setdefault(e['g']//3600,[]).append(m)
    for ms in B.values():
        ms.sort(key=lambda m:hashlib.md5(m.encode()).hexdigest())
        for i,m in enumerate(ms):
            if i<SPH: P[m]['smp']=1
            else: P[m].pop('smp',None)
    # current liquidity for recent pools (<=8d), 30 per call
    def soon(e):
        if e['g']>=now-24*3600: return True
        return any(k not in e['cp'] and -3600<=now-(e['g']+s)<=7200 for k,s in CP)
    live=[e for e in P.values() if e.get('smp') and e['g']>=now-8*86400 and soon(e)]
    for i in range(0,len(live),30):
        b=live[i:i+30]; r=get(GT+'multi/'+','.join(e['p'] for e in b)); calls+=1
        a={p['attributes']['address']:p['attributes'] for p in (r or {}).get('data',[])}
        for e in b:
            x=a.get(e['p'])
            if x:
                e['liq']=round(float(x['reserve_in_usd'] or 0)); e['liq_at']=now
                if x.get('fdv_usd'): e['now']=round(float(x['fdv_usd']))
        time.sleep(2.1)
    # checkpoints due & missing; freshest-due first (so liquidity can be captured), then backlog
    due=[]
    for m,e in P.items():
        if not e.get('smp'): continue
        miss=[(k,s) for k,s in CP if k not in e['cp'] and now>=e['g']+s]
        if miss and e.get('miss',0)<3: due.append((now-(e['g']+miss[0][1])>7200,-e['g'],m,miss))
    due.sort(); t0=time.time(); calls=0  # checkpoints get their own budget
    done=0
    for late,_,m,miss in due:
        if time.time()-t0>budget or calls>=maxcalls: break
        e=P[m]; end=min(now,e['g']+7*86400+3600); n=int((end-e['g'])//3600)+3
        r=get(f"{GT}{e['p']}/ohlcv/hour?aggregate=1&limit={min(1000,n)}&currency=usd&token=base&before_timestamp={end}"); calls+=1
        L=sorted((r or {}).get('data',{}).get('attributes',{}).get('ohlcv_list',[]) if r else [])
        L=[c for c in L if c[0]+3600>e['g']]
        if not L: e['miss']=e.get('miss',0)+1; time.sleep(2.1); continue
        p0=L[0][1]; e['g0']=round(p0*1e9)
        for k,s in miss:
            x=[c for c in L if c[0]<e['g']+s]
            if not x: continue
            c=x[-1]; peak=p0; mdd=0
            for cc in x: peak=max(peak,cc[2]); mdd=max(mdd,1-cc[3]/peak if peak else 0)
            ago=e['g']+s-c[0]  # seconds since last traded candle start
            mc=c[4]*1e9; alive=int(mc>=10000 and ago<=max(7200,s*0.25))
            liq=e.get('liq') if (not late and e.get('liq_at',0)>=now-600) else None
            e['cp'][k]=[round(mc),round(c[4]/p0-1,4),round(mdd,4),alive,liq]
        hi=max(c[2] for c in L)*1e9; e['post']=round(max(hi,e.get('ath_pf',0)))
        done+=1; time.sleep(2.1)
    json.dump(P,open(PP+'.tmp','w'),separators=(',',':')); os.replace(PP+'.tmp',PP)
    print('perf tokens',len(P),'sampled',sum(1 for e in P.values() if e.get('smp')),'due',len(due),'filled',done,'gecko calls',calls)
    return P
if __name__=='__main__':
    import sys
    db=json.load(open(f'{D}/data/tokens.json'))
    update(db,int(time.time()),budget=int(sys.argv[1]) if len(sys.argv)>1 else 600,maxcalls=int(sys.argv[2]) if len(sys.argv)>2 else 250)
