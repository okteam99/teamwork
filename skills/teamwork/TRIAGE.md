# TRIAGE · 入口规范

> **triage 是 PMO 入口行为 · 不是 state.py 命令 · 不是 stage**。
> triage 入口完成 → 按 mode 移交(B → prepare 子流程 / A/D/E 闭合 / C jump 状态机)。

---

## 1. 入口规范的本质

```
┌─ 入口规范(TRIAGE · 本文件) · PMO 主对话行为 ────────────┐
│ PMO 承接用户输入                                           │
│   → 5 mode 分诊(PMO 按关键词表判定)                      │
│   → 输出 audit_line(PMO 自己写 · 用户监督)               │
│   → 按 mode 移交去向:                                     │
│       · A query / D status / E discuss → 主对话闭合       │
│       · B execute → prepare 子流程(详 docs/prepare.md)  │
│       · C resume → 直接 jump 状态机(已有 state.json)    │
└────────────────────────────────────────────────────────────┘
 ↓ (mode B 路径 · prepare 子流程 · 不是 triage 范围)
┌─ prepare 子流程(docs/prepare.md) · PMO 主对话行为 ───────┐
│ 流程类型识别 → worktree 决策 → 暂停点 → 用户确认 →        │
│ PMO 显式 git worktree add + cd                              │
└────────────────────────────────────────────────────────────┘
 ↓ 进状态机(worktree 已在 · cwd 已在 worktree 内)
┌─ 状态机层(state.py 唯一域) ──────────────────────────────┐
│ init-feature → stage 链 → ship → completed                 │
└────────────────────────────────────────────────────────────┘
```

📎 **项目级系统维护**(骨架文档创建 / CLAUDE.md 注入段同步 / SKILL_VERSION 校验 / 版本迁移)
 全部由 Python 工具维护(`tools/bootstrap.py` session 启动 silent)· PMO 不关心。

**关键约束(triage 自身)**:
- triage 不写 state.json(state.json 由 init-feature 创建)
- triage 不识别流程类型 / 不做 worktree 决策 / 不收 4 项配置(都是 prepare 的事)
- triage 不进 LEGAL_STAGES(因为不是 stage)
- triage **没有 state.py 命令**
- triage 是 PMO 行为 · 仅做 5 mode 分诊 + audit_line + 移交

---

## 1.5 入口必读 · 项目全景认知(silent · session 启动一次性建立)

🔴 **PMO 完成 §4.0 bootstrap.py 后 · mode 分诊前必读以下项目级全景档(存在即读 · 缺失 silent skip)**:

| 文档 | 路径 | 读什么 | 缺失时 |
|---|---|---|---|
| **teamwork_space.md** | 项目根 | 项目结构(单/多子项目) · 子项目清单 · 跨项目变更 ID · § 待规划需求池 | silent skip(可能是单项目无全景档) |
| **PROJECT.md** | 项目根 / 子项目根 | 业务架构 · 执行手册 · 关键决策 | silent skip(可能项目早期未建) |
| **ROADMAP.md** | 项目根 / 子项目根 | BL 列表 · 当前/下一/储备 Feature | silent skip(无 Feature Planning) |

**为什么必读**:
- 后续 mode 分诊(关键词 → flow_type)需要项目结构上下文(单项目 vs 多子项目 → 路径/编号规则不同)
- prepare §2.1 复杂度升级判据(跨独立部署服务 / ≥2 BL)需 ROADMAP/子项目清单作判断依据
- 待规划池扫描(§2.1)需先认知池在哪个 teamwork_space.md
- 避免 mode B 起 Feature 时才发现"子项目结构与假设不符" → prepare 推倒重来

**读法**(silent · 不 emit 给用户):
- Read 一次 · 内化为 PMO 主对话上下文
- 不 cite / 不复述 · 用到时引(如"按 teamwork_space.md 子项目清单 · SVC-CORE 下一 F024")

**注意**:这是认知建立 · 不是讨论。读完直接进 §2 mode 分诊。

---

## 2. 5 Mode 分诊(关键词表)

| Mode | 触发关键词 | 行为 | 移交去向 |
|------|----------|------|---------|
| **A · query** | 看下 / 查 / why / 排查 / 解释 | grep + Read 答 + 跟进引导 | — 主对话闭合 |
| **B · execute** | 实现 / 修复 / 改 / 做 / 开发 / 新增 | audit_line · 识别为 execute 意图 | → **prepare 子流程**([docs/prepare.md](./docs/prepare.md))· 由 prepare 产出 worktree 确认 + init-feature |
| **C · resume** | 继续 / resume / ship F032 | 找 state.json + jump 到 current_stage | → 状态机(直接跳 · 不重 init · 不走 prepare)|
| **D · status** | status / 现在到哪 / 看板 | 加载 Feature 看板 + 输出 | — 主对话闭合 |
| **E · discuss** | 我感觉 / 你怎么看 / X vs Y / 哪种更合理 | 综合视角讨论 + 选项 + 推荐 | — 主对话闭合(讨论收敛后用户升级到 B → prepare)|

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

## 2.1 待规划需求池(命中查询意图时扫描)

🔴 **触发条件**:mode A query 关键词命中以下任一时 · PMO 扫 `teamwork_space.md § 待规划需求池` 列 status=📝/🔄 的项:
- "待做 / 待规划 / pending / backlog / 待办"
- "还有什么 / 还要做 / 接下来做什么 / 下一个"
- "看下池子 / 看下待规划"

