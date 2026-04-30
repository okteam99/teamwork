# 主对话输出 Tier 通用规范（v7.3.10+P0-54 抽取）

> 🔴 **本文件是所有 Stage 主对话输出形态的唯一权威源**。triage / Goal-Plan / blueprint / dev / review / test / ship 各 stage spec 引用本文件 + 加 stage-specific Tier 应用。

> 🟢 **抽取自**：原 triage-stage.md L751-853（P0-49-A 引入），三 stage 各自重复 → 单源化 + 各 stage 仅声明 Tier 应用部分。

---

## 一、决策呈现 vs 履职报告

主对话输出的核心是**给用户决策依据**，不是 PMO 履职汇报。规则：

```
✅ Tier 1（用户必看，永远输出）：
  ├── 决策点（暂停点 + 用户拍板内容）
  ├── 关键产出摘要（PRD / TC / TECH / REVIEW 等核心字段，不是完整复述）
  ├── 待确认文档/目录的**完整绝对路径**（v7.3.10+P0-61 — 见下方硬规则 §三-A）
  └── 状态变更声明（stage 切换 / 评审 verdict / 等）

🟡 Tier 2（命中 / 异常才输出，默认折叠）：
  ├── KNOWLEDGE / ADR 命中（仅在 Gotcha/Convention 命中时一行摘要）
  ├── 跨 Feature 冲突 / 跨项目依赖（仅在有冲突 / 依赖告警时输出）
  ├── 环境异常（仅在工作区脏 / path 偏离规范时一行摘要）
  └── 评审循环超 1 轮的 finding 累积（仅 round 2+ 时摘要）

❌ Tier 3（默认不输出，全部走 state.json）：
  ├── 角色可用性扫描（无异常时不输出）
  ├── 流程类型独立识别段（除非 PMO 不确定，否则识别结果直接体现在骨架/产物中）
  ├── worktree mode / path / artifact_root 等机读字段
  ├── state.json 配置详细复述（state.json 已存）
  └── "无变更归属" / "无 ADR" 等空段（不存在就不输出）
```

---

## 二、3 类反模式（必须杜绝）

### 反模式 1：履职报告体感（"我做了 N 件事"列表式）

```
❌ PMO 把扫了 KNOWLEDGE / 扫了 ADR / 扫了角色 / 识别了流程 / 查了冲突 /
   探测了环境 全部立段。即使没命中也立"无 ADR" / "无冲突" 段。
   用户最关心的决策点被推到第 N 段。
   → 用户认知负担 = N 段平铺，没法快速找到决策点。
```

### 反模式 2：state.json 复述表（违反 P0-48 红线）

```
❌ 把 worktree mode / path / sub_project / artifact_root 等机读字段
   以"维度: ... 值: ... 计划行为: ..."表格形态在主对话渲染。
   → state.json 已存，主对话再述 = padding。
```

### 反模式 3：决策菜单膨胀（违反双对齐姿态）

```
❌ 把"ok / 反馈"二选一退化为"1. 意图反馈 / 2. 调整骨架 / 3. 拍板 unknown /
   4. 切流程 / 5. 其他"。用户必须先选编号才能反馈。
   → 决策疲劳。"反馈"应该是自由文本入口，PMO 解析时分类，不让用户先选。
```

### 反模式 4：工程性切片暂停（违反 P0-45 反转）

```
❌ "暂停以让你预览 PRD 初稿（避免下一回复 dispatch 5 个 subagent 后重写）"
   → 评审本身就是发现偏离的机制；用户决议已嵌入 PRD。
   → 仅严重偏差时才暂停（standards/stage-instantiation.md 6 维度判定）。
```

---

## 三、Tier 应用通用规则

```
🔴 Tier 1 必须最前：用户最关心的决策点 / 产物摘要 / 状态变更，物理位置在 Tier 2/3 任何履职报告之前。

🔴 Tier 2 默认折叠：仅在命中或异常时输出一行摘要 + 详情指向 state.json / 对应资产文件。

🔴 Tier 3 不输出：机读字段 / 空段扫描结果 / 配置详细复述 全部走 state.json，绝对不在主对话渲染。

🔴 反模式禁令：4 类反模式（履职报告 / state.json 复述 / 决策菜单膨胀 / 工程性切片暂停）必须杜绝。
```

