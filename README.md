# 砾川材料 · 试件失效寿命复核

为砾川材料17人试验组正确记录右删失试件，用KM生存曲线、Greenwood方差和逐时log-rank风险集复核A/B加工批，并以Aalen–Johansen分别估计裂纹、腐蚀两类互斥终点的累积发生率。

## 场景

上游 `material_life_202611.csv` 包含360件模拟试件的观察时间和失效状态。团队原来用均值寿命表，把未失效试件的截止时间当失效寿命、同刻风险集容易错算、两组删失差异缺少说明。裂纹与腐蚀都会让试件退出试验，旧KM曲线只回答“是否失效”，回答不了裂纹的实际发生概率。本工程替代试件校验、删失口径锁定、统计计算与复核归档，下游工艺组据此安排后续试验讨论，不用于工程可靠性认证。

六实体：SpecimenDataset试件数据、CensoringRule删失口径、SurvivalStudy生存研究、SurvivalRun计算运行、LifeReview寿命复核、Report报告。六页：寿命手册、试件观测、删失口径、生存研究、曲线与风险集、寿命复核。总览/结果复用SurvivalChart与LifeSummary。

## 快速启动

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

前端 http://localhost:18220 ，API http://localhost:19220/docs ，PostgreSQL端口17720。恰好frontend/backend/worker/db/redis五服务全部配置健康检查；数据库、Redis队列和共享产物用命名卷。清理测试数据：`docker compose down -v --remove-orphans`。

| 账号 | 角色 | 权限 |
|---|---|---|
| admin@lichuan.test | admin / 材料试验复核人 | 全实体、批准/退回复核、审计 |
| analyst@lichuan.test | analyst / 寿命分析员 | 导入、口径、研究、运行、提审、生成报告 |
| viewer@lichuan.test | viewer / 工艺观察员 | 六实体只读、下载已批准报告 |

统一演示密码 `Life2026!`。PBKDF2密码哈希、JWT HS256、actor审计、全局错误响应、10任务队列配额。匿名401、越权写入403、重复审批409。开发密钥由JWT_SECRET配置。

## 一天的工作剧本

1. 09:00 分析员核查360件试件，确认A/B各180件与事件/删失人数。
2. 09:05 上传material_life_202611.csv，保留文件名，检查时间单位小时与唯一specimen_id。
3. 09:10 锁定240小时行政截止；记录独立、非信息右删失假设，不把未失效当失效。
4. 09:15 创建A/B加工批研究；其他组排除数量将在结果公开。
5. 09:20 Redis排队，独立Python worker计算KM、Greenwood与log-rank，结果持久化PostgreSQL及共享产物。
6. 09:25 看两条阶梯生存曲线、逐点区间与删失刻线，查看未达到中位寿命的组。
7. 09:30 逐时核对事件前风险集、观察/期望事件与方差；同刻删失在事件风险集中；另按Aalen–Johansen核对两类终点逐时增量与S+CIF₁+CIF₂=1。
8. 09:40 提交复核，材料复核人批准后生成报告，观察员下载完整证据CSV（含Aalen–Johansen逐时贡献）。

## 输入与删失规则

CSV必需列specimen_id,group,duration_hours,event，可选censored、failure_cause。event只能0或1；若提供censored须等于1−event。failure_cause仅event=1行填写，接受裂纹/腐蚀（crack/corrosion，中英文均可，归一为英文代码）；event=0的删失行不得带原因，带原因即拒绝。失效行可暂缺原因（旧口径补录场景），缺原因的组其竞争风险累积发生率标记为不可估计。时间为正有限小时且≤10,000,000，最多5000试件/8组。空字段、短行、重复ID、非有限时间、矛盾状态、非法原因拒绝。两组必须不同且存在。

所有试件从t=0进入，只支持右删失，不支持左截断、区间删失。行政截止为空则保留原始观察；duration>cutoff的记录转为cutoff时刻删失并清除失效原因（行政删失不带原因），duration=cutoff的原始事件（含原因）仍计入，修改数量单列披露。原始数据不覆盖，口径及输入哈希与每次结果固定保存。

## 竞争风险：Aalen–Johansen两类互斥终点

裂纹（crack）与腐蚀（corrosion）是互斥终点：试件因其中一类退出后不再暴露于另一类。另一类失效**绝不作为删失**，而是作为竞争事件保留在事前风险集n中，在同一时刻共同决定总体存活概率的跳变。

对每个观察时刻t，n为duration≥t的事前风险集（同刻两类事件与同刻删失共用同一份n），d₁、d₂为该时刻裂纹、腐蚀事件数，d=d₁+d₂。先在完整n上计算逐时贡献，再统一更新：

- 原因k累积发生率增量 ΔFₖ(t)=S(t−)×dₖ/n，Fₖ(t)=Fₖ(t−)+ΔFₖ(t)
- 总体存活 S(t)=S(t−)×(1−d/n)
- 恒等式逐点成立：S(t)+F裂纹(t)+F腐蚀(t)=1

