# FLOWS

> 流程闭集(红线 R2)与各自 telos。**判定权威 = [docs/prepare.md](./docs/prepare.md)**(关键词 + 复杂度 + 明确度)· 本文件只是视图。
> 🔴 机器层 `flow_type ∈ {Feature, Bug}` + Feature 重量档 `preset ∈ {full, tiny, micro}`;「Micro」为 legacy 别名(→ Feature·micro)。
> **四档但只有三个 preset** —— **lite 是 full 的装配形态、不是 preset**(用户拍板「lite 是不是可以被 full 装配出来」):它有 PRD、长在 goal 入口上,与 full 的唯一结构差是「跳 blueprint」一条边,由 `goal-complete --needs-blueprint false` 拧出来。判据:**preset 只给「不立就走不通链」的档**(micro 跳 review/test · tiny 无 goal/blueprint 入口);差一条边的用装配旋钮 —— 多一张转移图 = 多一处要同步的口径。
> 🔴 **与已退役的 legacy `lite`/`blueprint_lite` preset 不是一回事**:那两个是独立转移图(三份 flow-key 实现曾对同一输入解析出两张不同的图 · 已删净);现在的 lite **不加图**,只是 full 图上少走一条边 —— 同一个名字,反过来的做法。

## 闭集

| 流程 | telos(解决什么) | 链 | 产出 |
|------|----------------|-----|------|
| **Feature**(preset=full) | 从需求到上线的完整闭环 + 多视角质量门禁 | goal → (ui_design) → (blueprint) → dev → review → test → (browser_e2e) → pm_acceptance → ship | 代码 + 文档 + 测试 |
| **Feature**(full 的 **lite 装配形态**) | 有行为面但方案空间小(怎么做基本只有一种写法)· 需跑链路验证 —— **有 PRD、无 TC/TECH**;`goal-complete --needs-blueprint false` 跳 blueprint · goal 冷审 0 路缺省(**终确认停等照停** · 用户主权不因降档让渡)· review 单路 architect · AC↔测试绑定改由 PRD 机读块 `acceptance_criteria[].test_refs` 承载(dev 回填真实引用 · test-complete 校验非空**且引用真实存在**) | goal → dev → review → test → pm_acceptance → ship | 代码 + PRD + 测试 |
| **Feature**(preset=tiny) | 「直接做」形态(用户拍板:直接开发,完成后架构师 review 一下,PM 验收盯 staging 部署)—— 行为性但小 · 无契约面 · **diff 可验不需跑链路** · **零文档**(规格 = dev brief 理解卡) | dev → review〔architect 单路〕 → pm_acceptance → ship | 代码直改 |
| **Feature**(preset=micro) | 零逻辑改动最轻通道(文案/样式/资源/配置常量/注释 白名单 · 超纲即 tiny/full · 准入单源 prepare.md §2.2)· **execute 零门禁自由执行**(自选 model/subagent/workflow/测试 · 无规范限制)· 用户验收在 ship1 MR diff(R7)· | execute → ship | 代码直改 |
| **Bug** | 缺陷已指认 · **diagnose 先行**(根因 + 修复方案经用户确认才许修 · 防修偏)· review 单路 external | diagnose → dev → review → test → pm_acceptance → ship | 修复 + BUG 报告 + 回归测试 |
| **Feature Planning** | 产品方向 → 拆 ROADMAP · 不出代码(R6)· **不进状态机**(init reject · PMO 主对话执行 · 详 [docs/feature-planning.md](./docs/feature-planning.md)) | — | WS + ROADMAP + 全景 |
| **问题排查** | 理解现象 · 只定位根因 · **不进状态机**(mode A 深度版)· 🔴 排查先行律:根因未定的现象类输入一律先到这里 · 闭合再定流程(转 Bug 时结论直供 diagnose 复核不重查) | — | 排查报告 + 后续 todo |

## 关键约束

- 🎚️ **四档定档 = 减法侧分级缺省**(四轴越低档越轻):超低→micro · 低(diff 可验)→tiny · 中低(需跑链路 · 方案空间小)→lite · 中/高→full。🔴 **tiny/lite 的分界是四轴的「验证成本」轴,不是代码行数**。单源 [goal-stage § 链装配](stages/goal-stage.md) 减法侧分级表。
- 🔗 **装配决策点 = goal 调研后**(prepare 只对齐意图 · 不装配):环节(ui_design / **blueprint** / browser_e2e 三段可选)+ 评审面(roster / 方向 / 轮次)按调研实测四轴(方向 / 契约面 / 影响面 / 验证成本)定 · goal 自身评审面 AI 自定留痕 · 下游随 PRD 终确认导读「🔗 链装配」展示 —— **默认执行 · 用户不要求改就生效** · 单源 [goal-stage § 链装配](stages/goal-stage.md)。
  - **定档时机差**:micro/tiny 是 preset,prepare 就得选(在 goal 里才发现该降 = prepare 偏保守 · `init-feature --force` 重定档合法但要弃掉已产 PRD,多数情况按 lite 走完更划算);**lite 是装配形态 · goal 调研完当场拧旋钮 · 零 re-init** —— 这正是把它做成装配而非 preset 的收益。
- 轻量不靠独立 flow_type:**动态 roster(role_value_criteria)+ clarity + 四档** 承担。
- micro 涉代码仍必 ship(不停在本地未 push · P0-136)。
- 存量 legacy(M-id)兼容走完 · 新 init 不再产。

## 相关

[SKILL.md](./SKILL.md)(入口 + 暂停点) · [docs/prepare.md](./docs/prepare.md)(判定权威) · [STAGES.md](./STAGES.md)(编排单源)
