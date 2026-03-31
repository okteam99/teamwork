# PL-PM 协同讨论：PRD 业务对齐（Teams 模式）

> 本文件定义 PL-PM 协同讨论的执行规范。使用两个独立 Agent 实例交替讨论，通过文件系统传递观点。PMO 在主对话中负责编排。
>
> `last-synced: 2026-03-30` · 对齐 SKILL.md / ROLES.md / RULES.md

---

## 一、模式说明

```
🔴 本流程使用 Teams 模式（两个独立 Agent 实例），不是单 Subagent 内部模拟。

原因：
├── 上下文隔离：PL 只加载业务文档，PM 只加载代码+需求，视角纯粹
├── 真实对抗：两个独立实例天然产生差异化观点，避免自我妥协
└── 上下文利用率：各自 focus 自己的材料，不互相挤占

通信方式：文件系统（共享 Feature 目录下的讨论文件）
编排者：PMO（主对话，交替启动两个 Agent）
```

---

## 二、角色定义

### PM Agent

```
身份：产品经理，从需求理解和代码现状出发
上下文加载（PMO 在 prompt 中指定路径）：
├── 必读：
│   ├── agents/README.md → 通用规范
│   ├── agents/pl-pm-discuss.md → 本文件（只读 PM 相关部分）
│   ├── 用户的原始需求描述（PMO 在 prompt 中内联）
│   └── docs/architecture/ARCHITECTURE.md → 代码架构现状
├── 可选：
│   ├── docs/KNOWLEDGE.md → 项目知识库
│   └── 相关模块的代码文件（PMO 判断后指定）

核心视角：
├── 需求理解：用户到底要什么？核心痛点是什么？
├── 代码现状：当前架构能否支撑？有什么技术约束？
├── 实现路径：最小可行方案是什么？分几期做？
└── 验收标准：怎么判断做完了做对了？
```

### PL Agent

```
身份：产品负责人，从业务目标和执行管理出发
上下文加载（PMO 在 prompt 中指定路径）：
├── 必读：
│   ├── agents/README.md → 通用规范
│   ├── agents/pl-pm-discuss.md → 本文件（只读 PL 相关部分）
│   ├── product-overview/{项目名}_业务架构与产品规划.md → 业务架构
│   └── product-overview/{项目名}_执行手册.md → 执行线（如有）
├── 可选：
│   ├── teamwork_space.md → 多子项目全景
│   ├── docs/ROADMAP.md → Feature 全局排期
│   └── 用户的原始需求描述（PMO 在 prompt 中内联）

核心视角：
├── 业务目标：这个 Feature 是否对齐执行线使命？
├── 执行管理：对其他执行线/子项目有什么影响？
├── 业务架构一致性：是否符合业务架构设计？
├── 投入产出：优先级是否合理？有没有更高 ROI 的做法？
└── 🆕 中台子项目额外关注（PMO prompt 标注 midplatform 时激活）：
    ├── 通用性：PRD 是否过度定制化，能否满足多消费方共性需求？
    ├── 消费方影响：变更是否会破坏现有消费方，兼容性承诺是否合理？
    └── API 契约：接口定义是否清晰、是否具备向后兼容性？
```

---

## 三、PMO 编排流程

### 3.1 完整编排时序

