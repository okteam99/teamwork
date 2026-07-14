# Workstream 模板（WS）

> **位置**：`product-overview/workstream/WS-{NN}-{短名}.md`
> **产出者**：feature-planning 流程（PMO 切 Product Lead 引导/讨论 · 🔴 不在流程外 ad-hoc 手搓）
> **定位**：一块规划单元 —— 把一个能力/变更拆成**一组 feature**，写进各子项目 ROADMAP。
> **完成标准**：① 涉 UI 时 **全景初规 ✅ 且 `ui_panorama_confirmed` 已填**（页已在 `preview-project` **且用户看预览 URL 确认过** · 非 UI 标 `N-A`）+ ② 这组 feature **全部写入 ROADMAP**（原子）+ ③ **执行顺序与并行建议**已给（§执行顺序与并行建议 · 波次 + 哪些可并行）→ WS 转 `✅ 规划完成`，执行态交给 ROADMAP/BL 跟踪。
> 详 [SKILL.md § teamwork 业务流程架构](../SKILL.md) · [docs/feature-planning.md](../docs/feature-planning.md)。
>
> 🔴 取代旧的 `changes/` 变更单（CHG/BG）+ 执行手册的"拆 feature"职责。老项目 `changes/*.md` 向前兼容（保留可读）。

---

## 状态生命周期

```
📝 草稿 ──→ 🔄 讨论中 ──→ ⏸️ 待确认 ──→ ✅ 规划完成 ──→（执行交 ROADMAP）
              ↓                              ↑
           🗑️ 废弃                  feature 全部写入 ROADMAP（原子）
```

| 状态 | 含义 | 进度统计 |
|------|------|---------|
| `📝 草稿` / `🔄 讨论中` / `⏸️ 待确认` | 规划中（拆解未定 / 议题未决 / 待用户拍板） | **算"未完成 WS"** |
| `✅ 规划完成` | **全景初规 ✅ + 已用户确认(涉 UI · `ui_panorama_confirmed` 已填)** + 所有 feature 已写入各子项目 ROADMAP（成 BL） | 不算（转 ROADMAP 执行态统计） |
| `🗑️ 废弃` | 用户决定不做 | 不算（只读归档） |

🔴 **lock 语义**（承旧 BG locked）：WS 未 `✅ 规划完成` 前**禁止启动其子 Feature** —— 防"边规划边启动"。
🔴 **全景初规子门禁**（涉 UI 时）：`ui_panorama` 必为 `✅`（本 WS 的页已在规划期的 `preview-project` 全景里出过）**且 `ui_panorama_confirmed` 已填**（用户在 [feature-planning Step 5](../docs/feature-planning.md) 看**可访问预览 URL** 确认过全景设计）才能转 `✅ 规划完成`；非 UI WS 标 `N-A` 直接放行。🔴 **用户没确认过全景 = 不算规划完成** —— 光「页在 preview-project」是 AI 自标,得用户拍板。**先有全景、再拆 WS** —— 防 feature 边界跟 UI 结构对不齐。

🔴 **WS 状态 ≠ feature 进度**（两个维度别混）：本节 `📝→✅ 规划完成` 是 **WS 规划生命周期**（拆解定没定）；feature 的**执行进度**（建到哪了）是另一维，看 §feature 总览（`ws-progress` 自各 ROADMAP「状态」列**派生**，规划完成、feature 进 ROADMAP 后才有数据）。

---

## 模板

