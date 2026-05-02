# PRD 模板

> 🔴 v7.3 契约化更新：PRD 文件头必须包含 YAML frontmatter，将 `acceptance_criteria[]` 结构化为机器可读。
> 原因：AC 与 TC 测试反查绑定（`tests[].covers_ac`）是防止"需求→代码"漂移的关键机制。
> 机器校验脚本 `{SKILL_ROOT}/templates/verify-ac.py` 会校验每条 AC 都有对应测试。直接调用，无需各项目复制：
> `python3 {SKILL_ROOT}/templates/verify-ac.py {Feature 目录}`

## PRD.md（统一通用模板，v7.3.10+P0-47 合并）

> 🟢 **v7.3.10+P0-47 重构（PRD 模板合并）**：原"标准模板（业务类）" + "技术类变体"两套合并为统一通用模板。差异通过"按需必填"标注表达：
> - 业务类 Feature：用户故事 / 功能需求 / 埋点需求必填
> - 纯技术 refactor：用户故事可省（或写"使用方故事"）/ 功能需求改为"功能行为不变"声明 / 埋点需求标"不适用"
> - 中台子项目：消费方分析必填
> - 其他子项目：消费方分析不填
>
> 删除：`prd_variant` frontmatter 字段（合并后不需要变体区分）

```markdown
---
feature_id: "{缩写}-F{编号}-{功能名}"
status: draft  # draft | pending_review | confirmed
requires_ui: false  # v7.3.10+P0-44 新增：是否触发 Designer 评审（双保险之一；PMO 也按 UI 关键词识别）
business_direction_locked: false  # v7.3.10+P0-34-C：PL-PM 讨论收敛后由 PMO 写 true（v7.3.10+P0-44 改为讨论模式）
# v7.3.10+P0-48 删除：business_direction_locked_at（时刻信息由 state.json 单一记录）
acceptance_criteria:
  - id: AC-1
    description: "用户能用邮箱和密码登录"
    category: functional  # v7.3.10+P0-68：functional / telemetry / logging / config / performance / security / monitoring
    priority: P0
    test_refs: []  # Blueprint Stage 产出 TC 时填入测试 ID
    ui_refs: []    # UI Design Stage 产出时填入页面/状态（如 "login-page/normal"）
  - id: AC-2
    description: "密码错误显示红色提示"
    category: functional
    priority: P0
    test_refs: []
    ui_refs: []
  # v7.3.10+P0-68 实战补强：非功能性 AC（埋点 / 日志 / 配置 / 性能 / 安全 / 监控）必须显式声明 category
  # 因为 TC 通常无法覆盖这类 AC，Review Stage QA Step 4.5 会按 category 走 grep 对账（不通过 TC 中转）
  - id: AC-7
    description: "登录成功上报 login_success 埋点（含 user_id / source / timestamp）"
    category: telemetry  # 必标 · 触发 Step 4.5 grep SReporter
    priority: P0
    test_refs: []  # 可为空（非功能性 AC TC 难覆盖）
    grep_keyword: "SReporter.*login_success"  # v7.3.10+P0-68 新增 · 供 Step 4.5 直接使用
  - id: AC-8
    description: "登录关键路径打 INFO 日志（user_id 脱敏）"
    category: logging
    priority: P1
    test_refs: []
    grep_keyword: "SLogger.i.*login\\|Log.i.*login"
---

# {功能名称}

## 状态
草稿 | 待评审 | 已确认

## 背景

## 用户故事（🟡 业务类必填；纯技术 refactor 可省或写"使用方故事"）
作为 [角色]，我希望 [功能]，以便 [价值]

## 交付预期（用户视角）

> 做完后，用户能看到什么变化？去哪里验证？

| 变化 | 验证方式 |
|------|----------|
| {描述用户可感知的具体变化} | {在哪个页面/入口/命令可以看到效果} |

## 验收标准

> 🟢 v7.3.3 布局调整：验收标准紧跟交付预期，便于人类审查时聚焦"做完后长啥样 + 怎么判定做完"的契约核心。
> 🔴 v7.3 起，验收标准必须与 frontmatter 的 `acceptance_criteria[]` 一一对应（id 一致、description 一致）。
> 本 section 是人读视图，frontmatter 是机读源头。修改 AC 必须同步改两处（工具可校验一致性）。

| ID | 描述 | 优先级 | 覆盖测试（填到 frontmatter test_refs） |
|----|------|--------|---------------------------------------|
| AC-1 | {description} | P0 | {测试 ID，如 T-001, T-002} |
| AC-2 | {description} | P0 | |

## 功能需求（🟡 业务类必填；纯技术 refactor 改为"功能行为不变"声明）

### P0 (必须)
-

### P1 (应该)
-

### P2 (可选)
-

## 业务流程图 / 交互时序图（按需必填）

> 满足以下任一条件时必须画图，不能只用文字描述：
> - 用户操作超过 3 步且有分支路径
> - 涉及 2 个及以上系统/服务交互
> - 有状态流转（如订单状态、审批流）
> - 有异步流程或回调
>
> 不满足以上条件的简单功能可省略本节。
> 📎 图表规范见 standards/common.md「五、文档流程图规范」，统一使用 Mermaid。

### 业务流程（flowchart，多步骤/有分支时必填）
\`\`\`mermaid
flowchart TD
    A[起始] --> B{判断}
    B -->|条件1| C[步骤]
    B -->|条件2| D[步骤]
\`\`\`

### 系统交互时序（sequenceDiagram，多系统交互时必填）
\`\`\`mermaid
sequenceDiagram
    participant U as 用户
    participant C as 客户端
    participant S as 服务端
    U->>C: 操作
    C->>S: 请求
    S-->>C: 响应
\`\`\`

### 状态流转（stateDiagram，有状态机时必填）
\`\`\`mermaid
stateDiagram-v2
    [*] --> 状态A
    状态A --> 状态B: 触发条件
\`\`\`

## 埋点需求（🟡 前端/客户端业务功能必填；纯技术 refactor / 后端 / 内部功能标"不适用"）
> ⚠️ 纯后端功能 / 纯技术 refactor 标注「不适用」

| 埋点名称 | 事件类型 | 触发时机 | 参数 | 用途 |
|----------|----------|----------|------|------|
| | PV/Click/Submit/Error | | | |

## 消费方分析（中台子项目必填）

> 🔴 仅 midplatform 类型子项目的 Feature 需要填写此章节。business 类型子项目删除此章节。
> PMO 在 PM 编写 PRD 阶段启动时提示 PM 补充此章节（PRD 初稿即包含，PL-PM 讨论时可完善）。

### 消费方列表
| 消费方子项目 | 需要的能力 | 接入优先级 | 当前状态 |
|-------------|-----------|-----------|----------|
| | | P0/P1/P2 | 待开发/开发中/已接入 |

### API 契约（如适用）
<!-- 中台对外暴露的接口定义，消费方依据此开发 -->

### 兼容性承诺
<!-- 对现有消费方的兼容性保证：是否破坏现有接口、迁移方案等 -->

### 消费方接入计划
<!-- 各消费方何时开始接入、是否需要同步改动 -->

## 待决策项
| ID | 问题 | 选项 | 决策 |
|----|------|------|------|

## 变更记录
| 日期 | 变更 |
|------|------|
```

