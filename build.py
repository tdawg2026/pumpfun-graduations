#!/usr/bin/env python3
import json,os,time
D=os.path.dirname(os.path.abspath(__file__))
def q(g):
    # GMGN quality snapshot -> compact: [top10, bundler, insider, sniper, dev_hold, smart, kol, rug, clean]
    if not g: return None
    v=lambda k:(g.get(k) if isinstance(g.get(k),(int,float)) else 0) or 0
    clean=int(v('top_10_holder_rate')<0.3 and v('bundler_trader_amount_rate')<0.3 and v('rat_trader_amount_rate')<0.3
              and v('top70_sniper_hold_rate')<0.3 and v('dev_team_hold_rate')<0.1 and v('rug_ratio')<0.3 and not g.get('is_wash_trading'))
    r=lambda x:round(x,3)
    return [r(v('top_10_holder_rate')),r(v('bundler_trader_amount_rate')),r(v('rat_trader_amount_rate')),r(v('top70_sniper_hold_rate')),
            r(v('dev_team_hold_rate')),int(v('smart_degen_count')),int(v('renowned_count')),r(v('rug_ratio')),clean]
db=list(json.load(open(f'{D}/data/tokens.json')).values()); meta=json.load(open(f'{D}/data/meta.json'))
rows=[{'m':t['mint'],'s':t.get('symbol') or '','n':(t.get('name') or '')[:40],'g':t.get('grad') or t['created'],
       'a':t.get('ath_mcap'),'c':t.get('mcap'),'f':t.get('first_seen'),'h':t.get('holders_now'),'ha':t.get('holders_at'),'q':q(t.get('gm'))} for t in db]
