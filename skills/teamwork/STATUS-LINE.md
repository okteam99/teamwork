# 状态行（State Line）

> 本文件唯一权威：状态行格式 / Final Response Preflight / 决策点参考路径硬规则 / 暂停点模板渲染契约 / 阶段对照表 / 各流程状态行示例。
>
> 📎 跨主题单源（v7.3.10+P0-116 拆出）：
> - 流程持续规则（激活/退出）→ [SKILL.md § 会话级持续模式](./SKILL.md)
> - 用户意图识别 / 用户回复处理 / PMO 承接规则 → [roles/pmo.md](./roles/pmo.md)
> - 上下文恢复机制 → [CONTEXT-RECOVERY.md](./CONTEXT-RECOVERY.md)

---

## 📌 状态行格式定义

**每次回复必须包含状态标识，放在回复末尾。**

### 状态行格式规范

```
第一行：🔄 Teamwork 模式 [⚡ AUTO] [🌐 Ext: {model}] | 流程：[...] | 角色：[...] | 阶段：[...] | 下一步：[...]
🔴 必填追加字段（按流程类型）：
├── Feature / 敏捷需求 → 功能：{缩写}-F{编号}-{功能名}（🔴 必填，不可省略）
├── Bug 处理 → Bug：BUG-{编号}-{简述}（🔴 必填）
├── Micro → 功能：Micro-{简述}（🔴 必填）
└── 问题排查 / Feature Planning → 无功能编号时可省略
可选追加字段：子项目 / 跨项目需求 / 涉及 / 受影响子项目
🔴 ⚡ AUTO 徽章（v7.3.9+P0-11 新增）：
├── AUTO_MODE=true → 在「🔄 Teamwork 模式」与「|」之间插入「⚡ AUTO」
├── AUTO_MODE=false（默认）→ 不插入
└── 触发来源：/teamwork auto [需求]（详见 [stages/triage-stage.md](./stages/triage-stage.md) Step 0）
🌐 Ext 徽章（v7.3.10+P0-24 新增）：
├── state.external_cross_review 任一 *_enabled=true（plan/blueprint/review 任一）→ 在「🔄 Teamwork 模式」/「⚡ AUTO」之后插入「🌐 Ext: {model}」（model = codex / claude）
├── 三处 _enabled 全为 false 或字段不存在 → 不插入
├── 既有 Feature 仍走 codex_cross_review 字段 → fallback 显示「🌐 Ext: codex」
└── 触发来源：PMO 在初步分析阶段直接判定（v7.3.10+P0-72 自报宿主 + `command -v` 检查 CLI）后用户启用

第二行（按场景决定）：
├── 有明确功能目录 / bugfix 目录 → 必须输出 `📁 {绝对路径}`（🔴 emoji 与路径之间**必须有一个空格**，v7.3.10+P0-62）
├── 无功能目录但有工作区状态文件 → 输出该状态文件或工作区文档绝对路径
└── 纯讨论/梳理阶段暂时没有落盘目录 → 第二行可省略

第三行（分支 / worktree 状态，v7.3.9+P0 新增）：
├── Feature / 敏捷 / Bug（worktree=auto/manual）→ 🌿 分支：{branch} → {merge_target} | worktree：{worktree.path}
├── Feature / 敏捷 / Bug（worktree=off）→ 📍 当前分支：{branch} → {merge_target}（⚠️ 未启用 worktree，并行 Feature 请注意隔离）
├── Micro（worktree=off）→ 📍 当前分支：{当前分支名}（⚠️ Micro 直接改主分支，操作前确认工作区干净）
├── Micro（worktree=auto/manual）→ 🌿 分支：chore/{简述} → {merge_target} | worktree：{worktree.path}
├── Planning（Roadmap / Workspace 架构 / 跨项目拆分）→ 📍 当前分支：{当前分支名}（Planning 阶段不改代码，分支仅供参考）
├── Bug 修复阶段（复杂 Bug 已走 Feature 流程）→ 🌿 分支：bugfix/{编号}-{简述} → {merge_target} | worktree：{path}
├── 问题排查 / PL 纯讨论 / Goal-Plan Stage preflight 之前 → 可省略（无分支语义或 worktree 未建）
└── 字段取值优先级：
    ├── state.json.worktree.{path, branch} + state.json.merge_target → 首选
    ├── state.json 缺失时 → 回退 `git branch --show-current` 实时渲染，不虚构
    └── 🔴 禁止把 worktree.path 写成相对路径或省略 worktree 字段伪装成 off
```