### 三-A、待确认文档绝对路径硬规则（v7.3.10+P0-61）

**触发**：任何**用户需要确认/查看**的暂停点（PRD / TC / TECH / UI / REVIEW / 验收报告 / triage 骨架 / Feature 目录创建 / Bug 报告 / 排查记录 等）。

**硬规则**：
- 🔴 **必须输出完整绝对路径**（以 `/` 开头），方便用户在终端 / IDE / Finder 直接点击打开
- 🔴 **禁止仅输出相对路径**（如 `apps/partner/docs/features/...`）—— 终端通常不识别相对路径为可点击
- 🔴 **emoji 与路径之间必须保留一个半角空格**（v7.3.10+P0-62）：`📁 /Users/...`（✅）/ `📁/Users/...`（❌ 终端把 emoji+路径视为一体，不可点击）。同规则适用于状态行所有图标（见 STATUS-LINE.md § emoji 间隔硬规则）
- 🔴 路径计算：`{当前工作目录的绝对路径} + {相对项目根的资产路径}`
  - 当前工作目录：PMO 从主对话上下文已知（init Stage 探测）/ 必要时调用 `pwd`
  - 相对路径：来自 `state.artifact_root` 或资产文件名
- 🟢 多个文件用列表呈现（不要并列在一行内压成单行不可读）
- 🟢 是目录就输出目录路径（用户可直接 `ls` 或在 IDE 里展开）；是单文件就输出文件路径

**输出格式（暂停点结尾必含）**：

```markdown
📁 待确认资产：
   /Users/{user}/projects/{repo}/apps/partner/docs/features/PTR-F016-Integration-Testing-Fetch真实化/PRD.md
   /Users/{user}/projects/{repo}/apps/partner/docs/features/PTR-F016-Integration-Testing-Fetch真实化/PRD-REVIEW.md

⏸️ 双对齐确认 / PM 验收 / 等具体决策菜单
```

**示例对比**：

```
❌ 错误（用户无法点击）：
   ⏸️ 用户确认 PRD：apps/partner/docs/features/PTR-F016/PRD.md

✅ 正确（终端可点击）：
   📁 待确认 PRD：/Users/liam/apps/joli/aon/apps/partner/docs/features/PTR-F016/PRD.md
   ⏸️ 用户确认
```

**例外**：
- 仅当待确认资产**不是文件**（如纯主对话渲染的骨架内容、口头确认的方向决策）时，可不输出路径
- 状态行里的 `📁 ...` 已是相对路径（保留为状态行格式），不强制改绝对——本规则只约束**暂停点决策行附近的资产指针**

---

## 四、各 Stage 引用约定

各 Stage spec 在 Process Contract 段加：

```markdown
## 主对话输出 Tier 应用

> 🔴 **遵循 [standards/output-tiers.md](../standards/output-tiers.md) 通用 Tier 1/2/3 规范 + 4 类反模式禁令**。

本 Stage 特定 Tier 应用：

- **Tier 1（永远输出）**：<本 Stage 决策点 + 关键产出摘要>
- **Tier 2（命中折叠）**：<本 Stage 可能的 命中 / 异常项>
- **Tier 3（不输出，走 state.json）**：<本 Stage 的机读字段>
```

---

## 五、设计意图

triage 在实战 case（SVC-PLATFORM-F026）出现 9 段履职报告 + state.json 复述 + 5 选 1 菜单——这些都不该是主对话内容。Tier 1/2/3 强制 PMO 把"我做了什么"折到 state.json，主对话只装"用户必须看的决策依据"。这是 P0-49-A 的核心意图。

P0-54 把这套规范从 triage-stage.md 抽到本文件，并扩展应用到所有 Feature 级 stage（Goal-Plan / blueprint / dev / review / test / ship）—— 防止其他 stage 重复 triage 的体感问题。

末。
