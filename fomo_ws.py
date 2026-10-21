#!/usr/bin/env python3
"""Box-only long-running collector: FOMO API /ws/alerts (unofficial, fomoapi.io; 0 credits) -> buy/sell events.
Stores ~/.local/share/fomo/events.jsonl (eventId-deduped, 8-day retention) + heartbeat file. Auto-reconnects.
Key from ~/.config/fomoapi_key (never logged)."""
import asyncio,json,os,sys,time,websockets
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
S=os.path.expanduser('~/.local/share/fomo'); os.makedirs(S,exist_ok=True)
EV=f'{S}/events.jsonl'; HB=f'{S}/heartbeat'
KEY=open(os.path.expanduser('~/.config/fomoapi_key')).read().strip()
def log(*a): print(time.strftime('%F %T'),*a,flush=True)
seen=set()
def load():
    if not os.path.exists(EV): return
    keep=[]; cut=time.time()*1000-8*86400e3
    for l in open(EV):
        try: e=json.loads(l)
        except Exception: continue
        if e['ts']>=cut and e['id'] not in seen: seen.add(e['id']); keep.append(l)
    open(EV+'.tmp','w').writelines(keep); os.replace(EV+'.tmp',EV)
from fomo_common import norm
def rec(d,f):
    if d.get('type')!='alert': return 0
    e=norm(d)
    if not e or e['id'] in seen: return 0
    seen.add(e['id']); f.write(json.dumps(e)+'\n'); return 1
async def run():
    back=5
    while True:
        try:
            async with websockets.connect('wss://api.fomoapi.io/ws/alerts?key='+KEY,ping_interval=20,ping_timeout=30,open_timeout=30) as w:
                log('connected'); back=5; n=0; last=time.time()
                with open(EV,'a') as f:
                    while True:
                        x=await asyncio.wait_for(w.recv(),timeout=300)  # alert stream is never quiet 5 min
                        try: n+=rec(json.loads(x),f)
                        except Exception: pass
                        if time.time()-last>30: f.flush(); open(HB,'w').write(str(int(time.time()))); last=time.time()
        except Exception as ex:
            log('disconnected:',type(ex).__name__,str(ex)[:120].replace(KEY,'***'),'retry in',back,'s')
            await asyncio.sleep(back); back=min(back*2,300)
        if len(seen)>200000: seen.clear(); load()
load(); log('start, known events',len(seen)); asyncio.run(run())
