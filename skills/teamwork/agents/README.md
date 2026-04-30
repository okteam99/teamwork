# Teamwork Subagent 执行协议

> v7.3.10+P0-19-B：Teamwork 以 **Stage 为权威**，各 Stage 的角色任务规范已合并进对应 `stages/*.md`。本文件只保留 **Subagent 执行协议**（PMO dispatch / dispatch 文件格式 / 通用约束 / Progress Log / 外部 Codex spawn / 主对话产物协议），不再定义具体角色任务。
> PMO 在 Subagent 路径下必须让 Subagent 先读本文件 + 对应 Stage 文件；主对话路径下可跳过本文件直接读 Stage 文件。

---

## 一、执行方式与模型（由 AI Plan 动态决策）

执行方式（main-conversation / subagent / hybrid）+ 模型（opus / sonnet / haiku）+ 是否出 Plan 由 AI 在 Plan 模式中自主决策，各 Stage 的默认推荐见 `stages/*.md §AI Plan 模式指引`。本文件只列通用原则。

### 执行方式偏好指引

```
偏向 Subagent：
├── 任务预期 >5 分钟，冷启动税占比低
├── 产出量大（大量代码 / HTML / 测试输出），主对话 context 紧张
├── 需要外部工具（Codex CLI / AI 浏览器）
├── 需要独立视角防创建者偏见
└── 任务可自闭环，输入输出明确

偏向主对话：
├── 任务轻（预期 <5 分钟），冷启动不划算
├── 需要与用户多轮交互（暂停点）
├── 多角色多轮互动（如 UI 还原 Designer↔RD 循环）
├── 需要实时感知主对话上下文变化
└── 评审/审查类任务（读+判断+短报告）
```

### 模型偏好说明（v7.3.10+P0-40 调整）

```
原则："深度判断 = Opus / 执行验证 = Sonnet / 异质独立 = external（codex/claude CLI）"

├── Opus 推荐（深度判断 / 创造性产出）：
│   ├── RD 开发（Dev Stage）：写业务代码 + TDD + 复杂逻辑判断
│   ├── 架构师 Code Review（Review Stage / Bug 流程必经）：架构层最后 gate，深度判断不可降级 ★
│   ├── PM 起草 PRD（Goal-Plan Stage 子步骤 1）：业务方向澄清 + AC 结构化
│   ├── RD 写 TECH（Blueprint Stage）：技术方案设计
│   ├── 架构师评审 TECH（Blueprint Stage）：架构对齐 + ADR 决策
│   └── Designer UI 设计 / Panorama 设计：视觉创造性产出
│
├── Sonnet 推荐（校验型 / 执行型任务）：
│   ├── QA Code Review（Review Stage）：TC 逐条覆盖 + TDD 规范校验（执行型）
│   ├── QA 写 TC（Blueprint Stage）：测试场景枚举（执行型）
│   ├── QA 集成测试 + API E2E（Test Stage）：测试执行
│   ├── Browser E2E：浏览器测试执行
│   ├── PRD/TC/TECH 多角色并行评审（PMO/QA/Designer/PL）：校验型评审
│   └── Bug 排查（RD 在 Bug 流程的初步排查）：执行型分析
│
├── external（异质模型，立场独立）：
│   ├── PRD 评审（external_prd_reviewer）：codex / claude-cli
│   ├── TC+TECH 评审（external_blueprint_reviewer）
│   └── 代码评审（external code reviewer）
│
├── —（主对话继承）：主对话任务继承当前会话模型
└── PMO dispatch Subagent 时按宿主指定模型（Claude: Task model / Codex: agent toml model）

📌 PMO 自身模型（主对话）：继承用户会话模型；关键 Feature 建议 Opus 主对话。
🔴 Stage-specific 默认（含 Test Stage AI 自主决策）见 stages/*.md 文件。

🔴 v7.3.10+P0-40 关键变化：
   - RD 开发（Dev）默认 Opus（保持原推荐 / 显式化）
   - 架构师 Code Review 从 Sonnet 推荐改为 Opus 推荐（深度架构判断不可降级；含 Review Stage + Bug 流程必经）
   - QA Code Review 保持 Sonnet（执行型校验，TC 覆盖判断 Sonnet 够用）
```

---

## 二、通用 Subagent 执行约束

### 2.1 文件读取顺序

```
Subagent 启动后，必须按顺序读取：
1. 本文件（agents/README.md）→ 了解通用规范 + dispatch 协议
2. 对应 Stage 文件（如 stages/dev-stage.md）→ 含该 Stage 角色任务规范
3. Stage 规范中指定的项目文件（PRD / TC / TECH 等）→ 业务上下文
```

### 2.2 代码质量

```
所有 Subagent 产出的代码必须遵守：
├── 项目 standards/common.md + 对应技术栈规范（backend.md / frontend.md）
├── KNOWLEDGE.md 中的项目特定规则（如有）
├── 禁止遗留 TODO/FIXME/占位符
├── 禁止输出不完整的代码片段
└── 所有文件必须直接写入项目目录（共享文件系统）
```

### 2.3 异常处理

