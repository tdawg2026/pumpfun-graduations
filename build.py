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
LL=json.load(open(f'{D}/data/llama.json')) if os.path.exists(f'{D}/data/llama.json') else {}
KP=json.load(open(f'{D}/data/launchpads.json')) if os.path.exists(f'{D}/data/launchpads.json') else {}
for e in KP.values(): e['g']=list(e.pop('grads',{}).values())
data=json.dumps({'ll':LL,'lp':KP,'rows':rows,'updated':meta['updated'],'launch':L},separators=(',',':'))
html=r'''<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>pump.fun 每小时毕业代币</title><style>
body{background:#0d1117;color:#e6edf3;font:14px -apple-system,"PingFang SC",sans-serif;margin:0;padding:16px;max-width:1200px;margin:auto}
h1{font-size:20px;margin:4px 0}.sub{color:#8b949e;font-size:12px}.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;margin:12px 0;overflow-x:auto}
button{background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:4px 12px;cursor:pointer}button.on{background:#238636}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:5px 8px;border-bottom:1px solid #21262d;text-align:right;white-space:nowrap}
th{cursor:pointer;color:#8b949e;position:sticky;top:0;background:#161b22}td:first-child,th:first-child{text-align:left}a{color:#58a6ff;text-decoration:none}
.kpi{display:flex;gap:10px;flex-wrap:wrap}.kpi div{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:8px 12px}.kpi b{display:block;font-size:18px}
#chart,#trend,#bottrend{width:100%;height:220px}.big{font-size:32px!important}.scroll{max-height:520px;overflow:auto}.note{color:#8b949e;font-size:12px;line-height:1.6}</style></head><body>
<h1>Meme 情绪看板 · pump.fun 毕业与发射台</h1><div class="sub">时间均为 UTC+7 · 最后更新：<span id="upd"></span></div>
<div class="card"><b>综合 Meme 情绪指数</b> <span class="sub">发射台活跃度 + 交易机器人活跃度（DefiLlama）+ pump.fun 数量与质量（本站 + GMGN）</span>
<div class="kpi" id="overall" style="margin-top:10px"></div><div class="kpi" id="chains" style="margin-top:10px"></div><div class="note" id="ocomp"></div></div>
<div class="card"><b>交易机器人 / 交易终端</b> <span class="sub">DefiLlama「Trading App」+「Telegram Bot」类 7 天手续费前 3</span><div class="scroll"><table id="bott"></table></div><svg id="bottrend"></svg></div>
<div class="card"><b>发射台对比</b> <span class="sub">每条链除 pump.fun 外手续费前 2 的发射台（DefiLlama 7 天手续费排名）</span><div class="scroll"><table id="lpt"></table></div></div>
<div class="card"><b>pump.fun 情绪指数</b> <span class="sub">基于 pump.fun 毕业数量与质量，对比 7 天基线</span>
<div class="kpi" id="senti" style="margin-top:10px"></div><svg id="trend"></svg><div class="note" id="comp"></div></div>
<div class="card"><button data-h="24" class="on">24 小时</button> <button data-h="168">7 天</button>
<div class="kpi" id="kpi" style="margin-top:10px"></div><svg id="chart"></svg></div>
<div class="card"><b>每小时汇总</b><div class="scroll"><table id="sum"></table></div></div>
<div class="card"><b>优质毕业代币（近 24 小时）</b> <span class="sub">GMGN 干净 + 按 ATH 市值排序</span><div class="scroll"><table id="topq"></table></div></div>
<div class="card"><b>毕业代币列表</b> <span class="sub">点击表头排序</span><div class="scroll"><table id="tok"></table></div></div>
<div class="card note">数据说明：代币列表、ATH 市值和当前市值来自 pump.fun 前端接口（frontend-api-v3，非官方，单次最多翻 1000 条，所以首次抓取只能完整覆盖约最近 20 小时，更早的小时数偏少；之后每次运行会累积，最多保留 7 天）。毕业时间取 GeckoTerminal 上 PumpSwap 池子的创建时间。ATH 市值是 pump.fun 记录的历史最高（含内盘阶段），按 10 亿总供应计算，美元计价；流动性很薄的代币可能被刷高。持有人数通过 Helius RPC（getProgramAccountsV2）统计余额大于 0 的账户数（含池子/合约账户），每个代币只查一次、不再更新：新毕业代币一般在毕业后 1 小时内查询，数字下方为查询时间（UTC+7）。早期已收录的代币查询时间可能晚于毕业较久。质量数据来自 GMGN（market trenches，Pump.fun 已毕业列表），每个代币只在毕业后约 1–2 小时内取一次快照：前 10 持仓、捆绑、老鼠仓、狙击、开发者持仓、跑路风险、聪明钱/KOL 数。“干净”= 前10&lt;30%、捆绑&lt;30%、老鼠仓&lt;30%、狙击&lt;30%、开发者&lt;10%、跑路风险&lt;0.3 且无刷量。GMGN 数据从 2026-10-13 起收集，早期代币无质量数据；发射数为每次运行时用 GMGN 最新 60 个新币的时间跨度估算的速率。发射台数据来自 DefiLlama 免费接口（Launchpad 类协议的链上日手续费，按链拆分；Pons 为 V1+V2 合计；BSC 第二名 Binance Alpha 并非 meme 发射台但按数据排名纳入，GMGN 无对应数据）；其他发射台的毕业/新币速率和质量来自 GMGN trenches（StonkFun、Meteora DBC、Flap、Pons；NOXA Fun 与 Binance Alpha 在 GMGN 无数据），Meteora DBC 包含所有基于该曲线的发射台。页面由 GitHub Actions 每小时自动更新。</div>
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

// ===== 发射台层 & 综合指数 =====
const CL={SOL:'Solana',BSC:'BSC',Robinhood:'Robinhood Chain'},clip=v=>Math.max(0,Math.min(100,v)),sum=a=>a.reduce((x,y)=>x+y,0);
function lastFull(c){const P=Object.values(c.protos);let i=c.days.length-1;while(i>0&&P.some(p=>{const nz=p.slice(-14).filter(x=>x>0).length;return nz>=10&&p[i]==0}))i--;return i}
function feeScore(c){const i=lastFull(c),rec=sum(c.total.slice(i-2,i+1))/3,base=med(c.total.slice(Math.max(0,i-32),i-2));return {i,rec,base,s:base?clip(50*rec/base):null}}
function lpRate(e,key){const a=(e[key]||[]).map(x=>x[1]);return a.length?{now:a[a.length-1],base:med(a)}:null}

function botLayer(){const B=D.ll.BOTS;if(!B||!Object.keys(B.protos).length)return null;
 const ps=Object.entries(B.protos),days=ps[0][1].days,n=days.length,tot=days.map((d,j)=>sum(ps.map(([k,p])=>{const i=p.days.indexOf(d);return i<0?0:p.v[i]})));
 let i=n-1;while(i>0&&ps.some(([k,p])=>p.v[p.days.indexOf(days[i])]===0))i--;
 const rec=sum(tot.slice(i-2,i+1))/3,base=med(tot.slice(Math.max(0,i-32),i-2)),S=base?clip(50*rec/base):null,s7=(a,j)=>sum(a.slice(j-6,j+1));
 let t='<tr><th>名称</th><th>类别</th><th>最新日手续费</th><th>7 天</th><th>30 天</th><th>环比前 7 天</th><th>前 3 内占比(7天)</th><th>占整个板块(7天)</th><th>链分布(30天)</th></tr>';const T7=s7(tot,i);
 ps.forEach(([k,p])=>{const a=p.v,j=a.length-1-(n-1-i),w=s7(a,j),pw=s7(a,j-7),m=sum(a.slice(j-29,j+1));
  t+=`<tr><td><b>${k}</b></td><td>${p.cat=='Telegram Bot'?'TG 机器人':'交易终端/App'}</td><td>${f(a[j])}</td><td>${f(w)}</td><td>${f(m)}</td><td style="color:${w>=pw?'#3fb950':'#f85149'}">${pw?((w/pw-1)*100).toFixed(0)+'%':'-'}</td><td>${(100*w/T7).toFixed(1)}%</td><td>${(100*w/B.sector7d).toFixed(1)}%</td><td class=sub>${p.mix.map(([c,v])=>c.replace(' Chain','')+' '+Math.round(v*100)+'%').join(' · ')}</td></tr>`});
 t+=`<tr><td colspan=9 class=sub>板块 7 天前 8：${B.rank.map(r=>r[0]+' '+f(r[2])).join('，')}</td></tr>`;document.getElementById('bott').innerHTML=t;
 const sp=tot.slice(0,i+1),mx=Math.max(...sp);let s=`<svg id="bottrend" viewBox="0 0 1000 160" preserveAspectRatio="none">`;
 s+=`<polyline fill="none" stroke="#a371f7" stroke-width="2" points="${sp.map((v,j)=>(j*1000/(sp.length-1))+','+(150-140*v/mx)).join(' ')}"/>`;
 sp.forEach((v,j)=>{if(j%10==0)s+=`<text x="${j*1000/(sp.length-1)}" y="158" fill="#8b949e" font-size="11">${new Date(days[j]*1e3).toISOString().slice(5,10)}</text>`});
 s+=`<text x="4" y="12" fill="#8b949e" font-size="12">前 3 合计日手续费（近 ${sp.length} 天，最高 ${f(mx)}）</text></svg>`;document.getElementById('bottrend').outerHTML=s;
 return {S,rec,base,asof:days[i]}}
function overall(P){const LL=D.ll,ch={};let rec=0,base=0;
 Object.keys(CL).forEach(k=>{if(!LL[k])return;const fs=feeScore(LL[k]);ch[k]=fs;rec+=fs.rec;base+=fs.base});
 const A=base?clip(50*rec/base):null;
 // pump.fun 份额（近 7 天）
 const s7=(a,i)=>sum(a.slice(i-6,i+1)),sol=LL.SOL,ip=sol?lastFull(sol):0;let tot7=0,tot7p=0;Object.keys(ch).forEach(k=>{const c=LL[k],i=ch[k].i;tot7+=s7(c.total,i);tot7p+=s7(c.total,i-7)});
 const pumpShare=sol?s7(sol.protos['pump.fun'],ip)/tot7:null,pumpShareP=sol?s7(sol.protos['pump.fun'],ip-7)/tot7p:null;
 const BL=botLayer(),BS=BL?BL.S:null,parts=[[A,0.30],[BS,0.25],[P,0.45]].filter(x=>x[0]!=null),O=parts.length?sum(parts.map(x=>x[0]*x[1]))/sum(parts.map(x=>x[1])):null;
 const sub={};Object.keys(ch).forEach(k=>{const fs=ch[k].s;if(k=='SOL'){sub[k]=P!=null?0.5*fs+0.5*P:fs;return}
  const e=Object.values(D.lp).find(e=>e.chain==k),g=e&&lpRate(e,'grate');const gs=g&&g.base?clip(50*g.now/g.base):null;sub[k]=gs!=null?0.7*fs+0.3*gs:fs});
 const lab=v=>v==null?'-':v<40?'冷淡 🥶':v<=60?'中性 😐':'火热 🔥',col=v=>v<40?'#58a6ff':v<=60?'#d29922':'#f85149',n0=v=>v==null?'-':v.toFixed(0);
 document.getElementById('overall').innerHTML=`<div>综合指数<b class="big" style="color:${col(O)}">${n0(O)}</b>${lab(O)}</div><div>发射台活跃度<b>${n0(A)}</b><span class=sub>3 条链发射台日均手续费 ${f(rec)} · 基线 ${f(base)}</span></div><div>交易机器人活跃度<b>${n0(BS)}</b><span class=sub>前 3 日均手续费 ${BL?f(BL.rec):'-'} · 基线 ${BL?f(BL.base):'-'} · 截至 ${BL?new Date(BL.asof*1e3).toISOString().slice(5,10):'-'} UTC</span></div><div>pump.fun 指数<b>${n0(P)}</b><span class=sub>见下方 pump.fun 情绪指数</span></div><div>pump.fun 手续费份额（7天）<b>${pumpShare==null?'-':(pumpShare*100).toFixed(1)+'%'}</b><span class=sub>前 7 天 ${pumpShareP==null?'-':(pumpShareP*100).toFixed(1)+'%'}（仅展示，不计分）</span></div>`;
 document.getElementById('chains').innerHTML=Object.keys(ch).map(k=>`<div>${k} 子指数<b style="color:${col(sub[k])}">${n0(sub[k])}</b>${lab(sub[k])}<span class=sub>发射台手续费分 ${n0(ch[k].s)} · 近3日均 ${f(ch[k].rec)} / 基线 ${f(ch[k].base)} · 数据截至 ${new Date(LL[k].days[ch[k].i]*1e3).toISOString().slice(5,10)} UTC</span></div>`).join('');
 document.getElementById('ocomp').innerHTML=`<b>综合指数计算</b>：综合 = 30% 发射台活跃度 + 25% 交易机器人活跃度 + 45% pump.fun 指数（缺数据的分项不计入并按剩余权重归一）。交易机器人活跃度 = 50 × （DefiLlama「Trading App」+「Telegram Bot」类 7 天手续费前 3 的合计日手续费，最近 3 个完整日均值）÷（此前 30 天中位数），截断 0–100；前 3 名单为验证时的排名（Axiom、fomo Wallet、GMGN），表格下方显示每次运行的最新排名。发射台活跃度 = 50 × （SOL+BSC+Robinhood 链上所有 Launchpad 类协议最近 3 个完整日的日均手续费）÷（此前 30 天日手续费中位数），截断 0–100。链子指数：SOL = 50% SOL 发射台手续费分 + 50% pump.fun 指数；BSC / Robinhood = 70% 该链发射台手续费分 + 30% GMGN 毕业速率分（Flap / Pons 当前每小时毕业数 ÷ 其 7 天中位数 × 50；基线不足时只用手续费分）。pump.fun 份额只作参考不计分。DefiLlama 为日数据（UTC），当天不计；若某个主要发射台最新一天为 0（数据延迟），自动回退到上一个完整日。`;
 // 发射台表
 let t='<tr><th>链</th><th>发射台</th><th>最新日手续费</th><th>7 天手续费</th><th>环比前 7 天</th><th>占该链发射台</th><th>GMGN 毕业/小时</th><th>GMGN 新币/小时</th><th>干净占比</th><th>聪明钱参与</th><th>近 30 天走势</th></tr>';
 Object.keys(CL).forEach(k=>{const c=LL[k];if(!c)return;const i=ch[k].i;Object.entries(c.protos).forEach(([n,a])=>{
  const e=D.lp[n],g=e&&lpRate(e,'grate'),l=e&&lpRate(e,'launch'),G=e?e.g:[],w7=s7(a,i),p7=s7(a,i-7),sh=w7/s7(c.total,i);
  const sp=a.slice(-30),mx=Math.max(1,...sp),line=sp.map((v,j)=>`${j*4},${20-18*v/mx}`).join(' ');
  t+=`<tr><td>${k}</td><td><b>${n}</b></td><td>${f(a[i])}</td><td>${f(w7)}</td><td style="color:${w7>=p7?'#3fb950':'#f85149'}">${p7?((w7/p7-1)*100).toFixed(0)+'%':'-'}</td><td>${(sh*100).toFixed(1)}%</td><td>${g?g.now.toFixed(1):(n=='pump.fun'?(D.rows.filter(r=>r.g>=D.updated-86400).length/24).toFixed(1):'-')}</td><td>${l?Math.round(l.now):(n=='pump.fun'&&D.launch.length?Math.round(D.launch[D.launch.length-1].rate):'-')}</td><td>${G.length>=10?Math.round(100*G.filter(x=>x[1]).length/G.length)+'%':(n=='pump.fun'?pct(D.rows.filter(r=>r.g>=D.updated-86400),r=>r.q[8]):'-')}</td><td>${G.length>=10?Math.round(100*G.filter(x=>x[2]).length/G.length)+'%':(n=='pump.fun'?pct(D.rows.filter(r=>r.g>=D.updated-86400),r=>r.q[5]>0):'-')}</td><td><svg width="120" height="22"><polyline fill="none" stroke="#58a6ff" stroke-width="1.5" points="${line}"/></svg></td></tr>`})});
 document.getElementById('lpt').innerHTML=t}

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
 overall(S.v);
 const tq=D.rows.filter(r=>r.g>=end-86400&&r.q&&r.q[8]).sort((a,b)=>(b.a||0)-(a.a||0)).slice(0,20);
 document.getElementById('topq').innerHTML='<tr><th>代币</th><th>毕业时间</th><th>ATH 市值</th><th>当前市值</th><th>持有人</th><th>GMGN</th></tr>'+tq.map(r=>`<tr><td><b>${esc(r.s)}</b> <span class=sub>${esc(r.n)}</span></td><td>${ts(r.g)}</td><td>${f(r.a)}</td><td>${f(r.c)}</td><td>${r.h??'-'}</td><td>${qcell(r)}</td></tr>`).join('')||'<tr><td>暂无 GMGN 数据</td></tr>'}
senti();</script></body></html>'''
open(f'{D}/public/index.html','w').write(html.replace('__DATA__',data.replace('</','<\\/')))
print('built',len(rows))
