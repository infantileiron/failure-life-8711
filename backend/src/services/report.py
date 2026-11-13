import csv,io
from fastapi import HTTPException
from src.models.entities import Report
from src.config.settings import ARTIFACT_DIR
from src.utils import repository as repo
from src.utils.identity import new_id,now

def safe_cell(value):return "'"+value if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')) else value
def list_reports():return repo.all_rows('reports')
def create(data):
 run,review=repo.get('runs',data.run_id),repo.get('reviews',data.review_id)
 if review['status']!='approved' or review['run_id']!=run['id'] or run['status']!='completed':raise ValueError('报告必须引用该运行已通过的复核')
 report=repo.put('reports',Report(new_id('rpt'),data.run_id,data.review_id,data.title,now()));ARTIFACT_DIR.mkdir(parents=True,exist_ok=True);(ARTIFACT_DIR/(report['id']+'.csv')).write_text(download(report['id']),encoding='utf-8');return report
def download(id):
 report=repo.get('reports',id);run=repo.get('runs',report['run_id']);r=run['result']
 if repo.get('reviews',report['review_id'])['status']!='approved':raise HTTPException(403,'复核未通过')
 out=io.StringIO();w=csv.writer(out);lr=r['logrank']
 cs=r.get('cause_summary')
 w.writerow(['report','included','excluded_other_groups','administratively_censored','chi_square_df1','p_value','logrank_estimable','checksum']);w.writerow([safe_cell(report['title']),r['included'],r['excluded_other_groups'],r['administratively_censored'],lr['chi_square'],lr['p_value'],lr['estimable'],r['checksum']])
 if cs:
  w.writerow([]);w.writerow(['competing_risks_estimable','crack_events','corrosion_events','events_missing_cause'])
  w.writerow([cs['all_estimable'],cs['cause_counts'].get('crack',0),cs['cause_counts'].get('corrosion',0),cs['events_missing_cause']])
 w.writerow([]);w.writerow(['group','time_hours','at_risk','events','censored','risk_after','survival','greenwood_variance','ci95_low','ci95_high','median_hours'])
 for g in r['groups']:
  for p in g['curve']:w.writerow([safe_cell(g['group']),p['time'],p['at_risk'],p['events'],p['censored'],p['risk_after'],p['survival'],p['variance'],p['ci95_low'],p['ci95_high'],g['median_hours']])
 w.writerow([]);w.writerow(['event_time','n_a','n_b','d_a','d_b','expected_a','observed_minus_expected_a','variance_contribution'])
 for p in lr['contributions']:w.writerow([p[k] for k in ['time','n_a','n_b','d_a','d_b','expected_a','observed_minus_expected_a','variance_contribution']])
 # Aalen-Johansen 逐时贡献：两类互斥终点，同刻共用事前风险集，另一类失效不作删失。
 # 旧格式运行结果无 competing_risks 时整段省略，保持历史报告导出格式不变。
 cr_groups=[g for g in r['groups'] if g.get('competing_risks')]
 if cr_groups:
  w.writerow([]);w.writerow(['aalen_johansen_group','estimable','time_hours','at_risk_before_events','d_crack','d_corrosion','censored','cif_increment_crack','cif_increment_corrosion','cif_crack','cif_corrosion','survival','survival_plus_cif_total'])
  for g in cr_groups:
   cr=g['competing_risks']
   if not cr['estimable']:
    w.writerow([safe_cell(g['group']),False,'不可估计：'+cr['warning']]);continue
   for p in cr['curve']:
    w.writerow([safe_cell(g['group']),True,p['time'],p['at_risk'],p['d_crack'],p['d_corrosion'],p['censored'],p['cif_increment_crack'],p['cif_increment_corrosion'],p['cif_crack'],p['cif_corrosion'],p['survival'],p['identity_gap']])
 return '﻿'+out.getvalue()
