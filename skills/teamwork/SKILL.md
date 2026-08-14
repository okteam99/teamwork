---
name: teamwork
version: v8.327
description: AI 协作开发一体化框架 - 需求功能开发, bug 修复, 问题排查 · /teamwork 启动
---

# Teamwork Skill · v8.0 Code-driven Orchestration

**可枚举的规则进脚本(`tools/state.py`),不可枚举的判断留 AI。**
本文件只装**底线**:证据要求 · 独立采样 · 用户主权 · 机械操作(命令/路径/状态机)· 逆模型默认的判据。
**怎么设计架构 / 怎么拆任务 / 怎么写代码 / 怎么组织执行节奏 = AI 自决**(目标 + 契约给足,手段模型自推),结果由下游 gate(review / test / pm_acceptance)与物化门禁兜。

| 类别 | 例子 | 归宿 |
|------|------|------|
| 可枚举 | 状态转移、入口前置、出口产物、字段 schema、流程闭集、暂停点协议 | `tools/state.py` |
| 不可枚举 | PRD 完整性、架构合理性、代码优雅度、执行节奏、暂停点文案 | AI 自决 |
| 用户主权 | 代码布局、业务术语、排查命令 | 用户填,teamwork 按需读 |

---

## teamwork 业务流程架构(PMO 常驻认知)

> 从愿景到 feature 的纵向链路。**规划层不进状态机**(PMO 主对话直接做)· **执行层进状态机**(state.py 编排)。PMO 任何 triage / 规划 / 冷启动决策都以此为锚。

```
规划层(PMO 主对话 · 不进状态机)
  业务架构与产品规划.md       愿景 + 执行线列表(Line N · taxonomy · 稳定 · 新线才更新)
     └─(涉 UI)UI 全景初步规划  preview-project(系统+关键页)+ sitemap(IA 地图)· 拆 WS 之前出 · = 拆 WS 的输入
        └─ WS-NN(product-overview/workstream/ · 1..N 个)
               承接 1+ 执行线 · 拆一组 feature · 全景初规 ✅/N-A + 覆盖页清单 · 完成 = feature 写入 roadmap
             └─ ROADMAP/BL-NNN   feature 原子(关联回 WS-NN)
────────── 规划→执行 交接 = 用户拍板某 BL + prepare + init-feature ──────────
执行层(state.py 状态机)
     └─ F-NNN   goal →(ui_design)→ blueprint → dev → review → test →(browser_e2e)→ pm_acceptance → ship
```

- **WS 是 feature-planning 流程的产物**(不在流程外 ad-hoc 手搓)· 产出方式详 [docs/feature-planning.md](./docs/feature-planning.md)。
- **全景先于 WS**(涉 UI):拆 WS 前先在 `{子项目}/docs/design/preview-project/` 出 UI 全景初步规划 + `sitemap.md` · 🔴 **全景出完必给用户可访问预览 URL + 等用户确认**(R5 · 用户没确认过 = 不算规划完成)· 每 WS 记 `全景初规 ✅/N-A` + `ui_panorama_confirmed`(ISO)+ 覆盖页清单。
- **进度统计** = 未完成 WS(规划态)+ 各子项目 ROADMAP 的 BL(执行态);业务架构/执行线是愿景与 taxonomy · 不计入 · **不登记 WS**(保持稳定小列表)。
- **非开发工作**(运营/推广/BD):teamwork 不跟踪。
- 详:[PRODUCT-OVERVIEW-INTEGRATION.md](./PRODUCT-OVERVIEW-INTEGRATION.md)(规划层 · WS)。

---

## 快速开始

```bash
# 1. session 入口 · PMO 按 SKILL.md § Triage 入口规范分诊(不是 state.py 命令)

# 2. 用户确认 4 项配置后 · PMO 显式执行(主工作区 cwd):
git fetch origin
git worktree add -b <branch> <worktree-path> origin/<merge-target>
cd <worktree-path>

# 3. 此刻 cwd 在 worktree 内 · 进入状态机层(state.py 唯一域)
state.py init-feature --feature <feature-dir-in-worktree> ...

# 4. 各 stage 走 -start / -complete
state.py goal-start --feature <path>
# ... AI 按 next_action_brief 完成 stage 工作 ...
state.py goal-complete --feature <path> --auto-commit <hash> --artifacts ...
# state.py 自动校验产物 + 转移下一 stage + 输出下一 stage 的 brief

# 5. Ship(ship1 全交付在 worktree · ship2 零内容清场在主工作区)
state.py ship-start --feature <path>
state.py ship-phase --action sanitize --feature <path> ...
# 🔴 归档+规划翻牌进 feature 分支(单 commit · 随 feature MR 原子合入 · 翻牌先在 worktree 内改好):
state.py ship-phase --action archive --feature <path> --planning-artifacts <翻牌文件>|--no-planning-changes --archive-desc '<≤200 字>'
# → git push + gh/glab 创 feature MR(CLI-first)→ 记录:
state.py ship-phase --action push --feature <path> --mr-url <真实 URL> ...
# ⏸️ 贴 emit 的 user_card(MR URL 置顶)+ 📦 交付总结 → 立即跑监控(全模式必跑 · 停 ≠ 停监控):
state.py await-merge --feature <path>   # 30s 轮询 · 检测 MERGED → 自动 ship-finalize(ship2:验已交付→删 worktree→净化)
# (兜底:轮询不可用时用户合并后手动 cd 回主工作区跑 state.py ship-finalize)
```

---

## Subagent 默认授权

用户明确授权 AI(适用宿主:Claude Code / Codex CLI / Gemini CLI)在 Teamwork 流程中**默认使用 subagent · 无需每次另行确认**(满足各宿主 subagent 工具契约的 "user explicitly asks")。适用:各阶段 cross-review 与多角色评审、PL 对抗质疑(隔离执行)、并行探索调研、互不重叠 write scope 的实现子任务、验证/测试类 sidecar。

> 📎 teamwork **不注入**宿主指令文件(CLAUDE.md / AGENTS.md / GEMINI.md)—— 共享仓库里注入块会被 commit · 污染不用 teamwork 的用户。本段与 PMO 定位 / worktree 纪律等关键信息**以本 SKILL 为唯一载体**(加载 skill 即生效)· bootstrap 会自动清理项目里的历史注入块。

## worktree 纪律(🔴 红线)

**worktree 模式下 · 本 Feature 的文件写入优先用 worktree 内路径**(代码 / 文档 / 测试 / 配置):

- Feature 进 worktree 后 · **主工作区是其他并行 Feature 的基线**
- 写文件用 **worktree 内路径**(推荐绝对路径 `{worktree-path}/...`)· 不用相对路径 —— 部分宿主的 patch / 写工具不继承 shell `cwd`(如 codex `apply_patch`)· 相对路径会落到主工作区
- **违反后果**:主工作区被污染 → 改动串入其他并行 Feature / 主分支变脏 —— 并行开发的硬隔离被破坏
- 🔴 **确需写入主工作区的** · **须先经用户确认**(R5 暂停点)· 不可 AI 自决(注:ship2 零内容 · 不写主工作区任何文件 —— 副产物自动 commit 属清理非内容 · 无需此例外)
- **物化兜底**:`xx-complete` 时 state.py 检测主工作区是否冒出本 Feature 文件 → 命中写 `concerns WARN` + emit `main_tree_pollution`(**事后**兜底 · AI 应**事前**写对路径)
- 改完文件在 worktree 内 `git add -A {feature_dir}/` + commit(详 [stages/ship-stage.md R-S7](./stages/ship-stage.md))
- 🔴 **浏览器「看一眼」验证截图 → scratch 目录**(worktree 模式 `<worktree>/.teamwork-scratch/screenshots/`〔ignored〕· off 模式旧根)· **绝不散落 worktree 其他位置 / 主工作区根**(一次性截图 · 非交付 · 不 commit · 详 [conventions §12.5](./docs/conventions.md))· browser_e2e **证据**截图例外(交付物 · 落 `<feature_dir>/screenshots/`)

worktree 路径规范见 [docs/conventions.md §9-12](./docs/conventions.md)。

