import hashlib,json
from src.services.km import kaplan_meier
from src.services.logrank import log_rank
from src.services.competing_risks import aalen_johansen
from src.services.rule import apply_rule
from src.constants.domain import FAILURE_CAUSE_LABELS

def analyze(rows,rule,study):
 included=[r for r in rows if r['group'] in (study['group_a'],study['group_b'])]
 observed=apply_rule(included,rule['cutoff_hours']);a=[r for r in observed if r['group']==study['group_a']];b=[r for r in observed if r['group']==study['group_b']]
 groups=[]
 for rows_g in (a,b):
  group={'group':rows_g[0]['group'] if rows_g else '',**kaplan_meier(rows_g)}
  group['competing_risks']=aalen_johansen(rows_g)
  groups.append(group)
 cause_summary={
  'causes':list(FAILURE_CAUSE_LABELS),
  'cause_labels':dict(FAILURE_CAUSE_LABELS),
  'cause_counts':{cause:sum(g['competing_risks']['cause_counts'][cause] for g in groups) for cause in FAILURE_CAUSE_LABELS},
  'events_missing_cause':sum(g['competing_risks']['events_missing_cause'] for g in groups),
  'all_estimable':all(g['competing_risks']['estimable'] for g in groups),
 }
 return {'groups':groups,'cause_summary':cause_summary,'logrank':log_rank(a,b),'rule':rule,'study':study,'included':len(included),'excluded_other_groups':len(rows)-len(included),'administratively_censored':sum(r['administratively_censored'] for r in observed),'observations':observed,'checksum':hashlib.sha256(json.dumps({'rows':rows,'rule':rule,'study':study},sort_keys=True).encode()).hexdigest(),'limitations':['同刻失效与删失均进入事件前风险集，计算失效后再从风险集移除删失','KM假设独立、非信息右删失；不能用未失效试件的观察截止时间当失效寿命','Greenwood方差和逐点log-log区间非同时置信带；S=1且无事件时区间留空，S=0末端方差按极限置0','中位寿命未达到返回空值；全删失只说明观测内未记录失效，不证明无限寿命','log-rank渐近卡方df1；零方差不可估计；小样本/不同比例风险尤其交叉曲线时应谨慎解释','裂纹与腐蚀是互斥终点：Aalen-Johansen把另一类失效作为竞争事件保留在风险集内参与跳变，绝不当删失处理','同刻两类事件共用同一份事前风险集；每个事件时刻的逐时贡献为S(t−)×d_k/n，两类增量与存活概率满足S+CIF裂纹+CIF腐蚀=1','行政截止之后的记录按无原因右删失处理，截止时刻原始失效事件仍计入；删失记录不携带失效原因','缺少失效原因的旧数据只标记累积发生率不可估计，不填补、不反推原因，已有历史运行结果不改写','不估计原因别风险比/子分布风险比，不把组间p值替代材料采购或工程可靠性认证']}
