"""Holder count = token accounts with balance > 0.
Uses Helius getProgramAccountsV2 (1 credit/page, 10k accounts/page) if HELIUS_API_KEY is set, else public RPC getProgramAccounts."""
import json,subprocess,base64,struct,time,os
LAST='';CREDITS=0
KEY=os.environ.get('HELIUS_API_KEY','').strip()
PUB='https://api.mainnet-beta.solana.com'
PROG={'2022':'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb','spl':'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'}
def _post(url,body):
    # URL passed via curl config on stdin so the key never appears in the process list
    p=subprocess.run(['curl','-s','-m','60','-K','-','-H','content-type: application/json','-d',json.dumps(body)],
                     input=f'url = "{url}"\n',capture_output=True,text=True)
    try: return json.loads(p.stdout)
    except Exception: return {'error':p.stdout[:200]}
def _nz(accts): return sum(1 for a in accts if struct.unpack('<Q',base64.b64decode(a['account']['data'][0]))[0]>0)
def holders(mint,prog):
    global LAST,CREDITS
    f=[{"memcmp":{"offset":0,"bytes":mint}}]+([{"dataSize":165}] if prog==PROG['spl'] else [])
    opt={"encoding":"base64","dataSlice":{"offset":64,"length":8},"filters":f}
    if KEY:
        url='https://mainnet.helius-rpc.com/?api-key='+KEY; n=0; pk=None
        for page in range(50):
            o=dict(opt,limit=10000); 
            if pk: o['paginationKey']=pk
            for i in range(3):
                d=_post(url,{"jsonrpc":"2.0","id":1,"method":"getProgramAccountsV2","params":[prog,o]}); CREDITS+=1
                if 'result' in d: break
                LAST=str(d.get('error'))[:200]; time.sleep(1+2*i)
            else: return None
            n+=_nz(d['result']['accounts']); pk=d['result'].get('paginationKey')
            if not pk: return n
            time.sleep(0.12)
        return n
    for i in range(2):
        d=_post(PUB,{"jsonrpc":"2.0","id":1,"method":"getProgramAccounts","params":[prog,opt]})
        if 'result' in d: return _nz(d['result'])
        LAST=str(d)[:200]; time.sleep(2)
    return None
