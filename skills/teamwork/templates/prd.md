# PRD 模板

> 位置：`{Feature 目录}/PRD.md`
> 🔴 机读契约落 `TEAMWORK-MACHINE` HTML 注释块(MD 预览隐藏 · **非 frontmatter** · 解决 Zed/GitHub 等渲染器裸露机读内容)· 含机读 `acceptance_criteria[]`(AC↔TC `tests[].covers_ac` 反查绑定 = 防「需求→代码」漂移)· 校验:`python3 {SKILL_ROOT}/templates/verify-ac.py {Feature 目录}`(直接调 · 无需复制)。

## PRD.md(三层 · 必填核 / 按需 / 开放区)

> **三层结构**(消费测试定档:有工具或下游读者真读它 → 必填核):
> - **必填核**(每个 Feature 都填):背景 / 用户故事〔业务类;refactor 可写"使用方故事"或省〕/ 交付预期 / 待决策项 / 验收标准 / Out of Scope —— 被 verify-ac / PM / dev / 冷审消费 · 或不可省的 what/why/scope/决策。
> - **按需**(按 Feature 类型):业务流程图(多步/分支)/ 埋点(前端业务)/ 消费方分析(中台子项目)· 不适用标「N-A」。
> - **开放区**(结构没问到的):§开工前必须想清的 —— 逼判断的尖问题 · 人读不机读。
> 🔴 **PRD 的脊 = prepare 已确认的意图**(🎯理解 / 📦范围 / 🔁既有行为)· 起草不得偏离 · 冷审据此核对(防 goal 起草 re-drift)。
> 🧠 **起草思考规范**(v8.262 · 冷审关注点即起草写法 · **不是写完再检查 · 是写的时候就这样想**):
> - 写**背景/方案**时:PL 六问过脑(这个价值前提站得住吗?是不是最小范围?动了既有行为吗?)—— 写不顺的地方就是冷审会打的地方;
> - 写**每条 AC** 时:用可测判据写(明确动作 + 预期 · 边界/异常入 AC)· 「尽量/合理/优化/提升」这类词**落笔即换**成可判定表述;
> - 写**涉依赖/接口**时:先读真实代码确认存在再写(假设的字段 = 冷审必打的「可实现」finding);
> - 用**术语**时:GLOSSARY 没有的 · 当句给定义。
> - 涉**降级/兜底体验**时:默认不做(复杂度×收益过不了就砍)—— 确需的降级体验是**产品决策** · 列进 §待决策项或终确认导读让用户拍板 · 不默默写进方案。
> why:finding 采纳率 80-90% = 多数问题起草时可预见 · 按冷审标准写一遍 比 写完被打回改一遍 省一整轮。

