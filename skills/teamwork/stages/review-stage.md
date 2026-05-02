# Review Stage：三视角独立代码审查

> Dev Stage 通过后进入本 Stage。产出三份**独立视角**的代码审查报告（架构师 / QA / 外部），汇合到 REVIEW.md。
> 🔴 契约优先：独立性通过**产物结构**保证（而非强制执行方式）。AI 可按场景选择实现路径。
> 📎 **本文件即架构师 + QA 在 Review Stage 的完整任务规范**（v7.3.10+P0-19-B 合并 agents/arch-code-review.md + agents/qa-code-review.md）。外部模型视角单独走对应 CLI spawn（按 state.external_cross_review.model 选择 codex-agents/ 或 claude-agents/），prompt 模板见本文件 §外部模型代码 Review 任务规范。

---

## 本 Stage 职责

对 Dev Stage 产出的代码从三个独立视角审查：
- **架构师视角**：架构合理性、代码规范、ARCHITECTURE.md 同步
- **QA 视角**：TC 逐条验证覆盖、TDD 规范、测试质量
- **外部独立视角**（Codex 或等效外部模型）：发现同模型盲区、安全、第三方依赖

---

## 可配置点清单（v7.3.10+P0-55 新增）

| 可配置点 | 默认值 | 控制字段 | 决策时机 |
|---------|-------|---------|---------|
| `review_roles[]` | architect + qa + external（推荐默认含 external，代码层最后 gate）| `state.review_substeps_config.review_roles[]` | Stage 入口实例化 |
| 各角色 `execution` | architect / qa subagent（防鼓掌效应）+ external external-shell | `state.review_substeps_config.review_roles[].execution` | Stage 入口实例化 |
| `parallel_mode` | true（三视角并行）| `state.review_substeps_config.parallel_mode` | Stage 入口实例化 |
| 修复循环 max | 3 轮 | spec 内嵌 | Stage 出口判断 |
| 模型偏好（v7.3.10+P0-40）| Opus（AI Plan 模式默认）| `state.planned_execution.review.model` | Stage 入口 |
| `hint_overrides` | null | `state.review_substeps_config.hint_overrides` | Stage 入口实例化偏离 hint 时 |

🔴 不变内核：三视角独立性产物结构（独立 generated_at + files_read + 互不引用）+ external 异质性硬约束 + 完整性硬规则（按各自规范完整执行）。

---

## Input Contract

### 共用必读文件

```
├── {SKILL_ROOT}/stages/review-stage.md（本文件，含三视角任务规范）
├── {Feature}/PRD.md
├── {Feature}/TC.md
├── {Feature}/TECH.md
├── Dev Stage 产出（代码 diff + 自查报告路径）
└── {SKILL_ROOT}/standards/common.md

Subagent 模式额外：
└── {SKILL_ROOT}/agents/README.md（Subagent 执行协议）
```

### 各视角专属必读

```
架构师视角 额外读：
├── {SKILL_ROOT}/roles/rd.md（含架构师规范）
├── 本文件 §架构师 CR 任务规范
└── docs/architecture/ARCHITECTURE.md

QA 视角 额外读：
├── {SKILL_ROOT}/roles/qa.md
├── 本文件 §QA CR 任务规范
└── {Feature}/UI.md + preview/*.html（如有，用于设计-代码一致性）

外部视角（Codex / 其他模型） 额外读：
├── 🔴 严禁读：架构师 Review 报告（保持独立性）
└── 只基于代码 diff + PRD/TECH/TC + standards
```

### Key Context（逐项判断，无则 `-`）

- 本轮聚焦点（重跑时必填：上一轮问题清单）
- 已识别风险
- 降级授权（Codex CLI 不可用 → 🟢 AI 自主判断适合的降级模式，参考 agents/README.md §三「降级路径决策」）
- 优先级 / 容忍度

### 前置依赖

- `state.json.stage_contracts.dev.output_satisfied == true`
- Dev Stage 单测全绿
- state.json.current_stage == "review"

---

## 入口 Read 顺序（v7.3.10+P0-23 固定）

🔴 按以下顺序 Read，字节一致利于 prompt cache 命中。详见 [standards/prompt-cache.md](../standards/prompt-cache.md)。

```
Step 1: roles/rd.md（含架构师规范）, roles/qa.md        ← 角色层（L0 稳定）
Step 2: 无新模板                                        （checklist 在本 Stage spec 内）
Step 3: {Feature}/PRD.md, TC.md, TECH.md, REVIEW 基准 ← Feature 既有产物（L2）
        [条件] {Feature}/UI.md + preview/*.html         （若有 UI）
        docs/architecture/ARCHITECTURE.md（架构师视角）
Step 4: {Feature}/state.json                           ← 🔴 最后，动态入口（L3）
```

🔴 外部模型视角独立 dispatch 时，外部 session 内不经过 state.json 入口流，只读 diff + PRD/TECH/TC + standards（保持独立性）。
🔴 R3 约束：state.json 入口 Read 1 次 → 中段 0 读写 → 出口 Read 1 次 + Write 1 次。fix 修复循环豁免 ≤3 轮、每轮 ≤1 次 Write；全 Stage ≤ 8 次。

🌐 v7.3.10+P0-38：Stage 入口实例化时宣告 external 角色启用情况：
- `"external" in state.review_substeps_config.review_roles[].role`：`🌐 external 角色启用: model={state.external_cross_review.model}`
- 不在 review_roles[]：不输出此行（external 角色未启用）

---

## 🆕 Review Stage 入口实例化（v7.3.10+P0-48 引用统一规范）

> 🔴 **遵循 [standards/stage-instantiation.md](../standards/stage-instantiation.md) 通用流程**（4 步：read state hints → 决策 active_roles + execution + round_loop → 输出 5 行 Execution Plan → 默认通道 / 标准通道判定）。

**Review Stage 特定参数**：

- 候选 `active_roles`：Architect / QA / external（推荐：architect/qa 默认 active；external 视代码复杂度，推荐默认含 external——代码层最后 gate）
- `key_outputs`：CR finding / TC 验证结果 / external review report
- 子步骤：三视角并行审查（active_roles 互不依赖）
- `review_substeps_config` 特有字段：`parallel_mode: true`（三视角并行）
- 决策信号：Dev Stage 代码量 / 改动复杂度 / 跨模块影响

**特殊例外**：
- architect / qa 通常 execution=subagent（fresh context 防鼓掌效应）
- external 固定 execution=external-shell