---

## 命令清单(分类概览 · 🔴 权威 = `state.py --help`)

> 不留逐条命令枚举 —— **实测必漂**(曾有 11/52 个真实子命令从未出现在枚举里)。**指针 + 复制被指向内容 = 副本必漂**,这里只留 `--help` 给不出的**分类心智**:

> 🔴 **按「AI 要不要记」分类**(不是按功能分)—— 56 个子命令里,**AI 只需记住 A 类**。
> 实测触发:某次 AI 在 goal 阶段手跑 `verify-ac.py`(它记住了这个脚本),而该脚本在 goal **必然 FAIL**
> —— 减少命令总数解决不了这个,只有**把对的命令在对的时点推给它**才解决。

- **A 类 · 必记(状态机流转 · 30 个)**:`init-feature` + 每 stage 一对 `<stage>-start` / `<stage>-complete`
  + `review/test` 的 `-fix` / `-retry` + ship 专属(`ship-phase --action {sanitize|archive|push|close-unmerged}` /
  `await-merge` / `ship-finalize`)。链与可选性见 [FLOWS.md](./FLOWS.md)。
  ⚠️ `triage` 与 `prepare` **不是命令** —— 前者是 PMO 入口行为(见本文件 § Triage 入口规范)·
  后者是主对话子流程(见 [docs/prepare.md](./docs/prepare.md))。

- **B 类 · 不必记(流程在动作点推给你)**:`review-preventability` · `stage-cost` · `ledger-migrate` ·
  `external-review` · `add-concern`(auto skip 时)· `pause-mark` · `test-baseline` · `change-review-roles` …
  🔴 **它们会带着可直接跑的完整命令行出现在对应 emit / brief 里** —— 不必背,**照着跑**。
  > why:写进 stage 文档 ≠ 到达。文档在 stage-start 读,而动作点常在几十个工具调用之后 ——
  > **提醒与动作之间隔了太多 context**(实证:agent 读过派发声明制仍然漏了)。

- **C 类 · 不必记也别主动跑(逃生口 · 出事或用户要求时才用)**:`snapshot`(别名 `status`)/ `validate` /
  `raw-read` / `raw-write` / `recover` / `reset-prev` / `jump-to-stage` / `set-mode` / `audit-raw-writes` /
  `main-sync`。**查 `--help` 即可** —— AI 主动跑这些通常意味着它在绕流程。

🔴 **判据**:**「这个命令有没有一个确定的动作时点?」** 有 → 归 B 类并接进那个时点的 emit(不许只写进文档);
没有(靠人判断何时用)→ 归 C 类,不进任何提醒。**A 类之外都不该出现在 AI 的记忆负担里。**


命令现行权威 = `state.py --help` + [`tools/_v8_stage_specs.py`](./tools/_v8_stage_specs.py)(各 stage 契约)。

---

## 用户交互快捷词(全局语义规范)

| 快捷词 | 等价语义 | 适用场景 |
|---|---|---|
| `ok` / `OK` | **按建议** · 同意 PMO 当前推荐方案 | 任何 PMO 给出"建议:..."/"推荐:..."的暂停点 |
| `all default` | 全部用 PMO 给的默认值 | prepare 4 项配置暂停点 |
| `继续` / `next` | 继续推进流程(下一 stage / 下一 substep) | stage 完成后等用户拍板下一步 |
| `跳过` / `skip` | 跳过当前可选 substep / stage(若 spec 允许) | 可选 stage(如 ui_design / browser_e2e) |
| `bypass` | 触发 bypass 协议(R8 写操作硬门禁链 · 必带 --reason) | 状态机 FAIL 3 次后用户拍板逃生 |
| `回 dev` / `回 X stage` | jump-to-stage --to X(必带 reason) | pm_acceptance rejected / 用户主动回退 |

- 看到 `ok` → 复述"按建议执行 · <推荐方案 1 行摘要>" + 立即执行 · **不再二次确认**。
- 🔴 **`ok` 作用域 = 当前这一个暂停点** · **不预授权后续任何暂停点** —— 每个授权暂停点必**独立 emit + 独立等用户回应**(实证:prepare 的 `ok` 被误当成 PRD / UI / pm_acceptance 全部预授权 · 一路冲到底 = 违 R5)。

---

## PMO 软约束 + 暂停点标准格式(state.py 不物化 · PMO 必自觉)

state.py 物化了 9 红线中 8 条 · R3 + 部分行为约束(R4 / R5(b) / bypass)是主对话内的软约束。

### R3 · PMO 统一承接

所有用户输入 PMO 先承接 · 禁止 RD/Designer/PM 等角色直接响应(用户输入直接打 RD = 跳过 PM 的 PRD)。

### R3-E · 断言必须标注证据边界

🔴 **说某段代码/系统有某属性时,要么本次会话读过那一行,要么显式写「推断」——不许中间态。**

**高发形态 = 「读了旁边」**:grep 命中了 / 看到类型签名了 / 量了一个维度 —— 然后据此一般化到
**没亲眼看过的属性**(serde 标注 · DB 约束 · 默认值 · 那个分支是不是死代码)。
**证据是真的,推论是自己加的,而两者用同一语气一起给了出去。**

**给用户与下游的结论按证据分层写**:

> 「BFF 是类型化反序列化(**已验证** · 读了 `xxx.rs:1255`);因此我推断可增量扩展(**未验证** —— 没看 serde 是否 `deny_unknown_fields`)」

用户据此一眼知道**哪句该打问号**。这不减少出错,但让错误**在到达用户之前就带着标签**。

> *模型默认:把事实与推论连成一段流畅叙述 —— 那正是流畅写作的本质,所以必须逆着写。
> **且模型越强、叙述越流畅,推论就越像事实** —— 这条**不随模型变强而衰减,反而更需要**。*
>
> why(实证 SVC-CORE-F260728):AI 自省 9 个错误后归纳出**唯一共同点** ——
> 「我读了旁边的代码,然后把结论说成读过那一行」。其中一条把 external 给的行号直接写进 TECH
> (该函数根本不存在)· 一条据类型签名推出「新字段会被丢弃」(实为 `deny_unknown_fields` 会 502)。
> **不是验证不够** —— 那个 session 跑了几十次 grep 与 staging 实测;**是不标注验证止于何处**。
> 框架已有的 7+ 条规则(grounded 真实代码 / 不轻信摘要 / decisive 前提核验)**全在输入端**,
> 没有一条管输出端怎么标。

### R4 · 流程边界

- **不简化**:每种需求走对应级别的完整流程 ·「简单/文件少/无风险」不构成跳过理由。
- **不膨胀**:自动流转节点禁止插入暂停 ·「回合边界/容量预算/让用户看进度」不构成暂停理由(汇报/总结**不是回合终点** · 流转 emit 已机械附带 `continue_reminder`)。
- 🔴 **授权暂停点 = 用户决策点(固定闭集 · 见 §授权暂停点清单)· stage 内「怎么执行」= AI 自决**:改动大 / 破坏式 / 不可逆 / 文件多 / 用户全程参与设计**都不是**暂停理由 —— 不得构造「如何推进 / 落地节奏 / 先做一层给你看 / 一次性还是分批 / 要不要先停」等**伪决策暂停点**。
- 🔴 **规模 / 节奏是 AI 自己的执行问题 · 不甩给用户**:「用户参与了设计」≠「用户该决定执行节奏」(设计决策已在授权暂停点收敛 · 落地是 AI 的活)· 干到 stage 完成 · 后果由下游 gate 兜。
- **必给步骤描述**:选定流程类型后给完整步骤(stage 链 + 每个 stage 大致做什么 + 预期产出)。

### R4-P · 并行与 dispatch(subagent / teammate / workflow)

> 本节 = **并行姿态 + 声明制单源**;**档位表与四条硬边界单源 = [agents/README.md §一](./agents/README.md)**(全局规则 · 任何 subagent/teammate/workflow 适用)。

