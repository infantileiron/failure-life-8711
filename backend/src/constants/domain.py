GROUP_LIMIT=8
MAX_SPECIMENS=5000
EVENT_CODES=(0,1)
CENSORING_METHOD='independent_right_censoring'
# 两类互斥失效终点：裂纹与腐蚀。试件只能因其中一类退出试验。
FAILURE_CAUSES=('crack','corrosion')
FAILURE_CAUSE_LABELS={'crack':'裂纹','corrosion':'腐蚀'}
# CSV failure_cause 列接受英文代码或中文原因，统一归一到英文代码。
FAILURE_CAUSE_ALIASES={'crack':'crack','裂纹':'crack','corrosion':'corrosion','腐蚀':'corrosion'}