### 状态行规则

```
├── 「流程」字段只表示六种标准流程，不承载「工作区级」「PL 模式」等扩展语义
├── 「工作区级」「PL 讨论中」「PL 变更评估中」等信息写入阶段字段
├── 第二行路径必须是绝对路径（以 / 开头），不能用相对路径
├── 只有在当前阶段确实没有可点击目录/文件时，才允许省略第二行
├── 第三行在「分支 + merge_target」语义存在时必须输出；无 worktree 时用 📍 警示
├── 🌿 = 已启用 worktree 隔离（安全），📍 = 直接在分支上操作（谨慎）
├── ⚡ AUTO 徽章仅在 AUTO_MODE=true 时在第一行显示；默认不显示
├── 🌐 Ext 徽章仅在 state.{stage}_substeps_config.review_roles[] 任一含 external 时在第一行显示（v7.3.10+P0-38 改造，不再读老 *_enabled 字段）
├── 🔴 **emoji 间隔硬规则**（v7.3.10+P0-62）：所有图标（📁 / 🌿 / 📍 / ⚡ / 🌐 / 🔄 / 🔗 / ⏸️ 等）与其后紧随的文字内容之间**必须保留一个半角空格**。例：`📁 /Users/...`（✅）/ `📁/Users/...`（❌ 终端会把 emoji 和路径视为一体，不可点击）
├── 🔴 **路径边界硬规则**（v7.3.10+P0-67）：任何**绝对路径前后都必须有 whitespace 边界**（半角空格 / 行首 / 行尾），让终端正确识别 hyperlink。
│   ├── 路径**前**：emoji + 半角空格（已由 P0-62 规则保证）/ 或行首
│   ├── 路径**后**：半角空格 / 换行 / 行尾。**禁止全角符号 / 中文字符 / 标点紧贴路径**
│   ├── ✅ 正确：`📁 /Users/.../PRD.md\n` / `... 见 /Users/.../PRD.md ，请确认。`（路径后半角空格 + 全角逗号）
│   └── ❌ 错误：`见 /Users/.../PRD.md，请确认`（全角逗号紧贴路径 → 终端把"PRD.md，"识别为整体，链接断裂）/ `路径：/Users/.../PRD.md（待确认）`（全角括号紧贴）
└── 🔴 **长 URL / 长路径不进表格列硬规则**（v7.3.10+P0-70 实证 ship MR 链接被切碎）：长 URL（含 `?` `&` `=` `%` 等查询参数）/ 长绝对路径，**禁止挤入 markdown 表格列**或 markdown 链接语法 `[文字](URL)`，**必须独立成行裸输出**（前后 whitespace 边界）。
    ├── 原因：表格列宽切碎多行 / 全角竖线 `|` 干扰识别 → 终端无法识别为可点击 hyperlink
    ├── ✅ 正确（独立行裸输出）：
    │   ```
    │   🔗 MR 创建链接：
    │
    │   https://git.example.com/owner/repo/-/merge_requests/new?merge_request%5Bsource_branch%5D=feature%2FX
    │   ```
    └── ❌ 错误（挤入表格列）：
        ```
        | MR 创建链接 | https://git.example.com/owner/repo/-/merge_requests/new?merge_request%5Bsource_branch%5D=feature%2FX |
        ```
        → URL 被列宽切碎 / 全角竖线干扰 / 用户无法点击
```

### 🔴 Final Response Preflight（v7.3.10+P0-66 实战补充）

> 触发：实战 case（INFRA-F017 Ship finalize）AI 漏输出标准状态行，用了自定义「📍 Teamwork：...」摘要替代。根因 = 「相似格式漂移 + 完成时误以为流程退出 + 工程信息密集时压缩成摘要」。

**任何 final response 发送前 PMO 必须 self-check 4 项**（缺一即流程偏离）：

```
✅ Preflight checklist：
1. 状态行存在？ → 回复中是否含 `🔄 Teamwork 模式` 开头的标准行
2. 在末尾？ → 状态行物理位置在回复末尾（不在中段、不在开头）
3. 阶段值合法？ → 「阶段：...」字段在下方「阶段与下一步对照表」中存在
4. 下一步合法？ → 「下一步：...」字段在对照表「下一步」列存在（不填具体命令 / commit hash / 文件路径）
```

🔴 **禁止的相似格式**（违反 = 流程偏离）：