- **并行是默认考虑项**:每个 stage 开工先问「**哪些子任务可以并行?**」—— 冷审天然 N 路同发 · dev 多端/多模块各派一路 · 调研 fan-out 保主编排 context 干净 · 能并行的不串行(ultracode 开启时 workflow 优先)。
- **每进新子阶段重问**(实现 → 测试编写 → 修复):耦合度随阶段变 · 开工问一次会过期。🆕 **重问时加第三问:这些子任务的「验证目标」有重叠吗?**—— 🔴 **按产物归属切分容易让验证目标跨线**:切分看着正交(A=文档+单测 / B=新测试文件),验证目标却不正交。重叠 → 合并,或指定唯一 owner、其余路**显式声明「不做该验证」**。why(实证):dev 期 A 路自建 harness 验 6 场景,B 路的新测试文件验同一批场景 —— 同一件事做了两遍,多耗 ~40min 与 ~150k tokens。
- **派发后等待窗主对话不闲置**:干自己能干的(自查证据 / 再拆剩余工作)· 🔮 goal 终确认等待窗的投机窗见 [stages/goal-stage.md ④](./stages/goal-stage.md)。
- **拆分边界**:子任务**边界清晰且够大**才派(小 / 强耦合 / 强串行自己做 · 协调开销反拖慢)。
- 🔴 **编排权不外包**:stage 流转 / commit / `xx-complete` / 最终整合**永远归主对话**(并行的是执行 · 不是编排)· 代码类 subagent 只写 worktree 内路径。
- 🎚️ **派前定档**:不传 model = 继承会话模型 · **常费而不自知** —— 校验/枚举型(冷审对照 · TC 对照 · 测试执行 · 机械外化)→ 验证档;判断/创造型(Architect/PL 冷审 · 方案 · 裁决)→ **不降档**。
- 📣 **声明制(重写)**:声明**寄生在 prompt 首行**,不另起一句 —— `Meta: tier=<验证|执行|深度> · model=<留空则继承> · 理由=<一句>`。prompt 是派发时必然要写的,寄生其上才不会被忘(**高频低显著性的义务必然衰减** · 实证:agent 读过规则仍漏)。
- 🎚️ **验证类白名单一律降验证档 · 例外需用户授权**:写测试用例(TC 起草)· 执行测试 · 单测 · 集成测试 · e2e · TC 逐条对照 · 冷审执行 · 机械外化 —— 默认**全部**降档且**必须显式传 model**;认为本次特殊 → 🔴 **不许 AI 自决**,开 R5 请用户授权。判断/创造型允许继承(仍在首行声明 tier + 理由)。档位表与硬边界单源 [agents/README §一](./agents/README.md)。
- 📊 台账 `dispatch_models` 分两桶:`inherited_declared`(判定该继承 = **正确行为**)vs `unspecified`(真没分档)—— 两者干预手段相反,不可合并计数。
- 🔴 **评审模型必错开**(独立采样不变式):双路冷审(goal PL+外审 / blueprint·review Architect+外审)**两路模型必须不同**(主审路继承会话主模型 · 外审路错开一档);单路配置(fast 合并 / roster 减到一路)时**该路 ≠ 会话主模型**。**任何评审配置至少一路 ≠ 会话主模型** —— 同模型 = 盲区相关(两路同瞎)· 主对话热审 = 自审无效。验证轮降档本身即错开。
- **授权**见 § Subagent 默认授权(管「能不能用」)· 本节管「该不该用」。

### R5(b) 暂停点标准格式

🔴 **emit 任何 R5 暂停点前先跑** `state.py pause-mark --feature <path> --label '<暂停点名>'`:等待用户的墙钟计入该 stage `await_minutes`(下一个流程命令自动闭合)· 否则等待混入工作时长 · 耗时数据失真。

🔴 **投递位置**:暂停点 markdown / user_card 必须是**回合最后一条输出 · 其后零工具调用** —— 宿主可能不渲染回合中段文本(实证:卡片被吞 · 用户被迫问「url 发下」)。伴随暂停点的监控/标记类命令(pause-mark / await-merge 等)一律**先执行(后台/静默)再贴暂停点**。

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
- **判定**:任何"PMO emit 后需要用户回应才能继续"的点 = 暂停点 = 必走本格式。不可只描述情境让用户自由输入 · 不可用"回复『X』升级"等自由文本 —— 必给编号选项(斜杠并列候选清单「A / B / C」同属自由文本 · `ok` 无从解析)。
- 不可省略**编号** / **💡 推荐** / **理由**(缺任一 = 把判断甩回用户 + `ok` 快捷词失灵)。
- 🔴 **方案/变更确认类必自带变更点明细**:让用户拍板「改 X」时 · 选项之前必给**变更点清单**(对象级 · 每条一行:对象|变更|用途)—— 情境一句 + 分类概括 + 文件指针**不算**(用户被迫追问「方案是什么」= 暂停点白跑一轮)· 指针只作深读补充。
- 单选 → 1/2/3 · 多决策 → 1A/2B · 用户回 `ok` = **选 💡 推荐项**。
- 🔴 **「必带建议 + 理由」不止于三选项格式**:**任何抛给用户的决策项都算** —— PRD §待决策项逐条 · 多项一次性 escalate · 方案分叉 · 「要不要现在做 X」。**列了选项不给倾向 = 把判断甩回用户**,而 AI 有全部上下文、用户没有。
  🔴 **真推荐不了也要写明是哪一种**:① 缺信息(缺什么 · 谁能给)· ② 纯偏好(无技术优劣)· ③ 等上游决策。**空着不算** —— 用户只会被迫追问「你的建议和理由是什么」(实证 SVC-CORE-F260728:四条待决策项裸列,被逐条追问)。
  ❌ **选项集必须完整摊开 · 面向没读过产物的人写**:每个选项的内容与后果都写出(只写推荐项、让用户「可回 B」而 B 从没定义 = **假选择题**);每条带场景上下文与大白话(实证 CA-F260810:建议/理由都在,但全是术语压缩 + B 选项缺席,用户仍被迫追问 —— 拍板项四槽详 [goal-stage ④](./stages/goal-stage.md))。

### bypass 协议(R8 写操作硬门禁链 · 逃生通道)

`xx-start` FAIL → 按 `missing_prerequisites[*].hint` 自动修 + 重试(最多 3 次)→ 仍 FAIL 则走 R5 暂停点(1 继续尝试 / 2 跳过前置 ⚠️ 风险 / 3 其他)→ 用户拍板后:

```bash
state.py xx-start --bypass --reason "<用户提供>" --user-confirmed --missing <ids>
```

state.py 校验:`--user-confirmed` 必带(缺 = 立即 FAIL · 防 AI 自决)· `--missing` 必覆盖实际 missing(防漏报)· 通过后自动写 `bypass_log[]` + `concerns WARN`(审计闭环)。

**物化语义**:state.py 无法物理验证"用户真的说了" · 此 flag 的存在性 = AI 声称用户已确认。审计时发现 AI 自加此 flag(对话历史无用户确认)= 红线违规。

---

## Triage · 入口规范(5 mode 分诊 + audit_line + 移交)

> triage 是 PMO 入口行为 · 不是 state.py 命令 · 不是 stage。入口完成 → 按 mode 移交(B → prepare 子流程 / A/D/E 闭合 / C jump 状态机)。

### 🔴 管辖判据 · 直答通道(分诊之前先过)

**teamwork 只管四类工作:功能开发 / 缺陷修复 / 问题排查 / 项目规划。** 输入不属于这四类 → **直接回答 · 不走任何 teamwork 输出协议**(无 audit_line · 无 mode 宣告 · 无状态行 · 无 recap · 不套流程建议):

- **现状/知识问答**(「X 现在怎么实现的」「这配置什么意思」「项目结构长什么样」)→ grep/Read 后像正常助手一样答完就完;**通用技术问题 / 与本项目开发无关**→ 直答。
- **边界**:答完后用户追问升级成四类工作(「那把它改成…」)→ 此刻才进分诊;**不要在直答后主动推销流程**。
- 📎 mode A/D 是**项目内查询/看板**(轻仪式:可带状态行)· 直答通道是**管辖外**(零仪式)。拿不准 → 按直答处理(误加仪式的代价 > 误省)。

