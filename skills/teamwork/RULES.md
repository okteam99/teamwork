# Teamwork 核心规则

> 本文件定义所有角色共用的核心规则，各角色必须遵守。

---

## 🔴 PMO 每次阶段变更必做（3 件事，缺一不可）

```
1. 输出 1 行校验（必须引用 flow-transitions.md 行号+原文）：
   📋 {A} → {B}（📖 {🚀/⏸️}，来源：flow-transitions.md L{行号} "{原文}"）
   🔴 必须引原文，禁止只写"查 ✅"。编造行号/原文 = 伪造证据。

2. 按流转类型执行：
   🚀自动 → 直接执行，禁止插入任何选择/确认/询问
   ⏸️暂停 → 输出 💡建议 + 📝理由，等用户明确确认

3. 不跳步、不合并、不自创：
   按 flow-transitions.md 的顺序逐步走，禁止跳过/合并/自创步骤
   "效率更高""用户已给答案""太简单"都不是跳步理由
```

---

## PMO 热路径索引（compact 后优先读此段 + state.json）

> 🔴 PMO 日常流转只需查阅以上 3 条 + 按需查索引，无需通读全文。
> Compact 后恢复时：先读 `{Feature}/state.json` → 如需详细规则再按索引定位读取。
> 🟢 v7.3.2：STATUS.md 已废弃，state.json 是 Feature 状态的单一权威。

| 需要做什么 | 读哪里 | 行范围 |
|-----------|--------|--------|
| 判断是否需要暂停 | §一 暂停条件 | 本文件开头 |
| 阶段流转前校验 | rules/gate-checks.md | 1 行流转校验 + 门禁检查 + state.json 更新 |
| 查合法转移路径 | rules/flow-transitions.md | 6 种流程 + PL 模式 + 通用特殊状态 |
| Bug 简单/复杂判断 | FLOWS.md「Bug 处理流程」 | 判断表 + 简化/完整流程 + 闭环验证 |
| 功能完成收尾 | §四 功能完成时 PMO 必须执行 | `### 功能完成时 PMO 必须执行` |
| Subagent 启动规范 | §四-B Subagent 执行规则 | `## 四-B` |
| 执行方式判断（Subagent vs 主对话） | agents/README.md §一「执行方式速查表」 | `agents/README.md` |
| Subagent dispatch 前预检 | common.md「PMO 预检流程」L1/L2/L3 | `standards/common.md` |
| 编号分配 | rules/naming.md | 功能/Bug/优化/决策/变更/BG 编号 |

### 拆分文件索引

| 文件 | 内容 | 加载时机 |
|------|------|----------|
| [rules/flow-transitions.md](./rules/flow-transitions.md) | 阶段状态转移表（6 种流程 + PL 模式） | PMO 流转校验时 |
| [rules/gate-checks.md](./rules/gate-checks.md) | 1 行流转校验 + 门禁检查 + state.json 更新 | PMO 每次阶段变更时 |
| [rules/naming.md](./rules/naming.md) | 编号规则（功能/Bug/优化/决策/变更/BG） | PMO 分配编号时 |

---

## 一、暂停条件（统一定义）

### ⏸️ 必须暂停等待用户确认

以下情况必须暂停，等待用户明确确认后才能继续：

| 类型 | 场景 | 说明 |
|------|------|------|
| **🔴 项目空间变更** | teamwork_space.md 创建/修改/删除 | 任何对 teamwork_space.md 的变更都必须暂停等用户确认 |
| **🔴 跨项目需求拆分** | Feature 流程中识别到跨项目影响，PMO 输出拆分方案后 | 拆分方案（含 BG 业务关联 ID + 推进顺序）必须暂停等用户确认后才能开始各子项目流程 |
| **PL-PM 讨论分歧** | Plan Stage 内 PL-PM 讨论存在分歧时 | PL-PM 讨论未达成共识 → 展示分歧项，等待用户逐项决策 |
| **产品确认** | Plan Stage 完成后 | Plan Stage（PM PRD+PL-PM 讨论+多角色评审）→ 汇总问题，等待用户确认 |
| **设计确认** | UI Design Stage 返回后 | 输出设计稿 + HTML 预览 → PMO 摘要，等待用户确认 |
| **评审问题** | Blueprint Stage 内评审发现问题 | 汇总问题，等待用户决定修改/忽略 |
| **复杂技术方案** | 符合复杂度条件 | 输出技术方案，等待用户确认 |
| **产品逻辑变更** | 任何需求调整 | 无论大小，必须用户确认 |
| **UI 变更** | 任何设计调整 | 必须先出 HTML 预览稿，用户确认后才能改代码 |
| **外部资源** | 需要用户提供 | API Key、账号密码、第三方配置等 |
| **本地操作** | 需要用户执行 | 启动服务、安装软件、环境配置等 |
| **付费/不可逆** | 涉及成本或风险 | 付费服务调用、数据删除等 |
| **代码校验不通过** | PMO 检查发现问题 | 文档标记已完成但：测试未通过/有TODO/TC未覆盖 |
| **集成测试失败** | 需确认的失败 | 需求理解偏差/测试用例问题，需用户决定处理方式 |
| **资源依赖缺失** | 首次集成测试 | 数据库连接/测试账号等配置缺失，需用户提供 |
| **Roadmap 确认** | Feature Planning 流程 | PM 完成 ROADMAP.md 后，必须等用户确认优先级和依赖关系 |
| **🌐 teamwork_space.md 架构确认** | 工作区级 Feature Planning | PM 更新 teamwork_space.md 草稿后，必须等用户确认架构变更 |
| **🌐 Workspace Planning 收尾** | 工作区级 Feature Planning | 所有子项目 Planning 完成后，PMO 更新 teamwork_space.md 收尾，必须等用户最终确认 |
| **PL 讨论结论确认** | Product Lead 讨论模式 | PL 与用户讨论完毕，输出结论摘要后，必须等用户确认结论再进入执行 |
| **CHG 变更记录确认** | Product Lead 执行模式 | PL 产出 CHG 变更记录后，必须等用户确认变更范围和影响评估 |
| **变更影响评估确认** | 变更级联（Level 2/3） | PL 输出变更影响评估报告后，必须等用户确认后才能启动级联更新 |
| **全景设计同步确认** | Feature 流程（设计 Step 2） | Designer 更新全景设计（sitemap.md + overview.html）后，⏸️ 必须等用户确认全景再继续 QA |
| **全景设计确认** | Feature Planning | Designer Subagent 产出全景设计（全景重建模式）后，必须等用户确认 |
| **INFRA 影响面确认** | INFRA Feature 或技术类 PRD 影响 ≥3 个子项目 | Blueprint Stage 架构师评审 / Plan Stage PRD 评审发现影响面过大，需用户确认后继续 |
| **UI 还原验收** | Feature 流程（有 UI） | Designer 验收 RD 的 UI 实现，每轮修改后需用户确认（最多 3 轮） |
| **外部依赖就绪恢复** | Feature 被阻塞后依赖就绪 | 依赖就绪后 PMO 提醒用户，必须用户确认后才恢复 Feature 流程 |
| **🔴 闭环验证不通过** | RD 自查/QA 验证/PMO 完成报告缺少实际执行输出 | 必须补充验证证据（测试命令输出、通过率数据）后才能继续，禁止空口完成 |

> **多暂停条件同时触发时的优先级**（从高到低）：
> 1. 🔴 安全/数据相关（付费/不可逆、数据删除）
> 2. 🔴 架构影响（项目空间变更、跨项目需求拆分、INFRA 影响面）
> 3. 用户确认（PRD/设计/方案/Roadmap 确认）
> 4. 流程确认（评审问题、变更记录、外部依赖）
>
> PMO 按此优先级排序后，在一条暂停摘要中列出所有待确认项，用户可逐项回复。

### 🔴 暂停输出规范（所有 ⏸️ 暂停点统一适用）

```
PMO/当前角色在暂停点输出时，必须同时满足以下 5 条：

1. 给建议 + 理由（红线 #10）
   ├── 📌 待确认项：{具体内容}
   ├── 💡 建议：{推荐方案}（🔴 必须是下方编号选项中的某一个）
   ├── 📝 理由：{基于项目上下文的关键考量}
   └── 🔀 备选方案：{如有}
   🔴 禁止只抛问题不给方案，禁止「请用户自行决定」

2. 🔴 选项编号化（v7.3.5 / v7.3.6）—— 用户回复易打的字符
   ├── ✅ 单决策点：选项用 1/2/3/4 数字编号（用户回一个数字）
   ├── ✅ 多决策点：决策点用数字 1/2/3，选项用字母 A/B/C/D（用户回 "1A 2B" 两维组合）
   ├── ✅ 第一项是 PMO 推荐（与 💡 建议 一致，标注「推荐」）
   ├── ✅ 最后一项始终为「其他指示（自由输入）」
   ├── ❌ 禁止描述式选项（"- 跳过" / "- 跑 Browser E2E"）
   ├── ❌ 禁止用 ①②③ 这类要输入法切换的字符（v7.3.6）
   └── 用户可以回数字/字母组合，或自然语言覆盖默认

   2.1 单决策点（标准格式，用数字）：
   ```
   ⏸️ 请选择（回复数字即可）
   1. {推荐选项} ← 💡 推荐
   2. {备选选项 1}
   3. {备选选项 2（如有）}
   4. 其他指示（自由输入）
   ```

   2.2 🔴 多决策点（v7.3.6）—— 决策点数字 + 选项字母，回复 "1A 2B"
   ├── 场景：一个暂停点需要用户同时确认 2 个及以上独立决策（如「PRD 通过？」+「排期方案？」）
   ├── 结构：决策点用数字 `1.` `2.` `3.` 分隔；每个决策点内部选项用字母 `A.` `B.` `C.` `D.`
   ├── 用户回复格式：`1A 2B` / `1A  2B`（空格分隔，按决策点顺序）
   ├── 🔴 每个决策点独立必有 💡 推荐（首项 A）+ 「其他指示」（末项）
   └── 决策点之间必须语义独立（一个确认不应隐含另一个答案）

   多决策点标准格式（模板）：
   ```
   ⏸️ 请确认以下 {N} 件事（回复 "1A 2B" 这种组合即可）

   1. {决策点 1 标题}：
      A. {推荐选项} ← 💡 推荐
      B. {备选选项}
      C. {备选选项}
      D. 其他指示

   2. {决策点 2 标题}：
      A. {推荐选项} ← 💡 推荐
      B. {备选选项}
      C. {备选选项}
      D. 其他指示

   回复示例：
   - `1A 2B` = 决策 1 选 A，决策 2 选 B
   - `1A 2A` = 两项都采纳推荐（最常见）
   - 自然语言覆盖也可
   ```

   2.3 何时合并 vs 拆分
   ├── 合并（用多决策点）：两个独立决策**同时到达**同一暂停点，且完整反馈能一次决定
   │   示例：PRD 评审收尾时「PRD 通过？」+「排期策略？」同时浮现
   ├── 拆分（分多个暂停点）：后一决策需要前一决策结果才能判断
   │   示例：PRD 确认后才决定 UI 方向 → 两次暂停，不合并
   └── 🔴 多决策点上限 3 个；超过 3 个 → 拆分为多个暂停点

   2.4 打字友好性原则
   ├── 单决策：一个数字（1）→ 1 字符
   ├── 多决策（2 个）：数字+字母 两组（1A 2B）→ 5 字符（含空格）
   ├── 避免 ①②③（需输入法切换）/ 大写罗马数字 / emoji 编号
   └── 规则：用户能在**英文键盘直接敲出**的字符优先


3. 提问锚定流程（禁止暗示直接执行）
   ├── ✅「确认按 {流程名} 流程推进？我会切换到 {角色} 开始 {阶段}。」
   ├── ❌「要我 {做某事} 吗？」→ 绕过流程
   └── PMO 初步分析必须同时列出：(a) 流程类型确认 (b) 方案/范围确认

4. 模糊确认处理
   ├── 用户回复**纯数字**（1/2/3）→ 单决策映射到对应选项执行
   ├── 用户回复**数字+字母组合**（1A 2B / 1A2B）→ 多决策按顺序解析
   │   ├── 正解：`1A 2B` / `1A  2B` / `1A2B`（数字=决策点编号，字母=选项）
   │   ├── 大小写不敏感：`1a 2b` / `1A 2B` 同效
   │   ├── 数量必须匹配决策点数量；不匹配 → 回问补齐
   │   └── 解析歧义（单纯 `12` 无字母）→ 视为非法，要求明确
   ├── 用户回复 ≤5 字且非数字/字母组合、未提及流程名/阶段名 → PMO 复述阶段链 + 等二次确认
   ├── 豁免：用户回复含流程名（如「走敏捷」）或阶段名（如「开始写 PRD」）
   └── 🔴 禁止把「好」「行」直接视为全面授权（因为不对应具体编号）

5. 双向约束
   ├── 红线 5：暂停点必须停——用户未明确确认前禁止继续
   └── 红线 12：非暂停点禁止停——自动执行节点禁止插入确认/询问
```

