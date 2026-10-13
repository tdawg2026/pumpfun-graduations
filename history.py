"""Daily aggregate history (kept forever): data/history/daily.json (+ daily.csv).
Day = UTC+7 calendar day for pump.fun/GMGN metrics; DefiLlama series are UTC days (stored under the same date label).
src flags: llama = 'backfill' (DefiLlama history fetched retroactively) or 'observed'; pump = 'observed' (+ 'partial' for today)."""
import json,os,time,statistics,csv
D=os.path.dirname(os.path.abspath(__file__)); HP=f'{D}/data/history/daily.json'
TZ=7*3600
day=lambda t:time.strftime('%Y-%m-%d',time.gmtime(t+TZ))
uday=lambda t:time.strftime('%Y-%m-%d',time.gmtime(t))
med=lambda a:statistics.median(a) if a else None
def load(): return json.load(open(HP)) if os.path.exists(HP) else {}
def save(H):
    H=dict(sorted(H.items())); json.dump(H,open(HP,'w'),separators=(',',':'))
    keys=sorted({k for r in H.values() for k in r})
    with open(f'{D}/data/history/daily.csv','w',newline='') as f:
        w=csv.writer(f); w.writerow(['date']+keys)
        for d,r in H.items(): w.writerow([d]+[r.get(k,'') for k in keys])
def put_llama(H,LL,src):
    for ck in ('SOL','BSC','Robinhood'):
        c=LL.get(ck)
        if not c: continue
        for i,t in enumerate(c['days']):
            r=H.setdefault(uday(t),{})
            if r.get('src_llama')=='observed' and src=='backfill': continue
            r[f'lp_total_{ck}']=c['total'][i]
            for n,a in c['protos'].items(): r[f'lp_fee_{n}']=a[i]
            r['src_llama']=src
    B=LL.get('BOTS')
    if B:
        for n,p in B['protos'].items():
            for t,v in zip(p['days'],p['v']):
                r=H.setdefault(uday(t),{})
                if r.get('src_bots')=='observed' and src=='backfill': continue
                r[f'bot_fee_{n}']=v; r['src_bots']=src
        for d,r in H.items():
            vs=[r.get(f'bot_fee_{n}') for n in B['protos']]
            if all(v is not None for v in vs): r['bot_top3']=sum(vs)
def put_pump(H,rows,launch,lp,now):
    by={}
    for t in rows.values(): by.setdefault(day(t.get('grad') or t['created']),[]).append(t)
    oldest=min(by) if by else None
    fs=[t['first_seen'] for t in rows.values() if t.get('first_seen')]
    full=day(min(fs)-20*3600+86400) if fs else None  # first UTC+7 day fully covered by the collector
    for d,ts in by.items():
        if d==oldest and len(by)>1 and H.get(d,{}).get('src_pump')=='observed': continue  # retention edge day is incomplete; keep earlier stored value
        r=H.setdefault(d,{}); A=[t.get('ath_mcap') or 0 for t in ts]; G=[t['gm'] for t in ts if t.get('gm')]
        v=lambda g,k:g.get(k) if isinstance(g.get(k),(int,float)) else 0
        cl=lambda g:v(g,'top_10_holder_rate')<0.3 and v(g,'bundler_trader_amount_rate')<0.3 and v(g,'rat_trader_amount_rate')<0.3 and v(g,'top70_sniper_hold_rate')<0.3 and v(g,'dev_team_hold_rate')<0.1 and v(g,'rug_ratio')<0.3 and not g.get('is_wash_trading')
        r.update(pump_grads=len(ts),pump_ath1m_share=round(sum(a>1e6 for a in A)/len(A),4),pump_ath_med=round(med(A) or 0),
                 pump_holders_med=med([t['holders_now'] for t in ts if t.get('holders_now') is not None]),
                 pump_gmgn_n=len(G),pump_clean_share=round(sum(map(cl,G))/len(G),4) if len(G)>=10 else None,
                 pump_smart_share=round(sum(v(g,'smart_degen_count')>0 for g in G)/len(G),4) if len(G)>=10 else None,
                 src_pump='partial' if d==day(now) else ('incomplete' if full and d<full else 'observed'))
    for x in launch: H.setdefault(day(x['ts']),{}).setdefault('_l',[]).append(x['rate'])
    for lab,e in lp.items():
        for key,nm in (('grate','grad_rate'),('launch','launch_rate')):
            tmp={}
            for ts,val in e.get(key,[]): tmp.setdefault(day(ts),[]).append(val)
            for d,vals in tmp.items(): H.setdefault(d,{})[f'gmgn_{nm}_{lab}']=round(med(vals),2)
    for d,r in H.items():
        if '_l' in r: r['pump_launch_rate']=round(med(r.pop('_l')),1)
