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
OLD0=json.load(open(f'{D}/data/old.json')) if os.path.exists(f'{D}/data/old.json') else {}
for s in ('created_timestamp','last_trade_timestamp'):
    for o in range(0,1000,50):
        rows=get(PF.format(o=o,s=s),'pump') or []
        for c in rows:
            if not c.get('complete'): continue
            m=c['mint']
            if m in OLD0: continue
            t=db.setdefault(m,{'mint':m,'first_seen':now})
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
cut=now-7*86400
OP=f'{D}/data/old.json'; OLD=json.load(open(OP)) if os.path.exists(OP) else {}
for m,t in list(db.items()):
    if (t.get('grad') or t['created'])<cut: OLD[m]=now; del db[m]
OLD={m:x for m,x in OLD.items() if x>=now-14*86400}; json.dump(OLD,open(OP,'w'))
# holders: queried ONCE per token (only tokens without a value yet). Helius getProgramAccountsV2.
import holders as HL
calls['rpc']=0
for t in db.values(): t.pop('holders_max',None); t.pop('holders_max_at',None)
order=sorted([t for t in db.values() if t.get('holders_now') is None],key=lambda t:-(t.get('grad') or t['created']))
t0=time.time();fails=0;LIMIT=1600
for t in order[:LIMIT]:
    if time.time()-t0>900 or fails>=10:
        print('holders stopped early: fails',fails,'last',HL.LAST); break
    h=HL.holders(t['mint'],t.get('tprog') or HL.PROG['2022']); calls['rpc']+=1
    if h is None: fails+=1; continue
    fails=0
    t['holders_now']=h; t['holders_at']=now
    time.sleep(0.12 if HL.KEY else 0.15)
print('holders missing',len(order),'checked',calls['rpc'],'helius credits',HL.CREDITS,'mode','helius' if HL.KEY else 'public')
# GMGN quality snapshot (once per token) + launch-rate sample
import gmgn
G,err=gmgn.trenches(); calls['gmgn']=1
LP=f'{D}/data/launches.json'; L=json.load(open(LP)) if os.path.exists(LP) else []
if G:
    nc=[x['created_timestamp'] for x in G.get('new_creation',[]) if x.get('created_timestamp')]
    if len(nc)>=10 and max(nc)>min(nc): L.append({'ts':now,'rate':round((len(nc)-1)*3600/(max(nc)-min(nc)),1),'n':len(nc)})
    got=0
    for x in G.get('completed',[]):
        m=x['address']; t=db.get(m)
        if t is None:
            t=db[m]={'mint':m,'first_seen':now,'name':x.get('name'),'symbol':x.get('symbol'),'created':x.get('created_timestamp'),
                     'grad':x.get('complete_timestamp'),'mcap':x.get('usd_market_cap') and float(x['usd_market_cap']),'source':'gmgn'}
        if not t.get('grad') and x.get('complete_timestamp'): t['grad']=x['complete_timestamp']
        if 'gm' not in t:
            t['gm']={k:gmgn.num(x.get(k)) for k in gmgn.FIELDS if k in x}; t['gm_at']=now; got+=1
    print('gmgn completed',len(G.get('completed',[])),'new snapshots',got,'launch rate',L[-1] if L else None)
else: print('gmgn failed',err)
L=[x for x in L if x['ts']>=now-7*86400]; json.dump(L,open(LP,'w'))
# other launchpads: GMGN trenches (1 call each, weight 2) -> graduates de-duplicated by address
KP=f'{D}/data/launchpads.json'; K=json.load(open(KP)) if os.path.exists(KP) else {}
for ck,chain,plat,lab in gmgn.LPS:
    time.sleep(2.5); r=gmgn.trench(chain,plat); calls['gmgn']+=1
    e=K.setdefault(lab,{'chain':ck,'grads':{},'launch':[]})
    if not r: print('gmgn',lab,'failed'); continue
    for x in r.get('completed',[]):
        if x.get('complete_timestamp') and x['address'] not in e['grads']:
            e['grads'][x['address']]=[x['complete_timestamp'],int(gmgn.clean(x)),int((gmgn.num(x.get('smart_degen_count')) or 0)>0),
                                      round(float(x.get('usd_market_cap') or 0)),x.get('symbol')]
    ct=[x['complete_timestamp'] for x in r.get('completed',[]) if x.get('complete_timestamp')]
    if len(ct)>=5 and max(ct)>min(ct):
        win=[t for t in ct if t>=now-86400]  # rate over last 24h if list covers it, else over list span
        rate=len(win)/24 if min(ct)<now-86400 else (len(ct)-1)*3600/(max(ct)-min(ct))
        e.setdefault('grate',[]).append([now,round(rate,2)]); e['grate']=[x for x in e['grate'] if x[0]>=now-7*86400]
    nc=[x['created_timestamp'] for x in r.get('new_creation',[]) if x.get('created_timestamp')]
    if len(nc)>=10 and max(nc)>min(nc): e['launch'].append([now,round((len(nc)-1)*3600/(max(nc)-min(nc)),1)])
    e['grads']={a:v for a,v in e['grads'].items() if v[0]>=now-7*86400}; e['launch']=[x for x in e['launch'] if x[0]>=now-7*86400]
    print('gmgn',lab,'grads',len(r.get('completed',[])),'stored',len(e['grads']))
json.dump(K,open(KP,'w'))
# DefiLlama launchpad fees (3-8 calls)
import llama
try: json.dump({'updated':now,**llama.fetch(),'BOTS':llama.bots()},open(f'{D}/data/llama.json','w')); calls['llama']=1
except Exception as ex: print('llama failed',ex)
cut=now-7*86400
db={m:t for m,t in db.items() if (t.get('grad') or t['created'])>=cut}
json.dump(db,open(DB+'.tmp','w')); os.replace(DB+'.tmp',DB)
json.dump({'updated':now,'calls':calls,'n':len(db)},open(f'{D}/data/meta.json','w'))
print('tokens',len(db),'with grad time',sum(1 for t in db.values() if t.get('grad')),'calls',calls)