```
❌ 📍 Teamwork：INFRA-F017 | 阶段：✅ completed | shipped=merged
   （摘要风格 / 不是 🔄 Teamwork 模式 开头 / 用了自定义字段如 shipped=merged）

❌ Teamwork: 流程已完成
   （口语化 / 不含必填字段）

❌ ✅ Feature 已交付（PR #58675e6 已合并）
   （工程摘要伪装成状态行）

❌ 当前状态：Teamwork / Bug / Ship 等待合并（暂停）
   （v7.3.10+P0-118 实证 PTR-F001-BUG-013 Bug Ship Phase 1 case · 摘要风格 / 缺 📁 + 🌿 + 📚 决策参考）
   根因：PMO 沿用主对话上文轻量摘要风格 · 没读 ship-stage.md spec · STATUS-LINE.md Preflight 未触发
   修复：v7.3.10+P0-118 把 Preflight 升格 SKILL.md R5(c) 红线（每次启动必读 · 不再依赖 Read spec 触发）

❌ 输出 📋 阶段流转校验行后**跳过** 🔄 末尾状态行（v7.3.10+P0-118-A 同 case 子根因）
   （📋 校验行示例：「📋 Ship 等待合并 → 🔗 Ship Stage 第二段 finalize（📖 ⏸️，来源 flow-transitions.md L166...）」）
   根因：「阶段流转校验行」和「末尾状态行」是两类不同输出 · PMO 容易把前者当成"状态相关已输出"就跳过后者
   边界：⏸️ 暂停点必须两者并存 · 🚀 自动流转仅 📋 校验行
   修复：v7.3.10+P0-118-A 在 rules/flow-transitions.md 顶部加硬约束 + 7 处暂停点模板内嵌状态行骨架

✅ 🔄 Teamwork 模式 | 流程：敏捷需求 | 角色：PMO | 功能：INFRA-F017-... | 阶段：✅ 已完成 | 下一步：无
   📁 /Users/.../docs/features/INFRA-F017-.../
   📍 当前分支：staging → staging（worktree 已清理）
   （标准 3 行格式 / 含必填字段 / 阶段值在表中）
```

🔴 **「功能完成」例外明确化**：completed 状态的最后一条回复**仍然必须**带状态行（功能完成 ≠ 流程退出）：

- 阶段：`✅ 已完成`（v7.3.10+P0-66 起单一规范措辞 · 之前散落的「✅ 已交付」措辞 deprecated）
- 下一步：`无`
- 第二行 / 第三行按现行规则保留（功能目录路径 + worktree 状态如已清理则注明）

退出真正发生在**这条回复之后**用户输入新无关需求 / `/teamwork exit` / 或对话结束时。

**state.json `current_stage` enum vs 阶段字段语义映射（v7.3.10+P0-55 新增）**：

```
state.current_stage enum 值 → STATUS-LINE 阶段字段语义
├── triage              → "需求理解中"
├── goal_plan           → "PRD 起草中" / "PRD 评审中" / "⏸️ PRD 待确认"（按子步骤）
├── ui_design           → "UI 设计中" / "⏸️ 设计稿待确认"
├── blueprint           → "TC 起草中" / "TECH 起草中" / "⏸️ Blueprint 待确认"
├── dev                 → "开发中" / "TDD 红绿循环"
├── review              → "三视角并行审查" / "⏸️ QUALITY_ISSUE 待处理"
├── test                → "集成测试 / E2E 中"
├── browser_e2e         → "Browser E2E 中" / "⚡ AUTO 跳过"
├── pm_acceptance       → "⏸️ PM 验收（3 选 1）"
├── ship                → "净化 + push" / "⏸️ MR 待合并" / "Ship 第二段 finalize 中"
└── completed           → "✅ 已完成"（v7.3.10+P0-66 单一规范 · 替换原「✅ 已交付」）
```

🔴 PMO 渲染 STATUS-LINE 时按本表映射 current_stage 到语义化阶段字段，不直接显示 enum 值。

---

### 🔴 决策点参考文档绝对路径硬规则（v7.3.10+P0-75 实战补充）

