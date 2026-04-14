# Teamwork Subagent 通用规范

> 本目录定义各 subagent 的执行规范。PMO 启动 subagent 时，必须让 subagent 先读取本文件 + 对应的角色规范文件。

---

## 一、Subagent 适用原则

```
✅ 适合用 Subagent 的阶段：
├── 输入明确（所有依赖文件已就绪）
├── 无用户交互（无暂停点）
├── 输出明确（代码/报告/文档）
└── 阶段内部可自闭环

❌ 不适合用 Subagent 的阶段：
├── 需要用户确认（暂停点）
├── 涉及多角色多轮交互（如 UI 还原验收 Designer↔RD 循环）
└── 需要实时感知主对话上下文变化
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

Codex CLI 仅用于 **Codex Code Review Subagent**（[codex-code-review.md](./codex-code-review.md)）的独立外部代码审查。其他 Subagent 统一使用 Claude Task 执行。

### 可用性检测（INIT.md Step 3.5 完成，结果缓存至会话结束）

```
├── codex_cli_available = true → Codex Code Review 正常执行
├── codex_cli_available = false → PMO 启动 Codex Code Review 时 ⏸️ 提示用户：
│   「Codex CLI 不可用。选择：
│     1️⃣ 解决环境问题后继续
│     2️⃣ 降级到 Claude Sonnet 执行同等 Review
│     3️⃣ 跳过 Codex Review」
├── 选择 2️⃣ 时：使用 codex-code-review.md §五 相同的 prompt 模板，执行引擎改为 Claude Sonnet Subagent
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

### 4.1 启动方式

PMO 使用宿主环境支持的子任务工具启动 subagent。

**Prompt 结构**：

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

## 关键上下文（PMO 必须注入，Subagent 不需自行查找）

🔴 PMO 在启动 Subagent 前，必须读取以下文件并将关键内容直接注入 prompt，
   而不是只传路径让 Subagent 自己去读。减少 Subagent 读错/漏读的风险。

🔴 如果项目根目录存在 `CLAUDE.md` / `AGENTS.md` / `GEMINI.md`，PMO 必须先读取并提炼与当前任务相关的仓库级约束，再一并注入 prompt。仓库级约束优先于 teamwork 默认规则。

按角色注入内容：
├── RD 开发 Subagent → 注入 PRD 验收标准 + TC 用例清单 + TECH 技术方案全文
├── 架构师 Tech Review → 注入 TECH 技术方案全文 + ARCHITECTURE.md 核心章节
├── 架构师 Code Review → 注入 TECH 技术方案要点 + RD 自查报告 + 修改文件清单
├── Codex Code Review → 注入 PRD 验收标准 + TECH 核心设计 + TC 用例摘要 + 代码变更文件（🔴 不注入架构师 CR 报告）
├── QA 代码审查 → 注入 TC 用例清单 + RD 修改文件清单
├── PRD 评审 → 注入 PRD 全文
├── TC 评审 → 注入 TC 全文 + PRD 验收标准
├── Designer UI 设计 → 注入 PRD 全文 + 验收标准 + 现有 sitemap.md（如有）
├── 集成测试 → 注入 TC 中标记为 integration 的用例 + 项目集成测试命令
├── API E2E → 注入 TC.md「API E2E Scenarios」章节 + API base URL + 前置条件
└── Browser E2E → 注入 TC.md「Browser E2E Scenarios」章节 + 页面地址 + 前置条件

注入格式：在 prompt 的「关键上下文」区块中用 markdown 引用块包裹内容。
若存在仓库级规则文件，放在「关键上下文」最前面，标题标注为「仓库级约束」。

## 编辑范围约束（PMO 必须注入 prompt）

🔴 你只能操作以下路径，其他路径一律禁止读写：
- 允许读写：{子项目路径}/（功能代码 + 测试 + 配置）
- 允许读写：{子项目路径}/docs/features/{功能目录}/（文档产出）
- 允许只读：{项目根目录}/docs/（ARCHITECTURE.md / KNOWLEDGE.md 等共享文档）
- 允许只读：{项目根目录}/.claude/skills/teamwork/standards/（开发规范）
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
| 💥 FAILED | Task 工具报错 / 产出不完整 | 降级为主对话内执行 |

