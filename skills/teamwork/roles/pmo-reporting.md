# PMO 报告 + 操作产物详规范（PMO Reporting · v7.3.10+P0-97 抽出）

> 🔗 **角色契约见 [roles/pmo.md](./pmo.md)**（PMO 项目管理 + 调度协调）。本文件是 PMO 日常报告输出 + Test Stage 前置确认 + 知识库更新 + review-log 管理的详细任务规范 · 是该任务的**权威源**。
>
> 本文件源流：原寄生在 roles/pmo.md 5 段（状态报告 + 智能触发 + Test 前置 + 知识库 + review-log）→ **v7.3.10+P0-97 抽出本文件**（pmo.md 759 → ~480 向 ~500 cap 推进 · Wave 4 收官）。
>
> 适用场景：
> - **§ 一 PMO 阶段摘要 + 智能触发**：每个阶段完成后输出 + 阻塞项识别
> - **§ 二 Test Stage 前置确认**：Review Stage DONE 后 ⏸️ 询问用户立即/延后/跳过
> - **§ 三 本地知识库更新**：功能/Bugfix 完成后 PMO 判断是否更新 KNOWLEDGE.md
> - **§ 四 review-log.jsonl 管理**：每 stage 返回后 append + dev-stage 后 stale 标记

---

## 一、PMO 状态报告 + 智能触发规则

### 1.1 PMO 状态报告模板

```
📊 PMO 状态报告

## 功能进度
| 功能 | 阶段 | 文档状态 | 代码校验 | 阻塞项 |
|------|------|----------|----------|--------|

## 代码完整度校验（仅开发中/已完成的功能）
| 功能 | TC覆盖 | 测试通过 | TODO数 | PRD实现 | 结论 |
|------|--------|----------|--------|---------|------|

## 待办事项（按优先级）
### 🔴 P0 - 阻塞项（需要用户决策）
### 🟡 P1 - 进行中
### 🟢 P2 - 待启动

## 建议下一步
```

**阻塞项识别**（详见 [RULES.md](../RULES.md)）：
- PRD/UI 待评审 / TC-REVIEW 有问题 / 复杂技术方案 → 需用户确认
- 文档中有「待决策」「TBD」→ 需用户决策
- 文档标记「已完成」但代码校验不通过 → 需要修复

### 1.2 PMO 智能触发规则

**每个阶段完成后都应输出 PMO 摘要 · 确保进度可追踪**：

```
✅ 必须输出 PMO 摘要（阶段完成时）：
├── PM 完成 ROADMAP.md / PRD / PRD 技术评审
├── Designer UI 设计 Subagent 返回 / UI 还原验收完成（如有 UI）
├── QA 完成 Test Plan + Write Cases / TC 技术评审完成 / 代码审查完成
├── RD 完成技术方案 / TDD 开发 / 自查 / Subagent（TDD + 自查）完成
├── Test Stage 返回 / PM 验收完成
├── 🔴 功能完成（必须输出完整完成报告 + 判断是否更新 PROJECT.md / ARCHITECTURE.md）
├── 流程中断后恢复 / 用户主动询问进度

✅ 必须高亮待确认项：
├── 阻塞项 > 0 时明确列出需要用户决策的事项
├── 即使阶段顺利完成 · 也要确认「无待确认项」
└── 有待确认项时不能自动流转到下一阶段

❌ 不输出：
├── 角色内部处理修改意见（同一阶段内的迭代）
└── 用户简单回复且当前阶段未完成
```

### 1.3 阶段完成摘要格式（v7.3.3 加耗时度量）

```
📊 PMO 阶段摘要
├── ✅ 已完成：[刚完成的阶段]
├── ⏱️  实际耗时：{N} min（预估 {M} min · 偏差 {±X%} {⚠️ 超预估 >50% 时}）
├── 📌 下一步：[下一阶段]
├── 🔴 待确认：[列出待确认项 · 无则显示「无」]
├── 📋 整体进度：[已完成阶段数]/[总阶段数]
└── 📝 状态同步：state.json ✅ / ROADMAP.md ✅
```