### 5 mode 分诊(关键词表)

| Mode | 触发关键词 | 行为 | 移交去向 | 入口完成标志 |
|------|----------|------|---------|-------------|
| **A · query** | 看下 / 查 / why / 排查 / 解释 | grep + Read 答 + 跟进引导 | — 主对话闭合 | 答完 + 跟进引导给到用户 |
| **B · execute** | 实现 / 修复 / 改 / 做 / 开发 / 新增 | audit_line · 识别为 execute 意图 | → **prepare 子流程**([docs/prepare.md](./docs/prepare.md)) | audit_line 输出 + 移交 prepare |
| **C · resume** | 继续 / resume / ship F032 | 找 state.json + jump 到 current_stage | → 状态机(直接跳 · 不重 init) | state.json 已读 + current_stage 已 jump |
| **D · status** | status / 现在到哪 / 看板 | 加载 Feature 看板 + 输出 | — 主对话闭合 | 看板 markdown 已输出 |
| **E · discuss** | 我感觉 / 你怎么看 / X vs Y / 哪种更合理 | 综合视角讨论 + 选项 + 推荐 | — 主对话闭合(讨论收敛后用户升级到 B) | 讨论收敛 · 用户给出方向或升级到 B |

**audit_line**(承接 teamwork 工作时首条响应必含 · 直答通道免):

```
🔍 triage: mode=<A/B/C/D/E>(<name>) reason=<判定理由>
```

例:`🔍 triage: mode=B(execute) reason=识别为 Feature 流程 · 命中关键词 /^实现/` —— 用户据此知道 PMO 真做了分诊。

### bootstrap flow_gates 响应(首条响应前必扫)

session 启动 `bootstrap.py` emit `checks.skill_update_check` + `flow_gates[]`(forewarn · **非 BLOCK**)· PMO **首条响应前必扫**。

🔴 **禁截断工具输出**:teamwork 工具(`bootstrap.py` / `state.py` / `update.py`)输出 = 结构化 JSON · **关键 forewarn 在后位** —— 禁 `| head` / `| tail` / `| sed -n` 等任何截断(实证:`bootstrap.py | head -50` 切掉 `skill_update_check` → 漏升级提示)· 必完整读。bootstrap 已在输出**顶部**置 `pmo_must_read` 一行 digest,但仍以完整 JSON 为准。🔴 工具输出罕见过长时应**落文件 + emit 路径**(如 external-review 写 `external-cross-review/<stage>.md`)· 不 inline 巨串诱使截断。

🔴 **入口优先级**(多信号同时触发 · 按序 surface · **不可降成底部脚注**;bootstrap 已 emit `session_entry_priority` 物化):**① 升级**(`skill_update_check=outdated` · 旧版=旧行为)→ **② 补规划**(`cold_start` gate)→ **③ 任务**(triage/启动 Feature)。

按 gate 的 `action` 字段执行:

- `prepare_check_required_before_init_feature`(常驻)→ mode B 走 prepare(详 § Mode B 移交)
- `product_overview_planning_spec_required`(项目有 `product-overview/`)→ 规划类任务先跑 `state.py planning-check`(详 [docs/feature-planning.md](./docs/feature-planning.md))
- `cold_start_product_planning_recommended`(项目无 `product-overview/`)→ **产品规划上游引导**:
  - **地图 vs 规划解耦**:`teamwork-space.md`(知识地图根)由 **bootstrap 自动建骨架**(非规划内容 · 无需 R5)· `product-overview`(愿景/业务架构/执行线)**要人建** —— gate fire 于**它**缺失。
  - **权威顺序**:`product-overview`(PL 引导)→ ✅确认 → 回填 `teamwork-space.md` 子项目清单 → Feature Planning(涉 UI 先出全景初步规划 → 拆 WS / ROADMAP)→ Feature 状态机。
  - 按 mode:bare `/teamwork` 与 **mode D** → 首条响应 emit 下方 R5 暂停点(不当静默看板 · 即便已有 PROJECT/ROADMAP 仍 surface · 不降级成脚注)· **mode B** → 同一暂停点(执行前先问要不要补上游)· **mode A/E** → 轻提一句(不强暂停)· **mode C** → silent skip。
  - **R5 暂停点动作**:① 进产品规划冷启动(PL 引导建 product-overview → ✅确认 → 回填 teamwork-space.md)💡 / ② 跳过直接做任务(后续可补)/ ③ 其他 · 🔴 **用户拍板前不擅自建 `product-overview/`**(R5)。

Feature Planning / 冷启动 / 产品规划上游**不进状态机 · 无 state.py 兜底**(物化盲区 · 用 forewarn gate 补)—— 漏扫 flow_gates = 退回 v7「凭记忆读 spec」。

### Mode A / E 升级触发(PMO 主动建议 · 不等用户提)

mode A 排查 / mode E 讨论收尾时命中以下场景必须建议升 mode B:

- **多 Feature 范围拆分** / **ROADMAP 更新** / **P0/P1 优先级排序** → 升 **Feature Planning**
- **新功能实现方向** / **架构决策点** → 升 **Feature**(走 goal PRD 而非主对话伪 PRD)
- **已知 bug 根因 + 修复方案** → 升 **Bug**

🔴 升级建议本身是暂停点 · 走 § R5(b) 标准格式 · 且:**多候选动作逐一编号**(斜杠并列 = 自由文本 · `ok` 无从解析)· 选项**具体化自排查结论**(「先修正 staging 配置(不改代码)」而非抽象流程名)· **💡 推荐必给** = 排查结论指向的最可能动作(排查者最有信息量)· 选项动作写清进流程的落法(「prepare → init-feature → <first_stage> stage」)· 末项留「暂不处理 / 其他指示」(报告留档 · 可记入 `product-overview/PENDING.md`)。

### Mode B 必移交 prepare 子流程

mode B 识别后(**无论后续 flow_type = Feature〔full/micro〕还是 Bug · 都走 prepare**)· PMO **必走** [docs/prepare.md](./docs/prepare.md) · 不可在主对话散述准备步骤。

🔴 **mode B emit 任何 prepare 内容前 · 必先用 Read 工具打开 [docs/prepare.md](./docs/prepare.md)**(命令式 · 不是"参考")· 不读直接 emit 5 段 = R5 违规 + **必漏 §2.1 复杂度升级判据**(跨独立 git 仓库 / 数据模型重构 / 老需求架构性废弃 / 影响 ≥2 BL / 方向级业务变更 → 强制升 Feature Planning)**与 §2.2 preset=micro 准入校验**(零逻辑变更 + 仅 文案/样式/资源/配置常量/注释 · 超纲一律 full)—— 二者判定权威在 prepare.md · 此处只作警觉锚点。

判据:**进状态机 = 走 prepare**(Feature〔full/micro〕+ Bug 三条链都需 worktree + branch + merge_target + artifact ID 4 项配置 · ID 统一 **F/B**〔M 为 legacy 存量〕· 详 conventions.md §1)。即便最轻的 Feature·micro(改文案 1 行)也要 prepare。不进状态机的 Feature Planning / 问题排查 → 不走 prepare。

🔴 **物化硬墙**(两道):
- **prepare-check audit 门禁**:`state.py prepare-check` 跑成功写 audit jsonl(`~/.teamwork/prepare_check_audit.jsonl`)· `state.py init-feature` 校验近 60min 内有匹配 `--feature-id` 前缀的 audit record · **无匹配直接 BLOCKED**。
- **admission-judgment 必传**:`prepare-check` 必传 `--user-intent "<用户原话>"` + `--admission-judgment '<JSON>'`(含 sections_reviewed[] + matched_signals[] + recommended_flow_type + ai_rationale)· 缺任一 BLOCKED · **无 SKIPPED 兼容口子**。推荐流程 ≠ 实选 flow_type → emit WARN + audit 留痕(不强 BLOCK · 可能合理例外)。
- bypass(调试):`TEAMWORK_BYPASS_PREPARE_CHECK=1`(走 init-feature 门禁旁路 · prepare-check 仍校验 admission_judgment)。

### 待规划需求池(命中查询意图时扫描)

