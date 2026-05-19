# Prepare · 进状态机前的准备子流程

> **可重入子流程** · 任何"决定要走某流程"的 PMO 主对话点都走一次。
> 输入:用户意图(自然语言 / Feature Planning 中的 BL-NNN / 升级讨论收敛)
> 输出:`state.py init-feature` 命令的 5 项参数(flow_type + feature_id + worktree_path + branch + merge_target)

---

## 0. Must-read(PMO 进 prepare 前必读)

🔴 **必读 spec**(动手前主对话 cite 关键原文 · 详 SKILL.md § P0-11):
- **[conventions.md §9-12](./conventions.md)** — worktree path 规范(`{worktree_root_path}/{Feature-ID}` · 默认 `.worktree/`)
- **`.teamwork_localconfig.json`** — 项目级 worktree_root_path 配置(读 `worktree_root_path` 字段 · 不存在用 `.worktree`)
- **[feature-planning.md §0](./feature-planning.md)** — 何时改走 Feature Planning(关键词 + 复杂度双触发)

---

## 1. 触发场景

| 场景 | 何时走 |
|---|---|
| **新 session · mode B execute** | SKILL.md § Triage 入口规范 mode 分诊判 B → 进 prepare |
| **mode E discuss 升级 B** | 讨论收敛后 PMO 主动建议升级 → 进 prepare |
| **Feature Planning 完成后启 Feature** | PL 在 ROADMAP 拆完后 · 用户拍板某 BL → PMO 同 session 走 prepare 启动 Feature |
| **mode A/D 转 B**(罕见) | 用户从查看/状态切到执行 → 进 prepare |

**非触发场景**(prepare 不跑):
- mode A query / mode D status:不进状态机
- mode C resume:已有 state.json · 直接 jump
- Feature Planning 流程本身:由 PMO 主对话按 [docs/feature-planning.md](./feature-planning.md) 执行 · 不需 prepare(不进状态机)
- 问题排查流程:同上 · 不进状态机

---

## 1.5 Step 0 · 上下文准备

PMO 移交 prepare 后 · **必走以下 4 项准备**(emit 暂停点之前):

### 1.5.1 · 检 Planning ship 状态(若是 BL 启动 Feature)

若用户启动来自 ROADMAP 某 BL-NNN(Feature Planning 已完成):
- 读 ROADMAP.md 定位该 BL 行
- 检 Planning Feature 已 ship 的 commit hash(`git log --grep='<Planning Feature ID>'`)
- 输出"Planning ship 状态"行(给暂停点表格 · 用户看到 = 上游已 ready)

无 Planning(直接 mode B execute)→ 跳此项。

### 1.5.2 · 检上游依赖(state.json blocking)

若 prepare 是从已有 Feature 衍生:
- 检上游 Feature 的 `state.blocking.pending_external_deps`
- 列已就绪 / 待中(给暂停点表格)

无上游 → 跳。

### 1.5.3 · 扫代码现状(可选 · 1 句话总结)

可选(高复杂度 Feature 推荐):
- grep 关键模块当前实现(如 PTR-F041 = adapter.rs Impact-only 硬编码)
- 给暂停点表格 1 句话总结 · 让用户验证启动方向无误

低复杂度 / 用户已知 → 跳。

🔴 **路由前缀必判**(即便跳过上面的可选深挖):据**改动代码所在的子项目目录**定 artifact 前缀 + docs_root —— 查 `teamwork-space.md` 子项目清单(代码在 `apps/partner/` → 用 PTR 注册前缀 + docs_root · 在 `services/` → SVC-* · …)。**不可沿用上一个 Feature 的前缀**。错前缀 / 错路径 → `init-feature` 路由物化校验 FAIL(治本 F049:代码在 partner 却建成 `SVC-PLATFORM-F049` 落仓库根)。

### 1.5.4 · ID 冲突预检 + stage 评审角色预览(强制)

```bash
state.py prepare-check --feature-id-prefix <PROJ> --flow-type <Feature|Bug|Micro|敏捷需求>
```

输出含:
- `next_available_id_stem` + `existing_ids` + `id_letter`(ID 冲突预检 · 字母 F/B/M 由 `--flow-type` 定 · 详 conventions.md §1)
- `stage_chain_preview`(stage × 评审角色预览 · 让 AI 在 prepare 阶段就看到各 stage 的建议评审角色)