def score(series,i,win=3,base=30):
    vals=[v for v in series[max(0,i-win+1):i+1] if v is not None]; b=[v for v in series[max(0,i-win-base+1):i-win+1] if v]
    if len(vals)<win or len(b)<10: return None
    m=med(b); return round(max(0,min(100,50*(sum(vals)/len(vals))/m)),1) if m else None
def indices(H):
    ds=sorted(H); col=lambda k:[H[d].get(k) for d in ds]
    tot=[ (sum(v for v in x if v is not None) if x[0] is not None else None) for x in zip(*[col(f'lp_total_{c}') for c in ('SOL','BSC','Robinhood')])]  # chains not yet live count as 0
    bt=col('bot_top3'); ch={c:col(f'lp_total_{c}') for c in ('SOL','BSC','Robinhood')}
    PK=[('pump_grads',.30),('pump_launch_rate',.10),('pump_ath1m_share',.20),('pump_ath_med',.15),('pump_clean_share',.15),('pump_smart_share',.10)]
    for i,d in enumerate(ds):
        r=H[d]; r['idx_launchpad']=score(tot,i); r['idx_bots']=score(bt,i)
        for c in ch: r[f'idx_fee_{c}']=score(ch[c],i)
        # pump.fun daily index: each metric vs median of prior 7 recorded days (needs >=3)
        s=w=0
        for k,wt in PK:
            prev=[H[x].get(k) for x in ds[max(0,i-7):i] if H[x].get(k) and H[x].get('src_pump')=='observed']
            if r.get(k) is None or len(prev)<3: continue
            s+=wt*max(0,min(100,50*r[k]/med(prev))); w+=wt
        r['idx_pump']=round(s/w,1) if w else None
        r['idx_SOL']=round(0.5*r['idx_fee_SOL']+0.5*r['idx_pump'],1) if r['idx_fee_SOL'] is not None and r['idx_pump'] is not None else r['idx_fee_SOL']
        for c in ('BSC','Robinhood'): r[f'idx_{c}']=r[f'idx_fee_{c}']
        parts=[(r['idx_launchpad'],.30),(r['idx_bots'],.25),(r['idx_pump'],.45)]; parts=[p for p in parts if p[0] is not None]
        r['idx_combined']=round(sum(a*b for a,b in parts)/sum(b for _,b in parts),1) if parts else None
def update(LL,rows,launch,lp,now):
    H=load()
    if LL: put_llama(H,LL,'observed')
    put_pump(H,rows,launch,lp,now); indices(H); save(H); return H
if __name__=='__main__':  # one-time backfill of DefiLlama full history
    import llama
    LL={**llama.fetch(days=100000),'BOTS':llama.bots(days=100000)}
    H=load(); put_llama(H,LL,'backfill')
    db=json.load(open(f'{D}/data/tokens.json')); L=json.load(open(f'{D}/data/launches.json')); K=json.load(open(f'{D}/data/launchpads.json'))
    put_pump(H,db,L,K,int(time.time())); indices(H); save(H)
    print('days',len(H),min(H),max(H),os.path.getsize(HP),'bytes')