**触发条件**:mode A query 命中「待做 / 待规划 / pending / backlog / 待办」「还有什么 / 还要做 / 接下来做什么 / 下一个」「看下池子」时 · PMO **按需读** `product-overview/PENDING.md` · 列 status=📝/🔄 的项:

```
📋 待规划需求池:N 个 active 项(详 product-overview/PENDING.md)
1. PENDING-NNN · <标题>(来源:<source> · 状态:📝/🔄)
2. ...
回 "启动 PENDING-NNN" → 进 prepare 子流程 · 或 "稍后" 闭合。
```

**不扫场景**:mode B/C/D/E 入口 / 关键词不命中 / 池空 → silent skip。
**追加**:stage 内识别"本 Feature 范围外但要做"→ 用户确认后 append 到 `product-overview/PENDING.md`(无该文件则从 [templates/pending.md](./templates/pending.md) 建)。
**闭环清理**:PENDING-NNN 转 ✅ 已转 或 ❌ 不做 → **立即从表删** · 关联落对应 Feature `state.json.related_pending`。表始终只留 active。

### 入口红线 R-T1/2/3 + 接口边界

- **R-T1 · PMO 必先分诊**:承接任何用户输入必先完成 5 mode 分诊 + audit_line · 不可跳过直接 init-feature / stage-start
- **R-T2 · mode B 必移交 prepare**:triage 只做 mode 分诊 · 不做流程类型识别 / worktree 决策 / 暂停点(都是 prepare 的事)· 不可自己跑 git worktree add / init-feature
- **R-T3 · resume(mode C)不重 init**:jump 到现有 state.json;state.json 不存在 → 退回 mode B

**triage 入口完成 = init-feature 前置满足**:worktree 物理已创建(PMO 显式跑)· cwd 在 worktree 内(PMO 显式 cd)· artifact ID + branch + merge_target 已用户确认。
**init-feature 物化拦截**:worktree_mode != off 但 cwd 不在 worktree / worktree 物理不存在 → FAIL。
**triage 不做**:❌ 不写 state.json(init-feature 创建)· ❌ 不创建 worktree(PMO 显式跑)· ❌ 不自动跑 git(防漏看用户确认)。
📎 项目级骨架(KNOWLEDGE/TROUBLESHOOTING/GLOSSARY)由 init-feature 自动维护 · 不是 triage 职责。
📎 mode 判定不准 → 用户可指定重判;worktree 决策 / git 失败 → 详 [docs/prepare.md § 错误处理](./docs/prepare.md)。

---

## 流程类型(R2 闭集)

`flow_type ∈ {Feature, Bug}` + Feature 重量档 `preset ∈ {full, micro}` · Planning / 排查不进状态机 · 轻量由**动态 roster + clarity** 承担(legacy 别名自动映射)。**telos 与链条单源 = [FLOWS.md](./FLOWS.md)** · **判定权威 = [docs/prepare.md](./docs/prepare.md)**。

### 授权暂停点清单(非 auto 模式 · 每个独立 emit + 等用户)

🔴 **非 auto 模式 · 以下每个授权暂停点 PMO 必独立 emit + 停 + 等用户回应** · 不可凭一个 `ok` 推全程:

| 流程 | 授权暂停点(按顺序) |
|---|---|
| **Feature** | ① prepare 4 项配置 → ② goal PRD 最终确认(📄 回显 PRD 绝对路径)→ ③ ui_design UI 预览确认(若 --needs-ui) → ③′ panorama_sync L2 结构变更跨团队确认(条件 · L1 不停) → ④ blueprint 方案要素确认(条件:DB 变更 / 🛡️ 兜底清单非空 · 见下) → ⑤ pm_acceptance 三选项 → ⑥ ship1 终点 等平台合并 feature MR |
| **Bug** | ① prepare 4 项配置 → ② **diagnose 修复方案确认**(根因+方案 · 用户拍板才进 dev) → ③ pm_acceptance 三选项 → ④ ship1 终点 |
| **Feature · micro** | ① prepare 4 项配置 → ② ship1 终点 等 MR 合入(execute 零门禁 · 无 pm_acceptance · 用户验收 = ship1 MR diff review)|

📎 **blueprint 方案要素条件暂停点**(双触发):TECH 涉**数据库数据结构变更**(表/字段/索引/约束/migration)**或 🛡️ 含安全/降级兜底策略**(兜底不许默默做 · 复杂度×收益经用户拍板)时 · blueprint-complete 前必 emit 确认暂停点(详 [stages/blueprint-stage.md ④](./stages/blueprint-stage.md))· 不涉及则跳过。**Bug / Feature·micro** 不应涉及 DB 数据结构变更(命中则升 full 完整链)。
📎 **其余条件暂停**(命中才停 · 不入上表主链):goal 早问门三闸(如涉既有行为变更升级待决策)· review 轮次超预算升级。
📎 stage 间(goal-complete→ui_design / dev→review 等)是 state.py **自动流转** · 非暂停点 · 不插确认。

### auto_mode=true 时各暂停点行为(按名 · 不按编号)

🔴 `auto_mode=true` = 显式委托 AI 完成 stage 间流转。**仅"用户决策权"类暂停点保留 stop**;**"技术 / 设计 / 评审"类暂停点 AI 代用户接受确认 + 文档化**。🔴 这是**跳过用户确认暂停点** · **绝非**跳过/伪造**评审工作本身**——评审(多角色 + 第三视角)照常真跑。

| 暂停点 | auto 行为 | 理由 |
|---|---|---|
| **prepare 4 项配置** | **stop** | 用户初始配置(artifact ID / worktree / branch / merge_target)· AI 不能替选 |
| goal PRD 最终确认 | skip | PRD 已多角色 review(**真跑**)· 跳的是**用户确认** · 非评审本身 |
| diagnose 修复方案确认(Bug) | **skip + WARN** | 按推荐方案继续 + `add-concern --severity WARN --message "auto skip: diagnose 方案 ..."` 留痕 · 修偏由 pm_acceptance 兜 |
| ui_design UI 预览确认 | skip | 设计意图已落 UI.md / preview · auto 用户接受 |
| panorama_sync 跨团队 reviewer(仅 L2 结构变更停 · L1 任何模式都不停) | **skip + WARN** | `panorama-change-summary.md` 已文档化 · 必 `state.py add-concern --severity WARN --message "auto skip: panorama change scope=..."` |
| blueprint 方案要素确认(DB 变更/兜底) | **skip + WARN** | 高影响 · 必 `state.py add-concern --severity WARN --message "auto skip: 方案要素确认 · DB: .../兜底: ..."`(便于 dev/review 复查) |
| **pm_acceptance 三选项** | **stop** | 产品决策权:approved_and_ship / approved_no_ship / rejected_with_feedback · AI 不能替用户拍板(违 R3) |
| **ship1 终点 等平台 merge feature MR** | **stop + 监控** | 用户在 git host 平台操作 · AI 无法代办 · 🔴 stop = 不替用户点合并 · **仍必须跑 `await-merge` 轮询**(所有模式 · MERGED → 自动 ship-finalize)—— 否则用户合了没人收尾 |

🔴 **skip + WARN 行为**:跳过暂停点但必 `state.py add-concern --severity WARN` 写一条 audit 锚定 AI 自决的范围。
📎 `worktree_mode=auto` ≠ `auto_mode` —— 前者是 worktree 物理校验模式 · 与暂停点自动流转**完全无关**。

### fast 模式(评审收敛为两端单路 · 默认关 · localconfig 配置)

🔴 `.teamwork_localconfig.json` 的 `fast_mode: true` 开启(**缺省/false = 关** · init-feature 时快照进 `state.fast_mode` · 中途改配置不影响 in-flight feature):

- **留两端 · 各合并单路**(roster = `{goal: [fast], review: [fast]}` ·「fast」= 合并伪角色 · 单 agent 兼多帽 · 🎭 该单路模型 **≠ 会话主模型**):
  - **PRD 评审(goal)**:一路隔离冷审兼 **PL + 外审**关注点(质疑六问 ≥1 实质 + 可实现/可验证 + AI 自主方向)· 产单份 PRD-REVIEW.md(`reviewers: [fast]`)· verdicts 全 APPROVE 门照拦;
  - **代码 review**:一路隔离评审兼 **Architect + QA** 关注点(实现↔设计一致性/简洁性 counter-lens + 测试真实性与覆盖/代码质量盲区)· 产 REVIEW.md 单份 · findings/severity/验证轮协议照跑。
