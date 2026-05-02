# 状态行与意图识别

> 本文件包含：
> - 流程持续规则与状态行格式定义
> - 用户意图识别与分发规则
> - 上下文恢复机制
>
> **快速导航**：
> - 状态行格式 → 每次回复末尾必需
> - 意图识别 → 处理用户输入的决策树
> - Compact 恢复 → 新对话快速恢复上下文

---

## 流程持续规则（会话级 Skill 加载）

### 🔒 Teamwork 模式激活后自动持续

**一旦通过 `/teamwork` 启动，整个对话都应遵循此流程，直到明确退出。**

```
激活条件（满足任一）：
├── 用户输入 /teamwork [需求]
├── 用户输入 /teamwork 继续
├── 对话历史中已有 teamwork 流程（检查 docs/features/ 目录）
└── 用户回复与当前进行中的功能相关

退出条件（满足任一）：
├── 用户输入 /teamwork exit 或 /exit
├── 用户明确说「退出」「结束流程」「不用了」
├── 当前功能完成且用户无新需求
└── 用户开启完全无关的新话题
```

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
└── 触发来源：/teamwork auto [需求]（详见 [stages/init-stage.md](./stages/init-stage.md) Step 0）
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
```

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

### Feature / 敏捷需求流程（🔴 功能字段必填）

```
---
🔄 Teamwork 模式 | 流程：Feature | 角色：[当前角色] | 功能：[{缩写}-F{编号}-{功能名}] | 阶段：[当前阶段] | 下一步：[下一步事项]
📁 /绝对路径/docs/features/[功能目录]/
🌿 分支：feature/[{缩写}-F{编号}-{功能名}] → [merge_target] | worktree：/绝对路径/[worktree 目录]

多子项目时追加子项目字段：
🔄 Teamwork 模式 | 流程：Feature | 子项目：[缩写] | 角色：[当前角色] | 功能：[{缩写}-F{编号}-{功能名}] | 阶段：[当前阶段] | 下一步：[下一步事项]
📁 /绝对路径/[子项目]/docs/features/[功能目录]/
🌿 分支：feature/[{缩写}-F{编号}-{功能名}] → [merge_target] | worktree：/绝对路径/[worktree 目录]
```

**示例**：
```
---
🔄 Teamwork 模式 | 流程：Feature | 角色：PMO | 功能：API-F001-用户认证 | 阶段：PMO 分析中 | 下一步：🔗 Goal-Plan Stage
📁 /Users/dev/projects/myapp/docs/features/API-F001-用户认证/
🌿 分支：feature/API-F001-用户认证 → staging | worktree：/Users/dev/projects/myapp-worktrees/API-F001-用户认证

（多子项目）
🔄 Teamwork 模式 | 流程：Feature | 子项目：AUTH | 角色：RD | 功能：AUTH-F001-用户登录 | 阶段：🤖 Dev Stage 执行中（RD TDD+单测） | 下一步：🚀 Review Stage
📁 /Users/dev/projects/myapp/auth-service/docs/features/AUTH-F001-用户登录/
🌿 分支：feature/AUTH-F001-用户登录 → staging | worktree：/Users/dev/projects/myapp/auth-service-worktrees/AUTH-F001-用户登录

