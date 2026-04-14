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

> 📎 此段是 compact 后恢复的关键锚点。PMO 读取 STATUS.md 即可获得当前阶段的完整流转信息，无需重读 RULES.md 转移表。
> 🔴「禁止跳转到」是硬约束：PMO 流转时如果目标阶段出现在禁止列表中 → 必须阻塞并报错。
> 🔴「当前待确认项」是流程中断恢复的关键：即使对话被信息查询打断，PMO 可通过此字段恢复待确认上下文。

## 阶段历史

| 阶段 | 进入时间 | 退出时间 | 备注 |
|------|----------|----------|------|
| PM 编写 PRD | {时间} | {时间} | |
| PL-PM Teams 讨论 | {时间} | {时间} | |
| PRD 评审 | {时间} | {时间} | |
| PRD 待确认 | {时间} | {时间} | |
| Designer 设计 | {时间} | {时间} | 无 UI 时跳过 |
| UI 待确认 | {时间} | {时间} | 无 UI 时跳过 |
| QA Test Plan | {时间} | {时间} | |
| QA Write Cases | {时间} | {时间} | BDD + API E2E + Browser E2E |
| TC 评审 | {时间} | {时间} | |
| RD 技术方案 | {时间} | {时间} | |
| 架构师 Review | {时间} | {时间} | |
| 技术方案待确认 | {时间} | {时间} | |
| RD 实现计划 | {时间} | {时间} | |
| 🔗 Dev Chain | {时间} | {时间} | 内含 RD 开发+自查 → 架构师 CR → 修复循环 |
| UI 还原验收 | {时间} | {时间} | 无 UI 时跳过 |
| Codex Review | {时间} | {时间} | 外部独立代码审查（Codex CLI） |
| 🔗 Verify Chain | {时间} | {时间} | 内含 QA 审查 → 单元测试 → 集成测试 → API E2E |
| QA Browser E2E | {时间} | {时间} | 可选，PMO 建议+用户确认；TC.md 无浏览器行为时跳过 |
| PM 验收 | {时间} | {时间} | |
| ✅ 已完成 | {时间} | - | |
```

**当前阶段的合法值**（对齐 SKILL.md「阶段与下一步对照表」的「阶段」列，唯一权威来源）：
```
PM 编写 PRD → PL-PM Teams 讨论 → PRD 评审 → PRD 待确认 →
Designer 设计 → UI 待确认 →
QA Test Plan → QA Write Cases → TC 评审 → RD 技术方案 → 架构师 Review →
技术方案待确认 → RD 实现计划 → 🔗 Dev Chain →
UI 还原验收 → Codex Review → 🔗 Verify Chain → QA Browser E2E →
PM 验收 → ✅ 已完成

Micro 流程：Micro 变更说明 → 🤖 RD Subagent → 用户验收 → ✅ 已完成

特殊状态：⏳ 等待外部依赖 / RD Bug 排查
```

> 🔴 STATUS.md「当前阶段」使用上述阶段名（无 emoji 前缀）。PMO 阶段摘要中的「状态行显示」可带 emoji（如 🤖、⏸️），但 STATUS.md 字段值必须与此处一致。

**显示名映射**（状态行「阶段」字段的进行中显示 → 规范名对照）：

| 规范名 | 状态行进行中显示 | 说明 |
|--------|-----------------|------|
| PM 编写 PRD | PRD 编写中 | |
| PL-PM Teams 讨论 | 🤖 PL-PM 讨论中（Teams） | |
| RD 技术方案 | 技术方案中 | |
| 技术方案待确认 | ⏸️ 方案待确认 | 简写 |
| RD 开发+自查 | 🤖 Subagent 执行中 | 同其他 Subagent 阶段 |
| QA 集成测试前置检查 | 环境准备中 | |
| RD Bug 排查 | Bug 排查中 | Bug 处理流程 |
| PMO Bug 判断 | PMO 流程判断 | Bug 处理流程 |
| QA 补充用例 | QA 补充用例中 | Bug 处理流程 |
| RD Bug 修复 | Bug 修复中 | Bug 处理流程 |
| RD Bug 自查 | Bug 自查中 | Bug 处理流程 |
| QA Bug 验证 | QA 验证中 | Bug 处理流程 |
| PM 文档同步 | 文档同步检查中 | Bug 处理流程 |
| PMO Bug 总结 | PMO 总结中 | Bug 处理流程 |
| 问题排查梳理 | 问题排查中 | 问题排查流程 |
| 排查待确认 | ⏸️ 排查待确认 | 问题排查流程 |
| PM Roadmap 编写 | Roadmap 编写中 | Feature Planning |
| Roadmap 待确认 | ⏸️ Roadmap 待确认 | Feature Planning |
| 🌐 Workspace 架构讨论 | 架构讨论中 | Workspace Planning |
| 🌐 teamwork_space.md 待确认 | ⏸️ teamwork_space.md 待确认 | Workspace Planning |
| 🌐 子项目 Planning 中 | 子项目 [缩写] Planning | Workspace Planning |
| 🌐 Workspace Planning 收尾 | ⏸️ 最终确认 | Workspace Planning |
| PL 引导模式 | PL 引导（草案迭代中） | PL 模式 |
| PL 讨论模式 | PL 讨论中 | PL 模式 |
| PL 结论待确认 | ⏸️ PL 结论待确认 | PL 模式 |
| PL 执行模式 | PL 变更评估中 | PL 模式 |
| CHG 待确认 | ⏸️ CHG 待确认 | PL 模式 |
| ⏳ 等待外部依赖 | ⏳ 等待外部依赖（DEP-XXX） | 通用 |

> 📎 未列出的阶段，显示名 = 规范名 + "中"后缀（如 "PM 验收" → "PM 验收中"）。

**PMO 更新规则**：
```
├── 每次 PMO 阶段摘要时 → 更新 STATUS.md 的「当前阶段」「当前角色」「最后更新」
├── 阶段流转时 → 在「阶段历史」表追加/更新对应行的退出时间
├── Feature 完成时 → 当前阶段设为「✅ 已完成」
└── 🔴 STATUS.md 是 Feature 状态的 Single Source of Truth
```
