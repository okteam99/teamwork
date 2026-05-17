---
name: teamwork
version: v8.0.0
description: 状态机驱动的 AI 开发编排器。state.py 主动校验 + 主动告知,AI 跑命令即知做什么,不再读 spec 凭记忆。/teamwork 启动。
---

# Teamwork Skill · v8.0 Code-driven Orchestration

> v7 → v8 是范式切换 · 不向下兼容。
> 老 Feature 跑 `state.py migrate-v7-to-v8 --feature <path>` 迁移。

---

## 设计哲学

**可枚举的规则进脚本,不可枚举的判断留 AI。**

| 类别 | 例子 | 归宿 |
|------|------|------|
| 可枚举 | 状态转移、入口前置、出口产物、字段 schema、流程闭集、暂停点协议、措辞黑名单 | `tools/state.py` |
| 不可枚举 | PRD 完整性、架构合理性、代码优雅度、暂停点建议文案 | AI 自决 |
| 用户主权 | 代码布局、业务术语、排查命令 | 用户填,teamwork 按需读 |

### 范式对比

```
v7(被替换): v8:
PMO 凭记忆 + 读 spec markdown AI 跑 state.py xx-start
 ↓ ↓
按记忆调度 stage / role state.py 主动校验 + 主动告知
 ↓ ↓
state.py 被动记录 AI 按 state.py 指示执行
 ↓
 AI 跑 state.py xx-complete
 ↓
 state.py 校验产物 + 自动转下一 stage
```

---

## 快速开始

```bash
# 1. session 入口 · PMO 按 SKILL.md § Triage 入口规范分诊(不是 state.py 命令)
# - 5 mode 判定(A query / B execute / C resume / D status / E discuss)
# - mode B → 项目级骨架检查/创建 + 流程类型识别 + worktree 决策
# - 输出 audit_line + 暂停点 markdown 给用户

# 2. 用户确认 4 项配置后 · PMO 显式执行(主工作区 cwd):
git fetch origin
git worktree add -b <branch> <worktree-path> origin/<merge-target>
cd <worktree-path>

# 3. 此刻 cwd 在 worktree 内 · 进入状态机层(state.py 唯一域)
state.py init-feature --feature <feature-dir-in-worktree> ...

# 3. 各 stage 走 -start / -complete
state.py goal-start --feature <path>
# ... AI 按 next_action_brief 完成 stage 工作 ...
state.py goal-complete --feature <path> --auto-commit <hash> --artifacts ...
# state.py 自动校验产物 + 转移下一 stage + 输出下一 stage 的 brief

# 4. Ship
state.py ship-start --feature <path>
state.py ship-phase --action push --feature <path> ...
state.py ship-phase --action confirm-merged --feature <path> ...
state.py ship-phase --action cleanup --feature <path> --status cleaned
state.py ship-complete --feature <path> --auto-commit <hash>

# 5. 错误处理(state.py 主动 hint · PMO 优先按建议修)
# FAIL → 看 missing_prerequisites[*].hint → 自动修复 → 重试
# 重试 3 次仍 FAIL → 暂停点询问用户 → bypass:
state.py xx-start --bypass --reason "<用户确认理由>" --user-confirmed --missing <ids>
```

---

## 命令清单(state.py ≈ 39 命令 · 详 `state.py --help`)

```
A 类 · 状态机入口(用户确认 worktree 后 · 在 worktree 内运行)
└── init-feature 创建 Feature state.json(在 worktree 内)

(triage 是 PMO 入口行为 · 不是 state.py 命令 · 见 SKILL.md § Triage 入口规范)
(prepare 是 PMO 主对话子流程 · 不是 state.py 命令 · 见 docs/prepare.md)

B 类 · Stage 流转(10 stage × 2 + 4 fix/retry + ship-phase)
├── goal-start / goal-complete
├── ui_design-start / ui_design-complete (optional · --needs-ui)
├── blueprint-start / blueprint-complete
├── blueprint_lite-start / blueprint_lite-complete (敏捷需求 only)
├── dev-start / dev-complete
├── review-start / review-complete (--verdict APPROVE|NEEDS_REVISION) + review-fix / review-retry
├── test-start / test-complete (--integration/e2e-test-exit-code) + test-fix / test-retry
├── browser_e2e-start / browser_e2e-complete (optional · execution_hints)
├── pm_acceptance-start / pm_acceptance-complete (--decision approved_and_ship|...)
├── ship-start / ship-complete
└── ship-phase --action {sanitize|push|confirm-merged|cleanup|close-unmerged}

C 类 · 维护(6)
├── snapshot / validate / raw-read / raw-write 只读 + 逃生舱
├── recover state.json 被外部改后认证
└── migrate-v7-to-v8 一次性迁移老 Feature
```