```markdown
<!-- TEAMWORK-MACHINE · WS 机读/元数据契约 · 勿删外层注释包裹 · 标准 2 空格缩进
ws_id: WS-01
title: <一句话标题>
status: 📝 草稿        # 📝 草稿 / 🔄 讨论中 / ⏸️ 待确认 / ✅ 规划完成 / 🗑️ 废弃
ui_panorama: N-A       # 🔴 全景初规:✅(本 WS 的页已在 preview-project 全景)/ N-A(非 UI WS)
ui_panorama_confirmed: N-A  # 🔴 全景设计**已用户确认**:<ISO>(feature-planning Step 5 · 用户看预览 URL 拍板)/ N-A(非 UI)· 涉 UI 必填才能规划完成(光 ui_panorama:✅「页在全景」不够 · 得用户确认过)
ui_panorama_pages: []  # 本 WS 覆盖/新增的全景页(如 [offers-list, offer-detail])· 非 UI 留空(替代模糊的"哪一轮")
承接执行线:            # 🔴 1+ 条 · tag 业务架构「执行线列表」里的 Line(反查得"某线下有哪些 WS")
  - Line 1
  - Line 2
created_at: <ISO 8601 UTC>
planned_at: null       # 转 ✅ 规划完成（feature 全写入 ROADMAP）时填

affected_subprojects:  # 跨 0+ 子项目(单项目可空/填项目本身)
  - SVC-PLATFORM
  - PTR

features:              # 拆出的 feature · 写入各子项目 ROADMAP 后回填 bl · 🔴 落盘后合并/砍件不重排 id(被并件留 `→ 已并入 Sx` · 缺号不补 · v8.240)
  - id: WS-01-S1
    target: SVC-PLATFORM         # ROADMAP 归属(单选);实现可跨子项目 —— 拆分按交付内聚,不按子项目切(v8.240)
    bl: null                     # 写入 ROADMAP 后回填 BL-NNN
    scope: "<这个 feature 做什么>"
    current_state: "<🔴 由实际代码调研得:已有什么脚手架/复用点 · 真缺口在哪 · **附来源文件路径** · 全新填 greenfield(v8.239 ws-lint 抓占位=调研浅)>"
    flow_type: Feature           # Feature / Bug(v8.222 闭集 · 轻量走 preset: micro 不是独立类型)
    dependencies: []             # 依赖的其他 WS-01-Sx
    status: pending              # pending / planned(已写入 ROADMAP) / 废弃
  - id: WS-01-S2
    target: PTR
    bl: null
    scope: "..."
    current_state: "..."
    flow_type: feature
    dependencies: [WS-01-S1]
    status: pending

launch_order:          # 线性回退顺序(按依赖拓扑 · 不并行时逐个起)· 并行视图见 execution_waves + body
  - WS-01-S1
  - WS-01-S2

execution_waves:       # 🔴 并行执行建议 · 同 wave 内互不依赖 → 可并行(各自 worktree)· 跨 wave 串行
  - wave: 1
    parallel: [WS-01-S1, WS-01-S3]   # 同时可起(互不依赖 · 不同改面)
    after: []
  - wave: 2
    parallel: [WS-01-S2]
    after: [WS-01-S1]                # 等 S1 的 API 落地

risks:
  - id: R1
    description: "..."
    mitigation: "..."
    severity: high | medium | low
-->

# WS-01：{title}

> **状态** {status} · **承接** {见 §承接执行线} · **进度** 见下方 §feature 总览（`ws-progress` 自各 ROADMAP 汇总）

## 背景
{为什么做这块 · 业务/技术驱动 · 触发来源}

## 承接执行线
{服务哪条/哪几条执行线（业务价值视角）· 引用业务架构「执行线列表」的 Line}

## 怎么落实
{拆解思路 · 跨子项目怎么协调 · 关键设计取舍（细节落各 Feature PRD / ADR）}

## feature 总览（进度 · 工具汇总）
> 🔧 `state.py ws-progress --ws WS-NN --write` 自刷 · 🔴 勿手改 · 规划完成后刷新即出。**名册驱动**：以 frontmatter `features[]` 为权威名册（声明的 feature 全列出 · 含跨子项目/前置如 SDK-Fxxx），状态自各 ROADMAP 按 BL 匹配（含无「关联 WS」列的 legacy 表）· 匹配不到标「未匹配」不漏报。

<!-- WS-PROGRESS:START · 工具生成(state.py ws-progress) · 名册驱动 · 自各 ROADMAP 匹配状态 · 勿手改 -->
进度 暂无数据（feature 尚未写入 ROADMAP · 规划完成后 ws-progress 刷新自动出现）
<!-- WS-PROGRESS:END -->

## feature 依赖关系图（工具汇总）
> 🔧 同 `ws-progress --write` 自 frontmatter `features[].dependencies` 派生 Mermaid DAG · 🔴 勿手改（依赖语义改 features[] · 非改图）。节点 = feature 短名 · 边 = 依赖 → 被依赖。

<!-- WS-DAG:START · 工具生成(state.py ws-progress) · 自 features[].dependencies 派生 · 勿手改 -->
（规划完成后 ws-progress --write 刷新即出）
<!-- WS-DAG:END -->

## 拆出的 feature（拆解明细 · 规划态 · 人维护）
> 每个 feature 的范围/依赖/高层 AC（详细 AC 在各 Feature PRD）· 写入 ROADMAP 后**执行进度看上方 §feature 总览**，此处不复制状态（防双源 stale）。
### {feature_id}（→ {子项目} ROADMAP · BL 待回填）
- **范围**：{做什么}
- **flow_type**：{feature / agile / bug / micro}
- **依赖**：{其他 WS-01-Sx}
- **核心 AC**（高层 · 详细 AC 在 Feature PRD）：① ... ② ...

## 跨子项目依赖
（Mermaid 或表 · 无跨项目可省）

## 执行顺序与并行建议
> 🔴 **规划完成必给**：基于 `features[].dependencies` 算波次（结构化见 frontmatter `execution_waves`）· 同波互不依赖 → **可并行**（各自 worktree + 分支 + 状态机同时跑）· 跨波按依赖串行。WS 必 `✅ 规划完成` 后才可启动任一 feature。

| Wave | 可并行 feature | 前置 | 约束 / 串行原因 |
|------|---------------|------|----------------|
| 1 | WS-01-S1 · WS-01-S3 | — | 互不依赖 · 同时起 2 个 worktree |
| 2 | WS-01-S2 | S1（用其 API） | 等 S1 API 落地 |

🔴 **DAG 之外的额外串行约束**（judgment · `dependencies` 字段不含 · 拆完必想）：
- **同改面**：动同一组文件/模块的 feature 即便逻辑独立也建议**串行** —— 防并行 worktree merge 冲突（如多 feature 改同一 panorama 页 / 同一 migration 目录）。
- **跨子项目方向**：provider（后端 API / midplatform）先于 consumer（前端 / 调用方）· 即便无代码 import 依赖（见 §跨子项目依赖）。
- **带宽**：一次并行起的数量按 review / 测试 / 注意力带宽控（建议 ≤ 3）· 不为并行而并行。

> 与 ROADMAP Wave 的关系：本表是**跨子项目 / 跨 feature** 的编排权威；各子项目 `ROADMAP.md` 的 Wave 是落到该子项目的本地视图（详 [roadmap.md](./roadmap.md)）。

## 风险与缓解
| ID | 描述 | 严重度 | 缓解 |
|----|------|--------|------|
| R1 | ... | high | ... |

## 变更日志
| 时间 | 事件 |
|------|------|
| {ISO} | 创建（status=📝 草稿） |
```

