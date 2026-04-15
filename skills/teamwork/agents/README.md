# Teamwork Subagent 通用规范

> 本目录定义各 subagent 的执行规范。PMO 启动 subagent 时，必须让 subagent 先读取本文件 + 对应的角色规范文件。

---

## 一、执行方式决策（PMO 必读）

> 🔴 PMO 在每个阶段开始前，必须确认该阶段的执行方式（Subagent / 主对话）。
> 禁止凭"感觉"判断——查下表。

### 执行方式速查表

```
| 阶段 | 执行方式 | 推荐模型 | 原因 |
|------|----------|----------|------|
| Plan Stage（PM写PRD+PL-PM讨论+技术评审） | 🤖 Subagent | Sonnet | 一体化产出定稿 PRD |
| Designer UI 设计 | 🤖 Subagent | Opus | 需要设计审美 + HTML 产出质量 |
| Blueprint Stage（QA TC + TC 评审 + RD TECH + 架构师评审） | 🤖 Subagent | Sonnet | 4 步内部闭环，有阻塞 → DONE_WITH_CONCERNS 回 PMO ⏸️ 用户 |
| Dev Stage（RD TDD+单测） | 🤖 Subagent | Opus | 核心编码，质量要求最高 |
| Review Stage（架构师CR∥Codex∥QA审查） | 🤖 Subagent | Sonnet | 三 review 并行，校验型 |
| UI 还原验收（Designer↔RD） | 主对话 | — | 多轮交互 |
| ~~Codex Code Review~~ | 已合入 Review Stage | — | 不再独立 dispatch |
| Test Stage（QA+测试） | 🤖 Subagent | Sonnet | 校验型任务：跑测试+对照 checklist+解析输出 |
| Browser E2E | 🤖 Subagent | Sonnet | 执行型任务：发请求+校验 response |
| ~~QA Lead 质量总结~~ | 已移除 | — | Test Stage 通过后直接 PM 验收 |
| PM 验收 | 主对话 | — | 需要与用户交互 |

📎 推荐模型说明：
├── Opus：需要创造性产出（代码/设计）或复杂架构判断的任务
├── Sonnet：校验型/执行型任务（跑测试、对照 checklist、结构化讨论）
├── —（主对话）：继承当前会话模型，不单独指定
└── PMO dispatch Subagent 时按宿主方式指定模型（Claude: Task model 参数 / Codex: agent toml model 字段）
```

### 判断原则

```
什么时候用 Subagent（🤖）：
├── 任务重（预期 >5 分钟执行时间），冷启动开销占比低
├── 产出大（大量代码/HTML/测试输出），放主对话会挤占 context
├── 需要外部工具（Codex CLI / AI 浏览器）
└── 内部可自闭环（无暂停点，输入输出都明确）

什么时候在主对话执行：
├── 任务轻（预期 <5 分钟），冷启动开销占比高
├── 需要与用户交互（暂停点）
├── 涉及多角色多轮交互（如 UI 还原验收 Designer↔RD 循环）
├── 需要实时感知主对话上下文变化
└── 评审/审查类任务（读+判断+出报告，无大量产出）
```

---

## 二、通用执行约束

### 2.1 文件读取

```
Subagent 启动后，必须按顺序读取：
1. 本文件（agents/README.md）→ 了解通用规范
2. 对应角色规范文件（如 agents/rd-develop.md）→ 了解具体任务
3. 角色规范中指定的项目文件（PRD/TC/TECH 等）→ 了解业务上下文
```

### 2.2 代码质量

```
所有 subagent 产出的代码必须遵守：
├── 项目 standards/common.md + 对应技术栈规范（backend.md / frontend.md）中的编码规范
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
└── 4. 角色报告（如 RD 自查报告，格式见各角色规范）
```

### 2.5 危险命令红线

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

## 三、Codex CLI 调用规范（仅 Codex Code Review 使用）

Codex CLI 仅用于 **Codex Code Review Subagent**（[review-stage.md](./review-stage.md)）的独立外部代码审查。各阶段的执行方式（Subagent / 主对话）见上方 §一「执行方式速查表」。

### 可用性检测（INIT.md Step 3.5 完成，结果缓存至会话结束）