---

### 主对话输出 Tier 应用（v7.3.10+P0-54 升级）

> 🔴 **遵循 [standards/output-tiers.md](../standards/output-tiers.md) 通用 Tier 1/2/3 规范 + 4 类反模式禁令**。

**Review Stage 特定 Tier 应用**：

- **Tier 1（永远输出）**：5 行 Execution Plan / 三视角 verdict（PASS / NEEDS_FIX）/ 🔴 阻塞 finding 摘要 / ⏸️ 用户处理 QUALITY_ISSUE 暂停点
- **Tier 2（命中折叠）**：🟡 建议 / 🟢 优化 finding 摘要（仅 round 2+ 有累积时）/ external review ADOPT/REJECT 摘要 / 修复循环重启时的 round 标记
- **Tier 3（不输出，走 state.json）**：review_substeps_config 详细字段 / 各角色 execution / files_read[] / generated_at / 三视角独立性校验细节

---

## Process Contract

### 必做动作

1. **三视角独立审查**（顺序无关，可并行可串行）
   - 每个视角独立读取自己的输入文件，产出独立报告
   - 每个视角不得引用其他视角的报告
   - 每个视角必须记录自己读过的文件清单（审计）

2. **架构师 Code Review**
   - 按本文件 §架构师 CR 任务规范
   - 产出 `review-arch.md`
   - 维度：架构合理性 / 代码规范 / 性能 / 安全 / ARCHITECTURE.md 同步

3. **QA 代码审查**
   - 按本文件 §QA CR 任务规范
   - 产出 `review-qa.md`
   - 维度：TC 逐条覆盖 / TDD 规范 / 集成测试代码完整性 / 设计-代码一致性

4. **外部模型独立审查**（🟡 v7.3.10+P0-38 重构：external 升格为评审角色，受 review_substeps_config.review_roles[] 控制）
   - 🟡 **本 Stage external 评审现受 review_roles[] 控制**（v7.3.10+P0-38 改造）：`"external" in state.review_substeps_config.review_roles[].role` 时执行（推荐默认含 external——代码层最后 gate），不在 review_roles[] 时跳过本步（PMO 在 Stage 入口实例化时基于代码复杂度信号决定）。
   - 🔴 **默认推荐含 external**：与 v7.3.10+P0-27/P0-28 行为兼容；PMO 在 Review Stage 入口默认推荐 review_roles[] 含 external。仅当代码极简或用户主动调整时不含。
   - 🔴 **外部模型选择**（v7.3.10+P0-72 PMO 直接判定）：
     - PMO 在 Stage 入口实例化时**自报当前宿主**（基于自身运行环境，不读 state 旧值 / 不读项目目录标记），按当前宿主应用 E1 同源约束算 external 候选（详见 [standards/external-model.md § E2 PMO 直接判定](../standards/external-model.md)）
     - PMO 自报与 state 旧 host_main_model 不一致 → 按当前自报值更新 state + state.concerns 记录漂移 + 主对话显式声明切换
     ```
     ├── Claude Code 主对话 + Codex 可用 → 通过 Task/MCP 调 codex 子进程（codex-agents/reviewer.toml，fresh session）
     ├── Codex CLI 主对话 + Claude 可用 → shell 调 claude --print 子进程（claude-agents/invoke.md 范本，fresh session）
     │   └── 🔴 禁止："外部视角 = 主对话同模型自审"——必须是异质模型独立 spawn，不能在当前 session 内叙述
     ├── 两种宿主的独立性保证一致：fresh context + 独立 dispatch 文件 + 独立 generated_at
     └── 无可用外部模型（探测时所有候选不可用 / 调用失败）→ 进入降级分支（state.concerns 加 WARN + 跳过本步，依赖架构师 + QA 审查作为代码层 gate）
     ```
   - 按本文件 §外部模型代码 Review 任务规范
   - 产出 `review-external.md`（frontmatter：`perspective: external-{model}`（external-codex / external-claude），`executor: {对应调用机制描述}`）
   - 维度：逻辑正确性 / 安全漏洞 / 第三方依赖真实性 / 并发安全 / 代码质量

5. **汇合到 REVIEW.md**（PMO 职责）
   - 合并去重（同一文件同一位置问题合并）
   - 按严重程度排序（🔴 阻塞 > 🟡 建议修复 > 🟢 优化）

### 过程硬规则

- 🔴 **角色规范必读且 cite**：每视角开始前必读对应 §任务规范 + `roles/*.md`，产出前 cite 要点
- 🔴 **三视角独立性（结构约束）**：
  - 每份报告必须有独立 `generated_at` 时间戳
  - 每份报告必须列出"本视角读过的文件"清单
  - 三份报告互不引用（`grep -r "review-arch" review-external.md` 应为空，反之亦然）