**正面示例 vs 反面示例**：

```
❌ 反例 1（描述式，用户要打字）：
⏸️ 请回复
- 跳过（推荐，直接 PM 验收）
- 跑 Browser E2E
- 其他指示

✅ 正例 1（单决策点，回一个数字）：
⏸️ 请选择（回复数字即可）
1. 跳过 Browser E2E，直接进入 PM 验收 ← 💡 推荐
2. 跑 Browser E2E（+15-25 min，验证 Sidebar flag / LanguageSwitcher 等路径）
3. 其他指示（自由输入）

❌ 反例 2（多决策点用 ①②③ 需要输入法切换）：
⏸️ 请确认以下两件事
① PRD 是否通过：
  1. 通过  2. 修改某条  3. 忽略某条  4. 其他
② 排期方案：
  1. 并行推进  2. F003a 优先  3. F013 优先  4. 其他
（回复 "①1 ②2" ← 需切换输入法，❌ v7.3.6 禁止）

✅ 正例 2（多决策点，数字+字母组合）：
⏸️ 请确认以下两件事（回复 "1A 2B" 这种组合即可）

1. PRD 是否通过：
   A. 通过 — PRD v0.3 定稿，进入 UI Design Stage ← 💡 推荐
   B. 修改 RD-R1 / Designer-D1 / QA-Q1（当前均已转下游承接，非阻塞；要提前处理请指定）
   C. 忽略某条（需说明理由，PMO 记录）
   D. 其他指示

2. F013 与 F003a Blueprint 排期：
   A. 并行推进 — F003a 等 BG-007 依赖期间 F013 先进 UI Design ← 💡 推荐
   B. F003a 优先 — F013 排到 F003a 交付后再开
   C. F013 优先 — 先把 flag 链路端到端跑通
   D. 其他指示（例如先做 BG-008 评估再决定）

回复示例：
- `1A 2A` = PRD 通过 + 并行推进（双采纳推荐）
- `1A 2B` = PRD 通过 + F003a 优先
- `1B 2A` = PRD 先修某条 + 并行推进
```

### ✅ 无需暂停（执行阶段内的操作）

```
已进入执行阶段（PM/Designer/QA/RD 正在产出）且不在暂停点上时，
以下操作自动执行，禁止插入确认：
├── 代码编写/修改/删除、运行测试、构建、安装依赖
├── 代码重构、性能优化、修复测试失败
├── 创建目录/文档、补充遗漏实现细节
└── 🔴 暂停点仍须暂停（具体列表见上方暂停条件表 + flow-transitions.md 的 ⏸️ 标注）
```

---

## 二、技术方案复杂度判断

**复杂度判断对比表**：

| 维度 | ⏸️ 复杂方案（需用户确认） | 简单方案（可申请跳过，需用户同意） |
|------|--------------------------|----------------------------------|
| 文件数 | >= 2 个文件 | 1 个文件 |
| 模块范围 | 多模块联动或跨层调用 | 单模块内 |
| 数据库 | 需要数据迁移或结构变更 | 无 |
| 影响面 | 影响现有功能或公共接口 | 无影响 |
| 技术栈 | 引入新技术栈或第三方依赖 | 无新引入 |
| 方案选择 | 有多个可选方案需要权衡 | 方案明确 |
| 适用场景 | 满足任一即为复杂 | 简单 bugfix（根因明确）、纯 UI 还原、日志/注释、测试补充 |

**🔴 核心原则：优先合理方案，而非简单方案**

| 原则 | 说明 |
|------|------|
| 优先根因修复 | 不绕过症状，根因改动大也应选根因 → 走复杂方案 |
| 简单方案标准严格 | 仅拼写错误、配置值错误等确实简单的问题 |
| 极端情况允许症状修复 | 根因需重构核心架构且时间紧急时，必须说明原因 + 后续根因修复计划 |
| 禁止刻意简化 | RD 不能因为想走简化流程而把方案往"简单"方向靠 |

**🔴 申请跳过流程**：RD 判断为简单方案 → 输出跳过申请（原因 + 根因/症状说明 + 改动范围 + 申请跳过「技术方案 + TDD」）→ ⏸️ 等待用户确认（同意 → 直接开发；不同意 → 正常流程）

**🔴 禁止 RD 自行决定跳过！即使方案再简单，未经用户同意都必须走技术方案 + TDD。**

---

## 三、Bug 处理流程

> 📎 Bug 处理流程的权威定义已迁移到 [FLOWS.md](./FLOWS.md)「Bug 处理流程」章节，
> 包含：简单/复杂判断表、简化流程、完整流程起点、闭环验证、Bugfix 记录格式。
> PMO 处理 Bug 时查阅该文件。

---

## 四、自动流转规则

### 🔴 阶段切换预检（Pre-flight Check）— 已合并到下方「强制流转校验输出」

> 原独立的 Pre-flight Check 已合并到流转校验行中。
> PMO 每次阶段变更只需输出 1 行校验（格式见 [rules/gate-checks.md](./rules/gate-checks.md)）。
> 🔴 流转类型必须通过查 rules/flow-transitions.md 获取，禁止凭记忆填写。

### RD 完成后完整流转链（v7.3 更新，与 stages/*.md 实际实现一致）

```
📋 流转链设计原则（v7.3 契约化后）：
├── 每个 Stage 定义 Input Contract / Process Contract / Output Contract
├── 执行方式由 AI Plan 模式在每个 Stage 开始时决定（main-conversation / subagent / hybrid）
├── Dev Stage 不含 CR（架构师 CR 已拆到 Review Stage 并行）
├── Review Stage 三路独立视角（架构师 / QA / Codex），独立性由产物结构约束保证
├── Test Stage 环境独立（默认主对话起环境，集成测试 + API E2E 可 Subagent）
└── Build 不过不能进 Verify → 发现问题返回 PMO 安排修复 → 重新 Verify

📋 PMO L2 预检（见 common.md「PMO 预检流程」）
  ↓

🔗 Dev Stage（规范：stages/dev-stage.md）
  ├── 执行方式：AI 自主决定（按规模/复杂度）
  ├── 内部：按 TECH/TC 实现 + TDD（弱约束）+ 单测全绿 + RD 自查
  ├── ✅ DONE → 继续
  ├── ⚠️ DONE_WITH_CONCERNS → PMO 判断是否需要用户确认
  └── 🔁 QUALITY_ISSUE → ⏸️ 用户决策
  ↓

🔗 Review Stage（规范：stages/review-stage.md，三视角独立）
  ├── 架构师 Review：默认主对话（保留架构上下文 + 怀疑者视角防鼓掌）
  ├── QA 代码审查：默认 Subagent（独立视角，可用不同模型）
  ├── Codex Review：Subagent（外部工具，🔴 不读架构师报告）
  ├── 三份产物结构独立：不同 generated_at / files_read / 无交叉引用
  ├── ✅ DONE → 继续
  ├── ⚠️ DONE_WITH_CONCERNS → PMO 评估，非阻塞则继续
  ├── 🔁 NEEDS_FIX → RD 修复 → 重跑相关视角（≤3 轮）
  └── ❌ FAILED（Codex 不可用且降级失败）→ ⏸️ 用户
  ↓
  → 有 UI？
    ├── 是 → Designer UI 还原验收（最多 3 轮，每轮 ⏸️ 用户确认）
    │         └── 通过 ↓
    └── 否 ↓
  📋 PMO L2 预检（含 E2E 时升级 L3）
  ↓

🟡 Test Stage 前置确认（PMO 必须执行，见 roles/pmo.md「Test Stage 前置确认」）
  ├── 1. 🚀 立即执行 → 继续启动 Test Stage（💡 推荐）
  ├── 2. ⏸️ 延后批量测试 → 跳过本次 Test Stage，review-log 记 DEFERRED，直接进入 PM 验收
  │       └── 完成报告标「⚠️ 待测试」而非「✅ 已完成」
  └── 3. ⏭️ 跳过（需理由）→ review-log 记 SKIPPED + reason，直接进入 PM 验收
  ↓（仅 1 分支继续）

🔗 Test Stage（规范：stages/test-stage.md）
  ├── 环境准备（默认主对话）：scripts/test-env-check.sh → 落盘 test-env.json
  ├── 集成测试（可 Subagent 或主对话）：按 agents/integration-test.md
  ├── API E2E（默认 Subagent）：脚本化交付（tests/e2e/F{编号}/api-e2e.py）
  ├── ✅ DONE → 继续
  ├── 🔁 QUALITY_ISSUE（代码问题）→ PMO 安排 RD 修复 → 重新 Test Stage
  │   └── 🔴 Verify-Fix 循环最多 3 轮，超出 → ⏸️ 用户
  ├── ❌ BLOCKED（环境问题）→ ⏸️ 用户处理环境
  └── ⚠️ DONE_WITH_CONCERNS（TC 问题等）→ ⏸️ 用户确认
  ↓
  → PMO 读取 TC.md「Browser E2E 判断」章节：
    ├── Browser E2E = 需要 → PMO 给出建议 → ⏸️ 用户确认是否执行
    │   ├── 用户确认执行 → 🔗 Browser E2E Stage（默认主对话，需观察 / AI 浏览器）
    │   ├── 用户明确跳过 → 记录原因 ↓
    │   └── 通过 ↓
    └── Browser E2E = 不需要 / 无浏览器行为 → 自动跳过 ↓
  → PM 验收 → ✅ 已完成

🔴 Verify-Fix 循环规则：
├── Test Stage 返回 QUALITY_ISSUE → PMO 安排修复（主对话或 Subagent 由 AI 决定）
├── 修复完成 → PMO 重新进入 Test Stage（默认全量重跑）
├── 如果修复范围极小且 Test Stage 建议断点续跑 → PMO 可选择从断点开始
└── 最多 3 轮 Verify-Fix 循环，超出 → ⏸️ 用户决策

🔴 每个 Stage 开始前：AI 必须输出 Execution Plan 块（见 SKILL.md「AI Plan 模式规范」）。
   Plan 写入 state.json.planned_execution（含 estimated_minutes）。

🔴 v7.3.3 耗时度量闭环：
├── 进入 Stage：PMO 记录 state.json.stage_contracts[stage].started_at
├── Stage 完成：PMO 计算 duration_minutes、variance_pct，写入 state.json + append review-log
├── PMO 阶段摘要必须包含「⏱️ 实际耗时：N min（预估 M min，偏差 ±X%）」行
└── Feature 完成报告必须包含「⏱️ 耗时统计」章节（表格 + 超预估分析）
```