详细 schema 见 [`docs/v8-redesign/01-COMMAND-SCHEMA.md`](./docs/v8-redesign/01-COMMAND-SCHEMA.md)。

---

## 用户交互快捷词(全局语义规范)

PMO 在任何暂停点 / 决策点 / 推荐方案后 · 用户可用以下快捷词回复:

| 快捷词 | 等价语义 | 适用场景 |
|---|---|---|
| `ok` / `OK` | **按建议** · 同意 PMO 当前推荐方案 | 任何 PMO 给出"建议:..."/"推荐:..."的暂停点 |
| `all default` | 全部用 PMO 给的默认值 | prepare 4 项配置暂停点 |
| `继续` / `next` | 继续推进流程(下一 stage / 下一 substep) | stage 完成后等用户拍板下一步 |
| `跳过` / `skip` | 跳过当前可选 substep / stage(若 spec 允许) | 可选 stage(如 ui_design / browser_e2e) |
| `bypass` | 触发 bypass 协议(R8 写操作硬门禁链 · 必带 --reason) | 状态机 FAIL 3 次后用户拍板逃生 |
| `回 dev` / `回 X stage` | jump-to-stage --to X(必带 reason) | pm_acceptance rejected / 用户主动回退 |

**PMO 行为约束**:
- 看到 `ok` → 视作"按当前推荐建议执行" · 不再二次确认 · 直接走推荐路径
- 看到 `ok` 时 PMO 必复述"按建议执行 · <推荐方案的 1 行摘要>" + 立即执行
- 不可把 `ok` 解读为"用户没看清楚 · 我再问一次" · 这是用户已读 + 信任 PMO 的最短确认

---

## PMO 软约束 + 暂停点标准格式(state.py 不物化 · PMO 必自觉)

state.py 物化了 9 红线中 8 条(可枚举校验)· 1 条(R3)+ 部分行为约束(R4 / R5(b) / bypass)是 PMO 主对话内的软约束 · 必须 PMO 自觉:

### R3 · PMO 统一承接

所有用户输入 PMO 先承接 · 禁止 RD/Designer/PM 等角色直接响应。
多角色对话场景下 · 用户输入直接打 RD = 角色越权(RD 直接接需求跳过 PM 的 PRD)。

### R4 · 流程边界

- **不简化**:每种需求走对应级别的完整流程 · "简单/文件少/无风险" 不构成跳过理由
- **不膨胀**:自动流转节点禁止插入暂停 · "回合边界/容量预算/让用户看进度" 不构成暂停理由
- **必给步骤描述**:选定流程类型后必须给完整步骤(stage 链 + 每个 stage 大致做什么 + 预期产出)

### R5(b) 暂停点标准格式 🔴

**PMO 任何需要用户确认的点都用此模板**:

```
⏸️ <情境 1 句>

请选择:

1. **<选项 1 标题>** 💡 推荐
   理由: <1-2 句为什么推荐>
   动作: <选了之后 PMO 会做什么>

2. **<选项 2 标题>**
   理由: <1-2 句>
   动作: <PMO 会做什么>

3. **<其他指示>**(可选 · 让用户自由输入)

📚 决策参考(若适用):<相关 spec / 文件 / 上游 case 路径>
```

