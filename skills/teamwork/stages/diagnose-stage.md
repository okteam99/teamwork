# Diagnose Stage(Bug 流程 · 根因细查 + 修复方案确认)

> 🔴 **仅 Bug 流程**。在 `dev` 之前 · 把「根因 + 修复方案」查清楚并**让用户确认**,再进 dev 写码。
> **存在理由**:triage/prepare 时读的代码往往**不够细**(只够判流程类型 + 给个大致方向)· 直接进 dev 写 fix → **极易修偏**(改了症状不是根因 / 改错位置 / 漏了影响面)。diagnose 是 Bug 流程的「what + how 确认」闸 —— 对应 Feature 的 goal(PRD)+ blueprint(TECH)。
> 🔴 **入口分两种**:① **Bug 直入**(缺陷已指认 · prepare 只有大致方向)→ 本 stage 从零细查;② **问题排查转入**(排查先行律 · 已有**已验证**根因 · 详 [docs/prepare.md §2](../docs/prepare.md))→ cite 排查结论**复核**(核验关键文件仍一致)· **不重查** · 重点落 BUG 报告 + §修复方案 + R5 确认。

---

## 怎么做

### 1. 复现 + 锁定现象
- 明确 bug 的可复现路径(输入 → 期望 → 实际)· 写进 BUG 报告 §现象。
- 不能复现 → 先收集证据(日志 / 数据 / 调用栈)· 不靠猜。

### 2. 🔴 深读代码做根因细查(本 stage 的核心 · 不能省)
- **深读相关代码**:从现象入口顺着调用链读到真因 —— 读**实际代码 / 数据流 / 配置 / schema**,不是凭 prepare 时的浅印象。
- **挖到真因**:能指到「哪个文件 / 哪行 / 哪个调用 / 哪个字段 / 为什么」· 不是「大概是 X 模块的问题」。
- **decisive 前提核验真实文件**:涉及「数据是否真入库 / 字段是否真存在 / 能力是否真生效」→ 读真实代码/数据确认 · 不轻信 Explore/sub-agent 摘要(摘要常漏细节,正是修偏来源)。
- **区分症状 vs 根因**:症状(用户看到的错)往往离根因好几层 · 改症状 = 治标 = 复发。写 §根因 要写**根因**。

### 3. 起草修复方案(§修复方案 · 不写 fix 码)
- **改哪**(文件/函数)· **怎么改**(具体逻辑)· **取舍**(为什么这样改 · 有没有更简单的)· **影响面**(动这块会不会波及别处 / 是否需要回归)。
- 🔴 **本 stage 不写 fix 代码** —— 只查 + 规划。写码在 dev(按已确认的方案)。
- 多个候选方案 → 列出 + 给推荐 + 理由,让用户选。

### 4. 写 BUG 报告
`bugfix/BUG-<bug-id>.md`(模板 [templates/bug-report.md](../templates/bug-report.md))· frontmatter `bug_id / symptom / root_cause / fix_summary`(`fix_summary` = 修复**方案**摘要)· body §现象 / §根因 / §修复方案。

### 5. 🔴 用户确认修复方案(R5 暂停点 · 必停)
diagnose-complete **之前必停** · 把 **§根因 + §修复方案**(尤其方案:改哪、怎么改、影响面)呈现给用户:

```
⏸️ 根因 + 修复方案(请确认)· 回 ok 进 dev 写 fix · 或指正
- 根因:<一句话真因 + 实证位置>
- 修复方案:<改哪 / 怎么改 / 取舍 / 影响面>
- (可选)备选方案:<...>
```

用户 `ok` 才 `diagnose-complete` → dev。用户指正 → 改方案再确认。**不擅自进 dev**。

### 6. complete
```
state.py diagnose-complete --feature <path> --auto-commit <hash> --artifacts bugfix/BUG-<id>.md
```
→ 自动转 dev。dev 阶段按**已确认的方案**写 fix + §回归测试。

---

## 质量基线

- 🔴 **根因 ≠ 症状**:§根因 必须是真因(可指到代码位置)· 不是表面现象的复述。
- 🔴 **方案先确认再写码**:diagnose 出方案 → 用户确认 → dev 写码。**不在 diagnose 写 fix**,**不跳过用户确认直冲 dev**(治本「prepare 浅确认 → dev 一口气写报告+fix+commit」的修偏 case)。
- **深度优先**:宁可在 diagnose 多读 20 分钟代码,不要在 dev 写错方向返工 + review 才发现。
- 小到极致的 bug(一眼根因 · 改 1 行 · 零影响面):仍走 diagnose,但 §根因/§方案 可极简 · 用户确认走个过场即可(流程在 · 不啰嗦)。

---

## 相关
- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py) `FLOW_STAGE_CHAIN["Bug"]`
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `DIAGNOSE_SPEC`
- 模板:[../templates/bug-report.md](../templates/bug-report.md)
- 下游:[dev-stage.md](./dev-stage.md)(按确认方案写 fix)
