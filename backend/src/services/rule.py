from src.models.entities import CensoringRule
from src.utils import repository as repo
from src.utils.identity import new_id,now

def list_rules():return repo.all_rows('rules')
def create(data):return repo.put('rules',CensoringRule(new_id('rule'),data.name,data.cutoff_hours,data.note,now()))
def apply_rule(rows,cutoff):
 if cutoff is None:return [{**r,'administratively_censored':False} for r in rows]
 out=[]
 for r in rows:
  if r['duration_hours']>cutoff:
   # 行政截止之后的观察不再可见：转删失，且删失不带失效原因。
   out.append({**r,'duration_hours':cutoff,'event':0,'censored':1,'failure_cause':None,'administratively_censored':True})
  else:
   # duration==cutoff 的原始事件（含原因）仍计入。
   out.append({**r,'administratively_censored':False})
 return out