行政截止之后按无原因右删失处理，进入风险集但不产生任何终点增量。单原因极限下F裂纹=1−KM，可与KM互相校验。全删失时两类CIF观测内均为0并给警告，不宣称终点不会发生。

旧数据升级：历史数据集的失效行若没有failure_cause，启动时幂等补为None，只影响后续新运行；这些组的CIF返回estimable=false与中文原因说明，不填补、不反推原因。已有运行、复核、报告载荷一律不改写。前端在曲线与风险集页展示两组CIF阶梯图与逐时贡献表（事前风险集、d₁/d₂、两类增量、S与恒等式核验）；不可估计时整组显示原因提示。批准报告CSV新增原因汇总段与Aalen–Johansen逐时贡献段，历史格式结果导出时整段省略。

## KM与Greenwood

对每个观察时刻t，n为duration≥t的试件数，d为该时刻失效数，c为该时刻删失数。先计算事件前风险集，再更新S(t)=S(t−)×(1−d/n)，之后风险集移除d+c。同刻事件和删失不能先删失后算事件。

Greenwood方差为S²Σ[d/(n(n−d))]。S在(0,1)时给逐点log-log 95%区间；不是同时置信带。S=1且尚无事件时区间留空；末端d=n使S=0，和式本项不可定义（greenwood_sum=null），方差按末端极限记0，区间为[0,0]并标terminal_all_failed。中位为首次S≤0.5的时刻；未达到返回null，不能填0。全删失KM观测内点估计1，但失效分布/中位无法据此估计，不能宣称无限寿命。

## 两组log-rank

只在合并事件时刻计算n₁/n₂、d₁/d₂，E₁=d×n₁/n。方差贡献Vₜ=n₁n₂d(n−d)/(n²(n−1))，n≤1时贡献0；χ²=(Σ(d₁−E₁))²/ΣVₜ，df=1，p=erfc(√(χ²/2))。同刻删失仍在风险集中，ties使用超几何有限总体修正。

无事件或总方差0时χ²和p返回null，并说明不可估计，不硬填p=1。独立非信息删失是关键假设；小样本渐近近似有限，曲线交叉或非比例风险可能抵消差异，不能用p大证明两组相同。未估计风险比，不把p值替代材料决策或认证。

结果含两组完整逐时KM、风险集、失效/删失、Greenwood方差和区间、中位、log-rank逐时贡献、Aalen–Johansen两类终点逐时贡献与累积发生率、口径、排除数及SHA256。报告必须引用该运行已批准复核，CSV包含完整记录，文本公式前缀保护。

## 技术与结构

| 层 | 技术 |
|---|---|
| 前端 | React18 / TypeScript5.7 / Vite6 / Nginx1.28 |
| 后端 | Python3.12 / FastAPI / psycopg3 |
| 算法 | Python math标准库，KM/Greenwood/log-rank/Aalen–Johansen |
| 存储与异步 | PostgreSQL16 / Redis7.4 / 独立worker |

75职责源文件（新增后端services/competing_risks.py、前端components/CompetingRisks.tsx与utils/cifChart.ts）。后端src/{routes,controllers,services,models,schemas,middlewares,utils,constants,config}，前端src/{api,stores,types,components/common,hooks,pages,router,utils,constants}。业务表TEXT主键+JSON文本载荷；DDL在backend/migrations/001_initial.sql，事务级advisory lock保护首次并发建表；启动时幂等升级旧数据集行补failure_cause=None，不触碰运行/复核/报告。

共享枚举：后端src/constants/enums.py角色/运行/复核，src/constants/domain.py事件与配额；前端src/constants/enums.ts。模型/schema/前端类型分别在models/entities.py、schemas/entities.py、frontend/src/types/entities.ts。

Seed固定2301生成360件、A/B两组，失效时间和独立观察截止随机模拟并按5小时分辨率离散，含并列事件/删失；失效行由独立随机流2302按A组偏裂纹、B组偏腐蚀分配互斥原因，删失行无原因。SEED_DEMO=true自动seed，自然键insert-only，重复运行不新增、不覆盖手工修改；失败记录日志。演示数据不代表真实加工质量。

环境变量DATABASE_URL、REDIS_URL、JWT_SECRET、SEED_DEMO、TASK_MODE、ARTIFACT_DIR及端口/口令见.env.example。前端npm ci使用已验证锁版本，只改项目根包名。后端本地开发配置PostgreSQL/Redis并安装requirements，运行uvicorn src.main:app --reload；前端npm ci && npm run dev，通过Nginx或/api开发代理访问后端。

## 已知边界

数据全部模拟，删失机制的非信息性需要试验组判断，应用不自动证明。未实现原因别风险比/子分布风险比/精确小样本检验/左截断；Aalen–Johansen仅给累积发生率点估计，未含CIF方差与区间。缺失效原因的旧数据只能标记CIF不可估计，不能反推原因。Redis出队后worker强杀无自动重投，需要重新提交；JSON载荷无多人编辑乐观锁和迁移回滚。默认账号仅本地演示。

真实容器、HTTP、手算oracle、浏览器主流程及截图在批次test-artifacts/gb-2301，源码不含测试截图/日志/报告。

## License

MIT，见LICENSE。