- **去掉**:blueprint 评审(不产 TECH-REVIEW.md · TC/TECH 写完直进 dev)· 两端的多路独立性。
- 🎯 **评审最多 2 轮**:goal 冷审与代码 review 预算各封顶 2 轮(首轮全量 + 1 验证轮 · localconfig `max_review_rounds` 更小则从小)· 轮尽未收敛 → **未收敛决策点抛用户拍板**(goal → 列进 PRD 终确认导读;review → 引擎 review-retry 硬拦 · R5 暂停点列 open findings + 1/2/3)。
- **保留**:测试证据硬门(exit 0/差分)· verify-ac · **全部用户暂停点**(prepare 4 项 / PRD 最终确认 / DB schema 确认 / pm_acceptance / ship1)· worktree 纪律 · ship 全链。
- 🔴 **yolo 忽略 fast**(不报错):yolo 无人值守靠全量评审安全网 —— `--yolo` 时 fast_mode **静默不生效**(kickoff 记 INFO 留痕)· fast 仅有人值守生效;与 auto_mode 正交可叠。
- 适用:原型 / 个人项目提速;正式项目慎用(独立多路评审是拦真 bug 主力)。

### yolo 模式(完全自动 · 无人值守 · 高风险)

🔴 `yolo` = `auto_mode` **超集** —— 启动后**零 stop**(连 pm_acceptance 产品验收 + MR merge 都自动)。启用:`init-feature --yolo [<分支>]`(自动 implies `auto_mode`)。

🔴 **yolo 预研门**(正式自主前 · 物化硬门):`init-feature --yolo` **前**必产出 `YOLO-PREFLIGHT.md`(模板 [templates/yolo-preflight.md](./templates/yolo-preflight.md))—— ① 深入调研真实代码(grounded 实际文件 · 不靠假设)② 提炼**核心重要决策**(错了会让整条自主跑偏的:技术路线 / 数据模型 / 对外契约 / 范围取舍 / 安全)③ 和用户**逐条确认**。`init-feature --yolo` 校验该产物存在 + 已填(哨兵 `YOLO-PREFLIGHT-UNFILLED` 已删 + 含核心决策/用户确认段)· 否则 FAIL。理由:零暂停点 = 意图偏差**没机会中途纠** → 意图保真膜必 front-load 到跑前。

- **`--yolo <分支>`** = 本需求专属 `merge_target`(**覆盖** `--merge-target` / localconfig 默认)· 推荐给 yolo 一个专属集成分支隔离自动合入的代码(如 `--yolo yolo/feat-x`)
- **`--yolo`**(无值)= 用 `--merge-target` 的分支(二者至少给一个 · 都没 → FAIL)
- **中途切换** = `state.py set-mode --feature <F> --yolo [<分支>] --reason '<原因>'`(或 `--auto-mode` / `--no-yolo` / `--no-auto-mode`)· 走 `state.mode_changes` audit + 同款非 main 硬门 + implies-auto 护栏 · **不要 raw-write `state.json` 改 auto_mode/yolo**(无 audit·绕门禁)

🔴 **yolo ≠ 简化/提速 · 是「加重审核」**:无人值守 = 没人在看 → 自动化评审是**唯一安全网** · 必须保留/加重 · **绝不削弱**。yolo 的「零 stop」**只**针对**人工决策暂停点**(prepare / pm_acceptance / MR merge)。

- **roster 内评审全真跑 · 一个不少**(默认两路:Architect 主审 + 覆盖方向制第三视角〔QA 视角并入必覆盖方向〕)· **不得以「集中到 review stage」「效率」「价值低」为由去掉第三视角** —— `change-review-roles` 物化 BLOCK。
- 🔴 **真跑的物化校验**(严格按流程流转 · 不得「内化」自盖章 APPROVE · 不得 AI 手写 `external-cross-review/*.md`):第三视角必走 `state.py external-review --stage <X>` —— **默认 subagent 隔离冷审** → 校验 frontmatter `review_via: subagent`(无 → FAIL);**opt-in 异质** → 真调异质模型 + `~/.teamwork/external-review-logs/<feat>/codex-<stage>-*.log` 实跑日志(无 → FAIL · 伪造不了)。
- 🔴 **第三视角 = 🎭 错开模型 subagent 隔离冷审(唯一形态 · 跨厂商 CLI 异质已退役 —— 冷启动/慢路径/登录故障面实测严重拖慢)**:`state.py external-review` 只 emit subagent 配方(不 exec 子进程)· 产物须 `review_via: subagent` + 照实申报 `review_model` · 🔴 yolo 额外要 prompt doc(实跑证据 · 防手写自盖章)。—— **不许「不冷审」**(主对话自评 = 无独立性 · 门禁拦)。
- **不得擅自合并 BL / 跳 stage / 减 review 轮次 / 简化流程**(BL 拆分是 Planning 已定的范围)· ✅ **可以加重**:多跑 external、加 review 轮次、提高测试覆盖。

| 暂停点 | yolo 行为 |
|---|---|
| prepare 4 项配置 | 启动前给(kickoff 输入 · 非运行中 stop) |
| pm_acceptance 三选项 | **自动 `approved_and_ship`** + `state.py add-concern --severity WARN` |
| ship Phase 1 等平台 merge MR | **自动 merge**:`gh pr merge --auto --merge`(GitHub · check 全过才合)/ `glab mr merge`(GitLab) |
| ship-finalize(Phase 2 主工作区收尾) | **自动跑**(merge 确认后 · 见 main-sync) |

🔴 **硬约束**(init-feature 物化 gate · `_is_main_branch`):`merge_target` **必须非主分支**(`main`/`master`/远端默认)· 否则 `init-feature --yolo` 直接 FAIL。理由:无人 review 自动 merge · 不得让 AI 错误/幻觉直接进 main —— 只能合到 `dev`/`staging`/`integration` 等集成分支 · 主分支的提升仍由**人工 gate**。

⛔ **外部世界动作边界(用户拍板 · 同一风险模型的延伸)**:公网 registry 发布(npm/PyPI/crates 等)/ **创建公开仓** / 生产部署等**不经过分支门且不可逆**的动作,**不在「零 stop」范围** —— yolo 的自动只覆盖**分支门以内**(验收 / 合入集成分支 / 清场)。此类动作 = release 域(`RELEASE-GUIDE.md` · 发布归用户):**先自动验收 + 合入 + 清场(不阻断),外部发布单独停给用户拍板** · ❌ 不得以「有外部发布」为由把验收/合入也停下(实证 SDK-F260809171303:AI 把「外部发布该问用户」的正确直觉挂错到 pm_acceptance,停掉了本该自动的验收与合入)。why:上一条硬约束的安全网 = 主分支人工提升,而外部动作**绕过一切分支门** —— 一次幻觉级错误(泄密 / 白名单漏洞)直接入公网且不可撤。

**安全栏**:
- **尊重分支保护**:目标分支受保护 / 必需 check 没过 → `gh`/`glab` merge 失败 → 自动退回「手动 merge」stop + WARN(**绝不** force / 绕保护)
- **审计**:每个自动决策(pm_acceptance 自动过 / 自动 merge)写 `add-concern --severity WARN` 留痕
- **per-feature opt-in**:`--yolo` 不 sticky(每次显式传)· `state.json.yolo=true` 留痕

**自主解决(yolo 核心:失败/卡点也零人工)**:

