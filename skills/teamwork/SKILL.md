---
name: teamwork
version: v8.170
description: AI 协作开发一体化框架 · /teamwork 启动
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

## teamwork 业务流程架构(PMO 常驻认知)

> 从愿景到 feature 的纵向链路。**规划层不进状态机**(PMO 主对话直接做)· **执行层进状态机**(state.py 编排)。PMO 任何 triage / 规划 / 冷启动决策都以此为锚 —— 不靠"恰好读了某个 spec"。

```
规划层(PMO 主对话 · 不进状态机)
  业务架构与产品规划.md       愿景 + 执行线列表(Line N · taxonomy · 稳定 · 新线才更新)
     └─(涉 UI)UI 全景初步规划  preview-project(系统+关键页)+ sitemap(IA 地图)· 🔴 拆 WS 之前出 · = 拆 WS 的输入
        └─ WS-NN(product-overview/workstream/ · 1..N 个)
               承接 1+ 执行线 · 拆一组 feature · 全景初规 ✅/N-A + 覆盖页清单 · 完成 = feature 写入 roadmap
             └─ ROADMAP/BL-NNN   feature 原子(关联回 WS-NN)
────────── 规划→执行 交接 = 用户拍板某 BL + prepare + init-feature ──────────
执行层(state.py 状态机)
     └─ F-NNN   goal →(ui_design)→ blueprint → dev → review → test →(browser_e2e)→ pm_acceptance → ship
```

- **WS 怎么来**:WS 是 **feature-planning 流程的产物** —— "起一个 WS" = 进 feature-planning(PMO 切 Product Lead 引导/讨论 → 涉 UI 先出全景初步规划 → 据全景 + 业务目标拆 **1..N 个 feature** → 写 roadmap)· **不在流程外 ad-hoc 手搓**。
- **全景先于 WS**(涉 UI):feature-planning 在拆 WS 前先在 `{子项目}/docs/design/preview-project/` 出 **UI 全景初步规划**(design system + 关键页 · 初步 · 非每页)+ `sitemap.md`(IA 地图)· 看清产品长啥样 → feature 边界对齐 UI 结构 · 每 WS 记 `全景初规 ✅/N-A` + 覆盖页清单 · ui_design 阶段在此全景上增量扩(详 [docs/feature-planning.md](./docs/feature-planning.md) Step 5-6)。
- **进度统计** = N 个未完成 WS(规划态)+ 各子项目 ROADMAP 的 BL(执行态)· 业务架构/执行线不计入(它们是愿景 / taxonomy)。
- **能力级索引**:WS 向上 tag 执行线 · 反查得「某执行线下有哪些 WS / feature」· 业务架构**不登记 WS**(保持稳定小列表)。
- **非开发工作**(运营/推广/BD):teamwork 不跟踪 · 执行线列表留个名即可。
- 详:[PRODUCT-OVERVIEW-INTEGRATION.md](./PRODUCT-OVERVIEW-INTEGRATION.md)(规划层 · WS)· [docs/feature-planning.md](./docs/feature-planning.md)(产出 WS)。

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

# 4. Ship(v8.145:ship1 全交付在 worktree · ship2 零内容清场在主工作区)
state.py ship-start --feature <path>
state.py ship-phase --action sanitize --feature <path> ...
# 🔴 归档+规划翻牌进 feature 分支(单 commit · 随 feature MR 原子合入 · 翻牌先在 worktree 内改好):
state.py ship-phase --action archive --feature <path> --planning-artifacts <翻牌文件>|--no-planning-changes --archive-desc '<≤200 字>'
# → git push + gh/glab 创 feature MR(CLI-first)→ 记录:
state.py ship-phase --action push --feature <path> --mr-url <真实 URL> ...
# ⏸️ 提示用户合并 MR —— feature 的 ship 到此结束。合并后 cd 回主工作区:
state.py ship-finalize --feature <worktree 内 feature 路径>   # ship2:验已交付→删 worktree→净化(可重入 · 零内容)

# 5. 错误处理(state.py 主动 hint · PMO 优先按建议修)
# FAIL → 看 missing_prerequisites[*].hint → 自动修复 → 重试
# 重试 3 次仍 FAIL → 暂停点询问用户 → bypass:
state.py xx-start --bypass --reason "<用户确认理由>" --user-confirmed --missing <ids>
```

---

## worktree 纪律(🔴 红线)

🔴 **worktree 模式下 · 本 Feature 的文件写入优先用 worktree 内路径**(代码 / 文档 / 测试 / 配置):

- Feature 进 worktree 后 · **主工作区是其他并行 Feature 的基线**
- 写文件用 **worktree 内路径**(推荐绝对路径 `{worktree-path}/...`)· 不用相对路径 —— 部分宿主的 patch / 写工具不继承 shell `cwd`(如 codex `apply_patch`)· 相对路径会落到主工作区
- **违反后果**:主工作区被污染 → 改动串入其他并行 Feature / 主分支变脏 / 难追溯 —— 并行开发的硬隔离被破坏
- 🔴 **确需写入主工作区的** · **须先经用户确认**(R5 暂停点)· 不可 AI 自决(注:v8.145 起 ship2 零内容 · 不写主工作区任何文件 —— 副产物自动 commit 属清理非内容 · 无需此例外)
- **物化兜底**:`xx-complete` 时 state.py 检测主工作区是否冒出本 Feature 文件 → 命中写 `concerns WARN` + emit `main_tree_pollution` —— 但这是**事后兜底** · AI 应**事前**就把文件写在 worktree 内
- 改完文件在 worktree 内 `git add -A {feature_dir}/` + commit(详 ship-stage.md R-S7)
- 🔴 **浏览器「看一眼」验证截图 → 系统临时目录**(`${TMPDIR:-/tmp}/teamwork/<feature_id>/screenshots/`)· **绝不落 worktree / 主工作区根**(预览自检 / UI 核对的一次性截图 · 非交付 · 不 commit · 详 [conventions §12.5](./docs/conventions.md))· browser_e2e **证据**截图例外(交付物 · 落 `<feature_dir>/screenshots/`)

worktree 路径规范见 [docs/conventions.md §9-12](./docs/conventions.md)。

---

## 命令清单(state.py ≈ 40 命令 · 详 `state.py --help`)

```
A 类 · 状态机入口(用户确认 worktree 后 · 在 worktree 内运行)
└── init-feature 创建 Feature state.json(在 worktree 内)