### 流转条件

```
自动流转需**全部满足（AND）**：
├── ✅ 当前角色任务已完成
├── ✅ 无待决策项 / 待确认项
└── ✅ 文档状态已更新
```

### 阶段状态转移表（合法路径）

> 📎 转移表的权威定义在 [rules/flow-transitions.md](./rules/flow-transitions.md)（含流转类型 🚀/⏸️/🔀）。
> PMO 流转校验时必须查该文件，不在表中的转移路径为非法。
> 此表覆盖全部六类流程（Feature / Bug 处理 / 问题排查 / Feature Planning / 敏捷需求 / Micro）+ PL 模式 + 通用特殊状态。


> 📎 1 行流转校验格式、门禁检查、state.json 更新规则的权威定义见 [rules/gate-checks.md](./rules/gate-checks.md)。
> PMO 每次阶段变更必须查阅该文件。
### Feature 流转逻辑（8 Stage 模型）

> 📎 每个 stage 的详细定义见 stages/*.md。PMO 是纯调度器：dispatch stage → 收结果 → ⏸️ 或 🚀 → dispatch 下一个。

```
🔗 Plan Stage（stages/plan-stage.md）
    内部：PM 写 PRD → PL-PM 讨论 → 多角色技术评审 → 定稿 PRD
    ↓
    📊 PMO 摘要 → ⏸️ 用户确认 PRD
    ↓ 用户确认后
    ├── 需要 UI → UI Design Stage
    └── 不需要 UI → Blueprint Stage

🔗 UI Design Stage（stages/ui-design-stage.md，仅有 UI 时，v7.3.4 合并）
    内部：Designer 一次产出 Feature UI + 全景增量同步（🟡 全景默认增量合并，禁止重写）
    ↓
    📊 PMO 摘要 → ⏸️ 用户确认「设计批」（UI + 全景一起审，一个暂停点）
    ↓ 用户确认后（有问题 → 重新 dispatch，≤3 轮）
    └── Blueprint Stage

📎 v7.3.4 之前的 Panorama Design Stage 独立暂停点已合并。
    Panorama Design Stage 现在仅保留给 Feature Planning 流程的**全景重建模式**使用。

🔗 Blueprint Stage（stages/blueprint-stage.md）
    内部：QA 写 TC + TC 多角色评审 + RD 写 TECH.md + 架构师方案评审
    ↓
    📊 PMO 摘要 → ⏸️ 用户确认技术方案
    ↓ 用户确认后

📋 PMO L2 预检（见 common.md「PMO 预检流程」）
    ↓
🔗 Dev Stage（stages/dev-stage.md）
    内部：RD TDD 开发 + 单元测试（全绿才返回）
    ↓ 🚀 自动

🔗 Review Stage（stages/review-stage.md）
    内部：架构师 CR ∥ Codex Review ∥ QA 代码审查（三路并行）
    ├── DONE → 🚀 自动
    ├── NEEDS_FIX → RD 修复 → PMO 判断重跑哪些 review（≤3 轮）
    └── FAILED → ⏸️ 用户决策
    ↓ 🚀 自动

📋 PMO L3 预检（如需 E2E）
    ↓
🟡 Test Stage 前置确认（PMO 必询问 1/2/3，见 roles/pmo.md「Test Stage 前置确认」）
    ├── 1. 立即执行 → ↓ 继续（💡 推荐）
    ├── 2. 延后批量测试 → 记 DEFERRED，跳过本 Stage 直接进入 PM 验收
    └── 3. 跳过（需理由）→ 记 SKIPPED + 原因，直接进入 PM 验收
    ↓（仅 1 分支进入下方 Test Stage）
🔗 Test Stage（stages/test-stage.md，🟡 可选 Stage）
    内部：集成测试 ∥ API E2E（并行）
    ├── DONE → 🚀 自动
    ├── QUALITY_ISSUE → RD 修复 → 重跑（≤3 轮）
    └── BLOCKED → ⏸️ 用户处理环境
    ↓ 🚀 自动

Browser E2E 判断：
    ├── 需要 → 🔗 Browser E2E Stage → 通过 → PM 验收
    └── 不需要 → PM 验收

🔗 PM 验收 + commit + push（v7.3.4 合并暂停点）
    PM 完成验收判断 → PMO 自动本地 commit（含所有 Feature 产物）
    ↓
    📊 PMO 摘要 → ⏸️ 用户 3 选 1：
    ├── 1️⃣ ✅ 通过 → 自动 commit + push（默认远程分支）
    ├── 2️⃣ ✅ 通过 → 仅本地 commit（不 push）
    └── 3️⃣ ❌ 不通过 → 补充信息 → 回到上一阶段（Review/Test/RD 修复）
    ↓ 用户选 1/2 后
PMO 完成报告（含 Review Dashboard 全绿确认 + PROJECT.md 更新 + 全景确认 + 知识库总结 + commit hash + push 状态）→ ✅
```

### 敏捷需求流程自动流转

> 敏捷需求 = Feature 精简版。砍掉 PL-PM 讨论+技术评审、UI Design/Panorama、完整 Blueprint（含评审）。
> 用 BlueprintLite Stage（轻量蓝图）替代完整 Blueprint：简化 TC + 实现计划，无评审。
> Dev Stage 保持不变——始终按蓝图执行，不区分 Feature/敏捷模式。

```
PMO 初步分析 → ⏸️ 用户确认走敏捷
    ↓
PM 编写精简 PRD → ⏸️ 用户确认 PRD
    ↓
🔗 BlueprintLite Stage（主对话快速执行：QA 简化 TC + RD 实现计划，无评审）
    ↓ 🚀 自动
📋 PMO L2 预检
    ↓
🔗 Dev Stage → 🚀 → 🔗 Review Stage → 🚀 → 🔗 Test Stage（与 Feature 一致）
    ↓
Browser E2E（可选）→ PM 验收 → PMO 完成报告（含事后审计：文件数 ≤ 5）→ ✅

砍掉的环节（vs Feature）：
├── Plan Stage 内的 PL-PM 讨论 + 技术评审（PM 直接写精简 PRD）
├── UI Design Stage + Panorama Design Stage
└── 完整 Blueprint Stage → 替换为 BlueprintLite Stage（无 TC 评审、无架构师评审）

🔴 Dev Stage 始终不变：不管 Feature 还是敏捷，Dev Stage 收到的都是"已有 TC + 已有实现计划"，
   按蓝图执行 TDD。这保证了 Dev Stage 规范的单一职责和可预测性。
```

### Micro 流程自动流转

> Micro = 零逻辑变更的最轻量通道。砍掉 QA、架构师、Codex 全部环节，只保留 PMO 分析 + 用户确认 + RD Subagent 执行 + 用户验收。
> 📎 准入条件、白名单、规则详见 [FLOWS.md](./FLOWS.md)「六、Micro 流程」。

```
PMO 初步分析（判断符合 Micro 准入条件）
    ↓
📋 PMO 输出分析 + Micro 准入条件逐项检查
    ↓
⏸️ 等待用户确认走 Micro 流程（🔴 必须由用户确认）
    ↓ 用户确认
PMO 编写 Micro 变更说明
    ↓ 🚀 自动
📋 PMO L1 预检（见 common.md「PMO 预检流程」）
    ↓
🤖 RD Subagent 执行改动（🔴 PMO 禁止自己改，即使只改一行）
    ├── 执行改动 + 跑已有测试确认无回归
    └── 返回执行报告
    ↓
📊 PMO 阶段摘要
    ↓
⏸️ 用户验收
    ↓ 用户确认通过
PMO 完成报告（含 Micro 事后审计）
    ↓
Micro 需求完成 ✅
```

### Feature Planning 流程自动流转

```
/teamwork 规划 [产品目标]
    ↓
PMO 识别为 Feature Planning 类型
    ↓ 🚀 自动（同一回复中继续）
    └── 🔄 切换到 PM，开始产品规划

PM 与用户讨论产品方向（澄清目标、功能范围、取舍决策）
    ↓
🎨 全景设计验收（有 UI 的子项目。🔴 讨论达成共识后立即执行！）
    ├── 涉及页面结构变更 → 启动 Designer Subagent（全景重建模式）
    │   ├── 产出：design/sitemap.md + design/preview/overview.html（全新重建）
    │   └── PMO 摘要 → ⏸️ 等待用户确认全景设计
    ├── 无页面结构变更 → 显式输出「⏭️ 跳过全景重建」
    └── 非 UI 子项目 → 显式输出「⏭️ 非 UI 项目，跳过」
    ↓
用户确认全景设计
    ↓
📋 PM 更新 PROJECT.md（🔴 基于已确认的全景设计）
    ├── 产品方向/业务变更 → 更新业务流程、功能模块、关键决策等章节
    └── 仅追加新 Feature → 仅更新「当前状态」章节
    ↓
PM 基于 PROJECT.md 拆解 ROADMAP
    ├── 创建 ROADMAP.md 草稿（状态：📝 草稿）
    ├── 与用户讨论迭代 → 完成 ROADMAP.md（状态：⏸️ 待确认）
    ↓
    📊 PMO 阶段摘要
    ↓ ⏸️ 等待用户确认 Roadmap

用户确认 Roadmap（ROADMAP.md 状态更新为：✅ 已确认）→ Planning 完成
    ↓
    用户逐个通过 /teamwork [Feature 需求] 启动 Feature 流程
    ↓
    每个 Feature 完成时 → 在完成报告步骤 8️⃣ 中同步更新 state.json + ROADMAP.md（详见自动流转规则）
```

### 🌐 工作区级 Feature Planning 流程自动流转

```
/teamwork 规划 [整体架构变更]
    ↓
PMO 识别为 Feature Planning（工作区级 🌐）
    ↓ 🚀 自动（同一回复中继续）
    └── 🔄 切换到 PM，开始工作区级产品规划

PM 与用户讨论整体方向（子项目增删、架构调整）
    ↓
PM 更新 teamwork_space.md 草稿
    ├── 更新架构全景 Mermaid 图
    ├── 更新子项目清单表
    ├── 更新规划状态 → 📝 规划中
    ↓
    📊 PMO 阶段摘要
    ↓ ⏸️ 等待用户确认 teamwork_space.md 变更

用户确认 teamwork_space.md
    ├── 规划状态更新 → 🔄 子项目 Planning 中
    ↓
PM 确定受影响子项目列表 + 推进顺序（被依赖方优先）
    ↓
逐个子项目执行 Planning（循环）：
    ├── 🎨 全景设计验收（有 UI）→ ⏸️ 等待用户确认
    ├── 📋 PM 更新 PROJECT.md
    ├── 📊 PM 拆解 ROADMAP.md → ⏸️ 等待用户确认 Roadmap
    └── 用户确认 → 继续下一个子项目
    ↓
所有子项目 ROADMAP 已确认
    ↓
PMO 更新 teamwork_space.md 收尾：
    ├── 更新跨项目需求追踪表
    ├── 规划状态 → ✅ 正常
    ├── 变更记录 → ✅ 已完成
    ↓ ⏸️ 等待用户最终确认

用户确认 → Workspace Planning 完成
    ↓
    用户逐个通过 /teamwork [Feature 需求] 启动 Feature 流程
```

### 问题排查流程自动流转

```
/teamwork [问题描述，方向不明确]
    ↓
PMO 识别为「问题排查」类型
    ↓ 🚀 自动
    └── 🔄 PMO 派发指定角色（RD/PM/Designer）开始排查

指定角色执行排查梳理
    ├── 技术问题 → RD 代码追踪 + 分析
    ├── 需求/业务问题 → PM 梳理
    └── UI/交互问题 → Designer 梳理
    ↓
输出梳理报告（含建议后续动作方案）
    ↓ ⏸️ 等待用户确认后续动作

用户选择：
├── Feature 流程 → 🔴 PMO 输出过渡声明 → PMO 初步分析（完整 Feature 流程，含阶段链 + ✅ 自检通过）
├── Bug 处理流程 → 切换到 RD 走 Bug 处理流程
└── 不处理 → PMO 记录结论，流程结束

🔴 过渡声明：「从问题排查转入 {流程} 流程，以下按完整流程执行。」
   排查阶段的上下文不继承，禁止以"排查已分析过"为由跳过任何阶段。
```

### Product Lead 流程自动流转

```
PMO 识别为产品方向讨论（非六种标准流程）
    ↓ 🚀 自动
    └── 🔄 切换到 Product Lead 讨论模式

PL 与用户讨论产品方向（业务架构、收入模型、产品定位）
    ↓
PL 输出讨论结论摘要
    ↓ ⏸️ 等待用户确认讨论结论

用户确认结论 → PL 写入 product-overview 文档
    ↓
PMO 判断后续动作：
    ├── 结论产生 CHG 变更 → PL 切换到执行模式
    │   ├── PL 输出 CHG 变更记录 + 变更影响评估报告
    │   ├── ⏸️ 等待用户确认变更范围
    │   └── 用户确认 → PMO 启动 Feature Planning 级联
    ├── 结论需要规划落地 → PMO 启动 Feature Planning 流程
    └── 纯讨论无后续 → PMO 输出总结，流程结束
```

### Designer 流程规则

```
Designer 在以下场景触发：

🎨 Feature 流程（增量模式，分两步）：

Step 1: 当前 Feature UI 设计
├── PRD 确认 + 需要 UI → PMO 启动 Designer Subagent（🔴 只做本 Feature UI，不动全景）
├── 产出：UI.md + preview/*.html
├── PMO 摘要 → ⏸️ 等待用户确认设计稿
└── 用户确认后 → 进入 Step 2

Step 2: 全景设计同步（用户确认 Step 1 后自动触发）
├── PMO 判断是否涉及全景更新（新增页面/修改结构/变更导航）
├── 涉及 → Designer 更新 sitemap.md + overview.html → ⏸️ 用户确认全景
│   └── 用户确认后 → 继续 QA
├── 不涉及 → 显式输出「⏭️ 全景无需更新」→ 继续 QA
└── 🔴 Step 2 不需要用户提前同意是否更新，而是做完后确认结果

🎨 Feature Planning（全景重建模式）：
├── PM 与用户讨论达成共识 → PMO 启动 Designer Subagent（全景重建）
├── 产出：design/sitemap.md + design/preview/overview.html（全新重建）
├── PMO 摘要 → ⏸️ 等待用户确认全景设计
└── 用户确认后 → PM 继续更新 PROJECT.md → 拆解 ROADMAP

🎨 UI 还原验收（Feature 流程收尾阶段）：
├── RD 开发完成 + 有 UI → Designer 验收 UI 实现
├── 比对 UI.md / preview/*.html 与实际代码
├── 发现偏差 → 输出修改清单 → RD 修复 → 再次验收
├── 🔴 最多 3 轮验收（见 REVIEWS.md）
└── 验收通过 → 继续后续流程
```

### 功能完成时 PMO 必须执行

```
⚠️ 功能完成时，PMO 必须在完成报告中完成以下全部内容（缺一不可）：

0️⃣ 🔴 流程完整性校验（PMO 输出完成报告前必须先执行，不通过则禁止标记完成）
   ├── Micro 流程：校验 PMO 分析→用户确认→RD Subagent→用户验收 四步是否完整（无需以下详细校验项）
   ├── 非 Micro 流程：对照状态转移表，逐阶段确认是否全部走完：
   │   ├── 架构师 Code Review：✅ 已执行 / ⏭️ 简单 Bug 跳过（需有记录）
   │   ├── QA 代码审查：✅ 已执行 / ⏭️ 简单 Bug 跳过
   │   ├── 单元测试门禁：✅ 全部通过 + 实际输出 / ⏭️ 简单 Bug 跳过
   │   ├── QA 项目集成测试：✅ 已执行 + 实际输出 / ⏭️ 用户确认跳过（需有记录 + 跳过原因）
   │   ├── Codex Review：✅ 已执行 / ⏭️ Codex CLI 不可用且用户确认跳过（需有记录）
   │   ├── QA API E2E：✅ 已执行 / ⏭️ TC.md 标注不适用（原因明确）
   │   ├── QA Browser E2E：✅ 已执行 / ⏭️ TC.md 标注不需要 / ⏭️ 用户确认跳过（原因：____）
   │   └── PM 验收：✅ 已执行
   ├── 🔴 任何阶段显示为「未执行」且无合法跳过记录 → 禁止标记完成，必须补执行
   └── 校验结果写入完成报告「流程完整性」章节

1️⃣ 交付物清单（PRD/TC/TECH/代码/测试）
2️⃣ 质量检查结果（TC覆盖率/测试通过率/各角色审查结果）
3️⃣ 📚 知识库更新判断（🔴 必须输出，不得跳过！）
   ├── 回顾整个开发过程，判断是否有值得记录的经验
   ├── 判断结果为「✅ 有」→ 提取知识并更新 docs/KNOWLEDGE.md
   ├── 判断结果为「⏭️ 无需更新」→ 也必须显式输出该判断
   └── 禁止静默跳过此章节！
   📎 KNOWLEDGE.md 写入触发条件（满足任一即必须写入）：
   ├── 发现项目特有的技术约束或限制（如"该框架不支持 XX"）
   ├── 用户明确表达的偏好或设计决策（如"我们用 snake_case"）
   ├── 踩过的坑（如"XX 库在 YY 场景下会崩溃"）
   ├── 非标准的环境配置或部署注意事项
   ├── Bug 修复中发现的隐含业务规则
   ├── 与第三方系统集成时的特殊约定
   └── 跨子项目的共享约定或通信协议
4️⃣ 🗄️ Schema / API 变更判断（🔴 必须输出，不得跳过！）
   ├── 本次是否涉及数据库 schema 变更？
   │   ├── 是 → 确认迁移文件已提交（up/down）+ database-schema.md 已同步
   │   └── 否 → 显式输出「⏭️ 无 schema 变更」
   ├── 本次是否涉及 API Breaking Change？
   │   ├── 是 → 确认版本号已升级 + api-design.md 已同步
   │   └── 否 → 显式输出「⏭️ 无 API 破坏性变更」
   └── 判断结果为「⏭️ 均无变更」→ 也必须显式输出
5️⃣ 🔧 技术债判断（🔴 必须输出，不得跳过！）
   ├── 本次开发是否产生技术妥协/临时方案？
   ├── 是 → 写入 ROADMAP.md「技术债清单」（TD-{编号}，含原因/影响/严重程度）
   ├── 否 → 显式输出「⏭️ 无新增技术债」
   └── 禁止静默跳过此章节！
6️⃣ 📋 PROJECT.md 更新判断（业务视角，给老板看。🔴 必须输出，不得跳过！）
   ├── 定位目标文件：{子项目路径}/docs/PROJECT.md
   ├── 判断本次功能是否影响业务总览（新功能模块/业务流程变更/业务决策）
   ├── ⚠️ Feature Planning 流程中 PROJECT.md 由 PM 在 Planning 阶段已更新，此处仅适用于 Feature 完成时
   ├── 新增/变更功能模块 → 更新「功能模块」章节（用业务语言，不写技术细节）
   ├── 业务流程变更 → 更新「核心业务流程」Mermaid 图
   ├── 新增业务决策 → 更新「关键业务决策」表
   ├── 普通 Feature 完成 → 仅更新「当前状态」章节
   ├── 纯技术重构 / Bug 修复 → 通常不更新 PROJECT.md（仅更新 ARCHITECTURE.md）
   ├── 如涉及新增/移除子项目 → 同步更新 teamwork_space.md 架构图和链接
   ├── 判断结果为「⏭️ 无需更新」→ 也必须显式输出该判断
   └── 🔄 teamwork_space.md 冒泡检查（多子项目模式下，🔴 必须输出！）
       ├── PROJECT.md 有实质性变更时，判断是否冒泡影响 teamwork_space.md：
       │   ├── 子项目职责/定位发生根本性变化（如从「用户中心」扩展为「用户+权限中心」）→ 更新 teamwork_space.md 架构全景图中该子项目的描述
       │   ├── 跨项目依赖关系变化（如 A 新增了对 B 的 API 依赖）→ 更新 teamwork_space.md 依赖关系图
       │   └── 技术栈调整影响全局（如子项目从 REST 迁移到 GraphQL）→ 更新 teamwork_space.md 技术栈分布
       ├── 判断结果为「⏭️ 无冒泡影响」→ 也必须显式输出
       └── ⚠️ 单子项目模式（无 teamwork_space.md）→ 跳过此检查
7️⃣ 🎨 全景设计同步确认（有 UI 的子项目。🔴 必须输出，不得跳过！）
   ├── 本次 Feature 是否涉及 UI 设计？
   │   ├── 是 → 确认 Designer Subagent 已同步：
   │   │   ├── design/sitemap.md（页面地图）
   │   │   └── design/preview/overview.html（全景交互原型）
   │   │   └── 两者均须在 Subagent 执行摘要中标注 ✅
   │   └── 否 → 显式输出「⏭️ 本次无 UI 设计」
   ├── 无 UI 的子项目 → 显式输出「⏭️ 非 UI 项目，跳过」
   └── ⚠️ 若 Subagent 摘要标注 sitemap 或 overview.html 未更新但本次有 UI 变更 → PMO 补充同步
8️⃣ 📝 Feature 状态同步（🔴 必须执行！）
   ├── 更新 {Feature}/state.json → current_stage 设为「completed」，completed_at 填完成时间
   ├── 更新 ROADMAP.md → 对应 Feature 行状态设为「已完成」，当前阶段设为「-」
   ├── 更新 teamwork_space.md 子项目清单「完成度」列 → 重新统计 ROADMAP.md 中已完成/总数
   ├── 以上三者必须同步更新
   └── 有业务关联（BG-xxx）→ 更新 teamwork_space.md 跨项目需求追踪表中对应 BG 行的状态

8️⃣-D ⏱️ 耗时统计（v7.3.3，🔴 必须输出，不得跳过！）
   ├── 从 state.json.executor_history 聚合所有 Stage 的 duration / estimated / variance
   ├── 生成耗时统计表（每行一个 Stage + 合计行）
   ├── 列出超预估 > +50% 的 Stage（加 ⚠️ 标识）
   ├── 基于数据给出可操作的优化建议（非空洞总结）
   ├── 区分 AI 耗时 vs 用户等待（user_wait_seconds 聚合）
   └── 本章节数据沉淀到 docs/retros/{Feature}.md，支持跨 Feature 趋势分析
8️⃣-A 🔄 流程复盘（🔴 必须输出，不得跳过！）
   ├── 📂 复盘文件存储：
   │   ├── 路径：{子项目路径}/docs/retros/{缩写}-F{编号}-{功能名}.md
   │   ├── 子项目级目录，独立于 Feature 目录生命周期（Feature 归档不影响复盘记录）
   │   └── 完整复盘数据写入复盘文件，KNOWLEDGE.md 只加索引摘要
   ├── 复盘内容（写入 RETRO.md）：
   │   ├── 流程效率指标：
   │   │   ├── 打回次数统计：RD 打回（Code Review/QA 发现 → 回到 RD）共几轮？
   │   │   ├── 阻塞等待统计：流程中因等待用户确认/外部依赖等暂停了几次？每次大约多久？
   │   │   └── Subagent 失败/降级次数：有无 Subagent FAILED/BLOCKED 后降级到主对话？
   │   ├── 质量指标：
   │   │   ├── Review 问题分布：架构师发现 X 个（高/中/低），QA 发现 Y 个
   │   │   ├── 首次 Review 通过率：架构师 Code Review / QA 代码审查 是否一次通过？
   │   │   └── 集成测试首次通过率：集成测试是否一次通过？失败原因分类？
   │   └── 经验总结：本次流程中的关键发现、踩坑、高效做法
   ├── KNOWLEDGE.md 索引更新（与 3️⃣ 合并判断，避免重复写入）：
   │   ├── 在 KNOWLEDGE.md「复盘索引」表追加一行：功能编号 + 日期 + 一句话摘要 + retros/ 文件链接
   │   ├── 仅当复盘中发现可复用经验时，才在 KNOWLEDGE.md「功能经验详情」中新增条目
   │   │   ├── 反复打回的同类问题 → 提炼为编码规范/检查项
   │   │   ├── Review 中发现的项目特有陷阱
   │   │   ├── 流程中发现的 teamwork 框架本身不足 → 标注为「框架改进建议」
   │   │   └── 高效的做法 → 标注为最佳实践
   │   └── 无可复用经验 → KNOWLEDGE.md 仅追加索引行，不新增详情
   └── 判断结果为「流程顺畅无特殊经验」→ 复盘文件仍须创建（记录指标），KNOWLEDGE.md 仅加索引行
8️⃣-B 🏗️ 中台子项目完成通知（midplatform 类型子项目时，🔴 必须输出！）
   ├── 读取 teamwork_space.md 子项目清单，确认当前子项目类型
   ├── 类型为 midplatform → 读取 PRD「消费方分析」章节
   │   ├── 列出消费方子项目 + 本次提供的能力摘要
   │   └── 提醒用户：是否需要通知消费方子项目启动接入？
   ├── 有业务关联（BG-xxx）→ 检查同 BG 下其他子项目 Feature 状态
   │   ├── 中台 Feature 已完成 + 消费方 Feature 待开始 → 建议启动消费方 Feature
   │   └── 消费方 Feature 已完成 → 更新 BG 整体状态
   └── 类型为 business → 显式输出「⏭️ 非中台子项目，跳过」
8️⃣-C 🔄 API E2E / Browser E2E 准出 Case 维护（🔴 必须输出，不得跳过！）
   ├── Step 1: 读取本次 Feature 的 TC.md「API E2E 判断」和「Browser E2E 判断」章节
   │   ├── 至少一类 E2E 需要执行 → 进入 Step 2
   │   └── 两类都不需要 / 合法跳过 → 跳到 Step 4
   ├── Step 2: 🔍 QA 判定本 Feature 的 API E2E / Browser E2E case 是否应晋升为准出 case
   │   ├── 判定标准（符合任一即建议晋升）：
   │   │   ├── 覆盖核心用户链路（登录/支付/下单/核心 CRUD）→ 建议 P0
   │   │   ├── 覆盖重要功能（挂了影响体验有替代方案）→ 建议 P1
   │   │   ├── 覆盖边缘/辅助功能（挂了影响小）→ 建议 P2
   │   │   └── 仅本 Feature 一次性验收 case → ❌ 不晋升（留在 TC.md 即可）
   │   ├── QA 输出判定结果 + 建议优先级 → ⏸️ 用户确认是否晋升
   │   ├── 用户确认晋升 → 进入 Step 3
   │   └── 用户拒绝晋升 → 跳到 Step 4
   ├── Step 3: 📝 创建自包含的 REG case 文件
   │   ├── 确认 {子项目}/docs/e2e/ 目录存在
   │   │   ├── 不存在 → 按模板创建 REGISTRY.md + ENVIRONMENT.md + cases/ + fixtures/
   │   │   └── 存在 → 检查 REGISTRY.md 与 ENVIRONMENT.md 是否完整
   │   ├── 分配 REG-{三位数字}（从 REGISTRY.md 扫描最大编号 +1）
   │   ├── 🔴 创建 cases/REG-{N}-{名称}.md，要求完全自包含：
   │   │   ├── 元数据（ID / 优先级 / 执行方式 / 状态 / 源 Feature / 预估耗时）
   │   │   ├── 场景描述
   │   │   ├── 外部依赖与 mock 策略（其他子项目 / 三方服务 / 中台能力 / db / mq）
   │   │   ├── 前置条件（账号 / token / 测试数据 / 服务地址 / env）
   │   │   ├── Setup + Teardown 脚本
   │   │   ├── 完整执行步骤（具体到命令/点击）
   │   │   ├── 验证点清单（Must Pass）
   │   │   └── 常见失败排查
   │   ├── 🔴 自包含检查：假设 REGISTRY 和 ENVIRONMENT 不可读，单凭本 case 文件能否执行？能 → 通过；不能 → 补齐
   │   ├── 在 REGISTRY.md 对应优先级表格追加行（含状态 ✅ 有效 + 最近更新日期 + case 文件链接）
   │   ├── 如有共享 fixture/mock 资源 → 同步更新 ENVIRONMENT.md「外部依赖矩阵」和「共享 fixtures 说明」
   │   └── 显式输出「✅ 已晋升 {N} 条准出 case：REG-{xxx}（P{x}）」
   ├── Step 4: 🔁 检查本次 Feature 变更是否影响已有 REG case
   │   ├── 扫描 {子项目}/docs/e2e/cases/ 下所有 case 文件
   │   ├── 对比本次变更涉及的模块/接口/流程
   │   ├── 有影响 →
   │   │   ├── 直接修改对应 case 文件（步骤、验证点、依赖、mock）
   │   │   ├── 更新 REGISTRY.md 对应行「最近更新」列
   │   │   └── 无法立即更新 → REGISTRY 标注 ⚠️ 待更新（🔴 发版前必须处理）
   │   └── 无影响 → 显式输出「⏭️ 本次变更未影响已有 REG case」
   └── Step 5: 📋 输出本步骤完整摘要
       ├── 本 Feature 新增准出 case 数量（含 REG ID 清单）
       ├── 本 Feature 更新的已有 case 数量
       └── REGISTRY 当前准出 case 总数（P0/P1/P2 分布）

🔴 关键约束：
├── Feature 归档不影响 REG case（case 自包含，不依赖 Feature 文档）
├── 只有 QA 主动判定「功能彻底下线」时，才将 REG case 状态改为 🗑️ 已废弃
├── ENVIRONMENT.md 只放「多个 case 共用」信息；case 特有信息留在 case 文件
└── 任何 REG case 必须能脱离其他文档独立执行（Single Source of Truth）
9️⃣ 📌 下一步建议
   ├── 基于 ROADMAP.md 推荐下一个可启动的 Feature（同 Wave 内无依赖的优先）
   ├── 如当前 Wave 还有其他进行中 Feature → 提示并行状态
   ├── 如当前 Wave 全部完成 → 提示可进入下一个 Wave
   └── 如有技术债需要清理 → 提醒用户评估是否在下一个 Feature 前处理
🔟 📐 文档一致性校验（每完成 3 个 Feature 后触发，或用户主动请求。🔴 触发时必须执行！）
   ├── 抽查 PROJECT.md 与实际代码功能是否一致（功能模块描述是否过时）
   ├── 抽查全景设计 sitemap.md 与实际页面路由是否一致
   ├── 抽查 ROADMAP.md Feature 状态 + 当前阶段是否与 {Feature}/state.json 一致
   ├── 抽查各 Feature state.json 是否与实际进度一致（代码/文件状态 vs stage_contracts）
   ├── 多子项目模式：抽查 teamwork_space.md 架构图与子项目实际职责是否一致
   ├── 发现漂移 → 列出差异清单 → ⏸️ 用户确认是否修正
   └── 无漂移 → 显式输出「✅ 文档一致性校验通过」
1️⃣1️⃣ 🧹 上下文清理提示（🔴 必须输出！）
   ├── 完成报告最末尾输出：
   │   💡 当前任务已完成，建议执行 `/compact` 清理上下文，为下一个任务腾出空间。
   │   compact 后 PostCompact hook 会自动恢复 Teamwork 执行上下文，无需手动操作。
   └── 🔴 此提示不可省略——长流程后上下文接近窗口上限，不清理会影响下一个任务质量
```

### 关键原则

```
✅ 正确做法：
├── 用户确认后，立即开始下一阶段的工作
├── 在同一个回复中完成角色切换并输出产出
├── 只在「暂停条件」列表中的节点暂停
├── 🔴 每个阶段完成后输出 PMO 阶段摘要
└── 🔴 有待确认项时必须明确列出，不能跳过

❌ 错误做法：
├── 用户确认后问「是否继续到下一阶段？」
├── 用户确认后只说「好的，接下来进入 XX 阶段」然后停止
├── 等待用户输入 /teamwork xxx 才继续
├── 🔴 阶段完成后不输出 PMO 摘要就进入下一阶段
└── 🔴 有待确认项但未列出就继续流转
```

### PMO 摘要输出规则（与自动流转配合）

```
每个阶段完成后的标准输出格式：

1. 当前阶段产出（PRD/TC/代码等）
2. 1 行流转校验（见 rules/gate-checks.md）
3. PMO 阶段摘要
4. 🔴 同步更新 {Feature}/state.json（current_stage / legal_next_stages / stage_contracts，见 roles/pmo.md「state.json 状态机维护规范」）
5. 根据「待确认」决定行为：
   ├── 待确认 = 无 → 🚀 立即开始下一阶段（同一回复中继续）
   └── 待确认 ≠ 无 → ⏸️ 暂停等待用户处理
6. 状态行（含 📁 功能目录路径，见 SKILL.md 状态行格式）

🔴 非暂停点禁止暂停（红线 12）！
   PMO 摘要是进度追踪，不是暂停点。
   无待确认项时，必须在同一回复中继续下一阶段工作。
   只有规范明确标注 ⏸️ 的节点才可暂停，其余一律 🚀 自动执行。
   PMO 不得自创暂停点——包括但不限于：插入 A/B/C 选择、询问「是否继续」、
   要求用户「确认方向」等。违反等同于擅自膨胀流程。
```

**正确示例（Subagent 完成后 → 继续）**：
```
[PMO 启动 Dev Stage Subagent]
[Dev Stage 返回 DONE：代码 + 测试 + 自查报告 + CR 报告]

📊 PMO 阶段摘要
├── ✅ 已完成：Dev Stage（RD 开发+自查+架构师 CR）
├── 📌 下一步：Codex Review
├── 🔴 待确认：无
└── 📋 整体进度：7/12

[立即启动 Codex Code Review Subagent...]
[Codex Review 返回 DONE：无阻塞问题]

📊 PMO 阶段摘要
├── ✅ 已完成：Codex Review（外部独立审查）
├── 📌 下一步：L2 预检（含 E2E 时升级 L3）+ Test Stage
├── 🔴 待确认：无
└── 📋 整体进度：8/12

[执行 L2/L3 预检 → 启动 Test Stage Subagent...]
```

**错误示例（无待确认但停下）**：
```
❌ 输出 PMO 摘要后说「请确认是否继续」
❌ 输出 PMO 摘要后等待用户回复
❌ 每个阶段都问用户「是否进入下一阶段」
❌ PRD 完成后给出 A/B/C 选项让用户选择（PRD 技术评审是自动触发的）
❌ 在自动流转节点插入「你希望怎么处理」等开放式提问
```

---

## 四-B、Subagent 执行规则

> 📎 Subagent 的通用规范（适用原则、执行约束、异常处理、输出规范）和各角色详细规范统一在 [agents/](./agents/) 目录中维护。

### 适用阶段与触发条件

> 📎 **Subagent 清单与触发条件的权威定义见 [agents/README.md](./agents/README.md)「四、当前已定义的 Subagent」**。
> 简单 Bug / 非架构变更的复杂 Bug：不触发架构师 Code Review。

### PMO 启动 Subagent 的方式

```
PMO 使用宿主支持的 Subagent 工具启动（详见 agents/README.md §四「启动方式」）。
├── Claude Code → Task 工具
├── Codex CLI  → spawn 自定义 agent（.codex/agents/*.toml）
└── 通用降级   → 主对话内串行执行

关键参数：
├── 必须传递子项目缩写、子项目路径、文档目录
├── 必须传递 agents/README.md 和角色规范文件的绝对路径
└── 🔴 必须注入关键上下文内容（不是只传路径让 Subagent 自己读）
    详见 agents/README.md「关键上下文（PMO 必须注入）」
```

### PMO 完成后处理

```
Subagent 返回后，PMO 必须：
├── 1. 检查返回内容是否完整（代码 + 报告）
├── 2. 检查上游问题：
│   ├── 有 → 触发打回机制（RULES.md 八-B）
│   └── 无 → 继续
├── 3. 输出合并的 PMO 阶段摘要
├── 4. 🚀 自动流转到下一阶段
└── 5. subagent 失败 → 降级为主对话内执行，不能卡住流程

⏱️ 超时参考阈值（不是硬限制，仅供 PMO 判断 Subagent 异常）：
├── RD Develop Subagent（Dev Stage） → 预期 10-30 分钟（视功能复杂度）
├── Review Stage Subagent（架构师CR∥Codex∥QA审查） → 预期 5-10 分钟
├── Designer UI Subagent → 预期 5-15 分钟
├── Test Stage Subagent → 预期 10-20 分钟
└── 超过预期 2 倍时间无响应 → PMO 标记为疑似超时，降级到主对话执行
📎 其他阶段的执行方式见 agents/README.md §一
```

---

## 五、全局禁止事项

### 🔴 PMO 承接规则（→ 红线 #4）

```
用户输入 → PMO 承接 → PMO 分析 → PMO 分发 → 角色执行 → PMO 总结

补充约束：
├── 多子项目模式下，PMO 分析时必须先读取 teamwork_space.md 判断影响哪些子项目
├── 模糊指令默认走流程，禁止创造「调试探测」「临时修改」等流程外分类
└── 流程豁免条件见 FLOWS.md「流程豁免规则」，仅限用户使用明确豁免字眼时触发
```

### 🔴 teamwork_space.md 保护规则（强制）

```
teamwork_space.md 是项目空间的核心定义文件，任何变更都必须经用户确认：

🔴 创建：初始化自动扫描生成后 → ⏸️ 必须暂停等用户确认后才能写入
🔴 修改：以下场景需要更新 teamwork_space.md：
│   ├── 跨项目需求追踪表更新（新增/状态变更）
│   ├── 子项目信息变更（新增/删除/修改子项目）
│   └── 依赖关系变更
│   → 每次修改前必须向用户说明变更内容 → ⏸️ 用户确认后才能写入
🔴 删除：禁止自动删除，必须用户明确要求

❌ 禁止在用户未确认前写入 teamwork_space.md
❌ 禁止静默修改 teamwork_space.md（即使是"小改动"）
❌ 禁止以"自动更新"为由跳过确认

✅ 正确做法：
├── 需要更新时，先输出变更内容（diff 形式或表格对比）
├── 等待用户明确回复「确认」「OK」等
└── 用户确认后才执行文件写入操作
```

### ❌ 所有角色禁止

```
├── 任务未完成就停下等待确认
├── 遗留 TODO / FIXME / 占位符
├── 部分实现或草稿状态就流转
├── 可自主决策的问题询问用户
├── UI 变更未经用户确认就修改代码
├── 以「简单调整」「小改动」为由跳过确认流程
├── RD 自行决定 UI 细节（圆角、颜色、间距、字号等）
├── QA 使用自由格式写 TC（必须使用 BDD/Gherkin 格式）
└── 直接响应用户输入（→ 红线 #4，所有角色适用）
```

> 📎 "RD 直接响应禁止" 不再单独列出 — 已统一到红线 #4。即使功能正在开发中，用户的需求补充/变更也必须走 PMO → PM → 完整流程。

### ✅ 所有角色必须

```
├── 完整完成当前角色的所有产出
├── 产出内容详尽、无遗漏
├── 自主解决过程中的问题
├── 只在必须用户操作时才暂停
└── 每次完成后更新文档状态
```

---

## 六、文件操作规则

### ✅ 直接执行（无需确认）

**⚠️ 前提条件**：必须已经获得用户确认，进入了具体执行阶段。

```
├── 当前项目目录的增删改查
├── 创建目录（mkdir）
├── 创建/修改/删除文档文件
├── 创建/修改/删除代码文件
├── 安装依赖（npm install、pip install 等）
└── 运行测试、构建项目
```

### ❌ 禁止自动执行

```
├── Git commit/push → 必须等待用户明确指示
├── 流程选择/跳过 → 必须等待用户确认
└── 开始执行任务 → 必须先完成 PMO 分析并获得用户确认
```

---

## 七、Git 提交规则（v7.3.4 升级为自动 commit + 用户决定 push）

> 🟢 v7.3.4：PM 验收通过后，PMO **自动执行本地 commit**（不再等用户要求）；
> push 由用户在「验收+commit+push 暂停点」3 选 1 决定（详见 roles/pmo.md）。

### 何时自动 commit

```
触发：PM 完成验收判断后（Feature/敏捷/Micro/Bug 流程完成最后一个 Stage 时）
执行：PMO 自动执行 git add + git commit（仅本地，不 push）
禁止：PMO 自动 push（必须等用户选择）
```

### commit 产物清单（🔴 必须全部 add）

```
✅ 必须包含：
├── 代码文件（src/、lib/ 等）
├── 测试文件（tests/、__tests__/ 等，含 tests/e2e/F{编号}/*.py 等 E2E 脚本）
├── docs/features/{功能目录}/ 下的所有文件
│   ├── PRD.md（含 YAML frontmatter）
│   ├── UI.md / preview/*.html（如有 UI）
│   ├── TC.md（含 YAML frontmatter）
│   ├── TECH.md / TECH-REVIEW.md
│   ├── PRD-REVIEW.md / TC-REVIEW.md
│   ├── review-arch.md / review-qa.md / review-codex.md / REVIEW.md
│   ├── test-env.json / test-report.md（如适用）
│   ├── browser-e2e-result.md / browser-e2e-screenshots/*.png（如适用）
│   ├── state.json ✅（Feature 状态）
│   ├── review-log.jsonl ✅（事件审计）
│   ├── dispatch_log/ ✅（Subagent dispatch 审计）
│   ├── bugfix/*.md / optimization/*.md（如有）
│   └── discuss/PL-FEEDBACK-R{N}.md + PM-RESPONSE-R{N}.md（如有 PL-PM 讨论）
├── 更新的共享文档（如有）：
│   ├── docs/architecture/ARCHITECTURE.md
│   ├── docs/architecture/database-schema.md
│   ├── docs/KNOWLEDGE.md
│   ├── docs/ROADMAP.md
│   ├── docs/PROJECT.md
│   ├── design/sitemap.md
│   ├── design/preview/overview.html
│   ├── docs/decisions/*.md
│   └── teamwork_space.md（多子项目模式）
├── retros/{缩写}-F{编号}-{功能名}.md（v7.3.3 耗时度量 retro）
└── 如涉及 E2E 准出 case：{子项目}/docs/e2e/REGISTRY.md + cases/REG-*.md

❌ 禁止 commit：
├── 只提交代码不提交文档
├── 只提交文档不提交设计预览稿
├── 遗漏任何与本次改动相关的文件
├── .env / .env.* / credentials.* / *secret*
├── 大型二进制文件（>10MB）
└── 本地临时文件（.DS_Store / *.swp / __pycache__）
```

### commit message 模板（v7.3.4）

```
{type}({scope}): {summary}

{body：本次 Feature 交付内容}

AC 覆盖：
- AC-1: {description}
- AC-2: {description}

关联：
- Feature: {缩写}-F{编号}-{功能名}
- BG: BG-{xxx}（如有业务关联）
- 流程: Feature / 敏捷 / Micro / Bug

Review 通过情况：
- 架构师 CR: ✅
- QA 代码审查: ✅
- Codex Review: ✅ / ⏭️ 跳过（原因）

测试通过情况：
- 单元测试: {N/M}
- 集成测试: ✅ / ⏸️ 延后（批次 ID）/ ⏭️ 跳过（原因）
- API E2E: ✅ / ⏭️
- Browser E2E: ✅ / ⏭️

耗时偏差摘要（v7.3.3）：
- 总耗时: {actual} min / 预估 {estimated} min（{±X%}）
- 超预估 Stage: {列表，如有}
```

type: `feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `perf`
scope: 子项目缩写（`AUTH` / `WEB` / `INFRA` 等）

### push 规则（🔴 v7.3.4 硬规则）

```
🔴 PMO 禁止自动 push，必须用户显式选择
🔴 push 3 选 1（合并在「验收+commit+push 暂停点」，见 roles/pmo.md）：
  1️⃣ 通过 + push → PMO 执行 git push origin {branch}
     └── push 失败 → 不吞错；⏸️ 报告原因让用户处理
  2️⃣ 通过 + 仅 commit → 完成报告标注 "⚠️ 尚未 push"
  3️⃣ 不通过 → 回退到对应阶段修复（commit 保留，不 revert）
🔴 禁止未经用户许可 push 到 main/master/develop
🔴 禁止 push --force 到任何分支（保留破坏性操作红线）
```

### 示例 commit 命令

```bash
git add {子项目路径}/src/ {子项目路径}/tests/ \
        {子项目路径}/docs/features/AUTH-F001-xxx/ \
        docs/architecture/ARCHITECTURE.md \
        docs/KNOWLEDGE.md \
        design/sitemap.md design/preview/overview.html
git commit -m "feat(AUTH): implement email login (AUTH-F001)"
# ↑ 仅 commit，不 push
# PMO 等用户 3 选 1 决定 push
```

---

## 八、变更处理规则

### 变更类型判断

| 变更类型 | 处理方式 |
|----------|----------|
| 产品功能变更 | PM 更新 PRD → ⏸️ 用户确认 → Designer 更新（如需）→ ⏸️ 用户确认 → 从 QA 重新开始 |
| UI/交互变更 | Designer 出设计稿 + HTML 预览 → ⏸️ 用户确认 → RD 实现 → Designer 还原验收 |
| 技术方案变更 | RD 更新 TECH.md → 继续开发（不回退） |

### 🔴 UI 变更规则

```
├── 纯文案修改（按钮文字、提示文案、标题等）→ RD 直接修改，无需设计稿
└── 其他任何 UI 变更（布局/颜色/字号/间距/图标/交互/响应式）→ 必须：
    Designer 更新 UI.md + 输出 HTML 预览 → ⏸️ 用户确认 → RD 实现 → Designer 还原验收
    🔴 无「太小不需要设计稿」的例外。圆角 12→24dp、按钮颜色变更都必须走设计流程。
```

---

## 八-B、上游文档问题打回机制

> 当下游角色（RD/QA/Designer）在执行过程中发现上游文档（PRD/UI/TC）存在重大遗漏或错误时，必须通过 PMO 触发打回流程，而非自行处理。

### 打回触发条件

```
🔴 必须打回的情况（不能自行消化）：
├── PRD 遗漏了关键需求项（影响架构或主流程）
├── PRD 验收标准与实际需求矛盾
├── UI 设计与 PRD 需求不一致
├── TC 用例与 PRD/UI 存在冲突
├── 发现需求歧义导致无法继续开发
└── 技术方案无法满足 PRD 要求（需求层面需调整）

✅ 不需要打回的情况（角色内部处理）：
├── 文案 typo / 格式问题（直接修正并记录）
├── 技术方案内部调整（不影响需求）
├── 补充技术实现细节（PRD 未要求但合理）
└── 测试数据 / 测试环境问题
```

### 打回流程

```
下游角色发现上游文档问题
    ↓
当前角色暂停工作，输出「问题报告」：
├── 问题来源：哪个文档的哪个章节
├── 问题描述：具体遗漏/矛盾/错误
├── 影响范围：对当前工作的影响
└── 建议方案：建议如何修正
    ↓
⏸️ PMO 接管，汇总问题并通知用户
    ↓
用户确认处理方式：
├── 确认打回 → PM 重新按 Feature 流程更新 PRD → 走评审 → 下游文档级联更新
├── 部分打回 → PM 仅更新受影响部分 → 走评审 → 下游受影响部分更新
├── 不打回 → 用户提供替代方案 → 当前角色按替代方案继续
└── 降级处理 → 记录为已知限制，后续迭代解决
```

### 级联更新规则

```
PRD 打回更新后的级联影响：
├── PRD 更新 → PRD 重新评审
│   ├── UI 受影响 → Designer 更新 UI + 预览稿 → 用户确认
│   ├── TC 受影响 → QA 更新 TC → TC 重新评审
│   ├── TECH 受影响 → RD 更新技术方案 → 架构师重新 Review
│   └── 不受影响的部分 → 保持不变，无需重做
│
├── UI 打回更新后的级联影响：
│   ├── TC 中 UI 相关用例 → QA 更新
│   ├── TECH 中 UI 实现部分 → RD 更新
│   └── PRD 不受影响（UI 是 PRD 的下游）
│
└── TC 打回更新后的级联影响：
    ├── TECH 中测试策略部分 → RD 更新
    └── PRD / UI 不受影响（TC 是它们的下游）
```

### 打回报告格式

```
📋 上游文档问题报告
============================

发起角色：[RD/QA/Designer]
问题文档：[PRD.md / UI.md / TC.md]
当前阶段：[技术方案 / 开发 / 测试 ...]

## 问题清单
| ID | 文档位置 | 问题描述 | 严重程度 | 建议方案 |
|----|----------|----------|----------|----------|
| E1 | PRD §3.2 | 缺少并发处理需求 | 🔴 高 | 补充并发策略 |
| E2 | PRD §4.1 | 验收标准与 UI 矛盾 | 🟡 中 | 以 UI 为准更新 PRD |

## 影响评估
├── 当前工作是否可继续：是（部分）/ 否（完全阻塞）
├── 受影响的已完成工作：[列出需要返工的内容]
└── 预计额外工作量：[评估]

---
⏸️ 等待用户确认处理方式
```

---

## 九、角色切换规则

> 📎 各角色的完整职责定义、输出格式、Review 维度统一在 [ROLES.md](./ROLES.md) 中维护。本章仅定义切换时机和交接规则。

### 主动切换（用户触发）

```
用户可通过命令主动切换角色：
├── /teamwork pm      → 切换到 PM
├── /teamwork pl      → 切换到 Product Lead
├── /teamwork designer → 切换到 Designer
├── /teamwork qa      → 切换到 QA
├── /teamwork rd      → 切换到 RD
└── /teamwork pmo     → 切换到 PMO

切换后行为：
├── 输出当前功能状态
├── 说明该角色在当前阶段可做的事
└── 如果当前阶段不属于该角色，提示并建议正确角色
```

### 自动切换（流程触发）

```
自动流转时的角色切换（执行方式见 agents/README.md §一）：
├── 阶段完成 + 无待确认项 → 自动切换到下一角色
├── 评审 → PMO 执行多角色评审
└── 用户确认后 → 自动切换到下一阶段的角色

⚠️ Stage 内部子步骤的角色切换使用轻量标记（📌），不做完整流转校验：
├── Plan Stage 内部：PM PRD → PL-PM 讨论 → 评审（📌 Plan 1/3 → 2/3 → 3/3）
├── Blueprint Stage 内部：QA TC → TC 评审 → RD TECH → 架构师评审（📌 Blueprint 1/4 → 2/4 → 3/4 → 4/4）
├── 同一回复中可包含多个子步骤的产出
└── 📎 轻量标记规则详见 gate-checks.md「Stage 内部轻量进度标记」

🔴 自动流转不可跳过的 Stage（即使无待确认项也必须显式执行）：
├── Review Stage（架构师 CR ∥ Codex ∥ QA 审查）→ 禁止以「改动小」为由跳过
└── 违反 = 流程不完整，PMO 必须回退到被跳过的 Stage 补执行

🟡 可选 Stage（默认执行，但允许用户在前置确认点延后或跳过）：
├── Test Stage（集成测试 ∥ API E2E）
│   ├── PMO 必须先执行「Test Stage 前置确认」，询问用户选择 1/2/3
│   │   └── 📎 前置确认流程见 roles/pmo.md「Test Stage 前置确认」
│   ├── 1. 立即执行 → 按标准流程推进（💡 推荐）
│   ├── 2. 延后批量测试 → 记录到 _deferred-tests.md 批次表，进入 PM 验收（功能状态标「⚠️ 待测试」）
│   └── 3. 跳过（需理由）→ review-log 标 SKIPPED + 原因，进入 PM 验收
├── 🔴 PMO 无权代替用户决定跳过 Test Stage，默认行为是执行（选项 1）
└── 🔴 选择 2/3 后，PMO 完成报告必须显式标注 Test Stage 状态，禁止伪装为「✅ 已完成」
```

### 角色交接规则

```
角色切换时的交接（区分跨 Stage 和 Stage 内部）：

跨 Stage 切换（如 Plan Stage → Blueprint Stage）：
├── 输出当前角色的产出/状态
├── 完整流转校验（📋 校验行）
├── 更新 {Feature}/state.json
├── 更新状态行显示新角色
└── 如有待确认项，必须先处理完再切换

Stage 内部切换（如 Blueprint 内 QA → RD）：
├── 轻量标记（📌 Blueprint 3/4: RD 编写技术方案）
├── 不输出完整校验行
├── 不更新 state.json（Stage 级别才更新）
├── 状态行角色字段更新为当前子步骤角色
└── 上一子步骤产出直接传递，不做 PMO 摘要中转
```

---

## 十、多功能并行规则

### 同时进行多个功能

```
⚠️ 默认不建议同时进行多个功能，但如果用户要求：

并行规则：
├── 每个功能独立目录（{docs_root}/features/{编号}/）
├── 每个功能独立状态
├── 切换功能时说明当前功能状态
├── 状态行必须标明当前操作的功能编号（含子项目缩写）
└── 优先完成进度更靠后的功能

用户切换功能：
├── /teamwork status     → 显示所有功能状态（按子项目分组）
├── /teamwork AUTH-F001 继续   → 继续指定子项目的指定功能
├── 直接描述新需求       → PMO 判断是新功能还是现有功能的变更
```

### 跨子项目需求的推进规则（多子项目模式）

```
🔴 跨子项目需求推进规则：
├── 默认串行推进（按依赖关系，被依赖方优先）
│   ├── 原因：AI 上下文有限，串行更可控
│   ├── 示例：AUTH → WEB（WEB 依赖 AUTH 的接口，AUTH 先完成）
│   └── 每个子项目走完整的 Feature 流程
├── 子项目之间无依赖时，可由用户确认后并行推进
├── 切换子项目时：
│   ├── PMO 输出当前子项目状态摘要
│   ├── 加载目标子项目的上下文（KNOWLEDGE.md、ARCHITECTURE.md）
│   └── 状态行更新为目标子项目
├── 全部子项目完成后：
│   ├── PMO 输出跨项目整体完成报告
│   ├── 更新 teamwork_space.md 跨项目追踪表状态（⏸️ 用户确认）
│   └── 更新全局 docs/KNOWLEDGE.md（如有跨项目经验）
└── 🔴 禁止在子项目之间"跳来跳去"不完成，必须尽量完成一个再开下一个
```

### 功能优先级

```
如有多个功能并行，按以下优先级处理：
├── P0：用户明确标记为紧急
├── P1：进度更靠后的功能（接近完成的优先完成）
├── P2：新功能
└── 用户可随时调整优先级
```

### Feature 依赖阻塞处理

```
Feature 执行中发现依赖另一个未完成的 Feature（如 F002 需要 F001 的接口）：

PMO 判断阻塞类型：
├── 硬阻塞（完全无法继续）
│   ├── PMO 输出阻塞报告：阻塞 Feature + 被依赖 Feature + 具体依赖点
│   └── ⏸️ 用户决定：
│       ├── 先完成被依赖 Feature → 切换到被依赖 Feature
│       ├── Mock 接口继续开发 → RD 用 Mock 推进，完成报告标注 ⚠️ 待集成
│       └── 调整 ROADMAP 顺序 → PM 更新依赖图
├── 软阻塞（部分可继续）
│   ├── PMO 识别可独立推进的部分
│   └── 先完成不依赖的部分，阻塞部分挂起等待
└── 🔴 禁止假装无依赖强行推进
```

---

## 十一、超时/阻塞升级规则

### 等待用户响应

```
暂停等待用户确认时：
├── 第 1 次无响应 → 正常等待
├── 用户发送无关消息 → 提醒当前阻塞状态，询问是否继续
├── 用户明确切换话题 → 记录当前状态，允许切换
└── 用户回来后 → 恢复阻塞点，询问如何处理

提醒格式：
⏸️ 提醒：当前功能 F{编号}-{名称} 阻塞于 [阻塞原因]
├── 回复「继续」→ 处理阻塞项
├── 回复「稍后」→ 记录状态，处理其他事项
└── 回复「放弃」→ 标记功能为暂停状态
```

### 阻塞项处理

```
如果阻塞项长时间未处理：
├── 有默认方案 → 可提议使用默认方案
├── 无默认方案 → 继续等待或建议用户决策
└── 禁止自行跳过阻塞项
```

---

## 十二、编号规则

> 📎 编号规则的权威定义见 [rules/naming.md](./rules/naming.md)。
> 包含：功能编号、Bug 编号、优化编号、决策编号、变更编号、业务关联编号。

---

## 十三、状态恢复机制

> 📎 完整的状态恢复机制（恢复决策树、Workspace Planning/Feature Planning/Feature 流程状态判断、Feature 看板格式）见 [CONTEXT-RECOVERY.md](./CONTEXT-RECOVERY.md)。
> 🔴 按需加载：仅在新对话启动或用户执行 `/teamwork status` / `/teamwork 继续` 时读取。

---

## 十四、多人协作规则

> 多人并行开发同一产品时，按子项目分工，通过 `.teamwork_localconfig.md` 和 `DEPENDENCY-REQUESTS.md` 协调。

### 模块聚焦规则

```
PMO 在分析需求和分配任务时，必须参考 .teamwork_localconfig.md：
├── scope = all → 不限制，所有子项目均可操作，跳过依赖请求相关机制
│   （自己负责所有模块，不存在跨人依赖，直接在对应模块开发即可）
├── scope = 指定子项目列表 → 优先聚焦用户负责的子项目
│   ├── 需求属于用户负责模块 → 正常进入流程
│   ├── 需求属于其他模块 → PMO 提示：
│   │   「此需求属于 [模块缩写]，不在你当前负责范围内。
│   │    是否仍要处理？或创建依赖请求让对方模块负责人处理？」
│   └── 需求跨多个模块（含用户负责的 + 不负责的）→ PMO 拆分：
│       ├── 用户负责的部分 → 正常进入流程
│       └── 不负责的部分 → 在对方模块创建 DEPENDENCY-REQUESTS.md 请求
└── 🔴 localconfig 不影响读取权限，所有模块的文档都可以读取参考
```

### 跨模块依赖请求处理

```
创建依赖请求（开发过程中发现需要其他模块支持）：
├── PMO 自动检测到跨模块依赖 → 提示用户确认
├── 用户确认 → PMO 在被依赖模块的 {子项目路径}/docs/DEPENDENCY-REQUESTS.md 中追加记录
├── 填入：请求方、请求方模块、依赖描述、优先级、期望时间
└── 本模块继续开发不被阻塞的部分

处理依赖请求（其他模块对我的请求）：
├── PMO 启动时扫描 → 主动提醒（见 INIT.md Step 0-A3）
├── 用户选择处理 → PMO 将请求转为当前模块的 Feature / Bug 流程
├── 完成后更新 DEPENDENCY-REQUESTS.md 状态为 ✅ 已完成 + 填写处理说明
└── 拒绝时必须附拒绝理由 + 替代方案

PMO 依赖提醒时机：
├── 每次 teamwork 启动时（Step 0-A3）
├── 当前 Feature 完成后（PMO 功能完成报告中附带提醒）
└── 用户执行 /teamwork status 时
```

### Feature 外部依赖阻塞机制

```
当 Feature 开发过程中依赖其他模块尚未就绪的能力时：

触发条件：
├── RD 开发时发现需要调用其他模块未就绪的接口/服务
├── 集成测试因外部模块未就绪而无法通过
└── PMO 分析需求时判定前置依赖未满足

阻塞处理流程：
├── 1. PMO 在对方模块创建 DEPENDENCY-REQUESTS.md 请求（如尚未创建）
├── 2. PMO 将当前 Feature 状态标记为「⏳ 等待外部依赖」
│   ├── 在 ROADMAP.md 中标注：阻塞原因 + 依赖的 DEP 编号 + 被依赖模块
│   └── Feature 停在当前阶段，不继续流转，不标记为完成
├── 3. PMO 评估当前 Feature 可独立推进的部分：
│   ├── ✅ 优先继续推进不依赖外部的部分（阻塞 ≠ 停工）
│   │   ├── 本模块业务逻辑 → 正常开发
│   │   ├── 外部调用点 → 用 mock/stub 替代，开发 + 单元测试照常进行
│   │   ├── PRD/设计/TC 等文档工作 → 不受影响，正常推进
│   │   └── 仅集成测试和最终验收挂起
│   └── 完全阻塞（极少数，Feature 核心逻辑就是调用外部）→ Feature 整体挂起
└── 4. PMO 通知用户当前阻塞状态和可选行动

🔴 阻塞期间禁止：
├── 将 Feature 标记为已完成（必须所有依赖就绪 + 集成测试通过）
├── 跳过集成测试直接关闭 Feature
└── 自行假设外部接口行为来完成开发（mock 测试可以，但不算最终验收）

依赖就绪后恢复：
├── 对方模块完成依赖请求 → DEPENDENCY-REQUESTS.md 状态变为 ✅ 已完成
├── PMO 在下次启动或 Feature 完成报告中检测到依赖已就绪
├── ⏸️ 提醒用户：「Feature [编号] 的外部依赖已就绪，是否恢复推进？」
│   （此暂停属于「一、暂停条件」中的「外部依赖就绪恢复」类型）
├── 用户确认 → Feature 状态从「⏳ 等待外部依赖」恢复到阻塞前阶段
└── 继续正常流程：移除 mock → 对接真实接口 → 集成测试 → 验收
```

---

## 十五、状态行格式规范

> 📎 状态行的完整格式定义、阶段与下一步对照表统一在 [SKILL.md](./SKILL.md) 的「每次回复必须包含状态标识」章节中维护。本文件不再重复定义，避免多处维护导致不一致。
>
> 各规则中涉及的「下一步」字段，请参照 SKILL.md 中的对照表填写。