LP=f'{D}/data/launches.json'
L=json.load(open(LP)) if os.path.exists(LP) else []
data=json.dumps({'rows':rows,'updated':meta['updated'],'launch':L},separators=(',',':'))
html=r'''<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>pump.fun 每小时毕业代币</title><style>
body{background:#0d1117;color:#e6edf3;font:14px -apple-system,"PingFang SC",sans-serif;margin:0;padding:16px;max-width:1200px;margin:auto}
h1{font-size:20px;margin:4px 0}.sub{color:#8b949e;font-size:12px}.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;margin:12px 0;overflow-x:auto}
button{background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:4px 12px;cursor:pointer}button.on{background:#238636}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:5px 8px;border-bottom:1px solid #21262d;text-align:right;white-space:nowrap}
th{cursor:pointer;color:#8b949e;position:sticky;top:0;background:#161b22}td:first-child,th:first-child{text-align:left}a{color:#58a6ff;text-decoration:none}
.kpi{display:flex;gap:10px;flex-wrap:wrap}.kpi div{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:8px 12px}.kpi b{display:block;font-size:18px}
#chart,#trend{width:100%;height:220px}.big{font-size:32px!important}.scroll{max-height:520px;overflow:auto}.note{color:#8b949e;font-size:12px;line-height:1.6}</style></head><body>
<h1>pump.fun 每小时内盘打满（毕业）代币</h1><div class="sub">时间均为 UTC+7 · 最后更新：<span id="upd"></span></div>
<div class="card"><b>Meme 情绪指数</b> <span class="sub">基于 pump.fun 毕业数量与质量，对比 7 天基线</span>
<div class="kpi" id="senti" style="margin-top:10px"></div><svg id="trend"></svg><div class="note" id="comp"></div></div>
<div class="card"><button data-h="24" class="on">24 小时</button> <button data-h="168">7 天</button>
<div class="kpi" id="kpi" style="margin-top:10px"></div><svg id="chart"></svg></div>
<div class="card"><b>每小时汇总</b><div class="scroll"><table id="sum"></table></div></div>
<div class="card"><b>优质毕业代币（近 24 小时）</b> <span class="sub">GMGN 干净 + 按 ATH 市值排序</span><div class="scroll"><table id="topq"></table></div></div>
<div class="card"><b>毕业代币列表</b> <span class="sub">点击表头排序</span><div class="scroll"><table id="tok"></table></div></div>
<div class="card note">数据说明：代币列表、ATH 市值和当前市值来自 pump.fun 前端接口（frontend-api-v3，非官方，单次最多翻 1000 条，所以首次抓取只能完整覆盖约最近 20 小时，更早的小时数偏少；之后每次运行会累积，最多保留 7 天）。毕业时间取 GeckoTerminal 上 PumpSwap 池子的创建时间。ATH 市值是 pump.fun 记录的历史最高（含内盘阶段），按 10 亿总供应计算，美元计价；流动性很薄的代币可能被刷高。持有人数通过 Helius RPC（getProgramAccountsV2）统计余额大于 0 的账户数（含池子/合约账户），每个代币只查一次、不再更新：新毕业代币一般在毕业后 1 小时内查询，数字下方为查询时间（UTC+7）。早期已收录的代币查询时间可能晚于毕业较久。质量数据来自 GMGN（market trenches，Pump.fun 已毕业列表），每个代币只在毕业后约 1–2 小时内取一次快照：前 10 持仓、捆绑、老鼠仓、狙击、开发者持仓、跑路风险、聪明钱/KOL 数。“干净”= 前10&lt;30%、捆绑&lt;30%、老鼠仓&lt;30%、狙击&lt;30%、开发者&lt;10%、跑路风险&lt;0.3 且无刷量。GMGN 数据从 2026-10-13 起收集，早期代币无质量数据；发射数为每次运行时用 GMGN 最新 60 个新币的时间跨度估算的速率。页面由 GitHub Actions 每小时自动更新。</div>
<script>const D=__DATA__;
const f=v=>v==null?'-':v>=1e9?'$'+(v/1e9).toFixed(2)+'B':v>=1e6?'$'+(v/1e6).toFixed(2)+'M':v>=1e3?'$'+(v/1e3).toFixed(1)+'K':'$'+v.toFixed(0);
const tz=7*3600,hk=t=>Math.floor((t+tz)/3600),hs=h=>{const d=new Date(h*3600e3);return (d.getUTCMonth()+1)+'/'+d.getUTCDate()+' '+String(d.getUTCHours()).padStart(2,'0')+':00'};
const ts=t=>{const d=new Date((t+tz)*1e3);return d.toISOString().slice(5,16).replace('T',' ')};
document.getElementById('upd').textContent=ts(D.updated);
const med=a=>{if(!a.length)return null;a=[...a].sort((x,y)=>x-y);const m=a.length>>1;return a.length%2?a[m]:(a[m-1]+a[m])/2};
let H=24,sk='g',sd=-1;
function render(){const now=hk(D.updated),from=now-H+1,rs=D.rows.filter(r=>hk(r.g)>=from);
 const by={};for(let h=from;h<=now;h++)by[h]=[];rs.forEach(r=>by[hk(r.g)].push(r));
 const hs_=Object.keys(by).map(Number),cnt=hs_.map(h=>by[h].length),mx=Math.max(1,...cnt);
 const A=rs.map(r=>r.a||0);document.getElementById('kpi').innerHTML=`<div>毕业数<b>${rs.length}</b></div><div>平均每小时<b>${(rs.length/H).toFixed(1)}</b></div><div>ATH 中位数<b>${f(med(A))}</b></div><div>ATH &gt;$1M<b>${A.filter(x=>x>1e6).length}</b></div><div>ATH &gt;$10M<b>${A.filter(x=>x>1e7).length}</b></div>`;
 const W=1000,Hh=220,bw=W/hs_.length;let s=`<svg viewBox="0 0 ${W} ${Hh}" preserveAspectRatio="none">`;
 hs_.forEach((h,i)=>{const bh=(cnt[i]/mx)*(Hh-30);s+=`<rect x="${i*bw+1}" y="${Hh-20-bh}" width="${Math.max(1,bw-2)}" height="${bh}" fill="#2ea043"><title>${hs(h)}：${cnt[i]} 个</title></rect>`;
  if(H==24||i%24==0)s+=`<text x="${i*bw+bw/2}" y="${Hh-5}" fill="#8b949e" font-size="${H==24?11:12}" text-anchor="middle">${H==24?hs(h).slice(-5,-3):hs(h).split(' ')[0]}</text>`});
 s+=`<text x="4" y="12" fill="#8b949e" font-size="12">最高 ${mx}/小时</text>`;document.getElementById('chart').outerHTML=s.replace('<svg','<svg id="chart"')+'</svg>';
 let t='<tr><th>小时</th><th>数量</th><th>ATH 中位数</th><th>ATH 最高</th><th>&gt;$1M</th><th>&gt;$10M</th><th>持有人中位数</th><th>干净占比</th><th>聪明钱参与</th></tr>';
 hs_.slice().reverse().forEach(h=>{const a=by[h].map(r=>r.a||0);t+=`<tr><td>${hs(h)}</td><td>${a.length}</td><td>${f(med(a))}</td><td>${a.length?f(Math.max(...a)):'-'}</td><td>${a.filter(x=>x>1e6).length}</td><td>${a.filter(x=>x>1e7).length}</td><td>${med(by[h].map(r=>r.h).filter(x=>x!=null))??'-'}</td><td>${pct(by[h],r=>r.q[8])}</td><td>${pct(by[h],r=>r.q[5]>0)}</td></tr>`});
 document.getElementById('sum').innerHTML=t;
 rs.forEach(r=>r.qs=r.q?r.q[8]*10+r.q[5]:null);rs.sort((x,y)=>{const a=x[sk]??-1,b=y[sk]??-1;return (a>b?1:a<b?-1:0)*sd});
 const cols=[['s','代币'],['g','毕业时间'],['a','ATH 市值'],['c','当前市值'],['h','持有人（首次查询）'],['qs','GMGN 质量']];
 t='<tr>'+cols.map(([k,n])=>`<th data-k="${k}">${n}${sk==k?(sd>0?' ▲':' ▼'):''}</th>`).join('')+'<th>链接</th></tr>';
 rs.forEach(r=>{t+=`<tr><td title="${r.m}"><b>${esc(r.s)}</b> <span class="sub">${esc(r.n)}</span></td><td>${ts(r.g)}</td><td>${f(r.a)}</td><td>${f(r.c)}</td><td title="查询时间 ${r.ha?ts(r.ha):'-'}">${r.h??'-'}${r.ha?'<div class=sub>'+ts(r.ha)+'</div>':''}</td><td>${qcell(r)}</td><td><a href="https://pump.fun/coin/${r.m}" target="_blank">pump</a> · <a href="https://dexscreener.com/solana/${r.m}" target="_blank">dex</a></td></tr>`});
 const tb=document.getElementById('tok');tb.innerHTML=t;tb.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{const k=th.dataset.k;sd=sk==k?-sd:-1;sk=k;render()})}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
document.querySelectorAll('button').forEach(b=>b.onclick=()=>{document.querySelectorAll('button').forEach(x=>x.classList.remove('on'));b.classList.add('on');H=+b.dataset.h;render()});render();
function pct(a,fn){a=a.filter(r=>r.q);return a.length?Math.round(100*a.filter(fn).length/a.length)+'%':'-'}
function qcell(r){if(!r.q)return '<span class=sub>-</span>';const q=r.q,p=x=>Math.round(x*100);return `<span title="前10持仓 ${p(q[0])}% · 捆绑 ${p(q[1])}% · 老鼠仓 ${p(q[2])}% · 狙击 ${p(q[3])}% · 开发者 ${p(q[4])}% · 跑路风险 ${p(q[7])}%">${q[8]?'✅ 干净':'⚠️'}${q[5]?' 🧠'+q[5]:''}${q[6]?' 📣'+q[6]:''}</span><div class=sub>前10 ${p(q[0])}% 捆绑 ${p(q[1])}%</div>`}
// ===== 情绪指数 =====
const W=[['grad','毕业数',0.30],['launch','发射数(新币/小时)',0.10],['ath1m','ATH>$1M 占比',0.20],['athmed','ATH 中位数',0.15],['clean','GMGN 干净占比',0.15],['smart','聪明钱参与占比',0.10]];
function metrics(end){ // end: unix sec. 计数类用 [end-24h,end)，ATH 类用 [end-26h,end-2h)（给代币 2 小时以上时间走出高点）
 const c=D.rows.filter(r=>r.g>=end-86400&&r.g<end),a=D.rows.filter(r=>r.g>=end-26*3600&&r.g<end-7200),g=c.filter(r=>r.q);
 const L=D.launch.filter(x=>x.ts>end-86400&&x.ts<=end),A=a.map(r=>r.a||0);
 return {grad:c.length,launch:L.length?med(L.map(x=>x.rate)):null,ath1m:A.length?A.filter(x=>x>1e6).length/A.length:null,athmed:med(A),
  clean:g.length>=10?g.filter(r=>r.q[8]).length/g.length:null,smart:g.length>=10?g.filter(r=>r.q[5]>0).length/g.length:null,n:c.length,ng:g.length}}
function senti(){const end=D.updated,first=Math.min(...D.rows.map(r=>r.f||D.updated))-20*3600,pts=[];
 for(let e=Math.floor(end/3600)*3600;e>=first+86400;e-=3600)pts.unshift([e,metrics(e)]);
 const now=metrics(end),base={};W.forEach(([k])=>{base[k]=med(pts.map(p=>p[1][k]).filter(x=>x!=null&&x>0))});
 const score=m=>{let s=0,w=0;const parts={};W.forEach(([k,n,wt])=>{if(m[k]==null||!base[k])return;const v=Math.max(0,Math.min(100,50*m[k]/base[k]));parts[k]=v;s+=v*wt;w+=wt});return {v:w?s/w:null,parts}};
 const S=score(now),lab=v=>v==null?'-':v<40?'冷淡 🥶':v<=60?'中性 😐':'火热 🔥',col=v=>v<40?'#58a6ff':v<=60?'#d29922':'#f85149';
 const nb=pts.length;const ser=pts.map(([e,m])=>[e,score(m).v]).filter(x=>x[1]!=null);
 document.getElementById('senti').innerHTML=`<div>当前指数<b class="big" style="color:${col(S.v)}">${S.v==null?'-':S.v.toFixed(0)}</b>${lab(S.v)}<span class=sub>基线样本 ${nb} 小时${nb<24?'（不足，仅供参考）':''}</span></div>`+
  W.map(([k,n])=>`<div>${n}<b>${now[k]==null?'-':(k=='ath1m'||k=='clean'||k=='smart')?(now[k]*100).toFixed(1)+'%':k=='athmed'?f(now[k]):Math.round(now[k])}</b><span class=sub>基线 ${base[k]==null?'-':(k=='ath1m'||k=='clean'||k=='smart')?(base[k]*100).toFixed(1)+'%':k=='athmed'?f(base[k]):Math.round(base[k])} · 分 ${S.parts[k]==null?'-':S.parts[k].toFixed(0)}</span></div>`).join('');
 let s='<svg id="trend" viewBox="0 0 1000 220" preserveAspectRatio="none"><rect x="0" y="'+(200-60*2)+'" width="1000" height="'+(20*2)+'" fill="#d2992222"/>';
 if(ser.length>1){const x=i=>i*1000/(ser.length-1),y=v=>200-v*2;s+='<polyline fill="none" stroke="#58a6ff" stroke-width="2" points="'+ser.map((p,i)=>x(i)+','+y(p[1])).join(' ')+'"/>';
  ser.forEach((p,i)=>{if(i%24==0)s+=`<text x="${x(i)}" y="215" fill="#8b949e" font-size="12">${hs(hk(p[0])).split(' ')[0]}</text>`})}
 s+='<text x="4" y="14" fill="#8b949e" font-size="12">指数走势（每小时，滚动 24h）· 黄色带=中性 40–60</text></svg>';document.getElementById('trend').outerHTML=s;
 document.getElementById('comp').innerHTML=`<b>计算方法</b>：每个分项 = 50 × 当前值 ÷ 7 天基线（基线为过去每小时滚动 24h 值的中位数），截断在 0–100；指数 = 各分项加权平均（${W.map(([k,n,w])=>n+' '+(w*100)+'%').join('，')}），缺数据的分项不计入并按剩余权重归一。等于基线时为 50；基线只用数据完整覆盖的时段（从首次采集前约 20 小时起），会随运行逐步积累到 7 天；&lt;40 冷淡，40–60 中性，&gt;60 火热。计数类用最近 24 小时毕业的代币；ATH 类用 2–26 小时前毕业的代币（给代币时间走出高点）。GMGN 类分项需当期至少 10 个有快照的代币（当前 ${now.ng} 个）。`;
 const tq=D.rows.filter(r=>r.g>=end-86400&&r.q&&r.q[8]).sort((a,b)=>(b.a||0)-(a.a||0)).slice(0,20);
 document.getElementById('topq').innerHTML='<tr><th>代币</th><th>毕业时间</th><th>ATH 市值</th><th>当前市值</th><th>持有人</th><th>GMGN</th></tr>'+tq.map(r=>`<tr><td><b>${esc(r.s)}</b> <span class=sub>${esc(r.n)}</span></td><td>${ts(r.g)}</td><td>${f(r.a)}</td><td>${f(r.c)}</td><td>${r.h??'-'}</td><td>${qcell(r)}</td></tr>`).join('')||'<tr><td>暂无 GMGN 数据</td></tr>'}
senti();</script></body></html>'''
open(f'{D}/public/index.html','w').write(html.replace('__DATA__',data.replace('</','<\\/')))
print('built',len(rows))
