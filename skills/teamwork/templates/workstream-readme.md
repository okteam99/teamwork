# Workstream（规划单元）

> 本目录存放本项目的 **Workstream（WS）** —— feature-planning 流程的产物。
> 每个 WS = 一块规划（一个能力 / 变更）→ 拆一组 feature 写进各子项目 ROADMAP。
> 🔴 本 README 是**静态向导**，不是看板 —— WS 状态汇总进 `teamwork-space.md § 进度统计`。

## 这里放什么

- `WS-{NN}-{短名}.md` —— 一个 Workstream（格式 / 状态机 / frontmatter 见 `~/.claude/skills/teamwork/templates/workstream.md`）

## 不放什么

- ❌ feature 的执行态 / 进度 → 在各子项目 `ROADMAP.md`（BL）+ Feature `state.json`
- ❌ 产品愿景 / 业务架构 / 执行线列表 → 在 `../{项目名}_业务架构与产品规划.md`
- ❌ 非开发工作（运营 / 推广 / BD）→ teamwork 不跟踪（执行线列表里点个名即可）

## 关键规则（速记 · 详 templates/workstream.md）

- **WS 怎么来**：进 feature-planning（PMO 切 Product Lead）才产出 · 不 ad-hoc 手搓。
- **承接执行线 1+**：每个 WS tag 业务架构「执行线列表」里的 1 条或多条 Line。
- **完成标准**：拆出的 feature **全部写入 ROADMAP**（原子）→ WS 转 `✅ 规划完成`。
- **lock 语义**：WS 未 `✅ 规划完成` 前禁止启动其子 Feature（防边规划边启动）。
- **进度统计** = N 个未完成 WS（📝/🔄/⏸️）+ 各子项目 ROADMAP 的 BL。
