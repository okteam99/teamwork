# STATUS 模板

> 位置：`{docs_root}/features/{缩写}-F{编号}-{功能名}/STATUS.md`
> 🔴 PMO 每次阶段流转时必须更新此文件。

```markdown
# Feature 状态

| 字段 | 值 |
|------|-----|
| Feature | {缩写}-F{编号}-{功能名} |
| 当前阶段 | {阶段名称} |
| 当前角色 | {角色} |
| 最后更新 | {YYYY-MM-DD HH:mm} |
| 阻塞状态 | 无 / ⏳ {阻塞原因} |
| 业务关联 | - / BG-{三位数字}-{业务目标简述} |

## 流转约束（PMO 每次阶段变更时必须同步更新）

| 字段 | 值 |
|------|-----|
| 当前流程 | {Feature / Bug 处理 / 问题排查 / Feature Planning} |
| 当前阶段 | {规范阶段名} |
| 合法下一阶段 | {从转移表查出的唯一合法目标，多个用 / 分隔} |
| 禁止跳转到 | {当前阶段之后的所有非相邻阶段，明确列出} |
| 流转条件 | {触发条件简述} |
| 是否暂停点 | {是 → ⏸️ 等待用户确认 / 否 → 自动流转或角色执行} |
| 当前待确认项 | {暂停点时填写具体待确认内容，非暂停点填 无} |
| 回退路径 | {如有 🔁 回退可能则填写，否则填 无} |

> 📎 此段是 compact 后恢复的关键锚点。但 compact 恢复时必须跟 flow-transitions.md 交叉校验（见 gate-checks.md）。
> 🔴「禁止跳转到」是硬约束：PMO 流转时如果目标阶段出现在禁止列表中 → 必须阻塞并报错。
> 🔴「当前待确认项」是流程中断恢复的关键：即使对话被信息查询打断，PMO 可通过此字段恢复待确认上下文。
> 🔴 **禁止在 STATUS.md 中复写或改写流程链**。只能记录当前阶段的流转约束字段，不能自行给节点加 ⏸️/🚀 注释。流程链的权威定义在 flow-transitions.md，STATUS.md 复写会成为"衍生权威"导致循环论证。

## 阶段历史

| 阶段 | 进入时间 | 退出时间 | 备注 |
|------|----------|----------|------|
| PMO 初步分析 | {时间} | {时间} | |
| 🔗 Plan Stage | {时间} | {时间} | PM 写 PRD + PL-PM 讨论 + 技术评审 |
| PRD 待确认 | {时间} | {时间} | |
| 🔗 UI Design Stage | {时间} | {时间} | 无 UI 时跳过 |
| UI 待确认 | {时间} | {时间} | 无 UI 时跳过 |
| 🔗 Panorama Design Stage | {时间} | {时间} | 不涉及全景时跳过 |
| 全景待确认 | {时间} | {时间} | 不涉及全景时跳过 |
| 🔗 Blueprint Stage | {时间} | {时间} | QA TC + 技术方案 + 评审 |
| 方案待确认 | {时间} | {时间} | |
| 🔗 Dev Stage | {时间} | {时间} | RD TDD + 单测 |
| 🔗 Review Stage | {时间} | {时间} | 架构师 CR ∥ Codex ∥ QA 审查 |
| 🔗 Test Stage | {时间} | {时间} | 集成测试 ∥ API E2E |
| 🔗 Browser E2E Stage | {时间} | {时间} | 可选 |
| PM 验收 | {时间} | {时间} | |
| ✅ 已完成 | {时间} | - | |
```

**当前阶段的合法值**（对齐 STATUS-LINE.md「阶段与下一步对照表」，唯一权威来源）：
```
Feature 流程：
PMO 初步分析 → 🔗 Plan Stage → PRD 待确认 →
🔗 UI Design Stage → UI 待确认 → 🔗 Panorama Design Stage → 全景待确认 →
🔗 Blueprint Stage → 方案待确认 →
🔗 Dev Stage → 🔗 Review Stage → 🔗 Test Stage →
🔗 Browser E2E Stage → PM 验收 → ✅ 已完成

Micro 流程：Micro 变更说明 → 🤖 RD Subagent → 用户验收 → ✅ 已完成

特殊状态：⏳ 等待外部依赖 / RD Bug 排查
```

> 🔴 STATUS.md「当前阶段」使用上述阶段名（无 emoji 前缀）。PMO 阶段摘要中的「状态行显示」可带 emoji（如 🤖、⏸️），但 STATUS.md 字段值必须与此处一致。

**显示名映射**（状态行「阶段」字段的进行中显示 → 规范名对照）

> 🟢 v7.3：执行方式从"硬绑定"改为"AI Plan 模式自主决定"。显示名里的图标根据 state.json.planned_execution[stage].approach 动态渲染：
> - `approach: main-conversation` → 💬 图标
> - `approach: subagent` → 🤖 图标
> - `approach: hybrid` → 💬🤖 图标