---

## PRD-REVIEW.md（PRD 技术评审记录）

```markdown
# {功能名称} - PRD 技术评审记录

## 当前状态
🔄 第 X 轮评审中 | ✅ 已通过

---

## RD 评审（技术角度）
| ID | 问题 | 类型 | 建议 | 用户确认 | 状态 |
|----|------|------|------|----------|------|
| R1 | | 可行性/复杂度/风险/遗漏 | | 修改/忽略 | 待处理/已处理 |

**工作量预估**: X 人天
**技术风险**: 低/中/高
**RD 结论**: ✅ 可行 / ⚠️ 有风险 / ❌ 不可行

---

## Designer 评审（设计角度）
| ID | 问题 | 类型 | 建议 | 用户确认 | 状态 |
|----|------|------|------|----------|------|
| D1 | | 交互/信息架构/状态/响应式 | | 修改/忽略 | 待处理/已处理 |

**设计工作量**: X 人天
**Designer 结论**: ✅ 可行 / ⚠️ 需补充

---

## QA 评审（测试角度）
| ID | 问题 | 类型 | 建议 | 用户确认 | 状态 |
|----|------|------|------|----------|------|
| Q1 | | 验收标准/边界/异常/可测性 | | 修改/忽略 | 待处理/已处理 |

**QA 结论**: ✅ 清晰 / ⚠️ 需补充

---

## PMO 评审（项目角度）
| ID | 问题 | 类型 | 建议 | 用户确认 | 状态 |
|----|------|------|------|----------|------|
| P1 | | 范围/依赖/时间/优先级/冲突 | | 修改/忽略 | 待处理/已处理 |

**项目风险**: 低/中/高
**PMO 结论**: ✅ 可控 / ⚠️ 有风险

---

## 待用户确认汇总
| 序号 | 来源 | 问题 | 建议方案 | 用户决定 |
|------|------|------|----------|----------|
| 1 | | | | |

---

## 用户确认方式
- 回复「修改 R1」→ PM 按建议修改 PRD
- 回复「忽略 D1」→ 标记为已忽略，记录原因
- 回复「全部接受」→ PM 按所有建议修改
- 回复「通过」→ PRD 进入「已确认」状态

---

## 评审历史

### 第 1 轮 - [日期]
- RD 问题: X 个
- Designer 问题: X 个
- QA 问题: X 个
- PMO 问题: X 个
- 用户确认: 修改 X / 忽略 X
- 结论: 继续修改 / 通过
```

