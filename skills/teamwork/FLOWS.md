# FLOWS

> 流程闭集(红线 R2)与各自 telos。**判定权威 = [docs/prepare.md](./docs/prepare.md)**(关键词 + 复杂度 + 明确度)· 本文件只是视图。
> 🔴 v8.220-223:机器层 `flow_type ∈ {Feature, Bug}` + Feature 重量档 `preset ∈ {full, micro}`;「敏捷需求」「Micro」为 legacy 别名(→ Feature·full / Feature·micro)。

## 闭集

| 流程 | telos(解决什么) | 链 | 产出 |
|------|----------------|-----|------|
| **Feature**(preset=full) | 从需求到上线的完整闭环 + 多视角质量门禁 | goal → (ui_design) → (panorama_sync) → blueprint → dev → review → test → (browser_e2e) → pm_acceptance → ship | 代码 + 文档 + 测试 |
| **Feature**(preset=micro) | 零逻辑改动最轻通道(文案/样式/资源/配置常量/注释 白名单 · 超纲即 full · 准入单源 prepare.md §2.2)· **execute 零门禁自由执行**(自选 model/subagent/workflow/测试 · 无规范限制)· 用户验收在 ship1 MR diff(R7)· v8.250 | execute → ship | 代码直改 |
| **Bug** | 缺陷已指认 · **diagnose 先行**(根因 + 修复方案经用户确认才许修 · 防修偏)· review 单路 external(v8.270) | diagnose → dev → review → test → pm_acceptance → ship | 修复 + BUG 报告 + 回归测试 |
| **Feature Planning** | 产品方向 → 拆 ROADMAP · 不出代码(R6)· **不进状态机**(init reject · PMO 主对话执行 · 详 [docs/feature-planning.md](./docs/feature-planning.md)) | — | WS + ROADMAP + 全景 |
| **问题排查** | 理解现象 · 只定位根因 · **不进状态机**(mode A 深度版)· 🔴 排查先行律:根因未定的现象类输入一律先到这里 · 闭合再定流程(转 Bug 时结论直供 diagnose 复核不重查) | — | 排查报告 + 后续 todo |

## 关键约束

- 轻量不再靠独立类型:**动态 roster(role_value_criteria)+ clarity** 承担(v8.216/223)· preset=micro 是唯一结构性轻档(白名单准入 · 超出升 full)。
- micro 涉代码仍必 ship(不停在本地未 push · P0-136)。
- 存量 legacy(敏捷需求 / blueprint_lite / M-id)兼容走完 · 新 init 不再产。

## 相关

[SKILL.md](./SKILL.md)(入口 + 暂停点) · [docs/prepare.md](./docs/prepare.md)(判定权威) · [STAGES.md](./STAGES.md)(编排单源)
