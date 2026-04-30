# 文档模板已拆分

本文件的内容已拆分到 `templates/` 目录，按模板类型分别存放。

---

## 🔴 格式权威红线（v7.3.9+P0-7 新增）

```
├── 🔴 templates/ = 格式唯一真相源
│   任何 teamwork 产出文档（PRD / TC / TECH / state.json / review-log / dispatch 等）
│   的格式、字段、frontmatter schema、表头结构 —— 以 templates/ 下对应模板为准。
│
├── 🔴 禁止以 peer Feature 产物为格式基准
│   不得说"先参考一下最近一个 Feature 的 state.json / PRD 格式"。
│   peer Feature 的产物可能装的是老 schema、或被手动改过，抄过去 = 漂移放大。
│
├── 🟢 peer Feature 可作"内容参考"（允许）
│   ├── AC 怎么写得干净（内容层面）
│   ├── 类似业务的 TC 用例套路复用（业务逻辑层面）
│   ├── 架构决策的历史背景（ADR 追溯）
│   └── ⚠️ 但"怎么排字段、怎么写 frontmatter" 必须回 templates/ 对齐
│
├── 🔴 二者不一致时以 templates/ 为准
│   发现 peer Feature 与 templates/ 格式不一致 → templates/ 优先；
│   在 concerns 记录漂移（"F0xx 的 state.json 缺 ship 字段，建议归档时补齐"）。
│
└── 🔴 state.json 特别注意
    state.json schema 随版本演化（v7.3.2 / v7.3.9 / P0 均有增量字段）。
    peer Feature 的 state.json 很可能是老版，不能作 schema 基准。
    唯一权威 = templates/feature-state.json。
```

📎 该红线由 PMO / PM / RD 共同遵守，触发流程见 roles/{pmo,pm,rd}.md 对应「格式权威」条目。

---

## 快速导航

所有模板已按用途分类存放到 `templates/` 目录：

- **README.md** — 模板索引与快速导航
- **prd.md** — PRD 模板（v7.3.10+P0-47 合并为统一通用模板，含 YAML frontmatter AC 结构 + 按需必填标注）
- **tc.md** — 测试用例（BDD/Gherkin，含 YAML frontmatter tests[] 结构）
- **tech.md** — 技术方案设计
- **ui.md** — UI 设计文档
- **feature-state.json** — Feature 流转状态机（v7.3.2 起，替代原 status.md）
- **verify-ac.py** — AC↔test 覆盖校验脚本（标准实现）
- **state-patch.py** — state.json 增量更新工具（v7.3.10+P0-52，支持 set/append/merge-object/set-note/unset + schema 校验 + 原子写，节省 token 成本，详见 roles/pmo.md § state.json 更新优先用 patch 脚本）
- **roadmap.md** — 产品执行路线图
- **project.md** — 子项目业务总览
- **architecture.md** — 技术架构设计（含 database-schema 等子文档）
- **knowledge.md** — 项目本地知识库（v7.3.10+P0-22 收敛为 3 类：Gotchas / Conventions / Preferences，不再含架构决策——决策走 ADR）
- **teamwork-space.md** — 多子项目全景入口
- **bug-report.md** — Bug 排查与修复报告
- **config.md** — 项目配置（RESOURCES + .teamwork_localconfig + external/README）
- **dependency.md** — 跨子项目依赖请求追踪
- **e2e-registry.md** — E2E 回归测试中心（REGISTRY + ENVIRONMENT + REG cases）
- **pl-pm-feedback.md** — PL-PM 讨论反馈（PL-FEEDBACK + PM-RESPONSE）
- **adr.md** — ADR（Architecture Decision Record）单条决策记录模板（v7.3.10+P0-21 新增，opt-in 触发）
- **adr-index.md** — ADR 索引模板（每子项目一份 `docs/adr/INDEX.md`，v7.3.10+P0-21 新增）
- **retros-index.md** — 复盘索引模板（每子项目一份 `docs/retros/INDEX.md`，v7.3.10+P0-22 新增，与 KNOWLEDGE 收敛配套）

## 文件位置

所有模板文件位于当前 skill 仓库内的相对目录：`skills/teamwork/templates/`

如果是从本文件跳转，直接打开同级 `templates/` 目录即可，不依赖固定机器路径或会话路径。

## 使用说明

打开 `templates/README.md` 查看完整的模板索引和按流程的分类导航。

---

## 历史

- 原 TEMPLATES.md（~2977 行）已拆分为独立的模板文件
- 保留此文件作为重定向说明
- 模板内容完整保留，便于按需查找
