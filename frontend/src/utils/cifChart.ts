import type {CifPoint} from '../types/entities';
// Aalen-Johansen 累积发生率阶梯线：从0起跳，按原因分别绘制。
export function cifStepPath(points:CifPoint[],key:'cif_crack'|'cif_corrosion',maxTime:number){
 let d='M70 340';let previous=0;
 for(const p of points){
  const x=70+p.time/maxTime*960;
  d+=` L${x} ${40+(1-previous)*300} L${x} ${40+(1-p[key])*300}`;
  previous=p[key];
 }
 return d;
}
// 存活概率阶梯（与两类CIF互补，S+CIF裂纹+CIF腐蚀=1）。
export function survivalStepPath(points:CifPoint[],maxTime:number){
 let d='M70 40';let previous=1;
 for(const p of points){
  const x=70+p.time/maxTime*960;
  d+=` L${x} ${40+(1-previous)*300} L${x} ${40+(1-p.survival)*300}`;
  previous=p.survival;
 }
 return d;
}