| 卡点 | 正常(非 yolo) | yolo |
|---|---|---|
| stage 校验 FAIL | AI 修 + 重试 · 3 次仍 FAIL → 暂停问用户 bypass | **AI 持续自主解决**(更多轮 / 换思路 / 深挖根因)· 不向用户升级 |
| review NEEDS_REVISION / test FAIL | AI 改 + retry | 同上 · 持续修到绿 · 🔴 **同 stage fix-retry ≤10 轮**(超 → 硬停止损 surface · 收敛失败 ≠ 继续死磕) |
| bypass 协议(R8 写门禁) | 停 · 等用户 `--user-confirmed` | **AI 自授权**(`--yolo` = 用户 blanket 委托 · `require_user_confirmed` 物化放行)· 仍 `--reason` + `bypass_log` + concerns WARN |
| external CLI 缺/超时(仅 opt-in 异质) | — | **降级 subagent 冷审**(非去掉第三视角)· 冷审仍真跑 |
| merge 冲突 | 停 | AI 解冲突(非主分支一般无保护) |

**优先级:解决 > 绕过** —— bypass 只是穷尽自主解决后为不停下的最后兜底 · 每次必 WARN 留痕(审计看 `bypass_log` 频率 = yolo 健康度)。**真·硬停**极少(环境彻底不可用:网络死 / `gh`/`glab` 没装 / 磁盘满 / token 失效)· 仍先重试 / 找替代。

---

## 项目级文档信息架构(teamwork 框架规范)

> **teamwork 要求用户项目根含以下文档** · `init-feature` 自动维护(骨架 silent 复制)。

### 知识三层律(框架定位)

teamwork 承担**知识导航(索引/地图)**的责任 —— 让 AI 从一个根入口**零死角**抵达任何项目知识 —— 但**不承担知识内容**(内容会与代码漂移 · 腐烂后反向误导)。

| 层 | 角色 | 权威 | 陈旧时 |
|---|------|------|--------|
| `teamwork-space.md` + 各 doc | **地图**(指针 / 路由 / 一句话摘要) | teamwork 维护 | 指错一格 · 打开仍对(优雅降级) |
| **代码** | **领土**(细节唯一真相) | 🔴 **代码** | 永远现 grep+Read · 不信文档转述 |
| 归档 `_archive/*.zip` | **冷库**(已交付过程文件) | `_archive/INDEX.md` 索引 | 先读 INDEX 描述判相关 · 必要才解压 |

- **律法 vs 地图分工**:本节(SKILL)= 律法(generic 文档*类型*语义 + 话题路由 · 每项目一样 · 不复制进项目)· 项目的 `teamwork-space.md` = 地图(本项目*实例*的知识入口索引)。
- **地图根 = `teamwork-space.md`**(本项目「索引之索引」· 读取时点见 § session 入口必读)· 它指向的领土(代码 / 大文档)**按需懒加载**。
- **N≥1 统一模型**:1 个 `teamwork-space.md`(地图根)+ N≥1 个逻辑子项目(职责单元 · 非物理仓)· 单项目 = N=1(与是否 monorepo 无耦合)。

### 文档清单 · 权威范围 · 路由

> 🔴 **文件位置权威 = 各 `templates/*.md` 头部「位置:」声明**(单源 · 本表路径只作速查 · 冲突以模板为准)。产物**不在项目根裸放** —— 规划/设计类默认落 `docs/`(单项目)或 `{子项目}/docs/`(多项目)。

| 文档 | 权威范围 | 何时读(用户提到 / AI 需要) |
|------|---------|---------|
| `product-overview/{}_业务架构与产品规划.md` | 产品愿景 + 业务架构 + 执行线列表(taxonomy) | 规划 / 拆能力 / 起 WS / 路线图全景 / 执行线反查 |
| `product-overview/workstream/WS-NN.md` | 规划单元(一组 feature 的拆解 · 承接 1+ 执行线) | 起 WS / 看某规划拆了哪些 feature |
| `product-overview/PENDING.md` | 待规划需求池 | backlog 类查询命中时(见 § 待规划需求池) |
| `{子项目}/docs/PROJECT.md` | 产品全景(子项目级) | 讨论产品方向 / 创建 Feature |
| `docs/ROADMAP.md`(单项目)/ `{子项目}/docs/ROADMAP.md` | Feature(BL) 列表 + 优先级 + 排期 + 关联 WS | Feature 优先级 / 排期 / 创建 Feature |
| `{子项目}/docs/design/sitemap.md`(与全景 panorama 同目录) | 信息架构 / 页面层级 | 讨论 UI / 页面层级 / 创建含 UI 的 Feature |
| `project-specs/DEV-RULES.md` | **项目强制开发规范(人维护)**:API 契约 / 错误处理 / 其他约定(架构归 ARCHITECTURE.md+ADR · 命名/风格/测试策略走 standards 缺省) | **blueprint(TECH)+ dev(实现)必读** · 问开发规范/约定 |
| `project-specs/UI-RULES.md` | **项目设计规范(人维护)**:控件偏好 / 色板策略 / 交互约定 / a11y(装**策略**不装视觉值 —— 视觉值在 preview-project tokens) | **ui_design 必读** · 问设计规范/控件选型/配色策略 |
| `project-specs/test-baseline.md` | 红 base 测试基线(brownfield 预存在失败清单 · `state.py test-baseline --add` 生成) | 测试非全绿但非本次引入时(差分「0 新增」判定) |
| `project-specs/KNOWLEDGE.md` | Gotcha(踩坑)/ Preference / 已澄清歧义 / 已否方向(AI 沉淀) | triage 期 + 涉项目踩坑/历史坑/用户偏好 |
| `project-specs/GLOSSARY.md` | 业务术语 + 实体关系 + 命名约定 + 别名歧义 | PRD / TECH 起草前 · 问术语/实体/别名 |
| `project-specs/TROUBLESHOOTING.md` | 排查 / 运维操作手册(log / DB / 监控 / 部署 · **人维护 · AI 不代写**) | 报错 / 502 / 查 log / 异常 / 服务挂 / 查环境 / 查 DB / 查 Redis / 部署 / 回滚 |
| `project-specs/RELEASE-GUIDE.md` | **版本发布规范(人维护)**:集成分支→生产(默认 staging→main MR · URL 置顶 · 提醒用户合入 · 发布后补 release-gated 证据) | 用户说「发布 / 上线 / 发版」时 **PMO 必读照办**(合入归用户) |
| `project-specs/ARCHITECTURE.md` | **workspace 级**系统架构(子项目拓扑 + 依赖 + 目录布局) | 跨子项目架构 / 系统全貌 |
| `{子项目}/docs/architecture/ARCHITECTURE.md` | **单子项目内部**技术架构(技术栈/分层/模块) | 某子项目内部架构决策(模板 `templates/architecture.md`)|
| `docs/architecture/database-schema.md` | 数据库 schema | 讨论数据模型 / schema |
| `project-specs/PROCESS-LEDGER.md` | **流程价值台账**(一行一 feature:external 采纳率 / 角色真 finding / 暂停点互动 / bypass) | ship2 随收尾 MR append(详 [stages/ship-stage.md §16](./stages/ship-stage.md))· 流程审视 |
| `external/` | 三方/外部资源文档(SDK / 协议 / 供应商) | 对接外部系统 / 三方 API |
| `docs/features/{F}/` | 具体 Feature 产物 | 提到 F\d+ |
| `{子项目}/docs/adr/` + 其 `INDEX.md` | 架构决策记录(🔴 **唯一落点 · ADR 不落 Feature 目录** · 单源 `templates/adr.md`)| 历史决策 |
| `{子项目}/docs/features/_archive/INDEX.md`(单项目=repo 根 `docs/features/_archive/`) | 🔵 **归档冷库目录**(已交付 feature 的 id+描述+时间+zip 路径) | 查已交付/历史 feature / 翻旧账 · 先读描述判相关 → 必要才解压 zip |
| `teamwork-space.md` | **地图根**(索引之索引 · 结构 / 子项目清单 / 跨项目变更 ID) | 任何 session 必读 · 多子项目 / 知识全景入口 |
| 代码 | **细节唯一真相** | 涉及具体代码 → grep + Read(不信文档转述) |

