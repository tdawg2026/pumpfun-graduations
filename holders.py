import json,subprocess,base64,struct,time
LAST=''
RPC='https://api.mainnet-beta.solana.com'
PROG={'2022':'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb','spl':'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'}
def holders(mint,prog):
    f=[{"memcmp":{"offset":0,"bytes":mint}}]+([{"dataSize":165}] if prog==PROG['spl'] else [])
    b={"jsonrpc":"2.0","id":1,"method":"getProgramAccounts","params":[prog,{"encoding":"base64","dataSlice":{"offset":64,"length":8},"filters":f}]}
    global LAST
    for i in range(2):
        p=subprocess.run(['curl','-s','-m','60',RPC,'-H','content-type: application/json','-d',json.dumps(b)],capture_output=True,text=True)
        try: d=json.loads(p.stdout)
        except Exception: d={}
        if 'result' in d:
            return sum(1 for a in d['result'] if struct.unpack('<Q',base64.b64decode(a['account']['data'][0]))[0]>0)
        LAST=(p.stdout or p.stderr)[:200]; time.sleep(2)
    return None
if __name__=='__main__':
    import sys;t=time.time();print(holders(sys.argv[1],PROG['2022']),round(time.time()-t,1),'s')