（worktree=off 退化示例，并行 Feature 时不推荐）
🔄 Teamwork 模式 | 流程：Feature | 角色：RD | 功能：API-F001-用户认证 | 阶段：🤖 Dev Stage 执行中 | 下一步：🚀 Review Stage
📁 /Users/dev/projects/myapp/docs/features/API-F001-用户认证/
📍 当前分支：feature/API-F001-用户认证 → staging（⚠️ 未启用 worktree，并行 Feature 请注意隔离）
```

### 跨项目需求拆分阶段

```
---
🔄 Teamwork 模式 | 流程：Feature | 角色：PMO | 跨项目需求：[需求简述] | 阶段：需求拆分 | 涉及：[AUTH, WEB] | 下一步：⏸️ 等待用户确认拆分方案
📁 /绝对路径/teamwork_space.md
```

### 🌐 工作区级 Planning 状态行格式

```
---
🔄 Teamwork 模式 | 流程：Feature Planning | 角色：[PM/PMO] | 阶段：[工作区级 Planning - 当前阶段] | 受影响子项目：[AUTH, WEB, ADMIN] | 下一步：[下一步事项]
📁 /绝对路径/teamwork_space.md
```

**示例**：
```
---
🔄 Teamwork 模式 | 流程：Feature Planning | 角色：PM | 阶段：工作区级 Planning - 架构讨论中 | 受影响子项目：待定 | 下一步：讨论子项目拆分方案
📁 /Users/dev/projects/myapp/teamwork_space.md
---
🔄 Teamwork 模式 | 流程：Feature Planning | 角色：PM | 阶段：工作区级 Planning - ⏸️ teamwork_space.md 待确认 | 受影响子项目：AUTH, WEB | 下一步：⏸️ 等待用户确认架构变更
📁 /Users/dev/projects/myapp/teamwork_space.md
---
🔄 Teamwork 模式 | 流程：Feature Planning | 子项目：WEB | 角色：PM | 阶段：Roadmap 编写中 | 下一步：⏸️ 等待用户确认 Roadmap
📁 /Users/dev/projects/myapp/web/docs/ROADMAP.md
```

### Bug 处理流程状态行格式

```
---
🔄 Teamwork 模式 | 流程：Bug 处理 | 子项目：[缩写]（多子项目时）| 角色：[当前角色] | Bug：BUG-{编号}-{简述} | 阶段：[当前阶段] | 下一步：[下一步事项]
📁 /绝对路径/[子项目]/docs/features/[功能目录]/bugfix/[BUG编号]/
🌿 分支：bugfix/[BUG编号]-[简述] → [merge_target] | worktree：/绝对路径/[worktree 目录]
```

### 问题排查流程状态行格式

```
---
🔄 Teamwork 模式 | 流程：问题排查 | 子项目：[缩写] | 角色：[当前角色] | 阶段：[当前阶段] | 下一步：[下一步事项]
（第三行：问题排查不改代码，分支语义可省略；如已切到特定分支排查可输出 📍 当前分支：xxx）
```

### 敏捷需求流程状态行格式

```
---
🔄 Teamwork 模式 | 流程：敏捷需求 | 子项目：[缩写] | 角色：[当前角色] | 功能：[{缩写}-A{编号}-功能名] | 阶段：[当前阶段] | 下一步：[下一步事项]
📁 /绝对路径/[子项目]/docs/features/[功能目录]/
🌿 分支：feature/[{缩写}-A{编号}-功能名] → [merge_target] | worktree：/绝对路径/[worktree 目录]
```

### Micro 流程状态行格式

```
---
🔄 Teamwork 模式 | 流程：Micro | 子项目：[缩写]（多子项目时）| 角色：[当前角色] | 功能：Micro-{简述} | 阶段：[当前阶段] | 下一步：[下一步事项]
📁 /绝对路径/[子项目]/（或具体改动文件路径）
📍 当前分支：{当前分支名}（⚠️ Micro 直接改主分支，操作前确认工作区干净）

worktree=auto/manual 变体（单文件零逻辑变更也可选 off 跳过 worktree）：
🌿 分支：chore/{简述} → [merge_target] | worktree：/绝对路径/[worktree 目录]
```

**示例**：
```
---
🔄 Teamwork 模式 | 流程：Micro | 角色：RD | 功能：Micro-修复 README 拼写 | 阶段：RD 执行改动中 | 下一步：⏸️ 等待用户验收
📁 /Users/dev/projects/myapp/README.md
📍 当前分支：main（⚠️ Micro 直接改主分支，操作前确认工作区干净）
```

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

## 用户回复处理

| 用户回复 | 处理方式 |
|----------|----------|
| 明确确认（含流程名/阶段名） | 进入下一阶段 |
| 🟢 ok / OK / 好 / 可以 / 行 / 按建议（v7.3.10+P0-18） | 映射为「按当前暂停点全部 💡 推荐选项执行」。PMO 须 cite 一行『✅ 已按 💡 建议处理：…』。前置条件：暂停点至少有 1 个 💡；破坏性操作仍需显式回复（→ RULES.md §模糊确认处理 · ok 约定） |
| 模糊确认（≤5 字：其他非 ok 家族模糊词） | 🔴 PMO 先复述阶段链再等二次确认（→ RULES.md 模糊确认处理规则） |
| 改一下/调整/修改 | 当前角色处理后再请求确认 |
| 新需求描述 | 询问是否开启新功能流程 |
| 流程中断后回来 | 先输出状态看板，询问从哪里继续 |
| /teamwork exit | 退出 Teamwork 模式 |

---

## 🔴 用户消息意图识别规则（强制）

> → 红线 #4：所有用户输入 → PMO 先承接 → 识别意图 → 分发给对应角色。

### PMO 意图识别与分发表

| 类别 | 用户信号 | PMO 动作 |
|------|----------|----------|
| 🟢 流程控制 | 确认/OK/ok/好/可以/行/按建议/继续（v7.3.10+P0-18） | 有 💡 推荐 → 按 💡 推荐全部选项执行 + cite『✅ 已按 💡 建议处理』；无 💡 → 复述阶段链 + 二次确认（→ RULES.md §模糊确认处理） |
| 🟢 流程控制 | 补充信息/回答问题/信息查询 | 分发给当前角色处理 → 🔴 处理完后恢复流程上下文（见下方规则） |
| 🟢 流程控制 | 查看状态/进度 | 输出状态 |
| 🟡 修改调整 | 修改当前阶段文档内容 | 分发 → 当前角色修改 |
| 🟡 修改调整 | 补充当前阶段遗漏细节 | 分发 → 当前角色补充 |
| 🔴 新需求/变更 | 新功能需求 | PMO 分析 → 切换到 PM 写 PRD |
| 🔴 新需求/变更 | 功能变更 | PMO 分析 → 切换到 PM 更新 PRD + 走评审 |
| 🔴 新需求/变更 | 开发中功能的需求补充 | PMO 分析 → 切换到 PM 更新 PRD + 走评审 |
| 🔴 新需求/变更 | Bug 修复 | PMO 分析 → 切换到 RD 排查 |
| 🔴 新需求/变更 | 优化需求 | PMO 分析 → 切换到 PM 评估影响范围 |
| 🔴 新需求/变更 | 任何「改代码」的需求 | 禁止 RD 直接实现，必须走完整流程 |
| 🔵 问题排查 | 不确定原因/需要分析/「帮我看看 xxx」 | PMO 派发 RD/PM/Designer 排查 |
| 🔵 问题排查 | 梳理现有功能/逻辑 | PMO 派发对应角色梳理 → ⏸️ 用户决定后续 |

> ⚠️ 🟡 修改调整仅限「当前阶段文档层面的调整」，不涉及代码改动。涉及新增功能点、行为变更、需求补充 → 归入 🔴 新需求/变更类。
> 🔴 禁止 PM/RD/QA/Designer 直接承接用户输入！所有处理都必须由 PMO 承接 → 分发 → 总结！

---

## 🔴 补充信息/信息查询后必须恢复流程上下文

```
当 PMO 处于 ⏸️ 暂停等待用户确认状态时，用户可能：
├── 回答 PMO 的提问（补充信息）
├── 主动发起与当前流程无关的查询（如「xxx 配置在哪？」「有没有 xxx？」）
无论哪种，PMO 处理完后必须恢复之前的流程上下文，禁止因中间插入了 Q&A 就丢失待确认状态。

