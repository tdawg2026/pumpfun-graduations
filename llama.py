"""DefiLlama free API: per-chain daily fees of Launchpad-category protocols (3 calls/run)."""
import json,urllib.request,time
CHAINS={'SOL':'Solana','BSC':'BSC','Robinhood':'Robinhood Chain'}
# top-2 non-pump launchpads per chain by 7d fees on that chain (verified 2026-10-13); Pons V1+V2 merged
SLUG={'pump.fun':'pump.fun','StonkFun':'stonkfun','Meteora Dynamic Bonding Curve':'meteora-dynamic-bonding-curve','Flap sh':'flap-sh','Binance Alpha':'binance-alpha','Pons V2':'pons-v2','Pons V1':'pons-v1','NOXA Fun':'noxa-fun'}
PICK={'SOL':{'StonkFun':['StonkFun'],'Meteora DBC':['Meteora Dynamic Bonding Curve']},
      'BSC':{'Flap':['Flap sh'],'Binance Alpha':['Binance Alpha']},
      'Robinhood':{'Pons':['Pons V2','Pons V1'],'NOXA Fun':['NOXA Fun']}}
def get(u):
    for i in range(3):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=90))
        except Exception as e: err=e; time.sleep(5)
    raise err
def fetch(days=60):
    out={}
    for k,c in CHAINS.items():
        d=get('https://api.llama.fi/overview/fees/'+urllib.parse.quote(c)+'?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=false&dataType=dailyFees')
        lp={p['name'] for p in d['protocols'] if p.get('category')=='Launchpad'}
        today=int(time.time())//86400*86400
        rows=[r for r in d['totalDataChartBreakdown'] if r[0]<today][-days:]  # drop today's partial row
        ser={'days':[r[0] for r in rows],'total':[round(sum(v for n,v in r[1].items() if n in lp)) for r in rows],'protos':{}}
        names=dict(PICK[k]); 
        if k=='SOL': names={'pump.fun':['pump.fun'],**names}
        inbd=set().union(*[set(r[1]) for r in rows[-7:]])
        for lab,ns in names.items():
            tot=[0]*len(rows)
            for n in ns:
                if n in inbd: v=[r[1].get(n,0) for r in rows]
                else:  # missing from chain breakdown -> per-protocol summary, this chain only
                    sm=get(f'https://api.llama.fi/summary/fees/{SLUG[n]}?dataType=dailyFees'); time.sleep(1)
                    m={t:sum(x.get(c,{}).values()) if isinstance(x.get(c),dict) else (x.get(c) or 0) for t,x in sm.get('totalDataChartBreakdown',[])}
                    v=[m.get(r[0],0) for r in rows]
                    ser['total']=[a+b for a,b in zip(ser['total'],[round(x) for x in v])]
                tot=[a+b for a,b in zip(tot,v)]
            ser['protos'][lab]=[round(x) for x in tot]
        # rank snapshot for transparency
        ser['rank7d']=sorted([[p['name'],round(p.get('total7d') or 0)] for p in d['protocols'] if p.get('category')=='Launchpad'],key=lambda x:-x[1])[:8]
        out[k]=ser; time.sleep(1)
    return out