🔴 `--flow-type` 必传:Bug → `PREFIX-B{NNN}` · Micro → `PREFIX-M{NNN}` · Feature/敏捷需求 → `PREFIX-F{NNN}`。漏传退回字母 F · Bug/Micro 会错号(治本 PTR Bug 误推 PTR-F047 case)。

PMO 把数据填进暂停点表格:
- `next_available_id_stem` → artifact ID 推荐默认值
- `stage_chain_preview` → 渲染「📋 各 stage 评审角色」子表(详 §4 emit 模板)

---

## 2. Step 1 · 流程类型识别(6 闭集 · R2 红线)

PMO 按以下关键词表判定 user input 落入哪类流程:

| 关键词模式 | 流程类型 |
|----------|---------|
| 规划 / Feature Planning / feature planning / 更新 roadmap / 拆 roadmap / 路线图 / 全景 / 做电商 / 做 SaaS / 商业模式调整 | **Feature Planning** |
| 排查 / 查 log / 诊断 / why X 慢 / 调研 / 分析根因 | **问题排查** |
| 修复 / bug / 报错 / 500 / 502 / 挂了 / 无法登录 / 生产问题 | **Bug** |
| 换 logo / 换图 / 改文案 / 改样式 / 改颜色 / 改配置常量 | **Micro** |
| 加按钮 / 加导出 / 加字段 / 列表加列 | **敏捷需求** |
| 实现 / 开发 / 做功能 / 新建模块 | **Feature**(兜底)|

落入 6 闭集之一(R2 红线 · enum 强制)。

**触发场景为 "Feature Planning 启 Feature"** 时:flow_type 默认 `Feature`(因为是从 BL-NNN 启动具体功能 · BL 已经决定了"做什么")。

### 2.1 · 复杂度升级判据(覆盖关键词初判)

🔴 **关键词命中 Feature / 敏捷需求 / Micro 时 · PMO 必再扫以下复杂度信号** · 命中任一 → **强制升 Feature Planning**(覆盖关键词初判):

| 信号 | 例 | 不计入 |
|---|---|---|
| **跨独立部署服务**(≥2 个) | 独立 git repo / 独立 origin / 独立部署单元(后端服务 + 前端 + 管理后台) | mono-repo 内跨 apps(同 origin · 单部署单元) → 用"影响 ≥2 BL"判 |
| **数据模型重构** | 删/改老字段(影响存量) / 表结构变动 / 字段语义重定义 | 新增字段(无存量影响) |
| **老需求架构性废弃** | "X 不要了"/"统一为 Y"/"重构这套逻辑" / 整套机制语义替换 | 仅扩展(向后兼容) |
| **影响 ≥2 BL** | 一次需求拆成多个 Feature 协同(admin / backend / partner 各 1 BL) | 单 Feature 内多 commit |
| **方向级业务变更** | 新增/删除业务能力 / 商业模式调整 / 用户角色重新设计 | UI 文案微调 |

**为什么强制升级**:这些信号意味单 Feature 状态机承载不下 — 跨仓库要 panorama-design 全景 · 数据模型重构要 ROADMAP 多 Feature 协同 · 单 Feature 的 PRD/TC/TECH 写不下"3 仓库 + 老字段迁移 + 多 BL 拆解"。强行进 Feature → PMO 在主对话散述 Q1-Q4 决策树(违 R5 暂停点协议 · 写伪 PRD)。

**PMO 命中后必输出**(R5 标准 1/2/3 暂停点 · 不用自由文本):
```markdown
⏸️ 复杂度判据触发(prepare §2.1)· 你的需求触发以下复杂度信号:
- <信号 1>(具体:<例>)
- <信号 2>

请选择:

1. **进 Feature Planning 流程** 💡 推荐
   理由:跨仓库 / 数据模型重构 / 多 BL · 单 Feature 状态机承载不下
   动作:走 panorama-design 起全景 → ROADMAP 拆 BL-N → 每个 BL 后续启独立 Feature
2. **就一个 Feature**(确认范围未超 · 继续 mode B)
   理由:你确认信号是误判 / 范围实际收敛在单 Feature
   动作:继续 prepare · 按 Feature 流程走
3. **其他指示**
```