emit 格式:
```
📋 待规划需求池:N 个 active 项(详 teamwork_space.md § 待规划需求池)
1. PENDING-NNN · <标题>(来源:<source> · 状态:📝/🔄)
2. ...
回 "启动 PENDING-NNN" → 进 prepare 子流程 · 或 "稍后" 闭合。
```

**不扫场景**(避免噪音):
- 其它 mode B/C/D/E 入口(用户没问 → 不主动 emit)
- 关键词不命中 → silent skip
- 池空(无 📝/🔄)→ silent skip

**追加机制**(session 内发现新待规划项):
PMO/RD/PM 在 stage 内识别"本 Feature 范围外但要做"→ 主对话内 append 到 `teamwork_space.md § 待规划需求池` 表(用户确认后落盘)· 含 ID/标题/来源/目标项目/背景/状态=📝/日期。

**闭环清理机制**(防池臃肿):
- PENDING-NNN status 转 ✅ 已转(进 Feature/Bug)或 ❌ 不做 后 · **PMO 立即提示用户从表中删除**(标关联 Feature ID 到对应 Feature 的 state.json `related_pending` 字段留 audit)
- 表始终只保留 status=📝/🔄 的 active 项 · 历史不在 teamwork_space.md 沉淀
- 已转项的关联可从 Feature state.json `related_pending` 反查 · 已删项保留在 git log

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

### Step 4.1 · mode B → 必移交 prepare 子流程

mode B 识别后(**无论后续流程类型 = Feature / 敏捷需求 / Bug / Micro · 都走 prepare**)·
PMO **必走** [docs/prepare.md](./docs/prepare.md) 子流程 · 不可在主对话散述准备步骤。

判据:**进状态机 = 走 prepare**(4 个进状态机流程都需 worktree + branch + merge_target + Feature/Bug ID 4 项配置)。
即便最轻的 Micro(改文案 1 行)也要 prepare · 不可跳过(R5 暂停点协议)。
不进状态机的 Feature Planning / 问题排查 → 不走 prepare(由 PMO 主对话执行)。

prepare 子流程动作概览:
1. 流程类型识别(6 闭集 · R2 红线)
2. worktree 决策(branch 前缀 + path)
3. emit 暂停点 markdown(收集 4 项:Feature ID / merge_target / worktree path / branch)
4. 用户确认 → PMO 跑 git worktree add + cd → state.py init-feature

**prepare 是可重入子流程** · 同样适用以下场景:
- mode E discuss 收敛后升级到 mode B(见 §2 mode E 升级触发段)
- Feature Planning 完成后 · PL 拍板某个 BL-NNN 启动 Feature(同 session 内 · 不需重新 triage · 直接 prepare)
- 用户主动"启动新 Feature / Bug / Micro / 敏捷需求"的任何 PMO 入口

prepare 不调用场景:Feature Planning 流程本身 / 问题排查流程(都不进状态机)。

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

### R-T2 · mode B 必移交 prepare 子流程

triage 自身**只做 mode 分诊** · 不做"流程类型识别 / worktree 决策 / 暂停点"。
mode B 识别后 · PMO 必走 [docs/prepare.md](./docs/prepare.md) prepare 子流程 · 由 prepare 产出 worktree 确认 + 跑 init-feature。

triage 不可:
- ❌ 自己起暂停点(prepare 红线 R-P1)
- ❌ 自己拍板 worktree path / branch(prepare 红线 R-P2)
- ❌ 自己跑 git worktree add / init-feature(prepare 红线 R-P2)

### R-T3 · resume(mode C)不重 init

mode C 是 jump 到现有 state.json · **不可** 重跑 init-feature。
若 state.json 不存在 → 退回 mode B。

---

## 7. 各 mode 的"triage 入口完成"定义

triage 自身的入口完成(不含 prepare / init-feature 的事):

| Mode | triage 入口完成的标志 |
|------|--------------|
| A | grep + Read 答完 + 跟进引导给到用户 |
| B | audit_line 输出 + 移交 prepare(后续由 prepare 推进 worktree 确认 + init-feature)|
| C | state.json 已读 + current_stage 已 jump(直接进状态机 · 不走 prepare)|
| D | 看板 markdown 已输出给用户 |
| E | 讨论收敛 · 用户给出明确方向或升级到 B |

入口完成后:
- A/D/E · 入口闭合 · PMO 等下一轮用户输入
- B/C · 进状态机 · 走 stage 链(state.py 主导)

---

## 8. 错误处理

### 8.1 · triage 模式识别错(mode 判定不准)

PMO 觉得分诊错 → 直接告诉用户重判 · 或人工指定(用户回"应该是 mode E 讨论")。

📎 worktree 决策错 / git worktree add 失败 / 用户拒绝 4 项配置默认值 等错误 · 不在 triage 范围 · 详 [docs/prepare.md § 7 错误处理](./docs/prepare.md)。

---

## 9. 相关文档

- [SKILL.md](./SKILL.md) — 顶层叙事 + 项目级文档信息架构 + PMO 软约束 + 暂停点标准格式
- [FLOWS.md](./FLOWS.md) — 6 流程 telos
- [docs/v8-redesign/00-MANIFESTO.md § 十一](./docs/v8-redesign/00-MANIFESTO.md) — 9 红线归宿 + 详细 rationale
- [docs/v8-redesign/04-PAUSE-POINT-DISCIPLINE.md](./docs/v8-redesign/04-PAUSE-POINT-DISCIPLINE.md) — 暂停点纪律