---

## PRD-REVIEW.md frontmatter schema（v7.3.10+P0-34 新增，机读）

> Goal-Plan Stage 子步骤 2「多角色并行评审」产出 `{Feature}/PRD-REVIEW.md`，含以下机读 frontmatter。

```yaml
---
prd_feature_id: F025
review_round: 1
review_started_at: "<ISO 8601 UTC>"
review_completed_at: "<ISO 8601 UTC>"
reviews:
  # v7.3.10+P0-44 schema 调整：reviews[] 仅含 qa / rd / designer? / external?
  # v7.3.10+P0-46 加 review_scope 字段：标识本次评审范围
  # PL 走子步骤 2 PL-PM 讨论模式（独立产物 discuss/PL-FEEDBACK + PM-RESPONSE，不在本 reviews[] 数组）
  # PMO 不独立评审（折叠到 PMO 调度责任，整合 finding）
  - role: qa | rd | designer | external  # v7.3.10+P0-44：删 pl/pmo
    review_scope: prd                    # v7.3.10+P0-46：值 prd | blueprint | code-review，标识评审范围
                                          # PRD 评审仅审产品视角（业务可行性 / AC 可测试性 / 用户故事完整性）
                                          # 技术实现 / 测试用例细节在 Blueprint Stage 评审（review_scope=blueprint）
    execution: subagent | main-conversation
    verdict: PASS | PASS_WITH_CONCERNS | NEEDS_REVISION
    started_at: "<ISO 8601 UTC>"
    completed_at: "<ISO 8601 UTC>"
    files_read:
      - PRD.md
      - 其他真实读过的文件
    findings:
      - id: RD-1  # 角色前缀 + 序号
        severity: high | medium | low | info
        description: "1-2 句问题描述"
        suggestion: "建议改法（可执行的具体方向）"
        category: technical-consistency | business-alignment | ux | quality | business-decision  # v7.3.10+P0-34-A 新增
        # 以下字段在 PM 回应后填入（Round 2+）
        pm_response:
          action: ADOPT | REJECT | DEFER
          # v7.3.10+P0-34-A：DEFER 严格收紧，仅允许 category=business-decision 时使用
          category: business-decision  # 仅 action=DEFER 时必填，其他类别 DEFER = 违规
          # v7.3.10+P0-34-B：对抗性自查段（每条 ADOPT/REJECT 前必须先模拟反方最强论据）
          adversarial_self_check: |
            站在 finding 提出方视角写最强反驳论据（≥2 句具体内容）。
            示例（finding 由 RD 提，PM 想 REJECT）：
            "RD 反方最强论据：当前 PRD 接口缺 token 刷新策略，会导致鉴权失败回退到登录页，
             用户体验断点；如果不加，跨租户场景会出现幽灵会话。
             我的 REJECT 理由必须证明这两点不成立或代价可接受。"
          rationale: "ADOPT 时填'已修订：{改了什么 + PRD 段落引用}'；REJECT 时填'反方论据为何不成立 + 替代方案'；DEFER 时填'延后理由 + 追踪位置 + 上升给用户决策的具体问题'"
          responded_at: "<ISO 8601 UTC>"
overall_verdict: PASS | PASS_WITH_CONCERNS | NEEDS_REVISION
next_round_required: true | false
overall_decided_at: "<ISO 8601 UTC>"
---

# PRD-REVIEW（{feature_id}）Round {N}

## 各 reviewer 段（按 reviews[] 数组顺序展开）

### {role} 评审段（execution: {subagent|main-conversation}）

verdict: {PASS|PASS_WITH_CONCERNS|NEEDS_REVISION}

#### Findings

##### {id}（severity: {sev}）
{description}

**建议**：{suggestion}

**PM 回应**（Round 2+ 由 PM 填入）：
- 决策：{ADOPT|REJECT|DEFER}
- 理由：{rationale}

---

（重复其他 reviewer 段）

## 整合结论（Round {N} 完成后由 PMO 写）

- overall_verdict: {结果}
- next_round_required: {true|false}
- 下一步：{PM 修订 PRD 进 Round N+1 / 全员通过进子步骤 5 / 超 3 轮 ⏸️ 用户决策}
```

