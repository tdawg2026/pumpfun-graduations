"""Normalize a FOMO alert (WS or REST) into a stored buy/sell event, or None.
Measured: buy usdValue == positionValueUsd (post-fill position mark); SELL usdValue is REALIZED PnL ("sold $X (+$405 realized)"),
not size. So: buys -> pos (position USD); sells -> pnl (realized USD); fill = tradeUsd when FOMO supplies it."""
def norm(d):
    t=d.get('alertType') or d.get('type')
    if t not in ('buy','sell') or not d.get('eventId'): return None
    e={'id':d['eventId'],'ts':d.get('ts'),'chain':d.get('chain'),'side':t,'user':d.get('userId'),'token':d.get('tokenAddress'),'sym':d.get('token'),
       'fill':d.get('tradeUsd')}
    if t=='buy': e['pos']=d.get('positionValueUsd') if d.get('positionValueUsd') is not None else d.get('usdValue')
    else: e['pnl']=d.get('usdValue')
    return e