- 🔴 **外部模型独立性硬约束**：外部视角严禁读架构师 / QA 的 review 报告
- 🔴 **完整性**：每个视角按各自规范完整执行，不能因为另一个视角已通过就简化
- 🔴 **不修复**：Review 只审不改，发现问题返回 PMO 安排 RD 修复
- 🔴 **循环控制**：修复-重跑循环 ≤3 轮
- 🔴 **Stage 完成前 git 干净** → 统一遵循 [rules/gate-checks.md § Stage 完成前 git 干净](../rules/gate-checks.md#-stage-完成前-git-干净v739-硬规则p0-集中化)（本 Stage commit message：`F{编号}: Review Stage - fix {简述}`；每轮修复独立 commit；auto_commit 为**数组**字段，多轮 QUALITY_ISSUE 修复 append）

### 多视角独立性（产物结构保证）

这是本 Stage 契约的核心。Output Contract 要求三份独立报告 + 不互相引用 + 时间戳独立——AI 为满足这些产物条件，**结构上**必然做三次独立审查。

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需字段 |
|---------|------|---------|
| `{Feature}/review-arch.md` | Markdown + YAML frontmatter | `perspective: architect`, `generated_at`, `files_read[]`, `findings[]`（含 severity/file/line/message/suggestion） |
| `{Feature}/review-qa.md` | Markdown + YAML frontmatter | `perspective: qa`, `generated_at`, `files_read[]`, `tc_coverage_report`, `findings[]` |
| `{Feature}/review-external.md` | Markdown + YAML frontmatter | `perspective: external-{model}`（external-codex / external-claude）, `generated_at`, `files_read[]`, `findings[]` |
| `{Feature}/REVIEW.md` | Markdown | 汇总三份 + 合并去重问题清单 + 修复记录 |

### 机器可校验条件

- [ ] 三份 review 文件都存在
- [ ] 每份 frontmatter 可 YAML 解析且 `perspective` 字段唯一
- [ ] 三份 `generated_at` 时间戳互不相同
- [ ] 三份互不引用（`grep -l "review-{other}"` 互查为空）
- [ ] 每份都有 `findings[]`（空列表合法，但需显式 `findings: []`）
- [ ] 架构师视角必须有 ≥3 条 findings，若确实无则显式说明（例：`{severity: info, message: "整体高质量，未发现问题"}`）

### Done 判据

- 三份报告存在且通过结构/独立性校验
- 合并后无 🔴 阻塞问题（或有但已修复）
- REVIEW.md 落盘汇总
- `state.json.stage_contracts.review.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 三视角均无阻塞 | 进入 Test Stage |
| ⚠️ DONE_WITH_CONCERNS | 有 🟡 建议但无 🔴 阻塞 | PMO 评估，非阻塞则继续 |
| 🔁 NEEDS_FIX | 任一视角有 🔴 阻塞 | RD 修复 → 重跑相关视角（≤3 轮） |
| ❌ FAILED | Codex 不可用且降级失败 | PMO ⏸️ 用户选择 |

### 修复循环规则

```
Review Stage NEEDS_FIX 时：

1. PMO 合并三份 review 的问题清单（去重）
2. 派发 RD 修复（PMO dispatch 或主对话）
3. 修复范围 ≤2 文件且无逻辑变更 → 只重跑发现问题的视角
4. 修复涉及逻辑变更 → 全部三个视角重跑
5. 🔴 最多 3 轮，超出 → ⏸️ 用户决策

Codex 独立性保障：
├── 重跑时 Codex 仍不看架构师 / QA 报告
├── Codex 的问题由 RD + 架构师评估后决定是否采纳
└── 第三方依赖真实性问题严肃对待（Codex 说包不存在 → 必须核实）
```

---

## AI Plan 模式指引

📎 Execution Plan 3 行格式 → [SKILL.md](../SKILL.md#-ai-plan-模式规范v73-新增)。

本 Stage 默认 `hybrid`（架构师主对话 + QA / 外部模型并行 Subagent）。

三路分工理由：
- 架构师视角需项目全局上下文（ARCHITECTURE 演化、历史决策），主对话保留累积
- QA / 外部模型视角需独立性，Subagent / 异质 CLI 天然 fresh context
- 架构师主对话时加「怀疑者视角」prompt 防鼓掌（见下方）

🔴 **v7.3.10+P0-40 模型默认值**：
- **架构师 Code Review**：默认 `opus`（深度架构判断不可降级；含 Review Stage + Bug 流程必经）
  - 主对话模式：继承用户会话模型（如非 Opus，建议关键 Feature 切换；架构 review 是质量最后 gate）
  - Subagent 模式：dispatch 时显式 `model: opus`
- **QA Code Review**：默认 `sonnet`（执行型校验，TC 逐条覆盖判断 Sonnet 够用）
  - Subagent 模式：dispatch 时显式 `model: sonnet`
- **external Code Review**：异质模型（codex / claude-cli），与 Claude 模型选择正交

典型偏离：
- 小改动 / 主对话 context 足够 → 三视角全 `main-conversation`（需清洗 context 防创建者偏见）
- 大改动 / 要求最强独立性 → 三视角全 `subagent`（Dispatch 文件 Batch 字段同批次）

🔴 不论哪种 approach，Output Contract 的独立性校验（三份产物独立 generated_at / files_read / 不互相引用）都必须满足。

**Expected duration baseline（v7.3.3）**：hybrid（默认）10-20 min（三路并行，墙钟 = max(架构师, QA, Codex)）；全 subagent 约 15-25 min（冷启动税）；全主对话 8-15 min（小改动）。如发生 NEEDS_FIX 重跑，每轮 +5-10 min。

### 架构师主对话 Review 防鼓掌机制（approach 含 main-conversation 时必做）

- 开始前显式声明"进入架构师审查模式，采用怀疑者视角"
- 不读 RD 自查报告（只看代码 diff + TECH.md + ARCHITECTURE.md）
- 强制产出 ≥3 条批评；若确实无，显式说明"代码高质量，未发现"+ 审查过的维度清单

---

## 架构师 CR 任务规范

> 本节整合 v7.3.10+P0-19-B 前的 `agents/arch-code-review.md` 完整规范。主对话 / Subagent 模式均适用。

### 1. 角色定位

你是 Teamwork 协作框架中的 **资深架构师**，负责审查 RD 的代码实现并维护项目架构文档。你是独立于 RD 开发者的代码审查角色，核心职责是**确保代码实现符合技术方案和架构规范，并在 Review 后更新架构文档**。

### 2. Review 维度（全部必查）

```
📋 资深架构师 Code Review
├── 技术方案一致性
│   ├── 代码实现是否忠实于 TECH.md 的设计
│   ├── 是否有偏离技术方案的实现（未经确认的变更）
│   └── 接口/数据结构是否与方案一致
├── 架构合规性
│   ├── 分层是否正确（业务逻辑不在 UI 层/数据层）
│   ├── 依赖方向是否合理（无反向/循环依赖）
│   ├── 模块职责是否单一清晰
│   └── 是否复用了已有模块/组件（避免重复造轮子）
├── 代码质量
│   ├── 命名/分包是否与项目规范一致
│   ├── 是否有 God Class 或过长方法（>300行/文件，>50行/方法）
│   └── 复杂逻辑是否有足够注释
├── 性能与安全
│   ├── 🔴 并发与竞态（涉及共享资源/数据库写操作时必审）：
│   │   ├── TOCTOU：是否存在「先 SELECT 判断 → 再 UPDATE」的竞态模式？
│   │   ├── 原子性：余额/库存/计数器是否用原子 SQL 而非先读后写？
│   │   ├── 锁策略：并发写同一行时有无乐观锁/悲观锁保护？
│   │   ├── 死锁风险：多表/多资源加锁时锁顺序是否一致？是否有循环等待？
│   │   ├── 脏读/不可重复读：事务隔离级别是否匹配业务需求？（读已提交 vs 可重复读）
│   │   ├── 事务粒度：事务内是否包含外部调用导致长事务？
│   │   └── 幂等性：写入接口重复调用是否安全？重试机制是否会产生副作用？
│   ├── 🔴 资源耗尽（涉及外部资源/大数据量时必审）：
│   │   ├── 连接池：数据库/Redis/HTTP 连接是否正确归还？是否有连接泄漏路径？
│   │   ├── 内存：大数据集是否用流式处理？是否有未释放的缓冲区/闭包引用？
│   │   ├── 文件句柄：打开的文件/socket 是否在 defer/finally 中关闭？
│   │   ├── 线程/协程：是否有无限制的并发 spawn？是否有 goroutine/thread 泄漏？
│   │   └── 查询性能：是否有 N+1 查询？全表扫描？缺失索引的 WHERE 条件？
│   ├── 🔴 缓存策略（涉及缓存时必审）：
│   │   ├── 缓存击穿：热点 key 过期瞬间是否有并发回源保护？（互斥锁/逻辑过期）
│   │   ├── 缓存穿透：不存在的 key 是否会穿透到 DB？（空值缓存/布隆过滤器）
│   │   ├── 缓存雪崩：大量 key 是否同时过期？（过期时间是否加随机偏移）
│   │   ├── 一致性：缓存更新策略是否会导致数据不一致？（先删缓存还是先更新 DB）
│   │   └── 无缓存时输出：✅ 本功能不涉及缓存
│   ├── 🔴 安全漏洞：
│   │   ├── 注入：SQL 注入 / NoSQL 注入 / 命令注入 / 模板注入
│   │   ├── XSS：用户输入是否在输出时转义？
│   │   ├── 越权：水平越权（访问他人数据）/ 垂直越权（提升权限）
│   │   ├── 敏感数据：密码/token/密钥是否明文存储或日志输出？
│   │   └── 第三方依赖安全：
│   │       ├── 依赖包名是否真实存在？（防 AI 幻觉生成不存在的包名 → 供应链攻击）
│   │       ├── 是否有已知 CVE 漏洞？（检查版本号）
│   │       └── 许可证是否兼容项目？（GPL 传染性等）
├── 降级兜底实现验证（TECH.md 声明了降级策略时必审）
│   ├── 对照 TECH.md 降级策略，检查代码是否已落地：
│   │   ├── 声明「兜底」→ 是否有 fallback 值 / 降级逻辑 / 默认返回？
│   │   ├── 声明「fail-fast」→ 是否正确抛异常 / 返回错误码？（禁止静默吞错）
│   │   └── 声明「重试」→ 是否有重试次数上限 + 退避策略 + 最终失败处理？
│   ├── 过度兜底检查：
│   │   ├── 核心业务逻辑（金额/权限/数据完整性）是否错误地被 try-catch 吞掉？
│   │   ├── 是否存在 catch-all 空处理（catch (e) {}）隐藏了真实错误？
│   │   └── 降级返回值是否可能导致下游误判为正常数据？
│   └── 缺失兜底检查：
│       ├── 外部 HTTP 调用是否设置了超时？
│       ├── 第三方 SDK 调用是否有异常捕获？
│       └── 异步消息消费失败是否有死信队列或告警？
├── 🔴 日志完整性审查（v7.3.10+P0-69 扩展自原「异常 ERROR 日志审查」 · 实证 F059 触发）
│   ├── 6.1 异常分支 ERROR 日志（🔴 BLOCKER · 原硬规则保留 · 详见 standards/backend.md「三方/外部服务调用异常 ERROR 日志规则」）
│   │   ├── 扫描所有跨进程调用点：三方 API / 内部其他服务 / 云 SDK / 中间件
│   │   ├── 对每个调用点验证：
│   │   │   ├── 异常分支（含 try/catch、非 2xx、业务错误码、超时）是否有 ERROR 日志？
│   │   │   ├── ERROR 日志是否包含：调用目标 + traceId + 请求/响应摘要 + 耗时 + 业务上下文？
│   │   │   ├── 与降级并存时：是否先打 ERROR（异常本身）再打 WARN（降级动作）？（两条都必须）
│   │   │   └── 是否仅靠 APM/sidecar 自动上报而业务层缺失日志？（不免除打日志义务）
│   │   └── 任一缺失 → 🔴 BLOCKER（缺失即阻塞 CR）
│   ├── 6.2 关键路径 INFO 日志（v7.3.10+P0-69 新增 · 兜底机制 · 不依赖 PRD 显式声明）
│   │   > 实证触发：F059 ship 后才发现 7 个关键路径无 SLogger.i（notifySoReady / notifyFocus / drainQueue / execute / fetchConfig / cache hit-miss / download / MD5 校验 / rename）。当时 QA 没查 PRD AC（P0-68 修复了），架构师 §6 也只查 ERROR 日志（本 P0-69 修复）。两层都漏 → 用户实测无法判断"功能是否真在跑"。
│   │   ├── 识别核心数据流（架构师主动识别 · 不依赖 PRD 显式声明）：
│   │   │   ├── API 入口（请求接收 / 参数解析）
│   │   │   ├── 业务逻辑关键节点（决策分支 / 状态变迁 / 长操作起止）
│   │   │   ├── 持久化操作（DB 写入 / cache 读写 / 文件 IO）
│   │   │   ├── 跨进程调用（三方 API / 内部服务 / 云 SDK / 中间件）
│   │   │   ├── 异步触发点（事件订阅 / 队列 drain / worker init）
│   │   │   └── 外部依赖结果（fetchConfig 返回 / 第三方响应 → 决策依据）
│   │   ├── 每个关键节点验证 INFO/DEBUG 日志覆盖：
│   │   │   ├── **入口**：哪个调用方触发 / 关键参数（脱敏）
│   │   │   ├── **状态变迁**：worker init / 双条件齐备 / 队列 drain 起止 / 流程切换
│   │   │   ├── **长操作**：下载 / 上传 / IO / 网络 → 起点 + 终点 + 耗时
│   │   │   ├── **决策分支**：cache hit/miss / 校验通过/失败 / 降级触发 / 跳过原因
│   │   │   └── **外部依赖结果**：fetchConfig 返回 / 第三方响应字段（脱敏）
│   │   ├── 验证方式：grep `SLogger.i\|Log.i\|logger.info\|info!\|tracing::info` 在每个识别的关键节点
│   │   ├── 缺失分级：
│   │   │   ├── 🟡 concern（默认）：缺失但不阻塞 ship · 落 follow-up · ship 报告显式标注
│   │   │   └── 🔴 BLOCKER（特殊）：用户线上排障关键路径缺日志 / 已知历史排障难点路径无日志
│   │   └── 与 §6.1 区别：6.1 异常 ERROR 是**正确性兜底**（缺=不知道哪挂了）/ 6.2 关键路径 INFO 是**可观测性兜底**（缺=不知道有没有跑到）
│   ├── 6.3 安全脱敏（与上方「敏感数据」段联动）
│   │   ├── 密码 / token / 密钥 / API key / OAuth 凭证 · 全部不入日志
│   │   ├── 大字段（base64 / file blob / 长 JSON）· 截断 + 摘要 + 长度
│   │   └── PII（手机号 / 身份证 / 邮箱）· 按项目规范脱敏（如手机号留前 3 后 4）
│   └── 与 PRD AC §logging 的协作：如 PRD 显式声明日志 AC（P0-68 telemetry/logging category）→ QA Step 4.5 用 grep_keyword 精确对账走 BLOCKER；如 PRD 未声明 → 本段 6.2 主动兜底走 concern。两层互补，避免 PM 没写日志要求时全链路漏检。
├── 🔴 Schema 同步验证（涉及数据库变更时必审）：
│   ├── 对照 TECH.md「Schema 影响分析」表，逐行验证每个受影响 Model/Struct 是否有对应代码变更
│   ├── 每个变更的 Struct 的所有 SQL 查询（SELECT/RETURNING/INSERT）列列表是否与 Struct 字段匹配
│   ├── 迁移文件是否可逆（up + down 都有且合理）
│   ├── database-schema.md 是否已同步更新（Model 映射表 + SQL 引用点 + 变更记录）
│   └── 影响分析表有遗漏 → 标记为 🔴 阻塞项，RD 必须补全后重新 Review
├── 🔴 防御性路径审查（每个数据流必须覆盖 4 条路径）
│   ├── 审查方法：对每个核心数据流（API 入口 → 业务逻辑 → 持久化），逐一检查：
│   │   ├── ① Happy Path：正常输入 → 预期输出（RD 通常已覆盖）
│   │   ├── ② Nil/Null Path：关键字段为 null/undefined/零值时是否安全？
│   │   ├── ③ Empty Collection Path：列表/Map 为空时是否有兜底？（空页面/空响应/默认值）
│   │   └── ④ Upstream Error Path：上游返回错误/超时/脏数据时，当前层是否正确处理？
│   ├── 报告格式：
│   │   | 数据流 | Happy | Nil/Null | Empty | Upstream Error | 缺失路径 |
│   │   |--------|-------|----------|-------|----------------|----------|
│   │   | [流1]  | ✅    | ✅/❌   | ✅/❌ | ✅/❌          | [具体缺失] |
│   └── 发现缺失路径 → 标注为中/高严重程度问题，记录到问题清单
└── 架构文档同步
    ├── 新增/修改的模块是否需要更新 ARCHITECTURE.md
    └── 架构调整是否需要记录设计决策
```

### 3. 执行流程

```
Step 1: 读取所有输入文件，理解技术方案和需求
Step 2: 查看 RD 新增/修改的代码文件
├── 根据 RD 自查报告中的文件清单定位代码
├── 逐文件审查架构合规性
└── 对照 TECH.md 检查实现一致性
Step 3: 检查 RD 自查报告是否有遗漏
Step 4: 如发现问题，尝试内部修正：
├── 小问题（命名不规范、注释缺失等）→ 直接修正代码并在报告中说明
└── 大问题（架构不合理、方案偏离等）→ 记录到问题清单
Step 5: 更新架构文档
├── ARCHITECTURE.md：
│   ├── 读取 docs/architecture/ARCHITECTURE.md
│   ├── 根据代码变更更新相关章节（模块说明、架构图、目录结构等）
│   ├── 更新「最后更新」字段
│   └── 无架构变更则注明「ARCHITECTURE.md 无需更新」
├── database-schema.md 实现层补充（涉及 schema 变更时）：
│   ├── 📎 设计层内容（表结构、ER 图、设计原则）已在 Tech Review 阶段更新
│   ├── 补充「Model/Struct 映射」表（RD 实际创建/修改的 Model + 文件路径）
│   ├── 补充「SQL 查询引用点」表（实际的 SQL 查询 + 文件路径 + 行号）
│   ├── 更新「变更记录」
│   └── 无 schema 变更则注明「database-schema.md 无需更新」
Step 6: 输出 Review 报告
```

#### 3.1 执行约束

```
🔴 强制要求：
├── 必须逐文件审查代码，不能只看自查报告
├── 必须对照 TECH.md 检查实现一致性
├── 必须检查并更新架构文档（或明确注明无需更新）
├── 发现问题必须标注严重程度（高/中/低）
└── 有疑问时记录到问题清单，不要自行假设

❌ 禁止：
├── 自行修改 PRD/UI/TC 等上游文档
├── 自行决定跳过架构文档更新
├── 跳过代码审查只看报告
└── 修改测试代码的逻辑（只可修改命名/注释等非逻辑变更）
```

### 4. 架构文档更新规则

```
📁 架构文档位置：docs/architecture/

🔴 两阶段更新分工（database-schema.md）：
├── Tech Review 后（arch-tech-review）→ 更新设计层：表结构、ER 图、设计原则
└── Code Review 后（本阶段）→ 补充实现层：Model/Struct 映射、SQL 引用点

ARCHITECTURE.md 更新规则（仅 Code Review 阶段执行）：
├── 新增模块 → 在「核心模块说明」中添加
├── 架构调整 → 更新架构图 + 记录设计决策
├── 目录结构变化 → 更新「目录结构」章节
├── 分层变化 → 更新「分层与职责」章节
├── 无架构变更 → 在 Review 报告中注明「架构文档无需更新」
└── 更新后在「最后更新」字段记录日期和简述

⚠️ 架构文档不存在时（初始化阶段已自动创建基础版，此情况极少出现）：
├── 按 templates/architecture.md 模板创建
└── 填写项目基本信息和当前架构
```

### 5. 架构师 Review 输出模板

```
📋 资深架构师 Code Review 报告
├── 功能：F{编号}-{功能名}
│
├── 1️⃣ 技术方案一致性：
│   | 技术方案要点 | 代码实现 | 一致性 | 说明 |
│   |-------------|---------|--------|------|
│   | [要点1]     | [文件]  | ✅/❌  | xxx  |
│
├── 2️⃣ 架构合规性：
│   | 检查项 | 结果 | 说明 |
│   |--------|------|------|
│   | 分层正确 | ✅/❌ | xxx |
│   | 依赖方向 | ✅/❌ | xxx |
│   | 职责单一 | ✅/❌ | xxx |
│   | 模块复用 | ✅/❌ | xxx |
│   | 数据源验证 | ✅/❌/N/A | 跨服务字段 + DB Schema 列引用是否追溯确认 |
│
├── 3️⃣ 降级兜底验证：
│   | 依赖点 | TECH.md 策略 | 代码实现 | 结果 |
│   |--------|-------------|---------|------|
│   | [依赖1] | 兜底/fail-fast/重试 | [文件:行号] | ✅ 一致 / ❌ 缺失 / ⚠️ 过度兜底 |
│   无外部依赖时输出：✅ 本功能不涉及外部依赖
│
├── 4️⃣ 并发/资源/缓存审查：
│   | 审查项 | 结果 | 说明 |
│   |--------|------|------|
│   | 并发竞态 | ✅/❌/N/A | [具体发现] |
│   | 资源耗尽 | ✅/❌/N/A | [具体发现] |
│   | 缓存策略 | ✅/❌/N/A | [具体发现] |
│   | 安全漏洞 | ✅/❌/N/A | [具体发现] |
│   | 第三方依赖 | ✅/❌/N/A | [包名真实性 + CVE + 许可证] |
│   不涉及的项标注 N/A + 原因
│
├── 5️⃣ 问题清单：
│   | 维度 | 问题 | 严重程度 | 处理方式 |
│   |------|------|----------|----------|
│   | xxx  | xxx  | 高/中/低  | 已修正/待修复 |
│
├── 6️⃣ 防御性路径审查：
│   | 数据流 | Happy | Nil/Null | Empty | Upstream Error | 缺失路径 |
│   |--------|-------|----------|-------|----------------|----------|
│   | [流1]  | ✅    | ✅/❌   | ✅/❌ | ✅/❌          | [具体] |
│   无外部数据流时输出：✅ 本功能无需防御性路径审查
│
├── 7️⃣ 架构文档更新：
│   ├── 更新内容：[具体更新了什么 / 无需更新]
│   └── 更新文件：docs/architecture/ARCHITECTURE.md
│
├── Review 结论：✅ 通过 / ⚠️ 有建议 / ❌ 需修改
└── 修改说明（如有内部修正）：[修正了哪些文件的什么问题]
```

### 6. 上游问题清单（如有）

```
⚠️ 上游问题记录
| # | 来源 | 问题 | 影响 | 建议 |
|---|------|------|------|------|
| 1 | TECH | [描述] | [影响] | [建议] |

无上游问题时输出：✅ 无上游问题
```

---

## QA CR 任务规范

> 本节整合 v7.3.10+P0-19-B 前的 `agents/qa-code-review.md` 完整规范。主对话 / Subagent 模式均适用。

### 1. 角色定位

你是 Teamwork 协作框架中的 **QA 工程师**，负责对 RD 的代码实现进行质量审查。你的核心职责是 **阅读实际代码，逐条验证每个 TC 是否被正确实现和测试**。你独立于架构师 Code Review，关注的是功能覆盖度和测试有效性，而非架构合规性。

🔴 **核心原则**：必须阅读代码变更，逐条验证 **PRD AC ↔ 代码**（Step 4.5）+ **TC ↔ 代码**（Step 3）双重对账，不能仅看指标数字或测试通过率。

🔴 **TC 覆盖 ≠ AC 覆盖（v7.3.10+P0-68 实证补强）**：AC 中的非功能性承诺（埋点 / 日志 / 监控 / 配置 / 性能 / 安全校验）TC 通常无法覆盖，必须 **Step 4.5 用代码 grep 直接对账**。F059 实战教训：5 个 PRD 埋点 ship 后才发现全部未实现 + 7 个关键路径无 SLogger.i，因为 TC 没覆盖埋点 / 日志这种非功能性 AC，QA Review 也只在 TC 中转模式下工作，全链路漏检。

### 2. 执行流程

```
Step 1: 读取 TC.md，逐条理解每个测试场景的验证意图
        ├── 列出所有 TC 编号及其场景描述
        └── 理解每条 TC 要验证的核心行为

Step 2: 读取代码变更（实现代码 + 测试代码）
        ├── 根据 TECH.md 定位实现文件
        ├── 理解实现逻辑是否正确覆盖 TC 中的场景
        ├── 检查测试代码是否真正验证了 TC 描述的行为
        └── 🔴 不能只看测试是否通过，要看测试是否验证了正确的东西

Step 3: TC 逐条验证（输出 TC 验证报告）
        ├── 对每条 TC，检查两个维度：
        │   ├── 实现覆盖：代码逻辑是否处理了该场景
        │   └── 测试覆盖：测试代码是否验证了该场景的预期行为
        └── 标注代码位置 + 验证方式

Step 4: TDD 规范检查（🔴 单源 v7.3.10+P0-63 → [standards/tdd.md §三 自检清单](../standards/tdd.md) + [§四 反模式](../standards/tdd.md)）
        ├── 测试先于实现（检查 git 提交顺序，如可获取）
        ├── 测试命名规范
        ├── 断言质量（不能只有 toBeTruthy / 必须 assert 具体值）
        └── 边界条件覆盖

Step 4.5: 🔴 PRD AC 逐条直接对账（v7.3.10+P0-68 新增 · 不通过 TC 中转）
        > 实证触发：F059-StartupPreloader Ship 后发现 5 个 PRD 埋点全缺 + 7 个关键路径无日志，因为 TC 没覆盖非功能性 AC，QA Review 在 TC 中转模式下漏检。
        > 与 verify-ac.py 区别：verify-ac.py 在 Dev 出口验 AC.id ↔ TC.covers_ac 绑定关系（ID 层）；本 Step 在 Review 验 AC ↔ 代码（语义层）。两层互补，缺一不可。
        ├── Step 4.5.1: 读 PRD §acceptance_criteria 全表（含 must_have / should_have / 非功能性条款）
        ├── Step 4.5.2: 对每条 AC，**直接 grep 代码核对实现存在**（不通过 TC 中转）：
        │   ├── 功能性 AC（如「点击 X 触发 Y」）→ grep 业务代码定位实现点
        │   ├── 埋点 AC（如「上报 preload_browser_start」）→ grep `SReporter.report*\|reportEvent.*` + 事件名
        │   ├── 日志 AC（如「关键路径打 INFO 日志」）→ grep `SLogger.i\|Log.i\|logger.info` 在 PRD 声明的关键路径
        │   ├── 配置 AC（如「读 app_config.X」）→ grep AppConfigManager / config 读取点
        │   ├── 性能 AC（如「P95 < 200ms」）→ 检查 metrics 上报点 + 性能埋点
        │   ├── 安全 AC（如「MD5 + 包名校验」）→ grep 校验调用 + 失败处理路径
        │   └── 监控 AC（如「失败必告警」）→ grep ERROR 日志 / 告警上报点
        ├── Step 4.5.3: 任一 AC 在代码中找不到对应实现点 → ❌ BLOCKER（不允许进 Test Stage）
        ├── Step 4.5.4: 输出对账报告（5 列表格 · 见下方模板）
        └── Step 4.5.5: 报告中标注被 grep 的关键字 + 命中位置（file:line）便于复核

        🔴 **报告模板**（必填）：
        ```
        | AC ID | 类别 | PRD 声明（摘要）| 代码 grep 关键字 | 命中位置 | 状态 |
        |-------|------|----------------|------------------|---------|------|
        | AC-1  | 功能 | 点击按钮触发 X  | onClick.*X       | foo.java:123 | ✅ |
        | AC-7  | 埋点 | 上报 preload_browser_start | SReporter.*preload_browser_start | **0 处** | ❌ BLOCKER |
        | AC-12 | 日志 | drainQueue 起点打 INFO | SLogger.i.*drainQueue | **0 处** | ❌ BLOCKER |
        ```

Step 5: 集成测试覆盖检查（🔴 本 Feature 的核心场景是否有集成测试）
        ├── 读取 TC.md 中标注为后端 API / 数据库相关的用例
        ├── 检查集成测试文件中是否覆盖了这些场景
        ├── 特别关注：本 Feature 新增的配置开关、环境变量、特殊模式是否在集成测试中验证
        ├── 缺失的集成测试场景 → 列入「待补充集成测试」清单，RD 必须补充后才能进入集成测试阶段
        └── 📎 QA 代码审查的职责不止是验证已有测试，还要发现测试覆盖盲区

Step 5.5: 用户行为边界检查（有 UI 交互的功能必查）
        ├── 快速连续操作：按钮是否有防重复提交？表单连点是否安全？
        ├── 中途离开：表单填写一半刷新/后退，数据是否丢失？草稿是否保存？
        ├── 慢速网络：请求超时时 UI 是否有 loading/错误提示？是否有重试入口？
        ├── 浏览器后退：状态依赖路由的页面，后退后状态是否一致？
        ├── 并发编辑：多 tab 同时操作同一资源，是否有冲突检测/提示？
        └── 报告格式：
            | 检查项 | 是否涉及 | 结果 | 说明 |
            |--------|----------|------|------|
            | 防重复提交 | ✅/N/A | ✅/❌ | [具体] |
            无 UI 交互时输出：⏭️ 本功能无 UI 交互，跳过用户行为边界检查

Step 5.7: 设计-代码一致性检查（有 UI 交互 且 UI.md 存在时必查）
        ├── 对照 UI.md（UI Design Stage DONE 版本）逐项核对：
        │   ├── UI 元素：按钮 / 弹窗 / 输入 / 列表项 / 导航等是否齐全
        │   ├── 交互流程：点击响应 / 跳转 / 表单提交 / 反馈是否一致
        │   ├── 边界状态：空态 / 错误态 / Loading / 禁用态是否实现
        │   └── 文案/标签：关键文案与 UI.md 是否一致（允许微调，需在说明中标注）
        ├── 粒度定义（🟡 结构 + 交互层面，不做像素级比对）：
        │   └── 像素级视觉回归留给 Browser E2E Stage
        ├── 偏差分级：
        │   ├── 🔴 主流程 UI 元素缺失 / 关键交互走样 → QUALITY_ISSUE，打回 Dev
        │   ├── 🟡 非主流程偏差 / 次要状态缺失 → concerns，不阻塞
        │   └── 🟢 仅文案或视觉微调差异 → 记录到说明，不计入问题
        ├── UI.md 本身问题（设计不可实现 / 自相矛盾）→ 类别标「设计文档问题」，⏸️ 交 Designer 确认
        └── 无 UI.md 或纯后端功能：输出 ⏭️ 本功能无 UI.md 或无 UI 交互，跳过本步

Step 6: 架构文档一致性检查
        ├── 代码结构是否与 ARCHITECTURE.md 描述一致
        └── 新增模块是否在架构文档中有记录

Step 7: 输出审查报告
```

### 3. 执行约束

```
🔴 强制要求：
├── 必须逐文件阅读代码变更，不能只看测试报告或覆盖率
├── 必须对照 TC 逐条验证，每条 TC 都要有明确的验证结论
├── 实现覆盖和测试覆盖必须分别检查（可能实现了但没测试，或测试了但实现有误）
├── 发现问题必须标注类别（实现缺陷 / 测试缺陷 / TC 问题 / 集成测试缺口 / 设计一致性偏差 / 设计文档问题）
├── 涉及 UI 的功能，必须对照 UI.md 验证实现一致性（UI.md 不存在则跳过并在报告中标注）
└── TC 验证率必须 100% 才能通过（每条 TC 都需要 ✅）

❌ 禁止：
├── 跳过代码阅读，仅凭测试通过率判定
├── 不对照 TC 逐条验证，只做笼统检查
├── 架构师方案评审 通过就默认代码无问题
├── 自行修改实现代码（发现问题记录到报告，交 RD 修复）
├── 自行修改 PRD/UI/TC 等上游文档
└── 自行决定 TC 不合理而跳过验证（记录为 TC 问题，交用户确认）
```

### 4. QA Review 输出模板

```
📋 QA 代码审查报告
├── 功能：F{编号}-{功能名}
│
├── 1️⃣ TC 逐条验证：
│   | TC 编号 | 场景描述 | 实现覆盖 | 测试覆盖 | 代码位置 | 说明 |
│   |---------|----------|----------|----------|----------|------|
│   | TC-001  | xxx      | ✅/❌   | ✅/❌   | src/xxx  | [验证方式] |
│   | TC-002  | xxx      | ✅/❌   | ✅/❌   | src/xxx  | [验证方式] |
│
│   TC 验证率: X/Y (XX%)
│   ├── 实现覆盖率: X/Y
│   └── 测试覆盖率: X/Y
│
├── 2️⃣ TDD 规范检查：
│   | 检查项 | 结果 | 说明 |
│   |--------|------|------|
│   | 测试先于实现 | ✅/❌/N/A | xxx |
│   | 测试命名规范 | ✅/❌ | xxx |
│   | 断言质量 | ✅/❌ | xxx |
│   | 边界条件覆盖 | ✅/❌ | xxx |
│
├── 3️⃣ 集成测试覆盖检查：
│   | TC 编号 | 场景 | 单元测试 | 集成测试 | 缺口 |
│   |---------|------|----------|----------|------|
│   | TC-001  | xxx  | ✅       | ✅       | - |
│   | TC-003  | xxx  | ✅       | ❌       | 需补充：[具体场景] |
│
│   集成测试覆盖：X/Y 场景已覆盖
│   待补充集成测试：[列出缺失场景，RD 必须补充后才能进入集成测试阶段]
│
├── 3️⃣.5 设计-代码一致性（有 UI 时填写；无 UI 时输出 ⏭️ 跳过）：
│   | UI 元素 / 交互 | 设计描述（UI.md 出处） | 实现情况 | 代码位置 | 结论 |
│   |---------------|-----------------------|----------|----------|------|
│   | 提交按钮防重   | UI.md §2.3 点击后置 disabled | ✅/❌/⚠️ | src/xxx:L42 | [说明] |
│   | 空态文案       | UI.md §3.1 "暂无数据"        | ✅/⚠️   | src/xxx    | [实际:"没有数据"] |
│
│   一致性覆盖：X/Y 项
│   ├── 🔴 主流程偏差：N 项（列入 QUALITY_ISSUE）
│   ├── 🟡 非主流程偏差：N 项（列入 concerns）
│   ├── 🟢 文案/微调差异：N 项（仅记录）
│   └── UI.md 文档问题：N 项（⏸️ Designer 确认）
│
├── 4️⃣ 架构文档一致性：✅ 一致 / ⚠️ 有差异（列出）
│
├── 5️⃣ 问题清单（如有）：
│   | # | 类别 | TC 编号 | 问题描述 | 建议处理 |
│   |---|------|---------|----------|----------|
│   | 1 | 实现缺陷/测试缺陷/TC问题/集成测试缺口/设计一致性偏差/设计文档问题 | TC-xxx | [描述] | RD 修复/RD 补测试/⏸️用户确认 |
│
├── 审查结论：✅ 通过 / ❌ 需修改
└── 如需修改：问题分类汇总
    ├── 实现缺陷 X 项 → RD 修复
    ├── 测试缺陷 X 项 → RD 补充测试
    ├── 集成测试缺口 X 项 → RD 补充集成测试
    ├── 设计一致性偏差 X 项 → RD 修复（主流程）/ concerns（非主流程）
    ├── 设计文档问题 X 项 → ⏸️ Designer 确认
    └── TC 问题 X 项 → ⏸️ 用户确认
```

### 5. 结果处理

```
✅ 审查通过（TC 验证率 100% + TDD 规范通过 + 无问题）：
└── PMO 汇总三视角 → REVIEW.md → 进入 Test Stage

❌ 审查未通过：
├── 实现/测试缺陷 → RD 修复 → QA 重新审查
│   ├── 🔴 重新审查范围：全量重审（重新执行完整 7 步流程）
│   │   └── 原因：RD 修复可能引入新问题，增量审查会遗漏副作用
│   └── 最多 3 轮，3 轮未通过 → ⏸️ 升级给用户决定
└── TC 本身问题 → ⏸️ 用户确认处理方式
```

---

## 外部模型代码 Review 任务规范

> 外部视角通过对应外部模型 CLI 独立 spawn fresh session 执行（按 state.external_cross_review.model 选择 codex CLI 或 claude CLI；详见 §Process Contract §4 外部模型独立审查）。本节为外部视角的 prompt 模板（适用于所有外部模型实例）。

### 输入（PMO 在 dispatch 中提供）

```
├── {Feature}/PRD.md
├── {Feature}/TECH.md
├── {Feature}/TC.md
├── Dev Stage 代码 diff
├── {SKILL_ROOT}/standards/common.md + backend.md/frontend.md
└── 🔴 严禁读：review-arch.md / review-qa.md（独立性硬约束）
```

### 审查维度

```
├── 逻辑正确性（边界 / 异常路径 / 错误处理）
├── 安全漏洞（注入 / XSS / 越权 / 敏感数据）
├── 第三方依赖真实性（🔴 异质外部模型跨模型优势点）
│   └── 包名是否真实存在、版本是否有已知 CVE
├── 并发安全（TOCTOU / 死锁 / 幂等性）
└── 代码质量（可读性 / 可维护性 / 冗余）
```

### 输出

```
review-external.md，frontmatter：
---
perspective: external-{model}        # external-codex | external-claude
executor: codex-cli-subprocess | codex-cli-subagent | claude-cli-subprocess
generated_at: ISO8601
model: codex-{version} | claude-sonnet-{version}    # 实际使用的外部模型版本
files_read:
  - ...
findings:
  - severity: high|medium|low|info
    file: ...
    line: ...
    message: ...
    suggestion: ...
---
```

---

## 执行报告模板

```
📋 Review Stage 执行报告（F{编号}-{功能名}）
============================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / NEEDS_FIX / FAILED}
├── 执行方式：架构师{主对话/Subagent} + QA {主对话/Subagent} + 外部模型{model}（{对应 CLI spawn 方式}）
├── 合并问题数：🔴 {x} / 🟡 {y} / 🟢 {z}
└── 落盘：{Feature}/REVIEW.md

## 三视角产出
| 视角 | 文件 | generated_at | files_read | findings |
|------|------|-------------|------------|----------|
| 架构师 | review-arch.md | ... | 5 | 🔴0 🟡2 🟢1 |
| QA | review-qa.md | ... | 4 | 🔴0 🟡1 🟢0 |
| 外部（{model}）| review-external.md | ... | 3 | 🔴0 🟡0 🟢2 |

## Output Contract 校验
├── 三份报告存在：✅
├── frontmatter 可解析：✅
├── generated_at 互不相同：✅
├── 报告互不引用：✅（grep 校验）
└── 架构师批评 ≥3 条：✅（或显式说明）

## 修复记录（如有）
| 轮次 | 修复内容 | 重跑范围 | 结果 |
|------|----------|----------|------|

## ARCHITECTURE.md 更新
{已更新 / 无需更新 / 待更新}
```