**红线**:
- 不可省略**编号**(用户要打字 = 心智负担)
- 不可省略 **💡 推荐**(用户被迫现做决策)
- 不可省略**理由**(用户不知为什么选这个)
- 单选 → 1/2/3 · 多决策 → 1A/2B
- 用户回 `ok` = **选 💡 推荐项**(详 §"用户交互快捷词")

### bypass 协议(R8 写操作硬门禁链 · 逃生通道)

PMO 重试 3 次仍 FAIL → 暂停点询问用户 → bypass:

```bash
state.py xx-start --bypass --reason "<用户提供>" --user-confirmed --missing <ids>
```

state.py 校验:
- `--user-confirmed` 必带(防 AI 自决 · 红线违规拦截)
- `--missing` 覆盖实际 missing(防漏报)
- 通过 + 自动写 `bypass_log[]` + `concerns WARN`(完整审计闭环)

**物化语义**:state.py 无法物理验证"用户真的说了" · 但此 flag 的存在性 = AI 声称用户已确认。审计时若发现 AI 自加此 flag(对话历史无用户确认)= 红线违规。

详细 9 红线设计 rationale 见 [docs/v8-redesign/00-MANIFESTO.md § 十一](./docs/v8-redesign/00-MANIFESTO.md)。

---

## Triage · 入口规范(5 mode 分诊 + audit_line + 移交)

> triage 是 PMO 入口行为 · 不是 state.py 命令 · 不是 stage。
> 入口完成 → 按 mode 移交(B → prepare 子流程 / A/D/E 闭合 / C jump 状态机)。

### 5 mode 分诊(关键词表)

| Mode | 触发关键词 | 行为 | 移交去向 | 入口完成标志 |
|------|----------|------|---------|-------------|
| **A · query** | 看下 / 查 / why / 排查 / 解释 | grep + Read 答 + 跟进引导 | — 主对话闭合 | 答完 + 跟进引导给到用户 |
| **B · execute** | 实现 / 修复 / 改 / 做 / 开发 / 新增 | audit_line · 识别为 execute 意图 | → **prepare 子流程**([docs/prepare.md](./docs/prepare.md)) | audit_line 输出 + 移交 prepare |
| **C · resume** | 继续 / resume / ship F032 | 找 state.json + jump 到 current_stage | → 状态机(直接跳 · 不重 init) | state.json 已读 + current_stage 已 jump |
| **D · status** | status / 现在到哪 / 看板 | 加载 Feature 看板 + 输出 | — 主对话闭合 | 看板 markdown 已输出 |
| **E · discuss** | 我感觉 / 你怎么看 / X vs Y / 哪种更合理 | 综合视角讨论 + 选项 + 推荐 | — 主对话闭合(讨论收敛后用户升级到 B → prepare) | 讨论收敛 · 用户给出方向或升级到 B |

### audit_line(PMO 主对话首条响应必含)

```
🔍 triage: mode=<A/B/C/D/E>(<name>) reason=<判定理由>
```

例:`🔍 triage: mode=B(execute) reason=识别为 Feature 流程 · 命中关键词 /^实现/`

**用户监督**:用户看到 audit_line 知道 PMO 真做了分诊 · 不是直接跳过去做事。

### Mode E 升级触发(PMO 主动建议 · 不等用户提)

命中以下场景必须在收尾时建议升 mode B:
- 讨论涉及**多 Feature 范围拆分** / **ROADMAP 更新** / **P0/P1 优先级排序** → 建议升 **Feature Planning**(走 PROJECT/ROADMAP/sitemap · 非散述清单)
- 讨论涉及**新功能实现方向** / **架构决策点** → 建议升 **Feature**(走 goal PRD 而非主对话伪 PRD)
- 讨论涉及**已知 bug 根因 + 修复方案** → 建议升 **Bug**

```
📎 建议升级到 mode B · <flow_type>:本次讨论已涉及 <触发场景> ·
   建议进 <flow_type> 流程(走 <first_stage> stage 产 <artifact>)以保证 R6/多视角 review 闭环。
   回复 "进 <flow_type>" 升级 · 或继续讨论。
```

### Mode B 必移交 prepare 子流程