```
├── codex_cli_available = true → Codex Code Review 正常执行
├── codex_cli_available = false → PMO 启动 Codex Code Review 时 ⏸️ 提示用户：
│   「Codex CLI 不可用。选择：
│     1️⃣ 解决环境问题后继续
│     2️⃣ 降级到 Claude Sonnet 执行同等 Review
│     3️⃣ 跳过 Codex Review」
├── 选择 2️⃣ 时：使用 review-stage.md §五 相同的 prompt 模板，执行引擎改为 Claude Sonnet Subagent
└── 跳过 Codex Review 不阻塞后续流程（记录跳过原因即可）
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
   下方的 Prompt 结构适用于所有宿主。
```

**Prompt 结构**（所有宿主通用）：

```
你是 Teamwork 协作框架中的 {角色名}。

请先读取以下文件了解执行规范：
1. {agents/README.md 的绝对路径}
2. {agents/角色规范.md 的绝对路径}

## 任务信息
- 功能：{缩写}-F{编号}-{功能名}
- 子项目：{子项目缩写}
- 子项目路径：{子项目根目录绝对路径}
- 文档目录：{子项目路径}/docs/features/{缩写}-F{编号}-{功能名}/
- 项目根目录：{项目根目录路径}
- 任务：{具体任务描述}
- 子项目类型：{business / midplatform}（midplatform 时需关注消费方影响）
  📎 PMO 从 teamwork_space.md「子项目」表的「类型」列读取
- 业务关联：{无 / BG-xxx-业务目标}（跨项目 Feature 时提供）

## 关键上下文（文件路径优先，短文档直接注入）

🔴 策略：**传文件路径让 Subagent 自己读原文**，而不是 PMO 摘要后注入。
   Subagent 的 context 是干净的，有充足空间读完整文件。PMO 摘要转述会造成信息衰减。

```
注入策略（二选一，PMO 按文件大小判断）：
├── 文件路径模式（默认）：在 prompt 中列出文件绝对路径，Subagent 自行 Read
│   适用：PRD / TC / TECH / ARCHITECTURE.md / standards/*.md 等长文档
│   好处：零信息损失，PMO prompt 更短
│
├── 内容直接注入模式：PMO 读取后将内容注入 prompt
│   适用：仓库级约束（CLAUDE.md/AGENTS.md/GEMINI.md）、短配置、关键摘要
│   好处：Subagent 不需额外 Read 调用，高优先级内容确保被看到
│
└── 🔴 无论哪种模式，PMO 必须在 prompt 中列出完整的文件清单（路径+用途），
    Subagent 报告中也必须列出实际读取的文件（可追踪）
```

🔴 仓库级约束（CLAUDE.md / AGENTS.md / GEMINI.md）始终用内容直接注入模式——短小、高优先级、必须确保 Subagent 看到。

按 Stage / 任务的文件清单（PMO 传路径，Subagent 自行读取）：
├── Plan Stage → PRD.md（如已有草稿）、PROJECT.md、KNOWLEDGE.md
├── UI Design Stage → PRD.md + design/sitemap.md + design/preview/*.html（相关页面）
├── Blueprint Stage → PRD.md + UI.md（如有）+ ARCHITECTURE.md
├── Dev Stage → PRD.md + TC.md + TECH.md + standards/*.md
├── Review Stage：
│   ├── 架构师 CR → TECH.md + ARCHITECTURE.md + RD 自查报告 + git diff 文件清单
│   ├── Codex Review → PRD.md + TECH.md + TC.md + 代码变更文件（🔴 不传架构师 CR 报告）
│   └── QA 代码审查 → TC.md + git diff 文件清单
├── Test Stage → TC.md（integration/E2E 章节）+ TECH.md（测试命令）
└── Browser E2E → TC.md（Browser E2E Scenarios 章节）+ 页面地址

## 编辑范围约束（PMO 必须注入 prompt）

🔴 你只能操作以下路径，其他路径一律禁止读写：
- 允许读写：{子项目路径}/（功能代码 + 测试 + 配置）
- 允许读写：{子项目路径}/docs/features/{功能目录}/（文档产出）
- 允许只读：{项目根目录}/docs/（ARCHITECTURE.md / KNOWLEDGE.md 等共享文档）
- 允许只读：{SKILL_ROOT}/standards/（开发规范）
- 🚫 禁止：其他子项目路径
- 🚫 禁止：.env / .env.* / credentials.* / *secret* 等敏感文件
- 🚫 禁止：.git/ 目录直接操作（通过 git 命令操作）

违反时：立即停止 → 记录到问题清单 → 返回 DONE_WITH_CONCERNS
```

### 启动前自问（PMO 必须确认）

```
Subagent 启动前，PMO 快速自检：
├── 关键上下文是否已注入 prompt？（不是只传路径）
├── 该 Subagent 需要哪些文件？我都读过了吗？
└── 有没有 KNOWLEDGE.md 中的相关经验需要传递？
```

### 4.2 启动前检查

```
PMO 启动 subagent 前必须确认：
├── 所有前置阶段已完成（如技术方案已确认）
├── 所需文件已生成且路径正确
├── 用户已确认可以进入该阶段
├── 无未解决的阻塞项
└── 多子项目模式下：确认子项目路径正确，文档目录已创建
```

### 4.3 完成后处理

```
Subagent 返回后，PMO 必须：
├── 1. 检查返回内容是否完整（代码 + 报告）
├── 2. 检查是否有上游问题需要打回
│   ├── 有 → 触发打回机制（RULES.md 八-B）
│   └── 无 → 继续
├── 3. 输出合并的 PMO 阶段摘要
├── 4. 自动流转到下一阶段
└── 5. Subagent 异常处理（见下方失败分类）

🔴 Subagent 返回状态分级处理（参考 superpowers 升级策略）：

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
├── 真的做不了 → 降级到主对话内执行
└── 🔴 永远不要在不改变任何条件的情况下重试同一个 Subagent

🔴 核心原则：Subagent 异常不能卡住整个流程，降级后仍需完成该阶段任务
```

---

## 五、目录结构索引

```
stages/          ← Stage 定义（PMO dispatch 的单位）
├── plan-stage.md              PM 写 PRD + PL-PM 讨论 + 多角色技术评审
├── blueprint-stage.md        QA 写 TC + TC 评审 + RD 技术方案 + 架构师评审
├── dev-stage.md              RD TDD 开发 + 单元测试
├── review-stage.md           架构师 CR ∥ Codex Review ∥ QA 代码审查（并行）
├── test-stage.md             集成测试 ∥ API E2E（并行）
├── ui-design-stage.md          当前 Feature UI 设计
├── panorama-design-stage.md           全景设计同步更新（sitemap + overview）
└── browser-e2e-stage.md             Browser E2E 端到端验收

agents/          ← 任务单元规范（被 stage 内部引用，不被 PMO 直接 dispatch）
├── README.md（本文件）  执行方式速查 + 通用约束 + PMO dispatch 规范
├── rd-develop.md        RD TDD 开发 + 自查
├── arch-code-review.md  架构师 Code Review + 架构文档更新
├── qa-code-review.md    QA 代码审查（读代码 + TC 逐条验证）
├── integration-test.md  集成测试
└── api-e2e.md           API E2E 端到端验收

roles/           ← 角色定义（职责 + 输出标准 + 反模式）
├── pmo.md       PMO 角色规范
├── pm.md        含 Plan Stage PRD 评审维度
├── qa.md        含 Blueprint Stage TC 评审规范
├── rd.md        含 Blueprint Stage 架构师方案评审规范
├── designer.md
└── product-lead.md
```
> ⚠️ Feature Planning 流程中 PM 在主对话中执行（需要与用户交互）。PM 与用户讨论达成共识后，有 UI 的子项目先启动 Designer Subagent（全景重建模式）验收全景设计，确认后再更新 PROJECT.md 并拆解 ROADMAP。
> 🌐 工作区级 Feature Planning：PM 先与用户确认 teamwork_space.md 架构变更，然后对每个受影响的有 UI 子项目，依次启动 Designer Subagent（全景重建模式）。每个子项目的全景设计独立确认后，再更新 PROJECT.md 并拆解 ROADMAP。