| 规范名 | 状态行进行中显示 | 默认推荐 approach | 备注 |
|--------|-----------------|------------------|------|
| **Feature 流程（8 Stage）** | | | |
| PMO 初步分析 | PMO 分析中 | — | |
| 🔗 Plan Stage | 💬/🤖 Plan Stage 执行中（PRD+讨论+评审） | main-conversation | 多视角 prompt 切换 |
| PRD 待确认 | ⏸️ PRD 待确认 | — | |
| 🔗 UI Design Stage | 🤖/💬 UI Design 执行中 | subagent | 无 UI 时跳过 |
| UI 待确认 | ⏸️ UI 待确认 | — | 无 UI 时跳过 |
| 🔗 Panorama Design Stage | 🤖/💬 全景设计更新中 | subagent | 不涉及全景时跳过 |
| 全景待确认 | ⏸️ 全景待确认 | — | 不涉及全景时跳过 |
| 🔗 Blueprint Stage | 💬/🤖 Blueprint 执行中（TC+TECH+评审） | main-conversation | 多视角 prompt 切换 |
| 方案待确认 | ⏸️ 方案待确认 | — | |
| 🔗 Dev Stage | 💬/🤖 Dev Stage 执行中（按方案实现+TDD+单测） | AI 自主 | 按规模/复杂度决定 |
| 🔗 Review Stage | 💬🤖 Review Stage 执行中（架构师CR∥Codex∥QA审查） | hybrid | 架构师主对话 + QA/Codex Subagent |
| 🔗 Test Stage | 💬🤖 Test Stage 执行中（集成∥E2E） | hybrid | 环境主对话 + API E2E Subagent |
| 🔗 Browser E2E Stage | 💬/🤖 Browser E2E 执行中 | main-conversation | 半自动（可选） |
| PM 验收 | 💬 PM 验收中 | main-conversation | 人交互 |
| ✅ 已完成 | ✅ 已完成 | — | 终态 |
| **敏捷需求流程差异阶段** | | | |
| 精简 PRD 编写 | 💬 PRD 编写中（精简版） | main-conversation | PM 直接写精简 PRD |
| **Micro 流程（v7.3 放宽）** | | | |
| Micro 变更说明 | 💬 Micro 变更说明中 | main-conversation | PMO 起草说明 |
| 执行改动 | 💬 PMO 直接改动中 | main-conversation | v7.3：无需 Plan / 无需 Subagent |
| 用户验收（Micro） | ⏸️ 用户验收中 | — | |
| **Bug 处理流程** | | |
| RD Bug 排查 | Bug 排查中 | |
| PMO Bug 判断 | PMO 流程判断 | |
| QA 补充用例 | QA 补充用例中 | |
| RD Bug 修复 | Bug 修复中 | |
| RD Bug 自查 | Bug 自查中 | |
| QA Bug 验证 | QA 验证中 | |
| PM 文档同步 | 文档同步检查中 | |
| PMO Bug 总结 | PMO 总结中 | |
| **问题排查流程** | | |
| 问题排查梳理 | 问题排查中 | |
| 排查待确认 | ⏸️ 排查待确认 | |
| **Feature Planning** | | |
| PM Roadmap 编写 | Roadmap 编写中 | |
| Roadmap 待确认 | ⏸️ Roadmap 待确认 | |
| **Workspace Planning** | | |
| 🌐 Workspace 架构讨论 | 架构讨论中 | |
| 🌐 teamwork_space.md 待确认 | ⏸️ teamwork_space.md 待确认 | |
| 🌐 子项目 Planning 中 | 子项目 [缩写] Planning | |
| 🌐 Workspace Planning 收尾 | ⏸️ 最终确认 | |
| **PL 模式** | | |
| PL 引导模式 | PL 引导（草案迭代中） | |
| PL 讨论模式 | PL 讨论中 | |
| PL 结论待确认 | ⏸️ PL 结论待确认 | |
| PL 执行模式 | PL 变更评估中 | |
| CHG 待确认 | ⏸️ CHG 待确认 | |
| **通用特殊状态** | | |
| ⏳ 等待外部依赖 | ⏳ 等待外部依赖（DEP-XXX） | 适用所有流程 |
| 外部依赖已就绪 | 外部依赖已就绪 | |

> 📎 未列出的阶段，显示名 = 规范名 + "中"后缀（如 "PM 验收" → "PM 验收中"）。

**PMO 更新规则**：
```
├── 每次 PMO 阶段摘要时 → 更新 STATUS.md 的「当前阶段」「当前角色」「最后更新」
├── 阶段流转时 → 在「阶段历史」表追加/更新对应行的退出时间
├── Feature 完成时 → 当前阶段设为「✅ 已完成」
└── 🔴 STATUS.md 是 Feature 状态的 Single Source of Truth
```
