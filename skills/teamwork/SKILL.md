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
v7(被替换):                         v8:
PMO 凭记忆 + 读 spec markdown          AI 跑 state.py xx-start
       ↓                                     ↓
按记忆调度 stage / role                state.py 主动校验 + 主动告知
       ↓                                     ↓
state.py 被动记录                       AI 按 state.py 指示执行
                                             ↓
                                        AI 跑 state.py xx-complete
                                             ↓
                                        state.py 校验产物 + 自动转下一 stage
```

---

## 快速开始

```bash
# 1. session 入口 · PMO 按 TRIAGE.md 入口规范分诊(v8.0+P0-12 · 不是 state.py 命令)
#    - 5 mode 判定(A query / B execute / C resume / D status / E discuss)
#    - mode B → 项目级骨架检查/创建 + 流程类型识别 + worktree 决策
#    - 输出 audit_line + 暂停点 markdown 给用户

# 2. 用户确认 4 项配置后 · PMO 显式执行(主工作区 cwd):
git fetch origin
git worktree add -b <branch> <worktree-path> origin/<merge-target>
cd <worktree-path>

# 3. 此刻 cwd 在 worktree 内 · 进入状态机层(state.py 唯一域)
state.py init-feature --feature <feature-dir-in-worktree> ...

# 3. 各 stage 走 -start / -complete
state.py goal_plan-start --feature <path>
# ... AI 按 next_action_brief 完成 stage 工作 ...
state.py goal_plan-complete --feature <path> --auto-commit <hash> --artifacts ...
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

## 命令清单(state.py 30 个命令)

```
A 类 · 状态机入口(用户确认 worktree 后 · 在 worktree 内运行)
└── init-feature       创建 Feature state.json(在 worktree 内)

(triage 是 PMO 入口行为 · 不是 state.py 命令 · 见 TRIAGE.md · v8.0+P0-12)

B 类 · Stage 流转(23 = 11 stage × 2 + ship-phase)
├── goal_plan-start / goal_plan-complete
├── ui_design-start / ui_design-complete
├── panorama_design-start / panorama_design-complete       (Feature Planning only)
├── blueprint-start / blueprint-complete
├── blueprint_lite-start / blueprint_lite-complete         (敏捷需求 only)
├── dev-start / dev-complete
├── review-start / review-complete                          (--verdict APPROVE|NEEDS_REVISION)
├── test-start / test-complete                              (--integration/e2e-test-exit-code)
├── browser_e2e-start / browser_e2e-complete                (optional)
├── pm_acceptance-start / pm_acceptance-complete            (--decision approved_and_ship|...)
├── ship-start / ship-complete
└── ship-phase --action {sanitize|push|confirm-merged|cleanup|close-unmerged}

C 类 · 维护(6)
├── snapshot / validate / raw-read / raw-write              只读 + 逃生舱
├── recover                                                  state.json 被外部改后认证
└── migrate-v7-to-v8                                        一次性迁移老 Feature
```

详细 schema 见 [`docs/v8-redesign/01-COMMAND-SCHEMA.md`](./docs/v8-redesign/01-COMMAND-SCHEMA.md)。

---

## 5 mode 入口分诊

| Mode | 触发 | 行为 |
|------|------|------|
| A · query | 看下 / 查 / why / 排查 | 不进 stage 链 · 直接 grep/Read 答 |
| B · execute | 实现 / 修复 / 改 / 做 | 重型准备 → 流程类型识别 → 业务 stage 链 |
| C · resume | 继续 / resume / ship F032 | 找 state.json + jump 到 current_stage |
| D · status | 现在到哪 / 看板 | 加载 Feature 看板 + 输出 |
| E · discuss | 我感觉 / 你怎么看 / X vs Y | 综合视角 + 选项 + 推荐 |

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

## 项目级文档信息架构(teamwork 框架规范 · v8.0+P0-12)

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
| 多子项目 / 跨项目 | `teamwork_space.md` |
| 涉及具体代码 | grep + Read 实际代码 |

### 项目级系统维护(`tools/bootstrap.py` 独立脚本 · v8.0+P0-13)

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