mode B 识别后(**无论后续 flow_type = Feature / 敏捷需求 / Bug / Micro · 都走 prepare**)·
PMO **必走** [docs/prepare.md](./docs/prepare.md) · 不可在主对话散述准备步骤。

判据:**进状态机 = 走 prepare**(4 个进状态机流程都需 worktree + branch + merge_target + Feature/Bug ID 4 项配置)。
即便最轻的 Micro(改文案 1 行)也要 prepare · 不可跳过。
不进状态机的 Feature Planning / 问题排查 → 不走 prepare(由 PMO 主对话执行)。

prepare 子流程动作概览:流程类型识别 → worktree 决策 → emit 4 项暂停点 → 用户确认 → PMO 跑 git worktree add + cd → state.py init-feature。

### 待规划需求池(命中查询意图时扫描)

🔴 **触发条件**:mode A query 关键词命中以下任一时 · PMO 扫 `teamwork-space.md § 待规划需求池` 列 status=📝/🔄 的项:
- "待做 / 待规划 / pending / backlog / 待办"
- "还有什么 / 还要做 / 接下来做什么 / 下一个"
- "看下池子 / 看下待规划"

emit 格式:
```
📋 待规划需求池:N 个 active 项(详 teamwork-space.md § 待规划需求池)
1. PENDING-NNN · <标题>(来源:<source> · 状态:📝/🔄)
2. ...
回 "启动 PENDING-NNN" → 进 prepare 子流程 · 或 "稍后" 闭合。
```

**不扫场景**:mode B/C/D/E 入口(用户没问 → 不主动 emit)/ 关键词不命中 / 池空 → silent skip(避免噪音)。

**追加机制**(session 内发现新待规划项):PMO/RD/PM 在 stage 内识别"本 Feature 范围外但要做"→ 主对话内 append 到表(用户确认后落盘)。

**闭环清理**(防池臃肿):PENDING-NNN 转 ✅ 已转(进 Feature/Bug)或 ❌ 不做 → **立即从表删** · 关联落对应 Feature `state.json.related_pending` audit。表始终只保留 active(📝/🔄)。

### 入口红线 R-T1/2/3

- **R-T1 · PMO 必先分诊**:承接任何用户输入 · 必先完成 5 mode 分诊 + audit_line · 不可跳过直接 init-feature / stage-start
- **R-T2 · mode B 必移交 prepare**:triage 自身只做 mode 分诊 · 不做流程类型识别 / worktree 决策 / 暂停点(都是 prepare 的事)· 不可自己跑 git worktree add / init-feature
- **R-T3 · resume(mode C)不重 init**:mode C 是 jump 到现有 state.json · 不可重跑 init-feature;state.json 不存在 → 退回 mode B

### 入口与状态机的接口(triage 边界)

**triage 入口完成 = init-feature 前置满足**:
- ✅ worktree 物理已创建(PMO 显式跑)
- ✅ cwd 在 worktree 内(PMO 显式 cd)
- ✅ Feature ID + branch + merge_target 已用户确认

📎 项目级骨架(KNOWLEDGE/TROUBLESHOOTING/GLOSSARY)由 init-feature 自动维护 · 不是 triage 职责。

**init-feature 拒绝条件**(状态机入口物化拦截):
- worktree_mode != off 但 cwd 不在 worktree → FAIL(P0-3 沿用)
- worktree_mode != off 但 worktree 物理不存在 → FAIL(P0-2 沿用 stage-start 校验)

**triage 不做的事**(职责边界 · 防越权):
- ❌ 不写 state.json(由 init-feature 创建)
- ❌ 不创建 worktree(由 PMO 显式跑 git worktree add)
- ❌ 不自动跑 git(防 PMO 漏看用户确认)

### 错误处理

- mode 判定不准 → PMO 告诉用户重判 · 或人工指定(用户回"应该是 mode E 讨论")
- worktree 决策错 / git worktree add 失败 / 用户拒绝 4 项默认值 → 详 [docs/prepare.md § 错误处理](./docs/prepare.md)

---

## 6 流程类型(R 红线闭集)