(triage 是 PMO 入口行为 · 不是 state.py 命令 · 见 SKILL.md § Triage 入口规范)
(prepare 是 PMO 主对话子流程 · 不是 state.py 命令 · 见 docs/prepare.md)

B 类 · Stage 流转(12 stage × 2 + 4 fix/retry + ship-phase/ship-finalize/main-sync)
├── goal-start / goal-complete
├── ui_design-start / ui_design-complete (optional · --needs-ui)
├── panorama_sync-start / panorama_sync-complete (conditional · ui_design --panorama-changed=true)
├── blueprint-start / blueprint-complete
├── blueprint_lite-start / blueprint_lite-complete (敏捷需求 only)
├── diagnose-start / diagnose-complete (Bug only · 根因细查+修复方案 · 用户确认后才进 dev)
├── dev-start / dev-complete
├── review-start / review-complete (--verdict APPROVE|NEEDS_REVISION) + review-fix / review-retry
├── test-start / test-complete (--integration/e2e-test-exit-code) + test-fix / test-retry
├── browser_e2e-start / browser_e2e-complete (optional · execution_hints)
├── pm_acceptance-start / pm_acceptance-complete (--decision approved_and_ship|...)
├── ship-start / ship-complete
├── ship-phase --action {sanitize|archive|push|close-unmerged}(v8.145:archive = ship1 终幕 · 归档+翻牌进 feature 分支)
├── ship-finalize  ship2 零内容清场(verify-delivered→worktree 删→main-sync)· 必在主工作区
└── main-sync --strategy {commit-push|stash-pull|skip} [--merge-target <br>]  主工作区净化(不依赖 feature)