🔴 BLOCKED/FAILED 升级策略（不是无脑重试）：
├── 缺上下文 → PMO 补充后重新 dispatch（同一 Subagent）
├── 任务太大 → PMO 拆分为更小的步骤，分步执行
├── 真的做不了 → 降级到主对话内执行
└── 🔴 永远不要在不改变任何条件的情况下重试同一个 Subagent

🔴 核心原则：Subagent 异常不能卡住整个流程，降级后仍需完成该阶段任务
```

---

## 五、当前已定义的 Subagent

| 文件 | 角色 | 阶段 | 默认引擎 | 说明 |
|------|------|------|----------|------|
| **Chain Subagents（一体化执行，减少 PMO relay）** | | | | |
| [dev-chain.md](./dev-chain.md) | RD + 架构师 | 🔗 RD 开发+自查 → 架构师 CR → 修复循环 | Claude | 技术方案确认后触发，内部包含修复循环≤3 轮 |
| [verify-chain.md](./verify-chain.md) | QA | 🔗 QA 审查 → 单元测试 → 集成测试 → API E2E | Claude | Dev Chain 通过后触发，只验证不修复 |
| [codex-code-review.md](./codex-code-review.md) | Codex（外部） | 🤖 Codex 独立代码审查 | Codex CLI | Dev Chain 通过后触发，独立于架构师 CR 的外部视角 |
| **单阶段 Subagents** | | | | |
| [pl-pm-discuss.md](./pl-pm-discuss.md) | PL + PM | PL-PM 协同讨论（🆕 Teams 模式） | Claude | PM 输出 PRD 初稿后触发 |
| [prd-review.md](./prd-review.md) | 多角色 | PRD 多角色评审 | Claude | PL-PM 讨论收敛 + PRD 定稿后触发 |
| [tc-review.md](./tc-review.md) | 多角色 | TC 多角色评审 | Claude | QA 输出 TC 后触发 |
| [arch-tech-review.md](./arch-tech-review.md) | 架构师 | 技术方案 Review | Claude | RD 输出技术方案后触发 |
| [ui-design.md](./ui-design.md) | Designer | UI 设计 | Claude | PRD 用户确认后 + 需要 UI 时触发 |
| [qa-e2e.md](./qa-e2e.md) | QA | Browser E2E 端到端验收（AI 浏览器） | Claude | Verify Chain 通过 + 用户确认执行 Browser E2E 时触发 |
| [qa-lead-review.md](./qa-lead-review.md) | QA Lead | 质量总结（全局审查测试体系完整性） | Claude | 🔴 每个 Feature 必须触发 |
| **Chain 内部引用的子规范（不单独启动）** | | | | |
| [rd-develop.md](./rd-develop.md) | RD | TDD 开发 + 自查 | — | Dev Chain 内部引用 |
| [arch-code-review.md](./arch-code-review.md) | 架构师 | Code Review + 架构文档更新 | — | Dev Chain 内部引用 |
| [qa-code-review.md](./qa-code-review.md) | QA | 代码审查（读代码 + TC 逐条验证） | — | Verify Chain 内部引用 |
| [integration-test.md](./integration-test.md) | QA | 集成测试 | — | Verify Chain 内部引用 |
| [api-e2e.md](./api-e2e.md) | QA | API E2E 端到端验收（curl/httpie） | — | Verify Chain 内部引用 |

> 后续扩展新 subagent 时，在本目录新增对应 `.md` 文件并更新此表。
> ⚠️ Feature Planning 流程中 PM 在主对话中执行（需要与用户交互）。PM 与用户讨论达成共识后，有 UI 的子项目先启动 Designer Subagent（全景重建模式）验收全景设计，确认后再更新 PROJECT.md 并拆解 ROADMAP。
> 🌐 工作区级 Feature Planning：PM 先与用户确认 teamwork_space.md 架构变更，然后对每个受影响的有 UI 子项目，依次启动 Designer Subagent（全景重建模式）。每个子项目的全景设计独立确认后，再更新 PROJECT.md 并拆解 ROADMAP。