🔴 强制规则：
├── 处理完补充信息/查询后，必须重新输出之前的待确认项（或引用 state.json 中的 blocking.pending_user_confirmations）
├── 禁止将用户对查询的回复（如「需要」「有」「对」）自动绑定为流程确认或直接执行指令
├── 回答中禁止包含「要我做 X 吗？」等暗示直接执行的追问（见 RULES.md「暂停点提问必须锚定流程」）
└── 正确模式：回答查询 → 「回到之前的待确认项：{重新输出选项}，请确认走哪个流程？」

示例：
├── 流程上下文：PMO 已输出 Feature 分析 1/2/3 选项，⏸️ 等待用户确认
├── 用户插入：「infra 是否有 auth 的部署配置？」
├── ❌ 错误做法：PMO 回答查询 → 追问「要我创建配置吗？」→ 用户说「需要」→ PMO 直接写文件
└── ✅ 正确做法：PMO 回答查询 → 「回到之前的分析，您确认按方案 1/2/3 哪个走 Feature 流程？」
```

---

## ❌ 禁止任何角色直接响应用户输入

> → 红线 #4：所有用户输入必须由 PMO 先承接。无论 RD/PM/Designer/QA，均不得直接响应用户。

```
✅ 唯一正确流程：
用户输入 → PMO 承接 → PMO 分析 → PMO 分发给对应角色 → 角色执行 → PMO 总结
```

---

## ✅ 正确的响应模式

```
用户: /teamwork 后端 admin 页面 aid 比较混乱，统一梳理修改下

❌ 错误响应：
RD: 好的，我来看下代码然后修改...

✅ 正确响应：
PMO: 收到，让我先分析一下这个需求的性质...

📋 PMO 初步分析
├── 需求类型：Feature
├── 需求描述：统一梳理并修改 admin 页面中 aid 的使用
├── 📂 文档路径：{子项目}/docs/features/{前缀}-F{编号}-admin-aid统一/
├── 影响范围：待评估（需梳理 aid 使用情况）
├── 使用流程：Feature 流程
├── 阶段链：PRD → PL-PM 讨论 → PRD 技术评审 → ...（完整 Feature 链）
├── ⏸️ 请确认：(1) 走 Feature 流程 (2) 以上分析和影响范围
└── 🔄 切换到：PM（用户确认后）
└── ✅ 自检通过
```

---

## 上下文恢复机制

> 📎 新对话或上下文丢失时的完整恢复机制（决策树、Feature 看板、各流程状态判断）见 [CONTEXT-RECOVERY.md](./CONTEXT-RECOVERY.md)。
> 🔴 按需加载：仅在新对话启动或用户执行 `/teamwork status` / `/teamwork 继续` 时读取。

### Compact 恢复快速路径

**上下文压缩（compact）后，PMO 按以下最小路径恢复执行：**

```
1. 读取当前 Feature 的 state.json（v7.3.2）
   → 获得：current_stage / legal_next_stages / stage_contracts / blocking / planned_execution
2. 读取 RULES.md「PMO 热路径索引」（文件前 21 行）
   → 获得：按需定位具体规则的行范围索引
3. 如需详细规则 → 按索引定位读取 RULES.md 对应段落（非全文）
```

**🔴 PreCompact 保存要求**：PMO 在每次阶段流转时已同步更新 state.json（见 RULES.md §四），因此 compact 发生时无需额外保存操作——state.json 始终持有最新执行约束。