| 流程 | 适用场景 | 产出 |
|------|---------|------|
| **Feature** | 完整功能 | 代码 + 文档 + 测试 |
| **Bug** | 缺陷修复 | 修复 + BUG 报告 + 回归测试 |
| **Micro** | 零逻辑改动 | 代码直改(文案/样式/资源/配置) |
| **敏捷需求** | ≤5 文件 + 无 UI/架构变更 + 方案明确 | 代码 + 简化文档 + 测试 |
| **Feature Planning** | 拆 ROADMAP | PROJECT.md + ROADMAP.md + sitemap.md(不出代码) |
| **问题排查** | 不出代码 · 仅定位根因 | 排查报告 + 后续 todo 关联 |

---

## 错误处理协议

```
xx-stage-start FAIL
 ↓
state.py 返回 missing_prerequisites[] · 每条带 hint
 ↓
PMO 按 hint 自动执行修复(silent)
 ↓
重跑 xx-stage-start
 ↓
 ┌── PASS → 继续
 │
 └── FAIL → 再修(最多 3 次)
 ↓
 暂停点询问用户:
 1. 继续尝试
 2. 跳过前置 · ⚠️ 风险:{state.py 评估}
 3. 其他指示
 ↓ 用户选 2
 state.py xx-start --bypass --reason ... --user-confirmed --missing ...
 ↓
 自动写 bypass_log + concerns WARN(完整审计闭环)
```

**`--user-confirmed` 物化拦截**:缺此 flag + 带 `--bypass` → state.py 立即 FAIL,防 AI 自决逃生。

---

## 项目级文档信息架构(teamwork 框架规范)

> **teamwork 要求用户项目根含以下文档** · `init-feature` 自动维护(骨架 silent 复制 · 详见下方"系统维护")。

### 文档清单 + 权威范围

| 文档 | 权威范围 | 何时 read |
|------|---------|---------|
| `PROJECT.md` | 产品全景 | 讨论产品方向 / 创建 Feature |
| `ROADMAP.md` | Feature 列表 + 优先级 + 排期 | 讨论 Feature 优先级 / 创建 Feature |
| `sitemap.md` | 信息架构 / 页面层级 | 讨论 UI / 创建含 UI 的 Feature |
| `KNOWLEDGE.md` | Gotcha / Convention / Architecture(项目级踩坑 + 约定)| triage 期 + 涉项目级约定时 |
| `GLOSSARY.md` | 业务术语 + 实体关系 + 命名约定 + 别名歧义 | PM 起草 PRD 前 / RD 起草 TECH 前 |
| `TROUBLESHOOTING.md` | 排查 / 运维操作手册(log / DB / 监控 / 部署)| mode A query / E discuss 涉"排查 / 报错 / 查 log" |
| `docs/architecture/ARCHITECTURE.md` | 系统架构 | 讨论架构决策 |
| `docs/architecture/database-schema.md` | 数据库 schema | 讨论数据模型 |

### 按场景路由速查(PMO 任意时刻)

| 用户提到 | PMO 内部 read |
|--------|------------|
| 产品方向 / Feature 排期 / Roadmap | `PROJECT.md` / `ROADMAP.md` |
| 页面层级 / UI 整体 / 信息架构 | `sitemap.md` |
| Convention / 命名 / 约定 / Gotcha / 踩坑 | `KNOWLEDGE.md` |
| 业务术语 / 实体关系 / 别名 | `GLOSSARY.md` |
| **报错 / 502 / 查 log / 排查 / 异常 / 服务挂了 / 查环境 / 查 DB / 查 Redis / 部署 / 回滚** | **`TROUBLESHOOTING.md`** |
| 架构 / 数据库 / schema | `docs/architecture/` |
| F\d+(具体 Feature 编号) | `docs/features/{F}/` |
| 历史决策 / ADR | `docs/features/*/adrs/INDEX.md` |
| 多子项目 / 跨项目 | `teamwork-space.md` |
| 涉及具体代码 | grep + Read 实际代码 |

### 项目级系统维护(`tools/bootstrap.py` 独立脚本)

