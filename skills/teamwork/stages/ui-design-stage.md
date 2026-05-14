# UI Design Stage：Feature UI 设计 + 全景增量同步

> 用户确认 PRD 后（需要 UI 时）进入本 Stage。
> 🟢 **v7.3.4 合并**：Feature UI 和全景增量更新在同一 Stage 一次性产出，合并为一个「设计批」暂停点。
> 🔴 **全景是产品真相，修改必须谨慎**：全景设计（sitemap.md + overview.html）是已确认的设计 + 业务逻辑真相，默认**增量**合并本 Feature 内容，禁止重写；任何结构性变更必须在执行报告显式标红提示用户审查。
> 🔴 契约优先：执行方式由 AI 自主规划（默认 Subagent）。

---

## 本 Stage 职责

两件事一次性产出：
1. **本 Feature 的 UI**：UI.md + preview/*.html（覆盖正常/空/加载/错误 4 态）
2. **全景的增量同步**：将本 Feature 涉及的页面**合并**进 design/sitemap.md + design/preview/overview.html（默认增量，禁止重写）

产出一起给用户审（一个暂停点），避免原 UI 确认 + 全景确认两次打断。

📎 Feature Planning 流程的**全景重建**场景仍走独立的 [panorama-design-stage.md](./panorama-design-stage.md)（全景重建模式）；本 Stage 只做 Feature 流程的**增量合并**。

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/agents/README.md
├── {SKILL_ROOT}/stages/ui-design-stage.md（本文件）
├── {SKILL_ROOT}/roles/designer.md                 ← Designer 角色规范
├── {SKILL_ROOT}/templates/ui.md                   ← UI 设计模板
└── {Feature}/PRD.md（已确认）

🔴 全景基准（存在时必读，作为设计 + 业务逻辑真相）：
├── design/sitemap.md                              ← 全景页面地图
├── design/preview/overview.html                   ← 全景交互原型
└── design/preview/{相关页面}.html                  ← 全景中与本 Feature 相关的页面预览

可选：
├── docs/KNOWLEDGE.md                              ← 用户设计偏好
└── docs/PROJECT.md                                ← 产品总览
```

### Key Context（逐项判断，无则 `-`）

- 历史决策锚点（既定设计语言、配色规范、组件库）
- 本轮聚焦点（重派/修订场景必填）
- 跨 Feature 约束（与并行 UI Feature 的一致性）
- 已识别风险（如"全景导航结构最近有调整，注意对齐"）
- 降级授权
- 优先级 / 容忍度

### 前置依赖

- `{Feature}/PRD.md` 存在且确认
- state.json.current_stage == "ui_design"

---

## 入口 Read 顺序（v7.3.10+P0-23 固定）

🔴 按以下顺序 Read，字节一致利于 prompt cache 命中。详见 [standards/prompt-cache.md](../standards/prompt-cache.md)。

```
Step 1: roles/designer.md                              ← 角色层（L0 稳定）
Step 2: templates/ui.md                                ← 模板层（L0 稳定）
Step 3: {Feature}/PRD.md                               ← Feature 既有产物（L2）
        [条件] design/sitemap.md, design/preview/overview.html 及相关页面 preview  （全景基准，若存在）
Step 4: {Feature}/state.json                           ← 🔴 最后，动态入口（L3）
```

🔴 R3 约束：state.json 入口 Read 1 次 → 中段 0 读写 → 出口 Read 1 次 + Write 1 次。Subagent 整合豁免每次 dispatch 后 ≤1 次 Write；全 Stage ≤ 8 次。

---

## 🆕 Stage 入口实例化：全景路径探测（v7.3.10+P0-123 新增 · 跨子项目防漏 + 智能推荐）

> **触发条件**：本 Stage 实际启用（state.execution_plan_skeleton.stages 含 ui_design + PRD.requires_ui=true）。
>
> **设计原则**（P0-55 三层按需启动）：
> - 不在 prepare-stage 全仓库 find（无 UI 项目零开销）
> - 仅 UI Design Stage 真触发时跑探测（按需）
> - 探测结果在本 Stage 内部使用 · 不持久化 state.json（探测开销低 · 即时计算）
> - silent 优先（高置信度直接用）· 真不确定才 ⏸️ 暂停

### Step 0.1: 全仓库探测候选全景文件

```bash
# 即时执行 · 不依赖 prepare-stage
find {repo_root} -name "sitemap.md" -path "*/design/*" 2>/dev/null
find {repo_root} -name "overview.html" -path "*/design/preview/*" 2>/dev/null
```

**evidence-binding**（与 P0-101 协同 · 记录到本 Stage 执行摘要 · 不写 state.json）：
- command + stdout + exit_code + timestamp

### Step 0.2: 候选评分（PMO 智能推荐算法 · 即时计算）

| 评分维度 | 权重 | 判定 |
|---------|------|------|
| `hosting_subproject` = 当前 Feature 子项目 | +50 | 候选所在 design 路径前缀匹配 state.feature_subproject |
| sitemap.md 含 Feature 相关页面关键词 | +20 | grep PRD 关键词命中本候选 sitemap |
| preview/ 目录非空（≥3 个 HTML）| +10 | 全景成熟度 |
| design/ 路径深度（顶层 > 子项目）| +5 | 顶层 design/ 加 5 · 子项目内 design/ 不加 |
| teamwork_space.md 有 hosts_design 标注（多项目场景）| +30 | 显式声明 · 高优先级 |

🔴 **第 1 名标 💡 推荐** · 输出评分理由（具体分数 + 维度命中说明）。

### Step 0.3: 决策树（基于置信度阈值）

```
决策（按优先级）：
├── 最高评分 ≥ 60（信号充分 · 明显候选）
│   → silent 自动认定 · 内部记录 panorama_path = 候选 1
│   → 不暂停 · 不打扰用户
│
├── 0 候选（项目无全景设计）
│   → ⏸️ 暂停（推荐：触发 panorama-design 创建首版骨架）
│   → 用户可拒绝 → 项目无全景 · 跳过对齐校验
│
└── 探测后仍不确定（其他情况）
    触发条件：
    - 最高评分 < 60（信号不足）
    - 多候选评分接近（差 ≤ 15 分 · 平局）
    - 跨子项目 + 无明确依据
    → ⏸️ 暂停（PMO 给推荐 + 评分理由 + 候选清单 · 用户拍板）
```

### Step 0.4: 暂停点模板（决策类 · 按 P0-118-A 骨架强制 + P0-115 决策参考）

```
⏸️ 全景设计路径确认（PMO 探测后仍不确定）

📊 PMO 探测结果：
- 当前 Feature 子项目：{feature_subproject}
- 全仓库候选：{N} 个
- PMO 推荐：选项 {K}（💡 评分 {score}/100）

📚 候选清单（按推荐度排序）：

1. 💡 {abs_path_to_sitemap}（推荐 · 评分 {score}）
   - {评分维度命中说明 1}
   - {评分维度命中说明 2}
   - 推荐理由：{核心理由}

2. {abs_path_to_sitemap}（评分 {score}）
   - {评分维度说明}

3. 全部不对 · 我手动指定路径

4. 项目无全景 · 触发 panorama-design 创建首版骨架

请选择：1 / 2 / 3 / 4

📚 决策参考（点击查看）：
📄 {abs_path_to_candidate_1}/sitemap.md
📄 {abs_path_to_candidate_1}/preview/overview.html
📄 {abs_path_to_candidate_2}/sitemap.md
...

---
🔄 Teamwork 模式 | 流程：{Feature/敏捷需求} | 角色：PMO | 功能：{缩写}-F{编号}-{功能名} | 阶段：⏸️ 全景路径待确认 | 下一步：⏸️ 用户 4 选 1
📁 {worktree.path}/docs/features/{Feature}/
🌿 分支：{worktree.branch} → {merge_target} | worktree：{worktree.path}
```

### Step 0.5: 用户拍板后的处理

```
silent 自动认定 / 用户选 1-2：
  → panorama_path = {确认路径}
  → 进入 Process Contract Step 1 必做动作（用 panorama_path 替代原 design/sitemap.md 相对路径）

用户选 3（手动指定）：
  → 主对话承接用户输入的绝对路径
  → 校验文件存在 → 进 Step 1 ·  不存在 → ⚠️ 报错 + 重选

用户选 4（触发 panorama-design 创建首版）：
  → state.current_stage = "panorama_design"
  → 跳转到 panorama-design-stage.md 流程
```

### Step 0.6: 跨子项目场景

- panorama_path 所在子项目 ≠ 当前 Feature 子项目 → UI.md 顶部必须标注「全景宿主：{hosting_subproject}」（防 Designer 凭印象漏检）

---

## Process Contract

### 必做动作（顺序）

1. **按 PRD 需求设计当前 Feature 的 UI**
   - 布局、颜色、字体、间距、交互状态
   - **必须对齐全景基准**（v7.3.10+P0-123 跨子项目支持）：读取 Step 0 入口实例化确认的 `panorama_path/sitemap.md` + `panorama_path/preview/overview.html`，Feature UI 的风格/配色/布局/语言必须与全景一致
   - 跨子项目场景（panorama_path 不在当前 Feature 子项目）→ UI.md 顶部标注「全景宿主：{hosting_subproject}」
   - 项目无全景（Step 0 决策为「项目无全景」）→ 跳过对齐校验 · Concerns 记录
   - 覆盖正常/空/加载/错误 4 种状态

2. **产出 UI.md**（Feature 级设计**意图 / 追溯 / 审计**文档 · v7.3.10+P0-140 瘦身）
   - 🔴 **职责单源**：UI.md 只承载 panorama 对齐 / UI-AC-COVERAGE / Designer 自查 / 变更记录
   - 🔴 **不再写视觉描述**（布局 / 组件表 / 主色 / 字号 / 间距 / 响应式断点 / 状态设计文字 / 用户流程文字）—— 这些 HTML 是真相 · markdown 复述会 drift
   - 模板见 [templates/ui.md](../templates/ui.md)

3. **产出 Feature HTML 预览稿**（🔴 视觉真相的唯一载体 · v7.3.10+P0-140）
   - `{Feature}/preview/*.html`（每页面每状态一个文件）
   - Tailwind CSS
   - 🔴 HTML 区块加 `data-ac="AC-XX"` 锚定 · 与 UI-AC-COVERAGE 表对账
   - 🔴 布局 / 组件 / 配色 / 字号 / 间距 / 响应式 / 4 态 / 用户流程交互 **全部在 HTML 表达**

4. **产出验收标准覆盖声明**
   - 对照 PRD AC 逐条声明"UI 是否支撑"

5. **🔴 全景增量同步（谨慎）**
   - **判断**：本 Feature 是否引入新页面 / 修改现有页面结构 / 变更导航关系？
     - 是 → 执行增量合并（见下方规则）
     - 否 → 显式输出「⏭️ 本 Feature 无页面结构变更，全景无需同步」
   - **增量合并规则**（🔴 必须遵守）：
     - 读取现有 design/sitemap.md → 识别本 Feature 页面在全景中的位置（新增/修改/影响哪条导航）
     - 读取现有 design/preview/overview.html → 确认结构基线
     - **默认 append / modify-in-place**，禁止重写文件
     - **不删除任何现有页面/导航**（删除属于 Feature Planning 范畴，非 Feature 流程）
     - 修改全景时必须**标红注释**：在 sitemap.md 对应段加 `<!-- 🟡 {日期}: {FeatureID} 本次变更：{变更摘要} -->`
     - 修改全景时必须**结构对比**：执行报告列出全景变更前后的 diff（sitemap 的页面清单 + overview.html 的结构 DOM 差异摘要）
   - **产出**：更新后的 design/sitemap.md + design/preview/overview.html

### 过程硬规则

- 🔴 **角色规范必读且 cite**：必读 `roles/designer.md`，产出前 cite 要点
- 🔴 **对齐全景**：Feature UI 必须与全景风格/配色/布局/语言一致（不一致 → Concern，⏸️ 用户决策）· 下游：v7.3.10+P0-147 物化 — Designer 自查必跑 [`tools/diff-html-vs-panorama.py`](../tools/diff-html-vs-panorama.py)（panorama overview.html vs feature preview/*.html · DOM diff 出 extra colors / 字号 / layout tokens）· WARN 必修 / FAIL 阻断进入下个 Stage。实证 trigger：API-F048 case "页面框架还是和全景不对齐"
- 🔴 **全景增量不重写**：禁止用新版全景替换旧版；禁止删除现有页面或导航；只允许 append/modify-in-place
- 🔴 **全景变更显式标记**：任何对全景的修改必须在 sitemap.md 加标红注释 + 执行报告列出 diff
- 🔴 **HTML 预览必出**：Feature 每个页面/状态必须有 preview/*.html（Tailwind CSS）
- 🔴 **状态覆盖**：每页必须覆盖正常 / 空 / 加载 / 错误
- 🔴 **验收标准覆盖声明必出**：逐条对照 PRD AC
- 🔴 **结构性变更红线**：若本 Feature 涉及"删除现有页面" / "重构导航" / "修改核心业务流程状态机" → **停止本 Stage** → 返回 DONE_WITH_CONCERNS，建议用户走 Feature Planning 而非 Feature 流程（结构性变更不应在单 Feature 里做）
- 🔴 **Stage 完成前 git 干净** → 统一遵循 [rules/gate-checks.md § Stage 完成前 git 干净](../rules/gate-checks.md#-stage-完成前-git-干净v739-硬规则p0-集中化)（本 Stage commit message：`F{编号}: UI Design Stage - {简述}`；典型产物：UI.md / preview/*.html / 全景增量 sitemap/overview；HTML 预览稿是后续 Blueprint / Dev / Review 的基准）

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需内容 |
|---------|------|---------|
| `{Feature}/UI.md` | Markdown | **意图 / 追溯 / 审计**（panorama 对齐 + UI-AC-COVERAGE + Designer 自查 + 变更记录）· v7.3.10+P0-140 删除视觉描述段 |
| `{Feature}/preview/*.html` | HTML + Tailwind | **视觉真相**（布局 / 组件 / 配色 / 字号 / 间距 / 响应式 / 4 态 / 用户流程交互）· 每页面每状态一个文件 · `data-ac="AC-XX"` 锚定 |
| `{Feature}/UI-AC-COVERAGE.md`（或 UI.md 尾部）| Markdown 表 | 逐条 PRD AC → HTML 区块的追溯（人类阅读总览） |
| `design/sitemap.md` | Markdown | 🟡 增量更新（如有结构变更）+ 本次变更标红注释 |
| `design/preview/overview.html` | HTML | 🟡 增量更新（如有页面新增/修改） |

### 机器可校验条件

- [ ] UI.md 存在
- [ ] `{Feature}/preview/` 目录至少一个 HTML 文件
- [ ] HTML 引用 Tailwind CDN 或构建后的 CSS
- [ ] AC 覆盖声明覆盖 PRD 所有 AC
- [ ] 若本次涉及页面结构变更：design/sitemap.md 和 design/preview/overview.html 已同步更新（modified_time 晚于 Stage 开始时间）
- [ ] 若全景无变更：执行报告显式输出「⏭️ 全景无需同步」
- [ ] 🔴 **verify-panorama.py 物化校验通过**（v7.3.10+P0-132 出口前置）：
      `python3 {SKILL_ROOT}/tools/verify-panorama.py --feature {artifact_root} {--panorama-path X | --no-panorama} --stage-started-at {ISO}`
      校验 5 项：自查报告完整 / 跨子项目「全景宿主」标注 / panorama_path 有效 / sitemap mtime（涉及变更时）/ preview HTML 数量
      未通过 = 不进 ⏸️ 用户确认设计稿 · 按 stderr hint 补完 UI.md 自查段重跑

### Done 判据

- 所有产出文件存在
- PRD AC 全部有 UI 支撑声明
- 全景同步状态明确（已更新 / 无需更新，二选一）
- `state.json.stage_contracts.ui_design.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | Feature UI + 全景同步（或显式跳过）完成 | PMO ⏸️ 用户确认「设计批」（UI + 全景一起审）|
| ⚠️ DONE_WITH_CONCERNS | 与全景风格不一致 / PRD 描述不清 / 涉及结构性变更建议走 Planning | PMO ⏸️ 用户决策 |
| 💥 FAILED | 无法完成设计 | 返回错误 + 部分产出 |

---

## AI Plan 模式指引

📎 Execution Plan 4 行格式（含 Estimated）→ [SKILL.md](../SKILL.md#-ai-plan-模式规范v73-新增)。

本 Stage 默认 `subagent`（HTML 产出量大，全景增量合并需要读多文件；推荐 Opus）。典型偏离：小改动（1-2 页面 + 无全景变更）+ 用户需边讨论边调整 → `main-conversation`。

**Expected duration baseline（v7.3.4）**：
- Subagent：25-45 min（Feature UI + 全景增量判断/合并；全景无变更时压到 20-35 min）
- 主对话小改（1-2 页面 + 无全景变更）：10-18 min
- 原 Panorama 独立 Stage 的 15-25 min 增量耗时**并入本 Stage**，总耗时净减（少 1 次冷启动 + 少 1 次用户审查等待）

---

## 执行报告模板

```
📋 UI Design Stage 执行报告（F{编号}-{功能名}）
================================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── 执行方式：{主对话 / Subagent}
├── Feature 页面数：{N}
└── Feature 预览文件数：{M}

## Feature UI 产出
| 页面 | 状态覆盖（正常/空/加载/错误）| 与全景对齐说明 |
|------|-----------------------------|---------------|

## 验收标准覆盖声明
| AC | 覆盖状态 | 设计说明 |
|----|----------|----------|

## 🟡 全景同步状态（v7.3.4）
├── 是否需要同步：{是 / 否}
│
├── 否 → ⏭️ 本 Feature 无页面结构变更，全景无需同步
│
└── 是 → 增量同步结果：
    ├── 变更类型：新增页面 / 修改页面 / 变更导航 / 多项
    ├── sitemap.md 变更摘要：{新增/修改项清单}
    ├── overview.html 结构变更：{DOM 层面 diff 摘要}
    ├── 🟡 标红注释已添加：{行号}
    ├── 🔴 对全景的破坏性修改清单（如有）：
    │   └── {清单 + 理由；理论上本 Stage 不该有破坏性修改；若有则应降级为 DONE_WITH_CONCERNS}
    └── 全景修改谨慎度自检：
        ├── 未删除任何现有页面/导航：✅
        ├── 默认增量模式（未重写文件）：✅
        └── 与老板/产品方向一致（基于 PRD 解读）：✅

## 产出文件
├── 📁 UI.md
├── 📁 {Feature}/preview/*.html（{M} 个）
├── 📁 UI-AC-COVERAGE.md
├── 📁 design/sitemap.md（🟡 已更新 / ⏭️ 无需更新）
└── 📁 design/preview/overview.html（🟡 已更新 / ⏭️ 无需更新）

## Output Contract 校验
├── UI.md 存在：✅
├── Feature preview/ 非空：✅
├── 状态覆盖完整：✅
├── AC 全覆盖：✅
└── 全景同步状态明确：✅

## Concerns（如有）
- 涉及结构性变更（如删除现有页面）→ 建议用户走 Feature Planning 而非 Feature 流程
```
