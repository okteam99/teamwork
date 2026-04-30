# 编号规则

> PMO 分配编号时查阅此文件。各编号在对应范围内独立递增。

## 功能编号

```
格式：{子项目缩写}-F{三位数字}
示例：AUTH-F001, WEB-F001, ADMIN-F002...

规则：
├── 缩写取自 teamwork_space.md 的子项目缩写字段
├── 编号在各子项目内独立递增
├── 目录名：{缩写}-F{编号}-{功能名}
├── 目录位置：{子项目路径}/docs/features/{缩写}-F{编号}-{功能名}/
├── 标准子目录结构（v7.3.2）：
│   ├── state.json                 Feature 状态 SSOT（v7.3.2 起替代 STATUS.md）
│   ├── review-log.jsonl           阶段流水审计
│   ├── PRD.md                     产品需求文档（YAML frontmatter 含 acceptance_criteria[]）
│   ├── TC.md                      测试用例文档（YAML frontmatter 含 tests[].covers_ac）
│   ├── tech.md                    技术方案
│   ├── UI.md                      UI 设计（如有）
│   ├── dispatch_log/              🔴 Subagent dispatch 文件目录（每次 dispatch 一个文件 + INDEX.md）
│   │   ├── INDEX.md
│   │   ├── 001-{subagent-id}.md
│   │   ├── 002-{subagent-id}.md
│   │   └── ...
│   ├── bugfix/                    关联 Bug 报告（可选）
│   └── optimization/              关联优化报告（可选）
└── 文档内引用时使用完整格式 {缩写}-F{编号}-{功能名}
```

## Dispatch 文件编号

```
格式：{三位数字序号}-{subagent-id}.md
示例：001-blueprint.md, 002-rd-develop.md, 003-arch-code-review.md, 004-codex-review.md, 005-qa-code-review.md...

规则：
├── 分配者：PMO（每次 Subagent dispatch 前生成 dispatch 文件时分配）
├── 编号在单个 Feature 的 dispatch_log/ 目录内递增，跨 Feature 不共享
├── 并行 dispatch（同 Stage 同批次）各占一个序号，Batch 字段标注同批次
├── 重新 dispatch（NEEDS_CONTEXT 补充后）→ 新序号 + 新文件，Previous dispatch 字段指向前次
├── subagent-id 是 dispatch 文件标签，沿用原有命名（见 agents/README.md §一 速查表）：
│   blueprint / rd-develop / arch-code-review / codex-review / qa-code-review
│   integration-test / api-e2e / designer / pm-prd / qa-plan 等
│   🔴 v7.3.10+P0-19-B 起角色任务规范已合并至 stages/*.md，subagent-id 仅作标签用
└── INDEX.md 固定位于 dispatch_log/ 根下，不参与序号
```

## Bug 编号

```
格式：BUG-{子项目缩写}-{功能编号后三位}-{三位数字}
示例：BUG-AUTH-001-001, BUG-WEB-001-002...

规则：
├── 关联到子项目和功能
├── 文件位置：{子项目路径}/docs/features/{缩写}-F{编号}/bugfix/BUG-{缩写}-{编号}-{序号}-{简述}.md
└── 独立 Bug（不关联功能）：BUG-{缩写}-000-{序号}
```

## 优化编号

```
格式：OPT-{缩写}-{功能编号后三位}-{三位数字}（如 OPT-AUTH-001-001）

规则：
├── 关联到子项目和功能
├── 文件位置：{docs_root}/features/{功能目录}/optimization/OPT-{编号}-{简述}.md
└── 全局优化：OPT-000-{序号}
```

## 决策编号

```
格式：DEC-{三位数字}
示例：DEC-001, DEC-002...

文件位置：docs/decisions/DEC-{编号}-{主题}.md（全局决策，不区分子项目）
```

## 变更编号

```
格式：CHG-{子项目缩写}-{三位数字}
示例：CHG-AUTH-001, CHG-WEB-001...

分配规则：
├── 分配者：PL（执行模式下输出 CHG 变更记录时分配）
├── 编号在各子项目内独立递增
├── 记录位置：变更记录文件 + 各 Feature state.json 的 change_history 段（如适用）
└── PMO 在 Feature Planning 级联时引用 CHG 编号追踪变更落地
```

## 业务关联编号（跨子项目 Feature 关联）

```
格式：BG-{三位数字}
示例：BG-001, BG-002...

分配规则：
├── 分配者：PMO（跨子项目需求拆分时自动分配）
├── 编号全局递增（跨所有子项目唯一）
├── 存储位置：`product-overview/changes/{change_id}.md` 文件名 + frontmatter `change_id` 字段（v7.3.10+P0-59 起单源 · 不再维护 teamwork_space.md 内的索引表）
├── 反向引用：各子项目 Feature 的 state.json 新增顶层字段 business_group: "BG-xxx"
├── 单子项目 Feature 不分配 BG（state.json 的 business_group 字段置 null）
├── INFRA/midplatform Feature 不默认建 BG——只有当其他子项目需要主动配合改动时才分配
├── PMO 分配时读取 teamwork_space.md 已有 BG 编号，取最大值 +1
└── 🔴 冲突防护：分配前必须重新读取 teamwork_space.md 获取最新编号（不可用缓存值）
```

## Stage 名词在 prose 中的标准形（v7.3.10+P0-57）

> 🔴 避免大小写漂移。Stage 名词在文档 prose 中**必须用标准大写形式**，code identifier（文件名 / state.json 字段 / enum 值）保留小写。

| 含义 | 标准形（prose 中用） | code identifier 形（文件名 / state.json / enum） | 例外说明 |
|------|---------------------|-----------------------------------------------|---------|
| 目标规划阶段 | **Goal-Plan**（首字母大写 + 连字符） | `goal-plan-stage.md` / `goal_plan_substeps_config` / `current_stage = "goal_plan"` | — |
| 蓝图阶段 | **Blueprint** | `blueprint-stage.md` / `blueprint_substeps_config` / `"blueprint"` | — |
| 评审阶段 | **Review** | `review-stage.md` / `review_substeps_config` / `"review"` | — |
| 开发 / 测试 / 上线 | **Dev** / **Test** / **Ship** | `dev-stage.md` / `test-stage.md` / `ship-stage.md` | — |
| 分诊 / 初始化 | **Triage** / **Init** | `triage-stage.md` / `init-stage.md` | — |

🔴 **硬规则**：
- 在 prose（说明文字 / 注释 / 标题）中提到 Stage 概念时，用**标准形**（如 `Goal-Plan Stage 入口实例化`）
- 在文件名引用、markdown 链接 URL、state.json 字段名、enum 值中保留 code identifier 形（小写 + 连字符或下划线）
- 历史文档（`docs/CHANGELOG.md` / `docs/OPTIMIZATION-PLAN.md`）记录历史事实，**不回溯改名**
- PMO 起草任何新 prose 时必须用标准形，避免再次出现 `goal-plan stage` / `Plan stage` 等漂移变体