**每个 session 启动时 · PMO 首条响应前必跑**(silent · 不打扰用户)。
**独立脚本 · 不归 state.py 状态机域**(职责分离):

```bash
python3 <SKILL_ROOT>/tools/bootstrap.py \
 --host <claude-code|codex-cli|gemini-cli|unknown> \
 --skill-root <SKILL_ROOT 绝对路径> \
 --skill-version <SKILL.md frontmatter version>
```

`bootstrap.py` 做什么(silent · 不打扰用户):
- SKILL_VERSION 一致性校验
- 项目骨架检查/创建(KNOWLEDGE/TROUBLESHOOTING/GLOSSARY · 不存在则 silent 复制 templates/)
- CLAUDE.md / AGENTS.md / GEMINI.md 注入段检查(对接 sync-drift.py)
- state.json v7 → v8 迁移扫描

**设计原则**:
- 全 silent · 不 emit 用户可见报告
- 失败不阻塞(WARN/INFO 内部记录)
- 幂等(重复跑无副作用)
- AI 跑后不必 cite(audit 在内部 JSON · 不强制复制给用户)
- **独立脚本 · 不混入 state.py**(state.py 只管状态机)

PMO 只关注流程编排 · 系统维护是 `bootstrap.py` 的职责。

详细 PMO 入口行为见 [SKILL.md § Triage 入口规范](./SKILL.md)。

### session 入口必读 · 项目结构索引(silent · bootstrap.py 后 / mode 分诊前)

🔴 PMO bootstrap.py 完成后 · 进 mode 分诊前 · **必 silent Read `teamwork-space.md`**(存在即读 · 缺失 silent skip):

- 项目结构(单/多子项目) · 子项目清单 · 跨项目变更 ID · § 待规划需求池

**为什么只读这一份**:teamwork-space.md 是轻量结构索引(通常 < 200 行)· 已含分诊所需的全景上下文。
**PROJECT.md / ROADMAP.md / sitemap.md** 等详档**按需读**(用户提到 / 任务涉及时再 Read 对应段)· 不全文加载到 PMO 上下文(避免 context 浪费)。

**读法**:silent · 不 emit · 内化为 PMO 上下文 · 用到时引(如 "按 teamwork-space.md 子项目清单 · SVC-CORE 下一 F024")。

### silent read 原则

- ✅ 内部 read · 不输出过程
- ✅ 仅读相关段 · 不全扫整个文件
- ❌ 不输出 "我现在 read X 看看"

详细 silent execution 规范见 [SKILL.md § Triage 入口规范](./SKILL.md) 入口部分。

---

## 状态行(R5 软约束)

**AI 每次主对话回复(在 teamwork 流程内)末尾必含状态行 · v8 3 行格式**:

```
🔄 {feature_id} ({flow_type} · {current_stage}) | 下一步:{next_action}
📁 {artifact_root}
🌿 {branch}(worktree: {wt_path · 与 artifact_root 不同时显示})
```

**示例**(占位 `{repo}` / `{Feature-ID}` · 实际路径由 prepare 子流程按 conventions.md §9-12 + `.teamwork_localconfig.json` 推导 · **AI 禁止直接抄此例字符串**):
```
🔄 {Feature-ID} (Feature · blueprint) | 下一步:dispatch QA TC + RD TECH
📁 {repo-root}/{artifact-root}/{Feature-ID}
🌿 feature/{feature-id-kebab}(worktree: {repo-root}/.worktree/{Feature-ID})
```

📎 worktree path 物化校验:init-feature 强校验 `{worktree_root_path}/{Feature-ID}` 约定 · 错位 → FAIL with hint。

**物化兜底**:
- `state.py` 每次 `xx-start` / `xx-complete` emit 顶层含 `status_line` 字段
- brief 末尾自动 append "📊 状态行模板" 段(AI 复制粘贴)
- AI 跑命令后:从 stdout JSON.status_line 拿最新
- AI 纯对话回复:用最近一次 state.py 输出的 status_line(或从 state.json 读 + render)

