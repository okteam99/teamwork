# Workstream 模板（WS）

> **位置**：`product-overview/workstream/WS-{NN}-{短名}.md`
> **产出者**：feature-planning 流程（PMO 切 Product Lead 引导/讨论 · 🔴 不在流程外 ad-hoc 手搓）
> **定位**：一块规划单元 —— 把一个能力/变更拆成**一组 feature**，写进各子项目 ROADMAP。
> **完成标准**：① 涉 UI 时 **全景初规 ✅**（本 WS 的页已在 `preview-project` · 非 UI 标 `N-A`）+ ② 这组 feature **全部写入 ROADMAP**（原子）→ WS 转 `✅ 规划完成`，执行态交给 ROADMAP/BL 跟踪。
> 详 [SKILL.md § teamwork 业务流程架构](../SKILL.md) · [docs/feature-planning.md](../docs/feature-planning.md)。
>
> 🔴 取代 v8.49 前的 `changes/` 变更单（CHG/BG）+ 执行手册的"拆 feature"职责。老项目 `changes/*.md` 向前兼容（保留可读）。

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
| `✅ 规划完成` | **全景初规 ✅(涉 UI)** + 所有 feature 已写入各子项目 ROADMAP（成 BL） | 不算（转 ROADMAP 执行态统计） |
| `🗑️ 废弃` | 用户决定不做 | 不算（只读归档） |

🔴 **lock 语义**（承旧 BG locked）：WS 未 `✅ 规划完成` 前**禁止启动其子 Feature** —— 防"边规划边启动"。
🔴 **全景初规子门禁**（涉 UI 时）：`ui_panorama` 必为 `✅`（本 WS 的页已在规划期的 `preview-project` 全景里出过 · 见 [feature-planning Step 5](../docs/feature-planning.md)）才能转 `✅ 规划完成`；非 UI WS 标 `N-A` 直接放行。**先有全景、再拆 WS** —— 防 feature 边界跟 UI 结构对不齐。

---

## 模板

```markdown
---
ws_id: WS-01
title: <一句话标题>
status: 📝 草稿        # 📝 草稿 / 🔄 讨论中 / ⏸️ 待确认 / ✅ 规划完成 / 🗑️ 废弃
ui_panorama: N-A       # 🔴 全景初规:✅(本 WS 的页已在 preview-project 全景)/ N-A(非 UI WS)· 涉 UI 必 ✅ 才能规划完成
ui_panorama_pages: []  # 本 WS 覆盖/新增的全景页(如 [offers-list, offer-detail])· 非 UI 留空(替代模糊的"哪一轮")
承接执行线:            # 🔴 1+ 条 · tag 业务架构「执行线列表」里的 Line(反查得"某线下有哪些 WS")
  - Line 1
  - Line 2
created_at: <ISO 8601 UTC>
planned_at: null       # 转 ✅ 规划完成（feature 全写入 ROADMAP）时填

affected_subprojects:  # 跨 0+ 子项目(单项目可空/填项目本身)
  - SVC-PLATFORM
  - PTR

features:              # 拆出的 feature · 写入各子项目 ROADMAP 后回填 bl
  - id: WS-01-S1
    target: SVC-PLATFORM         # 落哪个子项目 ROADMAP
    bl: null                     # 写入 ROADMAP 后回填 BL-NNN
    scope: "<这个 feature 做什么>"
    current_state: "<🔴 由实际代码调研得:已有什么脚手架/复用点 · 真缺口在哪 · 全新填 greenfield>"
    flow_type: feature           # feature / agile / bug / micro
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

launch_order:          # 按依赖拓扑 · 用户拍板后逐个 prepare + init-feature
  - WS-01-S1
  - WS-01-S2

risks:
  - id: R1
    description: "..."
    mitigation: "..."
    severity: high | medium | low
---

# WS-01：{title}

## 背景
{为什么做这块 · 业务/技术驱动 · 触发来源}

## 承接执行线
{服务哪条/哪几条执行线（业务价值视角）· 引用业务架构「执行线列表」的 Line}

## 怎么落实
{拆解思路 · 跨子项目怎么协调 · 关键设计取舍（细节落各 Feature PRD / ADR）}

## 拆出的 feature
### {feature_id}（→ {子项目} ROADMAP）
- **范围**：{做什么}
- **flow_type**：{feature / agile / bug / micro}
- **依赖**：{其他 WS-01-Sx}
- **核心 AC**（高层 · 详细 AC 在 Feature PRD）：① ... ② ...

## 跨子项目依赖
（Mermaid 或表 · 无跨项目可省）

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
- **WS → teamwork-space**：WS `✅ 规划完成` 后，teamwork-space 进度统计把它从"未完成 WS"移除（详 templates/teamwork-space.md § 进度统计）。
- **BL → F**：用户拍板某 BL 启动 → `prepare` + `init-feature` 分配 F-NNN（详 [docs/conventions.md § 4](../docs/conventions.md)）。

## 编号约定

- `WS-{两位数}`：项目独立递增（详 [docs/conventions.md § 8](../docs/conventions.md)）。
- 子 feature 临时 ID `WS-{NN}-S{n}`（写入 ROADMAP 前的占位）→ 写入后以 BL-NNN / F-NNN 为准。

## 设计要点

1. **WS = feature-planning 产物**：进 feature-planning（切 Product Lead）才产出 · 不 ad-hoc。
2. **职责单一**：WS 存"规划/拆解/跨项目编排"；feature 的执行态（stage/状态）在 ROADMAP/BL + state.json，不在 WS 复制。
3. **原子完成**：feature 全写入 ROADMAP 才算 `✅ 规划完成`（防写一半两边重复计数）。
4. **承接执行线 1+**：与子项目「承接执行线」多值一致 · 反查得能力级索引。
5. **拆解 grounded 实际代码**：`features[].current_state` 必由代码调研填（已做/真缺口）· 不凭假设/spec · decisive 前提（数据是否真入库 / 能力是否真生效）核验真实文件,不轻信 Explore/sub-agent 摘要（治本 AON category case 2026-05-29）。
6. **全景先于 WS**：涉 UI 的轮次先在 [feature-planning Step 5](../docs/feature-planning.md) 出 `preview-project` 全景初步规划（design system + 关键页），WS 才据全景 diff + 业务目标拆 feature（边界对齐 UI 结构）· `ui_panorama_pages` 记本 WS owns 哪几页（替代模糊的"基于哪轮全景"）。
