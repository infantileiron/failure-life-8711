import csv,io,math
from dataclasses import asdict
from src.models.entities import SpecimenDataset
from src.utils import repository as repo
from src.utils.identity import new_id,now
from src.constants.domain import MAX_SPECIMENS,GROUP_LIMIT,FAILURE_CAUSE_ALIASES

def summary(item):
 rows=item['rows']
 return {k:v for k,v in item.items() if k!='rows'}|{'row_count':len(rows),'groups':sorted({r['group'] for r in rows}),'events':sum(r['event'] for r in rows),'censored':sum(1-r['event'] for r in rows),'events_missing_cause':sum(1 for r in rows if r['event']==1 and r.get('failure_cause') is None),'crack_events':sum(1 for r in rows if r['event']==1 and r.get('failure_cause')=='crack'),'corrosion_events':sum(1 for r in rows if r['event']==1 and r.get('failure_cause')=='corrosion')}
def list_datasets():return [summary(x) for x in repo.all_rows('datasets')]
def detail(id):return repo.get('datasets',id)
def rename(id,data):
 item=repo.get('datasets',id);item['name']=data.name;repo.put('datasets',item);return summary(item)
def create(data):
 reader=csv.DictReader(io.StringIO(data.csv_text.lstrip('﻿')))
 fieldnames=reader.fieldnames or []
 if not {'specimen_id','group','duration_hours','event'}.issubset(fieldnames):raise ValueError('CSV需要specimen_id,group,duration_hours,event；可含censored=1-event与failure_cause（裂纹/腐蚀）')
 has_cause='failure_cause' in fieldnames
 rows=[];seen=set()
 for n,r in enumerate(reader,2):
  if n>MAX_SPECIMENS+1:raise ValueError('最多5000试件')
  id=(r.get('specimen_id') or '').strip();group=(r.get('group') or '').strip()
  try:
   time=float(r.get('duration_hours') or 'nan');event=r.get('event')
   if not math.isfinite(time) or not 0<time<=10000000 or event not in ('0','1') or not id or id in seen or not 1<=len(group)<=30:raise ValueError()
   event=int(event)
   if 'censored' in fieldnames and r.get('censored')!=str(1-event):raise ValueError()
   raw_cause=(r.get('failure_cause') or '').strip() if has_cause else ''
   if event==0:
    # 删失不带原因：带原因的删失记录口径矛盾，拒绝。
    if raw_cause:raise ValueError()
    cause=None
   else:
    # 失效可暂缺原因（旧口径补录场景），缺原因的组竞争风险将标记不可估计。
    cause=FAILURE_CAUSE_ALIASES.get(raw_cause) if raw_cause else None
    if raw_cause and cause is None:raise ValueError()
  except (ValueError,TypeError):raise ValueError(f'第{n}行时间/事件/删失/组别/试件编号/失效原因无效或重复；失效原因仅接受裂纹(crack)、腐蚀(corrosion)，删失不得带原因')
  seen.add(id);rows.append({'specimen_id':id,'group':group,'duration_hours':time,'event':event,'censored':1-event,'failure_cause':cause})
 if len(rows)<2:raise ValueError('至少2个试件')
 if len({r['group'] for r in rows})>GROUP_LIMIT:raise ValueError('最多8个组别')
 item=SpecimenDataset(new_id('ds'),data.name,data.source,rows,now());repo.put('datasets',item);return summary(asdict(item))