### 机器可校验

- yq 可解析所有 frontmatter 字段
- 每个 reviews[].findings[] 必须有 id / severity / description / suggestion / category 5 字段
- Round 2+ 的 NEEDS_REVISION findings 必须含 pm_response.action + pm_response.adversarial_self_check + pm_response.rationale
- v7.3.10+P0-34-A：`pm_response.action == "DEFER"` 时必须 `pm_response.category == "business-decision"`，否则视为违规（PMO 校验拦截，打回 PM 重做）
- v7.3.10+P0-34-B：每条 `pm_response.action ∈ {ADOPT, REJECT}` 必须含非空 `adversarial_self_check`（≥2 句反方论据模拟），否则视为对抗强度不足（PMO 打回）
- overall_verdict 必须与所有 reviews[].verdict 一致（任一 NEEDS_REVISION → overall = NEEDS_REVISION）

### 历史 PRD-REVIEW.md 兼容性

v7.3.10+P0-33 之前的 PRD-REVIEW.md（无机读 frontmatter，4 视角文字汇总）仍允许存在；新建 Feature 用本 schema。

---

## 🔴 PM 起草规范 checklist（v7.3.10+P0-51 从 goal-plan-stage.md 迁入，单源化）

> 🟢 **v7.3.10+P0-46 边界 / +P0-51 单源化**：PRD 仅回答「做什么 + 为什么」，技术/测试细节在 Blueprint Stage 由 RD/QA 起草。本 checklist 是 PM 起草 PRD 时的产品视角必填项；goal-plan-stage.md 仅 cite 本段，不复述细节。

### 🔴 起草前必读：代码现状 Read（v7.3.10+P0-73 新增 · 防止 PRD 与代码现状脱节）

> **触发实证**：PM 不读代码 → PRD 假设功能不存在但实际有 / AC 与现有约束冲突 / 漏掉代码已知边界 → 子步骤 3 RD 评审才发现 → 评审循环多 1 轮（实测 1-3 轮）。本段把"PM 起草前必有代码意识"从隐性期望提升为 checklist 硬项。

🔴 **PM 起草 PRD 前必须 Read 相关代码模块**（只读不输出 brief，靠 PM 内化）：

```
Step 1: 从用户原始消息 / triage 意图段提取关键词
        ├── 业务关键词（如"登录" / "推送" / "结算"）
        ├── 模块名（如"shortcut sync" / "package check"）
        └── 触发关键词（如"实测预下载无效果"→ 关键词"预下载"）

Step 2: grep 关键词 → 找入口文件 / 主要模块
        ├── grep 命令：rg "关键词" --type-add ... 或 Glob 找相关文件
        ├── 优先入口：API/route handler / Service 类 / Manager / Controller
        └── 不要发散：3-5 个核心文件 / ~500 行内 / 不超过 10 min

Step 3: Read 这些文件了解
        ├── 现有功能边界（已有什么 / 还没什么）
        ├── 已知约束（接口签名 / 数据流 / 状态机分支 / 性能基线）
        ├── 边界场景（错误码 / 降级路径 / 历史 Hack 注释 TODO/FIXME）
        └── 与本 Feature 改动的关系（新增 / 修改 / 重构 / 替换）

Step 4: PM 起草时把发现内化到 PRD
        ├── AC 描述与代码现状契合（不假设代码不存在 / 不与现有约束冲突）
        ├── 影响范围段提及高层模块（不需要文件清单 · 模块名级即可）
        ├── 发现关键约束 / 不确定点 → 写入 PRD「待决策项」段（PRD 已有位置）
        └── 不输出独立 brief 文档，不在主对话复述 Read 过的文件清单
```

🔴 **不要做的事**：
- ❌ 跳过 Read 直接起草（"我从用户消息能推出来"）—— Read 是硬规则，不是建议
- ❌ Read 5+ 个文件 / 1000+ 行（PM 不是 RD，不做完整代码调研）
- ❌ 在 PRD 里写代码细节（接口签名 / 数据模型）—— 这些仍归 TECH.md，PRD 只描述用户感知
- ❌ 在主对话复述 Read 文件清单 / 列文件 brief（污染主对话 · 浪费 token）

