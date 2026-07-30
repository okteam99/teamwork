# Diagnose Stage(Bug 流程 · 根因细查 + 修复方案确认)

> 🧭 **四段结构**(目标 / 硬规则 / 建议手段菜单 / Output Contract)· 🔴 **仅 Bug 流程** · 位置在 `dev` 之前。

---

## ① 目标(telos)

**把 bug 从「症状」查成「可指到位置的真因 + 用户拍过板的修复方案」,再交给 dev 写码**。diagnose 是 Bug 流程的「what + how 确认」闸 —— 对应 Feature 的 goal(PRD)+ blueprint(TECH)。拦的风险:triage/prepare 时读的代码往往**不够细**(只够判流程类型 + 给个大致方向),照那个浅印象直接进 dev 写 fix → **极易修偏**(改了症状不是根因 / 改错位置 / 漏了影响面);以及修复方向被 AI 悄悄拍板 —— 用户在「报告 + fix + commit 一口气写完」的既成事实上补确认。**深度优先**:宁可在 diagnose 多读 20 分钟代码,也别在 dev 写错方向返工、到 review 才发现。

---

## ② 硬规则(白名单 · 每条一行 why)

1. **深读真实代码挖到可指位置的真因**:从现象入口顺调用链读到底,读**实际代码 / 数据流 / 配置 / schema** —— §根因 要能指到「哪个文件 / 哪行 / 哪个调用 / 哪个字段 / 为什么」,不是「大概是 X 模块的问题」;现象**不能稳定复现**时先收证据(日志 / 数据 / 调用栈)再判,**不靠猜**(why:凭 prepare 的浅印象或表面猜测出的方案,dev 照着写就是修偏)。
2. **decisive 前提必核验真实文件/数据**:方案依赖「数据是否真入库 / 字段是否真存在 / 能力是否真生效」时,读真实代码或数据确认 · **不轻信 Explore / sub-agent 摘要**(why:摘要常漏细节,正是修偏来源)。
3. **§根因 写根因、不写症状**:症状(用户看到的错)往往离根因好几层,改症状 = 治标 = 复发(why:根因写成现象复述,dev 只能修表面,同一个 bug 换个入口再来一次)。
4. 🔴 **本 stage 不写 fix 代码** —— 只查 + 规划,写码在 dev(按已确认的方案)(why:未确认的方案先落成代码 = 让用户在既成事实上拍板,确认沦为过场)。
5. 🔴 **R5 用户确认修复方案暂停点(必停 · 本 stage 的存在理由)**:`diagnose-complete` **之前必停**,把 **§根因 + §修复方案**(尤其方案:改哪、怎么改、影响面)呈现给用户 · emit R5 编号选项(字面见 ④)· **用户选 1 才 `diagnose-complete` → dev**;选 2 = 重新调查、修订 §根因/§修复方案后再次确认;**不擅自进 dev**(why:修哪儿、怎么修是用户主权决策,不是 AI 的)。多个候选方案 → 全部列出 + 给推荐 + 理由,让用户选。小到极致的 bug(一眼根因 · 改 1 行 · 零影响面)§根因/§方案 可极简、确认走个过场,**但流程不省**(流程在 · 不啰嗦)。
6. **auto_mode / yolo**:确认点不暂停,按推荐方案继续 + `add-concern --severity WARN` 留痕(diagnose 在状态机内 · 命令可用)(why:委托要留审计)。
7. **入口分两种,「问题排查转入」不重查**:① **Bug 直入**(缺陷已指认 · prepare 只给了大致方向)→ 按规则 1 从零细查;② **问题排查转入**(排查先行律 · 已有**已验证**根因 · 详 [docs/prepare.md §2](../docs/prepare.md))→ cite 排查结论并**复核**(核验关键文件仍一致)· **不重查** · 重点落 BUG 报告 + §修复方案 + R5 确认(why:已验证结论重查一遍是纯重复;但不复核就直接用 = 拿可能过期的结论定方案)。

---

## ③ 建议手段菜单 —— 本 stage 省略

> HOW 空间小:查因手段(顺调用链读 / 二分 / 收日志 / 核 schema)是模型自带的通用调试能力,写成菜单只会复述 ②。判断准则见 ① 的深度优先与 ② 各条。

---

## ④ Output Contract(产物契约 · 机读)

### `bugfix/BUG-<bug-id>.md`(模板 [templates/bug-report.md](../templates/bug-report.md))
- frontmatter:`bug_id` / `symptom` / `root_cause` / `fix_summary`(🔴 `fix_summary` = 修复**方案**摘要,不是「已修」—— diagnose 阶段还没写 fix 码)。
- body:**§现象**(可复现路径:输入 → 期望 → 实际)/ **§根因**(真因 + 实证位置)/ **§修复方案**(改哪 / 怎么改 / 取舍 / 影响面 / 备选)。
- §回归测试 + §修复记录由 **dev** 追加;dev **不重写** §根因/§修复方案(真发现根因判错 → `jump-to-stage --to diagnose` 复议 · 详 [dev-stage.md](./dev-stage.md) ②硬规则 6)。

### 物化拦截(diagnose-complete 校验)
`diagnose_doc`:`bugfix/BUG-*.md` 存在 **且** frontmatter `root_cause` + `fix_summary` 均非空(BUG-*.md 动态命名 → 走 evidence check,非固定路径 artifact)。

### ⏸️ R5 用户确认(硬规则 5 的字面)
```
⏸️ 根因 + 修复方案(请确认):
- 根因:<一句话真因 + 实证位置>
- 修复方案:<改哪 / 怎么改 / 取舍 / 影响面>
- (可选)备选方案:<...>

1. **确认根因与修复方案 · 进 dev 修复** 💡
2. **按指正修订诊断**(重新调查后再确认)
3. **其他**
```

### diagnose-complete(🔴 用户选 1 之后才跑)
```
state.py diagnose-complete --feature <path> --auto-commit <hash> --artifacts bugfix/BUG-<id>.md
```
→ 自动转 `dev`。dev 阶段按**已确认的方案**写 fix + §回归测试。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py) `FLOW_STAGE_CHAIN["Bug"]` · spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `DIAGNOSE_SPEC`
- 模板:[../templates/bug-report.md](../templates/bug-report.md) · 入口分流:[../docs/prepare.md §2](../docs/prepare.md)
- 下游:[dev-stage.md](./dev-stage.md)(按确认方案写 fix)· 通用纪律:[../STAGES.md](../STAGES.md)