```
Subagent 遇到问题时的处理方式：

可自行处理（不中断）：
├── 编译错误 → 修复后继续
├── 测试失败 → 修复代码后重试
└── 代码规范问题 → 修正后继续

需记录并上报（继续执行可实现的部分）：
├── 上游文档疑似有误（PRD/UI/TC 矛盾或缺失）
├── 技术方案无法按预期实现（依赖缺失/API 不存在）
└── 测试环境问题（无法连接数据库/缺少配置）

上报格式：
⚠️ 上游问题记录
├── 来源：[PRD/UI/TC/TECH]
├── 问题：[具体描述]
├── 影响：[对当前开发的影响]
└── 建议：[建议处理方式]
```

### 2.4 输出规范

```
Subagent 返回给主对话的内容必须包含：
├── 1. 执行摘要（做了什么、改了哪些文件）
├── 2. 产出清单（代码文件、测试文件、报告）
├── 3. 问题清单（上游文档问题 / 遗留问题，无则写「无」）
└── 4. 角色报告（如 RD 自查报告，格式见对应 Stage 文件）
```

### 2.5 Progress Log 实时维护（🔴 硬规则，v7.3.7 flush 语义 + 运行中轮询）

```
Subagent 执行过程中必须实时维护 dispatch 文件的 Progress Log 段：
├── 🔴 每个 Step 开始时立即 append `- [HH:MM:SS] step-start Step N: {名}`
├── 🔴 每个 Step 完成时立即 append `- [HH:MM:SS] step-done Step N（耗时 MmSs）`
├── 🔴 异常事件立即 append（step-concern / step-blocked / degradation）
├── 🔴 Append 必须立即 flush 到磁盘：
│   Python 用 f.write(); f.flush(); os.fsync(f.fileno())
│   shell 用 >> （天然 flush）
│   Claude Code 子 Agent 用 Edit/Write 工具（天然原子 flush）
│   buffered I/O 导致主对话读到空段 → 误判卡死
├── 🚫 禁止：等全部跑完后一次性补 Progress Log（崩溃时会丢失中段记录）
├── 🚫 禁止：忽略时间戳（无法评估每步耗时）
└── 🎯 双重目的：
    ├── 运行中：主对话可并发 Read 本段获取实时进度（见 §四 Progress 可见性协议）
    └── 运行后：PMO 转时间轴回放；失败/超时的根因排查第一手资料

Progress Log 缺失或断档 → PMO 在阶段摘要中标注「进度不可追溯」WARN。
格式详见 templates/dispatch.md §Progress Log 段。
```

### 2.6 危险命令红线

```
🔴 所有 Subagent 禁止执行以下操作（无论任何理由）：

| 类别 | 禁止命令/模式 | 说明 |
|------|--------------|------|
| 删除 | rm -rf /、rm -rf ~、rm -rf ./* | 递归强删根目录/家目录/当前目录 |
| 删除 | 未限定路径的 rm -rf（如 rm -rf $VAR 且 $VAR 可能为空） | 变量为空时等价于 rm -rf / |
| Git | git push --force（主分支）、git reset --hard（未确认） | 不可逆的仓库操作 |
| 数据库 | DROP DATABASE、DROP TABLE（生产环境） | 不可逆的数据破坏 |
| 数据库 | TRUNCATE TABLE（未经确认） | 清空全表数据 |
| 系统 | chmod -R 777、chown -R | 大范围权限变更 |
| 网络 | curl | bash、wget | sh | 远程脚本盲执行 |
| 凭证 | 将 API Key/密码/token 写入代码或日志 | 凭证泄露 |

✅ 白名单（允许执行）：
├── rm -rf 构建产物目录（dist/、build/、target/、node_modules/）
├── rm -rf 测试临时目录（明确以 test-tmp/ 或 .tmp/ 开头的路径）
├── git push --force 到个人 feature 分支（非 main/master/develop）
└── DROP/TRUNCATE 在测试数据库中执行（连接串含 test/mock）

🔴 遇到不在白名单内的危险命令：
├── 立即停止执行
├── 记录到上游问题清单
└── 返回 ⚠️ DONE_WITH_CONCERNS，由 PMO 决定是否暂停让用户确认
```

---

## 三、Codex CLI 调用规范（Review Stage 外部视角 + Plan/Blueprint 交叉评审）

Codex CLI 用于 Review Stage 外部 Codex Review（见 `stages/review-stage.md §外部视角 Codex Review`）+ Plan/Blueprint 交叉评审（见 `templates/codex-cross-review.md`）的独立外部审查。

### 宿主无关的独立性保证

🔴 **核心原则**：外部视角**必须通过 codex CLI 独立 spawn fresh session 执行**，不论 PMO 所在宿主是 Claude Code 还是 Codex CLI。独立性来源于 session 隔离 + 独立 dispatch 文件，**不依赖跨模型**。

```
├── Claude Code 宿主
│   └── 通过 Task 或 MCP 启 codex 子进程：fresh codex session 独立跑 review
├── Codex CLI 宿主
│   └── 在 prompt 中 spawn 独立 codex 子 agent（.codex/agents/*.toml）
│       fresh context，与主对话 session 完全隔离
│   └── 🔴 禁止："外部视角 = 主对话 Codex 自审"——必须显式 spawn 子 agent
├── 两宿主独立性保证一致：
│   ├── 独立 dispatch 文件（dispatch_log/NNN-codex-*.md）
│   ├── 独立 generated_at 时间戳（与架构师/QA 视角不重合）
│   ├── files_read 清单不含其他视角的 review 产物
│   └── 可由机器校验（见 stages/review-stage.md Output Contract）
└── dispatch 文件协议统一（本文件 §四），prompt 模板统一
```

