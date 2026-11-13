import type {GroupCurve} from '../types/entities';
import {cifStepPath,survivalStepPath} from '../utils/cifChart';
import {percent} from '../utils/format';

export default function CompetingRisks({groups}:{groups:GroupCurve[]}){
 return <section className="paper competing-block">
  <h2>裂纹 / 腐蚀互斥终点 · Aalen–Johansen 累积发生率</h2>
  <p className="method-line">两类失效互为竞争事件：另一类失效保留在事前风险集内参与跳变，不作删失；同刻事件共用同一风险集。逐时增量 = S(t−) × d<sub>k</sub>/n，恒有 S(t) + CIF裂纹 + CIF腐蚀 = 1。</p>
  {groups.map((g,i)=>{
   const cr=g.competing_risks;
   if(!cr)return <div className="diagnostic-note" key={g.group}>{g.group}组：历史运行结果不含竞争风险分析，已有结果不改写；请重新运行以估计累积发生率。</div>;
   if(!cr.estimable)return <div className="diagnostic-note" key={g.group}>{g.group}组：{cr.warning}</div>;
   const maxTime=Math.max(1,...cr.curve.map(p=>p.time));
   const last=cr.curve[cr.curve.length-1];
   return <article className="cif-card" key={g.group}>
    <div className="chart-title"><b>{g.group}组 · 累积发生概率（n={g.n}）</b><span>裂纹{cr.cause_counts.crack}件 / 腐蚀{cr.cause_counts.corrosion}件{cr.events_missing_cause?` / 缺原因${cr.events_missing_cause}件`:''}</span></div>
    <div className="chart-scroll"><svg viewBox="0 0 1100 410" role="img" aria-label={`${g.group}组裂纹与腐蚀累积发生率`}>
     {[0,.25,.5,.75,1].map(s=><g key={s}><line x1="70" x2="1030" y1={40+(1-s)*300} y2={40+(1-s)*300} className="grid-line"/><text x="22" y={44+(1-s)*300}>{Math.round(s*100)}%</text></g>)}
     {[0,.2,.4,.6,.8,1].map(f=><text x={70+f*960} y="370" textAnchor="middle" key={f}>{(f*maxTime).toFixed(0)}</text>)}
     <path d={survivalStepPath(cr.curve,maxTime)} className="cif-line cif-survival"/>
     <path d={cifStepPath(cr.curve,'cif_crack',maxTime)} className={`cif-line cif-crack curve-${i}`}/>
     <path d={cifStepPath(cr.curve,'cif_corrosion',maxTime)} className={`cif-line cif-corrosion curve-${i}`}/>
     <text x="1000" y="399">观察时间 / h</text>
    </svg></div>
    <div className="chart-legend"><span><i className="swatch survival"/>总体存活 S(t)</span><span><i className="swatch crack"/>裂纹 CIF（末点 {percent(last.cif_crack)}）</span><span><i className="swatch corrosion"/>腐蚀 CIF（末点 {percent(last.cif_corrosion)}）</span><span><i className="swatch total"/>S + 两类CIF = {percent(last.identity_gap)}</span></div>
    {cr.warning&&<div className="diagnostic-note">{cr.warning}</div>}
    <div className="table-scroll"><table>
     <thead><tr><th>时刻 h</th><th>事前风险集 n</th><th>裂纹 d₁ / 腐蚀 d₂</th><th>删失</th><th>裂纹逐时增量</th><th>腐蚀逐时增量</th><th>CIF裂纹</th><th>CIF腐蚀</th><th>S(t)</th><th>S+CIF₁+CIF₂</th></tr></thead>
     <tbody>{cr.curve.slice(0,15).map(p=><tr key={p.time}>
      <td>{p.time}</td><td>{p.at_risk}</td><td>{p.d_crack} / {p.d_corrosion}</td><td>{p.censored}</td>
      <td>{p.cif_increment_crack.toFixed(5)}</td><td>{p.cif_increment_corrosion.toFixed(5)}</td>
      <td>{p.cif_crack.toFixed(5)}</td><td>{p.cif_corrosion.toFixed(5)}</td><td>{p.survival.toFixed(5)}</td><td>{p.identity_gap.toFixed(6)}</td>
     </tr>)}</tbody>
    </table></div>
    <small>预览前15个观察时刻，完整逐时贡献随批准报告 CSV 导出。同刻两类事件共用事前风险集，另一类失效未作删失。</small>
   </article>;
  })}
 </section>;
}