详细 PMO 入口行为见 [TRIAGE.md](./TRIAGE.md)。

### silent read 原则

- ✅ 内部 read · 不输出过程
- ✅ 仅读相关段 · 不全扫整个文件
- ❌ 不输出 "我现在 read X 看看"

详细 silent execution 规范见 [TRIAGE.md](./TRIAGE.md) 入口部分。

---

## 状态行(v8.0+P0-10 · R5 软约束)

**AI 每次主对话回复(在 teamwork 流程内)末尾必含状态行 · v8 3 行格式**:

```
🔄 {feature_id} ({flow_type} · {current_stage}) | 下一步:{next_action}
📁 {artifact_root}
🌿 {branch}(worktree: {wt_path · 与 artifact_root 不同时显示})
```

**示例**:
```
🔄 PTR-F033 (Feature · blueprint) | 下一步:dispatch QA TC + RD TECH
📁 /Users/liam/apps/joli/aon/aon-ptr-worktrees/PTR-F033/apps/partner/docs/features/PTR-F033
🌿 feature/PTR-F033-credit-note-adjustment(worktree: /Users/liam/apps/joli/aon/aon-ptr-worktrees/PTR-F033)
```

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
| R6 Planning 只出文档 | panorama_design-complete 拒绝代码 artifact |
| R7 证据闭环 | xx-complete 必传 --auto-commit + 校验 commit 存在 + artifacts in changeset |
| R8 写操作硬门禁链 | state.py 内部 prepare 完成前拒绝 stage-start · ship Phase 1 CLI-first |
| R9 init_triage 必跑 | state.py triage 整合 |

完整红线设计 rationale 见 [`RULES.md`](./RULES.md)。

---

## 文档导航

| 文件 | 作用 |
|------|------|
| [TRIAGE.md](./TRIAGE.md) | **入口规范**(v8.0+P0-5)· triage 不是 stage · 5 mode 分诊 + mode B worktree 决策 |
| [docs/v8-redesign/00-MANIFESTO.md](./docs/v8-redesign/00-MANIFESTO.md) | 设计宪法 · 范式切换 · 红线归宿 |
| [docs/v8-redesign/01-COMMAND-SCHEMA.md](./docs/v8-redesign/01-COMMAND-SCHEMA.md) | 全 30 命令精确 schema |
| [docs/v8-redesign/02-CLEANUP.md](./docs/v8-redesign/02-CLEANUP.md) | v7 → v8 清理清单 |
| [docs/v8-redesign/03-MIGRATION.md](./docs/v8-redesign/03-MIGRATION.md) | 迁移路线图 |
| [RULES.md](./RULES.md) | 9 红线 rationale(只讲 why · 校验进 state.py) |
| [FLOWS.md](./FLOWS.md) | 6 流程 telos(详细步骤进 state.py prepare/各 stage brief) |
| [ROLES.md](./ROLES.md) | 角色索引(→ roles/*.md) |
| [STANDARDS.md](./STANDARDS.md) | 技术规范索引(→ standards/*.md · 不含流程规范) |
| [TEMPLATES.md](./TEMPLATES.md) | 文档模板索引 |
| [stages/*.md](./stages/) | 各 stage Telos + Output Contract(校验进 state.py) |
| [roles/*.md](./roles/) | 角色 telos + 创作要点(协作进 state.py) |
| [standards/*.md](./standards/) | 技术规范(common/backend/frontend/tdd · 流程规范已删) |
| [tools/state.py](./tools/state.py) | 唯一编排器入口 |
| [tools/_v8_engine.py](./tools/_v8_engine.py) | 通用 stage start/complete + bypass 引擎 |
| [tools/_v8_stage_specs.py](./tools/_v8_stage_specs.py) | 11 stage 完整契约 |
| [tools/_v8_ship.py](./tools/_v8_ship.py) | ship-phase 5 actions |
| [tools/_v8_init.py](./tools/_v8_init.py) | triage + prepare |
| [tools/_v8_migrate.py](./tools/_v8_migrate.py) | v7 → v8 迁移 |
| [docs/CHANGELOG.md](./docs/CHANGELOG.md) | 完整变更记录 |

---

## License

MIT