**反例**:
- 用户:"整体改下这里的逻辑 · source_type 不要了 · 统一为 api · adapter 改为账号可选功能"
- ❌ PMO 错:命中"整体改"→ Feature 兜底 → 主对话 emit Q1-Q4 决策树
- ✅ 正确:命中"跨 3 仓库 + 老字段废弃 + 数据模型重构"→ 升 Feature Planning → panorama-design + ROADMAP 拆 BL

### 2.2 · 敏捷需求 / Micro 准入校验(覆盖关键词初判)

🔴 **关键词命中「敏捷需求」或「Micro」时 · PMO 必验准入硬约束** · 任一不满足 → 升级(关键词只看字面 · 准入硬约束才是真流程边界):

**敏捷需求准入**(全满足才成立 · 否则升 **Feature**):

| 准入项 | 不满足的信号 |
|---|---|
| ≤5 文件改动 | 预估改动 >5 文件 |
| **无 UI 变更** | 改页面结构 / 加显示字段 / 加 UI 组件(预览/弹窗/图表)/ 改交互 |
| **无架构变更** | 新增模块 / 改接口契约 / **数据库数据结构变更**(新建/删除/修改 表、字段、索引、约束、migration) |
| 方案明确 | 用户需求有歧义 / 实现方式未定 |

**Micro 准入**(全满足才成立 · 否则升 **敏捷需求** 或 **Feature**):

| 准入项 | 不满足的信号 |
|---|---|
| 零逻辑变更 | 改动含任何条件 / 分支 / 数据流逻辑 |
| 改动类型在白名单 | 仅 文案 / 样式 / 资源 / 配置常量 / 注释 · 其它都不算 Micro |

**为什么校验**:关键词("加字段 / 列表加列")只看字面 · 无法区分"后端加字段(无 UI)"和"前端详情页加显示字段(UI 变更)"。命中关键词后 · PMO 必扫代码现状 + 需求范围 · 验准入。

**PMO 命中后必输出**(R5 标准 1/2/3 暂停点 · 不用自由文本):
```markdown
⏸️ 准入校验(prepare §2.2)· 关键词初判 <敏捷需求 / Micro> · 但触发以下准入不满足:
- <准入项>:<具体信号>

请选择:

1. **升级到 <Feature / 敏捷需求>** 💡 推荐
   理由:<准入项> 不满足 · 原流程 stage 链承载不下(如有 UI 变更但敏捷需求无 ui_design)
   动作:按 <Feature / 敏捷需求> 流程走;有 UI 变更的 Feature 在 goal-complete 标 `--needs-ui=true` 进 ui_design
2. **坚持 <原流程>**
   理由:你确认准入信号是误判
   动作:按 <原流程> 继续(⚠️ 跳过 ui_design / 完整 blueprint · 记流程例外)
3. **其他指示**
```

**反例**:
- 用户:"My Offers 详情页加 offerId label + 加 raw JSON 预览"
- ❌ PMO 错:命中"加字段"→ 敏捷需求(漏验准入)
- ✅ 正确:命中"加字段"→ 验准入 → "加 raw JSON 预览组件 + 改详情页信息结构" = UI 变更 → 升 Feature(goal-complete `--needs-ui=true`)

---

## 3. Step 2 · worktree 决策模板

PMO 按 flow_type 算 branch 前缀 + worktree path 建议:

| flow_type | branch 前缀 | worktree |
|----------|-----------|---------|
| Feature | `feature/` | 必 |
| 敏捷需求 | `agile/` | 必 |
| Bug | `fix/` | 必 |
| Micro | `micro/` | 必 |
| Feature Planning | — | 不进状态机 · 不走 prepare |
| 问题排查 | — | 不进状态机 · 不走 prepare |

**worktree path 默认** = `{worktree_root_path}/{Feature-ID}` ·
其中 `worktree_root_path` 解析顺序:
1. `state.json.environment_config.worktree_root_path`(已存在 Feature)
2. 项目根 `.teamwork_localconfig.json` 的 `worktree_root_path` 字段
3. 默认 `.worktree`(项目根子目录)

完整规范见 [docs/conventions.md § 9-11](./conventions.md)。

---

## 4. Step 3 · emit 完整表格(1 次完整 · 不分多轮)

PMO 复制给用户 · 🔴 **必含全 5 段**(漏任一段 = R5 暂停点违规 · 用户可叫停):