```markdown
<!-- TEAMWORK-MACHINE · 机读契约 · MD 预览隐藏(所有渲染器都不显)· verify-ac + goal-complete 解析此块 · 勿删外层注释包裹 · 标准 2 空格缩进
feature_id: "{缩写}-F{编号}-{功能名}"
status: draft # draft | pending_review | confirmed
requires_ui: false  # 是否触发 Designer 评审（双保险之一；PMO 也按 UI 关键词识别）
business_direction_locked: false  # 产品方向收敛(goal 评审 PL 质疑闭合 / 用户拍板)后 PMO 写 true
acceptance_criteria:   # 🔴 机读单源(verify-ac.py 读 id↔TC.covers_ac)· 只留机读字段 · AC 描述/BDD 全文在 body §验收标准表(人读单源 · 不两处同步 description)
  - id: AC-1
    category: functional   # functional / telemetry / logging / config / performance / security / monitoring
    priority: P0
    test_refs: []          # Blueprint 产 TC 时填测试 ID
    ui_refs: []            # UI Design 产出时填页面/状态
  # 非功能 AC(埋点/日志/配置/性能/安全/监控)必标 category · Review QA Step 4.5 按 category grep 对账(不过 TC 中转)
  - id: AC-7
    category: telemetry
    priority: P0
    test_refs: []
    grep_keyword: "SReporter.*login_success"   # 非功能 AC · 供 Step 4.5 grep
  - id: AC-8
    category: logging
    priority: P1
    test_refs: []
    grep_keyword: "SLogger.i.*login\\|Log.i.*login"
revision_history:   # 🔴 goal-complete 校验 ≥1 条(证明经 review 收敛)· 每轮修订 append 一条
  - {version: "0.1", date: "{YYYY-MM-DD}", changes: "首版草稿"}
-->

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

## 待决策项

<!-- 🔴 既有行为变更 → 必入此段(**刚性后果**):本 Feature 若改了某既有用户可感知默认行为(原 A → 现 B · 如「文件点击 原打开→现只定位」)· **必须**列为显式待决策项让用户拍板(原行为/新行为/为什么改/推荐)· **不可**在背景/「取舍」叙述段当既定事实蒙混。**侦测**在 §开工前必须想清的(🔁 主动挑衅)· 命中 → 后果落此段 · PL 质疑六问⑥ 复查。本表收待裁决(决策列空)+ 已裁决(决策列填)。 -->

| ID | 问题 | 选项 | 决策 |
|----|------|------|------|


## 验收标准

<!-- 🔴 本表 = AC **人读单源**(BDD 全文在此)· TEAMWORK-MACHINE 块 acceptance_criteria 只存机读字段(id/category/priority/test_refs/grep)· 两处 **id 一致** 即可(描述不再同步两份 · verify-ac.py 按 id↔TC.covers_ac 校验)· AC 写 BDD(Given/When/Then)· 行为/价值高度 · 🧠 写时即用可测判据(含糊词落笔即换 · 边界/异常入 AC —— 详模板头「起草思考规范」)。 -->

| ID | 描述(BDD) | 优先级 | 覆盖测试 |
|----|-----------|--------|----------|
| AC-1 | Given {前置} / When {操作} / Then {结果} | P0 | {测试 ID · Blueprint 填} |
| AC-2 | Given … / When … / Then … | P0 | |

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
> PMO 在 PM 编写 PRD 阶段启动时提示 PM 补充此章节（PRD 初稿即包含，评审讨论中可完善）。

### 消费方列表
| 消费方子项目 | 需要的能力 | 接入优先级 | 当前状态 |
|-------------|-----------|-----------|----------|
| | | P0/P1/P2 | 待开发/开发中/已接入 |

### API 契约（产品视角）
<!-- 中台对外暴露的接口能力承诺。仅写产品视角内容，技术实现细节归 TECH.md。 -->
<!--
✅ 写：method / path / 入参出参业务字段含义 / 错误情况下的用户感知 / 接口能力承诺
❌ 不写：鉴权方式 / 限流策略 / 序列化协议 / SLA / 内部缓存 / 数据库交互 / HTTP status code / 错误对象 schema
 这些归 TECH.md 接口实现段。
-->

### 兼容性承诺
<!-- 对现有消费方的兼容性保证：是否破坏现有接口、迁移方案等 -->

### 消费方接入计划
<!-- 各消费方何时开始接入、是否需要同步改动 -->

## Out of Scope（借鉴 mattpocock/skills to-prd · 必填）

> 🔴 **必填**：明确写出"本 Feature **不做**什么"——降低后期"为什么没做 X"的拉扯。
> 业务类 Feature：列业务范围外的功能 / 用户场景；纯技术 refactor：列不在重构范围的模块 / 路径。
> 与 KNOWLEDGE.md `## Out of Scope`（已拒绝过的全局方案）联动：本段是 Feature 级 scope 边界，KNOWLEDGE 是项目级长期拒绝记忆。

- {本 Feature 不做的事 1 + 简短理由}
- {本 Feature 不做的事 2 + 简短理由}
- ...

## 开工前必须想清的（结构没问到的）

<!-- 🔴 人读 · 机器禁入(无机读字段 / 不被 grep)· 至少 1 条实质 · 或显式「无 + 理由」· 冷审查此段是否过场(空着 / 套话 = NEEDS_REVISION)。 -->

> 逐条答(无则「无 + 为什么没有」· 证明想过不是跳过):
- **🔁 既有行为**:改了某既有用户可感知默认行为吗(原 A→现 B)? 若是 → 必入 §待决策项(刚性后果)。 → {答}
- **🧱 隐藏前提**:方案默认成立、但没写出来的前提是什么? 哪条错了会塌? → {答}
- **🌊 跨子系统涟漪**:改动波及哪些没列进 scope 的调用方 / 数据 / 契约? → {答}
- **❓ 最不确定**:你对这个 Feature 最没把握的一处是什么? → {答}

