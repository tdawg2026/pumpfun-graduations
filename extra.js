// ===== 首屏概览 =====
(function(){const OV=window.OV||{},SP=window.SP||{},clp=v=>Math.max(0,Math.min(100,v));
 const pw=Object.fromEntries(W.map(([k,n,w])=>[k,[n,w]]));
 const comps=[['发射台活跃度',OV.A,0.30,'h'],['交易机器人活跃度',OV.BS,0.25,'h']];
 Object.entries(SP).forEach(([k,v])=>comps.push(['pump.fun '+pw[k][0],v,0.45*pw[k][1],['grad','launch'].includes(k)?'h':'q']));
 const wavg=a=>{a=a.filter(x=>x[1]!=null);const w=sum(a.map(x=>x[2]));return w?sum(a.map(x=>x[1]*x[2]))/w:null};
 const heat=wavg([['',OV.A,0.30],['',OV.BS,0.25],['',SP.grad,0.30],['',SP.launch,0.15]]);
 const qual=wavg([['',SP.ath1m,0.35],['',SP.athmed,0.25],['',SP.clean,0.25],['',SP.smart,0.15]]);
 const O=OV.O,lab=v=>v==null?'-':v<40?'冷淡 🥶':v<=60?'中性 😐':'火热 🔥',col=v=>v==null?'#8b949e':v<40?'#58a6ff':v<=60?'#d29922':'#f85149',n0=v=>v==null?'-':v.toFixed(0);
 const hp=(D.hist.idx_combined||{p:[]}).p,td=new Date((D.updated+tz)*1e3).toISOString().slice(0,10);
 const ago=n=>{const d=new Date(Date.parse(td)-n*864e5).toISOString().slice(0,10),x=hp.find(p=>p[0]==d);return x?x[1]:null};
 const y1=ago(1),y7=ago(7),dl=(a,b)=>a==null||b==null?'<span class=sub>无数据</span>':`<span style="color:${a>=b?'#3fb950':'#f85149'}">${a>=b?'+':''}${(a-b).toFixed(0)}</span> <span class=sub>(${b.toFixed(0)})</span>`;
 const ct=comps.filter(c=>c[1]!=null).map(c=>[c[0],c[1],c[2]*(c[1]-50)]).sort((a,b)=>Math.abs(b[2])-Math.abs(a[2])).slice(0,3);
 const ws=sum(comps.filter(c=>c[1]!=null).map(c=>c[2]));
 const top=ct.map(c=>`<div>${c[0]}<b style="color:${c[2]>=0?'#3fb950':'#f85149'}">${c[2]>=0?'+':''}${(c[2]/ws).toFixed(1)}</b><span class=sub>分项 ${n0(c[1])} · 对综合指数的拉动（相对 50）</span></div>`).join('');
 const t1=ct[0],concl=O==null?'数据不足':`今日 Meme 情绪${lab(O).split(' ')[0]}（${n0(O)}），市场热度${lab(heat).split(' ')[0]}、代币质量${lab(qual).split(' ')[0]}${y1!=null?'，较昨日'+(O>=y1?'上升 ':'下降 ')+Math.abs(O-y1).toFixed(0):''}；${t1?'主要'+(t1[2]>=0?'拉动':'拖累')+'来自'+t1[0]:''}。`;
 document.getElementById('hero').innerHTML=`<b>今日概览</b> <span class=sub>综合指数为实时值；昨日 / 7 天前为每日记录（data/daily.json）</span>
 <div style="font-size:16px;margin:8px 0">${concl}</div>
 <div class="kpi"><div>综合指数<b class="big" style="color:${col(O)}">${n0(O)}</b>${lab(O)}</div><div>较昨日<b>${dl(O,y1)}</b></div><div>较 7 天前<b>${dl(O,y7)}</b></div>
 <div>市场热度<b style="color:${col(heat)}">${n0(heat)}</b><span class=sub>发射台 30% · 机器人 25% · 毕业数 30% · 发射数 15%</span></div>
 <div>代币质量<b style="color:${col(qual)}">${n0(qual)}</b><span class=sub>ATH&gt;$1M 占比 35% · ATH 中位数 25% · 干净占比 25% · 聪明钱 15%</span></div></div>
 <div class="sub" style="margin-top:8px">贡献最大的 3 个分项</div><div class="kpi">${top}</div>`})();
// ===== 毕业后表现 =====
function perfTable(){const P=D.ps[document.getElementById('pwin').value],G=[['clean','✅ 干净'],['dirty','⚠️ 不干净'],['nogm','无 GMGN 数据'],['all','全部']];
 const pc=v=>v==null?'-':(v*100).toFixed(0)+'%',rt=v=>v==null?'-':`<span style="color:${v>=0?'#3fb950':'#f85149'}">${v>=0?'+':''}${(v*100).toFixed(0)}%</span>`;
 let t='<tr><th>检查点</th><th>分组</th><th>样本 / 应到</th><th>收益中位数</th><th>上涨占比</th><th>存活率</th><th>最大回撤中位数</th><th>流动性中位数</th></tr>';
 ['1h','6h','24h','7d'].forEach(k=>G.forEach(([g,n],i)=>{const s=P[k+'_'+g];if(!s)return;const ok=s.n>=20;
  t+=`<tr${i==0?' style="border-top:2px solid #30363d"':''}><td>${i==0?'+'+k:''}</td><td>${n}</td><td>${s.n} / ${s.due}</td>`+(ok?`<td>${rt(s.ret)}</td><td>${pc(s.win)}</td><td>${pc(s.alive)}</td><td>${pc(s.mdd)}</td><td>${s.nliq>=20?f(s.liq):'<span class=sub>样本不足('+s.nliq+')</span>'}</td>`:`<td colspan=5 class=sub>样本不足（${s.n} &lt; 20）${s.due?'，检查点会随时间补齐':''}</td>`)+'</tr>'}));
 document.getElementById('perf').innerHTML=t}
