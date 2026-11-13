import math
from src.constants.domain import FAILURE_CAUSES,FAILURE_CAUSE_LABELS

# Aalen-Johansen 多终点累积发生率（竞争风险）。
# 裂纹、腐蚀是互斥终点：一类失效的试件不能再经历另一类，也不能当另一类的删失，
# 而是在该时刻从事前风险集中移除（体现为总体存活概率 S(t-) 同时受两类终点作用）。
# 同刻事件共用同一份事前风险集 n；行政截止记录在调用前已转为无原因删失。
def aalen_johansen(rows):
 if not rows:raise ValueError('组内没有试件')
 if any(not math.isfinite(r['duration_hours']) or r['duration_hours']<=0 or r['event'] not in (0,1) for r in rows):raise ValueError('生存观测时间/事件无效')
 events_total=sum(r['event'] for r in rows)
 missing_cause=sum(1 for r in rows if r['event']==1 and r.get('failure_cause') is None)
 cause_counts={cause:sum(1 for r in rows if r['event']==1 and r.get('failure_cause')==cause) for cause in FAILURE_CAUSES}
 # 旧数据升级后失效行缺原因：原因不可识别，CIF 不可估计，不硬算、不把另一类当删失。
 estimable=events_total==0 or missing_cause==0
 if not estimable:
  return {'estimable':False,'causes':list(FAILURE_CAUSES),'cause_labels':FAILURE_CAUSE_LABELS,'cause_counts':cause_counts,'events_missing_cause':missing_cause,'curve':[],'warning':f'{missing_cause}件失效记录缺少失效原因（旧数据升级），裂纹/腐蚀累积发生率不可估计；请补录原因后重新运行，已有历史结果不改写'}
 times=sorted({r['duration_hours'] for r in rows})
 survival=1.;cif={cause:0. for cause in FAILURE_CAUSES};curve=[]
 for t in times:
  at_risk=sum(r['duration_hours']>=t for r in rows)
  d_censored=sum(r['duration_hours']==t and r['event']==0 for r in rows)
  d_by_cause={cause:sum(1 for r in rows if r['duration_hours']==t and r['event']==1 and r.get('failure_cause')==cause) for cause in FAILURE_CAUSES}
  events=sum(d_by_cause.values())
  # 同刻事件共用事前风险集：先在完整 n 上估计各原因增量，再统一更新。
  increments={}
  for cause in FAILURE_CAUSES:
   increment=survival*d_by_cause[cause]/at_risk if at_risk else 0.
   cif[cause]+=increment;increments[cause]=increment
  if events:survival*=1-events/at_risk
  total_cif=sum(cif.values())
  curve.append({'time':t,'at_risk':at_risk,'events':events,'censored':d_censored,
   'd_crack':d_by_cause['crack'],'d_corrosion':d_by_cause['corrosion'],
   'risk_after':at_risk-events-d_censored,
   'cif_crack':cif['crack'],'cif_corrosion':cif['corrosion'],
   'cif_increment_crack':increments['crack'],'cif_increment_corrosion':increments['corrosion'],
   'survival':survival,'cif_total':total_cif,
   'identity_gap':survival+total_cif})
 warning='' if events_total else '全删失：观测内未记录任何终点事件，两类累积发生率均为0；不能宣称裂纹或腐蚀不会发生'
 return {'estimable':True,'causes':list(FAILURE_CAUSES),'cause_labels':dict(FAILURE_CAUSE_LABELS),
  'cause_counts':cause_counts,'events_missing_cause':missing_cause,'curve':curve,'warning':warning}
