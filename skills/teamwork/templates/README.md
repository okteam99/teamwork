# 文档模板索引

本目录是 Teamwork 所有产出文档的**格式唯一真相源**（红线详 [TEMPLATES.md](../TEMPLATES.md)）。
任何 teamwork 产出的格式 / 字段 / frontmatter schema / 表头结构，以本目录对应模板为准；禁止以 peer Feature 产物为格式基准。

> 无手写模板的两类机读产物：`state.json`（`tools/state.py` 单源维护）与 Feature 内 `review-log.jsonl`（state.py 各 stage 完成时自动追加）——**工具单源 · 不在本目录**。
> 另：TECH-REVIEW.md 与 REVIEW.md / REVIEW-arch / REVIEW-qa 的 schema 单源在 stages/（blueprint-stage.md / review-stage.md）· 无独立模板。

## 执行链产物（Feature 状态机内各 stage 产出）

| 文件 | 用途 | 主要消费方 / 时机 |
|------|------|------------------|
| [prd.md](./prd.md) | PRD（`TEAMWORK-MACHINE` 机读块含 `acceptance_criteria[]`） | goal stage PM 起草 · verify-ac / 评审 / dev 消费 |
| [tc.md](./tc.md) | 测试用例（frontmatter `tests[].covers_ac` 反查 AC） | blueprint stage QA 起草 · verify-ac 校验覆盖 |
| [tech.md](./tech.md) | 技术方案设计 | blueprint stage RD 起草 · 架构师 Tech Review |
| [ui.md](./ui.md) | UI 意图 / 追溯 / 审计（视觉真相在 preview 产物） | ui_design stage Designer 产出 |
| [bug-report.md](./bug-report.md) | Bug 排查修复报告（frontmatter 承担 Bug 流程机读状态） | diagnose stage 产出根因+方案 · dev stage 补 fix+回归 |
| [test-report.md](./test-report.md) | 测试报告（`test-complete` 物化 evidence） | test stage QA 产出 |
| [browser-test-report.md](./browser-test-report.md) | 浏览器 E2E 测试报告 | browser_e2e stage QA+Designer 产出 |
| [pm-note.md](./pm-note.md) | PM 验收说明（可选 · rejected 时 finding 必填） | pm_acceptance stage PM 产出 |
| [yolo-preflight.md](./yolo-preflight.md) | YOLO 预研 + 核心决策确认（含未填哨兵行） | `init-feature --yolo` 物化校验存在且已填 |

## 项目骨架（bootstrap 自动建 / 项目级长期文档）

| 文件 | 用途 | 主要消费方 / 时机 |
|------|------|------------------|
| [teamwork-space.md](./teamwork-space.md) | 知识地图根实例化骨架（N≥1 统一模型 · 单项目也有） | bootstrap 缺失时自动建 · 每 session 必读入口 · 维护规则见 [docs/teamwork-space-guide.md](../docs/teamwork-space-guide.md) |
| [architecture-workspace.md](./architecture-workspace.md) | `project-specs/ARCHITECTURE.md`（workspace 级：子项目拓扑+依赖+目录） | bootstrap 建空骨架 · 结构变更时 PM 更新 |
| [architecture.md](./architecture.md) | 单子项目内部技术架构（含 database-schema） | 子项目初始化时创建 · RD/架构师维护 |
| [project.md](./project.md) | 子项目业务总览（业务语言 · 非技术细节） | 子项目初始化 / Feature Planning 后更新 |
| [knowledge.md](./knowledge.md) | KNOWLEDGE（AI 沉淀：Gotchas / Flagged Ambiguities / Preferences / Out-of-Scope） | bootstrap 建骨架 · bug/review/验收硬时机追加 |
| [dev-rules.md](./dev-rules.md) | DEV-RULES（人维护强制开发规范） | bootstrap 无则建空壳 · blueprint/dev 必读 |
| [ui-rules.md](./ui-rules.md) | UI-RULES（人维护设计策略 · 装策略不装视觉值） | bootstrap 无则建空壳 · ui_design 必读 |
| [glossary.md](./glossary.md) | GLOSSARY 业务术语表 | bootstrap 建空壳 · PRD/TECH 起草前 + triage 按需读 |
| [troubleshooting.md](./troubleshooting.md) | TROUBLESHOOTING 排查工具集（环境 / log / DB / 敏感配置读法） | bootstrap 建空壳 · 排查与 AI 连环境时必读 |
| [process-ledger.md](./process-ledger.md) | PROCESS-LEDGER 流程价值台账（一行一 feature · 年检数据源） | ship1 规划 gate append · 无则按模板建 |

## 规划层（product-overview / 子项目 ROADMAP）

| 文件 | 用途 | 主要消费方 / 时机 |
|------|------|------------------|
| [workstream.md](./workstream.md) | WS 规划单元（frontmatter 名册 + WS-PROGRESS/WS-DAG 标记区） | feature-planning 产出 · `state.py ws-lint / ws-progress` 消费 |
| [roadmap.md](./roadmap.md) | ROADMAP（BL 清单 + Wave 编排 + 关联 WS · 位置 `docs/ROADMAP.md`） | feature-planning 写入 · PMO 随 Feature 流转同步 |
| [sitemap.md](./sitemap.md) | IA 地图（页面层级/导航/路由 · 位置 `{子项目}/docs/design/sitemap.md` 与全景同目录） | feature-planning Step 5 seed · ui_design 增量扩页 |
| [pending.md](./pending.md) | PENDING 待规划需求池（`product-overview/PENDING.md`） | PMO 发现"范围外但要做"即追加 · 转化即删 |

## 配置与脚本

| 文件 | 用途 | 主要消费方 / 时机 |
|------|------|------------------|
| [config.md](./config.md) | RESOURCES.md + `.teamwork_localconfig.json` 字段说明 + external/README | 项目初始化 / 配置调整时对照 |
| [teamwork_localconfig.json](./teamwork_localconfig.json) | `.teamwork_localconfig.json` 实例模板（worktree / scope / id_strategy 等 + bootstrap state） | bootstrap 创建与维护 |
| [local-env-config.properties](./local-env-config.properties) | `.teamwork-local-env/config.properties` 模板（本机 secret · 双重 gitignore） | bootstrap 缺失时自动建 · 用户填真值 |
| [preview-project-preview.sh](./preview-project-preview.sh) | same-stack 预览脚本（动态端口 dev server · 输出 PREVIEW_URL） | ui_design / 规划层全景 seed 时拷入 `preview-project/` |
| [verify-ac.py](./verify-ac.py) | AC↔test 覆盖机器校验脚本（直接调 · 无需复制） | blueprint / dev Output Contract 调用 |

## 机制文件（决策 / 测试资产）

| 文件 | 用途 | 主要消费方 / 时机 |
|------|------|------------------|
| [adr.md](./adr.md) | ADR 单条决策（Context / Alternatives≥2 / Decision / Consequences） | Blueprint「3 问触发器」全 yes 时架构师创建 · 落 `{子项目}/docs/adr/` |
| [adr-index.md](./adr-index.md) | ADR 索引（每子项目 `docs/adr/INDEX.md`） | 首条 ADR 时创建 · 每次 ADR 变更同步 · PMO triage 读 |
| [e2e-registry.md](./e2e-registry.md) | E2E 回归中心（REG case 完全自包含） | QA 在 Feature 完成时晋升 / 同步 REG case |
| [test-baseline.md](./test-baseline.md) | 测试基线失败集（brownfield 预存在失败登记 · test gate 差分判定） | test stage 差分判定 · `--add` 登记核实过的预存在失败 |