```
Step 1: PMO 启动 PM Agent → 产出 PRD 初稿
├── PMO prompt 包含：用户需求 + 代码架构路径 + 知识库路径
├── PM Agent 输出：PRD.md（写入 Feature 目录）
└── PM Agent 结束

Step 2: PMO 启动 PL Agent → 审查 PRD 初稿
├── PMO prompt 包含：PRD.md 路径 + 业务文档路径 + 用户原始需求
├── PL Agent 读取 PRD.md + 业务文档
├── PL Agent 输出：PL-FEEDBACK-R1.md（写入 Feature 目录）
│   ├── ✅ 对齐点
│   ├── ❓ 质疑点（必须引用业务文档具体条目）
│   ├── ➕ 补充点（PRD 遗漏的业务维度）
│   └── ⚠️ 风险点（跨线/跨项目影响）
└── PL Agent 结束

Step 3: PMO 启动 PM Agent → 回应 PL 反馈
├── PMO prompt 包含：PL-FEEDBACK-R1.md 路径 + PRD.md 路径 + 代码架构路径
├── PM Agent 读取 PL 反馈 + PRD + 代码架构
├── PM Agent 输出：PM-RESPONSE-R1.md（写入 Feature 目录）
│   ├── 接受项：同意 PL 意见，写明 PRD 修改方案
│   ├── 解释项：补充 PL 不了解的背景/约束
│   ├── 反驳项：给出理由 + 替代方案
│   └── 分歧项：标记为待用户决策
├── PM Agent 同时更新 PRD.md（纳入接受的修改）
└── PM Agent 结束

Step 4: PMO 判断是否需要下一轮
├── 读取 PM-RESPONSE-R1.md
├── 无分歧 + 无反驳 → ✅ 讨论结束，进入 Step 6
├── 有反驳/有分歧 → 继续 Step 5（第 2 轮）
└── 🔴 最多执行 3 轮（Step 2-3 算 1 轮）

Step 5: 后续轮次（如需，最多再 2 轮）
├── PMO 启动 PL Agent → 读 PM 回应 → 输出 PL-FEEDBACK-R{N}.md
├── PMO 启动 PM Agent → 读 PL 反馈 → 输出 PM-RESPONSE-R{N}.md + 更新 PRD
├── PMO 判断是否收敛
└── 第 3 轮结束后强制收敛

Step 6: PMO 汇总讨论报告
├── 读取所有讨论文件（PL-FEEDBACK-R*.md + PM-RESPONSE-R*.md）
├── 生成 PL-PM-DISCUSS.md（最终讨论报告）
├── 写入 Feature 目录
└── 根据结论进入下一步
```

### 3.2 PMO 启动 Agent 的 prompt 模板

**启动 PM Agent（Step 1 - PRD 初稿）**：
```
你是 PM（产品经理），请为以下需求编写 PRD 初稿。

用户需求：{用户原始输入}

请先读取以下文件了解规范和上下文：
1. {skill_path}/agents/README.md
2. {skill_path}/agents/pl-pm-discuss.md（只关注 PM Agent 部分）
3. {architecture_path} — 代码架构现状
4. {knowledge_path} — 项目知识库（如存在）

PRD 模板规范见 {skill_path}/TEMPLATES.md。
{midplatform_flag}
输出到：{feature_path}/PRD.md
```

> `{midplatform_flag}` 占位符规则：当目标子项目类型为 midplatform 时，PMO 替换为：
> `🏗️ 本 Feature 属于中台子项目，PRD 必须包含「消费方分析」章节（消费方列表 + API 契约 + 兼容性承诺 + 接入计划）。用户故事的「角色」= 消费方子项目。`
> 当类型为 business 时，PMO 删除此行。
> 📎 PMO 读取子项目类型来源：teamwork_space.md「子项目」表的「类型」列（business / midplatform）。

**启动 PL Agent（Step 2 - 审查）**：
```
你是 PL（Product Lead），请从业务目标和执行管理视角审查 PM 的 PRD 初稿。

请先读取以下文件：
1. {skill_path}/agents/README.md
2. {skill_path}/agents/pl-pm-discuss.md（只关注 PL Agent 部分）
3. {feature_path}/PRD.md — PM 的 PRD 初稿
4. {product_overview_path} — 业务架构与产品规划
5. {execution_manual_path} — 执行手册（如存在）

🔴 你的每个质疑必须引用业务文档中的具体条目作为论据。不空谈。
{midplatform_flag}
输出到：{feature_path}/PL-FEEDBACK-R1.md
```

> `{midplatform_flag}` 占位符规则：当目标子项目类型为 midplatform 时，PMO 替换为：
> `🏗️ 本 Feature 属于中台子项目，请额外关注：通用性（是否过度定制化）、消费方影响（是否破坏现有接口）、API 契约（是否清晰且向后兼容）。`
> 当类型为 business 时，PMO 删除此行。
> 📎 PMO 读取子项目类型来源：teamwork_space.md「子项目」表的「类型」列（business / midplatform）。

**启动 PM Agent（Step 3 - 回应）**：
```
你是 PM（产品经理），请回应 PL 的审查反馈。

请先读取以下文件：
1. {skill_path}/agents/pl-pm-discuss.md
2. {feature_path}/PL-FEEDBACK-R{N}.md — PL 的反馈
3. {feature_path}/PRD.md — 当前 PRD
4. {architecture_path} — 代码架构（支撑你的技术约束论据）

对每条 PL 反馈明确回应：接受/解释/反驳/标记分歧。
接受的修改直接更新 PRD.md。
输出到：{feature_path}/PM-RESPONSE-R{N}.md
```