## 变更记录
| 日期 | 变更 |
|------|------|
```

---

## PRD-REVIEW.md frontmatter schema（机读）

> Goal Stage substep 3「并行冷审」产出 `{Feature}/PRD-REVIEW.md`(单源 schema)。机读 frontmatter:

```yaml
---
prd_feature_id: F025
review_round: 1
review_started_at: "<ISO 8601 UTC>"
review_completed_at: "<ISO 8601 UTC>"
reviewers: [pl, external]  # 机读汇总 · = state.stage_review_roles[goal](v8.243 默认 2 路:PL 对抗质疑 + 覆盖方向制外审 · 无 pm:PM 是整合者非 reviewer)· 校验 reviewers_match
verdicts: {pl: APPROVE, external: APPROVE}  # 🔴 全 APPROVE/SKIP 才可 goal-complete(prd_verdicts_all_pass · 词表 APPROVE|NEEDS_REVISION|SKIP · 无 pm verdict)
reviews:
 # goal 评审角色 = state.stage_review_roles[goal](v8.243 默认 pl/external 两路并行隔离冷审 · QA 可验证/ARCH 可实现并入外审覆盖方向 · 复杂 feature change-review-roles 加回独立 qa/architect · PM 整合非 reviewer)
 # PMO 不独立评审(折叠到调度责任 · 整合 finding)
 - role: pm | qa | architect | pl | external  # schema 通用 · rd/designer 值用于 TECH-REVIEW / REVIEW.md 复用场景
 review_scope: prd # 值 prd | blueprint | code-review
 # PRD 评审审产品视角(业务可行性 / AC 可测试性 / 用户故事完整性)· 技术/测试细节归 Blueprint Stage(review_scope=blueprint)
 # 🔴 pl 段 = 对抗质疑段:finding id 用 PL-CHALLENGE-{n} · category=premise-challenge(质疑六问〔含 ⑥ 既有行为变更〕· 至少 1 条实质质疑或显式「无实质质疑+理由」· 详 stages/goal-stage.md §3)
 # 🔴 external 段 = 覆盖方向制(v8.243):必覆盖 可实现(技术可行/架构影响/简洁性 counter-lens)· 可验证(AC 可测/边界/空值异常)+ AI 自主方向 ≥1(安全/性能/数据一致性/兼容…按 feature 挑)· 每方向 finding 或「查过无发现」· 下方 coverage 必填(物化门 external_coverage_present)
 coverage: [可实现, 可验证, <AI 自主方向>]  # 仅 role=external 必填 · 申报本次实际覆盖的方向
 execution: subagent | main-conversation
 verdict: APPROVE | NEEDS_REVISION  # 词表:APPROVE(含 advisory finding 留痕)| NEEDS_REVISION
 started_at: "<ISO 8601 UTC>"
 completed_at: "<ISO 8601 UTC>"
 files_read:
 - PRD.md
 - 其他真实读过的文件
 findings:
 - id: RD-1 # 角色前缀 + 序号
 severity: high | medium | low | info
 description: "1-2 句问题描述"
 suggestion: "建议改法（可执行的具体方向）"
 category: technical-consistency | business-alignment | ux | quality | business-decision | terminology-ambiguity | premise-challenge # terminology-ambiguity 触发 Flagged Ambiguities 写入 · premise-challenge = PL 质疑六问(含 ⑥ 既有行为变更)
 cross_role: []  # （可选）· 一个 finding 同时关联多视角时（如 [qa, rd]）· 仍归入主要视角段 · 不复制到多段
 # 涉及代码现状的 finding 必填 code_evidence(category=technical-consistency 时强制)
 code_evidence: # 可选 · category=technical-consistency 时必填
 file_path: "{绝对路径或仓库相对路径}"
 line_range: "{起始行-结束行，如 42-58}"
 snippet: "{可选 · 关键代码片段 ≤5 行 · 用于离线参考}"
 # 以下字段在 PM 回应后填入（Round 2+）
 pm_response:
 action: ADOPT | REJECT | DEFER
 # DEFER 严格收紧:仅 category=business-decision 可用
 category: business-decision # 仅 action=DEFER 时必填，其他类别 DEFER = 违规
 # 对抗性自查段（🔴 方向对称 · 每条 ADOPT/REJECT 前必填 · 默认姿态=质疑 · 不盲目认同）
 # 详 standards/external-model-usage.md §12（处理顺序 质疑→确认→裁决 + 对称举证）
 adversarial_self_check: |
 ADOPT 方向（先质疑 finding 再采纳 · 防盲采=最常踩）：写「这条 finding 不成立的最强反方」
 ——是否 false positive / 过度设计 / 责任焊错层 / 不适用本项目 / reviewer 没看全上下文？
 然后说明「我回读 {真实代码/AC/DEV-RULES} 确认这些反方都不成立，所以确为真问题」（≥2 句）。
 REJECT 方向（先 steelman finding 再驳）：站在 finding 提出方视角写最强反驳论据（≥2 句）。
 示例（REJECT）："RD 反方最强论据：PRD 接口缺 token 刷新策略 → 鉴权失败回退登录页 + 跨租户幽灵会话；
 我的 REJECT 理由必须证明这两点不成立或代价可接受。"
 示例（ADOPT）："质疑：这条『加幂等键』可能是过度设计——本接口是只读查询，无副作用。
 回读 dev/handler.go:42 确认它确有写库分支（缓存回填），并发下确会重复写 → 质疑不成立 → 采纳。"
 rationale: "🔴 ADOPT 必含『质疑→确认链』：① 我质疑了什么 ② 回读 {文件/AC} 确认质疑不成立 ③ 故采纳 + 改了什么 + PRD 段落引用（不接受『reviewer 说得对』式无核实采纳）；REJECT 填'反方论据为何不成立 + 替代方案'；DEFER 填'延后理由 + 追踪位置 + 上升给用户决策的具体问题'"
 responded_at: "<ISO 8601 UTC>"
