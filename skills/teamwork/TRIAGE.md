# TRIAGE · 入口规范

> **triage 是 PMO 入口行为 · 不是 state.py 命令 · 不是 stage**。
> 入口完成 + 用户确认 worktree → 才进状态机层(init-feature 起)。

---

## 1. 入口规范的本质

```
┌─ 入口规范(TRIAGE · 本文件) · PMO 主对话行为 ────────────┐
│ PMO 承接用户输入 │
│ → 5 mode 分诊(PMO 按关键词表判定) │
│ → 输出 audit_line(PMO 自己写 · 用户监督) │
│ → mode B 时: │
│ · 流程类型识别(PMO 按关键词表) │
│ · worktree 决策 │
│ · 暂停点(PMO 复制模板给用户) │
│ → 用户确认 → PMO 显式 git worktree add + cd │
└────────────────────────────────────────────────────────────┘
 ↓ 进状态机(worktree 已在 · cwd 已在 worktree 内)
┌─ 状态机层(state.py 唯一域) ──────────────────────────────┐
│ init-feature(自动维护项目级骨架 · silent) │
│ · stage 链 · ship · completed │
└────────────────────────────────────────────────────────────┘
```

📎 **项目级系统维护**(骨架文档创建 / CLAUDE.md 注入段同步 / SKILL_VERSION 校验 / 版本迁移)
 全部由 Python 工具维护 · 在 init-feature 内 silent 做 · PMO 不关心。

**关键约束**:
- triage 不写 state.json(state.json 由 init-feature 创建)
- triage 不创建 worktree(由 PMO 在用户确认后显式执行)
- triage 不进 LEGAL_STAGES(因为不是 stage)
- triage **没有 state.py 命令**
- triage 是 PMO 行为 · 按本文档规范做

---

## 2. 5 Mode 分诊(关键词表)

| Mode | 触发关键词 | 行为 | 是否进状态机 |
|------|----------|------|-------------|
| **A · query** | 看下 / 查 / why / 排查 / 解释 | grep + Read 答 + 跟进引导 | ❌ |
| **B · execute** | 实现 / 修复 / 改 / 做 / 开发 / 新增 | 见 §3 完整子流程 | ✅(经用户确认 worktree)|
| **C · resume** | 继续 / resume / ship F032 | 找 state.json + jump 到 current_stage | ✅(直接跳 · 不重 init)|
| **D · status** | status / 现在到哪 / 看板 | 加载 Feature 看板 + 输出 | ❌ |
| **E · discuss** | 我感觉 / 你怎么看 / X vs Y / 哪种更合理 | 综合视角讨论 + 选项 + 推荐 | ❌(讨论收敛后用户升级到 B)|

🔴 **mode E 升级触发**(PMO 主动建议 · 不等用户提)·命中以下场景必须在收尾时建议升 mode B:
- 讨论涉及**多 Feature 范围拆分** / **ROADMAP 更新** / **P0/P1 优先级排序** → 建议升 **Feature Planning**(PMO 主对话按 [docs/feature-planning.md](./docs/feature-planning.md) 起 PROJECT/ROADMAP/sitemap · 而非散述清单)
- 讨论涉及**新功能实现方向** / **架构决策点** → 建议升 **Feature**(走 goal PRD 而非主对话伪 PRD)
- 讨论涉及**已知 bug 根因 + 修复方案** → 建议升 **Bug**

PMO 在 mode E 收尾时输出:
```
📎 **建议升级到 mode B · <flow_type>**:本次讨论已涉及 <触发场景>,建议进 <flow_type> 流程(走 <first_stage> stage 产 <artifact>)以保证 R6/多视角 review 闭环。
回复 "进 <flow_type>" 升级 · 或继续讨论。
```

---

## 3. audit_line(PMO 主对话首条响应必含)

PMO 完成 5 mode 分诊后 · 在主对话首条响应中输出:

```
🔍 triage: mode=B(execute) reason=识别为 Feature 流程 · 命中关键词 /^实现/
```

格式:`🔍 triage: mode=<A/B/C/D/E>(<name>) reason=<判定理由>`

**用户监督**:用户看到 audit_line 知道 PMO 真做了分诊 · 不是直接跳过去做事。

---

## 4. Mode B 子流程(核心 · PMO 按以下步骤做)

### Step 4.0 · session 入口必跑 bootstrap.py(silent)

**PMO 主对话首条响应前必跑**(任何 mode · 不止 B):

```bash
python3 <SKILL_ROOT>/tools/bootstrap.py \
 --host claude-code \
 --skill-root <SKILL_ROOT 绝对路径> \
 --skill-version <SKILL.md frontmatter version>
```

- **独立脚本 · 不归 state.py 域**(职责分离)
- silent · 不打扰用户
- 系统维护(骨架 / 版本 / 注入段 / v7 扫描)自动做
- 失败不阻塞 · PMO 跑后直接进入 mode 分诊
- 不需要 cite 输出(audit 在 stdout JSON · 不强制复制)

详见 [SKILL.md § 项目级系统维护](./SKILL.md)。

### Step 4.1 · 流程类型识别(6 闭集 · R2 红线)

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

### Step 4.2 · worktree 决策模板

PMO 按 flow_type 算 branch 前缀 + worktree path 建议:

| flow_type | branch 前缀 | worktree |
|----------|-----------|---------|
| Feature | `feature/` | 必 |
| 敏捷需求 | `agile/` | 必 |
| Bug | `fix/` | 必 |
| Micro | `micro/` | 必 |
| Feature Planning | `plan/`(可选) | 可选 · 由 PMO 主对话执行 · 不进状态机 |
| 问题排查 | — | 不进 stage · 类似 mode A query |