### 可用性检测（stages/init-stage.md Step 3.5 完成，结果缓存至会话结束）

```
├── codex_cli_available = true → Codex Code Review 正常执行（两宿主统一路径）
├── codex_cli_available = false → PMO ⏸️ 提示用户三选一（降级由 AI 自主规划）：
│   「Codex CLI 不可用。选择：
│     1️⃣ 解决环境问题后继续
│     2️⃣ 降级到等效独立审查（🟢 AI 自主判断适合的降级模式，见下方"降级路径决策"）
│     3️⃣ 跳过 Codex Review」
└── 跳过 Codex Review 不阻塞后续流程（记录跳过原因 + WARN 到 review-log.jsonl）
```

### 降级路径决策（🟢 AI 自主判断，v7.3.9+P0）

```
🔴 核心原则：不预设具体模型（Sonnet/GPT-4/o3 等），由 AI 按当前宿主可用资源 + 任务复杂度 + 独立性要求自主规划。

AI 自主判断维度：
├── 宿主可用模型清单（Claude 宿主：opus/sonnet/haiku；Codex 宿主：宿主内置；通用：自评估）
├── 独立性强度需求（Review Stage 最高；codex-cross-review 次之）
├── 任务复杂度（代码规模 / 场景数 / 历史问题密度）
├── 成本容忍度（用户是否有快速迭代需求）
└── 上一轮降级结果（是否已经降过一次 → 进一步降级还是升级兜底）

典型可行降级模式（非强制，仅供 AI 参考）：
├── 换 fresh context 同宿主强模型（保独立性，降来源独立性）
├── 换低成本模型（保独立性，降深度 → 适合小改动）
├── 并发双模型（两个弱模型投票替代一个强模型）
└── 降级为"PMO 主对话按 Codex prompt 模板内省自审"（最弱兜底，标注 `DONE_WITH_CONCERNS`）

🔴 AI 必须在 Execution Plan 或 review-log 的 concerns 中显式写明：
├── 为什么选此降级模式（决策理由）
├── 独立性如何保证（fresh context / 跨模型 / 哪个更弱）
└── 对用户的风险提示（例：同模型 fresh context → 模型共性盲区未覆盖）

🔴 禁止：AI 不说理由静默降级；用户端看到的是 ⚠️ WARN [degradation-fallback] + 决策理由块。
```

### CLI 配置

```
├── 命令入口：`codex`
├── 如项目已有 `.codex/` 配置则沿用
└── 如用户环境已配置则按用户配置执行
```

### 异常处理

```
Codex CLI 执行中出错（超时/返回异常/输出为空）→ ⏸️ 用户选择：重试 / 跳过 Codex Review
```

---

## 四、PMO 启动规范

### 4.1 启动方式（宿主适配）

PMO 根据宿主环境选择 Subagent dispatch 方式：

```
宿主 dispatch 方式速查：
├── Claude Code → Task 工具（model 参数指定模型）
│   └── 示例：Task(prompt="...", model="sonnet")
├── Codex CLI  → prompt 指示 Codex spawn 自定义 agent
│   └── 示例：「请使用 rd_developer agent 执行以下任务...」
│   └── 自定义 agent 定义见 .codex/agents/*.toml（由 install.sh 生成）
├── Gemini CLI → 主对话内执行（Gemini 暂无 subagent 机制）
└── 通用降级   → 主对话内串行执行（丧失并行，功能完整）

🔴 核心原则：dispatch 方式不同，但 prompt 内容和输入输出格式完全一致。
   下方的 Dispatch 文件协议适用于所有宿主。

🔴 降级兜底必须输出 WARN 日志（硬规则，无例外）：
触发任何降级路径时，PMO 必须在主对话输出一条结构化 WARN 提示：

⚠️ WARN [degradation-fallback]
├── reason    : {为什么触发降级：Subagent 失败 / 宿主不支持 / Codex 不可用 等}
├── from      : {原计划路径：如 Claude Task Subagent / Codex agent / 并行 dispatch}
├── to        : {实际兜底路径：如 主对话执行 / Sonnet 降级 / 串行执行}
├── stage     : {当前 Stage 名}
└── impact    : {影响评估：失去并行 / 模型能力差异 / 需要补充监控 等}

适用的降级场景（非穷举）：
├── Subagent dispatch 失败 → 主对话执行（见 §4.6 FAILED 兜底）
├── Codex CLI 不可用 → 其他模型执行 Review
├── 宿主不支持 TodoWrite → 输出 markdown 进度块
├── git worktree 不可用 → worktree=off 降级
├── PreCompact/PostCompact hooks 不存在 → 跳过
└── 任何「首选方案不可用 → 走兜底方案」的路径

🎯 目的：降级是正确但不正常的路径，必须可观测、可追溯。
       静默降级会让用户误以为一切正常，埋下质量风险。
```

### Dispatch 文件协议（所有宿主通用，🔴 硬规则）