1. `# 流程概览`(flow_type + stage 链 + 理由)
2. `# 建议评审角色`(stage × 评审角色 × 建议理由表 · 数据从 `prepare-check --flow-type` 渲染)
3. `# 上下文准备(Step 0 已读)`(Planning ship / 上游依赖 / 代码现状 / ID 冲突)
4. `# Worktree 策略`(branch 前缀 + worktree_root_path + 推荐 path)
5. `# 4 项配置`(artifact ID + merge_target + worktree path + branch)

```markdown
⏸️ Prepare · 进入流程前总览(回 `ok` / `all default` 全用推荐 · 或修改某几项 + 确认)

# 流程概览
📋 **流程类型**:<flow_type>(命中关键词 /<keyword>/)
📋 **stage 链**:<完整 stage 链 · 由 FLOW_BY_TYPE[flow_type] 渲染>
📋 **理由**:<识别理由 1 句>

# 建议评审角色 🔴(初步建议 · 各 stage 进入时可按方案复杂度调整)
> 数据从 `prepare-check --flow-type` 输出 `stage_chain_preview` 渲染 · **不可跳过**。

| stage | 必/选 | 建议评审角色 | 建议理由 |
|---|---|---|---|
| <stage> | <必跑/可选(若可选括号注触发条件)> | <reviewers 列表 / — (无 reviewer)> | <从 reason 字段渲染 · 1 句话为什么这些角色> |
| ...(每 stage 一行) | | | |

📎 reviewers="—" 表示 stage 无多角色评审(dev = RD 自写代码 + git commit / ship = PMO 编排 push+MR)。
📎 **初步建议 · 可调整**:
  - 各 stage-start 时 state.py 会再次输出本 stage 的「建议评审角色」段 · AI 按方案复杂度判定是否需调整
  - 简单方案可去 external · 高风险方案补 architect/external
  - **调整命令**:
    ```bash
    state.py change-review-roles --feature <path> --stage <stage> --roles 'a,b,c' --reason '<理由>'
    ```
    自动写 `stage_review_roles_adjustments` audit · 后续 stage-complete 校验按新值。

# 上下文准备(Step 0 已读)
- **Planning ship 状态**:<✅ <Planning Feature ID> · commit ... merge 到 staging | ⏭️ N/A>
- **上游依赖**:<✅ <list> | ⏭️ 无外部依赖>
- **当前代码现状**(可选):<1 句话总结 | ⏭️ 跳过>
- **ID 冲突扫描**:<已占 [<ids>] · 推荐 <next_available_id>>

# Worktree 策略
- **branch 前缀**:<feature/ | agile/ | fix/ | micro/>(由 flow_type 决定)
- **worktree_root_path**:<.worktree | ../<repo>-worktrees>(读 .teamwork_localconfig.json · 默认 .worktree)
- **推荐 path**:`{repo-root}/{worktree_root_path}/<Feature-ID>`

# 4 项配置(默认推荐 · 可改)
| # | 字段 | 推荐 | 理由 |
|---|---|---|---|
| 1 | **artifact ID** | <prepare-check `next_available_id_stem` · 字母 F/B/M 按 flow_type> | <冲突避让 + 业务命名> |
| 2 | **merge_target** | staging | <与项目历史 Feature 一致> |
| 3 | **worktree path** | <推荐 path 同上> | 默认 worktree_root_path |
| 4 | **branch** | <branch-prefix><Feature-ID-kebab-case> | 与 ID 一致 |

📎 **是否需要 UI Design Stage** 由 goal-complete 时 `--needs-ui` 决策 · prepare 入口不强制提前拍板。
```

flow_type → first_stage 映射:
- Feature / 敏捷需求 → `goal`
- Bug / Micro → `dev`
- Feature Planning / 问题排查 → 不进状态机 · prepare 在这两个流程上不调用

🔴 **必 1 次完整 emit · 不分多轮**(防 PMO 先建议 + 再"最终确认"的 2 轮交互浪费)。
🔴 **用户回 `ok`** · PMO 视作"按建议全部默认值" · 不再二次确认 · 立即执行 §5。

### 4.1 · emit 自检清单(PMO emit 前自查 5 段齐)

- [ ] § 流程概览(flow_type + stage 链 + 理由)
- [ ] § 建议评审角色(prepare-check `stage_chain_preview` 表已渲染 · 不可漏)
- [ ] § 上下文准备(4 子项:Planning / 上游 / 代码 / ID 冲突)
- [ ] § Worktree 策略(branch 前缀 + worktree_root_path + 推荐 path)
- [ ] § 4 项配置(artifact ID + merge_target + worktree path + branch)