**worktree path 默认** = `{worktree_root_path}/{Feature-ID}` ·
其中 `worktree_root_path` 解析顺序:
1. `state.json.environment_config.worktree_root_path`(已存在 Feature)
2. 项目根 `.teamwork_localconfig.md` 的 `worktree_root_path` 字段
3. 默认 `.worktree`(项目根子目录)

完整规范见 [docs/conventions.md § 9-11](./docs/conventions.md)。

### Step 4.3 · emit 暂停点 markdown(PMO 复制给用户)

```markdown
⏸️ 进入流程前请确认 4 项:

📋 **流程类型**:<flow_type>
📋 **理由**:<识别理由>
📋 **首个 stage**:<first_stage>

请提供:
1. **Feature ID**(如 PTR-F033-Credit-Note-Adjustment · 编号规则见 [docs/conventions.md § 1](./docs/conventions.md))
2. **merge_target**(如 staging / main)
3. **worktree path**(默认:`{worktree_root_path}/<FEATURE-ID>` · 见 [docs/conventions.md § 9](./docs/conventions.md))
4. **branch**(默认:`<branch-prefix><FEATURE-ID>`)

回复 4 项或 "all default" 用默认值(仅需 Feature ID + merge_target)

📎 **是否需要 UI Design Stage** 由 goal-complete 时 `--needs-ui` 决策(P0-6)·
 triage 入口不强制提前拍板。
```

flow_type → first_stage 映射:
- Feature / 敏捷需求 → `goal`
- Bug / Micro → `dev`
- **Feature Planning** → 不进 stage 链 · PMO 主对话按 [docs/feature-planning.md](./docs/feature-planning.md) 执行
- **问题排查** → 不进 stage 链 · 类似 mode A query

### Step 4.4 · 用户确认后 · PMO 显式执行

```bash
# 用户回(或 all default):
# 1. Feature ID: PTR-F033
# 2. merge_target: staging
# 3. worktree path: <repo>/worktrees/PTR-F033
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

---

## 5. 入口与状态机的接口

**triage 入口完成 = init-feature 前置满足**:
- ✅ worktree 物理已创建(PMO 显式跑)
- ✅ cwd 在 worktree 内(PMO 显式 cd)
- ✅ Feature ID + branch + merge_target 已用户确认

📎 项目级骨架(KNOWLEDGE/TROUBLESHOOTING/GLOSSARY)由 init-feature 自动维护 · 不是 triage 职责。

**init-feature 拒绝条件**(状态机入口物化拦截):
- worktree_mode != off 但 cwd 不在 worktree → FAIL(P0-3 沿用)
- worktree_mode != off 但 worktree 物理不存在 → FAIL(P0-2 沿用 stage-start 校验)

**triage 不做的事**:
- ❌ 不写 state.json
- ❌ 不创建 worktree(由 PMO 显式跑)
- ❌ 不自动跑 git(防 PMO 漏看用户确认)

---

## 6. 入口红线

### R-T1 · PMO 必先按本文档分诊

PMO 承接任何用户输入 · **必先按 TRIAGE.md 入口规范完成 5 mode 分诊** · 不可直接跳 init-feature / 任何 stage-start。

### R-T2 · mode B 必经用户确认

mode B 输出暂停点后 · 必须等用户明确回 4 项配置(或 "all default")。
**不可** PMO 自己拍板 worktree path / branch / merge_target。

### R-T3 · 入口完成才进状态机

PMO 在用户未确认前 · **不可** cd / git worktree add / init-feature。
违规 = 主 tree 污染风险(实证 PTR-F033 case)。

### R-T4 · resume(mode C)不重 init

mode C 是 jump 到现有 state.json · **不可** 重跑 init-feature。
若 state.json 不存在 → 退回 mode B。

---

## 7. 各 mode 的"入口完成"定义

| Mode | 入口完成的标志 |
|------|--------------|
| A | grep + Read 答完 + 跟进引导给到用户 |
| B | state.json 在 worktree 内已落 + current_stage 已设(由 init-feature 完成)|
| C | state.json 已读 + current_stage 已 jump |
| D | 看板 markdown 已输出给用户 |
| E | 讨论收敛 · 用户给出明确方向或升级到 B |

入口完成后:
- A/D/E · 入口闭合 · PMO 等下一轮用户输入
- B/C · 进状态机 · 走 stage 链(state.py 主导)

---

## 8. 错误处理

### 8.1 · triage 模式识别错(mode 判定不准)

PMO 觉得分诊错 → 直接告诉用户重判 · 或人工指定(用户回"应该是 mode E 讨论")。

### 8.2 · 用户拒绝 worktree 默认值

用户提供 4 项中部分值 · 部分 default → PMO 用混合值跑 git worktree add。
用户全否决 → 等用户提供完整 4 项后再推进。

### 8.3 · git worktree add 失败

- branch 已存在 → `git worktree remove <path>` + `git branch -D <branch>`
- origin/base 不存在 → `git fetch origin`
- path 已存在但非 worktree → 删 path 或换 path

错误处理由 PMO 主导 · 不在 state.py 状态机里。

---

## 9. 相关文档

- [SKILL.md](./SKILL.md) — 顶层叙事 + 项目级文档信息架构
- [RULES.md](./RULES.md) — 9 红线 rationale
- [FLOWS.md](./FLOWS.md) — 6 流程 telos
- [docs/v8-redesign/00-MANIFESTO.md](./docs/v8-redesign/00-MANIFESTO.md) — 设计宪法
- [docs/v8-redesign/04-PAUSE-POINT-DISCIPLINE.md](./docs/v8-redesign/04-PAUSE-POINT-DISCIPLINE.md) — 暂停点纪律