Teamwork 采用**文件化 dispatch**：PMO 不再在 Task/Agent prompt 里塞长文本，而是把所有 dispatch 信息写到一个 markdown 文件，Subagent 读该文件执行，完成时 append Result 回同一文件。

```
核心原则：
├── 🔴 一次 Subagent dispatch = 生成一个 dispatch 文件
├── 🔴 dispatch 文件 = Subagent 入参 + 审计记录（同一份，消除重复劳动）
├── 🔴 Subagent prompt 极简（~5 行），只含 dispatch 文件路径
├── 🔴 Subagent 必须 append Result 区域，否则视为 FAILED
└── 🔴 PMO 写入 dispatch 文件是 Subagent dispatch 的前置条件（未写 = 不得 dispatch）
```

**dispatch 文件位置**：

```
{子项目路径}/docs/features/{缩写}-F{编号}-{功能名}/dispatch_log/
├── 001-blueprint.md           # 序号从 001 起，三位数字
├── 002-rd-develop.md          # {subagent-id} 是 dispatch 文件标签（stage 或 stage+角色）
├── 003-arch-code-review.md    # 并行 dispatch 各用独立文件
├── 004-codex-review.md        # 同批次标注 Batch 字段
├── 005-qa-code-review.md
└── INDEX.md                   # 汇总索引（每次 dispatch 完成后 append 一行）

📎 **subagent-id 说明（v7.3.10+P0-19-B 起）**：
- `{subagent-id}` 是 dispatch 文件的**标签**，沿用原有 id（rd-develop / arch-code-review / qa-code-review / integration-test / api-e2e / blueprint / designer 等），PMO 按 Stage + 角色组合填写。
- 🔴 但**角色任务规范**已物理合并进 `stages/*.md § 角色任务规范`（dev-stage.md / review-stage.md / test-stage.md），不再在 `agents/*.md` 中存在。
- dispatch 文件的 Input files 清单应指向 `stages/{stage}-stage.md §{角色任务规范节}`，不是已删除的 `agents/{subagent-id}.md`。
```

**dispatch 文件模板**：见 `{SKILL_ROOT}/templates/dispatch.md`（含完整字段定义和 INDEX 模板）。

**Subagent prompt 极简结构**（替代原来的长 prompt 结构）：

```
你是 Teamwork 协作框架中的 {角色名}。

请读取以下 dispatch 文件并按其内容执行任务：
{dispatch 文件绝对路径}

🔴 执行规则：
1. 严格按 dispatch 文件的 "Input files" 清单按序读取
2. 产出满足 "Expected deliverables" 列出的所有交付物
3. 🔴 执行过程中必须实时维护 dispatch 文件的 "Progress Log" 段：
   每个 Step 开始/完成时 append 一行时间戳 + 事件，禁止最后一次性补全
4. 完成后在 dispatch 文件末尾 append "Subagent Result" 区域（格式见文件末尾模板）
5. 未 append Result 视为 FAILED；Progress Log 缺失 → PMO 标记「进度不可追溯」WARN
```

**关键字段责任划分**：

| 字段 | 谁填 | 何时填 |
|------|------|--------|
| Meta（Feature/时间/宿主/model/pre-check） | PMO | dispatch 前 |
| Task（任务描述） | PMO | dispatch 前 |
| Input files（按序读取的文件清单） | PMO | dispatch 前 |
| Additional inline context | PMO | dispatch 前（仓库级约束 / 短配置） |
| **🎯 Key Context（6 类关键点）** | **PMO** | **dispatch 前（逐项判断，无则写 `-`）** |
| Edit scope constraints | PMO | dispatch 前（复制模板标准段） |
| Expected deliverables | PMO | dispatch 前 |
| **Progress Log（每步开始/完成 append）** | **Subagent** | **执行中实时 append，禁止最后一次性补全** |
| Return format | PMO | dispatch 前（复制模板标准段） |
| **Subagent Result** | **Subagent** | **完成前 append** |

**PMO 启动前自问（变更版）**：

```
Subagent 启动前，PMO 快速自检：
├── dispatch 文件是否已生成并保存到 dispatch_log/？（未生成 = 不得 dispatch）
├── Input files 清单是否完整覆盖任务所需上下文？
├── 仓库级约束（CLAUDE.md/AGENTS.md/GEMINI.md）是否已作为 Additional inline context 注入？
├── 🎯 Key Context 6 类关键点是否逐项判断？（无则写 `-`，证明已判断）
│   1. 历史决策锚点（用户已拍板的选择）
│   2. 本轮聚焦点（重派/修复必填）
│   3. 跨 Feature 约束（禁改文件 / 兼容要求）
│   4. 已识别风险 / 历史陷阱（预检 / KNOWLEDGE.md / 历史 Bug）
│   5. 降级授权（预先授权的降级路径）
│   6. 优先级 / 容忍度（进度 vs 质量）
├── 📣 主对话 TodoWrite 是否已预声明本次 Subagent 的 Step 列表？
│   ├── 内容从 stage 文件「执行流程」章节抽取
│   ├── 粒度对齐 Expected deliverables（用户能一眼看到「接下来做哪 N 步」）
│   └── 宿主不支持 TodoWrite → 降级输出 markdown 进度块（并走 WARN 日志）
└── KNOWLEDGE.md 中相关经验是否已作为 Input files 之一？
```

**🔴 Key Context 硬规则**：

```
├── 字段必须完整（6 个子项全部出现，无内容写「-」）
├── 严禁留空或删除字段 → 无判断痕迹 = Subagent 返回 NEEDS_CONTEXT
├── 只写 Input files 里读不到的信息
│   ├── ✅ 用户在 Goal-Plan Stage 拍板「用 PostgreSQL 不用 MySQL」（附 PL-PM 纪要引用）
│   ├── ❌ 复制 PRD 的验收标准进来（Subagent 会读 PRD.md）
│   └── ❌ 「请注意代码质量」这种废话
├── 必须附证据链（来源文件 + 位置）
│   └── 反例：「用户说要用 PostgreSQL」→ 无来源，不可追溯
└── 反模式防范：
    ├── PMO 偷懒 → 全写「-」 → 审查环节会发现（Review/Test 暴露后追责）
    └── PMO 过度写 → 把主对话思考负担转嫁给 Subagent → 6 类边界严格约束
```

**注入策略（写进 dispatch 文件）**：

```
├── 长文档（PRD / TC / TECH / ARCHITECTURE.md / standards/*.md）→ 放 Input files
│   好处：零信息损失，Subagent 自行 Read 原文
│
├── 短文档 / 仓库级约束（CLAUDE.md / AGENTS.md / GEMINI.md / 短配置）
│   → 放 Additional inline context，PMO 直接复制原文到 dispatch 文件
│   好处：确保高优先级内容被看到，不依赖 Subagent 主动 Read
│
└── 🔴 Subagent Result 的 Files read 字段必须列出实际读取的文件清单（可追溯）
```

**按 Stage / 任务的 Input files 建议**（PMO 填 dispatch 文件时参考）：

```
├── Goal-Plan Stage → PRD.md（如有草稿）、PROJECT.md、KNOWLEDGE.md
├── UI Design Stage → PRD.md + design/sitemap.md + design/preview/*.html（相关页面）
├── Blueprint Stage → PRD.md + UI.md（如有）+ ARCHITECTURE.md + KNOWLEDGE.md
├── BlueprintLite Stage → 简化 PRD.md + ARCHITECTURE.md（相关章节）
├── Dev Stage → PRD.md + TC.md + TECH.md + standards/{common,backend/frontend}.md + stages/dev-stage.md
├── Review Stage：
│   ├── 架构师 CR → TECH.md + ARCHITECTURE.md + stages/review-stage.md + dispatch_log/{RD dispatch}.md（含自查报告）+ git diff 文件清单
│   ├── Codex Review → PRD.md + TECH.md + TC.md + stages/review-stage.md §外部视角 Codex Review + 代码变更文件（🔴 不传架构师 CR 报告避免偏见）
│   └── QA 代码审查 → TC.md + stages/review-stage.md + git diff 文件清单
├── Test Stage → TC.md（integration/E2E 章节）+ TECH.md（测试命令）+ stages/test-stage.md
└── Browser E2E → TC.md（Browser E2E Scenarios 章节）+ 页面地址
```

**Edit scope constraints 标准段**（PMO 直接复制到 dispatch 文件）：

```
🔴 你只能操作以下路径，其他路径一律禁止读写：
- 允许读写：{子项目路径}/（功能代码 + 测试 + 配置）
- 允许读写：{子项目路径}/docs/features/{功能目录}/（文档产出，含 dispatch_log/）
- 允许只读：{项目根目录}/docs/（ARCHITECTURE.md / KNOWLEDGE.md 等共享文档）
- 允许只读：{SKILL_ROOT}/standards/（开发规范）
- 🚫 禁止：其他子项目路径
- 🚫 禁止：.env / .env.* / credentials.* / *secret* 等敏感文件
- 🚫 禁止：.git/ 目录直接操作（通过 git 命令操作）

违反时：立即停止 → 记录到 Subagent Result 的 Concerns → 返回 DONE_WITH_CONCERNS
```

### 4.2 Dispatch 文件生命周期

```
├── dispatch 前：PMO 生成文件，保存到 dispatch_log/
├── dispatch 中：Subagent 读文件执行（多次 Read 不占 prompt token）
├── dispatch 后：Subagent append Result → PMO 读 Result 确认状态
├── PMO 扫 INDEX.md 追加一行（时间、状态、降级、文件链接）
└── Feature ✅ 完成：PMO 复盘所有 dispatch，教训写入 KNOWLEDGE.md；dispatch_log/ 保留
```

### 4.3 Progress 可见性协议（🔴 硬规则）

Subagent → 主对话的宿主 Task 工具 API 本身同步阻塞（PMO 发 → 主对话挂起 → Subagent 跑完 → 返回），但 **文件系统是天然的异步实时通道**——Subagent 写 dispatch 文件、主对话 Read 同一文件，无需宿主 API 支持。Teamwork 采用「前置预声明 + 中途自述 + 运行中轮询 + 事后回放」四段式进度协议。

```
四段式 Progress 协议：

┌─ 阶段 1：dispatch 前（PMO 职责） ────────────────────────┐
│ 🔴 PMO 必须在主对话 TodoWrite 预声明 Subagent Step 列表   │
│ ├── 内容来源：stage 文件「执行流程」章节                │
│ ├── 粒度：对齐 Expected deliverables                    │
│ ├── 宿主不支持 TodoWrite → 输出 markdown 进度块 + WARN   │
│ └── 目的：dispatch 前用户已看到「接下来做哪 N 步」        │
└──────────────────────────────────────────────────────────┘

┌─ 阶段 2：dispatch 中（Subagent 职责） ───────────────────┐
│ 🔴 Subagent 必须在 dispatch 文件 Progress Log 段实时记录  │
│ ├── 每步开始：`- [HH:MM:SS] step-start Step N: {名}`     │
│ ├── 每步完成：`- [HH:MM:SS] step-done Step N（耗时 XmXs）`│
│ ├── 异常事件：step-concern / step-blocked / degradation │
│ ├── 🔴 Append 立即 flush（flush + fsync / >> / Edit 工具）│
│ ├── 禁止：最后一次性补全（崩溃时会丢失）                 │
│ └── 目的：运行中可被主对话读取 + 事后回放 + 失败排查     │
└──────────────────────────────────────────────────────────┘

┌─ 阶段 3：dispatch 运行中（主对话按需轮询） ──────────────┐
│ 🔴 用户问进度 / >5min dispatch / 并行多路 → 主对话主动 Read │
│ ├── 读 dispatch 文件的 Progress Log 段（不读全文）      │
│ ├── 对比最新行 vs 上次读取 → 增量汇报                   │
│ ├── 轮询节奏：用户触发即读；不建议 <10s tight loop      │
│ ├── 🚫 禁止读 subagent session JSONL 当进度源          │
│ │   （格式不稳定，非协议产物；Progress Log 才是契约）    │
│ └── Progress Log 长时无新行（>预估步时长 2x）→ 疑似卡死 │
└──────────────────────────────────────────────────────────┘

┌─ 阶段 4：dispatch 后（PMO 职责） ────────────────────────┐
│ 🔴 PMO 读 Progress Log 转成主对话可见的时间轴            │
│ ├── step-start/step-done → 主对话 TodoWrite 状态更新     │
│ ├── step-concern / degradation / step-blocked → 高亮提示 │
│ ├── 总耗时 + 每步耗时展示在 PMO 阶段摘要                 │
│ └── 目的：用户看到「计划 → 等待（但清楚在等什么，期间 │
│     可随时查询进度）→ 时间轴回放」而不是「黑盒 → 突然完成」│
└──────────────────────────────────────────────────────────┘
```

**可选加强：切分 Subagent 粒度（按需启用，不默认）**

对于体感特别差的长 Stage（典型是 Test Stage 总耗时 >15 分钟），PMO 可将「一次 dispatch」拆成「多次短 dispatch」：

```
├── 适用条件（同时满足才切分）：
│   ├── Stage 整体预期 >15 分钟
│   ├── 内部步骤之间无强上下文依赖（切分不损失信息）
│   └── 用户明确表达对该 Stage 过程敏感
├── 切分方式：
│   ├── Test Stage 例：环境复核 Subagent → 集成测试 Subagent → API E2E Subagent
│   └── 每个 Subagent 用独立 dispatch 文件，Batch 字段标同批次
├── 代价：
│   ├── 多次冷启动开销（每次 ~10-30s）
│   └── PMO 维护中间状态（需在主对话做串联）
└── 🔴 不作为默认，只在用户显式要求或 Stage 明确属于「用户盯盘型」时启用
```

### 4.4 Subagent 未 append Result 的处理

```
情况 1：Subagent 返回但未 append → PMO 视为 FAILED
├── PMO 在 dispatch 文件末尾 append 自己的 Result 段
│   ├── Status: FAILED (Subagent did not append Result)
│   ├── Completed at: {PMO 接管时间}
│   └── Degradation: ⚠️ WARN [missing-result-append]
└── 按 §4.6 FAILED 兜底：降级主对话执行，输出 WARN 日志

情况 2：Subagent 卡死/超时 → PMO 超时兜底
├── 同情况 1 处理
└── dispatch 文件保留，便于后续排查 Subagent 行为异常根因
```

### 4.5 启动前检查

```
PMO 启动 subagent 前必须确认：
├── 🔴 dispatch 文件已生成并保存到 {Feature}/dispatch_log/（未生成 = 不得 dispatch）
├── dispatch 文件的 Input files 清单完整覆盖任务所需上下文
├── 所有前置阶段已完成（如技术方案已确认）
├── 所需文件已生成且路径正确
├── 用户已确认可以进入该阶段
├── 无未解决的阻塞项
└── 多子项目模式下：确认子项目路径正确，文档目录已创建
```

### 4.6 完成后处理

```
Subagent 返回后，PMO 必须：
├── 1. 🔴 读取 dispatch 文件，确认 Subagent Result 区域已 append
│   ├── 未 append → 视为 FAILED，按 §4.4「Subagent 未 append Result 的处理」执行
│   └── 已 append → 按 Status 字段分级处理
├── 2. 🔴 读取 dispatch 文件的 Progress Log 段，转成主对话时间轴回放
│   ├── 把 step-start/step-done 映射为主对话 TodoWrite 状态更新
│   ├── 高亮异常事件（step-concern / step-blocked / degradation）
│   ├── 展示总耗时 + 每步耗时（便于后续优化 / 排查卡点）
│   └── Progress Log 缺失或断档 → 在 PMO 摘要中标注「进度不可追溯」WARN
├── 3. 检查返回内容是否完整（代码 + 报告 + Result 字段全填）
├── 4. 检查是否有上游问题需要打回
│   ├── 有 → 触发打回机制（RULES.md 八-B）
│   └── 无 → 继续
├── 5. 🔴 更新 dispatch_log/INDEX.md：追加一行记录本次 dispatch 结果
├── 6. 输出合并的 PMO 阶段摘要（含 Progress Log 时间轴回放）
├── 7. 自动流转到下一阶段
└── 8. Subagent 异常处理（见下方失败分类）

🔴 Subagent 返回状态分级处理：

| 返回状态 | 判断依据 | PMO 处理 |
|----------|----------|----------|
| ✅ DONE | 产出完整 + 无上游问题 | 正常流转到下一阶段 |
| ⚠️ DONE_WITH_CONCERNS | 产出完整但报告了非阻塞性 concerns | 读 concerns，关键的先处理再流转 |
| 🔄 NEEDS_CONTEXT | Subagent 报告缺少上下文（如「缺少 PRD 中的 xxx」） | PMO 补充上下文 → 重新 dispatch（不降级） |
| 🔁 QUALITY_ISSUE | 产出质量不达标（Review 严重问题 / 测试全失败） | 走正常打回机制（RULES.md 八-B） |
| ❌ BLOCKED | Subagent 报告上游阻塞 | 触发打回机制，不降级 |
| 💥 FAILED | Subagent dispatch 失败 / 产出不完整 | 降级为主对话内执行 |

🔴 BLOCKED/FAILED 升级策略（不是无脑重试）：
├── 缺上下文 → PMO 补充后重新 dispatch（同一 Subagent）
├── 任务太大 → PMO 拆分为更小的步骤，分步执行
├── 真的做不了 → 降级到主对话内执行（🔴 必须输出 WARN 日志，见 §4.1 降级 WARN 规则）
└── 🔴 永远不要在不改变任何条件的情况下重试同一个 Subagent

🔴 核心原则：Subagent 异常不能卡住整个流程，降级后仍需完成该阶段任务，
   但所有降级必须有 WARN 日志可追溯（静默降级 = 隐藏问题 = 违反红线 #9 闭环验证）
```

---

## 五、主对话产物协议

> 🔴 **协议补齐**：Dispatch 协议（§四）只覆盖 Subagent 执行场景。v7.3 契约化改造后，许多 Stage 可以主对话直接执行（由 AI Plan 模式决定）。主对话执行时的产物必须按本协议落盘，不能只存在对话记忆中。

### 5.1 适用场景

本协议适用于**主对话内执行**的任务：
- Goal-Plan Stage PRD 起草、PL-PM 讨论、多视角技术评审
- Blueprint Stage TC / TECH 起草、技术评审
- Review Stage 架构师 Code Review（若选主对话 approach）
- Dev Stage（v7.3.9+P0-14 默认主对话）
- Test Stage 环境启动
- Browser E2E 执行（默认）
- UI 还原验收、PM 验收（原本就在主对话）
- 任何 AI Execution Plan 声明的 "approach: main-conversation" 任务

📎 Subagent 执行场景仍走 Dispatch 文件协议（§四）。

### 5.2 产物文件命名约定

按任务类型：

| 任务 | 产物文件路径 | 格式 |
|------|------------|------|
| Goal-Plan Stage（PRD） | `{Feature}/PRD.md` | Markdown + YAML frontmatter（含 acceptance_criteria）|
| Goal-Plan Stage（技术评审）| `{Feature}/PRD-REVIEW.md` | Markdown |
| Goal-Plan Stage（PL-PM 讨论）| `{Feature}/discuss/PL-FEEDBACK-R{N}.md` + `PM-RESPONSE-R{N}.md` | Markdown |
| Blueprint Stage（TC）| `{Feature}/TC.md` | Markdown + YAML frontmatter（含 tests[]）|
| Blueprint Stage（TECH）| `{Feature}/TECH.md` | Markdown |
| Blueprint Stage（评审）| `{Feature}/TC-REVIEW.md` + `TECH-REVIEW.md`（或尾部段）| Markdown |
| Dev Stage 产出 | `{Feature}/dev-report.md` | Markdown + YAML frontmatter |
| Review Stage 架构师 | `{Feature}/review-arch.md` | Markdown + YAML frontmatter |
| Test Stage 环境 | `{Feature}/test-env.json` | JSON |
| Browser E2E | `{Feature}/browser-e2e-result.md` + `browser-e2e-screenshots/*.png` | Markdown + YAML + PNG |
| PM 验收 | `{Feature}/acceptance.md` | Markdown + YAML frontmatter |

### 5.3 产物文件必需字段（YAML frontmatter）

每份主对话产物文件头部必须包含 frontmatter：

```yaml
---
executor: main-conversation
task: {任务名，如 "review-arch"}
feature: {feature_id}
started_at: {ISO 8601 时间戳}
completed_at: {ISO 8601 时间戳}
status: DONE | DONE_WITH_CONCERNS | BLOCKED | FAILED
files_read:           # 审计：本次任务读过的文件（对应 Subagent 侧 "Files read"）
  - {绝对或相对路径}
concerns: []          # 非阻塞问题清单
---

# 产物正文...
```

🔴 **硬规则**：
- `executor: main-conversation` 必填（区别于 Subagent 产物的 `executor: subagent`）
- `started_at` / `completed_at` 必填（审计 + 独立性校验）
- `files_read[]` 必填（证明"角色规范必读且 cite"硬规则已遵守）
- `status` 必填（无状态字段 = 产物不完整）

### 5.4 Key Context 在主对话任务中的复用

主对话执行任务时，同样需要 Key Context 6 类（§四 Dispatch 文件的 Key Context）：
- 历史决策锚点 / 本轮聚焦点 / 跨 Feature 约束 / 已识别风险 / 降级授权 / 优先级

主对话任务的 Key Context 写法：
- **方式 A（推荐）**：写入 `state.json.planned_execution[{stage}].key_context`
- **方式 B**：在主对话输出 Execution Plan 块时显式输出一个 🎯 Key Context section

无论哪种方式，PMO 必须逐项判断 6 类，无则写 `-`（证明已判断）。

### 5.5 review-log.jsonl schema 扩展

主对话任务完成后，PMO 必须 append 一行到 `{Feature}/review-log.jsonl`：

```json
{
  "stage": "plan | review-arch | test-env | browser-e2e | ...",
  "executor": "main-conversation",
  "status": "DONE | ...",
  "timestamp": "2026-04-18T10:30:00Z",
  "artifact_path": "{Feature}/review-arch.md",
  "summary": "一句话摘要"
}
```

字段 `executor`：可选值 `"main-conversation"` | `"subagent"`。区分执行来源，便于审计和统计。

### 5.6 与 Dispatch 文件协议的对比

| 协议项 | Subagent dispatch 文件（§四）| 主对话产物文件（§五）|
|-------|-----------------------------|-------------------|
| 入参记录 | dispatch 文件 Input files + Key Context 段 | Execution Plan 块 + 主对话产物 frontmatter 的 files_read[] |
| 中途进度 | Progress Log（dispatch 内 append） | 对话本身可见（无需额外记录） |
| 产出 | Subagent 写 Result 段 | 产物文件本身（含 frontmatter）|
| 审计 | `dispatch_log/INDEX.md` 汇总 | `review-log.jsonl` 行 + 产物 frontmatter |
| 降级 WARN | 写入 dispatch 文件 Result 段 | 写入产物 frontmatter 的 `concerns[]` + review-log |

### 5.7 独立性保证（三视角评审场景）

Review Stage 要求三视角独立。如果架构师视角选主对话执行（推荐），需要配合：
- 开始前**显式清洗 context**："进入 code review 模式，采用怀疑者视角"
- 只读 Input Contract 列出的文件，不读其他视角的 review 报告
- 产物 frontmatter 的 `files_read[]` 必须列出已读文件（审计证据）
- 产物的 `generated_at` 时间戳必须与其他视角的 review 产物不同

这是 stages/review-stage.md Output Contract 的硬校验项。

---

## 六、目录结构索引

```
stages/          ← Stage 定义（PMO dispatch 的单位 + 角色任务规范权威，v7.3.10+P0-19-B 起）
├── goal-plan-stage.md              PM 写 PRD + PL-PM 讨论 + 多角色技术评审
├── blueprint-stage.md        QA 写 TC + TC 评审 + RD 技术方案 + 架构师评审
├── dev-stage.md              RD TDD 开发 + 单元测试（含 RD 任务规范）
├── review-stage.md           架构师 CR ∥ Codex Review ∥ QA 代码审查（含 CR 任务规范）
├── test-stage.md             集成测试 ∥ API E2E（含 QA 测试任务规范）
├── ui-design-stage.md        当前 Feature UI 设计
├── panorama-design-stage.md  全景设计同步更新（sitemap + overview）
└── browser-e2e-stage.md      Browser E2E 端到端验收

agents/          ← Subagent 执行协议（非任务规范）
└── README.md（本文件）        执行方式偏好 + 通用约束 + Codex CLI spawn + PMO dispatch 规范 + 主对话产物协议

roles/           ← 角色定义（职责 + 输出标准 + 反模式）
├── pmo.md       PMO 角色规范
├── pm.md        含 Goal-Plan Stage PRD 评审维度
├── qa.md        含 Blueprint Stage TC 评审规范
├── rd.md        含 Blueprint Stage 架构师方案评审规范
├── designer.md
└── product-lead.md
```

🔴 **v7.3.10+P0-19-B 变更说明**：
- 原 `agents/rd-develop.md` / `arch-code-review.md` / `qa-code-review.md` / `integration-test.md` / `api-e2e.md` 已物理合并进对应 `stages/*.md`。
- `agents/` 目录保留但只剩本 README（Subagent 执行协议）。
- 引用原 `agents/*.md § 某节` 的地方应改为「本文件 §某节」或 `stages/{stage}.md §某节`。