C 类 · 维护(6)
├── snapshot(别名 status · 看当前 stage/下一步 · compact 恢复用)/ validate / raw-read / raw-write
├── recover state.json 被外部改后认证
└── migrate-v7-to-v8 一次性迁移老 Feature
```

命令现行权威 = `state.py --help` + [`tools/_v8_stage_specs.py`](./tools/_v8_stage_specs.py)(各 stage 契约)。(v8.0 命令 schema 快照已清理 · git 历史可溯)。

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

🔴 **`ok` 作用域 = 当前这一个暂停点**:
- `ok` 只确认 PMO **当前 emit 的那一个暂停点** · **不预授权后续任何暂停点**
- AI 不可把一个 `ok` 推到后续 stage —— 每个授权暂停点必**独立 emit + 独立等用户回应**
- 反例(实证):用户在 prepare 回 `ok`(只确认 4 项配置)· AI 误当成"goal PRD 确认 / ui_design UI 确认 / pm_acceptance 决策全部预授权" · 非 auto 模式下一路冲到 pm_acceptance · 跳过中间所有暂停点 = 违 R5

---

## PMO 软约束 + 暂停点标准格式(state.py 不物化 · PMO 必自觉)

state.py 物化了 9 红线中 8 条(可枚举校验)· 1 条(R3)+ 部分行为约束(R4 / R5(b) / bypass)是 PMO 主对话内的软约束 · 必须 PMO 自觉:

### R3 · PMO 统一承接

所有用户输入 PMO 先承接 · 禁止 RD/Designer/PM 等角色直接响应。
多角色对话场景下 · 用户输入直接打 RD = 角色越权(RD 直接接需求跳过 PM 的 PRD)。

### R4 · 流程边界

- **不简化**:每种需求走对应级别的完整流程 · "简单/文件少/无风险" 不构成跳过理由
- **不膨胀**:自动流转节点禁止插入暂停 · "回合边界/容量预算/让用户看进度" 不构成暂停理由
  - 🔴 **授权暂停点 = 用户决策点(固定闭集 · 见 §授权暂停点清单)· stage 内"怎么执行" = AI 自决的执行细节 · 不是暂停点**:改动大 / 破坏式 / 不可逆 / 文件多 / 用户全程参与设计 **都不是**暂停理由 —— 不得构造"如何推进 / 落地节奏 / 先做一层给你看 / 一次性还是分批 / 要不要先停"等**伪决策暂停点**
  - 🔴 **规模 / 节奏是 AI 自己的执行问题 · 不甩给用户**:体量大不是暂停理由 —— AI 自己组织消化;**"用户参与了设计" ≠ "用户该决定执行节奏"**(设计决策已在授权暂停点收敛 · 落地是 AI 的活)· 闷头干到 stage 完成 · 后果由 review/test/pm_acceptance 下游 gate 兜
  - 🧩 **subagent(`Agent` 工具)= 可选执行手段(AI 自决 · 非默认 · 非每 stage 必用)**:有**独立可并行 / 需隔离的大块**子任务时按需用(典型:dev 多端/多模块并行实现 · goal/blueprint 多方案多领域调研 · 大块读码/探索丢 subagent 保主编排 context 干净)· ⚠️ **不过度使用** —— 小 / 耦合 / 强串行的任务直接自己做 · subagent 有 context 切换 + 协调 + 结果校验开销 · 滥用反拖慢 + 增碎片。判据:**子任务相互独立且够大** → 值得;否则自己做。🔑 **授权已长期化**(v8.135):宿主注入块(CLAUDE/AGENTS/GEMINI.md「Subagent 默认授权」段)已含用户对 teamwork 流程内 subagent 的**默认授权**(满足各宿主工具契约的 "user explicitly asks" · 无需每次口头确认)——授权解决「能不能用」· 本条判据仍管「该不该用」
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
- **判定**:任何"PMO emit 后需要用户回应才能继续"的点 = 暂停点 = 必走本格式。不可只描述情境让用户自由输入 · 不可用"回复『X』升级"等自由文本 —— 必给编号选项。
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

详细 9 红线设计 rationale 原载 v8.0 设计稿(已清理 · git 历史可溯)。

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

### bootstrap flow_gates 响应(首条响应前必扫)

session 启动 `bootstrap.py` emit `checks.skill_update_check` + `flow_gates[]`(forewarn · **非 BLOCK**)· PMO **首条响应前必扫**。

🔴 **禁截断工具输出**(例:`bootstrap.py | head -50` 把 `skill_update_check`〔在 JSON 后位〕切掉 → PMO 漏升级提示 · 还误判"bootstrap 没检查升级"):teamwork 工具(`bootstrap.py` / `state.py` / `update.py`)输出 = **结构化 JSON · 字段顺序有意义 · 关键 forewarn 在后位** —— **禁 `| head` / `| tail` / `| sed -n` 等任何截断**,必完整读(Read 整个文件或直接看完整 stdout)。bootstrap 已在输出**顶部**置 `pmo_must_read` 一行 digest(升级 / gates / 优先级 · survive `head -5`)· 即便习惯性截断也能见,但仍以完整 JSON 为准。🔴 工具输出**罕见过长**时应落文件 + emit 路径(如 external-review 写 `external-cross-review/<stage>.md`)· **不 inline 巨串**诱使截断。

🔴 **入口优先级**(多信号同时触发 · 按序 surface · **不可降成底部脚注**;bootstrap 已 emit `session_entry_priority` 物化):**① 升级**(`skill_update_check=outdated` · 旧版=旧行为/补规划白补 → 最先)→ **② 补规划**(`cold_start` gate)→ **③ 任务**(triage/启动 Feature)。反模式:把 ①② 降「维护提醒」脚注、先推任务 = 优先级倒置。

按 gate 的 `action` 字段执行:

- `prepare_check_required_before_init_feature`(常驻)→ mode B 走 prepare(详 § Mode B 移交)
- `product_overview_planning_spec_required`(项目有 `product-overview/`)→ 规划类任务先跑 `state.py planning-check`(详 [docs/feature-planning.md](./docs/feature-planning.md))
- `cold_start_product_planning_recommended`(项目无 `product-overview/` · 地图根 `teamwork-space.md` 已 bootstrap 自动建)→ 🔴 **产品规划上游引导**:
  - 🔴 **地图 vs 规划解耦(v8.116)**:`teamwork-space.md`(知识地图根)由 **bootstrap 自动建骨架**(N≥1 · 单项目=1 子项目 · 知识入口自动探测 · 子项目清单空表待填 · **不再"单项目可无"**)· `product-overview`(产品规划上游 · 愿景/业务架构/执行线)**要人建** —— gate fire 于**它**缺失。`teamwork-space.md` 子项目清单由 product-overview「✅ 已确认」+ Feature Planning **回填**(派生关系不变 · 仅地图骨架自动化 · [PRODUCT-OVERVIEW-INTEGRATION.md](./PRODUCT-OVERVIEW-INTEGRATION.md))。
  - 🔴 **权威顺序**:`product-overview`(PL 引导)→ ✅确认 → 回填 `teamwork-space.md` 子项目清单 → Feature Planning(涉 UI 先出全景初步规划 → 拆 WS / ROADMAP)→ Feature 状态机。
  - **bare `/teamwork` / mode D 无具体任务** → 🔴 **不当静默看板** · 首条响应 emit 下方 R5 暂停点(即便已有 PROJECT/ROADMAP · 说明跳过了上游产品规划 · 仍 surface「缺 product-overview」· 不降级成脚注)
  - **mode B execute** → 首条响应 emit 同一 R5 暂停点(执行前先问要不要补产品规划上游)
  - **mode A/E** query/discuss → 轻提一句(可选)· 不强暂停
  - **mode C** resume(已有 state.json 续作)→ silent skip(不打扰)
  - **R5 暂停点动作**(引导 product-overview · 用户可拒):① 进产品规划冷启动(PL 引导建 product-overview → ✅确认 → 回填 teamwork-space.md 子项目清单)💡 / ② 跳过直接做任务(单 Feature 快速 · 后续可补)/ ③ 其他 · 🔴 **用户拍板前不擅自建 `product-overview/`**(R5)· 注:`teamwork-space.md` 地图骨架由 bootstrap 自动建(非规划内容 · 无需 R5)

🔴 PMO 漏扫 flow_gates = 退回 v7「凭记忆读 spec」· Feature Planning / 冷启动 / 产品规划上游 不进状态机 · 无 state.py 兜底(物化盲区 · 用 forewarn gate 补)。

### Mode A / E 升级触发(PMO 主动建议 · 不等用户提)

mode A 排查 / mode E 讨论收尾时 · 命中以下场景必须建议升 mode B:
- 涉及**多 Feature 范围拆分** / **ROADMAP 更新** / **P0/P1 优先级排序** → 升 **Feature Planning**(走 PROJECT/ROADMAP/sitemap · 非散述清单)
- 涉及**新功能实现方向** / **架构决策点** → 升 **Feature**(走 goal PRD 而非主对话伪 PRD)
- 涉及**已知 bug 根因 + 修复方案** → 升 **Bug**

🔴 **升级建议是暂停点 · 必走 R5 标准 1/2/3 格式**(不可用"回复『进 Bug』"自由文本 · 用户要打字 = 心智负担):

```markdown
⏸️ <排查完成 / 讨论收敛> · 建议升级到 <flow_type> 流程 · 请选择:

1. **进 <flow_type> 流程** 💡 推荐
   理由:<为什么升 · 1-2 句>
   动作:PMO 进 prepare 子流程(建 worktree + init-feature)→ 走 <first_stage> stage

2. **暂不升级**(仅排查闭合 / 继续讨论)
   理由:<你想先观察 / 排期 / 自己改>
   动作:<排查报告留档 · 可记入待规划需求池(product-overview/PENDING.md)| 继续当前讨论>