document.getElementById('pwin').onchange=perfTable;perfTable();
// ===== 榜单 =====
let RK='best';
function rankTable(){const win=+document.getElementById('rwin').value,lm=+document.getElementById('liqmin').value||0;
 let a=D.rows.filter(r=>r.g>=D.updated-win);
 const desc={best:'按毕业后 ATH ÷ 毕业市值倍数排序（毕业 ≥2 小时）；高倍数可能来自薄流动性被刷高，请结合流动性看。',trade:`当前流动性 ≥ ${f(lm)} 的代币，按当前市值排序。`,clean:`GMGN 干净且当前流动性 ≥ ${f(lm)}，按当前市值排序。`};
 if(RK=='best')a=a.filter(r=>r.post&&r.g0&&r.g<=D.updated-7200).sort((x,y)=>y.post/y.g0-x.post/x.g0);
 else a=a.filter(r=>(r.lq||0)>=lm&&(RK=='trade'||(r.q&&r.q[8]))).sort((x,y)=>(y.c||0)-(x.c||0));
 document.getElementById('rkdesc').textContent=desc[RK]+` 共 ${a.length} 个，显示前 30。`;
 const rt=v=>v==null?'-':`<span style="color:${v>=0?'#3fb950':'#f85149'}">${v>=0?'+':''}${(v*100).toFixed(0)}%</span>`;
 document.getElementById('rank').innerHTML='<tr><th>代币</th><th>毕业时间</th><th>毕业市值</th><th>内盘 ATH</th><th>毕业后 ATH</th><th>倍数</th><th>当前市值</th><th>流动性</th><th>+1h</th><th>+24h</th><th>GMGN</th><th>链接</th></tr>'+
  a.slice(0,30).map(r=>`<tr><td><b>${esc(r.s)}</b> <span class=sub>${esc(r.n)}</span></td><td>${ts(r.g)}</td><td>${f(r.g0)}</td><td>${f(r.pre)}</td><td>${f(r.post)}</td><td>${r.post&&r.g0?(r.post/r.g0).toFixed(1)+'x':'-'}</td><td>${f(r.c)}</td><td>${f(r.lq)}</td><td>${rt(r.cp&&r.cp['1h'])}</td><td>${rt(r.cp&&r.cp['24h'])}</td><td>${qcell(r)}</td><td><a href="https://dexscreener.com/solana/${r.m}" target="_blank">dex</a></td></tr>`).join('')||'<tr><td class=sub>暂无符合条件的代币</td></tr>'}
document.querySelectorAll('button.rk').forEach(b=>b.onclick=()=>{document.querySelectorAll('button.rk').forEach(x=>x.classList.remove('on'));b.classList.add('on');RK=b.dataset.r;rankTable()});
document.getElementById('rwin').onchange=rankTable;document.getElementById('liqmin').oninput=rankTable;rankTable();
// ===== 覆盖率 =====
(function(){const C=D.cov,p=(a,b)=>b?Math.round(100*a/b)+'%':'-',U=ts(D.updated),ok=(a,b,min)=>b<min?' <span class=sub>⚠️ 样本不足</span>':'';
 const P=D.ps.all,cp=k=>P[k+'_all'];
 const rows=[['毕业时间（GeckoTerminal）',p(C.grad,C.n),C.n,U],['持有人数（Helius，查一次）',p(C.hold,C.n),C.n,U],
  ['GMGN 质量快照（近 24h 毕业）',p(C.gm24[0],C.gm24[1])+ok(C.gm24[0],C.gm24[1],10),C.gm24[1],U],
  ['流动性（近 48h 毕业）',p(C.liq48[0],C.liq48[1]),C.liq48[1],C.liq_at?ts(C.liq_at):'-'],
  ...['1h','6h','24h','7d'].map(k=>[`毕业后 +${k} 检查点`,p(cp(k).n,cp(k).due)+ok(cp(k).n,cp(k).due,20),cp(k).due,U]),
  ['pump.fun 发射速率样本（近 7 天）',D.launch.length?'-':'无',D.launch.length,D.launch.length?ts(D.launch[D.launch.length-1].ts):'-'],
  ['DefiLlama 手续费（发射台 / 机器人）','UTC 日粒度','-',C.llama?ts(C.llama):'-'],
  ['pump.fun 指数基线（小时）',window.NB>=24?'正常':'不足 24h',window.NB,U],
  ['每日历史记录',`${C.pump_days} 天 pump.fun 完整日`+(C.pump_days<30?' <span class=sub>⚠️ 分位需 ≥30 天</span>':''),C.hist_days,U]];
 document.getElementById('cov').innerHTML='<tr><th>指标</th><th>覆盖率</th><th>样本量</th><th>最后更新</th></tr>'+rows.map(r=>`<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td><td>${r[3]}</td></tr>`).join('')+
  `<tr><td colspan=4 class=sub>毕业后表现数据从 ${C.perf_first?ts(C.perf_first):'-'} 毕业的代币开始，共 ${C.perf_n} 个</td></tr>`})();