> 触发：实战 case（AND-F062 Review QUALITY_ISSUE 决策点）PMO 给了 4 个选项 + 推荐理由，但**没列做这个决策需要参考的文档绝对路径**（REVIEW.md / external-cross-review/*.md / 涉及代码文件）。用户被迫凭记忆找路径或盲信摘要做决策。同 case 还出现代码文件被错误包成 `[file.java](http://file.java)` markdown 链接 → 指向虚假 URL → 不可点击。

🔴 **决策类暂停点必须含「📚 决策参考」段**，列出参考文档 / 代码文件的**绝对路径**，让用户直接 drill-down 到 evidence。

🔴 **与 mode 字段的关系（v7.3.10+P0-76）**：决策类暂停点 ⊆ **⏸️ HITL** 集合（auto 模式不豁免 + 必含 📚 决策参考）；非决策类暂停点 ⊆ **⏸️ AFK** 集合或部分 HITL（详见 [rules/flow-transitions.md § ⏸️ HITL 清单 / AFK 示例](../rules/flow-transitions.md)）

#### 决策类暂停点清单（必须列 references · 全部归 HITL）

```
1. Review Stage QUALITY_ISSUE 决策（A/B/C/D 修哪些 finding）
   📚 必含：REVIEW.md / external-cross-review/review-external-{model}.md（如启用）/ 涉及代码文件 / 涉及测试文件
2. PRD 评审 verdict（PASS / NEEDS_REVISION / 用户对 finding 的处理）
   📚 必含：PRD.md / PRD-REVIEW.md / 相关 KNOWLEDGE / ADR
3. 流程类型识别歧义（多候选 / Bug 升级 Feature / Micro 升级敏捷）
   📚 必含：BUG-REPORT.md（Bug 流程）/ 用户原始消息引用 / 准入条件检查表
4. 评审组合智能推荐用户改选
   📚 必含：roles/pmo.md 智能推荐表 / 上一轮 PRD-REVIEW.md 的 finding 密度
5. PL-PM 业务方向分歧（discuss）
   📚 必含：PRD-REVIEW.md.reviews[role=pl].pl_rounds[] / product-overview.md / 相关 ADR
6. PM 验收三选项
   📚 必含：PRD.md / TC.md / 测试报告 / Browser E2E 截图（如适用）
7. Stage 入口偏差判定（Goal-Plan / Blueprint / Review 推荐组合需调整）
   📚 必含：state.json.execution_plan_skeleton.stages[] / 上一 Stage 产物
8. 升级确认（Micro → 敏捷 / Bug 简单 → Bug 复杂 / 敏捷 → Feature）
   📚 必含：当前流程的入口准入条件 / 触发升级的具体 finding
9. ADR 候选方案选择（Blueprint Stage 触发 ADR 时）
   📚 必含：相关历史 ADR / 候选方案对比段（在 PRD 或 TECH 内）
10. 技术评审分歧（Blueprint Stage TECH 评审 NEEDS_REVISION）
    📚 必含：TECH.md / TECH-REVIEW.md / 涉及 ARCHITECTURE.md 段
```

#### 非决策类暂停点（不强制列 references）

```
- ok / 反馈 二选一（继续 / 不继续）
- 用户手测验收（Micro / 简单 Bug）
- push 失败降级 2 选 1
- 等待外部依赖恢复 / 外部依赖已就绪
- 简单流程类型确认（用户消息已明确 · 无歧义）
```

#### 渲染规范

🔴 **格式**（紧跟 ⏸️ 决策点选项之后 / 状态行之前）：

```
⏸️ 决策点（请回数字）
1. 💡 ...
2. ...
3. ...
4. 其他指示

📚 决策参考（点击查看）：
{emoji} {绝对路径}
{emoji} {绝对路径}
...
```

🔴 **emoji 约定**：
- `📄` 规范文档 / 评审产物（PRD.md / TC.md / TECH.md / REVIEW.md / PRD-REVIEW.md / external-cross-review/*.md / BUG-REPORT.md）
- `📝` 代码文件 / 测试文件（*.java / *.ts / *.py / *_test.go 等）
- `🔗` MR URL / 外部链接（含 `?` `=` `%` 查询参数的长 URL · 仍须独立成行）

🔴 **路径规范**（继承 P0-67 / P0-70）：
- 必须**绝对路径**（以 `/` 开头）
- 路径**前后** whitespace 边界（emoji + 半角空格 + 路径 + 换行）
- ❌ **禁止用 markdown 链接语法包裹**：`[REVIEW.md](http://REVIEW.md)`（实战漂移产物 · 终端会指向虚假 URL · 不可点击）
- ❌ **禁止只写文件名 / 相对路径**：`📄 REVIEW.md`（用户不知道是哪个 worktree / 哪个 Feature）
- ❌ **禁止挤入表格列**（继承 P0-70 路径不进表格列规则）

#### 正反例

❌ **错误（实战 AND-F062 case）**：
```
⏸️ 决策点（请回数字）
1. 💡 追认方案 A + RD 修测试 bug + 提交
2. 重新审视 QUALITY_ISSUE 改选 B / C / D
3. 进 worktree 让我自己看看代码再决定
4. 其他指示
```
（无参考路径 · 用户做不了 informed decision · PMO 摘要黑盒）

❌ **错误（markdown 链接漂移）**：
```
- [VpnAppExclusionPolicy.java](http://VpnAppExclusionPolicy.java)：加 cap...
```
（指向虚假 http URL · 终端不可点击 · 失去绝对路径定位）

✅ **正确**：
```
⏸️ 决策点（请回数字）
1. 💡 追认方案 A + RD 修测试 bug + 提交
   📝 推荐理由：代码逻辑符合建议、改动范围合理...
2. 重新审视 QUALITY_ISSUE 改选 B / C / D
3. 进 worktree 让我自己看看代码再决定
4. 其他指示

📚 决策参考（点击查看）：
📄 /Users/.../docs/features/AND-F062-.../REVIEW.md
📄 /Users/.../docs/features/AND-F062-.../external-cross-review/review-external-claude.md
📝 /Users/.../android/.../VpnAppExclusionPolicy.java
📝 /Users/.../android/.../VpnAppExclusionPolicyTest.java
```

#### 实施约束

🔴 **PMO 在决策类暂停点 self-check**（Final Response Preflight 4 项之外的扩展）：
- 决策类暂停点 → 必含「📚 决策参考」段
- 路径绝对（不是相对 / 不是文件名）
- 路径独立成行（不挤表格 / 不包 markdown 链接语法）
- 路径前后 whitespace 边界

违反 = 流程偏离（用户被迫盲选 · 决策质量受损）。
```

---

### 🔴 暂停点模板渲染契约（v7.3.10+P0-115 新增 · 单源反向 cite）

> **触发**：实战 case（PM 验收暂停点 verbatim 渲染时漏标准状态行）暴露 spec 文件中的暂停点模板（`roles/pmo-*-ship.md` / `stages/*-stage.md` 内的 verbatim ⏸️ 模板块）若不显式 cite 本文件 · AI 严格按模板渲染时会漏 📚 决策参考 + 漏 3 行状态行。

🔴 **所有 spec 文件的 verbatim 暂停点模板必须 cite 本文件**（不复述格式 · 保单源）：

```
任意 spec 文件中的 ⏸️ 暂停点 verbatim 渲染模板末尾必须写：

🔴 渲染必含（cite STATUS-LINE.md · 不在本文件复述格式）：
- 决策类暂停点 → 📚 决策参考段（cite STATUS-LINE.md § 决策点参考文档绝对路径硬规则 · 列绝对路径）
- 标准 3 行状态行 → cite STATUS-LINE.md § 状态行格式定义
  · 阶段值取自本文件 § state.json current_stage enum vs 阶段字段语义映射
```

🔴 **架构原则**：
- 状态行格式 / emoji 间隔 / 路径边界 / 决策参考清单 = 本文件单源
- spec 文件只声明「这是哪类暂停点 · 阶段 enum 是什么」 · 反向 cite 本文件
- 未来本文件改格式（如 P0-62 emoji / P0-67 路径边界 / P0-70 表格列规则）· spec 文件零修改自动跟随

🔴 **覆盖清单**（v7.3.10+P0-115 已加 cite 的 spec 暂停点模板）：

| 文件 | 暂停点 | 决策类？ | 阶段 enum |
|------|-------|---------|---------|
| `roles/pmo-pm-acceptance-ship.md` § 2.2 | PM 验收（3 选 1） | ✅ 决策类 | `pm_acceptance` |
| `stages/ship-stage.md` Step 3 变体 A/B | Phase 1 第一段报告（4 选 1） | ✅ 决策类 | `ship` |
| `stages/ship-stage.md` 完成报告 | worktree 清理（3 选 1） | 非决策类 | `ship` |
| `stages/ship-stage.md` 异常处理 | MR 异常（4 选 1） | ✅ 决策类 | `ship` |
| `stages/goal-plan-stage.md` 子步骤 5 | PRD 用户最终确认（4 选 1） | ✅ 决策类 | `goal_plan` |
| `stages/prepare-stage.md` Step 13 | 双对齐暂停（ok / 反馈） | 非决策类 | `triage` |

新增 spec 暂停点模板时必须加 cite + 更新本表。

---

**⚡ AUTO 徽章示例**（v7.3.9+P0-11）：

```
AUTO_MODE=true：
🔄 Teamwork 模式 ⚡ AUTO | 流程：Feature | 角色：PMO | 功能：API-F001-用户认证 | 阶段：PRD 待确认 | 下一步：⚡ 自动进入 UI Design
📁 /Users/dev/projects/myapp/docs/features/API-F001-用户认证/
🌿 分支：feature/API-F001-用户认证 → staging | worktree：/Users/dev/projects/myapp-worktrees/API-F001-用户认证

AUTO_MODE=false（默认，不显示徽章）：
🔄 Teamwork 模式 | 流程：Feature | 角色：PMO | 功能：API-F001-用户认证 | 阶段：⏸️ PRD 待确认 | 下一步：⏸️ 等待用户确认
```

**🌐 Ext 徽章示例**（v7.3.10+P0-24）：

```
启用外部模型交叉评审（model=codex）：
🔄 Teamwork 模式 🌐 Ext: codex | 流程：Feature | 角色：PMO | 功能：API-F001-用户认证 | 阶段：Goal-Plan Stage | 下一步：⏸️ PRD 待确认

AUTO 模式 + 外部模型同时启用：
🔄 Teamwork 模式 ⚡ AUTO 🌐 Ext: claude | 流程：敏捷需求 | 角色：PMO | 功能：UI-F012-导出 CSV | 阶段：Blueprint Stage | 下一步：⚡ 自动进入 Dev

外部模型未启用（默认）：
🔄 Teamwork 模式 | 流程：Feature | 角色：PMO | ...
```

### 各流程状态行差异表（v7.3.10+P0-116 压缩 · 单源对照）

| 流程 | 流程字段 | 必填字段 | 第二行 📁 | 第三行分支语义 |
|------|---------|---------|---------|------------|
| **Feature** | `Feature` | 功能：`{缩写}-F{编号}-{功能名}` | `docs/features/{功能目录}/` | 🌿 `feature/{Feature 全名} → {merge_target}` |
| **敏捷需求** | `敏捷需求` | 功能：`{缩写}-A{编号}-{功能名}` | `docs/features/{功能目录}/` | 🌿 `feature/{敏捷全名} → {merge_target}` |
| **Bug 处理** | `Bug 处理` | Bug：`BUG-{编号}-{简述}` | `docs/features/{功能目录}/bugfix/{BUG编号}/` | 🌿 `bugfix/{编号}-{简述} → {merge_target}` |
| **Micro** | `Micro` | 功能：`Micro-{简述}` | 改动文件路径 / 子项目根 | 默认 📍 `当前分支`（⚠️ 直接改主分支 · worktree=auto 时升 🌿 `chore/{简述}`） |
| **问题排查** | `问题排查` | （无功能编号） | 可省略 | 可省略 / 📍 `当前分支`（不改代码） |
| **Feature Planning** | `Feature Planning` | 受影响子项目：`[AUTH, WEB, ...]` | `teamwork_space.md` 或 `{子项目}/docs/ROADMAP.md` | 📍 `当前分支`（Planning 不改代码） |
| **跨项目需求拆分** | `Feature` | 跨项目需求 + 涉及：`[AUTH, WEB, ...]` | `teamwork_space.md` | （拆分阶段省略 / 拆分后按子项目走对应分支） |

**Feature 完整示例**（其他流程套用差异表）：

```
---
🔄 Teamwork 模式 | 流程：Feature | 角色：PMO | 功能：API-F001-用户认证 | 阶段：PMO 分析中 | 下一步：🔗 Goal-Plan Stage
📁 /Users/dev/projects/myapp/docs/features/API-F001-用户认证/
🌿 分支：feature/API-F001-用户认证 → staging | worktree：/Users/dev/projects/myapp-worktrees/API-F001-用户认证
```

**多子项目变体**（任意流程通用）：第一行 `流程：X` 之后插入 `子项目：{缩写}` · 第二行路径加 `{子项目}/` 前缀。

**worktree=off 退化**：第三行 🌿 → 📍（`📍 当前分支：{branch} → {merge_target}（⚠️ 未启用 worktree，并行 Feature 请注意隔离）`）。

### 第二行路径规则

```
默认优先输出当前阶段实际落盘的功能目录或状态文件路径。
示例优先级：
├── Feature / 敏捷需求 → 功能目录
├── Bug → bugfix 目录
├── 工作区级 Planning / 跨项目拆分 → teamwork_space.md
└── 纯问题排查且尚未产出文档 → 可省略第二行
```

### 第三行分支规则

```
默认优先输出 state.json 中的 worktree + merge_target 组合。
渲染决策：
├── state.json.worktree.strategy == "auto" / "manual" + path 存在 → 🌿 分支：... | worktree：...
├── state.json.worktree.strategy == "off" → 📍 当前分支：... → {merge_target}
├── Micro 默认 off → 📍 当前分支：{git branch --show-current}（用户显式开启 worktree=auto 时才走 🌿 分支）
├── Goal-Plan Stage preflight 之前 worktree 尚未创建 → 省略第三行或标注"worktree 待创建"
├── 问题排查 / PL 纯讨论 / 初始 PMO 分析 → 可省略
└── 🔴 禁止：worktree.path 用相对路径 / 伪造 state.json 字段 / 混用 🌿 和 📍 语义
```

### 下一步说明规则

```
下一步内容根据流转规则填写：
├── 自动流转阶段 → 「自动进入 XXX」
├── 暂停等待阶段 → 「⏸️ 等待用户确认 XXX」
├── 用户确认后 → 「用户确认后进入 XXX」
└── 已完成 → 「无（功能已完成）」
```

---

## 阶段与下一步对照表

**唯一权威定义，其他文件引用此表**。

```
🔴 硬约束：
├── 「阶段」字段只能使用下表中「状态行显示」列的值，禁止自编内容
├── 「下一步」字段只能使用下表中「下一步」列的值，禁止填写具体命令、commit hash 等
└── 不在表中的阶段值 = 非法状态，必须纠正
```

| 阶段 | 状态行显示 | 下一步 |
|------|-----------|--------|
| **Feature 流程（8 Stage）** | | |
| PMO 初步分析 | 阶段：PMO 分析中 | 下一步：🔗 Goal-Plan Stage |
| 🔗 Goal-Plan Stage | 阶段：🤖 Goal-Plan Stage 执行中（PRD+讨论+评审） | 下一步：⏸️ 等待用户确认 PRD |
| PRD 待确认 | 阶段：⏸️ PRD 待确认 | 下一步：用户确认后进入 UI Design / Blueprint |
| 🔗 UI Design Stage | 阶段：🤖 UI Design 执行中 | 下一步：⏸️ 等待用户确认设计 |
| UI 待确认 | 阶段：⏸️ UI 待确认 | 下一步：Panorama Design / Blueprint |
| 🔗 Panorama Design Stage | 阶段：🤖 全景设计更新中 | 下一步：⏸️ 等待用户确认全景 |
| 全景待确认 | 阶段：⏸️ 全景待确认 | 下一步：Blueprint Stage |
| ⚠️ _UI 跳过规则_ | _PRD「需要 UI: 否」→ 跳过 UI Design + Panorama，直接 Blueprint_ | _（非阶段）_ |
| 🔗 Blueprint Stage | 阶段：🤖 Blueprint 执行中（TC+技术方案+评审） | 下一步：⏸️ 等待用户确认方案 |
| 方案待确认 | 阶段：⏸️ 方案待确认 | 下一步：用户确认后进入 Dev Stage |
| 🔗 Dev Stage | 阶段：🤖 Dev Stage 执行中（RD TDD+单测） | 下一步：🚀 Review Stage |
| 🔗 Review Stage | 阶段：🤖 Review Stage 执行中（架构师CR∥Codex∥QA审查） | 下一步：🚀 Test Stage / NEEDS_FIX → RD 修复 |
| 🔗 Test Stage | 阶段：🤖 Test Stage 执行中（集成∥E2E） | 下一步：Browser E2E 判断 / PM 验收 |
| 🔗 Browser E2E Stage | 阶段：🤖 Browser E2E 执行中 | 下一步：通过 → PM 验收 / 有问题 → RD 修复 |
| PM 验收 | 阶段：PM 验收中 | 下一步：PMO 完成报告 |
| 功能完成 | 阶段：✅ 已完成 | 下一步：无 |
| **敏捷需求流程差异阶段** | | |
| 精简 PRD 编写 | 阶段：PRD 编写中（精简版） | 下一步：⏸️ 等待用户确认 PRD |
| PRD 待确认（敏捷） | 阶段：⏸️ PRD 待确认 | 下一步：用户确认后进入 BlueprintLite |
| 🔗 BlueprintLite Stage | 阶段：BlueprintLite 执行中（简化TC+实现计划） | 下一步：🚀 Dev Stage |
| _敏捷后续（Dev→Review→Test→PM验收）复用 Feature 定义_ | | |
| _以下为 Micro 流程专用阶段（v7.3.10+P0-20：主对话 PMO→RD 身份切换，由 RD 改动；不再启 Subagent；角色切换必读 rd.md+standards/*.md 不可豁免）_ | | |
| PMO 加载 RD 规范（Micro）| 阶段：PMO→RD 身份切换、加载 RD 规范中 | 下一步：RD 执行改动 |
| RD 执行改动（Micro） | 阶段：RD 执行改动中 | 下一步：RD 自查 |
| RD 自查（Micro）| 阶段：RD 自查中 | 下一步：⏸️ 等待用户验收 |
| Micro 升级判定 | 阶段：⏸️ Micro 升级确认 | 下一步：用户确认后进入敏捷 / Feature |
| 用户验收（Micro） | 阶段：⏸️ 用户验收中 | 下一步：通过 → PMO 完成报告 |
| RD Bug 排查 | 阶段：Bug 排查中 | 下一步：PMO 判断流程 |
| PMO Bug 判断 | 阶段：PMO 流程判断 | 下一步：QA 补充用例 |
| QA 补充用例 | 阶段：QA 补充用例中 | 下一步：RD 修复 |
| RD Bug 修复 | 阶段：Bug 修复中 | 下一步：RD 自查 |
| RD Bug 自查 | 阶段：Bug 自查中 | 下一步：架构师 Code Review |
| 架构师 Bug Code Review | 阶段：架构师 Code Review 中 | 下一步：QA 验证 |
| QA Bug 验证 | 阶段：QA 验证中 | 下一步：PM 文档同步检查 |
| PM 文档同步 | 阶段：文档同步检查中 | 下一步：PMO 结束流程 |
| PMO Bug 总结 | 阶段：PMO 总结中 | 下一步：流程结束 |
| Bugfix 完成 | 阶段：✅ Bugfix 已完成 | 下一步：无（Bugfix 已完成）|
| 问题排查梳理 | 阶段：问题排查中 | 下一步：⏸️ 等待用户确认后续动作 |
| 排查待确认 | 阶段：⏸️ 排查待确认 | 下一步：用户确认后进入 Feature 流程（→ PMO 初步分析）/ Bug 处理流程（→ RD Bug 排查）/ 结束 |
| PM Roadmap 编写 | 阶段：Roadmap 编写中 | 下一步：⏸️ 等待用户确认 Roadmap |
| Roadmap 待确认 | 阶段：⏸️ Roadmap 待确认 | 下一步：用户确认后逐个启动 Feature |
| 🌐 Workspace 架构讨论 | 阶段：架构讨论中 | 下一步：PM 更新 teamwork_space.md |
| 🌐 teamwork_space.md 待确认 | 阶段：⏸️ teamwork_space.md 待确认 | 下一步：用户确认后逐个子项目 Planning |
| 🌐 子项目 Planning 中 | 阶段：子项目 [缩写] Planning | 下一步：该子项目全景设计/PROJECT.md/ROADMAP |
| 🌐 Workspace Planning 收尾 | 阶段：⏸️ 最终确认 | 下一步：用户确认后逐个启动 Feature |
| PL 引导模式 | 阶段：PL 引导（草案迭代中）| 下一步：⏸️ 等待用户审阅草案并反馈 |
| PL 讨论模式 | 阶段：PL 讨论中 | 下一步：⏸️ 等待用户确认讨论结论 |
| PL 结论待确认 | 阶段：⏸️ PL 结论待确认 | 下一步：用户确认后 PL 写入文档 / 进入执行模式 |
| PL 执行模式 | 阶段：PL 变更评估中 | 下一步：⏸️ 等待用户确认 CHG 变更记录 |
| CHG 待确认 | 阶段：⏸️ CHG 待确认 | 下一步：用户确认后启动 Feature Planning 级联 |
| ⏳ 等待外部依赖 | 阶段：⏳ 等待外部依赖（DEP-XXX） | 下一步：依赖就绪后恢复推进 |
| 外部依赖已就绪 | 阶段：外部依赖已就绪 | 下一步：⏸️ 用户确认后恢复 Feature 流程 |

---

## 跨主题单源指针（v7.3.10+P0-116 抽出 · 跨文件单源）

```
📎 用户回复识别（数字 / 字母组合 / ok 约定 / 自由输入解析）→ RULES.md § 4
📎 PMO 用户消息承接 + 意图识别 + 补充信息恢复 + 正确响应模式 → roles/pmo-user-input.md
📎 红线 R3 PMO 统一承接（禁止其他角色直接响应）→ SKILL.md R3
📎 上下文恢复机制（compact / 新对话）→ CONTEXT-RECOVERY.md
```