**反模式**(命中 = 流程偏离):
- ❌ 主对话回复无状态行
- ❌ 状态行随便写(不按 v8 2 行格式)
- ❌ 状态行的 next_action 与实际下一步不符

---

## 核心保证(对应 v7 9 红线 R1-R9)

v8 把 v7 的 9 红线中 16/17 子条目物化进 state.py · 仅 1 条(R3 PMO 统一承接)仍是软规则。

| v7 红线 | v8 归宿 |
|---------|---------|
| R1 代码写权归 RD | state.py 校验写操作时身份切换 |
| R2 流程类型闭集 | init-feature --flow-type enum |
| R3 PMO 统一承接 | 保留 AI 自决(不可枚举) |
| R4 流程边界 | state.py 按 flow_type 强制 stage 链 |
| R5 暂停点协议 | state.py emit 暂停点 markdown(强制格式) |
| R6 Planning 只出文档 | init-feature reject "Feature Planning" · PMO 主对话执行(详 docs/feature-planning.md) |
| R7 证据闭环 | xx-complete 必传 --auto-commit + 校验 commit 存在 + artifacts in changeset |
| R8 写操作硬门禁链 | state.py 内部 prepare 完成前拒绝 stage-start · ship Phase 1 CLI-first |
| R9 session bootstrap 必跑 triage | tools/bootstrap.py + PMO 按 SKILL.md § Triage 入口规范 分诊 |

详细 9 红线 rationale 见 [docs/v8-redesign/00-MANIFESTO.md § 十一](./docs/v8-redesign/00-MANIFESTO.md)。

---

## 文档导航

| 文件 | 作用 |
|------|------|
| [SKILL.md § Triage 入口规范](./SKILL.md) | **入口规范** · triage 不是 stage · 5 mode 分诊 + mode B worktree 决策 |
| [docs/v8-redesign/00-MANIFESTO.md](./docs/v8-redesign/00-MANIFESTO.md) | 设计宪法 · 范式切换 · 红线归宿 |
| [docs/v8-redesign/01-COMMAND-SCHEMA.md](./docs/v8-redesign/01-COMMAND-SCHEMA.md) | 全 30 命令精确 schema |
| [docs/v8-redesign/02-CLEANUP.md](./docs/v8-redesign/02-CLEANUP.md) | v7 → v8 清理清单 |
| [docs/v8-redesign/03-MIGRATION.md](./docs/v8-redesign/03-MIGRATION.md) | 迁移路线图 |
| [docs/v8-redesign/00-MANIFESTO.md § 十一](./docs/v8-redesign/00-MANIFESTO.md) | 9 红线归宿 + 详细 rationale |
| [FLOWS.md](./FLOWS.md) | 6 流程 telos(详细步骤进 docs/prepare.md 子流程 + 各 stage brief) |
| [ROLES.md](./ROLES.md) | 角色索引(→ roles/*.md) |
| [STANDARDS.md](./STANDARDS.md) | 技术规范索引(→ standards/*.md · 不含流程规范) |
| [TEMPLATES.md](./TEMPLATES.md) | 文档模板索引 |
| [stages/*.md](./stages/) | 各 stage Telos + Output Contract(校验进 state.py) |
| [roles/*.md](./roles/) | 角色 telos + 创作要点(协作进 state.py) |
| [standards/*.md](./standards/) | 技术规范(common/backend/frontend/tdd · 流程规范已删) |
| [tools/state.py](./tools/state.py) | 唯一编排器入口 |
| [tools/_v8_engine.py](./tools/_v8_engine.py) | 通用 stage start/complete + bypass 引擎 |
| [tools/_v8_stage_specs.py](./tools/_v8_stage_specs.py) | 10 stage 完整契约 |
| [tools/_v8_ship.py](./tools/_v8_ship.py) | ship-phase 5 actions |
| [tools/_v8_migrate.py](./tools/_v8_migrate.py) | v7 → v8 迁移 |
| [tools/bootstrap.py](./tools/bootstrap.py) | session 启动维护(骨架 / hooks / 注入段) |
| [docs/CHANGELOG.md](./docs/CHANGELOG.md) | 完整变更记录 |

---

## License

MIT
