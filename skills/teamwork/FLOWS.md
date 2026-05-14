# FLOWS · v8.0

> 6 流程类型的 telos 与适用场景。
> 详细步骤由 `state.py prepare --user-input <原话>` 自动 emit · AI 不再读步骤 spec。

---

## 流程类型闭集(红线 R2)

| 流程 | 适用场景 | 默认暂停点 | 产出 |
|------|---------|----------|------|
| **Feature** | 完整功能(含 UI/架构/产品方向)| 3-5 | 代码 + 完整文档 + 测试 |
| **Bug** | 缺陷修复 | 3-4 | 修复 + BUG 报告 + 回归测试 |
| **Micro** | 零逻辑改动(文案/样式/资源/配置)| 2 | 代码直改 |
| **敏捷需求** | ≤5 文件 + 无 UI/架构变更 + 方案明确 | 2-3 | 代码 + 简化文档 + 测试 |
| **Feature Planning** | 从产品目标拆 ROADMAP | 1(仅摘要确认)| PROJECT.md + ROADMAP.md + sitemap.md(不出代码 · R6)|
| **问题排查** | 不出代码 · 仅定位根因 | 0-1 | 排查报告 + 后续 todo |

---

## Telos:每种流程在解决什么问题

### Feature
**完整 stage 链**:goal_plan → (ui_design) → blueprint → dev → review → test → (browser_e2e) → pm_acceptance → ship → completed

解决:**从需求到上线的完整闭环 + 多视角质量门禁**。
适用 Feature 触发场景:用户提"实现/开发/做一个 X 功能"。

### Bug
**精简 stage 链**(跳过 goal_plan / blueprint):dev → review → test → pm_acceptance → ship → completed

解决:**已知现象 + 已知期望 · 直接进入修复 · 不重复需求讨论**。
Ship Stage 缩简(标题 `[Bug] <简述> (BUG-<id>)`)。

### Micro
**最短 stage 链**:dev → ship → completed

解决:**零逻辑改动的最轻量通道 · 跳过所有质量门禁 stage**。
准入:改动类型在白名单(文案 / 样式 / 资源 / 配置常量 / 注释)+ 文件 ≤5。
超出白名单 → 升级敏捷需求 / Feature。
代码仍要走 Ship(R7 证据闭环)。

### 敏捷需求
**简化 stage 链**:goal_plan → blueprint_lite → dev → review → test → pm_acceptance → ship → completed

解决:**简单功能不需要完整 blueprint 的 overkill · 但保留多视角 review**。
准入:文件 ≤5 + 无 UI/架构变更 + 方案明确(用户无歧义)。
砍 TECH.md / TECH-REVIEW.md / External(blueprint_lite 只产 TC.md 简化版)。

### Feature Planning
**规划 stage 链**:goal_plan → panorama_design → completed

解决:**产品方向决策 · 拆 ROADMAP · 不出代码(R6)**。
PL(Product Lead)主导。Feature 启动前的"想清楚拆什么"。
完成后不自动进 Feature 流程 · 由用户选择启动哪个 Feature(R6)。

### 问题排查
**不进 stage 链**(类似 mode A query):
- 按问题描述 grep / Read 代码 + 日志
- 读 TROUBLESHOOTING.md(如存在)
- 给出根因分析
- ⏸️ 用户选:不动 / 转 Bug / 转 Feature

解决:**用户想理解一个现象 · 不一定要代码修复**。
state.py 不为问题排查启 stage 链 · 由 PMO 在主对话执行类似 mode A 的工作。

---

## 流程类型识别(自动 · 由 state.py prepare 执行)

`state.py triage --user-input "..."` 内部跑关键词匹配 + 优先级:
1. **Feature Planning**:`规划` / `拆 roadmap` / `做电商/SaaS`
2. **问题排查**:`排查` / `查 log` / `why X 慢/挂` / `调研`
3. **Bug**:`修复` / `bug` / `报错` / `500/502` / `挂了`
4. **Micro**:`换 logo` / `改文案` / `换图`
5. **敏捷需求**:`加个按钮` / `加导出` / `列表加列`
6. **Feature**:`实现` / `开发` / `做功能`(兜底)

识别结果落 `state.flow_type` · 后续 stage 链按此走。

---

## 关键约束(R6 红线物化)

- **Feature Planning · 只出文档**:`panorama_design-complete` 拒绝接受代码 artifact · 自动转 `completed` 而非 `dev`。
- **Micro · 涉代码仍要 Ship**:Micro 末尾必须 ship-* · 不能停在本地未 push(v7 P0-136 治本)。
- **敏捷需求 · 准入校验**:不能用 `blueprint_lite-start` 跳过完整 blueprint(`allowed_flow_types=["敏捷需求"]`)。

---

## v7 → v8 流程文档变化

| 范式 | FLOWS.md 行数 | 内容 |
|------|--------------|------|
| v7 | 876 行 | 每流程详细步骤 + 暂停点 + 角色 dispatch · AI 必读 cite |
| v8 | ~120 行 | 只讲 telos + 适用场景 · 步骤由 state.py prepare emit |

详细步骤渲染逻辑见 [`tools/_v8_init.py`](./tools/_v8_init.py) 的 `_render_flow_steps()`。

---

## 相关

- [SKILL.md](./SKILL.md) — 命令清单 + 5 mode 入口
- [RULES.md](./RULES.md) — 9 红线 rationale
- [stages/*.md](./stages/) — 各 stage Telos + Output Contract
- [tools/state.py](./tools/state.py) — 编排器入口
