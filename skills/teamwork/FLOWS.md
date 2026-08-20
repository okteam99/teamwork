# FLOWS

> 流程闭集(红线 R2)与各自 telos。**判定权威 = [docs/prepare.md](./docs/prepare.md)**(关键词 + 复杂度 + 明确度)· 本文件只是视图。
> 🔴 机器层 `flow_type ∈ {Feature, Bug}`;Feature 的重量由**四个维度**决定,不由一个档名决定(用户拍板:「把流程、环节、评审力度三个维度拆开,交给 AI 组装」):
> **D1 规格深度**(none / prd / prd_tech)· **D2 证据门**(开 / 关)· **D3 验证深度**(self / test / test_e2e)· **D4 评审力度**(逐评审点:路数 × 角色 × 模型)· 另加一个**事实开关 UI**(有没有 UI 改动 · 与轻重正交)。
> **链由维度推导**(`derive_chain`)—— 档名(micro / floor / tiny / lite / medium / full)只是**命名的默认元组 + 一句入场问句**,是起手点不是终点:`--dims` 可拧任意一维,`revise-plan` 可在每个 stage 边界改。
> 🔴 **与已退役的 legacy `lite`/`blueprint_lite` 不是一回事**:那两个是**独立转移图**(三份 flow-key 实现曾对同一输入解析出两张不同的图 · 已删净);现在的档**零独立图**,全部走同一条推导 —— 名字回来了,危险没回来。

| 流程 | telos(解决什么) | 链 | 产出 |
|------|----------------|-----|------|
| **Feature · `full`** | 契约面宽 / 影响面广 / 方案分叉多 —— 两路并行冷审的边际收益压得过开销 | goal → (ui_design) → blueprint → dev → review → test → (browser_e2e) → pm_acceptance → ship | 代码 + PRD/TECH/TC + 测试 |
| **Feature · `medium`** | 方案空间值得先写 TECH,但**没到要两路并行冷审** → goal `[fast]`(PL 质疑 + 覆盖方向制并作一路)· blueprint `[architect]` 单路 · 链同 full | 同 full | 代码 + PRD/TECH/TC + 测试 |
| **Feature · `lite`** | **有规格风险要 PRD,但方案空间小到只有一种写法** → 不写 TECH。goal 冷审 0 路缺省(**终确认停等照停** · 用户主权不因降档让渡)· AC↔测试绑定走 PRD 机读块 `acceptance_criteria[].test_refs`(dev 回填真实引用 · test-complete 校验非空**且引用真实存在**) | goal → dev → review → test → pm_acceptance → ship | 代码 + PRD + 测试 |
| **Feature · `tiny`** | 测试证得了实现,但**值得一双眼看 diff** —— 用户拍板形态:直接开发、完成后架构师 review 一下、PM 验收盯 staging 部署 · **零文档**(规格 = dev brief 理解卡) | dev → review〔architect 单路〕 → pm_acceptance → ship | 代码直改 |
| **Feature · `floor`** | 有行为面,但**测试能完全证明它对**、不动契约面 → 最轻的**有证据门**档。与 micro 的分界不是更轻,是**拿什么换轻**:floor 保留全部测试证据门(所以能接真逻辑改动),拿掉的是评审与独立验收口 · 验收在 ship1 MR diff | dev → ship | 代码 + 测试 |
| **Feature · `micro`** | **无行为面**(文案/样式/资源/配置常量/注释)—— 测试无从写起 · 证据门关、准入靠白名单兜 · 用户验收在 ship1 MR diff(R7) | execute → ship | 代码直改 |
| **Bug** | 缺陷已指认 · **diagnose 先行**(根因 + 修复方案经用户确认才许修 · 防修偏)· review 单路 external | diagnose → dev → review → test → pm_acceptance → ship | 修复 + BUG 报告 + 回归测试 |
| **Feature Planning** | 产品方向 → 拆 ROADMAP · 不出代码(R6)· **不进状态机**(init reject · PMO 主对话执行 · 详 [docs/feature-planning.md](./docs/feature-planning.md)) | — | WS + ROADMAP + 全景 |
| **问题排查** | 理解现象 · 只定位根因 · **不进状态机**(mode A 深度版)· 🔴 排查先行律:根因未定的现象类输入一律先到这里 · 闭合再定流程(转 Bug 时结论直供 diagnose 复核不重查) | — | 排查报告 + 后续 todo |

## 关键约束

- 🎚️ **定档判的是「风险的种类」,不是改动大小**:无行为面→micro · 测试能完全证明→floor · 值得一双眼看 diff→tiny · 有规格风险→lite · 值得写 TECH→medium · 两路冷审划算→full。**代码行数从来不是判据**。单源 [goal-stage § 链装配](stages/goal-stage.md)。
- 🎛️ **档是起手点不是终点**:`--dims` 拧任意一维(custom 装配)· 一致性组合机器校验(不连贯直接拒)· 只报个档名不拧 = 退化情形,不是默认姿态。
- 🔗 **装配决策点 = goal 调研后**(prepare 只对齐意图 · 不装配)· **默认执行 · 用户不要求改就生效**。无 goal 的档(micro/floor/tiny)在 prepare 定 —— 那时信息最少,所以它们的入场问句刻意做成**可判**的(有没有行为面 / 测试能不能完全证明)。
- 🔁 **每个 stage 边界都是显式修订点**:`stage-complete` emit 带 `plan_checkpoint`(计划 · 剩余链 · 一句可判问句)· 有新事实用 `revise-plan --evidence` 改、没有就照计划走 · **回显不停等** · **加与减同价**(都只要一行证据)。🔴 **计划可改 · 历史不可改**(已走过的 stage 不许被移出链 · 已交的证据不许回溯放松)。
- 🔴 **降档不降三样**:用户主权(该停的停等照停)· 评审独立性(单路仍须模型错开)· 已产生的证据门。
- micro 涉代码仍必 ship(不停在本地未 push · P0-136)。
- 存量 legacy(M-id)兼容走完 · 新 init 不再产。

## 相关

[SKILL.md](./SKILL.md)(入口 + 暂停点) · [docs/prepare.md](./docs/prepare.md)(判定权威) · [STAGES.md](./STAGES.md)(编排单源)