overall_verdict: APPROVE | NEEDS_REVISION
next_round_required: true | false
overall_decided_at: "<ISO 8601 UTC>"
---

# PRD-REVIEW（{feature_id}）Round {N}

## 各 reviewer 段（按 reviews[] 数组顺序展开）

### {role} 评审段（execution: {subagent|main-conversation}）

verdict: {APPROVE|NEEDS_REVISION}

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
- 下一步：{PM 修订 PRD 进 Round N+1 / 全员通过进 substep 7 判定 → 8 needs-ui / 超 3 轮 ⏸️ 用户决策}
```

### 机器可校验

- yq 可解析所有 frontmatter 字段
- 每个 reviews[].findings[] 必须有 id / severity / description / suggestion / category 5 字段
- Round 2+ 的 NEEDS_REVISION findings 必须含 pm_response.action + pm_response.adversarial_self_check + pm_response.rationale
- `pm_response.action == "DEFER"` 时必须 `pm_response.category == "business-decision"`，否则视为违规（PMO 校验拦截，打回 PM 重做）
- 每条 `pm_response.action ∈ {ADOPT, REJECT}` 必须含非空 `adversarial_self_check`（≥2 句反方论据模拟），否则视为对抗强度不足（PMO 打回）
- finding `category=technical-consistency` 时必含 `code_evidence.{file_path, line_range}` —— 防止"猜测式 finding"（reviewer 没读代码就提出问题）。空值 = PMO 打回 reviewer 重审 + 提示"必须 cite 代码 location"
- finding `category=terminology-ambiguity` 触发后澄清结论必须**实时**写入 KNOWLEDGE.md `## Flagged Ambiguities` 段（不等评审循环结束批处理）+ `pm_response.rationale` 字段引用 FA-NNN 编号
- overall_verdict 必须与所有 reviews[].verdict 一致（任一 NEEDS_REVISION → overall = NEEDS_REVISION）

## 🔴 PM 起草规范 checklist（单源化）

> PRD 仅回答「做什么 + 为什么」· 技术/测试细节归 Blueprint(RD/QA 起草)。本 checklist 是 PM 产品视角必填项 · goal-stage.md/roles/pm.md 仅 cite 不复述(单源)。

### 🔴 起草前必读：代码现状 Read

> 为什么硬规则:PM 不读代码 → PRD 假设功能不存在但实际有 / AC 与现有约束冲突 → 冷审才发现 → 多 1 轮评审。

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
- 兜底：substep 5 多角色评审(architect/qa)仍会做最后一道核对，PM Read 是前置补强不是替代

🔴 **调研四类**(§4 早问门入场券 · 单源 stages/goal-stage.md ③手段菜单〔调研四类〕):代码现状(本段)+ KNOWLEDGE(Flagged Ambiguities / Preferences / Out-of-Scope)+ GLOSSARY + 上游规划(BL / WS / 愿景 / PENDING + prepare 流程目标)—— 全部 AI 可自答 · 没查完没资格问用户。


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

### 🔴 PRD 不写什么

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

🔴 **`code_context_read` 字段**：标记 PM 起草前是否完成"代码现状 Read"硬规则（grep 关键词 + Read 3-5 个核心文件 / 5-10 min 内化）。`code_context_read: false` = 跳过 Read 起草 → substep 5 多角色评审若发现 AC 与代码现状冲突，PMO 自动 NEEDS_REVISION 打回 PM 重读重起；不接受"PM 自报已读"以外的省略。

---

🟢 **设计意图**：
- PRD 回答"做什么 + 为什么"（产品/业务视角）
- TECH.md 回答"怎么做"（Blueprint Stage RD 写）
- TC.md 回答"怎么测"（Blueprint Stage QA 写）
- 三阶段职责正交，PRD 不再被技术/测试细节淹没
- 本 checklist 单源此文件 · goal-stage.md / roles/pm.md 仅 cite 不复述