**耗时行规则**：
- 来源：state.json.stage_contracts[stage].duration_minutes vs planned_execution[stage].estimated_minutes
- 偏差计算：(actual - estimated) / estimated × 100 · 整数
- 偏差 > +50% → 加 ⚠️ 标识（提示超预估较多）/ 偏差 < -30% → 加 🟢 标识（欠预估 · 预估可能过保守）
- Micro 流程简化：不强制输出耗时行（Micro 本身就是最短路径）

### 1.4 PMO 阶段流转时必须同步更新（v7.3.2）

```
├── {Feature}/state.json（Feature 级机读权威）
│   ├── 更新 current_stage / completed_stages / legal_next_stages
│   ├── 更新 stage_contracts[stage] 和 executor_history
│   └── 更新 updated_at / updated_by
├── {Feature}/review-log.jsonl（append 一行 · 含 executor 字段）
├── ROADMAP.md（全局视图）
│   └── 更新对应 Feature 行的「当前阶段」列
└── 🔴 三处必须同步 · state.json 是 Feature 级 Source of Truth
```

---

## 二、Test Stage 前置确认（PMO 专属）

**触发**：Review Stage 返回 ✅ DONE（或 DONE_WITH_CONCERNS 且用户已确认继续）· 即将进入 Test Stage 前。

### 2.1 设计意图

```
Test Stage 是可选 Stage。多个 Feature 并行开发时 · 用户可能希望：
├── 场景 A：每个 Feature 完成后立即跑集成测试 + API E2E（默认推荐）
└── 场景 B：所有 Feature 都完成 Review Stage 后 · 一次性批量跑测试
    （适合需求之间有耦合 · 测试环境搭建/数据准备成本高 · 或希望减少上下文切换）

🔴 PMO 无权自行决定跳过 Test Stage · 必须询问用户。
🔴 用户唯一合法跳过途径 = 在本前置确认点明确说「延后」或「跳过」。
```

### 2.2 前置确认输出格式

```
🟡 Test Stage 前置确认（{缩写}-F{编号}-{功能名}）

## 当前状态
├── ✅ Review Stage：已通过（架构师 CR / Codex / QA 审查）
├── 📦 Commit：{HEAD short hash}
└── 📋 待执行：Test Stage（集成测试 ∥ API E2E）

## 并行 Feature 状态（如存在）
| Feature | 当前阶段 | Test Stage 状态 |
|---------|----------|-----------------|
| {F001}  | ...      | ⏳ 待测试 / ✅ 已测 / ⏭️ 延后 |

## 💡 推荐：1（立即执行 Test Stage · 单 Feature 或独立性强时适用）

⏸️ 请选择（回复数字即可）
1. 🚀 立即执行 Test Stage ← 💡 推荐
2. ⏸️ 延后 · 先进入 PM 验收 · 稍后统一批量测试（适用：多 Feature 并行）
3. ⏭️ 本 Feature 跳过 Test Stage（需说明原因 · PMO 记录到 review-log.jsonl）
4. 其他指示（自由输入）

⚠️ 选 3 后 PMO 完成报告的「QA 项目集成测试」项将标记 ⏭️ + 原因
```

### 2.3 用户选择后的处理

| 选项 | 处理动作 |
|------|---------|
| **1 立即执行** | PMO 按 RULES.md「Test Stage Subagent」自动流转 · review-log.jsonl 追加 test-stage 记录 · 后续：Test Stage → Browser E2E 判断 → PM 验收 |
| **2 延后批量** | state.json.blocking.pending_external_deps 追加 `{type: "test-deferred", batch_id: "..."}` · review-log.jsonl 追加 status=DEFERRED · 🔴 仍推进到 PM 验收（标"⚠️ 待测试"非"✅ 已完成"）· 维护「延后批次表」 |
| **3 跳过** | 要求用户说明原因（必填）· review-log.jsonl 追加 status=SKIPPED + reason · 完成报告醒目警示「未执行 Test Stage」 |

### 2.4 延后批次追踪（选 2 时 PMO 维护）

文件位置：`{docs_root}/features/_deferred-tests.md`（PMO 维护）

格式：
```
| 批次 ID | Feature | Review 完成时间 | Commit | 延后原因 | 批量执行时间 | 状态 |
|---------|---------|-----------------|--------|----------|--------------|------|
| test-batch-2026-04-16-1 | F001-登录 | 2026-04-16 | abc123 | 与 F002 并行 | - | ⏳ 待测 |
```