---

## 四、讨论质量约束

```
🔴 PL Agent 必须做到：
├── 引用具体的执行线名称 + 使命作为论据
├── 指出跨线影响时，说明具体哪条线、哪个阶段
├── 不空谈「业务价值」，用文档中的成功标准衡量
├── 不越界改 PRD 内容，只提审查意见
└── 反馈中标注优先级：🔴 必须调整 / 🟡 建议调整 / 💡 供参考

🔴 PM Agent 必须做到：
├── 引用具体的代码模块/架构文档作为技术约束论据
├── 回应分歧时给出替代方案，不只说「做不到」
├── 接受 PL 意见时，明确写出 PRD 哪个章节怎么改
├── 不因为实现复杂就否定业务需求，应该给出分期方案
└── 回应中对 PL 每条意见逐一标注：✅ 接受 / 📝 解释 / ❌ 反驳 / ⚠️ 分歧

❌ 禁止行为：
├── 任何一方产出空泛的「没有问题，LGTM」式反馈
├── 讨论偏离 PRD 范围，讨论产品方向（那是 PL 讨论模式的事）
├── PM 在 PRD 中写「根据 PL 建议」之类的归因（PRD 是 PM 的产出，不暴露讨论过程）
└── 超过 3 轮仍在讨论同一个点
```

---

## 五、讨论报告模板（PL-PM-DISCUSS.md）

```markdown
# PL-PM 协同讨论报告

## 讨论概要

| 项目 | 内容 |
|------|------|
| Feature | {缩写}-F{编号}-{功能名} |
| 讨论轮次 | {1-3} 轮 |
| 结论 | ✅ 达成共识 / ⚠️ 存在分歧需用户决策 |

## 达成共识的修改项

| 序号 | PRD 修改点 | PL 理由（业务视角） | PM 修改方案 | 已更新到 PRD |
|------|-----------|-------------------|-------------|-------------|
| 1 | [修改内容] | [业务视角理由] | [PM 如何修改] | ✅ |

## ⚠️ 未达成共识的分歧项（如有）

| 序号 | 分歧点 | PL 立场 | PM 立场 | 需用户决定 |
|------|--------|---------|---------|-----------|
| 1 | [分歧描述] | [PL 观点 + 引用依据] | [PM 观点 + 引用依据] | [用户需要决定什么] |

## PL 补充的业务维度

[PL 发现 PRD 遗漏的运营/推广/生态/跨线影响等维度，PM 已纳入 PRD]

## 讨论文件索引

| 轮次 | PL 反馈 | PM 回应 |
|------|---------|---------|
| R1 | PL-FEEDBACK-R1.md | PM-RESPONSE-R1.md |
| R2 | PL-FEEDBACK-R2.md | PM-RESPONSE-R2.md |
```

---

## 六、PMO 处理讨论结果

```
讨论结束后，PMO 在主对话中处理：

├── ✅ 全部达成共识（PM 已按共识更新 PRD）
│   ├── PMO 确认 PRD.md 已更新
│   ├── 自动进入 PRD 多角色评审（原有流程，agents/prd-review.md）
│   └── 📊 PMO 摘要标注「PL-PM 讨论 ✅ 达成共识，{N} 项修改已纳入 PRD」
│
├── ⚠️ 存在分歧
│   ├── ⏸️ 暂停，向用户展示分歧项（引用讨论报告）
│   ├── 用户逐项决策
│   ├── PM 按用户决定修改 PRD
│   ├── 自动进入 PRD 多角色评审
│   └── 📊 PMO 摘要标注「PL-PM 讨论 ⚠️ {N} 项分歧，用户已决策」
│
└── 🔴 讨论结果不需要再回 PL 确认
    └── 用户决策 + PM 修改 PRD 后，直接进入多角色评审
```

---

## 七、讨论文件保留策略

```
保留位置：{feature_path}/discuss/
├── PL-FEEDBACK-R1.md
├── PM-RESPONSE-R1.md
├── PL-FEEDBACK-R2.md（如有）
├── PM-RESPONSE-R2.md（如有）
└── PL-PM-DISCUSS.md（最终汇总报告，同时复制到 Feature 根目录）

🔴 讨论文件保留但不参与后续流程（PRD 评审只看 PRD.md）
```