---

## 与下游的关系

- **WS → BL**：WS 拆出的每个 feature 写进 `target` 子项目的 `ROADMAP.md` 成一行 BL；ROADMAP「关联 WS」列回指本 `ws_id`，`features[].bl` 回填 BL-NNN。
- **WS → teamwork-space**：WS `✅ 规划完成` 后，teamwork-space 把它从"未完成 WS"移除（详 templates/teamwork-space.md § 规划状态）。
- **BL → F**：用户拍板某 BL 启动 → `prepare` + `init-feature` 分配 F-NNN（详 [docs/conventions.md § 4](../docs/conventions.md)）。

## 编号约定

- `WS-{两位数}`：项目独立递增（详 [docs/conventions.md § 8](../docs/conventions.md)）。
- 子 feature 临时 ID `WS-{NN}-S{n}`（写入 ROADMAP 前的占位）→ 写入后以 BL-NNN / F-NNN 为准。

## 设计要点

1. **WS = feature-planning 产物**：进 feature-planning（切 Product Lead）才产出 · 不 ad-hoc。
2. **职责单一**：WS 存"规划/拆解/跨项目编排"；feature 的执行态（stage/状态）在 ROADMAP/BL + state.json，**不在 WS 手抄** —— WS 的 §feature 总览 是 `ws-progress` 自 ROADMAP **确定性派生的只读视图**（单源派生 · 防 stale 双源）。
3. **原子完成**：feature 全写入 ROADMAP 才算 `✅ 规划完成`（防写一半两边重复计数）。
4. **承接执行线 1+**：与子项目「承接执行线」多值一致 · 反查得能力级索引。
5. **拆解 grounded 实际代码**：`features[].current_state` 必由代码调研填（已做/真缺口）· 不凭假设/spec · decisive 前提（数据是否真入库 / 能力是否真生效）核验真实文件,不轻信 Explore/sub-agent 摘要。
6. **全景先于 WS**：涉 UI 的轮次先在 [feature-planning Step 5](../docs/feature-planning.md) 出 `preview-project` 全景初步规划（design system + 关键页），WS 才据全景 diff + 业务目标拆 feature（边界对齐 UI 结构）· `ui_panorama_pages` 记本 WS owns 哪几页（替代模糊的"基于哪轮全景"）。
7. **规划完成给并行建议**：拆完 feature 必产出 §执行顺序与并行建议（波次 + 哪些可并行 + 同改面 / 跨子项目方向 / 带宽 的额外串行约束）+ frontmatter `execution_waves`（结构化）—— 让用户拿到 WS 就知道"先起哪几个、能同时开几个 worktree"，不必自己重排依赖。
8. **进度可见但不双源**：用户翻一个 WS 就该一眼看到"这条线建到哪了"，但执行态单一源在 ROADMAP「状态」列 → `state.py ws-progress --ws WS-NN --write` **名册驱动**汇总进 `WS-PROGRESS` 标记区（rollup + 总览表）+ 自 `features[].dependencies` 派生 Mermaid DAG 进 `WS-DAG` 标记区。🔴 **名册驱动**：以 frontmatter `features[]` 为权威名册（声明的 feature 全列出 · 含**跨子项目前置**如 SDK-Fxxx），状态自各 ROADMAP 按 BL 匹配（解析器吃无「关联 WS」列的 **legacy 表**）· 匹配不到标「未匹配」不漏报 —— 纯按「关联 WS」扫会漏掉登记在 legacy ROADMAP 的跨子项目 feature。
9. **元数据隐藏**：机读/元数据契约包进 `<!-- TEAMWORK-MACHINE ... -->` 注释（同 PRD 的机读块）—— 在 TermPro/Zed 等"显示 frontmatter"的渲染器里**不当正文渲染成一面 YAML 墙** · body 章节是唯一可见权威。🔴 注释内**严禁出现字面 `-->`**（会提前闭合注释）。