任一项缺 → 重 emit(用户不应被迫忽略漏段)。

---

## 5. Step 4 · 用户确认后 · PMO 显式执行

```bash
# 用户回(或 all default):
# 1. Feature ID: PTR-F033
# 2. merge_target: staging
# 3. worktree path: <repo>/.worktree/PTR-F033
# 4. branch: feature/PTR-F033

# PMO 跑(在主工作区 cwd · 不是 worktree):
git fetch origin
git worktree add -b feature/PTR-F033 <worktree-path> origin/staging
cd <worktree-path>

# 此刻 cwd 在 worktree 内 · 进状态机:
state.py init-feature \
 --feature docs/features/PTR-F033 \
 --feature-id PTR-F033 \
 --flow-type Feature \
 --merge-target staging \
 --branch feature/PTR-F033 \
 --worktree-mode auto \
 --worktree-path <worktree-path>
```

🔴 **Bug 流程额外前置**:init-feature 之后 · dev-start 之前先起草 `bugfix/BUG-<bug-id>.md`(模板 `templates/bug-report.md`)· 含 frontmatter `bug_id/symptom/root_cause/fix_summary` + body §现象/§根因/§修复方案/§回归测试。

---

## 6. 与状态机的接口

prepare 完成 = init-feature 前置满足:
- ✅ flow_type / feature_id 已用户确认
- ✅ worktree 物理已创建(PMO 显式跑)
- ✅ cwd 在 worktree 内(PMO 显式 cd)
- ✅ branch / merge_target 已用户确认

**init-feature 拒绝条件**(状态机入口物化拦截):
- worktree_mode != off 但 cwd 不在 worktree → FAIL
- worktree_mode != off 但 worktree 物理不存在 → FAIL
- flow_type ∈ {Feature Planning, 问题排查} → reject(不进状态机)

**prepare 不做的事**:
- ❌ 不写 state.json(state.json 由 init-feature 创建)
- ❌ 不创建 worktree(由 PMO 显式跑)
- ❌ 不自动跑 git(防漏看用户确认)

---

## 7. 错误处理

### 7.1 · 流程类型识别错(关键词模糊)

PMO 识别不准 → 在暂停点列出"我猜是 X · 你确认是 Y/Z?"让用户拍板。

### 7.2 · 用户拒绝 worktree 默认值

部分用 default + 部分自定 → PMO 用混合值跑 git worktree add。
全否决 → 等用户给完整 4 项。

### 7.3 · git worktree add 失败

- branch 已存在 → `git worktree remove <path>` + `git branch -D <branch>`
- origin/base 不存在 → `git fetch origin`
- path 已存在但非 worktree → 删 path 或换 path

错误处理由 PMO 主导 · 不在 state.py 状态机里。

---

## 8. 红线

### R-P1 · 必经用户确认

prepare 输出暂停点后 · 必须等用户明确回 4 项配置(或 "all default")。
**不可** PMO 自己拍板 worktree path / branch / merge_target。

### R-P2 · 用户未确认前不进状态机

PMO 在用户未确认前 · **不可** cd / git worktree add / init-feature。
违规 = 主 tree 污染风险。

### R-P3 · 不可枚举判断留 PMO

意图总结 / 流程类型识别的不可枚举部分 → PMO 主对话判断(模糊时问用户)。
关键词表是辅助 · 不是强制 · PMO 可基于上下文覆盖默认。

---

## 9. 相关文档

- [SKILL.md § Triage 入口规范](../SKILL.md) — 5 mode 入口分诊(prepare 由 mode B / mode E 升级触发)
- [docs/feature-planning.md § 5](./feature-planning.md) — Feature Planning 完成后启 Feature 走 prepare
- [docs/conventions.md](./conventions.md) — Feature ID + worktree path 编号规范
- [SKILL.md](../SKILL.md) — 顶层叙事 + 项目级文档信息架构
- [SKILL.md § PMO 软约束 + 暂停点标准格式](../SKILL.md) — R5(b) PMO 必读
- [docs/v8-redesign/00-MANIFESTO.md § 十一](./v8-redesign/00-MANIFESTO.md) — R2 流程闭集 + R5 暂停点 rationale
