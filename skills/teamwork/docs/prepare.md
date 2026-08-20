# Prepare · 进状态机前的准备子流程

> **可重入子流程** · 任何"决定要走某流程"的 PMO 主对话点都走一次。
> 输入:用户意图(自然语言 / Feature Planning 中的 BL-NNN / 升级讨论收敛)
> 输出:`state.py init-feature` 的参数 —— 4 项用户确认配置(feature_id + worktree_path + branch + merge_target)+ flow_type(+ 可选 `--preset` / `--clarity` / `--bl`)

---

## 0. Must-read(PMO 进 prepare 前必读)

🔴 **必读 spec**(prepare 动手前读):
- **[conventions.md §9-12](./conventions.md)** — worktree path 规范(`{worktree_root_path}/{Feature-ID}` · 默认 `.worktree/`)
- **`.teamwork_localconfig.json`** — 项目级 worktree_root_path 配置(读 `worktree_root_path` 字段 · 不存在用 `.worktree`)
- **[feature-planning.md §0](./feature-planning.md)** — 何时改走 Feature Planning(关键词 + 复杂度双触发)

🔴 **PMO 必先 Read 本 prepare.md(工具调用)再 emit 任何 prepare 内容** —— SKILL.md 只给"移交 prepare 子流程"指针 · 具体 emit 模板(🎯 意图确认 + ⚙️ 配置)/ 准入校验 / prepare-check 用法都在本文件。不读直接 emit = R5 违规(详 §0.5 #1)。

---

## 0.5 反模式黑名单

🔴 **AI 凭直觉 / 短回路跳步骤 · 大概率被用户叫停重做 · 不省 token · 反多消耗**。以下都是 R5 违规 · emit 前逐条自检(任一命中即重来):

| # | 违规 | 触发场景 | 治本 spec 位 |
|---|---|---|---|
| 1 | 漏 Read 本 prepare.md · 凭 SKILL.md「移交 prepare」概览就 emit | mode B 首次触发 prepare | § 0 必读 |
| 2 | 漏跑 `prepare-check`(或漏 / 错 `--features-root`)· 用 `ls` / `grep` 手算 next ID | 「目录看一眼就知道」/ monorepo 子项目场景(`apps/partner` 在 PTR namespace) | § 1.5.4 + conventions §1 |
| 3 | `prepare-check` 未叠加 worktree branch 上 in-flight Feature 占用的 ID → 撞号 | 并行 Feature 多 worktree 时 | § 1.5.4 |
| 4 | 关键词命中即推 preset=micro · 漏 §2.2 准入**反向扫描**("改样式"→ micro · 没扫"实为改布局结构/交互逻辑"信号) | 用户原文含 UI 调整 / 加组件 / 改布局 / 改交互 | § 2.2 |
| 5 | 漏「🎯 我的理解」意图确认段 / 把意图埋到配置后 / 🧩 假设不摊开(只给干净 restatement)| 短回路("配置够了" · 或怕暴露假设) | § 4 |
| 6 | 现象类输入未排查直接定 Bug + emit prepare(「代码现状」填未验证猜测 · 命名/路由押在猜测上) | 用户只给现象(CI 失败/报错/挂了)· 无修复指令 | § 2 排查先行律 |

🔴 **AI 短回路 ≠ 用户授权**:用户给短指令("改下页面")**不等于** AI 可跳意图确认。指令越短 · AI 补的假设越多 · 越**该**摊开让用户校(短指令恰是误读高发区)· AI 无权省。

📎 **已物化的拦截**(工具层兜底 · 不依赖意志力):`init-feature` 门禁(**60 分钟窗**内该 prefix 无 prepare-check audit → FAIL with hint · 无 audit 不可 init-feature);`prepare-check --user-intent + --admission-judgment`(用户原文留痕 + AI 判断 JSON schema 校验 · recommended vs `--flow-type` MISMATCH → WARN · 不用 regex 关键词扫描:可枚举的进脚本、不可枚举的留 AI)。
📎 其余拦截待物化项属框架维护 backlog · 不在本运行时 spec 内跟踪(归框架仓 `docs/CHANGELOG.md` / `docs/RETRO-LEDGER.md`)。

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
- Planning **未 ship** 才入暂停点 ⚠️ 异常行(已 ship / N-A → 不显 · 全绿不噪)

无 Planning(直接 mode B execute)→ 跳此项。

### 1.5.2 · 检上游依赖(state.json blocking)

若 prepare 是从已有 Feature 衍生:
- 检上游 Feature 的 `state.blocking.pending_external_deps`
- **有待中依赖**才入暂停点 ⚠️ 异常行(全就绪 → 不显)

无上游 → 跳。

### 1.5.3 · 扫代码现状(可选 · 1 句话总结)

可选(高复杂度 Feature 推荐):
- grep 关键模块当前实现(如「<核心模块> 当前只支持 X 场景 / 关键分支硬编码」的一句话现状)
- 1 句话总结 · 喂「🎯 我的理解」的 📦 范围 / 🧩 假设(让用户据代码现实校启动方向)

低复杂度 / 用户已知 → 跳。

🔴 **「代码现状」只写已验证事实**:根因类判断必须来自排查先行 / 实证(读过真实代码与日志)· **未验证假设不得写入**(写进总览 = 误导用户 review · §2 排查先行律的反面教材)。

🔴 **路由前缀必判**(即便跳过上面的可选深挖):据**改动代码所在的子项目目录**定 artifact 前缀 + docs_root —— 查 `teamwork-space.md` 子项目清单(代码在 `apps/partner/` → 用 PTR 注册前缀 + docs_root · 在 `services/` → SVC-* · …)。**不可沿用上一个 Feature 的前缀**。错前缀 / 错路径 → `init-feature` 路由物化校验 FAIL(错前缀会落错位置)。🔴 **改动跨多个子项目(monorepo 内)= 照样一个 feature**:前缀/docs_root 取**业务交付宿主**(交付物主要落地 / 用户感知所在的子项目)· 其余子项目的改动在同一 worktree 同一 feature 里做 —— 「代码跨子项目」**不是拆 feature 的理由**(交付内聚单源 [feature-planning Step 5.7](./feature-planning.md) · 前缀选择的别扭不构成拆分压力)。

### 1.5.4 · ID 冲突预检 + stage 评审角色预览(强制)

```bash
state.py prepare-check --feature-id-prefix <PROJ> --flow-type <Feature|Bug>
```

输出含:
- `next_available_id_stem` + `existing_ids` + `id_letter`(ID 冲突预检 · 字母 **F/B**〔M 为 legacy 存量〕· 详 conventions.md §1)
- `stage_chain_preview`(canonical 链回显 · 仅供暂停点「链=」行)—— 🔴 评审面与环节**不在 prepare 装配**(后移 · 见 §1.5.4)

🔴 `--flow-type` 必传:Bug → `PREFIX-B{NNN}` · Feature(含 preset=micro)→ `PREFIX-F{NNN}`。漏传退回字母 F · **Bug 会错号**。

PMO 把数据填进暂停点表格:`next_available_id_stem` → artifact ID 默认值;`stage_chain_preview` → §4 emit 模板的「链=」行(canonical 回显)。

🔴 **prepare 不做装配**(用户拍板 · 装配后移):**环节**(`ui_design` / `browser_e2e` 进不进)与**评审面**(各 stage roster / 外审方向 / 轮次)两个维度的装配,**全部移到 goal 调研之后**按实测复杂度定 —— prepare 手里只有需求文本、没有代码现状,在信息最少的时刻做信息最密的决策 = 结构性错判(实证:删 3 个按钮被字面定价成九段全链)。单源 = [goal-stage § 链装配](../stages/goal-stage.md)。prepare 仅剩四件:**意图对齐**(§4 理解卡)· **flow 大类**(Feature/Bug)· **preset=micro 白名单速通**(§2.2 · 类型判断非复杂度装配)· **clarity + 4 项机械配置**。

---

## 1.6 模型档位与并行度(一行建议)

- **关键 Feature(规划/方案/关键裁决重)建议主对话用深度档模型**(档位判断框架 = [agents/README.md §一](../agents/README.md) · 主对话模型是用户主权 · AI 只建议);
- **并行度**:prepare 时顺手标出「可并行的子任务」(评审冷审/多模块 dev/调研 fan-out)→ 各 stage 开工按 agents/README 并行姿态派 subagent/teammate。

## 1.7 明确度判定(clarity · 证据先行)

🔴 **「看过再判」**:流程类型判定前先做 30 秒侦察(**具体查什么由 AI 自行判断**)· 填 `prepare-check` emit 的 `triage_evidence` 槽(**空着不给判**)· 据证据判 `clarity`:

- **explicit**(明确):用户给出明确方案 **或** 机械映射类(外化/重命名/迁移/升级)且无新业务行为。🔴 clarity **仅记录**(`init-feature --clarity` → state · 台账/年检校准)· **评审配置由 AI 动态决策** —— 按 emit 的 `role_value_criteria` **逐 stage 逐角色**判「对本 feature 有没有值」(可去 pl 也可去 qa/architect/external · 每角色一行理由)→ `change-review-roles --reason` 配 roster(审计留痕 · gate 按 roster 自动放行)· review stage 从严(建议 ≥2 视角 · <2 需强理由)。
- **ambiguous**(模糊):一句话含方向词 / 多方案可选 → goal 深门(既有)。
- **normal**(默认):其余。

🔴 解耦「大」和「不确定」:改动面大 → Feature **骨架**(worktree/状态机/测试门);不确定性低 → **评审走轻档**。prepare 暂停点向用户显示判定(可一字改)。

## 2. Step 1 · 流程类型识别(闭集 · R2 红线)

> 🔴 机器层闭集 = `flow_type ∈ {Feature, Bug}` + Feature 重量档 `--preset full|micro`(legacy 别名「Micro」→ preset=micro)· 关键词命中「micro」= 推荐对应 preset 而非独立类型 · 闭集权威视图 [FLOWS.md](../FLOWS.md)。

PMO 按以下关键词表判定 user input 落入哪类流程:

| 关键词模式 | 流程类型 |
|----------|---------|
| 规划 / 拆 roadmap / 路线图 / 全景 / 商业模式调整(如做电商 / 做 SaaS 等新方向) | **Feature Planning** |
| 排查 / 查 log / 诊断 / why X 慢 / 调研 / 分析根因 · 🔴 以及一切**根因未定的现象类输入**(报错 / 挂了 / CI·编译失败 / 慢 · 无修复指令) | **问题排查**(排查先行律 · 见下) |
| 修复 / fix / 处理掉 X bug / 生产缺陷 · 🔴 仅当**缺陷已指认**(用户明确要求修复 · 或 现象+期望+大致位置已知) | **Bug** |
| 换 logo / 换图 / 改文案 / 改样式 / 改颜色 / 改配置常量 | **Feature · preset=micro** |
| 加按钮 / 加导出 / 加字段 / 列表加列 | **Feature**(轻量由 roster/clarity 承担)|
| 实现 / 开发 / 做功能 / 新建模块 | **Feature**(兜底)|

落入闭集之一(R2 红线 · enum 强制 · Feature/Bug 进状态机 + Planning/排查不进)。

🔴 **排查先行律**(现象类输入不排查就定 Bug 的后果:「代码现状」填上未验证猜测 · 命名/前缀路由/worktree 全押在猜测上 · 真因若在别的子项目就全配错):
- **现象类输入**(报错 / 挂了 / CI 失败 / 慢)且 根因·影响面·归属 未定 → **不直接定 Bug · 不 emit prepare 总览** —— 先走问题排查(主对话 · 不进状态机 · 详 [FLOWS.md § 问题排查](../FLOWS.md))。
- 排查闭合 → 按 [SKILL.md § Mode A / E 升级触发](../SKILL.md) emit 升级暂停点:排查小结(**已验证**根因 / 影响面 / 修复性质)+ 候选动作**逐一编号**(R5 标准 1/2/3 + 💡 推荐 · 模板/反模式详 SKILL 该节)→ **用户拍板后**才进 prepare。
- 转入 prepare 时:排查结论 = 「代码现状」内容(已验证事实 · 非假设)· Feature 命名 / 前缀路由据**真因所在子项目**定;后续 diagnose stage cite 排查结论**复核** · 不重查(详 [stages/diagnose-stage.md](../stages/diagnose-stage.md))。
- 边界:**Bug 直入仍合法** —— 用户明确指认缺陷并要求修复(现象+期望清楚 · 大致位置已知)→ 直接 Bug 流程 · 根因细查由 diagnose stage 承担。判别题不是「用户用了哪个词」· 是「**定流程所需的事实(根因/归属/规模)是否已知**」。

**触发场景为 "Feature Planning 启 Feature"** 时:flow_type 默认 `Feature`(因为是从 BL-NNN 启动具体功能 · BL 已经决定了"做什么")。

### 2.1 · 复杂度升级判据(覆盖关键词初判)

🔴 **关键词命中任何执行类流程(Feature 全档 / Bug)时 · PMO 必再扫以下复杂度信号** · 命中任一 → **强制升 Feature Planning**(覆盖关键词初判):

| 信号 | 例 | 不计入 |
|---|---|---|
| **跨独立 git 仓库**(≥2 repo/origin) | 改动落在不同 git 仓库 —— **一个 worktree / 一个 MR 装不下**,单 Feature 状态机真承载不了 | 🔴 **同 repo 内跨子项目 / 多独立部署单元(后端 + Console + 管理后台)不计入** —— 一个 worktree 原子交付 · 照样一个 feature(交付宿主定前缀 · 详 §1.5.3);规模用「影响 ≥2 BL」判 · 部署协调由 WS「跨子项目方向」串行约束管 |
| **数据模型重构** | 删/改老字段(影响存量) / 表结构变动 / 字段语义重定义 | 新增字段(无存量影响) |
| **老需求架构性废弃** | "X 不要了"/"统一为 Y"/"重构这套逻辑" / 整套机制语义替换 | 仅扩展(向后兼容) |
| **影响 ≥2 BL** | 一次需求拆成多个 Feature 协同(admin / backend / partner 各 1 BL) | 单 Feature 内多 commit |
| **方向级业务变更** | 新增/删除业务能力 / 商业模式调整 / 用户角色重新设计 | UI 文案微调 |

**为什么强制升级**:这些信号意味单 Feature 状态机承载不下(如老字段迁移 + 多 BL 拆解写不进单份 PRD/TECH)· 强行进 Feature = 主对话散述伪 PRD(违 R5)。

**PMO 命中后必输出**(R5 标准 1/2/3 暂停点 · 不用自由文本):
```markdown
⏸️ 复杂度判据触发(prepare §2.1)· 你的需求触发以下复杂度信号:
- <信号 1>(具体:<例>)
- <信号 2>

请选择:

1. **进 Feature Planning 流程** 💡 推荐
   理由:跨仓库 / 数据模型重构 / 多 BL · 单 Feature 状态机承载不下
   动作:进 Feature Planning(涉 UI 先出全景初步规划 preview-project + sitemap)→ 拆 WS → ROADMAP 拆 BL-N → 每个 BL 后续启独立 Feature
2. **就一个 Feature**(确认范围未超 · 继续 mode B)
   理由:你确认信号是误判 / 范围实际收敛在单 Feature
   动作:继续 prepare · 按 Feature 流程走
3. **其他指示**
```

### 2.2 · preset=micro 准入校验(覆盖关键词初判)

🔴 **关键词命中「micro / 改文案 / 换图 / 改样式」类轻信号时 · PMO 必验准入硬约束** · 任一不满足 → `preset=full`(关键词只看字面 · 准入硬约束才是真流程边界):

**micro 准入**(全满足才成立 · 否则 preset=full):

| 准入项 | 不满足的信号 |
|---|---|
| 零逻辑变更 | 改动含任何条件 / 分支 / 数据流逻辑 |
| 改动类型在白名单 | 仅 文案 / 样式 / 资源 / 配置常量 / 注释 · 其它都不算(加组件 / 改页面结构 / 改交互 / 改接口契约 / 动数据结构 → 全部超纲) |

📎 轻量但超 micro 白名单的需求**没有独立轻类型** —— 一律 Feature·full · 轻量由动态 roster + clarity 承担(评审面自动收窄 · 骨架不减)。

**为什么校验**:关键词只看字面 · 无法区分"改静态文案"与"改文案渲染逻辑"—— 命中关键词后仍须验准入。

**PMO 命中后必输出**(R5 标准 1/2/3 暂停点 · 不用自由文本):
```markdown
⏸️ 准入校验(prepare §2.2)· 关键词初判 preset=micro · 但触发以下准入不满足:
- <准入项>:<具体信号>

请选择:

1. **preset=full** 💡 推荐
   理由:<准入项> 不满足 · micro 链(dev→review→ship)承载不下
   动作:按 Feature·full 走;有 UI 变更在 goal-complete 标 `--needs-ui=true` 进 ui_design
2. **坚持 preset=micro**(行为性小改动亦合法 · 用户拍板「直接做」形态)
   理由:你确认这就是「直接开发」级的小改动(风险自担 · 记流程例外留痕)
   动作:按 micro 继续 · 🔴 **建议附轻门**:execute 完成后派单路 architect diff 冷审(subagent 错开模型 · 只拦 BLOCKER)+ PM 验收 = MR diff + 合并后盯 staging 部署(await-merge 自动带 CI)
3. **其他指示**
```

---

## 3. Step 2 · worktree 决策模板

PMO 按 flow_type 算 branch 前缀 + worktree path 建议:

| flow_type(+preset) | branch 前缀 | worktree |
|----------|-----------|---------|
| Feature(full/micro)| `feature/` | 必(🔴 `agile/`/`micro/` 前缀已退役 · 统一 `feature/`)|
| Bug | `fix/` | 必 |
| Feature Planning | — | 不进状态机 · 不走 prepare |
| 问题排查 | — | 不进状态机 · 不走 prepare |

**worktree path 默认** = `{worktree_root_path}/{Feature-ID}`(`worktree_root_path` 三级解析:state.json > `.teamwork_localconfig.json` > 默认 `.worktree` —— 规范单源 [conventions.md § 9-11](./conventions.md))。

---

## 4. Step 3 · emit 暂停点(🎯 意图 + ⚙️ 配置 · 1 次完整 · 不分多轮)

PMO 复制给用户 · 🔴 **意图确认在最前** —— 它是用户 review 的**第一校准点**:执行 setup 领头会被 `ok` 盖章、把意图埋成一行 restatement → 误读搭便车溜过;意图提前 + 摊开「你没说、我替你补的假设」= 用户一眼抓误读。配置塌一段(均默认)· 评审表不在此展开(各 stage-start 会再 emit · prepare 重列 = 噪音)· 异常才展开:

1. `# 🎯 我的理解`(意图确认 · **暴露补的假设** · 每次必出 · 在最前)
2. `# ⚙️ 配置`(flow + stage 链 + 4 项配置 + 评审一行 · 均默认可改)
3. `⚠️ 异常行`(仅上游未就绪 / ID 撞号 / Planning 未 ship 时出 · 全绿不显)

```markdown
⏸️ Prepare(回 `ok` 全默认 · 或纠正某项)

# 🎯 我的理解(先确认这个 · 下面配置可 default)
🗣️ 你说的:「<用户原话节选 · 源 --user-intent>」
🎯 理解:<要达成什么 · 1-2 句 · 要什么不写怎么做>
🧩 我补的假设〔仅「我假设你**想要** X」类意图解读 · 非平凡才列 · 否则写「请求明确 · 无补」〕:
   - <你没明说、我按 X 理解的点 · 错了请纠 · 源 admission-judgment.ai_rationale>
📦 范围:做 <Y> · 不做 <Z>
🔁 既有行为:<改「原 A → 现 B」· goal 将升级为待决策项 | 否 · 不动既有默认行为>

# ⚙️ 配置(均默认 · 改某项才说 · 回 `ok` 即全默认)
flow=<Feature[·micro] / Bug> · clarity=<normal> · bl=<BL-NNN|无> · 链=<canonical:goal→…→ship> · ID=<PTR-F033> · merge_target=<staging> · wt=<.worktree/PTR-F033> · branch=<feature/ptr-f033>
装配:环节 + 评审面在 **goal 调研后**按实测复杂度定(§1.5.4 后移律)· PRD 确认时展示(默认执行 · 可调)· 高风险想**全局**加 external 现在说

⚠️ <上游依赖未就绪:… | ID 撞号:… | Planning 未 ship:…> ← 仅有问题才出此行 · 全绿删除
```

🔴 **意图段全是 prepare-check 已采数据**(非即兴):🗣️=`--user-intent` 原话 · 🎯🧩=`--admission-judgment.ai_rationale` 解读。🧩「补的假设」是抓误读**核心零件**(干净 restatement 会把假设藏起)· 无非平凡假设时显式写「请求明确 · 无补」(证明想过)。
🔴 **🧩 只列意图解读假设**(「我假设你**想要** X」· 用户域 · 用户能直接拍)· **禁抛未验证的代码/可行性猜测**(「我假设后端有 X 列」)—— 那归 §1.5.3「代码现状只写已验证事实」+ 反模式 #6:要么先验证再写,要么留给 goal 调研后的**深门**。prepare 在强制读代码**之前** · 此处抛代码猜测 = 让用户确认 AI 本该去查的事(误导 review)。
`ok` = 意图在最前的**知情**点头 · 非盲签。

flow_type → first_stage 映射:
- Feature(preset=full)→ `goal`
- Bug → `diagnose`(根因细查 + 修复方案 · 用户确认后才进 dev · 防修偏)
- Feature(preset=micro)→ `execute`(零门禁自由执行 → ship · 无 dev/pm_acceptance)
- Feature Planning / 问题排查 → 不进状态机 · prepare 在这两个流程上不调用

🔴 **必 1 次完整 emit · 不分多轮**(防 PMO 先建议 + 再"最终确认"的 2 轮交互浪费)。
🔴 **用户回 `ok`** · PMO 视作"按建议全部默认值" · 不再二次确认 · 立即执行 §5。

### 4.1 · emit 前自查

🔴 **emit 前逐项核对**:🎯 意图段在最前(🧩 假设已摊开或显式写「无补」)+ ⚙️ 配置含 4 项与评审一行 + ⚠️ 异常行仅在有问题时出现 —— 缺一 / 意图埋到配置后 / 假设藏起不摊开 → 重 emit(误读会溜过)。

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
 --worktree-path <worktree-path> \
 --clarity <explicit|normal|ambiguous>   # §1.7 判定 · 仅记录(台账/年检校准)
 # --preset micro                        # 仅 §2.2 判 micro 时带 · 缺省 full
 # --bl BL-NNN                           # 从 ROADMAP BL 启动时必带 · ship 翻牌/台账用
```

🔴 **Bug 流程先 diagnose**(不是 dev):根因细查 + 修复方案须经用户 R5 确认后才进 dev 写 fix —— 详见 [stages/diagnose-stage.md](../stages/diagnose-stage.md)。

---

## 6. 与状态机的接口

prepare 完成 = init-feature 前置满足(4 项配置已用户确认 + worktree 物理已建 + cwd 在 worktree 内)。拒绝条件 + prepare 职责边界(不写 state.json / 不建 worktree / 不自动跑 git)同 [SKILL.md § 入口与状态机的接口](../SKILL.md)。额外一条:flow_type ∈ {Feature Planning, 问题排查} → init-feature reject(不进状态机)。

---

## 7. 错误处理

### 7.1 · 流程类型识别错(关键词模糊)

PMO 识别不准 → 在暂停点列出"我猜是 X · 你确认是 Y/Z?"让用户拍板。

### 7.2 · 用户拒绝 worktree 默认值

部分用 default + 部分自定 → PMO 用混合值跑 git worktree add。
全否决 → 等用户给完整 4 项。

### 7.3 · git worktree add 失败

按报错自行处置(branch 已存在 / origin 未 fetch / path 被占 —— git 排障是模型自带知识 · 不列修法)。错误处理由 PMO 主导 · 不在 state.py 状态机里。

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
