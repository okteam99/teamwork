# Teamwork vs GStack - 深度对比与借鉴建议

> 调研日期：2026-04-14
> 对象：Teamwork Skill（本仓库） vs [garrytan/gstack](https://github.com/garrytan/gstack)
> 结论：GStack 更像“单人超级开发者工具箱”，Teamwork 更像“多角色流程治理系统”。两者不是替代关系。Teamwork 应该吸收 GStack 的交付闭环、独立审查、浏览器/性能/部署能力，但不应复制其松散多入口模型。

---

## 1. 快速结论

GStack 的最新 README 显示，它已经不是早期“23 个专项工具”的简单集合，而是一个跨宿主的 AI coding workflow：支持 Claude Code、Codex、OpenClaw 等多种 agent 环境；提供 `/review`、`/ship`、`/land-and-deploy`、`/qa`、`/benchmark`、`/canary`、`/codex`、`/learn`、`/guard` 等命令；通过 `~/.gstack/` 保存 review、timeline、learnings、benchmark、deploy 等运行数据。

Teamwork 目前的优势是流程完整、角色边界清楚、文档体系强、跨子项目协作更强。它的问题是重、慢、入口单一、交付链条止于验收，缺少 GStack 这种“从计划到 PR 到部署验证再到学习沉淀”的自动化闭环。

最值得借鉴的不是 GStack 的品牌化话术，而是 9 个机制：

1. Review Readiness Dashboard
2. `/ship` 的发版前自动审查 + 覆盖率审计 + PR body 生成
3. `/land-and-deploy` 的首次 dry-run + CI/merge/deploy/canary 报告
4. `/review` 的 specialist 并行审查 + cross-model adversarial review
5. `/qa` 的健康分、baseline、regression fix loop
6. `/benchmark` 的性能 baseline/trend
7. `/learn` 的结构化经验沉淀
8. `/guard`、`/freeze` 的编辑范围与危险命令防护
9. proactive routing 的自然语言触发建议

---

## 2. 当前 GStack 状态

### 2.1 仓库规模与定位

截至 2026-04-14 GitHub 页面显示：

| 指标 | 当前值 |
|------|--------|
| Stars | 71.5k |
| Forks | 10.1k |
| Commits | 214 |
| Issues | 113 |
| Pull requests | 224 |

README 对 GStack 的描述是：把 Claude Code 变成一个虚拟工程团队，包含 CEO、工程经理、设计师、reviewer、QA lead、安全官、release engineer 等角色，并通过 slash commands 调用。

一个细节：README 文案仍说“23 specialists and eight power tools”，但安装命令列出的可用命令已经超过 30 个，包括：

`/office-hours`、`/plan-ceo-review`、`/plan-eng-review`、`/plan-design-review`、`/design-consultation`、`/design-shotgun`、`/design-html`、`/review`、`/ship`、`/land-and-deploy`、`/canary`、`/benchmark`、`/browse`、`/connect-chrome`、`/qa`、`/qa-only`、`/design-review`、`/setup-browser-cookies`、`/setup-deploy`、`/retro`、`/investigate`、`/document-release`、`/codex`、`/cso`、`/autoplan`、`/plan-devex-review`、`/devex-review`、`/careful`、`/freeze`、`/guard`、`/unfreeze`、`/gstack-upgrade`、`/learn`。

这说明它的实际形态已经从“技能包”演进成“AI 开发操作系统”。

### 2.2 跨宿主支持

GStack README 明确说支持 8 种 AI coding agents，不再只面向 Claude Code。它还提供 OpenClaw routing 示例，能让 OpenClaw spawn Claude Code session 并要求其运行 `/cso`、`/review`、`/qa`、`/autoplan`、`/ship` 等。

Teamwork 当前更偏 Claude Code / Subagent 语义。虽然本仓库刚加入 Codex Review 相关规范，但整体仍是单宿主模型。

---

## 3. 核心架构对比

| 维度 | GStack | Teamwork | 判断 |
|------|--------|----------|------|
| 入口 | 多 slash command，按任务直接触发 | `/teamwork` 单入口，PMO 判断流程 | Teamwork 治理更强；GStack 使用成本更低 |
| 控制方式 | 工具型，自选命令组合 | 流程型，PMO 中央调度 | Teamwork 防漏步骤；GStack 更快 |
| 角色模型 | 每个 skill 自带角色、人设、约束 | PMO/PL/PM/Designer/QA/RD/Architect/QA Lead | Teamwork 角色边界更清晰 |
| 状态管理 | `~/.gstack/projects/{slug}` JSONL/Markdown artifacts | 项目文档 + STATUS + teamwork_space | GStack 运行态强；Teamwork 项目可审计强 |
| Review | `/review` + specialist + Codex | 架构 CR + QA CR + Codex Review | GStack 的 dashboard 和去重更成熟 |
| QA | 浏览器 daemon + health score + baseline | TC + integration/API/browser E2E | Teamwork 测试设计强；GStack 实测闭环强 |
| 发版 | `/ship` + PR + docs sync | 当前无完整发版角色 | GStack 明显领先 |
| 部署 | `/land-and-deploy` + canary | 当前无完整部署流程 | GStack 明显领先 |
| 安全 | `/careful`、`/freeze`、`/guard`、`/cso` | 红线、暂停点、危险命令约束 | 各有优势，应合并 |
| 学习沉淀 | `/learn`、learnings.jsonl、timeline | KNOWLEDGE.md、文档沉淀 | Teamwork 可读性强；GStack 可检索性强 |

---

## 4. GStack 的主要优点

### 4.1 交付闭环比 Teamwork 更完整

GStack 的链条可以做到：

```
plan / review / qa
  -> ship
  -> create PR
  -> document-release
  -> land-and-deploy
  -> canary
  -> benchmark
  -> learn
```

Teamwork 的主流程目前通常停在“PM 验收”。这对需求研发管理足够，但对真实交付不够。用户真正关心的是 PR 有没有创建、CI 有没有过、生产有没有部署、线上有没有健康验证、文档有没有跟上。

GStack 的 `/ship` 有几个关键设计值得直接吸收：

- 必须从 feature branch 发版，不能在 base/default branch 上 ship。
- 读取 review log，生成 Review Readiness Dashboard。
- 自动运行缺失的 pre-landing review。
- 对 coverage 做代码路径和用户路径的 ASCII diagram。
- 写 test plan artifact 给后续 QA 复用。
- 创建/更新 PR body，包含 coverage、review、design、verification、TODO、test plan。
- PR 创建后自动触发 `/document-release` 同步文档。

Teamwork 建议新增 `Release Chain`，放在 PM 验收之后：

```
PM 验收 -> Release Readiness -> Ship PR -> Docs Sync -> Land/Deploy -> Canary/Benchmark -> Closeout
```

### 4.2 Review Readiness Dashboard 是高价值抽象

GStack `/ship` 会读取 review log，并显示 Eng Review、CEO Review、Design Review、Adversarial、Outside Voice 的运行次数、最近运行时间、状态、是否 required。

这个设计很好，因为它把“做没做过 review”从口头承诺变成可查询状态。Teamwork 现在有多个评审阶段，但缺少一个统一的 readiness dashboard。状态分散在 PRD/TC/TECH/自查报告/QA 报告里。

Teamwork 可以引入 `TEAMWORK_REVIEW_LOG.jsonl` 或 `docs/features/{feature}/review-log.jsonl`，每次 PRD Review、TC Review、Arch CR、Codex Review、QA CR、QA Lead 都写一行：

```json
{"stage":"arch-code-review","timestamp":"2026-04-14T10:00:00Z","status":"clear","findings":0,"commit":"abc123"}
```

PMO 每次流转时输出一个简版 dashboard：

```text
Review Readiness
| Stage | Required | Status | Last Run | Stale |
| PRD Review | yes | clear | 2026-04-14 | no |
| TC Review | yes | clear | 2026-04-14 | no |
| Arch CR | yes | issues_fixed | 2026-04-14 | no |
| Codex Review | no | skipped | - | - |
| QA CR | yes | clear | 2026-04-14 | no |
```

### 4.3 Specialist 并行 Review 更工程化

GStack `/review` 不是一个 reviewer 从头看到尾，而是按 scope 选择 specialist，并行 dispatch。它还做：

- specialist selection / skip / gated 说明
- JSON line findings
- fingerprint 去重
- confidence gate
- 多 specialist 确认时提高置信度
- red team conditional dispatch
- prior skipped findings suppress
- cross-model synthesis

Teamwork 现在的架构师 CR、QA CR、Codex Review 是串行阶段，质量稳定但耗时重。可以借鉴 GStack，把架构师 CR 拆成可选 reviewer 维度：

| Specialist | 触发条件 |
|------------|----------|
| security | auth、permission、secret、payment、SQL、upload |
| performance | query、cache、loop、render、bundle、large data |
| data migration | schema、migration、backfill |
| API contract | public endpoint、SDK、shared DTO |
| frontend design-lite | CSS/layout/component/UI |
| test coverage | 新业务逻辑、bug fix、复杂分支 |

注意：不建议把 Teamwork 评审完全改成 GStack 的 loose specialist model。Teamwork 仍应保留必经阶段，只把 specialist 作为 Arch CR / QA CR 内部的并行子任务。

### 4.4 Cross-model Review 已经落地得更深

Teamwork 已有 `codex-code-review.md`，但 GStack 把 Codex 放进多个位置：

- `/codex` 可独立运行 review/challenge/consult。
- `/review` 内有 Codex adversarial challenge。
- 200+ 行大 diff 会额外跑 Codex structured review，并用 `[P1]` 做 gate。
- `/ship` 的 Review Readiness Dashboard 会显示 Codex/Adversarial 状态。
- `/codex` 会对 Claude Review 和 Codex Review 做交集/差异分析。

Teamwork 建议升级 Codex Review 为两层：

1. 默认层：所有 Feature 进入 Codex adversarial，非阻塞，给 PMO 汇总。
2. 强门禁层：大 diff、auth/payment/data/migration/security 改动时，Codex structured review 必须通过或用户确认 override。

### 4.5 QA 的实测反馈闭环强

GStack `/qa` 的强项不是“写测试计划”，而是“真跑浏览器并把结果变成健康分和 regression loop”。它会：

- 生成 QA report。
- 截图和 console/network 证据。
- 计算 health score。
- 保存 baseline.json。
- regression 模式对比 fixed/new issues 和 score delta。
- 对 fixable issues 做 fix loop。
- 每个 fix 后重新截图/console/snapshot 验证。
- 为 regression 写测试。
- 用 WTF-likelihood 控制继续修复的风险。

Teamwork 的 TC 和 E2E 设计更系统，但实测指标不够产品化。建议在 Browser E2E / QA Lead 中加入：

```text
Health score: 0-100
Console errors: N
Critical user flows passed: X/Y
Regression delta: +N fixed / -N new
Screenshots: before/after paths
WTF-likelihood: N%
```

这个比“测试通过”更有决策价值。

### 4.6 `/land-and-deploy` 很适合作为 Teamwork 的交付后半段

GStack `/land-and-deploy` 设计了首次 dry-run：

- 检测 GitHub CLI auth。
- 找 PR。
- 检测 merge method / merge queue / CI / deploy workflow / staging / canary URL。
- 首次部署前让用户确认它对项目部署方式的理解。
- 后续用 deploy config hash 判断是否需要重新 dry-run。
- CI pending 时等待，CI fail 则停止。
- merge 后等待 deploy，并做单次 canary verification。
- 输出 deploy report，包含 timing、review status、CI、deploy、staging、verification、verdict。

Teamwork 目前没有同级能力。建议新增 `Release/Deploy` 角色或 `Release Chain` agent。最小版本先不做真正部署，只做：

1. PR readiness 检查
2. CI 状态读取
3. PR/MR 创建
4. 部署配置 dry-run
5. post-merge health check

### 4.7 `/learn` 和 timeline 比单纯 KNOWLEDGE.md 更适合 agent 检索

Teamwork 的 `KNOWLEDGE.md` 对人类友好，但 agent 检索不一定稳定。GStack 用 JSONL 记录：

- type: pattern / pitfall / preference / architecture / tool / operational
- source: observed / user-stated / inferred / cross-model
- confidence: 1-10
- files: related paths

建议 Teamwork 保留 `KNOWLEDGE.md`，但增加机器可读 companion：

```text
docs/teamwork-learnings.jsonl
```

每个 Subagent 输出“知识沉淀”时，PMO 同步写一行结构化记录。这样后续 PMO 启动 Subagent 时可以按 `files`、`type`、`confidence` 检索并注入 prompt。

---

## 5. GStack 的主要缺点

### 5.1 流程一致性弱

GStack 每个 skill 都很强，但跨 skill 的强制顺序弱。用户可以直接 `/ship`，也可以不跑 `/plan-ceo-review`、不跑 `/design-review`、不跑 `/qa`。虽然 `/ship` 会补一些检查，但它本质仍是“命令组合”，不是“流程治理”。

Teamwork 的阶段链和 PMO gate 更适合复杂项目、跨子项目、多人协作和需要审计的场景。

### 5.2 中央治理弱，容易变成工具菜单

GStack 多入口灵活，但也容易让用户不知道下一步该用什么。它用 proactive suggestions 缓解，但这仍然依赖 trigger 规则和用户接受程度。

Teamwork 的 PMO 模型更像项目经理，能持续维护全局状态、依赖、阶段链、暂停点和跨项目拆分。

### 5.3 本地状态强，项目内可审计性弱

GStack 很多数据写到 `~/.gstack/`。这对单人开发效率很好，但对团队共享、代码审计、CI 复现不一定理想。Teamwork 的文档产物在 repo 内，便于 review 和交接。

建议 Teamwork 不要照搬 `~/.gstack/` 为主的状态策略。更好的方式：

- repo 内保存 feature 相关状态：review log、QA report、release report、learnings。
- 用户本地只保存隐私/全局配置：偏好、浏览器 cookie、agent telemetry。

### 5.4 Preamble 过重且重复

GStack raw skill 里每个 skill 都有大段 preamble：update check、sessions、telemetry、routing、vendoring、voice、context recovery、completion protocol 等。这样独立 skill 很方便，但复制成本高、维护容易漂移。

Teamwork 已经在做模块化拆分，不应走“每个角色文件复制大 preamble”的路线。应该继续坚持：

- `SKILL.md` 做索引和红线
- `FLOWS.md` 管流程
- `agents/README.md` 管通用 subagent 规范
- 单 agent 文件只保留角色私有规则

### 5.5 过度自动提交/自动文档更新可能不适合 Teamwork

GStack `/qa` fix loop 有“一 issue 一 commit”，`/ship` 会自动 `/document-release` 并提交文档。这对个人 builder 很顺手，但 Teamwork 用户可能希望 PMO 在关键写操作前汇报状态。

Teamwork 可以借鉴“自动发现文档漂移”和“生成 PR body”，但是否自动 commit/push 应保留用户确认或项目配置。

---

## 6. Teamwork 已经吸收的 GStack 思路

本地 Teamwork 已经部分吸收了旧版分析中的建议：

| 建议 | 当前状态 |
|------|----------|
| 危险命令红线 | 已加入 `agents/README.md` 2.5 |
| 编辑范围约束 | 已加入 PMO 启动 Subagent prompt |
| Codex Review | 已新增 `agents/codex-code-review.md` |
| Dev Chain / Verify Chain | 已新增 `agents/dev-chain.md`、`agents/verify-chain.md` |
| 模板拆分 | 已新增 `templates/` 目录 |
| 流程拆分 | 已新增 `FLOWS.md`、`STATUS-LINE.md`、`rules/` |
| API E2E | 已新增 `agents/api-e2e.md` |

这说明下一步不应该再重复“加危险命令红线、加 Codex Review”这类已经完成的动作，而应该补齐 GStack 的第二层能力：readiness dashboard、release/deploy、QA health score、learning JSONL、performance baseline。

---

## 7. 建议借鉴清单

### P0：新增 Release Chain

**目标**：补齐 Teamwork 从“验收完成”到“PR/CI/部署/验证”的断点。

建议文件：

```text
skills/teamwork/agents/release-chain.md
skills/teamwork/templates/release-report.md
skills/teamwork/templates/pr-body.md
```

建议流程：

```text
PM 验收完成
  -> Release Readiness Dashboard
  -> git status / diff / log
  -> review freshness check
  -> test evidence summary
  -> PR/MR body 生成
  -> 可选 docs sync 检查
  -> 用户确认后创建 PR/MR
```

第一版不必自动 merge/deploy。先做到“创建 PR + 完整交付报告”。

### P0：新增 Review Readiness Dashboard

**目标**：让 PMO 不再凭文档记忆判断“评审是否完成”。

建议新增：

```text
docs/features/{feature}/review-log.jsonl
```

写入来源：

- PRD Review
- TC Review
- Arch Tech Review
- Arch Code Review
- Codex Review
- QA Code Review
- Integration Test
- API E2E
- Browser E2E
- QA Lead
- PM Acceptance

PMO 每次关键流转读取并输出 dashboard。对过期评审做 stale 标记：如果 review commit 与 HEAD 不一致，显示需重跑或说明差异不影响。

### P1：把 Codex Review 升级为 Cross-model Review Gate

当前 Teamwork 有 Codex Review agent，但建议加触发条件：

| 条件 | 动作 |
|------|------|
| diff > 200 lines | Codex structured review 必跑 |
| auth/payment/security/data migration | Codex structured review 必跑 |
| 普通 Feature | Codex adversarial 非阻塞 |
| Micro | 默认跳过，PMO 可建议 |

输出时不要只贴 Codex 结论，应该做 synthesis：

```text
Cross-model Synthesis
| Finding | Claude Arch | QA | Codex | Action |
| ... | yes/no | yes/no | yes/no | fix/accept/skip |
```

### P1：QA Health Score + Regression Baseline

建议在 Browser E2E / QA Lead 后生成：

```text
docs/features/{feature}/QA-HEALTH.md
docs/features/{feature}/qa-baseline.json
```

基础评分可以先简单：

| 类别 | 权重 |
|------|------|
| Console | 15% |
| Critical flow | 30% |
| API errors | 20% |
| Visual/layout | 15% |
| Accessibility smoke | 10% |
| Performance smoke | 10% |

不用一开始就实现 GStack 的完整 fix loop。先把“健康分 + 证据 + baseline”落地。

### P1：新增 Deploy Dry-run，不急着自动部署

GStack `/land-and-deploy` 的首次 dry-run 很值得借鉴。Teamwork 第一版可以只做部署配置认知：

```text
Deploy Dry-run
| Item | Detected | Evidence | Risk |
| Platform | Vercel/GitHub Actions/... | file/command | low |
| CI required | yes/no | gh pr checks | medium |
| Deploy trigger | merge/main/manual | workflow file | medium |
| Health URL | /health or unknown | config | high |
```

PMO 问用户确认：

```text
我对部署方式的理解是否正确？
A. 正确，保存为项目部署配置
B. 不正确，我补充说明
C. 暂不处理部署
```

### P1：新增 structured learning JSONL

保留 `KNOWLEDGE.md`，同时写：

```text
docs/teamwork-learnings.jsonl
```

字段：

```json
{"type":"pitfall","key":"redis_test_env","insight":"Integration tests require REDIS_HOST=localhost and empty REDIS_PASSWORD","confidence":9,"source":"observed","files":["infra/docker-compose.yml"]}
```

PMO 启动 Subagent 前按 `files` 和 `type` 检索，注入“相关历史经验”。

### P2：Proactive Routing 建议模式

Teamwork 不适合改成 GStack 的多入口，但可以加自然语言建议：

| 用户输入 | PMO 建议 |
|----------|----------|
| “帮我发版/提交 PR” | 建议 Release Chain |
| “上线后看看有没有问题” | 建议 Canary/Deploy Verify |
| “测一下网站” | 建议 Browser E2E / QA Health |
| “性能怎么样” | 建议 Benchmark |
| “这个方案靠谱吗” | 建议 Product Lead / Arch Review |

注意：建议模式不要绕过 Teamwork 流程。它只帮助选择流程，不创建第七种需求类型。

### P2：Performance Benchmark

GStack `/benchmark` 的 baseline/trend 很好，但 Teamwork 可以轻量化：

```text
docs/features/{feature}/PERF-BASELINE.json
docs/features/{feature}/PERF-REPORT.md
```

先记录：

- TTFB
- FCP
- LCP
- DOM complete
- total requests
- total transfer bytes
- largest JS/CSS resources

不用一开始做趋势分析，先在 UI/性能相关 Feature 中要求 RD/QA 记录关键页面基线。

---

## 8. 不建议借鉴的点

| GStack 机制 | 不建议照搬原因 | Teamwork 替代方案 |
|-------------|----------------|-------------------|
| 多 slash command 随意组合 | 会削弱 PMO 中央治理 | 维持 `/teamwork` 单入口，增加 PMO proactive suggestion |
| 大量本地 `~/.gstack/` 状态 | 团队共享弱 | feature 级 artifact 放 repo，本地只存偏好 |
| 每个 skill 复制 preamble | token 成本和漂移风险 | 继续模块化：SKILL/FLOWS/RULES/agents |
| 自动 commit/push/docs sync 全自动 | 对团队流程风险高 | 默认生成建议，用户确认后执行 |
| 强人格化 voice rules | 会干扰 Teamwork 专业角色边界 | 保留角色专业语气，不引入 founder-style copy |
| 过多可选命令 | 用户认知负担大 | PMO 根据上下文调度 |

---

## 9. 推荐实施路线

### Phase 1：交付可见性

1. 增加 `review-log.jsonl` 模板。
2. PMO 增加 Review Readiness Dashboard 输出。
3. QA Lead 增加 Health Score 输出。
4. Codex Review 输出增加 cross-model synthesis。

### Phase 2：发版闭环

1. 新增 `release-chain.md`。
2. 新增 PR/MR body 模板。
3. Release Chain 读取 review-log、测试输出、git diff/log。
4. 生成 PR/MR 文案和 release report。
5. 用户确认后创建 PR/MR。

### Phase 3：部署与线上验证

1. 新增 Deploy Dry-run。
2. 保存部署配置到 repo 内文档，敏感信息除外。
3. 增加 post-merge health check。
4. 增加 canary / benchmark 轻量报告。

### Phase 4：长期学习

1. 新增 `teamwork-learnings.jsonl`。
2. PMO 启动 Subagent 前注入相关 learnings。
3. 增加 stale 检测：如果 learning 关联文件已变更或删除，降低 confidence 或提示复核。

---

## 10. 最终判断

Teamwork 不缺“流程”，缺的是 GStack 那种贴近真实交付现场的 operational loop。

最优方向不是把 Teamwork 改造成 GStack，而是保留 Teamwork 的 PMO 治理和多角色文档体系，把 GStack 的工具型能力纳入 Teamwork 的阶段链：

```text
Teamwork = 流程治理 + 多角色协作 + 文档审计
GStack 可借鉴 = review dashboard + ship/deploy/qa/benchmark/learn 工具链
```

优先做 P0：

1. Review Readiness Dashboard
2. Release Chain

这两个落地后，Teamwork 的最大短板会从“验收后断链”变成“有完整交付报告但部署验证还可增强”。后续再逐步补 QA Health、Deploy Dry-run、Benchmark、Learning JSONL。

---

## 参考来源

- [garrytan/gstack GitHub README](https://github.com/garrytan/gstack)
- [GStack `/review` raw skill](https://raw.githubusercontent.com/garrytan/gstack/refs/heads/main/review/SKILL.md)
- [GStack `/ship` raw skill](https://raw.githubusercontent.com/garrytan/gstack/refs/heads/main/ship/SKILL.md)
- [GStack `/qa` raw skill](https://raw.githubusercontent.com/garrytan/gstack/refs/heads/main/qa/SKILL.md)
- [GStack `/codex` raw skill](https://raw.githubusercontent.com/garrytan/gstack/refs/heads/main/codex/SKILL.md)
- [GStack `/land-and-deploy` raw skill](https://raw.githubusercontent.com/garrytan/gstack/refs/heads/main/land-and-deploy/SKILL.md)
- [GStack `/benchmark` raw skill](https://raw.githubusercontent.com/garrytan/gstack/refs/heads/main/benchmark/SKILL.md)
- [GStack `/learn` raw skill](https://raw.githubusercontent.com/garrytan/gstack/refs/heads/main/learn/SKILL.md)
- 本地 Teamwork 文件：`skills/teamwork/SKILL.md`、`FLOWS.md`、`ROLES.md`、`agents/README.md`、`docs/OPTIMIZATION-PLAN.md`
