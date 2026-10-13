"""GMGN read-only: market trenches (Pump.fun completed + new_creation). Weight 2 per call; one call per run."""
import json,subprocess,shutil,os,time
CLI=shutil.which('gmgn-cli') or (subprocess.run(['npm','prefix','-g'],capture_output=True,text=True).stdout.strip()+'/bin/gmgn-cli')
FIELDS=['top_10_holder_rate','bundler_trader_amount_rate','rat_trader_amount_rate','top70_sniper_hold_rate','dev_team_hold_rate',
 'smart_degen_count','renowned_count','rug_ratio','creator_created_count','creator_created_open_ratio','is_wash_trading',
 'entrapment_ratio','fresh_wallet_rate','bot_degen_rate','holder_count','usd_market_cap','volume_24h','complete_cost_time']
def trenches():
    if not CLI or not os.path.exists(CLI): return None,'gmgn-cli not found'
    for i in range(2):
        p=subprocess.run([CLI,'market','trenches','--chain','sol','--type','completed','--type','new_creation',
                          '--launchpad-platform','Pump.fun','--limit','80','--raw'],capture_output=True,text=True,timeout=60)
        try: return json.loads(p.stdout),None
        except Exception: err=(p.stdout+p.stderr)[:200]; time.sleep(10)
    return None,err
def num(v):
    try: return float(v)
    except Exception: return v

LPS=[('SOL','sol','stonkfun','StonkFun'),('SOL','sol','meteora_virtual_curve','Meteora DBC'),
     ('BSC','bsc','flap','Flap'),('Robinhood','robinhood','pons','Pons')]
def trench(chain,plat):
    p=subprocess.run([CLI,'market','trenches','--chain',chain,'--type','completed','--type','new_creation',
                      '--launchpad-platform',plat,'--limit','80','--raw'],capture_output=True,text=True,timeout=60)
    try: return json.loads(p.stdout)
    except Exception: return None
def clean(x):
    v=lambda k:num(x.get(k)) if isinstance(num(x.get(k)),float) else 0
    return (v('top_10_holder_rate')<0.3 and v('bundler_trader_amount_rate')<0.3 and v('rat_trader_amount_rate')<0.3 and
            v('top70_sniper_hold_rate')<0.3 and v('dev_team_hold_rate')<0.1 and v('rug_ratio')<0.3 and not x.get('is_wash_trading'))