🟢 **执行边界**：
- 时间预算：5-10 min（不是完整代码调研）
- 输出形式：**只读不输出**（不产 brief 文件 · 不在主对话列读过的文件）
- 唯一痕迹：PM 起草后 self_check 勾选 `code_context_read: true`（一个 boolean 承诺）
- 兜底：子步骤 3 RD 评审仍会做最后一道核对，PM Read 是前置补强不是替代

📎 **与方向 A grep + 方向 B brief 的对比**：本 P0-73 = 方向 B 只读不输出（无 brief 文档 · 无 stage 膨胀）。如未来发现 PM 偷读不读 → 升级到方向 B 原版（加 brief 输出 / 加 PMO 校验段）；当前先靠 boolean self_check + 角色纪律。

### 通用 checklist（所有 Feature 必填）

```markdown
## 产品目标（Why）
- [ ] 解决什么用户问题 / 业务问题
- [ ] 关联的产品策略 / KNOWLEDGE 历史决策

## 验收标准（AC，可验证的业务行为）
- [ ] 每条 AC 有唯一 id（AC-1 / AC-2 / ...）
- [ ] 每条 AC 量化可验证（避免"用户体验好"等模糊描述）
- [ ] 每条 AC 标注优先级（P0 / P1 / P2）
- [ ] 边界场景的业务行为（用户感知的异常 / 错误提示 / 极端输入处理）
- [ ] AC 可测试性（QA 能从中转化为测试用例 = AC 描述清晰即可，不需要 PM 写测试用例）

## 影响范围
- [ ] 明确 in_scope / out_of_scope（避免 scope 蔓延）
- [ ] 列出 KNOWLEDGE.md / ADR 关联条目（复用既有产品/业务模式）
- [ ] 跨子项目依赖（DEP 编号 + 上游子项目，业务依赖层面）
- [ ] 业务风险表（业务风险 + 已知技术风险方向 + ROLLBACK 业务侧）
```

### UI 用户故事维度（仅 requires_ui=true 时填）

```markdown
## UI 用户故事（PM 描述高层产品意图）
- [ ] 涉及的页面 / 组件清单（高层）
- [ ] 交互改动描述（新增 / 修改 / 删除）
- [ ] 用户故事 + 状态流（含 normal / empty / loading / error）

🔴 不写：视觉风格约束 / 视觉细节（→ UI Design Stage / Designer）
```

### 🔴 PRD 不写什么（v7.3.10+P0-46 边界）

```
❌ 接口 schema（→ TECH.md，Blueprint Stage RD 写）
❌ 数据模型 / migration up/down（→ TECH.md）
❌ 调用链路 / 共享状态 / 事务边界（→ TECH.md）
❌ 异常处理实现策略：重试 / 降级 / 兜底（→ TECH.md，PRD 仅描述用户感知的异常行为）
❌ 性能实现方案（→ TECH.md，PRD 仅描述性能要求作为 AC）
❌ 复用既有库 / 模式（→ TECH.md）
❌ 测试用例（→ TC.md，Blueprint Stage QA 写）
❌ 集成测试规划 / 性能测试规划 / ROLLBACK 测试（→ TC.md）
❌ 视觉风格约束 / token / 全景同步细节（→ UI Design Stage / Designer）
```

### 🔴 PM 起草后必做自查

通用 + UI 用户故事（如适用）勾选完整；如发现自己在写技术细节或测试用例 → 立即停止 + 移到 TECH/TC 起草阶段。

写入 `PRD-REVIEW.md.reviews[role=pm].pm_self_check`（schema：`{checklist_passed: true|false, code_context_read: true|false, failed_items: ["..."], notes: "..."}`），不复述 checklist 全文（避免主对话重复述 3 遍）。

🔴 **`code_context_read` 字段（v7.3.10+P0-73 新增 · 必填 boolean）**：标记 PM 起草前是否完成"代码现状 Read"硬规则（grep 关键词 + Read 3-5 个核心文件 / 5-10 min 内化）。`code_context_read: false` = 跳过 Read 起草 → 子步骤 3 RD 评审若发现 AC 与代码现状冲突，PMO 自动 NEEDS_REVISION 打回 PM 重读重起；不接受"PM 自报已读"以外的省略。

---

🟢 **设计意图（v7.3.10+P0-46 职责正交回归 / +P0-51 单源化）**：
- PRD 回答"做什么 + 为什么"（产品/业务视角）
- TECH.md 回答"怎么做"（Blueprint Stage RD 写）
- TC.md 回答"怎么测"（Blueprint Stage QA 写）
- 三阶段职责正交，PRD 不再被技术/测试细节淹没
- v7.3.10+P0-51：本 checklist 单源在本文件，goal-plan-stage.md / roles/pm.md 仅 cite，不复述