🔴 **AI 自己需连环境(查 DB / log / 服务 / 跑运维命令)时也走 `TROUBLESHOOTING.md`** —— 不只"用户提到",含规划期代码调研需 live 数据、stage 内联调/排错。**先读它拿连接 + 操作方式,别凭 `.env` / 启动脚本瞎试**。它是**人维护**文件(同 DEV-RULES 模式)· **AI 不在流程中改它**:连法缺失/自己摸索出来的 → 记 `KNOWLEDGE.md`(AI 沉淀)+ **提示用户**固化进 TROUBLESHOOTING · 不代写。

### 项目级系统维护(`tools/bootstrap.py` 独立脚本)

**每个 session 启动时 · PMO 首条响应前必跑**(silent · 不打扰用户)· 独立脚本 · 不归 state.py 状态机域:

```bash
python3 <SKILL_ROOT>/tools/bootstrap.py --host <claude-code|codex-cli|gemini-cli|unknown>
```

🔴 **只传 `--host`**:宿主是 AI 关于自身的事实(不在文件里 · 须显式)。`--skill-root` 自推、版本号 bootstrap 自读 `SKILL.md` frontmatter(单源)—— **AI 不传版本号**。`<SKILL_ROOT>` = `~/.claude/skills/teamwork` 或 `~/.codex/skills/teamwork`。

**host 是 per-feature**(非全局 · 否则全局 audit 跨 session 污染):`init-feature --host` / `<stage>-start --host` 写 `state.json.host` · `external-review` 读 state.json.host;跨 session 切宿主用 `<stage>-start --host <new>` 显式覆盖(自动 emit `host_change_warning` + concerns);`~/.teamwork/host_audit.json`(全局)仅 fallback · 读到会 emit `deprecation_warning`。

bootstrap 做什么:版本号自读 frontmatter · 项目骨架检查/创建(project-specs/ 下 KNOWLEDGE/TROUBLESHOOTING/GLOSSARY · 旧散放自动迁移)· 宿主指令文件历史注入段清理 · state.json v7→v8 迁移扫描 · **知识图谱结构可达性校验**(归档 `INDEX.md`↔`*.zip` 双向对账 + workspace 节点登记 · 命中 emit `checks.knowledge_graph` WARN · 🔴 只查**可达性**不查内容新鲜度)。
特性:全 silent(不 emit 用户可见报告)· 失败不阻塞 · 幂等 · AI 跑后不必 cite。

### session 入口必读 · 项目结构索引(silent · bootstrap.py 后 / mode 分诊前)

🔴 PMO bootstrap.py 完成后 · 进 mode 分诊前 · **必 silent Read `teamwork-space.md`**(存在即读 · 缺失 silent skip)—— 它是轻量结构索引(通常 < 200 行)· 已含分诊所需全景上下文。**PROJECT.md / ROADMAP.md / sitemap.md / PENDING.md** 等详档**按需读**(不全文加载 · 避免 context 浪费)。

🔴 **文件名**:规范名是连字符 `teamwork-space.md`。legacy 下划线名 `teamwork_space.md` 由 `bootstrap.py` 在本步**之前**自动迁移 —— 故此处只找连字符名(下划线名会导致子项目 registry 静默不加载、路由失效)。

**创建/维护规则**(字段语义 / 硬规则 / 生命周期 / 进度统计 / 跨项目变更单源)→ [docs/teamwork-space-guide.md](./docs/teamwork-space-guide.md)(模板 [templates/teamwork-space.md](./templates/teamwork-space.md) 只留实例化骨架)。

**silent read 原则**:内部 read · 只读相关段 · 不输出「我现在 read X 看看」。

---

## 状态行(R5 软约束)

**AI 每次主对话回复(在 teamwork 流程内)末尾必含状态行 · v8 3 行格式**(🔴 作用域:**有活动 feature/流程时**才输出 · 直答通道与管辖外轮次**免** —— 给闲聊贴状态行 = 仪式噪音):

```
🔄 {feature_id} ({flow_type} · {current_stage}) | 下一步:{next_action}
📁 {artifact_root}
🌿 {branch}(worktree: {wt_path · 与 artifact_root 不同时显示})
```

**示例**(占位 · 实际路径由 prepare 按 conventions.md §9-12 + `.teamwork_localconfig.json` 推导 · **AI 禁止直接抄此例字符串**):
```
🔄 {Feature-ID} (Feature · blueprint) | 下一步:dispatch QA TC + RD TECH
📁 {repo-root}/{artifact-root}/{Feature-ID}
🌿 feature/{feature-id-kebab}(worktree: {repo-root}/.worktree/{Feature-ID})
```

**取值**:`state.py` 每次 `xx-start` / `xx-complete` emit 顶层含 `status_line` 字段(brief 末尾也 append「📊 状态行模板」段)· 纯对话回复用最近一次输出的 status_line(或从 state.json 读 + render)。
📎 worktree path 物化校验:init-feature 强校验 `{worktree_root_path}/{Feature-ID}` 约定 · 错位 → FAIL with hint。
**反模式**(命中 = 流程偏离):无状态行 / 不按 3 行格式 / next_action 与实际下一步不符。

---

## 核心保证(对应 v7 9 红线 R1-R9)

v8 把 9 红线的可枚举子条目物化进 state.py;R3 + 部分行为约束(R4 / R5(b) / bypass)是 PMO 软约束(口径单源 = 本文件 § PMO 软约束)。

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

---

## 文档导航

| 文件 | 作用 |
|------|------|
| [FLOWS.md](./FLOWS.md) | 流程闭集 telos(Feature/Bug × preset + 2 个不进状态机) |
| [STAGES.md](./STAGES.md) | **stage 编排单源**(定义 / 链 / 通用纪律 / 执行方式 §4 / spec 四段结构) |
| [ROLES.md](./ROLES.md) | 角色索引(→ roles/*.md) |
| [standards/HARD-RULES.md](./standards/HARD-RULES.md) | **工程硬规则白名单**(standards/ 唯一必读 · 逆模型默认 + 框架约定 · 分册索引在其尾部「相关」) |
| [templates/README.md](./templates/README.md) | 文档模板索引(格式唯一真相源 · 全清单 + 消费方) |
| [PRODUCT-OVERVIEW-INTEGRATION.md](./PRODUCT-OVERVIEW-INTEGRATION.md) | 产品规划上游(product-overview 引导 / 规划状态管理) |
| [stages/*.md](./stages/) | 各 stage Telos + 硬规则 + Output Contract(校验进 state.py) |
| [roles/*.md](./roles/) | 角色 telos + 创作要点(协作进 state.py) |
| [agents/README.md](./agents/README.md) | Subagent 执行协议(**档位表单源** / dispatch / Progress Log / 状态分级) |
| [docs/prepare.md](./docs/prepare.md) | mode B 必经 prepare 子流程(流程识别 / worktree / 关键词表) |
| [docs/feature-planning.md](./docs/feature-planning.md) | Feature Planning 流程(Step 0-10 · 全景 / WS / 收尾) |
| [docs/conventions.md](./docs/conventions.md) | 命名与目录约定(ID / BL / 文档路由 / worktree 路径) |
| [docs/teamwork-space-guide.md](./docs/teamwork-space-guide.md) | teamwork-space.md 维护规范 |
| [tools/state.py](./tools/state.py) | 唯一编排器入口 |
| [tools/_v8_engine.py](./tools/_v8_engine.py) | 通用 stage start/complete + bypass 引擎 |
| [tools/_v8_stage_specs.py](./tools/_v8_stage_specs.py) | 12 stage 完整契约(stage 数单源 `STAGE_SPECS`) |
| [tools/_v8_ship.py](./tools/_v8_ship.py) | ship-phase actions + ship-finalize + await-merge |
| [tools/bootstrap.py](./tools/bootstrap.py) | session 启动维护(骨架 / 历史注入段与 hooks 清理 / legacy codex agent toml 回收) |
| [claude-agents/](./claude-agents/) | 第三视角冷审 prompt 模板(`state.py external-review` 组装进配方 · codex-agents 已随跨厂商退役删除) |
| [docs/CHANGELOG.md](./docs/CHANGELOG.md) | 变更记录 · [RETRO-LEDGER.md](./docs/RETRO-LEDGER.md) 一行一版自省 |

---

## License

MIT