3. **其他指示**
```

### Mode B 必移交 prepare 子流程

mode B 识别后(**无论后续 flow_type = Feature / 敏捷需求 / Bug / Micro · 都走 prepare**)·
PMO **必走** [docs/prepare.md](./docs/prepare.md) · 不可在主对话散述准备步骤。

🔴 **mode B emit 任何 prepare 内容前 · 必先用 Read 工具打开 [docs/prepare.md](./docs/prepare.md)**(命令式 · 不是"参考")· 不读直接 emit 5 段 = R5 违规 + **必漏 §2.1 复杂度升级判据 / §2.2 准入校验**。

📋 **prepare.md §2.1 / §2.2 quick-ref**(读 prepare.md 前就先警觉 · 但**不替代**真读 prepare.md):
- **§2.1 复杂度升级判据**:关键词命中 Feature 时必再扫这 5 信号(命中任一 → 强制升 **Feature Planning**)
  跨独立部署服务 / 数据模型重构 / 老需求架构性废弃 / 影响 ≥2 BL / 方向级业务变更
- **§2.2 准入校验**:关键词命中"敏捷需求 / Micro"时必反向扫准入硬约束(任一不满足 → 升 Feature)
  敏捷需求:≤5 文件 + 无 UI + 无架构 + 方案明确
  Micro:零逻辑变更 + 仅 文案/样式/资源/配置常量/注释

判据:**进状态机 = 走 prepare**(4 个进状态机流程都需 worktree + branch + merge_target + artifact ID 4 项配置 · ID 按 flow_type 分 F/B/M · 详 conventions.md §1)。
即便最轻的 Micro(改文案 1 行)也要 prepare · 不可跳过。
不进状态机的 Feature Planning / 问题排查 → 不走 prepare(由 PMO 主对话执行)。

prepare 子流程动作概览:流程类型识别(§2.1/§2.2 扫信号)→ worktree 决策 → emit 4 项暂停点 → 用户确认 → PMO 跑 git worktree add + cd → state.py init-feature。

🔴 **物化硬墙**(两道):
- **prepare-check audit 门禁**:`state.py prepare-check` 跑成功写 audit jsonl(`~/.teamwork/prepare_check_audit.jsonl`)· `state.py init-feature` 校验近 60min 内有匹配 `--feature-id` 前缀的 audit record · **无匹配直接 BLOCKED**。
- **admission-judgment 必传**:`prepare-check` 必传 `--user-intent "<用户原话>"` + `--admission-judgment '<JSON>'`(AI 读 §2.1/§2.2 后输出的判断 · 含 sections_reviewed[] + matched_signals[] + recommended_flow_type + ai_rationale)· 缺任一 BLOCKED · **无 SKIPPED 兼容口子**(全局强制必传)。设计理由:**不依赖 AI 自觉读 prepare.md** · 工具物化 "你必须想这件事" · 推荐流程 ≠ 你选的 flow_type → emit WARN + audit 留痕(R0 兜底 · 不强 BLOCK · 因为可能合理例外)。
因果:prepare-check 决定 prefix / features_root / flow_type / admission_judgment 4 项;省了下游撞墙。bypass(调试):`TEAMWORK_BYPASS_PREPARE_CHECK=1`(走 init-feature 门禁旁路 · prepare-check 仍校验 admission_judgment)。

### 待规划需求池(命中查询意图时扫描)

🔴 **触发条件**:mode A query 关键词命中以下任一时 · PMO **按需读** `product-overview/PENDING.md`(外置 · 不随 session 入口 silent-read · 命中 backlog 查询才读)· 列 status=📝/🔄 的项:
- "待做 / 待规划 / pending / backlog / 待办"
- "还有什么 / 还要做 / 接下来做什么 / 下一个"
- "看下池子 / 看下待规划"

emit 格式:
```
📋 待规划需求池:N 个 active 项(详 product-overview/PENDING.md)
1. PENDING-NNN · <标题>(来源:<source> · 状态:📝/🔄)
2. ...
回 "启动 PENDING-NNN" → 进 prepare 子流程 · 或 "稍后" 闭合。
```

**不扫场景**:mode B/C/D/E 入口(用户没问 → 不主动 emit)/ 关键词不命中 / 池空 → silent skip(避免噪音)。

**追加机制**(session 内发现新待规划项):PMO/RD/PM 在 stage 内识别"本 Feature 范围外但要做"→ 主对话内 append 到 `product-overview/PENDING.md` 表(用户确认后落盘 · 无该文件则从 [templates/pending.md](./templates/pending.md) 建)。

**闭环清理**(防池臃肿):PENDING-NNN 转 ✅ 已转(进 Feature/Bug)或 ❌ 不做 → **立即从表删** · 关联落对应 Feature `state.json.related_pending` audit。表始终只保留 active(📝/🔄)。

### 入口红线 R-T1/2/3

- **R-T1 · PMO 必先分诊**:承接任何用户输入 · 必先完成 5 mode 分诊 + audit_line · 不可跳过直接 init-feature / stage-start
- **R-T2 · mode B 必移交 prepare**:triage 自身只做 mode 分诊 · 不做流程类型识别 / worktree 决策 / 暂停点(都是 prepare 的事)· 不可自己跑 git worktree add / init-feature
- **R-T3 · resume(mode C)不重 init**:mode C 是 jump 到现有 state.json · 不可重跑 init-feature;state.json 不存在 → 退回 mode B

### 入口与状态机的接口(triage 边界)

**triage 入口完成 = init-feature 前置满足**:
- ✅ worktree 物理已创建(PMO 显式跑)
- ✅ cwd 在 worktree 内(PMO 显式 cd)
- ✅ artifact ID(Feature/Bug/Micro · F/B/M)+ branch + merge_target 已用户确认

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

### 授权暂停点清单(非 auto 模式 · 每个独立 emit + 等用户)

🔴 **非 auto 模式 · 以下每个授权暂停点 PMO 必独立 emit + 停 + 等用户回应** · 不可凭一个 `ok` 推全程(详 §用户交互快捷词「ok 作用域」):

| 流程 | 授权暂停点(按顺序) |
|---|---|
| **Feature** | ① prepare 4 项配置 → ② goal PRD 最终确认 → ③ ui_design UI 预览确认(若 --needs-ui) → ④ blueprint DB schema 变更确认(条件 · 见下) → ⑤ pm_acceptance 三选项 → ⑥ ship1 终点 等平台合并 feature MR |
| **敏捷需求** | ① prepare 4 项配置 → ② goal PRD 最终确认 → ③ pm_acceptance 三选项 → ④ ship1 终点 |
| **Bug** | ① prepare 4 项配置 → ② **diagnose 修复方案确认**(根因+方案 · 用户拍板才进 dev) → ③ pm_acceptance 三选项 → ④ ship1 终点 |
| **Micro** | ① prepare 4 项配置 → ② pm_acceptance 三选项 → ③ ship1 终点 |

📎 **blueprint DB schema 条件暂停点**:Feature 的 TECH 方案涉及**数据库数据结构变更**(新建/删除/修改 表、字段、索引、约束、migration)时 · blueprint-complete 前必 emit 用户确认暂停点(详 [stages/blueprint-stage.md § 7.5](./stages/blueprint-stage.md))· 不涉及则跳过。**敏捷需求 / Bug / Micro** 不应涉及 DB 数据结构变更(属架构性 · 命中则按 prepare §2.2 升 Feature)。
📎 stage 间(goal-complete→ui_design / dev→review 等)是 state.py **自动流转** · 非暂停点 · 不插确认。

### auto_mode=true 时各暂停点行为(按名 · 不按编号)

🔴 用户选 `auto_mode=true` = 显式委托 AI 完成 stage 间流转。**仅"用户决策权"类暂停点保留 stop**;**"技术 / 设计 / 评审"类暂停点 AI 代用户接受确认 + 文档化**(不打扰用户)。🔴 这是**跳过用户确认暂停点** · **绝非**跳过/伪造**评审工作本身**——评审(多角色 + external)照常真跑。

| 暂停点 | auto 行为 | 理由 |
|---|---|---|
| **prepare 4 项配置** | **stop** | 用户初始配置(artifact ID / worktree / branch / merge_target)· AI 不能替选 |
| goal PRD 最终确认 | skip | PRD 已多角色 review(**真跑**)· auto 跳过的是**用户确认** · 非评审本身 |
| ui_design UI 预览确认 | skip | 设计意图已落 UI.md / preview · auto 用户接受 |
| panorama_sync 跨团队 reviewer(仅 L2 结构变更停 · L1 节点内增量任何模式都不暂停) | **skip + WARN** | `panorama-change-summary.md` 已文档化 · auto 用户接受跨 Feature 影响 · PMO 必 `state.py add-concern --severity WARN --message "auto skip: panorama change scope=..."` 留 audit |
| blueprint DB schema 变更确认 | **skip + WARN** | 技术决策 auto 委托 AI · 但 DB 变更高风险 · PMO 必 `state.py add-concern --severity WARN --message "auto skip: DB schema change ··· tables/fields/migrations: ..."` 留 audit(便于 dev/review 复查) |
| browser_e2e 用户看截图 | skip | 截图已入 evidence · auto 用户接受 |
| **pm_acceptance 三选项** | **stop** | 产品决策权:approved_and_ship / approved_no_ship / rejected_with_feedback · AI 不能替用户拍板(违 R3) |
| **ship1 终点 等平台 merge feature MR** | **stop** | 用户在 git host 平台操作 · AI 无法代办 |

🔴 **skip + WARN 行为**:PMO 跳过暂停点 · 但 `state.py add-concern --severity WARN` 写一条 audit 锚定 AI 自决的范围(防 audit 看不到 / 后续复查无迹)。

📎 `worktree_mode=auto` ≠ `auto_mode` —— 前者是 worktree 物理校验模式(prepare/init-feature)· 与暂停点自动流转**完全无关**。

### yolo 模式(完全自动 · 无人值守 · 🔴 高风险)

🔴 `yolo` = `auto_mode` **超集** —— 启动后**零 stop**(连 pm_acceptance 产品验收 + MR merge 都自动)。启用:`init-feature --yolo [<分支>]`(自动 implies `auto_mode`)。
- **`--yolo <分支>`** = 本需求专属 `merge_target`(**覆盖** `--merge-target` / localconfig 默认)· 推荐给 yolo 一个**专属集成分支**隔离自动合入的代码(如 `--yolo yolo/feat-x`)· 该分支即 yolo 自动 merge 的目标
- **`--yolo`**(无值)= 用 `--merge-target` 的分支(二者至少给一个 · 都没 → FAIL)
- **中途切换** = `state.py set-mode --feature <F> --yolo [<分支>] --reason '<原因>'`(或 `--auto-mode` / `--no-yolo` / `--no-auto-mode`)· 语义命令 · 走 `state.mode_changes` audit + 同款非 main 硬门 + implies-auto 护栏 · **不要 raw-write `state.json` 改 auto_mode/yolo**(无 audit·绕门禁)

🔴🔴 **yolo ≠ 简化/提速 · 是「加重审核」**:无人值守 = **没人在看** → 自动化评审(尤其 **external 异质模型 cross-review**)是**唯一安全网** · 必须**保留 / 加重** · **绝不削弱**。yolo 的「零 stop」**只**针对**人工决策暂停点**(prepare / pm_acceptance / MR merge)· 技术与评审环节**一个不少**。
- 🔴🔴 **严格按 teamwork 流程流转 · 不得「内化」**:每个 stage 的评审必**真跑** —— 多角色真分析(找真问题 · 不是 `mode: yolo-internalized` 自盖章 APPROVE)· external 必**真调异质模型**(`state.py external-review --stage <X>` · 不得 AI 手写 `external-cross-review/*.md`)。external **实跑日志物化校验**:yolo 下 `xx-complete` 校验 `~/.teamwork/external-review-logs/<feat>/codex-<stage>-*.log` 存在(无 → FAIL · 文件名/frontmatter 能伪装合规 · 实跑日志伪造不了)。auto_mode 的「内化」**仅指跳过用户确认暂停点**(AI 代用户接受)· **绝非**跳过/伪造评审工作本身。
- 🔴 **不得去 external 评审**(以"集中到 review stage""效率""价值低"为由)—— yolo 下 `change-review-roles` 去 external **物化 BLOCK** · 仅 external CLI **客观不可用**(未装 / 网络死 · 已重试失败)才 `--accept-external-removal --reason '<技术原因>'`(写 concern WARN)
- 🔴 **不得擅自合并 BL / 跳 stage / 减 review 轮次 / 简化流程** —— 该走的 stage、该跑的评审角色一个不省;BL 拆分是 Planning 已定的范围,yolo 不重新打包
- ✅ **可以加重**:必要时每个 stage 都跑 external、加 review 轮次、提高测试覆盖 —— 无人值守正该更严

| 暂停点 | yolo 行为 |
|---|---|
| prepare 4 项配置 | 启动前给(kickoff 输入 · 非运行中 stop) |
| pm_acceptance 三选项 | **自动 `approved_and_ship`** + `state.py add-concern --severity WARN`(连"是否 ship"也委托 AI) |
| ship Phase 1 等平台 merge MR | **自动 merge**:`gh pr merge --auto --merge`(GitHub · check 全过才合)/ `glab mr merge`(GitLab) |
| ship-finalize(Phase 2 主工作区收尾) | **自动跑**(merge 确认后 · 见 main-sync) |

🔴 **硬约束(init-feature 物化 gate · `_is_main_branch`)**:`merge_target` **必须非主分支**(`main`/`master`/远端默认)· 否则 `init-feature --yolo` 直接 FAIL。理由:yolo **无人 review 自动 merge** · 不得让 AI 错误/幻觉特性直接进 main —— 只能合到 `dev`/`staging`/`integration` 等集成分支 · 主分支的提升仍由**人工 gate**。

🔴 **安全栏**:
- **尊重分支保护**:目标分支受保护 / 必需 check 没过 → `gh`/`glab` merge 命令失败 → 自动退回「手动 merge」stop + WARN(**绝不** force / 绕保护)
- **审计**:每个自动决策(pm_acceptance 自动过 / 自动 merge)写 `add-concern --severity WARN` 留痕
- **per-feature opt-in**:`--yolo` 不 sticky(每次显式传)· `state.json.yolo=true` 留痕 · 不会误触发

🔴 **自主解决(yolo 核心:失败/卡点也零人工)**:yolo 真义 = **AI 自主解决所有问题 · 不回退给人** —— 不止 happy-path 零 stop · 连**校验失败 / 重试耗尽 / 升级点 / bypass 请求**都 AI 自决:

| 卡点 | 正常(非 yolo) | yolo |
|---|---|---|
| stage 校验 FAIL | AI 修 + 重试 · 3 次仍 FAIL → 暂停问用户 bypass | **AI 持续自主解决**(更多轮 / 换思路 / 深挖根因)· 不向用户升级 |
| review NEEDS_REVISION / test FAIL | AI 改 + retry | 同上 · 持续修到绿 · 不回退给人 |
| bypass 协议(R8 写门禁) | 停 · 等用户 `--user-confirmed` | **AI 自授权**(`--yolo` = 用户 blanket 委托 · `require_user_confirmed` 物化放行)· 仍 `--reason` + `bypass_log` + concerns WARN |
| external review CLI 缺/超时 | 问用户 / change-review-roles | 🔴 **优先重试 / 修环境**(external = 唯一安全网 · 默认**保留**)· **仅 CLI 客观不可用**才去 external（物化需 `change-review-roles ... --accept-external-removal` + WARN）· **绝不为效率去** |
| merge 冲突 | 停 | AI 解冲突(非主分支一般无保护) |

🔴 **优先级:解决 > 绕过**。yolo ≠「遇错就 bypass 硬推」· 而是「AI 当负责的工程师 · 穷尽手段把问题**真解决**」;bypass 只是穷尽自主解决后为不停下的**最后兜底** · 每次必 WARN 留痕。审计看 `bypass_log` 频率 = yolo 健康度(频繁 bypass = AI 没在真解决 · 该回炉 / 降级 yolo)。

🔴 **真·硬停(极少 · AI 客观无法自决)**:环境彻底不可用(网络死 / `gh`/`glab` 没装 / 磁盘满 / token 失效)—— AI 物理做不了 · 仍先重试 / 找替代 · 实在不行才 surface(因为继续不可能 · 不是"该问人")。

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

### 🔴 知识三层律 + 律法/地图分工(框架定位)

teamwork 承担**知识导航(索引/地图)**的责任 —— 让 AI 从一个根入口**零死角**抵达任何项目知识 —— 但**不承担知识内容**(内容会与代码漂移 · 腐烂后反向误导)。

| 层 | 角色 | 权威 | 陈旧时 |
|---|------|------|--------|
| `teamwork-space.md` + 各 doc | **地图**(指针 / 路由 / 一句话摘要) | teamwork 维护 | 指错一格 · 打开仍对(优雅降级) |
| **代码** | **领土**(细节唯一真相) | 🔴 **代码** | 永远现 grep+Read · 不信文档转述 |
| 归档 `_archive/*.zip` | **冷库**(已交付过程文件) | `_archive/INDEX.md` 索引 | 先读 INDEX 描述判相关 · 必要才解压 |

- **律法 vs 地图分工**:本节(SKILL)= **律法**(generic 文档*类型*语义 + 话题路由 · 每项目一样 · 框架知识 · 稳定 · 不复制进项目)· 项目的 `teamwork-space.md` = **地图**(本项目*实例*的知识入口索引 · 随项目变 · 见 § teamwork 业务流程架构)。
- 🔴 **任何 session 先读 `teamwork-space.md`** —— 它是本项目「**索引之索引**」· 列出每个知识节点的指针(子项目 / 规划 / 工程文档 / 归档冷库)· **必读地图根**。它指向的领土(代码 / 大文档)**按需懒加载** —— 读地图 ≠ 读全量。
- **N≥1 统一模型**:任何 teamwork 项目 = 1 个 `teamwork-space.md`(地图根)+ **N≥1 个逻辑子项目**(职责单元 · 非物理仓)· **单项目 = N=1**。知识层与项目是否 monorepo **无直接耦合**(子项目是职责分解 · 不是打包方式)。

### 文档清单 + 权威范围

| 文档 | 权威范围 | 何时 read |
|------|---------|---------|
| `product-overview/{}_业务架构与产品规划.md` | 产品愿景 + 业务架构 + 执行线列表(taxonomy) | 规划 / 拆能力 / 起 WS（有 product-overview 时） |
| `product-overview/workstream/WS-NN.md` | 规划单元(一组 feature 的拆解 · 承接 1+ 执行线) | 起 WS / 看某规划拆了哪些 feature |
| `PROJECT.md` | 产品全景(子项目级) | 讨论产品方向 / 创建 Feature |
| `ROADMAP.md` | Feature(BL) 列表 + 优先级 + 排期 + 关联 WS | 讨论 Feature 优先级 / 创建 Feature |
| `sitemap.md` | 信息架构 / 页面层级 | 讨论 UI / 创建含 UI 的 Feature |
| `project-specs/DEV-RULES.md` | **项目强制开发规范(人维护)**:分层 / 命名 / 错误处理 / 依赖方向 / 测试策略 / 风格 | **blueprint(TECH)+ dev(实现)必读** · 起草/写码前 |
| `project-specs/KNOWLEDGE.md` | Gotcha(踩坑)/ Preference / 已澄清歧义 / 已否方向(AI 沉淀)| triage 期 + 涉项目踩坑/事实时 |
| `project-specs/GLOSSARY.md` | 业务术语 + 实体关系 + 命名约定 + 别名歧义 | PM 起草 PRD 前 / RD 起草 TECH 前 |
| `project-specs/TROUBLESHOOTING.md` | 排查 / 运维操作手册(log / DB / 监控 / 部署)| mode A/E 涉排查 · **或 AI 自己需连环境/查 DB/log(任何 stage/规划)→ 先读拿连法** |
| `project-specs/ARCHITECTURE.md` | **workspace 级**系统架构(子项目拓扑 + 依赖 + 目录布局) | 讨论跨子项目架构 / 看系统全貌 |
| `project-specs/PROCESS-LEDGER.md` | **流程价值台账**(一行一 feature:external 采纳率 / 角色真 finding / 暂停点互动 / bypass · 详 [stages/ship-stage.md §16](./stages/ship-stage.md)) | ship2 planning-backref 随收尾 MR append · 流程审视 / 年检时读 |
| `{子项目}/docs/architecture/ARCHITECTURE.md` | **单子项目内部**技术架构(技术栈/分层/模块) | 讨论某子项目内部架构决策 |
| `docs/architecture/database-schema.md` | 数据库 schema | 讨论数据模型 |
| `external/` | 三方/外部资源文档(SDK / 协议 / 供应商) | 对接外部系统 / 三方 API |
| `{子项目}/docs/features/_archive/INDEX.md`(每子项目 docs_root 下 · 单项目=repo 根 `docs/features/_archive/`) | 🔵 **归档冷库目录**(已交付 feature 的 id+描述+时间+zip 路径) | 查已交付/历史 feature · 先读描述判相关 → 必要才解压对应 zip |

### 按场景路由速查(PMO 任意时刻)

| 用户提到 | PMO 内部 read |
|--------|------------|
| 规划 / 拆能力 / 起 WS / 路线图全景 | `product-overview/{}_业务架构与产品规划.md` + `product-overview/workstream/` |
| 执行线 / 业务线 / 某能力下有哪些 feature | `业务架构与产品规划.md § 执行线列表`（反查 `workstream/` 的 tag） |
| 产品方向 / Feature 排期 / Roadmap | `PROJECT.md` / `ROADMAP.md` |
| 页面层级 / UI 整体 / 信息架构 | `sitemap.md` |
| 开发规范 / 约定 / 分层 / 命名 / 错误处理 / 依赖方向 / 测试策略 / 代码风格 | `project-specs/DEV-RULES.md` |
| Gotcha / 踩坑 / 历史坑 / 项目特有约束 / 用户偏好 | `project-specs/KNOWLEDGE.md` |
| 业务术语 / 实体关系 / 别名 | `project-specs/GLOSSARY.md` |
| **报错 / 502 / 查 log / 排查 / 异常 / 服务挂了 / 查环境 / 查 DB / 查 Redis / 部署 / 回滚** | **`project-specs/TROUBLESHOOTING.md`** |
| 系统全貌 / 跨子项目架构 / 子项目拓扑依赖 | `project-specs/ARCHITECTURE.md`(workspace 级) |
| 某子项目内部架构 / 数据库 / schema | `{子项目}/docs/architecture/` |
| F\d+(具体 Feature 编号) | `docs/features/{F}/` |
| 历史决策 / ADR | `docs/features/*/adrs/INDEX.md` |
| 对接三方 / 外部 SDK / 供应商协议 | `external/` |
| 已交付/历史 feature / 翻旧账 / 归档 | `{子项目}/docs/features/_archive/INDEX.md`(对应子项目 docs_root · 先读描述 · 相关才解压 zip) |
| 多子项目 / 跨项目 / **本项目知识全景入口** | `teamwork-space.md`(🔴 必读地图根 · 索引之索引) |
| 涉及具体代码(细节唯一真相) | 🔴 grep + Read 实际代码(不信文档转述) |

🔴 **AI 自己需连环境(查 DB / log / 服务 / 跑运维命令)时也走 `TROUBLESHOOTING.md`** —— 不只"用户提到",含**规划期代码调研需 live 数据**、stage 内联调/排错。**先读它拿连接 + 操作方式,别凭 `.env` / 启动脚本瞎试**。TROUBLESHOOTING 是**用户主权**运维手册 · AI 按需读、不重新发明;连法缺失 → 补进它(知识沉淀)。

### 项目级系统维护(`tools/bootstrap.py` 独立脚本)

**每个 session 启动时 · PMO 首条响应前必跑**(silent · 不打扰用户)。
**独立脚本 · 不归 state.py 状态机域**(职责分离):

```bash
python3 <SKILL_ROOT>/tools/bootstrap.py --host <claude-code|codex-cli|gemini-cli|unknown>
```

🔴 **只传 `--host`**:宿主是 AI 关于自身的事实(不在文件里 · 须显式)。`--skill-root` 自推、版本号 bootstrap 自读 `SKILL.md` frontmatter(单源)—— **AI 不传版本号**(转述文件里已有的事实必错)。`<SKILL_ROOT>` = `~/.claude/skills/teamwork` 或 `~/.codex/skills/teamwork`。

🔴 **host 是 per-feature(非全局 · 否则全局 audit 跨 session 污染)**:
- **主路径**:`init-feature --host` / `<stage>-start --host` 写 `state.json.host`(per-feature 隔离)· `external-review` 读 state.json.host(不再依赖全局)
- **跨 session 切宿主**:用 `<stage>-start --host <new>` 显式覆盖 · state.py 自动 emit `host_change_warning` + concerns 留痕
- **兼容路径**:`~/.teamwork/host_audit.json`(全局)仍作 fallback · 但 `external-review` 读到会 emit `deprecation_warning`(已废弃 · 勿依赖)
- bootstrap 仍写 audit · 但加 `_deprecated` 字段(线上 grep 可见迁移期)

`bootstrap.py` 做什么(silent · 不打扰用户):
- 版本号自读 SKILL.md frontmatter(单源)
- 项目骨架检查/创建(project-specs/ 下 KNOWLEDGE/TROUBLESHOOTING/GLOSSARY · 旧散放自动迁移)
- CLAUDE.md / AGENTS.md / GEMINI.md 注入段检查(对接 sync-drift.py)
- state.json v7 → v8 迁移扫描
- **知识图谱结构可达性校验**(归档 `INDEX.md`↔`*.zip` 双向对账 + workspace 节点登记 · 命中 emit `checks.knowledge_graph` WARN + digest 行)· 🔴 只查**可达性**不查**内容新鲜度**(内容=代码唯一真相)· teamwork-space.md 缺则 skip

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

- 项目结构(单/多子项目) · 子项目清单 · 跨项目变更 ID

**为什么只读这一份**:teamwork-space.md 是轻量结构索引(通常 < 200 行)· 已含分诊所需的全景上下文。
**PROJECT.md / ROADMAP.md / sitemap.md / `product-overview/PENDING.md`(待规划需求池)** 等详档**按需读**(用户提到 / 任务涉及时再 Read 对应段 · 待规划池在命中 backlog 查询时才读)· 不全文加载到 PMO 上下文(避免 context 浪费)。

🔴 **创建/维护 teamwork-space.md 的规则**(字段语义 / 硬规则 / 生命周期 / 进度统计 / 跨项目变更单源)→ [docs/teamwork-space-guide.md](./docs/teamwork-space-guide.md)(规则外迁 · 模板 [templates/teamwork-space.md](./templates/teamwork-space.md) 只留实例化骨架)。

🔴 **文件名**:规范名是连字符 `teamwork-space.md`。v7 期项目的 legacy 下划线名 `teamwork_space.md` 由 `bootstrap.py` 在本步**之前**自动迁移成连字符名 —— 故此处只找连字符名即可(legacy 下划线名会导致子项目 registry 静默不加载、路由失效)。

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

详细 9 红线 rationale 原载 v8.0 设计稿(已清理 · git 历史可溯)。

---

## 文档导航

| 文件 | 作用 |
|------|------|
| [SKILL.md § Triage 入口规范](./SKILL.md) | **入口规范** · triage 不是 stage · 5 mode 分诊 + mode B worktree 决策 |
| [FLOWS.md](./FLOWS.md) | 6 流程 telos(详细步骤进 docs/prepare.md 子流程 + 各 stage brief) |
| [ROLES.md](./ROLES.md) | 角色索引(→ roles/*.md) |
| [STANDARDS.md](./STANDARDS.md) | 技术规范索引(→ standards/*.md · 不含流程规范) |
| [TEMPLATES.md](./TEMPLATES.md) | 文档模板索引 |
| [stages/*.md](./stages/) | 各 stage Telos + Output Contract(校验进 state.py) |
| [roles/*.md](./roles/) | 角色 telos + 创作要点(协作进 state.py) |
| [standards/*.md](./standards/) | 技术规范(common/backend/frontend/tdd · 流程规范已删) |
| [tools/state.py](./tools/state.py) | 唯一编排器入口 |
| [tools/_v8_engine.py](./tools/_v8_engine.py) | 通用 stage start/complete + bypass 引擎 |
| [tools/_v8_stage_specs.py](./tools/_v8_stage_specs.py) | 12 stage 完整契约(stage 数单源 `STAGE_SPECS`) |
| [tools/_v8_ship.py](./tools/_v8_ship.py) | ship-phase 5 actions |
| [tools/_v8_migrate.py](./tools/_v8_migrate.py) | v7 → v8 迁移 |
| [tools/bootstrap.py](./tools/bootstrap.py) | session 启动维护(骨架 / hooks / 注入段) |
| [docs/CHANGELOG.md](./docs/CHANGELOG.md) | 完整变更记录 |

---

## License

MIT
