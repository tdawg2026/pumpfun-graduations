#!/usr/bin/env python3
import json,os,time
D=os.path.dirname(os.path.abspath(__file__))
db=list(json.load(open(f'{D}/data/tokens.json')).values()); meta=json.load(open(f'{D}/data/meta.json'))
rows=[{'m':t['mint'],'s':t.get('symbol') or '','n':(t.get('name') or '')[:40],'g':t.get('grad') or t['created'],
       'a':t.get('ath_mcap'),'c':t.get('mcap'),'f':t.get('first_seen'),'h':t.get('holders_now'),'ha':t.get('holders_at')} for t in db]
data=json.dumps({'rows':rows,'updated':meta['updated']},separators=(',',':'))
html=r'''<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>pump.fun 每小时毕业代币</title><style>
body{background:#0d1117;color:#e6edf3;font:14px -apple-system,"PingFang SC",sans-serif;margin:0;padding:16px;max-width:1200px;margin:auto}
h1{font-size:20px;margin:4px 0}.sub{color:#8b949e;font-size:12px}.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;margin:12px 0;overflow-x:auto}
button{background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:4px 12px;cursor:pointer}button.on{background:#238636}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:5px 8px;border-bottom:1px solid #21262d;text-align:right;white-space:nowrap}
th{cursor:pointer;color:#8b949e;position:sticky;top:0;background:#161b22}td:first-child,th:first-child{text-align:left}a{color:#58a6ff;text-decoration:none}
.kpi{display:flex;gap:10px;flex-wrap:wrap}.kpi div{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:8px 12px}.kpi b{display:block;font-size:18px}
#chart{width:100%;height:220px}.scroll{max-height:520px;overflow:auto}.note{color:#8b949e;font-size:12px;line-height:1.6}</style></head><body>
<h1>pump.fun 每小时内盘打满（毕业）代币</h1><div class="sub">时间均为 UTC+7 · 最后更新：<span id="upd"></span></div>
<div class="card"><button data-h="24" class="on">24 小时</button> <button data-h="168">7 天</button>
<div class="kpi" id="kpi" style="margin-top:10px"></div><svg id="chart"></svg></div>
<div class="card"><b>每小时汇总</b><div class="scroll"><table id="sum"></table></div></div>
<div class="card"><b>毕业代币列表</b> <span class="sub">点击表头排序</span><div class="scroll"><table id="tok"></table></div></div>
<div class="card note">数据说明：代币列表、ATH 市值和当前市值来自 pump.fun 前端接口（frontend-api-v3，非官方，单次最多翻 1000 条，所以首次抓取只能完整覆盖约最近 20 小时，更早的小时数偏少；之后每次运行会累积，最多保留 7 天）。毕业时间取 GeckoTerminal 上 PumpSwap 池子的创建时间。ATH 市值是 pump.fun 记录的历史最高（含内盘阶段），按 10 亿总供应计算，美元计价；流动性很薄的代币可能被刷高。持有人数通过 Helius RPC（getProgramAccountsV2）统计余额大于 0 的账户数（含池子/合约账户），每个代币只查一次、不再更新：新毕业代币一般在毕业后 1 小时内查询，数字下方为查询时间（UTC+7）。早期已收录的代币查询时间可能晚于毕业较久。页面由 GitHub Actions 每小时自动更新。</div>
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
 let t='<tr><th>小时</th><th>数量</th><th>ATH 中位数</th><th>ATH 最高</th><th>&gt;$1M</th><th>&gt;$10M</th><th>持有人中位数</th></tr>';
 hs_.slice().reverse().forEach(h=>{const a=by[h].map(r=>r.a||0);t+=`<tr><td>${hs(h)}</td><td>${a.length}</td><td>${f(med(a))}</td><td>${a.length?f(Math.max(...a)):'-'}</td><td>${a.filter(x=>x>1e6).length}</td><td>${a.filter(x=>x>1e7).length}</td><td>${med(by[h].map(r=>r.h).filter(x=>x!=null))??'-'}</td></tr>`});
 document.getElementById('sum').innerHTML=t;
 rs.sort((x,y)=>{const a=x[sk]??-1,b=y[sk]??-1;return (a>b?1:a<b?-1:0)*sd});
 const cols=[['s','代币'],['g','毕业时间'],['a','ATH 市值'],['c','当前市值'],['h','持有人（首次查询）']];
 t='<tr>'+cols.map(([k,n])=>`<th data-k="${k}">${n}${sk==k?(sd>0?' ▲':' ▼'):''}</th>`).join('')+'<th>链接</th></tr>';
 rs.forEach(r=>{t+=`<tr><td title="${r.m}"><b>${esc(r.s)}</b> <span class="sub">${esc(r.n)}</span></td><td>${ts(r.g)}</td><td>${f(r.a)}</td><td>${f(r.c)}</td><td title="查询时间 ${r.ha?ts(r.ha):'-'}">${r.h??'-'}${r.ha?'<div class=sub>'+ts(r.ha)+'</div>':''}</td><td><a href="https://pump.fun/coin/${r.m}" target="_blank">pump</a> · <a href="https://dexscreener.com/solana/${r.m}" target="_blank">dex</a></td></tr>`});
 const tb=document.getElementById('tok');tb.innerHTML=t;tb.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{const k=th.dataset.k;sd=sk==k?-sd:-1;sk=k;render()})}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
document.querySelectorAll('button').forEach(b=>b.onclick=()=>{document.querySelectorAll('button').forEach(x=>x.classList.remove('on'));b.classList.add('on');H=+b.dataset.h;render()});render();</script></body></html>'''
open(f'{D}/public/index.html','w').write(html.replace('__DATA__',data.replace('</','<\\/')))
print('built',len(rows))