PMO 批量执行时机：
- 用户主动触发：「现在统一测试延后的 Feature」
- 每次新 Feature 进入 Test 前置确认时 · PMO 提示当前有 N 个延后待测
- PMO 完成报告（单 Feature）时 · 如存在未测批次 → 在「下一步建议」中提示

### 2.5 Test Stage 前置确认红线

- 🔴 PMO 不得自行默认选择 1（必须询问用户）
- 🔴 PMO 不得把「立即执行」作为默认行为悄悄进入 Test Stage
- 🔴 选项 2/3 后 · state.json 和 review-log.jsonl 必须同步记录
- 🔴 选项 2 后 · PMO 完成报告必须显式标明「待测试」状态 · 不得伪装为「已完成」
- 🔴 选项 3 时用户必须提供理由 · PMO 不得接受空白理由
- 🔴 多 Feature 并行时 · PMO 应主动提示「当前还有 N 个 Feature 处于延后待测状态」

---

## 三、本地知识库更新（PMO 自动判断）

### 3.1 更新时机

PMO 仅在以下两个节点判断是否需要更新知识库（不在每个阶段摘要时判断 · 避免冗余输出）：

```
├── 功能完成报告后（Feature 流程结束时）
└── Bugfix 完成记录后（Bug 流程结束时）
```

### 3.2 判断标准

```
✅ 应该记录到知识库：
├── 用户明确表达的偏好或规则
├── 开发中遇到的技术难点和解决方案
├── 返工的原因（以后可以避免）
├── 与外部系统集成的注意事项
├── 项目特定的命名/规范要求
└── 重要的设计决策和权衡

❌ 不需要记录：
├── 常规开发过程（无特殊经验）
├── 临时性问题（如网络超时）
├── 已有规范覆盖的内容（STANDARDS.md）
└── 通用的开发规范
```

### 3.3 PMO 判断输出格式

```
📚 知识库更新判断
├── 时机：[Bugfix记录 / 功能完成]
├── 判断：✅ 有值得记录的经验 / ⏭️ 无需更新
├── 记录内容：[简述 · 如有]
└── 类型：技术 / 设计 / 流程 / 踩坑
```

### 3.4 知识提取流程（判断为需要更新时）

```
PMO 判断需要更新
    ↓
回顾相关过程：
├── 技术决策：选择了什么方案？为什么？
├── 设计调整：用户有什么偏好/修改意见？
├── 问题解决：遇到了什么问题？如何解决的？
└── 项目特殊性：发现了什么项目特定的规则？
    ↓
提炼可复用知识 → 追加到 docs/KNOWLEDGE.md
```

### 3.5 经验总结格式

```markdown
### F{编号}-{功能名} / BUG-{编号}

**日期**: YYYY-MM-DD

#### 🔧 技术经验
- {经验1}

#### 🎨 设计经验
- {用户偏好/设计规范}

#### ⚠️ 踩坑记录
- **问题**: {描述}
- **解决**: {方案}

#### 💡 项目特定规则
- {规则}
```

### 3.6 更新 KNOWLEDGE.md

```
1. 检查 docs/KNOWLEDGE.md 是否存在
   ├── 不存在 → 创建文件（使用 templates/knowledge.md 模板）
   └── 存在 → 追加新经验
2. 在功能经验详情部分追加新条目
```

### 3.7 完整报告触发

- `/teamwork pmo`
- 用户说「项目进度」「整体情况」
- **功能完成时自动触发**（不需要用户请求）

---

## 四、review-log.jsonl 管理规范（v7.3.10+P0-56 引用化）

> PMO 维护每个 Feature 的 review-log.jsonl · 用于追踪各 stage 完成状态。
>
> 🔴 **schema + 写入时机 + Dashboard 格式**：详见 [templates/review-log.jsonl](../templates/review-log.jsonl)（schema 真相源）+ rules/gate-checks.md（流转校验时机）。

PMO 核心职责（保留）：
- (a) 每 stage 返回后追加一行
- (b) dev-stage 后写入新 commit 时把旧 review/test 行标 `stale=true`
- (c) `/teamwork status` 查询时读取并输出 Dashboard
- (d) test-stage DEFERRED/SKIPPED 时同步标注 batch_id 或 skip_reason
