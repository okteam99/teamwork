# Changelog

## v7.3.10 + P0-23（当前）

> v7.3.10+P0-23 Prompt Cache 友好改造（R1+R2+R3 子集）：teamwork 在 Claude Code / Codex 等宿主下跑时，宿主会自动做隐式 prompt caching（前缀命中则按 ~10% 价格 + ~5x 速度计费）；teamwork 原先的 prompt 组织方式未优化命中率——动态内容（日期/git/state.json）散落在稳定层中、Stage 入口 Read 顺序不固定、state.json 中段反复读写。按用户「针对 teamwork prompt caching 怎么改造」→ R1-R7 改造清单 → 用户「先落 R1+R2+R3」定稿：R1 动态内容后置（稳定层禁止字面值时间/git/身份/状态/环境）+ R2 Stage 入口 Read 顺序固定化（roles → templates → Feature 产物 → state.json 最后）+ R3 state.json 访问 ≤ 5 次/Stage（入口 1R + 出口 1R + 1W，中段 0，豁免仅评审循环/Subagent 整合/用户追加）。按 Anthropic 公开数据，Feature 输入 ≥50K token 场景命中率 20% → 80% 改造收益 ≈ 成本下降 2-3 倍。

### P0-23：Prompt Cache 友好 R1+R2+R3 落地

- 触发：用户「针对 teamwork prompt caching 怎么改造」→ 分层分析 L0/L1/L2/L3 + 3 大 cache miss 源（动态前缀/state.json 穿透/Read 顺序不固定）→ R1-R7 改造清单 → 用户「先落 R1+R2+R3」
- 理论依据：Anthropic 公开文档（Claude Code / Codex 宿主自动 prompt caching，前缀稳定 ≥ 1024 token + 字节一致时命中 → input token ~10% 计费 + ~5x 解码速度）
- 设计决策：
  - 只做 R1+R2+R3（显式高 ROI），R4-R7（多指令文件合并/subagent 组装/token 峰值瘦身/审计自动化）暂缓 → 避免过度改造
  - 不触碰 Anthropic API `cache_control` 显式 breakpoint（宿主接管层级，skill 不干预）
  - 红线数量保持 15 条（P0-23 的 3 条性能规则纳入 standards/prompt-cache.md，不升格红线——因违反不产生流程偏离，仅 cache miss，记入 state.concerns 即可）
- 处理（新建 1 文件 + 12 处改造）：
  - **A. 新建 `standards/prompt-cache.md`**（~170 行）：
    - 顶部红线定位 + 三条硬规则（R1/R2/R3）+ ROI 锚点（Feature 场景 50K token 20%→80% 改造 ≈ 2-3x 成本下降）
    - §一：4 层模型（L0 框架 / L1 项目 / L2 Feature / L3 动态）
    - §二 R1：7 类禁止字面值（时间/git/身份/状态/环境/会话）+ 错误 vs 正确表达表 + 允许承载位置（STATUS-LINE / PMO 输出块 / tool call 结果 / Subagent dispatch）
    - §三 R2：通用入口 Read 顺序（roles → templates → Feature 产物 → state.json 最后），每个 stage spec 补「入口 Read 顺序」段
    - §四 R3：state.json 访问次数表（入口 1R + 中段 0 + 出口 1R + 1W）+ 3 类豁免（评审循环 ≤3 轮 / Subagent 整合 / 用户追加）+ 量化上限 ≤5 次常规 / ≤8 次极端
    - §五：审计清单（grep 时间字面值 / stage spec 入口段存在 / PMO state.json 约束 / 中段禁写豁免标注）
    - §六：与 SKILL/RULES/common/INIT 的协作关系
    - §七：明确不覆盖（API-level cache_control / 跨 session 持久化 / subagent prompt 组装 / token 峰值瘦身）
  - **B. `SKILL.md` 文档表新增 prompt-cache.md 行**（责任人：PMO 每 Stage 入口引用约束）
  - **C. `RULES.md` 拆分文件索引新增 prompt-cache.md 行**（时机：PMO 每 Stage 入口 + 审计自查时）
  - **D. 10 个 stage spec 在 Input Contract 与 Process Contract 之间新增「入口 Read 顺序（v7.3.10+P0-23 固定）」段**：
    - plan / blueprint / blueprint-lite / ui-design / panorama-design / dev / review / test / browser-e2e / ship
    - 每段含 4 步固定顺序（角色 → 模板 → Feature 产物 → state.json 最后）+ R3 访问次数约束说明
    - 各 Stage 按特性标注豁免情形（Blueprint/Review 3 轮修复循环；Dev/Test 多次 Subagent dispatch 整合）
  - **E. `roles/pmo.md` §state.json 状态机维护规范 新增子段 state.json 访问模式约束**（紧接「Stage 结束必做」后，「state.json 与现有文件的关系」前）：
    - 4 行访问次数表（Stage 入口 1R / 中段 0 / Stage 出口 1R + 1W）
    - 3 类豁免条件（评审循环/Subagent 整合/用户追加）+ 量化上限 ≤5/≤8
    - 4 条反模式（每 Step 开头 Read / 每字段 Write / 保险再 Read / 中段兜底 Read）
  - **F. `INIT.md` CLAUDE.md 注入段审计**：逐行审计 L170-207 → 结果**清洁**（无日期/git/身份/state 值动态字面值）；版本号类型 `v7.3.10+P0-20/P0-15` 属稳定引用（符合 R1 §2.2）；保留不变
  - **G. 版本号 bump**：SKILL.md frontmatter 7.3.10+P0-22 → 7.3.10+P0-23；INIT.md L111 同步
- 影响：
  - 典型 Feature 场景（50K token 输入）命中率从 ~20% 提升到预期 ~70-80%（实测需生产数据验证）
  - 每 Stage 入口 Read 顺序统一 → 跨 Stage 切换时的前缀碎片化消除
  - state.json 中段禁读写 → 前缀稳定段结束点清晰化，下游 L3 动态内容明确后置
  - 红线条数保持 15 条（P0-23 未增红线，仅新增性能规则 standards/）
  - 无迁移成本（纯注解+约束，不改现有文件语义）
  - 改造范围：1 新文件 + 12 处编辑（3 索引文件 + 10 stage + 1 pmo + 1 version）
- 风险控制：
  - ⚠️ 违反 R3（中段读写 state.json）不触发红线机制 → 仅记 state.concerns（cache miss 自然反映在延迟/成本，不做硬阻塞）
  - ⚠️ 用户追加需求导致中段 Read/Write 豁免合规（必须先走 PMO 分析 + 用户确认）
  - ⚠️ Subagent dispatch 整合写 state.json 豁免必须每次 dispatch ≤ 1 次（否则打破 prompt 前缀一致性）
- 待观察 / 后续可能动作：
  - R4（多指令文件 CLAUDE.md + AGENTS.md 合并）— 若后续发现跨宿主启动命中率仍低，考虑两个文件合并
  - R5（subagent dispatch prompt 组装优化）— 等 dispatch.md 下次 revamp 时同步
  - R6（token 峰值瘦身）— 独立优化路径，与命中率无关
  - R7（审计自动化 - grep 规则跑 CI）— 待 skill-creator evals 建成后接入

---

## v7.3.10 + P0-22

> v7.3.10+P0-22 KNOWLEDGE.md 收敛 + retros 索引拆离：P0-21 落地混合 ADR 后，用户追问「KNOWLEDGE.md 还有必要么，是否需要精简」——审视当前模板确认：它把"架构决策（为什么选某方案）"明确写在🔧技术经验首项，与新的 ADR 体系直接抢地盘；把复盘索引和经验索引混塞；PMO 知识提取仅靠软提示易失活。按**方案 A**（收敛保留，非删除）落：KNOWLEDGE.md 收敛到 3 类纯"事实型"内容——⚠️ Gotchas（陷阱）/ 📋 Conventions（团队约定）/ 🎨 Preferences（用户偏好），明确"决策走 ADR / 复盘走 retros / 通用规范走 standards"的边界；复盘索引剥离到独立 `templates/retros-index.md`；PMO 新增📚 KNOWLEDGE 扫描段（与 ADR 扫描对称）+ 7 条硬触发时机表（从软提示升硬时机）；体量上限 300 行强制归档。

### P0-22：KNOWLEDGE.md 3 类收敛 + 硬触发时机 + 复盘索引剥离

- 触发：用户「我们的 KNOWLEDGE.md 还有必要么，是否需要精简下」→ 分析当前模板 3 大冗余问题 → 3 方案（A 收敛保留 / B 激进拆散 / C 最小改动）→ 用户「按 A 落地」
- 根因分析：
  - ADR 体系（P0-21）落地后，KNOWLEDGE.md 仍在🔧技术经验段收录"架构决策（为什么选某方案）"，和 ADR 直接抢领域 → 同一决策可能双写/漂移
  - KNOWLEDGE.md 同时承担「经验索引」+「复盘索引」两种不同时间语义的信息（主题复用 vs 时间回顾）→ 文件职责不纯
  - 当前 PMO 知识提取靠软提示（"功能完成时应基于以下维度总结"），没有硬时机约束 → 实际运行下绝大多数 Feature 完成时不会真提取 → 慢慢失活
  - 模板分类过细（8 大类 20+ 小项），AI 实际写入时犹豫"这条算技术还是流程"，同一条知识被写到多个位置
  - 无体量上限 → 长期容易变成"什么都往里塞"的垃圾桶
- 处理（模板重写 + 新模板 + PMO 专属段新增 + 3 处活引用 + 索引 2 处）：
  - **A. `templates/knowledge.md` 全文重写**：
    - 顶部新增「🔴 边界声明」表：明确架构决策→ADR / 通用规范→standards / 复盘→retros / 项目特有事实→本文件
    - 正文收敛到 3 类表格：⚠️ Gotchas (GO-NNN) / 📋 Conventions (CV-NNN) / 🎨 Preferences (PR-NNN)，每条都有 ID + 主题 + 来源 Feature + 时间
    - 按主题索引段（db / api / auth / frontend / UI / 交互 / ...）
    - 归档段（archived）：过期条目加 archived 标记保留备查
    - 🔴 体量上限 300 行（超出必选一种处理：升格 ADR / 子项目级分拆 / 归档）
    - 🔴 每条 ≤ 2 行（超出说明不够"事实"，可能是决策伪装）
    - ID 编号连续不复用（归档保留原 ID）
  - **B. `templates/retros-index.md` 新增**（~50 行）：复盘索引模板
    - 时间线段（最近在前）+ 按流程类型索引 + 偏差警报段（Stage 连续偏差 ≥ 3 次触发流程优化 proposal）
    - 位置：`{子项目}/docs/retros/INDEX.md`（和 `docs/adr/INDEX.md` 对称）
    - 维护约定：每次产单条复盘时同步 INDEX；体量上限 200 行
  - **C. `roles/pmo.md` 新增 §📚 KNOWLEDGE 扫描 + 写入时机**（紧接 ADR 扫描段后）：
    - 定位声明：3 类收录 + 4 类排除（决策/通用规范/复盘/临时笔记）
    - **A. preflight 扫描**（读操作）：4 步操作 + 输出格式 + 3 条硬规则（必出行 / ≤300 行 / 只列清单不下结论）
    - **B. 写入硬时机表**（7 条触发场景 × 类别 × 写入方 × PMO 提示措辞）：
      1. Bug 修复完成 → Gotcha → RD
      2. Dev Stage 调试 ≥30min 或 retry ≥2 → Gotcha → RD
      3. Review 发现 workaround → Gotcha → 架构师
      4. Review 发现自发约定 → Convention → 架构师
      5. Plan 用户强调跨 Feature 要求 → Convention → PM
      6. PM 验收用户明确偏好 → Preference → PM
      7. UI Design 用户选项陈述理由 → Preference → Designer
    - 🔴 PMO 显式提示即完成其职责；对应角色未写入 → state.concerns 记 skip_reason
    - 🟢 PMO 本身不直接写入 KNOWLEDGE（除流程型 Convention 外）
    - 反模式表 6 行（遗漏扫描行 / 读全文 / 决策写入 Gotcha / 通用规范写入 Convention / Bug 后漏提示 / 超体量继续追加）
  - **D. `FLOWS.md` 三种 PMO 初步分析格式**均新增「📚 相关项目事实（KNOWLEDGE）」行（单子项目 Feature / 工作区级 Feature Planning / 敏捷需求）
  - **E. 索引同步**：
    - `TEMPLATES.md`：knowledge.md 描述更新 + 新增 retros-index.md 行
    - `templates/README.md`：knowledge.md 描述 + 加载时机细化；新增 retros-index.md 行
- 版本号：
  - SKILL.md frontmatter：`7.3.10+P0-21` → `7.3.10+P0-22`
  - INIT.md Step 1.2-a 注释同步
- 设计要点：
  - **收敛而非删除**：KNOWLEDGE 有独立价值（项目特有事实 + 偏好）不能丢，但要和 ADR 清晰分工
  - **3 类硬隔离**：Gotchas / Conventions / Preferences 三段完全独立，有 ID 段 + 主题索引 → 不再纠结"这条写哪"
  - **决策 vs 事实的边界**：备选项 ≥ 2 → ADR；被动发现的客观约束 → KNOWLEDGE Gotcha；这是最关键的分流规则
  - **硬时机取代软提示**：7 条写入时机绑定到 Stage 完成报告，PMO 提示是硬职责；未提示 = 流程偏离
  - **体量上限 = 扫描上限**：300 行一口气读完，不用分页；超出必归档 → 文件不会膨胀
  - **复盘独立索引**：时间线语义（retros）和主题语义（KNOWLEDGE）彻底分离，和 ADR-INDEX 形成"3 套索引"对称结构
  - **零新红线**：总红线数仍 15 条；所有约束落在 PMO 专属规范 + 模板硬规则里
  - **与 ADR 的协作**：ADR 记"为什么选了这个"，KNOWLEDGE Gotcha 记"选了之后踩了什么坑"——两者互补
- 保留未做（后续可能 P0/P1）：
  - KNOWLEDGE.md 自动校验脚本（verify-knowledge.py）：ID 连续性、主题索引完整性、体量上限 → 当前手工
  - 跨项目 KNOWLEDGE 聚合视图：多子项目模式下全局概览，当前各子项目独立维护
  - 归档条目的定期回顾机制：archived 条目是否真的不适用，需要多版本验证
  - Bug 修复流程 Stage spec 是否在完成报告明确要求"PMO 提示写 Gotcha"的声明格式 → 当前靠 roles/pmo.md 硬时机表约束，未在 bug-stage 单独落硬规则
  - Review Stage spec 是否在 findings 分类里新增"trigger_knowledge_write"标记 → 当前靠架构师读 roles/pmo.md 硬时机表自觉执行

## v7.3.10 + P0-21

> v7.3.10+P0-21 混合 ADR（Architecture Decision Record）体系：用户追问"TECH.md 接近但不是 ADR 语义（Context / Decision Drivers / Alternatives ≥ 2 / Consequences），teamwork 需要补充完善么"——分析后确认：TECH.md 混合了"怎么做（实现计划）"和"为什么这么选（决策记录）"两类信息，当跨 Feature 引用决策时（"用户系统当初选 PostgreSQL 是为了什么"）没有稳定引用点；但强制每 Feature 产 ADR 会把轻量流程拖垮。按**方案 C 混合 ADR**落：ADR 作为可选产物，由架构师在 Blueprint Stage 用"3 问触发器"判断是否抽取（影响未来 ≥1 Feature / 反悔成本高 / 多合理方案非显然 —— 三问全 yes 才产）。TECH.md 保持不变是实现计划的主体，决策则被抽离到独立 `{子项目}/docs/adr/NNNN-{slug}.md`，PMO 初步分析阶段扫描 INDEX.md 让未来 Feature 自动感知既有决策约束——这是 ADR 对 AI 自引用最关键的价值。

### P0-21：混合 ADR 体系（opt-in 决策记录 + 3 问触发器 + PMO 索引扫描）

- 触发：用户「文档即代码（ADR / RFC）：TECH.md 接近但不是 ADR 语义（ADR 要求决策记录 + 备选项 + 后果）这个 teamwork 需要补充完善么」→ 评估三方案 A（TECH.md 内嵌）/ B（全面 ADR）/ C（混合 opt-in）→ 用户「按方案 C 落」
- 根因分析：
  - TECH.md 实际承担两类信息：「实现计划」（文件清单 + 改动要点 + 测试策略）+「技术决策」（为什么选 A 不选 B）——两者耦合导致跨 Feature 引用决策时没有稳定锚点
  - 未来 Feature 的 AI 想知道"本项目为什么当初选 PostgreSQL"只能全文搜索所有历史 TECH.md，没有索引也没有按主题聚合
  - 全面强制 ADR（方案 B）会让小 Feature 额外付 ~50-100 行 ADR 成本 → 流程不可持续；完全不加（方案 A）无法解决跨 Feature 决策引用问题
  - 合理的解法：opt-in + 触发器 + 索引聚合 → 只有真正影响未来 / 反悔成本高 / 多方案非显然的决策才升格 ADR
- 处理（2 个新模板 + 4 处活引用 + 1 条工作流）：
  - **A. 新增 `templates/adr.md`**（~120 行）：完整 ADR 模板
    - frontmatter 7 字段：`id` / `title` / `status`(proposed|accepted|deprecated|superseded-by-ADR-NNNN) / `date` / `tags[]` / `triggered_by`(触发 Feature) / `supersedes[]`
    - 正文 7 段：背景 / 决策驱动因素 / 备选项（≥ 2） / 决策 / 后果（✅ 正面 / ⚠️ 负面 / 🔗 长期 / ❓ 未解决）/ 相关 / 修订历史
    - 硬规则：ID 连续编号永不复用、备选项 < 2 走 TECH.md 不走 ADR、每次变更同步 INDEX.md、superseded 时双向关联、体量 50-150 行
  - **B. 新增 `templates/adr-index.md`**（~65 行）：ADR 索引模板
    - 三段：活跃决策（Accepted） / 提案中（Proposed） / 已废弃（Deprecated / Superseded）
    - 按主题索引：db / api / auth / frontend / backend / deploy / observability / security
    - 位置：`{子项目}/docs/adr/INDEX.md`（每子项目一份）
    - 体量上限 200 行，超出说明需分片
  - **C. `stages/blueprint-stage.md` §架构师方案评审**（Step 4 增子步 + Step 6 新增 + 硬规则 +2 + Output Contract +2 行 + 判据 +4 项）：
    - **Step 4.1 ADR 抽取判断**：架构师必须对本 Feature 每条技术决策应用"3 问触发器"——
      1. 这个决策会影响 ≥ 1 个未来 Feature 吗？
      2. 反悔成本很高吗（需要大规模改动）？
      3. 存在多个合理方案，选哪个不是显然的吗？
      - 三问全 yes → 抽取为独立 ADR；任一 no → 决策留在 TECH.md 即可
      - 🔴 判断本身（包括"不产 ADR 的理由"）必须在 TECH-REVIEW.md 留痕
    - **Step 6 ADR 抽取流程**（Step 5 Codex 之后）：前置（TECH-REVIEW 已记 ADR 判断）/ 架构师 4 步职责（分配 ID / 按模板创建文件 / 填 frontmatter + 正文 / 更新 INDEX.md）/ PMO 流程整合（列摘要 + ⏸️ 用户确认→ status proposed→accepted + 多轮讨论不受 ≤3 轮限制）/ 产出清单 / 体量控制 / 🔴 TECH.md 去重（决策 rationale 迁移后 TECH.md 只留 ADR-ID 引用）
    - **过程硬规则 +2**：🔴 ADR 抽取判断不可跳过（跳过 = 流程偏离） + 🔴 ADR 格式合规（严格按 adr.md 模板、备选项 ≥ 2、同步 INDEX.md）
    - **Output Contract +2 行**：`docs/adr/NNNN-{slug}.md`（🟡 仅触发时必需）+ `docs/adr/INDEX.md`（🟡 首次产 ADR 时创建/每次变更时更新）
    - **机器可校验条件 +5 项**（触发时生效）：frontmatter 5 字段全非空、备选项 ≥ 2、体量 50-150 行、INDEX.md 已同步、文件名 NNNN 连续不复用
    - **Done 判据 +1**：ADR 触发时 status=accepted + INDEX.md 同步 + TECH.md 去重
  - **D. `roles/pmo.md` §📜 ADR 索引扫描**（新段，紧接 Codex 决策段后）：
    - 触发：PMO 初步分析任何 Feature / 敏捷需求 / Feature Planning 时必须扫描
    - 目的：让 PMO 在需求分析阶段就提醒"本 Feature 受哪些历史决策约束"——这是 ADR 对 AI 自引用最关键的价值（不扫描 = AI 重复发明或违反既有决策）
    - 4 步操作：定位 INDEX.md → 读前 200 行 → 按主题 + 涉及模块交叉扫描活跃决策 → 注入初步分析输出
    - 硬规则 4 条：必须显式输出「📜 相关 ADR」行（即使为空）+ 只读 INDEX.md 不读单 ADR 全文 + PMO 不做决策抽取判断（留给架构师）+ 无 ADR 记录时显式声明
    - 反模式表 +3 行：遗漏行 / 读全部 ADR / 替架构师下结论
  - **E. `FLOWS.md` §PMO 初步分析输出格式**：三种格式（单子项目 Feature / 工作区级 Feature Planning / 敏捷需求）均新增「📜 相关 ADR」行；§PMO 初步分析流程步骤描述 Blueprint Stage 改述为"含 💡 ADR 3 问触发器判断"
- 版本号：
  - SKILL.md frontmatter：`7.3.10+P0-20-B` → `7.3.10+P0-21`
  - INIT.md Step 1.2-a 注释同步
- 设计要点：
  - **opt-in 而非强制**：3 问触发器把 ADR 抽取成本精确定位到"跨 Feature 影响 + 反悔成本高 + 非显然"三者同时满足的决策——绝大多数 Feature 一个 ADR 都不用产，流程开销几乎为零
  - **零新红线**：保持总红线数 15 条不变；ADR 约束全部落在 Blueprint Stage 规范 + PMO 专属规范里（而不是升格为全局红线）
  - **PMO 只扫描不判断**：PMO 负责"历史扫描 + 注入"，架构师负责"抽取判断"——两个职责清晰分工，避免 PMO 越权替架构师决策
  - **INDEX.md 体量可控**：200 行上限 + 只读索引不读全文 → 即使项目积累 100 个 ADR，PMO 初步分析阶段的 token 开销也可控
  - **AI 自引用价值最大化**：通过「主题索引 + PMO 每次扫描」让未来 AI Feature 自动感知既有决策约束——这是 ADR 对 LLM 自主开发最关键的贡献
  - **与 TECH.md 去重**：决策 rationale + 备选项 + 后果 → 迁移到 ADR；TECH.md 只留 ADR-ID 引用一句话——避免双份真相
  - **备选项 ≥ 2 的硬门槛**：单方案走 TECH.md 不走 ADR，防止 ADR 被用作"凡决策必记"的形式主义产物
- 保留未做（后续可能 P0/P1）：
  - ADR 状态流转（superseded-by-* 双向关联）的自动化校验脚本：当前靠架构师手工，未来可加 python3 verify-adr.py
  - ADR 搜索/聚合 CLI：INDEX.md 体量够用时搜索基本靠人眼，未来项目 ADR 数量大时再引入
  - Micro 流程是否扫描 ADR：Micro 场景改动极小、准入条件已排除架构变更，当前不加扫描；若未来发现 Micro 漂到边缘决策再补
  - RFC（Request for Comments）体系：ADR 记录「已做的决策」，RFC 用于「待讨论的提案」——当前 TEAMWORK 不引入 RFC，团队内部讨论走 PRD / PL-PM 讨论已足够；未来多 AI 协作场景可能需要

## v7.3.10 + P0-20-B

> v7.3.10+P0-20-B 反漂移双补丁：P0-20 把 Micro 流程里"谁写代码"的语义统一为"主对话内 PMO→RD 身份切换"，但用户追问"身份切换语义模型现在能理解吗"——深究后确认：LLM 可以 parse 这个短语，但"身份切换"不是原子操作（没有进程/状态切换、没有 context 隔离），让切换真正生效靠的是 P0-16 补丁留下的四个仪式（切换前必读 + cite + 改后自查 + STATUS-LINE 显示角色）。仪式全在改动**前后**，改动**过程中**存在两个漂移口：(1) 跨多 turn 悄悄漂回 PMO 口吻；(2) 用户中途追加改动时 RD 身份顺手接单导致身份蠕变。本次补两条轻量规则堵漏。

### P0-20-B：反漂移双补丁（第一人称锚点 + 追加改动回退规则）

- 触发：用户「身份切换语义代表什么现在模型能理解么」→ 回答"语义能懂但靠仪式落地"+ 识别两个漂移口 → 用户"按建议"全做
- 根因分析：
  - 身份切换在 LLM 上是 prompt-level convention，不是 runtime state 切换 → 仅靠"称呼改变"不足以持续约束行为
  - P0-20 保留的 P0-16 四仪式（必读 + cite + 自查 + 状态行）全是**前后**锚点，没有**过程中**锚点
  - 漂移场景 1：Micro 改动跨多 turn 时，模型可能在中间某轮悄悄恢复 PMO 口吻（产出不一定错，但审计痕迹乱）
  - 漂移场景 2：用户中途说"顺便再改一下 X"，RD 身份顺手接单 → 没有 PMO 的 Micro 准入重评 → 身份蠕变、Micro 越扩越大
- 处理（两条规则 + 三处活引用 + 事后审计补两项）：
  - **A. 第一人称锚点**：身份切换后阶段摘要**首句必须以「作为 RD，……」开头**。LLM 在开头强制自称特定角色时，后续 token 生成会显著向该角色的语言分布靠拢——这是反漂移的最小开销锚。
  - **B. 追加改动回退规则**：RD 身份执行过程中若用户追加新改动请求 → 必须跳回 PMO 身份重新做 Micro 准入：
    - 通过 5 项准入 + 仍在白名单内 → PMO 输出增量分析 + ⏸️ 等用户确认 → 再切回 RD 执行
    - 越出白名单 → PMO 输出升级原因 → ⏸️ 用户确认走敏捷或 Feature
    - 🔴 禁止在 RD 身份下直接接收新需求
  - 活引用三处（A+B 同步写入）：
    - **FLOWS.md §六 Micro 流程规则 L954-965**：强制规则块头部更新版本标记到 `v7.3.10+P0-20-B 补两条反漂移规则`；在 cite 规则之后插入 🔴 第一人称锚点 + 🔴 追加改动回退规则（带 3 项子流程分支）两条硬规则
    - **FLOWS.md §六 Micro 事后审计**：新增 2 项 checklist——"身份切换第一人称锚点是否写入首句" + "执行中是否发生追加改动、若是是否跳回 PMO 准入"
    - **roles/pmo.md L5 Micro 头部段**：在 P0-16 必读子句后追加"🔴 第一人称锚点（P0-20-B）" + "🔴 追加改动回退规则（P0-20-B）"；完整闭环表述里加入「RD 改动（「作为 RD，…」锚句开头）」
    - **roles/pmo.md L1381-1382 反模式表**：新增两行——"RD 身份途中用户顺便追加改动 → 直接顺手改了" 和 "身份切换后用'我'/'PMO'/泛指" 对应 🔴 正确做法
    - **rules/flow-transitions.md Micro preamble**：在 P0-16 必读硬规则后追加一条 🔴 **反漂移双补丁（P0-20-B）** 复合规则（第一人称锚点 + 追加改动回退）
  - 版本号：SKILL.md frontmatter `7.3.10+P0-20` → `7.3.10+P0-20-B`；INIT.md Step 1.2-a 注释同步
- 设计要点：
  - **零新流程**：没有加 Stage、没有改流转图、没有新红线条目——全部在现有 Micro 规则块内补条款
  - **最低侵入**：第一人称锚点只是一句话约束，追加改动回退只是路由规则，不需要新的 state 字段
  - **可审计**：两条规则都能在事后审计 checklist 里直接检查（首句是否以"作为 RD，"开头 / 执行过程中有无追加改动且是否跳回 PMO）
  - **行为面提升**：堵了真实会发生的两个漂移口，特别是 B（"顺便"追加）——这是 Micro 蠕变到敏捷规模的最常见路径
- 保留未做（review 视角发现的次要点，留后续 P0）：
  - RD 身份在 Subagent dispatch 路径下是否需要等价的第一人称锚点 → 当前 subagent 隔离已经天然强化身份，不急着加
  - STATUS-LINE 是否应根据追加改动回退动态切换"角色：PMO" → 规则层已经够用，避免状态行过度工程化

## v7.3.10 + P0-20

> v7.3.10+P0-20 红线 #1 职责正交化：把"谁写代码"（维度 A）与"怎么组织流程"（维度 B）解耦——代码写权在所有流程下都归 RD，Micro 不再是红线 #1 的例外，而是省 Plan/Blueprint/UI/Review/Test Stage 的最短 RD 闭环（独立流程），允许主对话内 PMO→RD 身份切换由 RD 改动。红线 #1 因此从权限矩阵压缩为一句话；所有 Micro 相关描述统一为"身份切换"语义。

### P0-20：红线 #1 重构（职责正交化 + Micro 升格为独立流程）

- 触发：用户 insight「Micro 流程 PMO 可直接改 是不是改为切换 RD 身份来改，或者在主对话由 RD 来改，我感觉是一样的，核心目的是阅读过 RD 的开发规范」。
- 根因分析：
  - 旧红线 #1 把"谁写代码"和"怎么组织流程"两个维度混在一起，用"Micro 例外"打了个补丁 → 红线从一行变成权限矩阵，读者难记
  - Micro 流程的行为等价：PMO 直接改 / PMO 切 RD 身份 / 主对话由 RD 改，三种表述本质相同——核心约束是"改之前必读 RD 规范 + 自查"，不是"允许哪个角色 handle"
  - 正交化后：代码写权 = RD 本职（维度 A，无例外）；流程组织 = 完整 Stage 链 / Micro 最短链（维度 B，独立选择）
- 处理（一次性统一表述）：
  - **SKILL.md L62-67 红线 #1 改一句话版**：「代码 / 测试 / 构建配置的写操作 = RD 本职。必须由 RD 角色执行（主对话切换身份 / Subagent dispatch 均可），RD 必须先真实 Read 规范...改后按 rd.md 自查段执行自查。」附 📎 说明执行方式由 AI Plan 决定 / 流程选择由 Micro 准入决定；去掉"Micro 例外"子分支
  - **SKILL.md L123-135 Micro 简化规则块**：从"PMO 直接改代码"改成"主对话内 PMO→RD 身份切换，由 RD 直接改"，新增 📎 与红线 #1 的关系说明（"不是例外，是省 Stage 的独立流程"）
  - **SKILL.md L328** Micro 描述：→「✍️ 主对话 PMO→RD 身份切换（Read 规范 + cite）→ RD 改动 + 自查」
  - **INIT.md L185 CLAUDE.md 注入红线 #1**：同步简化，明确"PMO 本职写权仅限流程审计文件"+ "Micro 不是红线例外，是省 Stage 的最短 RD 闭环"
  - **FLOWS.md §六 Micro 流程**：preamble 从"PMO 不写代码在 Micro 不适用"改为"Micro = 省 Stage 的最短 RD 闭环...不是红线 #1 例外"；流程链路、自动流转、PMO 分析输出格式、Micro 规则块五个子段全部把"PMO 直接改 / PMO 切 RD 身份 / PMO 以 RD 身份直接"统一为"主对话 PMO→RD 身份切换 + RD 改动"
  - **RULES.md L531-554 Micro 自动流转段**：preamble 统一；执行分支表述从「主对话以 RD 身份直接改」→「主对话 PMO→RD 身份切换 → RD 改动」
  - **roles/pmo.md L5 顶部例外段**：重写为"Micro 流程身份切换"，明确"不是红线 #1 例外 → 省 Stage 的 RD 闭环"；身份切换必读不豁免保留
  - **roles/pmo.md L1379 反模式表**：「再由 PMO 主对话直接改」→「主对话内 PMO→RD 身份切换，由 RD 改动」
  - **STATUS-LINE.md L277-279 Micro 阶段行注释**：「PMO 主对话直接改」→「主对话 PMO→RD 身份切换，由 RD 改动」；阶段名「PMO 执行改动（Micro）」→「RD 执行改动（Micro）」
  - **standards/common.md L243 / L355 L1 预检注释**：同步身份切换语义 + 保留"身份切换必读不可豁免"
  - **rules/flow-transitions.md L167-179 Micro 表**：preamble + 表格 5 行全部统一为"PMO→RD 身份切换 → RD 执行改动"
  - **版本号**：SKILL.md frontmatter `7.3.10+P0-19-C` → `7.3.10+P0-20`；INIT.md Step 1.2-a 注释同步（触发 CLAUDE.md 自愈把新红线 #1 + 身份切换注释写入）
- 设计要点：
  - **正交化原则**：红线 #1 只管"谁写代码"（A），Micro/敏捷/Feature 只管"跑哪些 Stage"（B），两维度解耦。Micro 是独立流程 × 流程 B 的一个选项，不是红线 #1 的例外
  - **行为面零变化**：Micro 流程下"主对话 PMO→RD 身份切换"与旧描述"PMO 直接改"+"角色切换必读"语义等价；只是表述更干净
  - **红线条数不变**：仍为 15 条（#1 表述重写、不拆也不删）
  - **P0-16 补丁保留**：身份切换必读 `roles/rd.md` + `standards/common.md` + 按需 frontend/backend.md + 阶段摘要 cite 规范要点 + 改后自查—— P0-20 没有放松这条
- 用户价值：
  - 读者只需记一句「代码写权归 RD」—— 不再需要记 Micro 例外树
  - Micro 的本质（省 Stage）比之前更清晰，不用再纠结"PMO 为什么突然可以改代码"
  - 新增 RD 的职责边界更刚性——便于未来 Subagent 自动化 / 审计 / 权限隔离
- 未处理项：
  - OPTIMIZATION-PLAN.md / CHANGELOG.md 历史条目中的"PMO 可直接改"保留为历史记录，不回溯改写
  - SKILL.md 红线体系的更大结构性重排（整合多处子条款、抽出 RULES.md 的独立章节）留到后续 P0

## v7.3.10 + P0-19-C

> v7.3.10+P0-19-C 外部视角 fresh review 修补：P0-19-B 物理合并 agents/*.md → stages/*.md 后，通过独立 subagent 以零上下文视角复审 skill，发现 3 个 S1 阻塞项（红线计数不一致 + `roles/rd.md` 残留 arch-code-review Subagent 幽灵引用 + `agents/README.md` dispatch 示例未加 subagent-id 语义说明）+ 4 处连带活引用遗漏（standards/backend.md / templates/dispatch.md / rules/naming.md）。本次 patch 全部修复。

### P0-19-C：外部视角 review 的 S1 阻塞项 + 连带清理

- 触发：P0-19-B 合并完成后，用户要求「以全新视角 review 一下 teamwork skill」。通过独立 subagent（等同 fresh session 无历史上下文）走完 skill 通读，以外部视角校验 merge 质量。
- 根因分析：
  - P0-19-B merge 时只处理了 `agents/*.md` → `stages/*.md` 的**直接活引用**（16 处），漏了**二阶引用**：术语表 / 幽灵 Subagent 名 / subagent-id 语义说明
  - `INIT.md` 的红线计数（13 条）是从 v7.3.9 以前复制来的，v7.3 加了 #14 / #15 后一直没同步
  - `roles/rd.md` 的两阶段架构文档更新图和架构师 CR 完成后回调逻辑还在用「arch-code-review Subagent」的老措辞，P0-19-B 把它合并进 Review Stage 后该措辞就成了幽灵
  - `agents/README.md` dispatch 文件名示例保留了老 subagent-id，但没有明确「这些 id 是 dispatch 文件标签，不是规范源」—— 读者容易回读去找 `agents/rd-develop.md` 这种已删除的文件
- 处理（3 S1 + 4 连带）：
  - **S1-1 INIT.md 红线计数**：L184「13 条」→「15 条」；CLAUDE.md 注入模板补全红线 #14（AI Plan 模式）+ #15（流程确认）；Step 0 AUTO_MODE 强制保留项 L55「13 条绝对红线」→「15 条绝对红线」
  - **S1-2 roles/rd.md arch-code-review 幽灵 Subagent**：
    - L220「Code Review 后（arch-code-review Subagent 执行）」→「Review Stage 架构师 Code Review 后（规范见 stages/review-stage.md §架构师 CR 任务规范，执行方式见 agents/README.md §一）」
    - L212「Tech Review 后（arch-tech-review）」→「Blueprint Stage 架构师方案评审后（主对话角色，规范见 roles/rd.md §架构师方案评审）」
    - L376「自动进入架构师 Code Review（Subagent）→ 有 UI 则 UI 验收 → 🤖 QA 代码审查（Subagent）」→ 合并为「自动进入 Review Stage（架构师 CR + QA CR + 外部 Codex，执行方式见 agents/README.md §一，任务规范见 stages/review-stage.md）→ 有 UI 则 UI 验收」
    - L388 §架构师方案评审规范 角色定位「在独立 subagent 中对 RD 的技术方案进行全面审查」→ 去「独立 subagent 中」，加 📎 注脚说明「默认主对话，大方案由 AI Plan 决定是否 Subagent 隔离」
  - **S1-3 agents/README.md dispatch 示例加 subagent-id 语义块**：L286-290 下方新增 📎 三点说明（`{subagent-id}` 是 dispatch 文件标签 / 角色任务规范现在在 stages/*.md / dispatch 文件 Input files 应指向 stages/*.md 而非已删除的 agents/*.md）
  - **连带 #1 standards/backend.md L622-628 Schema 变更链条术语对照表**：列头「Agent 文件」→「规范位置」；各行指向改为：RD 开发→`stages/dev-stage.md §RD 角色任务规范`；架构师 Code Review→`stages/review-stage.md §架构师 CR 任务规范`；集成测试→`stages/test-stage.md §集成测试任务规范`；Blueprint 架构师方案评审→`roles/rd.md §架构师方案评审规范`
  - **连带 #2 templates/dispatch.md L9 命名规则行**：补充「subagent-id 是 dispatch 文件标签，沿用原有命名，角色任务规范已合并至 stages/*.md」
  - **连带 #3 rules/naming.md L44-46 subagent-id 列表**：补加一行「🔴 v7.3.10+P0-19-B 起角色任务规范已合并至 stages/*.md，subagent-id 仅作标签用」
  - **连带 #4 版本号 bump**：SKILL.md frontmatter `7.3.10+P0-19` → `7.3.10+P0-19-C`；INIT.md Step 1.2-a 注释同步（触发下次启动的 CLAUDE.md 漂移自愈校验，使红线 15 条写入 CLAUDE.md）
- 保留项（review 报告中的 S2/S3 **不处理**，留作后续 P0）：
  - S2-1 红线 #1 Micro exception 树过度工程化 —— 设计决策，需单独讨论
  - S2-2 dev-stage.md 7 自检维度「L108 + L352-392 各一份」—— 复核结论是**误报**（L108 是指针引用 `§4 RD 自查 7 维度`，只有 L352-392 真正列维度）
  - S2-3 RULES.md 1628 行 + 自带热路径索引 —— 需结构性拆分，单独 P0
  - S2-4 Key Context 6 类「写 -」的可 game 性 —— 设计决策
  - S2-5 Review/Test 3 轮封顶在 AUTO 下的浪费 —— 需 AUTO 模式分支调整
  - S3 polish（naming.md subagent-id 清单 / test-stage.md 内嵌 Python 模板 / {SKILL_ROOT} glossary 缺失 / 版本号程序化派生）—— 价值低、择机
- 收益：
  - 单一权威源一致性：`SKILL.md` 红线数 = `INIT.md` 红线数 = CLAUDE.md 注入红线数 = 15 条
  - 无幽灵 Subagent 引用：`roles/rd.md` 三处措辞 + `backend.md` 术语对照表 + `dispatch.md` + `naming.md` 全部指向合并后的 stages/*.md 权威位置
  - dispatch 示例消歧：`{subagent-id}` 的语义（文件标签 vs 规范源）首次被显式说明，避免读者回读已删除的 `agents/*.md`
- 兼容性（非破坏性）：
  - 无行为变更：只改文案 / 术语 / 链接，不触动任何 Stage 契约 / 流转 / 预检
  - 既存 dispatch_log/ 的 `002-rd-develop.md` / `003-arch-code-review.md` 等文件名继续有效（subagent-id 作为标签未变）
  - CLAUDE.md / AGENTS.md 会在下次 `/teamwork` 启动时自动漂移自愈（7.3.10+P0-19 → 7.3.10+P0-19-C 触发 full path），同步红线 15 条
- 相关 meta 观察（review 报告内）：**3 个月 19 个 P0 无一次删除**。下一个 P0 建议不再新增能力，聚焦消费：拆 RULES.md / 统一红线计数 / 红线 #1 Micro exception 二选一 / 全仓 grep 审计死引用。本次 P0-19-C 只修了审计类问题的子集。

---

## v7.3.10 + P0-19

> v7.3.10+P0-19 结构重构补丁：**Stage 升格为权威层级，Subagent 降格为执行选项**。物理合并 `agents/rd-develop.md` / `arch-code-review.md` / `qa-code-review.md` / `integration-test.md` / `api-e2e.md` 五个角色任务规范到对应 `stages/*.md` 的新增 §角色任务规范段；`agents/` 目录只保留 `README.md`（瘦身为纯 Subagent 执行协议：dispatch 文件协议 + Progress 可见性 + 主对话产物协议 + 通用执行约束 + Codex CLI 调用规范）。PMO 在 Plan 模式中按需选择执行方式（主对话 / Subagent / 混合），Subagent 不再作为"规范归档维度"存在。非破坏性：所有规范内容原样迁移，仅物理位置变动 + 章节编号微调。

### P0-19-B：Stage 升格 + agents/ 物理合并（stages/dev-stage.md + stages/review-stage.md + stages/test-stage.md + agents/README.md + 引用迁移）

- 触发：用户反馈「从合理的方向看，是不是弱化 subagent, 强调 stage, 增加各个 stage 中的规范文档，因为执行层面 pmo 可以按需选择 subagent」。承接 P0-19-A（subagent 降级为执行维度）的物理落地。
- 根因分析：
  - **Stage 是业务权威层级，Subagent 是执行手段**。v7.3.9+P0-14 dual-mode 化后，RD / 架构师 / QA 都可以主对话或 Subagent 执行，"按 agent 归档规范" 不再是自然语义分类
  - `agents/rd-develop.md` / `arch-code-review.md` 等文件命名暗示「这是 Subagent 专属规范」，导致主对话执行时 PMO 不确定是否仍需加载 → 双重权威源
  - Stage 级契约（Input/Process/Output）和 Stage 内角色任务规范分居两处（stages/ + agents/），PMO 派发时需要同时引用两个路径，心智负担 + 漏读风险
  - 把角色任务规范嵌入 stage 契约之后，**一个 stage 一个权威文件**，主对话 / Subagent 两种模式均从同一文件读取
- 处理（4 Stage 文件 + 1 README + 引用迁移）：
  - **§一 stages/dev-stage.md 合并 agents/rd-develop.md 全文**（+229 行）：新增 §RD 角色任务规范（1. 角色定位 Dual-Mode / 2. TDD 开发流程 / 3. UI 还原 / 4. RD 自查 7 维度）+ §RD 执行输出模板（执行摘要 / 自查报告 / 上游问题清单）
  - **§二 stages/review-stage.md 合并 agents/arch-code-review.md + agents/qa-code-review.md 全文**（+456 行）：新增 §架构师 CR 任务规范（角色定位 / Review 维度 / 执行流程 / 架构文档更新规则 / 输出模板 / 上游问题清单）+ §QA CR 任务规范（角色定位 / 执行流程 / 执行约束 / 输出模板 / 结果处理）+ §外部视角 Codex Review（codex CLI spawn prompt 模板）
  - **§三 stages/test-stage.md 合并 agents/integration-test.md + agents/api-e2e.md 全文**（+554 行）：新增 §集成测试任务规范（角色定位 / 执行流程 / 执行约束 / 证据要求 / 报告模板）+ §API E2E 任务规范（角色定位 / 触发条件 / 执行流程 / 脚本生成规范 / 脚本落盘 + e2e-registry 注册 / 报告模板 / 红线 / 降级处理 / 含完整 Python 脚本模板）
  - **§四 agents/README.md 瘦身**（734 → ~700 行，重组为 6 个顶级章节）：§一 执行方式与模型（偏好指引 + 模型推荐）/ §二 通用 Subagent 执行约束（文件读取 / 代码质量 / 异常处理 / 输出规范 / Progress Log / 危险命令红线）/ §三 Codex CLI 调用规范（宿主无关独立性 + 降级路径决策）/ §四 PMO 启动规范（含 Dispatch 文件协议 4.1-4.6 + 4.3 Progress 可见性协议 + 4.6 Subagent 返回状态分级处理）/ §五 主对话产物协议（命名约定 + frontmatter 硬规则 + Key Context 复用 + review-log.jsonl schema + 独立性保证）/ §六 目录结构索引（含 v7.3.10+P0-19-B 变更说明）
  - **§五 物理删除 5 个 agents/*.md 文件**：`agents/rd-develop.md` / `arch-code-review.md` / `qa-code-review.md` / `integration-test.md` / `api-e2e.md`；`agents/` 目录现仅保留 `README.md`
  - **§六 引用迁移**（16 处活引用 + 保留 CHANGELOG/OPTIMIZATION-PLAN 历史引用）：
    - `SKILL.md` 示例 Plan 模板 / 索引表：`agents/rd-develop.md` → `stages/dev-stage.md §RD 角色任务规范`；`agents/arch-code-review.md` → `stages/review-stage.md §架构师 CR 任务规范`；`agents/qa-code-review.md` → `stages/review-stage.md §QA CR 任务规范`
    - `RULES.md` Test Stage 子流程：`agents/integration-test.md` → `stages/test-stage.md §集成测试任务规范`；四-B 首段说明文字同步
    - `roles/rd.md`：架构师 CR 规范链接指向 stages/review-stage.md；内嵌审查项注释同步
    - `roles/qa.md`：集成测试 / API E2E / 集成测试规范链接全部指向 stages/test-stage.md
    - `templates/feature-state.json`：`loaded_role_specs[]` 从 `agents/rd-develop.md` 改为 `stages/dev-stage.md`
    - `templates/e2e-registry.md`：生成 Subagent 引用指向 `stages/test-stage.md §API E2E 任务规范`
    - `templates/dispatch.md`：Input files 模板第 2 项从 `agents/{subagent-id}.md` 改为 `stages/{stage}-stage.md §角色任务规范`；§四 4.3 / §五 Progress 章节编号同步为 §四 4.6 / §四 4.3
    - `codex-agents/tester.toml` / `reviewer.toml` / `rd-developer.toml`：developer_instructions Read 列表的第 3-4 项（旧 agents/*.md）合并为单行「stages/{stage}.md § ...（merged in v7.3.10+P0-19-B）」
  - **§七 agents/README.md 内部 §4.3 → §4.6 修正**：FAILED 兜底从旧 §4.3 改为新 §4.6（Subagent 返回状态分级处理表合并到完成后处理段）
  - **§八 SKILL.md frontmatter version bump**：`7.3.10+P0-18` → `7.3.10+P0-19`（触发下次启动的漂移自愈校验，使 CLAUDE.md / AGENTS.md 同步新目录结构）
- 保留项：
  - `CHANGELOG.md` / `OPTIMIZATION-PLAN.md` 历史引用 **不改写**（这些是历史事实记录，非当前规范）
  - `stages/*.md` 新增段顶部的合并注释（「本节整合 v7.3.10+P0-19-B 前的 agents/xxx.md 完整规范」）保留，为合并过程提供可追溯的 git-log 替代信息
- 收益：
  - Stage = 一个物理文件 = 一个权威：PMO 派发 / 切换角色 / 主对话执行时只需引用一个路径，心智负担 -50%
  - 规范与契约同居：Input Contract → 角色任务执行流程 → Output 模板串联在同一文件内，RD / 架构师 / QA 读时上下文天然连贯
  - Subagent 回归执行手段本位：`agents/README.md` 只负责"如何跨宿主派发 + 如何保证可观测性"，不再承担规范归档
  - Plan 模式更纯粹：approach=main-conversation/subagent/hybrid 只影响执行方式，不影响「读哪个规范文件」
- 兼容性（非破坏性）：
  - 所有规范内容原样迁移（无内容删减 / 强度调整），章节编号微调
  - Subagent dispatch 协议（dispatch 文件 / INDEX / Progress Log）完全不变
  - `.teamwork_localconfig.md` 的 `teamwork_version` 缓存机制（P0-17 引入）会在下次启动自动捕获 `7.3.10+P0-19`，触发 CLAUDE.md / AGENTS.md 校验一次（若发生漂移将被漂移自愈机制同步）
  - 用户侧无任何行为变更，`/teamwork` 命令 / 阶段流转 / 角色切换全部保持

## v7.3.10 + P0-18

> v7.3.10+P0-18 人机约定补丁：新增「ok = 按 💡 建议」全局快捷授权约定。用户在 ⏸️ 暂停点回复 `ok` / `OK` / `好` / `可以` / `行` / `嗯` / `按建议` / `按推荐` → PMO 自动映射为「当前暂停点全部 💡 推荐选项」执行（单决策等价于回复 💡 对应数字；多决策等价于所有决策都选 💡 推荐）。前置条件：暂停点至少有 1 个 💡（红线 #10 本就强制）；破坏性操作 / 无 💡 暂停点 / ok+补充语句 不适用本约定，仍按原规则处理。PMO 须输出一行 cite『✅ 已按 💡 建议处理：…』作为审计痕迹。非破坏性，仅加强用户体验。

### P0-18：ok = 按 💡 建议 约定（RULES.md + STATUS-LINE.md + SKILL.md + INIT.md）

- 触发：用户反馈"加一个指令说明，ok = 按建议"。观察：现有规范（RULES.md §模糊确认处理 L186）是『🔴 禁止把「好」「行」直接视为全面授权』，要求复述+二次确认；但实际交互中用户回复 ok 几乎 100% 是『按 💡 推荐走』意图，多余的二次确认增加摩擦。
- 根因分析：
  - 旧规则是为了防止"无上下文确认"——担心 ok 被误解为授权破坏性操作。但红线 #10 已经强制要求每个暂停点都输出 💡 推荐 + 📝 理由，ok 在"有 💡 推荐"的上下文中语义完全明确（= 按推荐走）
  - 多决策点（1A 2B）即使用户想『都按推荐』也要打 `1A 2A` 5 字符，ok 2 字符更省
  - 破坏性操作（force push / drop 表 / 删分支）属强制保留暂停点（见 flow-transitions.md），本就不应依赖模糊确认，单独拉保护线即可
- 处理（4 文件）：
  - **§一 RULES.md §模糊确认处理**（L177-186）：新增「🟢 ok = 按 💡 建议」段，含 7 字（ok/OK/Ok/好/可以/行/嗯/按建议/按推荐）识别清单 + 单决策/多决策映射规则 + 前置条件（必须有 💡）+ 强制 cite 输出格式 + 4 条边界保留（破坏性操作 / 无 💡 暂停点 / ok+补充语句 / 非暂停点）。原 L186 禁令改为边界语句，不再"全面禁止"
  - **§二 STATUS-LINE.md 用户回复处理表**（L313-321）：新增一行『🟢 ok/OK/好/可以/行/按建议』列映射到『按 💡 推荐全部选项执行 + cite』；原"模糊确认（≤5 字：好/可以/OK）"行改为『其他非 ok 家族模糊词』，避免与新规冲突
  - **§三 STATUS-LINE.md 意图识别表**（L332）：🟢 流程控制行扩展识别词表 + 处理方式改为『有 💡 → 按 💡 执行 + cite；无 💡 → 复述 + 二次确认』双分支
  - **§四 SKILL.md frontmatter version**: 7.3.10+P0-17 → 7.3.10+P0-18（触发下次启动的漂移自愈校验，使 CLAUDE.md/AGENTS.md 同步）
  - **§五 INIT.md Step 1.2-a 当前版本标注**同步更新为 7.3.10+P0-18
- 收益：
  - 人机交互摩擦降低：最常见的"采纳推荐"路径从 `1A 2A` → `ok`（2 字符），大幅降低打字成本
  - 决策意图明确化：PMO cite 一行『✅ 已按 💡 建议处理：…』让用户立刻看到 ok 被如何解读，防止误解
  - 规范语义一致：红线 #10（暂停点必须给 💡）与 ok 约定形成闭环——💡 不只是"参考建议"而是"ok 对应的具体选项"
  - 边界清晰：破坏性操作 / 非暂停点 / ok+补充语句 保留原路径，不会因 ok 约定扩大授权面
- 兼容性（非破坏性，仅放宽授权）：
  - 旧行为：用户回复 ok → PMO 复述+二次确认 → 用户再回复 1A 2A → 执行
  - 新行为：用户回复 ok → PMO cite『按 💡 建议处理』→ 直接执行。用户如不满意可中断，实际事故面与旧行为相当（PMO cite 相当于"软复述"）
  - 多决策点 "1A 2A" 显式回复仍然有效，ok 只是快捷方式
  - 破坏性操作 / 无 💡 暂停点：行为不变
  - 红线 #10（暂停点必须给 💡 + 📝）事实上成为 ok 约定的前置条件，变相加强红线 #10 的约束

## v7.3.10 + P0-17

> v7.3.10+P0-17 启动 token 优化：引入 **skill 版本缓存机制**，复用 `.teamwork_localconfig.md`（已 gitignore）记录 `teamwork_version` 字段。每次 `/teamwork` 启动时，先比对 SKILL.md frontmatter 的 `version` 与 localconfig 缓存值：一致（99%+ 场景）→ 跳过 CLAUDE.md/AGENTS.md Read + 逐字符 diff；不一致（skill 升级 / 首次 / 降级）→ 走全量校验 + 写回新版本号。估计节省 ~65-75% 启动阶段 token 消耗。漂移自愈（skill 升级后模板变动自动同步到 CLAUDE.md）能力保留；`/teamwork force-init` 作为逃生舱。非破坏性变更，向前兼容 v7.3.10+P0-16（localconfig 无 teamwork_version 字段 → 自动走全量 + 写入一次即进入稳态）。

### P0-17：skill 版本缓存优化 CLAUDE.md 校验（SKILL.md + templates/config.md + INIT.md）

- 触发：用户反馈"目前读 Init.md 的逻辑是什么，从 token 占用角度，是否有优化空间"；复盘发现 Step 1.2 每次启动都会 Read `{HOST_INSTRUCTION_FILE}`（CLAUDE.md / AGENTS.md）+ 做逐字符 diff，占用 ~2000-3500 token。用户反建议："我们是否在 .teamwork_localconfig.md 中加一个当前 teamwork 版本，如果和 skill.md 版本不一致的时候再去做 claude.md 和 agent.md 检查，更合理，复用本地的轻量级文件。"
- 根因分析：
  - CLAUDE.md/AGENTS.md 模板内容只在 skill 升级时才会变化；日常启动 99%+ 场景是"skill 未升级 → 模板未变 → diff 必然一致"的重复工作
  - 漂移自愈能力（skill 升级后模板变动同步到 CLAUDE.md）只需在升级时触发一次，不需要每次启动都跑
  - `.teamwork_localconfig.md` 已经存在（gitignore、每开发者各自维护）、是启动必读文件（已在 Step 2 加载），作为版本缓存载体成本为零
- 处理（3 文件）：
  - **§一 SKILL.md frontmatter 新增 `version: 7.3.10+P0-17` 字段**（单一权威版本号）：放在 frontmatter 使解析成本最低（Skill 加载时已可见）；后续每次 skill 升级需同步更新此字段
  - **§二 templates/config.md `.teamwork_localconfig.md` 模板新增「Skill 版本标记」段**：含 `teamwork_version:` 字段 + 详细注释说明机制 + "🔴 禁止手改（PMO 自动维护）"警示 + 逃生舱说明
  - **§三 INIT.md Step 1.2 重写为缓存-校验-回写模式**：
    - **Step 1.2-a**：读取 SKILL.md frontmatter `version` → `SKILL_VERSION`（缺失则降级全量+一次性 ⚠️ 提示）
    - **Step 1.2-b**：读取 `.teamwork_localconfig.md` `teamwork_version` → `LOCAL_VERSION`（文件/字段缺失/损坏均降级为 null）
    - **Step 1.2-c**：版本比对决定路径
      - ⚡ fast path（一致）：跳过 CLAUDE.md/AGENTS.md Read + diff，输出「⚡ CLAUDE.md 校验跳过（teamwork_version={VERSION} 命中缓存）」
      - 🔄 full path（不一致/null）：走原 P0-17 前的全量校验（文件不存在→创建、存在→逐字符 diff、漂移→替换），完成后回写 localconfig `teamwork_version: {SKILL_VERSION}`，输出「🔄 CLAUDE.md 已同步（{旧版本 or "缺失"} → {新版本}）」
      - 🚨 SKILL_VERSION=null：走全量 + 不回写 + ⚠️ 提示
  - **§四 INIT.md Step 0 加 `/teamwork force-init` 命令**（+ `/teamwork init --force` 别名）：用户怀疑 CLAUDE.md 被外部工具手改 / 缓存脏污时强制走全量校验
- 收益：
  - 启动 token 节省：fast path（99%+ 场景）跳过 ~2000-3500 token 的 CLAUDE.md Read + diff；估计节省 ~65-75% 启动阶段 token 消耗
  - 漂移自愈保留：skill 升级 → 版本不一致 → 一次性全量 diff 修复 CLAUDE.md → 写回新版本 → 此后跳过；机制语义与 P0-17 前完全等价
  - 复用本地轻量文件：localconfig 已 gitignore + 已是 Step 2 必读文件，无额外 I/O 成本
  - 多开发者一致性：localconfig 是每个开发者各自维护，版本缓存也是本地化（不产生跨机器 / 跨用户 git 冲突）
- 兼容性（非破坏性，向前兼容）：
  - P0-16 用户升级到 P0-17：首次启动 `LOCAL_VERSION=null` → 走全量校验 + 写回 → 此后稳态 fast path
  - localconfig 不存在：首次启动走全量校验 + 按 templates/config.md 创建最小版 localconfig（只填 scope:all + teamwork_version）
  - CLAUDE.md 被用户手改但 skill 未升级：版本仍命中 → 跳过校验 → 用户修改被保留（"respect user edits" 默认行为；若要强制恢复模板，用 `/teamwork force-init`）
  - 用户伪造 localconfig 的 teamwork_version（手改成最新值）：绕过校验的理论风险 → 靠模板注释"禁止手改"约束 + `/teamwork force-init` 兜底（此场景极少）
  - 无字段变更影响 state.json / agents/ spec
- 未变更：
  - P0-16 及之前所有行为语义（Micro 流程、红线 #1、Ship MR 模式等）完全不变
  - P0-11 AUTO_MODE / P0-13 Codex opt-in / P0-15 Ship Stage MR 流 等所有其他机制保持原样

## v7.3.10 + P0-16

> v7.3.10+P0-16 一致性修订：Micro 流程去「强制 RD Subagent」化 → 统一为「PMO 自行判断（主对话以 RD 身份直接改 / 升级 Plan 模式）」。核心实体（FLOWS.md §六、SKILL.md 红线 #1 Micro 例外）早已在 v7.3 放宽为 PMO 直接改，但 SKILL.md L320 / RULES.md L521-547 / rules/flow-transitions.md / STATUS-LINE.md / roles/pmo.md / standards/common.md 等 7 个文件仍残留「RD Subagent 执行 / 必须启 Subagent」旧描述，形成自相矛盾。P0-16 清理全部残留，使"PMO 自行判断执行方式"贯穿全部 Micro 相关描述。非破坏性变更（行为层面已经是 PMO 直接改，仅补齐文档一致性）。

### P0-16：Micro 流程描述一致性修订（SKILL.md + RULES.md + rules/flow-transitions.md + roles/pmo.md + STATUS-LINE.md + standards/common.md）

- 触发：用户反馈"Micro 流程是否还强制 RD 在 subagent 下执行，预期是 Micro 流程在初步分析后，PMO 自行判断是否切 Plan 模式还是以 RD 角色身份直接在主对话修改"。
- 根因分析：
  - v7.3 放宽了 Micro 流程红线：FLOWS.md §六「Micro 流程」+ SKILL.md 红线 #1 Micro 例外 + SKILL.md L122-126「AI Plan 模式 Micro 例外」已统一为「PMO 可直接改，无需 Subagent / Execution Plan / dispatch」
  - 但 SKILL.md L320 六种流程速查 / RULES.md 流转图 / rules/flow-transitions.md Micro 流程表 / STATUS-LINE.md Micro 示例 + 阶段对照表 / roles/pmo.md 反模式 / standards/common.md 预检级别表 等 7 处未同步更新，仍保留 v7.2 前的「RD Subagent 执行」旧描述
  - 导致跨文件描述自相矛盾：同一套规范里有地方说"PMO 直接改"，有地方说"必须启 RD Subagent"，对 PMO 读者造成歧义
- 处理（7 文件 / 11 处）：
  - **§一 SKILL.md L320**：六种流程 Micro 行 `RD Subagent 执行` → `PMO 自行判断执行方式（✍️ 主对话以 RD 身份直接改 / 🔀 升级为 Plan 模式走敏捷或 Feature）`
  - **§二 RULES.md L521-547 Micro 流程自动流转**：流程图去掉「🤖 RD Subagent 执行改动（🔴 PMO 禁止自己改，即使只改一行）」+「PMO L1 预检」节点；改为「PMO 自行判断：✍️ 主对话以 RD 身份直接改 / 🔀 升级 Plan 模式」分支；描述语加 v7.3 放宽 + P0-16 明确标注
  - **§三 RULES.md L720 功能完成时 PMO 必须执行**：Micro 流程校验改为「PMO 分析→用户确认→PMO 执行（主对话直接改 或 升级 Plan 模式）→用户验收 四步」
  - **§四 rules/flow-transitions.md**：
    - L39-40 强制保留暂停点表 Micro 两行（🤖 RD Subagent → 用户验收 / → ⏸️ 升级确认）改为 PMO 执行改动路径
    - L52 豁免示例 Micro 行改「按 💡 自动进入（PMO 自行判断执行方式，无需暂停）」
    - L167-177 § Micro 流程节完全重写：header 从「🔴 PMO 禁止自己改代码，必须启 RD Subagent」反转为「🟢 PMO 自行判断执行方式」；表格行从「PMO 分析 → Micro 变更说明 → 🤖 RD Subagent → 用户验收」4 行改为「PMO 分析 → PMO 执行改动 → 用户验收」3 主路径 + 升级确认支路
  - **§五 roles/pmo.md**：
    - L5 版本头「Micro 流程例外（v7.3）」描述修正：去掉「但必须走 Plan 模式规划 + 用户确认流程」与 FLOWS.md §六 冲突的旧字句，改为「无需 Subagent / Execution Plan / dispatch」+ P0-16 标注
    - L748 auto 豁免表 Micro 行改「PMO 执行改动（主对话直接改）」
    - L1379 反模式首行从「即使只改一行也必须启 RD Subagent」改为「必须先输出 PMO 初步分析 + Micro 准入检查 → ⏸️ 等用户确认 → 再由 PMO 主对话直接改」+ P0-16 标注
    - L1388-1399 PMO 小改动决策树末段从「🔴 任何情况下 PMO 都不能自己动手改代码」改为双分支：Micro 外保持禁止 + Micro 内 PMO 自行判断（直接改 / 升级 Plan）
  - **§六 STATUS-LINE.md**：
    - L201 Micro 示例状态行「下一步：🤖 启动 RD Subagent」改为「下一步：⏸️ 等待用户验收」，阶段从「Micro 变更说明中」改为「PMO 执行改动中」
    - L277-280 阶段对照表 Micro 专用阶段 3 行（Micro 变更说明 / 🤖 RD Subagent / 用户验收）重写为 PMO 执行改动 / Micro 升级判定 / 用户验收
  - **§七 standards/common.md**：
    - L242 L1 预检描述「包括 Micro 流程的 RD Subagent」改为「Micro 流程 PMO 主对话直接改，不走 Subagent，不触发本预检」
    - L354 各流程预检级别速查表 Micro 行从「Micro | RD Subagent | L1」改为「Micro | _（不启 Subagent）_ | —」
- 收益：
  - Micro 流程描述一致性：全部 12 处引用统一到「PMO 自行判断执行方式」语义，消除 v7.3 放宽以来遗留的 7 文件自相矛盾
  - 用户意图承载：显式写出「✍️ 主对话以 RD 身份直接改 / 🔀 升级 Plan 模式」双路径，PMO 读规范即知自己有判断空间，不再被旧描述误导去强启 Subagent
  - 红线体系简化：Micro 外「PMO 不得改代码」+ Micro 内「PMO 可直接改（白名单内零逻辑）」边界清晰，不需要维护"什么时候启 Subagent"的额外规则
- 兼容性（非破坏性）：
  - 行为面无变化：FLOWS.md §六 + SKILL.md 红线 #1 Micro 例外早已是"PMO 直接改"语义；PMO 按新描述执行与按旧描述通过"豁免启 Subagent"执行等价
  - state.json / localconfig：无字段变更
  - Subagent 不再在 Micro 下 dispatch，因此不影响 dispatch 模板 / agents/ spec

### P0-16 补丁：Micro RD 身份切换的必读规则（SKILL.md + FLOWS.md + RULES.md + rules/flow-transitions.md + roles/pmo.md + STATUS-LINE.md）

- 触发：用户反馈"如果切换 RD 身份是否会加载 rd 的规范，避免还是 PMO 只是输出描述改了"
- 根因：P0-16 主体改动把 Micro 执行路径统一到「PMO 以 RD 身份主对话直接改」，但未显式要求真实加载 RD 规范。Micro 流程免 Execution Plan 同时把 SKILL.md 红线 #14「Role specs loaded 必须真实 Read」也隐性豁免了——存在"PMO 换个名头凭记忆改"的漏洞
- 处理（6 文件）：
  - **SKILL.md L63 红线 #1 Micro 例外条款**：加"🔴 角色切换必读不豁免"子句，要求 Read roles/rd.md + standards/common.md + 按改动类型加读 frontend.md/backend.md + 摘要 cite 规范要点
  - **SKILL.md L122-126 AI Plan 模式 Micro 例外段**：扩展 Micro 例外条款的"不豁免项"清单，显式列出必读文件 + cite 规则 + 自查要求
  - **FLOWS.md §六 Micro 流程规则**：强制规则段加「角色切换必读」3 项新条款；流程链路 + 流转图 + 分析输出格式步骤描述 全部加入「PMO 加载 RD 规范+cite」节点 + 「RD 自查」节点；事后审计加 2 项校验（是否真实 Read / 自查是否执行）
  - **RULES.md Micro 流转图**：在「✍️ 主对话以 RD 身份直接改」分支下补全"改动前必读 / 改动前 cite / 改动后自查" 3 层硬约束
  - **rules/flow-transitions.md § Micro 流程**：表头加第二行「角色切换必读不豁免」警示；流转表从 4 行（PMO 分析 / 执行 / 升级 / 验收）扩展为 6 行（PMO 分析 / 加载 RD 规范 / 执行 / RD 自查 / 升级 / 验收）
  - **roles/pmo.md L5 头部 Micro 例外描述**：补全「角色切换必读不豁免」+「cite 规范要点」+「改动后自查」3 项硬约束
  - **STATUS-LINE.md L277-281 阶段对照表**：Micro 专用阶段从 3 行（PMO 执行改动 / 升级判定 / 用户验收）扩展为 5 行（PMO 加载 RD 规范 / PMO 执行改动 / RD 自查 / 升级判定 / 用户验收）
- 收益：
  - 堵住"换名头凭记忆改"漏洞：PMO 必须真实 Read + cite 规范要点，"我切 RD 了"一句话不能替代"读规范"
  - Micro 流程仍然是最轻量通道：不要求完整 Execution Plan / dispatch，但保留"真实加载 + cite + 自查" 3 层最小质量锚
  - 与红线 #14「Role specs loaded 必须真实 Read」+ AI Plan 模式红线「角色切换必 cite」保持一致：Micro 只豁免 Execution Plan 的输出形式，不豁免底层纪律
- 兼容性（非破坏性，仅加强约束）：
  - 行为面轻微变化：之前可能存在"PMO 未 Read rd.md 就直接改"的灰色操作，现在必须真实 Read + cite
  - 流转图多出 2 个新阶段（「PMO 加载 RD 规范」+「RD 自查」），属自动流转节点（🚀自动，无需用户确认）
  - state.json / localconfig：无字段变更

## v7.3.10 + P0-15

> v7.3.10 相对 v7.3.9 的唯一破坏性变更：Ship Stage 从「PMO 本地 merge + push merge_target」改为「MR 模式」（P0-15）。PMO 只负责净化 + push feature + 生成 MR/PR create URL，合并权由平台和用户处理。红线 #1 不再有 Ship 例外条款；localconfig 移除 `ship_rebase_before_push` / `ship_policy`；state.json.ship 字段重构。详见 P0-15 条目。

## v7.3.9 + P0 简化

> P0 是 v7.3.9 落地后的一轮"反刍"简化：抽取重复描述、收敛 preflight 暂停点、修正依赖安装时机表述、Codex 成本治理（P0-13：Plan/Blueprint opt-in 默认 OFF，Review 保持强制）、Dev Stage 默认主对话（P0-14：RD 自行规划 Plan 模式，subagent 降为 opt-in）、Ship Stage MR 化（P0-15：简化 PMO 职责边界）。无破坏性变更（P0-15 仅影响 Ship Stage 流程和 state.json.ship schema，向前兼容 v7.3.9 其他部分）。

### P0-15：Ship Stage MR 模式重构（stages/ship-stage.md + templates/feature-state.json + SKILL.md + INIT.md + roles/pmo.md + rules/flow-transitions.md + FLOWS.md + templates/config.md）

- 触发：用户反馈"当前 Ship 流程是否可以简化，例如开发完成后新分支的代码提交 push 后，生成 MR create 链接由用户创建 MR 可以了，这个 MR create 链接要记到 state.json 中，方便以后回溯，然后清理 worktree（如有），不删远程 feature 分支"。
- 决策：**Ship Stage 从 6 步直连合并流（净化 → push feature → rebase → 本地 merge --no-ff → push merge_target → worktree 清理）改为 3 步 MR 流（净化 → push feature + 生成 MR/PR create URL → worktree 清理）**。PMO 不做本地 merge / push merge_target / 冲突解决；合并权由平台（GitHub/GitLab/Gitee/Bitbucket 等）和用户处理。
- 根因分析：
  - v7.3.9 Ship Stage 让 PMO 承担了过多"最后一公里"职责：本地 merge、rebase、冲突解决、push merge_target。这些操作在多人协作场景下风险高（覆盖他人改动、污染主干）、需要复杂的红线 #1 例外条款（允许 PMO 改代码解冲突），且实际合入已由 MR/PR 平台做得更好（代码评审、CI/CD 门禁、合规审计、审批流）
  - 主流 git workflow（GitHub Flow / GitLab Flow / Trunk-Based）核心就是"push 分支 + 平台合入"，直连合并反而是反模式
  - 红线 #1 "PMO 非 Micro 流程下不得改代码" 加 Ship 例外条款使红线复杂化，不利于信任边界表达
- 处理（8 文件）：
  - **§一 stages/ship-stage.md 完全重写**（核心）：Input/Process/Output Contract 全部按 MR 模式重写；3 步流（Step 1 净化 / Step 2 push feature + host 识别 + MR URL 生成 / Step 3 worktree 清理暂停点）；per-host URL 模板（github / gitlab / gitlab-self-hosted / gitee / bitbucket / unknown）；unknown 平台走 localconfig `mr_url_template` 或 concerns 标注"未识别平台"；push FAILED 直接升级 ⏸️ 用户决策（不重试、不降级）；Anti-patterns 表更新（禁止本地 merge / 禁止 push merge_target / 禁止伪造 URL / 禁止删除远程 feature 分支）
  - **§二 templates/feature-state.json ship 字段重构**：移除 `rebase_status` / `merge_commit_hash` / `push_status`；新增 `sanitize_log` / `git_host` / `mr_create_url` / `feature_pushed_at` / `worktree_cleanup` / `shipped`；顶部 `_instructions.ship_tracking_v7_3_10_P0_15` 注释说明字段变更
  - **§三 SKILL.md 红线 #1 + INIT.md 红线 #1**：移除"🆕 Ship Stage 例外（v7.3.9）rebase/merge 冲突 PMO 可直接解决"条款；改为"🟢 Ship Stage 行为（v7.3.10+P0-15）：Ship Stage PMO 不做本地 merge / push merge_target / 冲突解决；只负责净化 + push feature + 生成 MR 创建链接。合并权由平台和用户处理（红线 #1 不再有 Ship 例外条款）"
  - **§四 roles/pmo.md**：PM 验收三选项 + Ship Stage 章节版本号 v7.3.9 → v7.3.10+P0-15；Merge 预览模板改 MR 模式（去掉 rebase 预处理行）；Ship Stage PMO 职责速查段全部重写（3 步流 + 禁止清单 + push FAILED 处理）；Commit / Push / Ship 状态报告改 MR 模式（`mr_create_url` / `git_host` / `worktree_cleanup` 字段）；强制保留暂停点清单移除"ship_policy=confirm merge+push"（第 2 项）和"Ship Stage 冲突 PMO 解不了"（第 4 项），改为 push FAILED 暂停点；移除"Ship Stage 冲突解决权限（红线 #1 例外）"段
  - **§五 rules/flow-transitions.md**：Feature 流程 Ship 行重写（PM 验收 → Ship Stage → worktree 清理 → 完成；移除 merge+push 待确认 / 本地 merge 行）；push FAILED 暂停点 2 选 1（手工处理后复跑 / 取消 Ship）
  - **§六 FLOWS.md**：PMO 初步分析阶段链 v7.3.4 → v7.3.10+P0-15（末段改 PM 验收 + Ship Stage MR 模式）；流程步骤描述第 8-10 步重写
  - **§七 templates/config.md 本地配置**：移除 `ship_rebase_before_push` / `ship_policy`；保留 `merge_target` / `worktree_cleanup`；新增 `mr_url_template` 字段（可选，自建 GitLab / 企业 git 自定义链接格式，支持 `{remote_url}` / `{repo_path}` / `{feature_branch_enc}` / `{merge_target}` 占位符）
- 收益：
  - PMO 职责边界清晰：Ship Stage 只负责"把分支送到平台门口 + 给用户合入入口"，不越界做代码层决策
  - 红线 #1 简化：移除 Ship 例外条款后，"PMO 非 Micro 流程下不得改代码" 变为真正的绝对红线，无需维护例外清单
  - 多人协作友好：平台 MR/PR 合入有代码评审 / CI / 审批记录，比 PMO 本地 merge 可审计性强
  - 无冲突解决成本：PMO 不解冲突 → 不需要单测全绿校验 / 不需要升级决策路径 / 不产生"解一半再回退"的中间态
  - 暂停点收敛：v7.3.9 "merge+push 待确认" + "worktree 清理" + "Ship 冲突/FAILED" 3 个 Ship 暂停点收敛为 1 个（worktree 清理）+ 1 个异常暂停点（push FAILED）
- 兼容性（破坏性变更，需迁移）：
  - **state.json.ship schema**：v7.3.9 已完成 Ship 的 Feature 保留旧字段（merge_commit_hash / push_status 等）不清理，可查阅；v7.3.9 进行中未到 Ship Stage 的 Feature 进入 Ship 时走新流程、写新字段
  - **localconfig**：v7.3.9 用户升级到 v7.3.10 时，`ship_rebase_before_push` / `ship_policy` 字段 PMO 自动忽略（不报错）；建议用户手动清理这两行 + 新增 `mr_url_template:`（空值即可）
  - **Codex CLI 子 agent**：Ship Stage 不通过 subagent 执行（PMO 主对话自主），无影响
  - **历史 Feature 的完成报告**：v7.3.9 报告中含 `merge_commit` / `已合入 {merge_target}` 字段的历史数据保留（审计痕迹）
- 未变更：
  - PM 验收三选项（通过+Ship / 通过暂不 Ship / 不通过）语义不变，只是"通过+Ship"进入的 Ship Stage 流程变了
  - 选 2（通过暂不 Ship）的 push feature 归档流程不变
  - 其他 Stage 的 auto-commit 硬规则 / git 干净校验 / Stage 切换预检均不变
  - merge_target 配置链（state.json > localconfig > 默认 staging）不变
  - worktree 清理策略（`worktree_cleanup: ask/keep/remove`）不变

### P0-1：auto-commit 硬规则集中化（rules/gate-checks.md + 8 个 Stage md）

- 问题：v7.3.9 在 8 个 Stage md（plan / ui_design / blueprint / blueprint_lite / dev / review / test / browser_e2e）中各重复一遍 5-7 行的 "Stage 完成前 git 干净" 流程描述。改文案需改 8 处，用户读 Stage 文件看到大段重复。
- 处理：将完整规则抽取到 `rules/gate-checks.md § Stage 完成前 git 干净`（含通用流程、各 Stage commit message 规范、单值/数组字段语义、免除场景）。各 Stage md 只保留一行引用 + 本 Stage commit message 示例。
- 收益：文案减少 ~35 行；单一修改点；引用链从分散变为集中。

### P0-2：Preflight 从 6 项砍到 4 项（plan-stage.md + pmo.md + flow-transitions.md + feature-state.json）

- 问题：v7.3.9 原设计"3 硬门禁 + 3 软提示"，实践发现：
  - "工作区干净" 是硬条件（worktree 继承脏状态代价大），不应软化
  - "merge_target 解析" 在级联无分歧时无需交互
  - "分支命名" 可从 Feature 全名自动派生
  - 最多 3 次暂停，用户体验冗长
- 处理：收敛为 **4 项硬门禁 + 0 软提示**：
  - 门禁 1：worktree 策略无残留
  - 门禁 2：分支名无冲突（分支名自动派生）
  - 门禁 3：base 分支可达（merge_target 自动解析）
  - 门禁 4：**工作区干净（P0 升级为硬门禁）**
  - 暂停点：最多 1 次（仅真冲突时）
- 收益：preflight 交互次数从"至多 3 次"降到"最多 1 次"。plan-stage.md / pmo.md 的校验表 + 暂停点模板同步更新。flow-transitions.md L11-12 更新 preflight 描述。feature-state.json 的 plan_preflight.checks 增加说明注释。

### P0-3：懒装依赖模型（plan-stage.md + dev-stage.md + test-stage.md）

- 问题：v7.3.9 描述 Feature worktree 创建时需装依赖（npm/pip/build），隐含 ~分钟级冷启动成本。实际只有 Dev / Test Stage 需要依赖，其他 Stage（Plan / Blueprint / Review）纯文档产出，空壳 worktree 就能跑。把依赖安装绑在 worktree 创建上是过早优化为保守。
- 处理：
  - `plan-stage.md` worktree 创建段补 "🟢 P0 懒装依赖模型" 说明：worktree 创建不装依赖
  - `dev-stage.md` 新增 "Stage 入口 Preflight：懒装依赖" 段：检测 → symlink 或 install → 记录到 `state.json.stage_contracts.dev.dependency_install`
  - `test-stage.md` 环境准备段补"懒装依赖兜底"：Dev 跳过场景下在 Test 入口补装
- 收益：Feature worktree 创建开销统一 ~1-2s（无 npm/pip 等待），Plan / Blueprint / Review 等纯文档 Stage 无冷启动税；依赖安装发生在真正需要它的 Stage 入口（单次付费）。

### P0-5：状态行第三行 —— 分支 / worktree 语义（STATUS-LINE.md）

- 问题：v7.3.9 状态行只有流程 / 角色 / 功能 / 阶段 / 下一步 + 功能目录路径两行。worktree 启用后，用户肉眼看不到"现在在哪个 worktree、绑定哪个分支、合入目标是什么"——必须翻 state.json 或跑 `git status` 才能确认。并行 Feature 或 Micro 直接改主分支的场景下，这种不可见性容易导致误操作（例如误以为还在 worktree，实际已回到主分支）。
- 处理：`STATUS-LINE.md` 新增第三行规范：
  - 🌿 = 启用了 worktree 隔离（安全）：`🌿 分支：{branch} → {merge_target} | worktree：{path}`
  - 📍 = 直接在分支上操作（谨慎）：`📍 当前分支：{branch} → {merge_target}（⚠️ ...）`
  - 各流程（Feature / 敏捷 / Bug / Micro / Planning / 问题排查）模板与示例同步更新
  - 字段取值优先 state.json.worktree + merge_target，缺失时回退 `git branch --show-current`
- 收益：PMO 每次回复都把分支 / worktree / merge_target 显式化，Micro 场景用 📍+⚠️ 做软兜底防误操作；并行 Feature 场景 worktree 路径直出，减少"在哪改"的混淆。

### P0-6：Codex CLI 宿主兼容性审计（browser-e2e-stage.md + review-stage.md + agents/README.md + templates/codex-cross-review.md + dispatch.md + review-log.jsonl + plan-stage.md + blueprint-stage.md + flow-transitions.md）

- 问题：审计各 Stage 在 Codex CLI 宿主下的可跑通性，发现 3 处强耦合 Claude 生态的表述：
  - **P0-6-A（Browser E2E 工具硬编码）**：`browser-e2e-stage.md` 隐含 `mcp__Claude_in_Chrome__*` / `mcp__gstack__*`，Codex CLI 宿主无此 MCP，Stage 直接跑不通
  - **P0-6-B（Review Stage 外部视角在 Codex 宿主下坍缩为自审）**：Codex CLI 宿主若"用自己当 Codex 外部视角"，则失去 session 隔离的独立性保证，"外部视角"名存实亡
  - **P0-6-C（降级模型硬编码 Sonnet）**：多处文档把"Codex CLI 不可用"的降级路径写死为"Sonnet fallback"，Codex 宿主用户没有 Sonnet 可降，该表述不成立
- 处理：
  - **P0-6-A**：`browser-e2e-stage.md` 新增"浏览器工具宿主适配"块：Claude Code 宿主用 MCP，Codex CLI 宿主走 Playwright/puppeteer 子进程，通用宿主无浏览器工具时降级为 ⏸️ 用户手动验收（带 WARN 日志 + `executor: user-manual` frontmatter）
  - **P0-6-B**：`review-stage.md` 步骤 4 + `agents/README.md §三` + `templates/codex-cross-review.md §二/§六` 统一规则——无论宿主是 Claude Code 还是 Codex CLI，外部视角**都通过 codex CLI 独立 spawn fresh session**（Claude 宿主：Task/MCP 调 codex 子进程；Codex 宿主：prompt 内 spawn `.codex/agents/*.toml` 子 agent）；🔴 明令禁止"外部视角 = Codex 主对话自审"
  - **P0-6-C**："Sonnet fallback" 全部替换为 "🟢 AI 自主规划等效独立审查"，并在 `agents/README.md §三` 新增"降级路径决策（🟢 AI 自主判断）"段：列决策维度（宿主可用模型清单 / 独立性强度 / 任务复杂度 / 成本 / 历史降级）+ 典型可行模式（fresh context 同宿主 / 低成本模型 / 并行双模型投票 / PMO 自审最弱兜底）；要求 AI 在 Execution Plan 或 concerns 写明降级决策理由
  - 同步扫清：`flow-transitions.md` L25 / `plan-stage.md` L225 / `blueprint-stage.md` L96 / `templates/dispatch.md` L78 + L260 + 降级汇总表 / `templates/review-log.jsonl` 示例注释
- 收益：三处"Claude 独有"表述转为宿主无关语义；Codex CLI 宿主可走全流程；外部视角独立性的来源从"不同模型"重定义为"fresh session 隔离"（可叠加跨模型做强形式）；降级策略从硬编码转为 AI 自主决策 + 理由留痕。

### P0-7：文档基准锚定（templates/ 格式权威 · TEMPLATES.md + roles/pmo+pm+rd.md + plan-stage.md）

- 问题：实战观察发现 AI 在起草 PRD / state.json / TECH 时倾向于"先参考最近一个 Feature 的格式"而非 Read `templates/` 中的模板。后果：
  - peer Feature 的产物可能装的是老 schema（state.json 尤其敏感，v7.3.2 / v7.3.9 / P0 都有增量字段），抄过去 = 漂移放大
  - peer Feature 可能被手动改过格式，漂移会扩散到新 Feature
  - templates/ 下模板齐全但没有任何文档声明它是"格式唯一真相源"，AI 的最近邻检索本能占上风
- 处理：新增"格式权威"契约，显式规定 templates/ 为唯一格式真相源：
  - `TEMPLATES.md` 顶部新增"🔴 格式权威红线"块：templates/ = 格式唯一真相源 / 禁止以 peer Feature 产物为格式基准 / peer Feature 仅可作内容参考 / state.json 特别注意
  - `roles/pmo.md` 顶部（职责段后）加"🔴 格式权威守门"：PMO 作为流转守门员对格式合规性负责，禁止在 Execution Plan 说"先参考最近一份 X 格式"
  - `roles/pm.md` 实现原则后加"🔴 PRD 格式权威"：起草 PRD 前 Read templates/prd.md 为基准
  - `roles/rd.md` 开发前必读后加"🔴 TECH / TC 格式权威"：起草前 Read templates/tech.md + templates/tc.md 为基准
  - `stages/plan-stage.md` PM 起草 PRD 步骤内插入"格式基准锚定"子条（v7.3.9+P0-7 硬规则）
- 收益：AI 的"抄邻居"本能被显式红线拦截；三角色（PMO 守门 / PM 起草 PRD / RD 起草 TECH+TC）都有对应条款；peer Feature 仅可作内容参考的语义清晰；state.json schema 漂移风险收敛。

### P0-8：跨项目依赖识别前置（FLOWS.md + roles/pmo.md + templates/dependency.md + stages/plan-stage.md）

- 问题：实战观察到 AI 在消费方 Feature 识别到"需要其他子项目能力"时，自由发挥：
  - 自创 DEPS.md（非 teamwork 标准文件名）
  - 放在消费方 Feature 目录（应放**上游子项目** `{upstream}/docs/DEPENDENCY-REQUESTS.md`）
  - 不读 templates/dependency.md 为格式基准（叠加违反 P0-7）
- 根因：templates/dependency.md 模板齐全，但 PMO 初步分析输出格式里没有「🔍 跨项目依赖识别」触发项；roles/pmo.md 的"跨子项目需求拆分"只覆盖场景 B（横跨多子项目 naturally），没显式区分场景 A（单 Feature 上游依赖）
- 处理：显式区分两种场景 + 前置触发 + 强绑定 templates/dependency.md：
  - `FLOWS.md` PMO 初步分析输出格式新增「🔍 跨项目依赖识别」项（和「🔍 跨 Feature 冲突检查」并列）：扫描上游依赖信号 → 场景 A（上游 `DEPENDENCY-REQUESTS.md` 追加 DEP-N）/ 场景 B（走跨子项目拆分）/ 无依赖
  - `FLOWS.md` 同时新增「📋 本轮拟产出文档清单」项（强化 P0-7 格式权威露出）：每份产物对应 templates/ 路径，PMO 声明 Write 前必 Read 模板
  - `roles/pmo.md` 新增「🔗 跨项目依赖识别」专门章节，详述场景 A 处理流程与硬规则：DEPENDENCY-REQUESTS.md 只放上游子项目目录 / 禁止消费方 Feature 目录自创文件 / 多条依赖分散到多个上游子项目
  - `templates/dependency.md` 顶部加"何时触发使用"说明（消费方 / 被依赖方各自触发点）+ 回链 roles/pmo.md
  - `stages/plan-stage.md` PM 起草 PRD 步骤加「跨项目依赖前置」硬规则：PM 发现上游依赖 → 立即通知 PMO 走场景 A（而非等 PRD 写完再补）
- 收益：消费方 Feature 遇上游依赖有明确流程可套；DEPENDENCY-REQUESTS.md 回到标准位置（上游子项目目录）；templates/dependency.md 触达面打开；P0-7 格式权威在 PMO 初步分析模板里露出，触达面从"藏在 roles/ 里"升级到"每次初分析都显式"。

### P0-14：Dev Stage 默认主对话 + RD 自行规划 Plan 模式（rd-develop.md + dev-stage.md + agents/README.md + feature-state.json）

- 触发：用户反馈"开发阶段在主对话，是否合理，不要求在 subagent，由 RD 自行规划 Plan 模式"。审计发现 v7.3.9 虽声称"Dev Stage AI 自主判断"，但 3 处残留默认偏向 subagent：
  - `agents/rd-develop.md` 整篇以"RD Subagent"视角书写（标题 / 执行摘要 / 自检触发条件均内嵌"subagent"措辞）
  - `templates/feature-state.json` planned_execution.dev 示例直接写 approach="subagent"
  - `agents/README.md` §一默认表虽写"AI 自主"，但判断条列"≤3 文件 → main"，隐含 >3 文件即 subagent 的保守基线
- 决策：**Dev Stage 默认 `main-conversation`**；subagent 降为 opt-in 路径（TECH.md 文件清单 >10 / 预期产出 >500 行 / 需独立聚焦或跨模型独立性时使用）；RD 在 AI Plan 阶段自评规模 + 声明 Rationale。
- 根因分析：
  - 主对话模式对大多数 Feature（单模块、改动 ≤10 文件、产出 ≤500 行）更优：省冷启动（3-5 min subagent 税）、TDD 过程用户可见、多轮调试不用重启 context、Plan/Blueprint 已加载的 PRD/TC/TECH 可直接复用（省 5-10K token 重读）
  - 原"AI 自主"措辞被"subagent 默认"的细节稀释 —— RD 启动时若第一眼看到 rd-develop.md 整篇 subagent 语境 + state.json 示例 subagent + README 表"≤3 文件才 main" → 自然默认选 subagent
  - subagent 的独立性价值在 Dev Stage 相对其他 Stage 弱：Review Stage 的 Codex / QA 独立性来自跨模型 + 盲区兜底；Dev Stage 是 RD 单视角执行，独立性收益不显著，冷启动税却实打实
- 处理（4 文件 + dual-mode 契约）：
  - **§一 rd-develop.md dual-mode 化**：标题从"RD Subagent：TDD 开发 + 自查"改为"RD 开发执行规范：TDD 开发 + 自查（Dual-Mode）"；新增 7 维对比表（启动方式 / 上下文 / 输入来源 / 用户可见性 / 进度汇报 / 最终输出 / 适用场景）+ 5 条 🔴 共同契约（TDD / UI 还原自检 / 自查 7 维度 / 产物格式 / auto-commit）；§二 输入文件加模式对比（主对话直读 + 可复用已加载 vs subagent 按 dispatch 硬读）；§四 执行摘要拆 4.1a 主对话（边做边汇报模板 + 5 个阶段性节点）+ 4.1b subagent（完成后一次性返回含 TDD 阶段耗时）；§四.2 RD 自查报告 + §四.3 上游问题清单两模式一致不变；UI 还原 NEEDS_FIX 自降规则改"两种模式一致"
  - **§二 dev-stage.md AI Plan 指引改写**：条件表从"AI 自主按规模判断"升级为"默认 main-conversation + 超阈值 opt-in subagent"5 行条件：默认无特别信号 → main / 文件 >10 或 >500 行 → subagent / 跨模型独立性 → subagent / 多轮调试跨 Feature → main 强化 / 灰色地带向默认倾斜；新增 3 条灰色地带判定示例（10 文件/400 行/单模块、12 文件/600 行/跨前后端、8 文件/300 行/3 轮 TDD 调试）；Duration baseline 前置主对话路径（≤3 文件 15-25 / 5-10 文件 30-60）+ subagent 档（>10 文件 30-90 含冷启动税）
  - **§三 agents/README.md §一默认表**：Dev Stage 行从"AI 自主按规模判断"改为"main-conversation（v7.3.9+P0-14 默认）"；判断列改"默认主对话；TECH 文件清单 >10 / 预期产出 >500 行 / 需独立聚焦 → subagent（opt-in）"
  - **§四 feature-state.json 示例**：planned_execution.dev 主示例改 approach="main-conversation" + rationale 引用 P0-14 默认 + 无 dispatch_file 字段（加 `_dispatch_file_comment_v7.3.9+P0-14` 解释）；保留 `_subagent_alternative_example` 子对象作为 opt-in 样例（TECH >10 文件的场景）
- 收益：
  - 默认 Feature 节省 3-5 min subagent 冷启动 + 5-10K token（复用 Plan/Blueprint 已加载产物）
  - TDD 过程用户可见 → 早发现方向偏差 / 提前介入多轮调试
  - Subagent opt-in 通道保留，大改动 / 跨前后端场景不牺牲独立聚焦
  - RD 自查 + UI 还原自检 + NEEDS_FIX gate 两模式完全一致，契约不变
  - dual-mode 表 + rationale 要求 → RD 在 Plan 阶段的判断更透明（retro 可统计默认采纳率、subagent opt-in 比例）
- 兼容性：
  - 既存 Feature（已完成 Plan/Blueprint）不受影响；Dev Stage 未启动的 Feature 进入 Dev Stage 时按新默认
  - 既存 dispatch_log（已派发 subagent 的 RD 任务）保持有效 —— subagent 模式路径完整保留，只是不再是默认
  - state.json schema 不变（approach 字段早已支持 main-conversation / subagent / hybrid）
  - rd-develop.md dual-mode 化后 Codex CLI 子 agent（若有）仍可按原 prompt 调用（subagent 模式契约未变）
- 未变更：
  - TDD 红-绿-重构三步流程（§三.1）/ 开发约束（§三.2）/ RD 自查 7 维度（§三.3）/ UI 还原权威层级 + 自检清单（§三.4，P0-12 成果）全部保持不变
  - DONE / NEEDS_FIX / FAILED 三态 gate + UI 还原缺失自降 NEEDS_FIX 规则不变
  - Review Stage 三视角契约不变（本 P0 只改 Dev Stage 执行方式默认）
  - Codex CLI 子 agent / subagent dispatch.md 协议 / standards/{common,backend,frontend}.md 加载规则均保持

### P0-13：Plan/Blueprint Codex 交叉评审 降为 opt-in 默认 OFF（成本治理 · templates/codex-cross-review.md + plan-stage.md + blueprint-stage.md + roles/pmo.md + FLOWS.md + feature-state.json）

- 触发：用户明确反馈"Feature 流程每次都强制 Codex 成本太高，PRD 流程也不需要"。审计发现 Plan + Blueprint Stage 的 Codex 交叉评审每次 +10-20 min + ~10K token，对小改动 / 内部视角已充分的场景 ROI 偏低。
- 决策：**Plan + Blueprint Stage** 的 Codex 交叉评审从 🔴 强制降为 🟡 opt-in 默认 OFF；**Review Stage** 的 Codex 代码审查保持 🔴 强制不变（其盲区独立采样 + 静态分析价值最高，且是代码层最后一道质量 gate）。
- 根因分析：
  - Plan/Blueprint 产物为文档（PRD / TC / TECH），内部多视角评审（PM + PL + RD + Designer + QA + PMO + 架构师）已覆盖质量下限；Codex 的增量价值随 Feature 规模递减
  - Review Stage 的 Codex 是代码层盲区兜底，与其他场景不同 —— 代码 bug 进入代码库的代价远高于文档修订，Codex 在此保留强制
  - 先前"🔴 强制"设计偏向保守，缺乏"用户可按风险/规模动态开关"的弹性
- 处理（6 文件 + 3 层开关）：
  - **Schema 层**：`templates/feature-state.json` 新增 `codex_cross_review = {enabled, decided_at, decided_by, note}` 字段，默认 `enabled: false`；_comment 明确 Review Stage 不受本开关影响
  - **决策点层（PMO 初步分析）**：
    - `FLOWS.md` PMO 初步分析输出格式 4 种变体（Feature / 敏捷需求 / Feature Planning / 跨子项目）追加「🤖 Codex 交叉评审决策」行，4 选 1 默认不开
    - `roles/pmo.md` 新增「🤖 Codex 交叉评审开关决策」独立章节，含建议逻辑（规模/风险信号）+ state.json 写入规范 + 硬规则（默认 OFF / 必须显式输出 / Review Stage 独立）
  - **执行层（Stage 内条件化）**：
    - `stages/plan-stage.md` Input Contract 的 codex-cross-review.md 改为条件必读（`enabled==true`）；Process Contract Step 3 的 Codex 改为 opt-in + 关闭时声明；过程硬规则 5 条 Codex 相关项从 🔴 降为 🟡；Output Contract 表格加条件列（pmo-internal-review / prd-codex-review 仅开启时必需）；机器校验分两组（开启/关闭）
    - `stages/blueprint-stage.md` 同 pattern：本 Stage 职责描述、Input Contract、Process Contract Step 5、过程硬规则、Output Contract 表格、机器校验、Done 判据、AI Plan 模式指引、执行报告模板 全部条件化
  - **治理层**：`templates/codex-cross-review.md` §二适用场景表 Feature / Feature Planning / 敏捷需求的 Plan/Blueprint 列统一改为"🟡 opt-in（默认 OFF）"；新增 §2.1「PMO 初步分析决策」规范 + §八 R7 改写为 P0-13 修订说明 + 明确 Review Stage 独立强制
- 收益：
  - 默认场景节省 10-20 min + ~10K token（小改动 / 单子项目 / 内部视角充分的场景多数符合）
  - 保留 opt-in 通道（大改动 / 跨子项目 / 高风险场景用户主动开启）
  - Review Stage 代码审查保持强制，代码层最后一道 gate 不放松
  - state.json 持久化开关 + 决策留痕（decided_at / decided_by / note）便于 retro 分析采纳率
- 兼容性：
  - 既存 state.json（v7.3.9 + P0-11 及之前）**缺少 codex_cross_review 字段** → PMO 读取时按 "enabled=false" 默认处理（等价"关闭"），不触发迁移
  - 既存 Feature（已完成 Plan/Blueprint）不受影响；当前进行中的 Feature 若已完成 Plan Stage 产物，Blueprint Stage 进入时由 PMO 补写 codex_cross_review（enabled=false，note="既存 Feature 默认关闭"）
  - codex-cross-review.md / codex-agents/*.toml / prd-reviewer / blueprint-reviewer 均保留（开启时走原路径）
- 未变更：
  - Review Stage 的 Codex 代码审查：🔴 强制不变（review-stage.md + codex-agents/code-reviewer.toml）
  - 4 流程（Bug / 问题排查 / Micro / Feature Planning）与 Codex 的关系：Bug / 问题排查 / Micro 本就跳过 Codex；Feature Planning 沿用 Feature 同规则（opt-in 默认 OFF）
  - 降级路径、独立性校验、输出 schema、findings 分类规则：开启时完全复用原规范

### P0-12：preview/*.html 漏传 + UI 还原权威层级（实战漏洞修复 · dispatch.md + dev-stage.md + rd-develop.md + roles/pmo.md）

- 触发：实战 case —— RD 实现页面时"遵循了文字规格却没还原 HTML 预览稿"，PM 验收发现明显偏差，被迫走 Bug 流程。
- 根因分析（两层叠加）：
  - **第一层：preview 漏传**。`templates/dispatch.md` 的 Input files 清单只列了通用项（README / agent md / standards），Feature 产物走占位符 `{其他必需文件绝对路径}`；同时 `stages/dev-stage.md` L30 的必读清单里 `UI.md + preview/*.html` 用"（如有）"措辞，让 PMO 把一定存在的 preview 当成可选 → 起草 dispatch 时漏列。RD subagent 只看 dispatch Input files，不会主动翻 roles/stages，漏列 = 真漏传。
  - **第二层：即便传了也没权威层级**。`agents/rd-develop.md` 原 Step 5 只写"如有 UI → 还原页面"，没定义 preview 和文字规格冲突时谁是权威；LLM 天然偏好结构化文本（PRD/TECH.md）→ 视觉 / 交互偏差。
- 处理（4 文件 + 三层防护）：
  - **第一层（模板硬化）**：`templates/dispatch.md` 新增「🔴 Feature 产物强制白名单」段，按 Stage 列出 blueprint / dev / review / test / browser-e2e 的必选 Feature 产物；Dev Stage 在 `ui_design.output_satisfied==true` 条件下 **显式要求 UI.md + preview/*.html 进 Input files**；附反模式："把 preview 当'可选参考'仅在 Additional inline context 里提一嘴"。
  - **第二层（措辞硬化）**：`stages/dev-stage.md` L30 去掉"（如有）"暧昧措辞，改为条件式："若 `state.stage_contracts.ui_design.output_satisfied==true` → 必读（视觉/交互权威）"；L86 还原段引用 rd-develop.md 的 UI 还原权威层级 + 自检。
  - **第三层（RD 侧权威层级 + 自检）**：`agents/rd-develop.md` 新增 §三.4 「UI 还原（有 preview 时必做）」：
    - 权威层级（冲突时优先级）：视觉/间距/颜色/响应式 → preview 权威；交互状态 → preview 权威，未覆盖看 TECH；业务逻辑 → TECH 权威，禁止照抄 preview mock 数据；验收判定 → TC 权威
    - 冲突兜底：preview 视觉 ≠ PRD 文字 → 以 preview 为准 + concerns 1 行；preview 交互 ≠ TC AC → 以 TC 为准 + concerns
    - UI 还原自检清单（Dev 完成前必做）：视觉 / 交互状态 / 响应式 / 偏离项 concerns / mock 数据未照抄 / preview 未覆盖状态找依据
    - 反模式 4 条
    - 自查表新增 UI 还原 4 行（视觉 / 交互 / 响应式 / 偏离 concerns），**缺失或未贴证据 → 自降 NEEDS_FIX**
  - **PMO 侧硬校验**：`roles/pmo.md` 进入 Stage 的 subagent 路径新增"Feature 产物白名单硬校验"：若 `ui_design.output_satisfied==true` 但 Input files 未包含 UI.md + preview → **PMO 自拒重生**，不得发出。
- 收益：
  - 漏传链路补齐（模板白名单 + 措辞硬化 + PMO 自校验 + Subagent `NEEDS_CONTEXT` 兜底，四层 gate）
  - 权威层级清晰（冲突时有规可循，不再靠 LLM 天然偏好）
  - 自检 gate 可执行（7 项清单 + DONE/NEEDS_FIX 硬绑定，漂移可被拦截）
  - 反模式负向定义（过度还原 / 欠还原 各自拦截，避免从一个坑跳进另一个坑）
- 兼容性：UI Design Stage 未跑的 Feature 流程完全不变；preview 不存在时自检项填 "-" + 说明"无 UI Design 产物"。

### P0-11-B：auto 模式默认跳过 Browser E2E Stage（roles/pmo.md + rules/flow-transitions.md + INIT.md）

- 触发：Browser E2E Stage 启动成本显著（headless 浏览器冷启动 / MCP 握手 / 脚本录制回放），auto 模式下默认应倾向"快速走完主干"。用户明确要求："auto 模式默认不启动 browser-e2e"。
- 处理（3 文件，新增"默认跳过 + 可逃逸 + 必留痕"三件套）：
  - **默认跳过条件**：`AUTO_MODE=true` + Test Stage 完成 + `TC.md` 含 Browser E2E AC → **跳过 Browser E2E Stage**，直接进 PM 验收
  - **留痕（三处，便于事后追溯 / PM 验收判断）**：
    - `state.json.stage_contracts.browser_e2e = {status: "SKIPPED_BY_AUTO", skipped_at, skip_reason}`
    - `review-log.jsonl` 追加一行 `{event: "browser_e2e_skipped_by_auto", feature_id, timestamp}`
    - PMO 输出 `⚡ auto skip: Browser E2E Stage | 💡 直接进 PM 验收 | 📝 AUTO_MODE 默认跳过` 日志
  - **显式标注（PM 验收 / 完成报告）**：PM 验收摘要和完成报告必须打出「⚠️ Browser E2E 已按 auto 模式跳过」提醒
  - **用户逃逸路径（两种）**：
    - PM 验收时选"3 返修"+ 备注「跑 Browser E2E」→ 下轮补跑
    - 下轮命令带「含 browser e2e / 带 e2e / run e2e」关键词 → 例外命中，不跳过
  - **例外（不跳过）**：命令关键词命中 / `TC.md required_even_in_auto=true` / 手动模式（AUTO_MODE=false，原流程不变）
  - **文件落点**：
    - `roles/pmo.md` 豁免表新增 Browser E2E 行 + 新增「🟡 Browser E2E auto 默认跳过（P0-11-B 新增专项规则）」专章（含触发 / 留痕 / 标注 / 逃逸 / 例外 / 设计理由）
    - `rules/flow-transitions.md` 顶部 auto 豁免速查增补 Browser E2E 子块
    - `INIT.md` Step 0 速查表补一条"Browser E2E auto 默认跳过"规则
- 设计理由：
  - Browser E2E 启动成本明显高于其他 Stage（浏览器进程 / 录屏 / 网络往返），auto 的设计目标是"压暂停点"而非"压成本"，但 Browser E2E 是单 Stage 成本占比最高的一环，跳过的 ROI 显著
  - PM 验收本就是 auto 模式下的强制保留点（业务决策），Browser E2E 缺失由 PM 在验收时决定是否补跑，链路闭环
  - 三处留痕确保"跳过"可审计、可回溯、不静默
- 收益：auto 模式全链路时长显著缩短（省去 Browser E2E Stage 整段）；用户可通过"关键词显式要 E2E"或"PM 验收补跑"双通道保留覆盖能力；跳过决策留痕三处，事后可查。
- 兼容性：手动模式（AUTO_MODE=false）流程完全不变；`TC.md required_even_in_auto=true` 是显式覆盖开关，向前兼容。

### P0-11-A：auto 模式豁免/保留边界修订（实战漏洞修复 · INIT.md + roles/pmo.md + flow-transitions.md）

- 触发：P0-11 落地首轮实战，用户 `/teamwork auto ... 推进到 Blueprint 完成` 命令被中间"外部依赖已就绪 → 恢复流程"暂停点卡住。根因：P0-11 原强制保留清单把"外部依赖恢复"归为保留，与 auto 模式设计意图直接冲突。
- 根因分析：
  - 暂停点的本质 = 请求用户给出**决策内容**
  - 若决策内容已被 `/teamwork auto [推进/恢复/继续...]` 命令语境承载 → 再停下来要一次确认 = 把命令意图当空气
  - 强制保留的合理边界 = 需要**新**决策内容（业务判断 / 技术分歧 / 破坏性授权 / 红线处理）
- 处理（3 文件）：
  - **新增元规则「意图承载豁免」** 写进 `roles/pmo.md` + `rules/flow-transitions.md` + `INIT.md`：判定前先问「此暂停点需要的决策内容是否已被 auto 命令承载？」；是则豁免，否则保留
  - **从强制保留清单移除 2 项**（归入豁免）：
    - ~~外部依赖已就绪 → 恢复流程~~ → 豁免：auto 命令已承载"恢复"意图
    - ~~Planning / PL 模式的最终确认~~ → 豁免：auto 命令已承载"推进"意图（且原豁免表已有 Roadmap / teamwork_space / Workspace Planning 收尾行覆盖）
  - **新增 Test Stage 前置确认 到强制保留**（原遗漏补齐）：跨 Feature 节奏决策，需用户判断立即 / 延后 / 跳过
  - 强制保留清单从 15 项收敛到 **13 项**（边界更锐利）
  - **反模式样例**写进文档：「auto 命令明说推进到 X，却被中间恢复确认卡住 = 把用户意图当空气」
- 收益：
  - auto 模式实战可用——用户给定终点的命令不会被"你确定要继续吗"类暂停点坍缩
  - 强制保留语义从"列表式枚举"升级为"决策类型判定"，新暂停点上线时可按元规则快速归类
  - 反模式样例给 PMO 自检提供具体参照

### P0-11：⚡ auto 模式（一次性总开关，INIT.md + roles/pmo.md + flow-transitions.md + STATUS-LINE.md）

- 背景：teamwork 暂停点密集（Feature 流程单次跑全流程 10+ 次 ⏸️），对"我已经心里有数、按你建议走"的场景体验重。需要一个一次性总开关让 PMO 按 💡 自动推进，同时保留关键决策的强制暂停。
- 设计取舍（6 点均按用户"按建议"确认）：
  1. **入口命令**：`/teamwork auto [需求]` / `/teamwork auto 继续` / `/teamwork auto ship F{编号}`（第一个 token 为 `auto` 开启）
  2. **作用域**：单次命令周期（仅本次 /teamwork 生命周期有效）；用户重新 `/teamwork`（不带 auto）自动重置；compact 后默认 false；**不写 localconfig / state.json**（避免"以为关了其实没关"）
  3. **豁免范围**：普通方案 review / 阶段切换 / preflight 默认值 / PRD-UI-TC-TECH 草稿 review / dispatch 前检 / review 结果接受
  4. **强制保留 15 项**（按 roles/pmo.md 强制保留清单）：PM 验收三选项 / Ship 关键操作 / Blueprint concerns / MUST-CHANGE / 破坏性操作 / 13 红线 / Micro 用户验收 / 外部依赖解锁 / 意图不确定语气 等
  5. **与 ship_policy 正交**：auto 是 session 级总开关，ship_policy 是 Ship Stage 细粒度；auto **不覆盖** `ship_policy=confirm`
  6. **关闭方式**：命令级（下次不带 auto 即手动）+ 运行时（用户消息含「停 / 暂停 / manual / 等一下 / 先等等」立即关闭）
- 处理（5 文件）：
  - `INIT.md` 启动必做前加 **Step 0**：解析 `/teamwork auto` 命令行 + 速查豁免与强制保留清单
  - `roles/pmo.md` 在 "⚡ PMO 自动推进规则" 后新增 **"⚡ auto 模式暂停点豁免规则"** 章节：触发时机 / 豁免表 / 强制保留 15 项表 / 跳过日志格式 / 强制保留命中提示格式 / PMO 自检清单 / 运行时关闭
  - `rules/flow-transitions.md` 顶部新增 **"⚡ auto 模式豁免速查"** 块：列出所有强制保留行号+理由；给出典型豁免示例（其余默认豁免）
  - `STATUS-LINE.md` 第一行格式增加可选 **`⚡ AUTO` 徽章**（AUTO_MODE=true 时在 `🔄 Teamwork 模式` 和 `|` 之间显示）+ 状态行规则 + 示例
  - 跳过日志：`⚡ auto skip: {决策简述} | 💡 {建议} | 📝 {理由}` 每次豁免输出一行，便于追溯
- 收益：
  - 一次性开关覆盖高频 ⏸️，用户体验从"每步都要回确认"降到"关键处再决策"
  - 作用域仅 per-command，不污染 localconfig，降低"隐藏状态"事故面
  - 强制保留清单明确兜底所有破坏性 / 业务判断 / 红线场景
  - 跳过日志 + 徽章让"auto 到底替我做了什么"完全可见
  - 与 P0-9（worktree 默认 off）形成对称：worktree 需显式 opt-in，auto 也需显式 opt-in；不隐藏复杂性

### P0-9：worktree 保留默认 off（设计决策 · templates/config.md + INIT.md 决策注释）

- 背景：曾考虑把 worktree 默认从 off 翻转到 auto（让新用户开箱即得并行隔离），深入讨论后回撤，**保留 off 为默认**。
- 回撤理由（四个税点，默认 auto 让新用户透明付费不合理）：
  1. **megarepo 全量 checkout 代价**：`git worktree add` 不支持按子目录稀疏 checkout（需额外配 `git sparse-checkout`）；大仓并行 3 个 Feature = 3 份全量工作树（每份 ~GB 量级），磁盘 / IDE 索引 / 工具链遍历开销显著
  2. **IDE review 不便**：worktree 在 sibling 目录下，IDEA 单 Project 窗口看不到其他 worktree 的代码 / 文档；VS Code 需要 Multi-root Workspace 配置；跨 worktree Cmd+Click / 搜索被割裂
  3. **`.worktree/` 内嵌方案的隐性长尾**：即便内嵌到项目根 + `.gitignore`，仍需为每个扫描项目根的工具（tsc / eslint / prettier / jest / pytest / webpack / nx / turbo / docker / IDE LSP / CI find-grep）单独维护排除规则——新工具加入默认踩坑
  4. **默认 auto 把复杂性隐藏**：用户不理解 worktree 语义时遇到上述问题会困惑，把选择权还给用户（显式 opt-in）更稳
- 处理：保持 off 为默认 + 把决策理由注释到 localconfig 模板：
  - `templates/config.md` 保留 `worktree: off`；注释块新增"保留 off 为默认的原因"四点说明，引导用户 opt-in 前先评估 P0-10 的 worktree_base + IDE workspace 自动配置（待实施）
  - `INIT.md` localconfig 不存在分支保持"默认 scope=all，worktree=off"，加提示"如需并行 Feature 隔离，主动改 localconfig 为 auto/manual"
  - `docs/OPTIMIZATION-PLAN.md` 历史记录段保持"默认 off"
- 收益：对初学者友好（不引入 worktree 的 megarepo / IDE review / 工具链忽略复杂性）；有需要的用户显式配置 auto/manual 时自担理解成本；为 P0-10（worktree 路径合法性 + 分组 `../.{repo}-worktrees/` + IDE workspace 自动生成）铺好 opt-in 路径。

### P0 影响面（非破坏性）

```
├── state.json schema：兼容（P0-3 新增 dev.dependency_install 可选字段；P0-2 plan_preflight.checks._note 注释；P0-5 复用既有 worktree + merge_target 字段；P0-6 无 schema 变化；P0-7 无 schema 变化，纯契约文档加强；P0-8 复用既有 blocking.pending_external_deps 字段；P0-9 决策保留默认 off · 无默认值改动；P0-11 AUTO_MODE 纯运行时状态，不写 state.json / localconfig）
├── localconfig：无新增字段（P0-11 刻意不持久化 AUTO_MODE）
├── 历史 Feature：完全兼容（P0 是描述修正 + 文案抽取 + 渲染增强 + 宿主适配 + 格式权威契约 + 依赖识别前置 + 一次性 auto 总开关，不改流程语义）
└── CI / 工具链：无影响（P0-6-A 浏览器工具为宿主可选，项目未启用 Browser E2E 不受影响；P0-7/P0-8/P0-11 纯文档与运行时规则；P0-9 设计决策）
```

### P0 后未涉及的内容

```
- Ship Stage / PM 验收三选项 / merge_target 三层解析：保持 v7.3.9 定义
- 红线 #1 例外条款：保持 v7.3.9 定义
- Micro 流程 worktree 方案：暂缓（见 docs 讨论，待真实需求再做）
```

---

## v7.3.9 —— PM 验收三选项 + Ship Stage + 每阶段 auto-commit + Plan Stage 入口 Preflight

背景：v7.3.4 的 PM 验收合并暂停点（验收 + commit + push 三项打包）存在 3 个结构性缺陷：
1. **合并目标缺省硬编码**：push 目标默认 `origin/{feature branch}`，用户真正的目标分支（staging / develop）无处配置，合入动作被迫延后到命令行手工解决
2. **单暂停点承载过多决策**：验收 + commit 策略 + push 策略 + 目标分支挤在一个暂停点，用户必须一次回答完，错一个选项回退代价极高
3. **冲突 / 净化 / rebase 无流程位**：push 前是否需要 rebase、feature 分支有无需要净化的残留 commit（debug 文件、合并遗留）、冲突解决授权——这些本质是 Ship 流程问题，塞在 PM 验收里越想越不对

同时在使用过程中发现另一个风险源：**Feature 的全部产物（PRD/UI/TC/TECH/代码/测试）都从 Plan Stage 开始累积**。如果 worktree 基于错误的 base 分支（陈旧 main 而非 origin/staging），到 Ship 时 rebase onto staging 会遇到大规模冲突——此时产物已成定局，回退代价高于 Ship 本身。v7.3.8 的"前移 worktree 创建"只解决了隔离问题，没解决 base 问题。

本版把 v7.3.4 的 PM 验收合并暂停点**拆解成 3 段**，并在 Plan Stage 入口加一层 preflight：

```
v7.3.4（旧）：PM 验收 → ⏸️（3 选 1 全打包）→ 完成 / 合入
v7.3.9（新）：PM 验收 → ⏸️ 3 选 1（业务判断）→ Ship Stage（PMO 自主合并） → ⏸️ 2 选 1（push 目标分支或仅本地）→ ⏸️ worktree 清理 → 完成
            ↑
            Plan Stage 入口 preflight（v7.3.9 新增）提前锁定 base 分支，防止 Ship 时灾难
```

### 1) PM 验收三选项（roles/pmo.md + rules/flow-transitions.md）

- **选 1**：通过 + Ship → 进入 Ship Stage（独立 Stage）
- **选 2**：通过但暂不 Ship → PMO 执行 `git push origin {feature branch}` 归档 `shipped: false`，后续可 `/teamwork ship F{编号}` 触发
- **选 3**：不通过（有建议）→ 按问题类型回退（功能缺陷 → Review Stage / 测试遗漏 → Test Stage / UI 不符 → UI Design / 需求偏差 → Plan Stage），前序 commit 保留，修复循环 ≤3 轮

### 2) Ship Stage（新建独立 Stage，stages/ship-stage.md）

- **PMO 自主执行 Step 1-4**：净化 → push feature → rebase 可选（`ship_rebase_before_push` 默认 false，多人场景兼容）→ 本地 merge --no-ff onto `merge_target`
- **单一暂停点 2 选 1**：merge + push `{merge_target}` / 仅本地 merge 不 push
- **worktree 清理暂停点**：worktree ≠ off 时询问清理 / 保留
- **冲突授权**（红线 #1 例外）：PMO 可直接解 git marker 冲突（前提：前序 DONE + 单测全绿 + 解完重跑单测）；不满足升级 ⏸️ 用户决策
- **Sanitize 日志**：residual_commits（待审）/ cleaned_files（已处理）/ suspicious_files（灰名单仅报不动，用户决定）

### 3) 每阶段 auto-commit 硬规则（stages/dev-stage.md + review-stage.md + test-stage.md + browser-e2e-stage.md）

- 每个 Stage `output_satisfied=true` 之前 PMO 执行 `git status --porcelain`
- 非空 → PMO auto-commit `git add -A && git commit -m "F{编号}: {Stage} Stage - {简述}"`，commit hash 写入 `state.json.stage_contracts.{stage}.auto_commit`（单值）或 `auto_commit[]`（多轮修复）
- 目的：每个 Stage 产物落地即 commit，Ship Stage 不再需要"一次性收拾"所有遗留改动；同时给 Review Stage 提供稳定 diff 锚点

### 4) Plan Stage 入口 Preflight（stages/plan-stage.md + roles/pmo.md）

- PMO 在用户确认流程类型后、Plan Stage 产物诞生前执行 6 项校验：
  - 🔴 硬门禁：worktree 策略无残留 / 分支名无冲突 / base 分支可达
  - 🟡 软提示：工作区干净 / merge_target 解析清晰 / Feature 编号命名合规
- **worktree 创建显式指定 base**（v7.3.9 关键改动）：
  ```bash
  git fetch origin {merge_target}
  git worktree add ../feature-{全名} -b feature/{全名} "origin/{merge_target}"
  ```
- state.json 新增 `stage_contracts.plan_preflight` 记录 6 项校验结果 + base_branch

### 5) merge_target 配置三层解析（templates/config.md + feature-state.json）

- 优先级：`state.json.merge_target` > `.teamwork_localconfig.md` 中 `merge_target` > 默认 `staging`
- 新增 localconfig 字段：`merge_target` / `ship_rebase_before_push` / `ship_policy` / `worktree_cleanup`
- state.json 新增顶层 `ship` 块（sanitize_log / rebase_status / merge_commit_hash / push_status / worktree_cleanup / shipped）

### 6) 红线 #1 例外条款（INIT.md + SKILL.md）

- v7.3.9 新增 Ship Stage 冲突解决例外：PMO 可直接解 git marker 冲突，前提：前序 DONE + 单测全绿 + 解完重跑单测通过
- 不满足则升级为 ⏸️ 用户决策

### 7) flow-transitions.md 更新

- PM 验收行拆为 5 行（PM 验收三选项 / Ship Stage / merge+push 待确认 / worktree 清理待确认 / Ship Stage 冲突回退）
- PMO 初步分析 → Plan Stage 之间插入 Plan Stage 入口 preflight 暂停点

### 为什么这样拆（设计取舍）

| 候选设计 | 评估 |
|---------|------|
| ~~PM 验收暂停点内嵌 Ship 策略~~（v7.3.4）| 单点决策过多，回退代价高，用户体感卡 |
| ~~Ship 整个走 Subagent~~ | Feature 最后一步，主对话 context 已沉淀，新 Subagent 要 /clear 反而丢失一致性 |
| **Ship Stage 由 PMO 自主执行 + 两段暂停** ✅ | 决策维度清晰（业务判断 vs 合入策略 vs 清理策略），每段单点决策 |
| ~~Ship 时一次性 commit 所有 Stage 遗留~~ | 破坏 Stage 边界，diff 锚点模糊，review 困难 |
| **每 Stage 独立 auto-commit + Ship 仅净化** ✅ | Stage 产物落地即 commit，Ship 只解决 git 异常 |

### 不改动项（仍保留）

- Worktree 创建触发点仍在 Plan Stage 入口（v7.3.8 定稿）
- 默认 `worktree` 值仍为 `off`
- PMO 非 Micro 流程下不得改代码的红线 #1 主干不变（仅加 Ship Stage 例外）
- Review / Test / Browser E2E 的产物契约不变（只加 auto-commit 过程规则）

### 操作影响

- **新 Feature**：经历 6 步（preflight → Plan → ... → PM 验收 → Ship → 清理），每步暂停点用 1/2/3 编号单点决策
- **进行中 Feature**（v7.3.8 及之前启动）：到达 PM 验收时按新流程分叉（无 preflight 重跑），已累积的 commit 由 auto-commit 硬规则补齐
- **单分支用户**（merge_target = main）：ship_rebase_before_push = true 更合适，通过 localconfig 显式配置

## v7.3.8 —— Worktree 创建时机前移至 Plan Stage 入口

背景：v7.1 引入 worktree 集成，触发点放在"方案待确认 → Dev Stage"的流转（即 Blueprint 结束后）。这意味着 **Plan Stage 的 PRD/discuss/评审产物、UI Design 的 UI.md、Blueprint 的 TC/TECH**——一整套 Feature 早期文档都**落在 main 分支上**。这违反了 worktree 隔离的初衷：
- 用户拒绝 PRD → 一堆文档孤儿留在 main，要么 revert 要么保留
- v7.3.7 引入的 Codex 交叉评审读的是主分支 PRD，受 main 并发修改干扰
- 跨 Feature 并行时 Plan 阶段文档互相污染（F042 的 PRD 在 F043 工作区可见）

本版把 worktree 创建触发点从 Dev Stage 前移到 **Plan Stage 入口**（"PMO 初步分析 → Plan Stage"的流转上），让 Feature 一启动就进入自己的分支。

- **rules/flow-transitions.md**：Feature 流程触发点从第 19 行（方案待确认 → Dev Stage）移到第 11 行（PMO 初步分析 → Plan Stage）；敏捷需求流程对应在"PMO 分析 → 精简 PRD 编写"触发；Micro 流程在"PMO 分析 → Micro 变更说明"触发（分支名用 `chore/*`）
- **stages/plan-stage.md**：新增 §Worktree 集成段（触发时机 / auto 命令 / state.json 写入 / 降级链），前置依赖增补 "worktree 已创建切换" 条款
- **stages/dev-stage.md**：§Worktree 集成改为"校验存在 + 必要时补建"；补建场景（路径缺失 / 分支不匹配）作为异常分支保留，触发时写 WARN 到 state.json.concerns
- **INIT.md**：修正 "Dev Stage 前按策略创建" → "Plan Stage 入口按策略创建"

### 为什么是 Plan Stage 入口而不是其他点

| 候选 | 评估 |
|------|------|
| ~~Dev Stage 入口~~（v7.3.7 前）| Plan/UI/Blueprint 产物已落 main，隔离迟到 |
| ~~PMO 初步分析之前~~ | 用户还没确认流程类型，可能跳流程（走 Bug / 问题排查），空建 worktree 浪费 |
| **PMO 初步分析确认后，Plan Stage 入口** ✅ | 流程类型已定，第一份产物（PRD）就入 feature 分支 |
| ~~按 Stage 动态切换~~ | 每阶段切 worktree 碎片化，state.json 记录复杂度爆炸 |

### 分支命名规范（v7.3.8 正式化）

| 流程 | 分支名 | worktree 路径 |
|------|--------|--------------|
| Feature | `feature/{子项目缩写}-F{编号}-{功能名}` | `../feature-{...}` |
| 敏捷需求 | `feature/{子项目缩写}-F{编号}-{功能名}`（同 Feature）| `../feature-{...}` |
| Bug 处理 | `bugfix/{子项目缩写}-B{编号}-{摘要}` | `../bugfix-{...}` |
| Micro | `chore/{Micro 摘要}` | `../chore-{...}` |
| 问题排查 | （按需，通常不建）| - |

### 降级链（auto → manual → off）

每档降级必须写 WARN 到 `state.json.concerns`：
- `auto` 失败（git 不可用 / worktree add 错误 / 磁盘不足）→ 降 `manual`
- `manual` 用户 2 次未响应 → 降 `off`
- `off` → 所有阶段在当前工作区执行，跨 Feature 约束回退为人工注意力（原 v7.3.7 行为）

### 不改动项（仍保留）

- **默认值** 仍为 `off`（降低新用户门槛；建议 1 未落地）——已启用 teamwork 的用户可显式改为 auto
- **清理时机** 仍在 commit+push 完成后，PMO 询问用户（不自动删）
- **命令规范** 仍用标准 `git worktree add/remove/list`

### 操作影响

- **新 Feature**：启动即进入 feature 分支，所有阶段产物自然隔离
- **进行中 Feature**（v7.3.7 及之前启动）：不做迁移，保持原路径完成
- **worktree=off 用户**：零影响，行为不变

## v7.3.7 —— PRD/Blueprint Codex 交叉评审 + Progress Log 实时轮询

本版解决两个独立问题：
1. Codex 交叉评审之前只存在于 Review Stage（代码审查），Plan Stage 的 PRD 和 Blueprint Stage 的 TC+TECH 缺少外部视角保底，导致同模型多角色评审的注意力盲点无法被捕获
2. v7.2 建立的 Progress Log 三段式协议声明"Subagent → 主对话无实时通道"——这是**反事实陈述**，文件系统本身就是天然的异步实时通道。主对话读 dispatch 文件可随时获取进度，无需宿主 API 支持

### 1) Codex 交叉评审扩展到 Plan / Blueprint Stage

- **新建 `codex-agents/prd-reviewer.toml`**：Plan Stage PRD 外部评审 agent，独立性通过产物 frontmatter (`perspective: external-codex` + `files_read` grep) 强制，`sandbox_mode = read-only`
- **新建 `codex-agents/blueprint-reviewer.toml`**：Blueprint Stage TC+TECH 外部评审 agent，Step 5 在 4 步内部闭环（QA TC → TC 评审 → RD TECH → 架构师评审）之后执行
- **新建 `templates/codex-cross-review.md`**（230 行）：6 项 checklist (C1-C6) 针对 PRD 和 TC+TECH 两个变体、YAML 输出 schema、PMO 整合流程（ADOPT/REJECT/DEFER 分类）、降级处理、成本治理
- **stages/plan-stage.md**：多视角评审 4 → 5（加 Codex），新增 pmo-internal-review.md 作为 dispatch 前置（≥3 条实质 finding），PRD-REVIEW.md 尾部加「Codex 交叉评审整合」section
- **stages/blueprint-stage.md**：4 步闭环后追加 Step 5 Codex 交叉评审；TC-REVIEW/TECH-REVIEW 分别 append Codex 整合段；独立性 grep 校验加入机器可校验清单
- **templates/review-log.jsonl**：stage 枚举新增 `plan-codex-review` / `blueprint-codex-review`；补两者建行规则 + 示例行
- **codex-agents/README.md**：索引表增补两行

### 2) Progress Log 升级：四段式协议，支持运行中轮询

- **templates/dispatch.md Progress Log 段修订**：
  - 双重目的明确：运行中（主对话并发 Read）+ 运行后（PMO 时间轴回放）
  - 🔴 新增 **Append 语义硬规则**：`f.write() + f.flush() + os.fsync()` / shell `>>` / Edit 工具，禁止 buffered I/O 导致主对话读到空段误判卡死
  - 反模式表新增 2 条：buffered append、主对话绕过 Progress Log 读 session JSONL
- **templates/dispatch.md PMO 使用流程新增 Step 2.5（Subagent 运行中 — 主对话按需轮询）**：
  - 触发条件：用户问进度 / >5min dispatch / 并行多路
  - 读法：offset 跳到 Progress Log 段 + 增量对比
  - 节奏上限：用户触发即读，不建议 <10s tight loop
  - 🔴 显式禁止读 subagent session JSONL 当进度源（格式不稳定、非协议产物）
- **设计原则 #8 修订**：三段式 → **四段式**（前置预声明 / 中途自述 / 运行中轮询 / 事后回放）；删除"无实时通道"的反事实陈述
- **agents/README.md §2.5 + §五 Progress 可见性协议**同步修订：四段式协议、flush 语义、运行中轮询明细（相同修订在两个文件落地保证一致）

### 为什么要纠正"无实时通道"陈述

v7.2 起的原版陈述是基于宿主 Task/Agent API 同步阻塞推出的。这个推论本身没错——宿主 API 确实同步。但结论错了：**Subagent 和主对话共享文件系统**，Subagent 写 dispatch 文件、主对话随时 Read 同一文件，这就是异步实时通道。v7.3.7 前用户问"Subagent 现在到哪步了？"时，主对话会引用不存在的"规范禁止读 transcript"搪塞，实际上协议允许的正确操作是 **Read dispatch 文件的 Progress Log 段**。本版把这个隐含能力显式化为协议条款。

### 操作影响

- **Subagent 作者**：原有 Progress Log 逻辑照跑，仅需保证 append 时 flush（Python 加 `f.flush(); os.fsync(f.fileno())`；shell/Edit 天然满足）
- **主对话 / PMO**：用户问进度时可直接 `Read {dispatch 文件} → offset=Progress Log 段` 返回增量；并行 dispatch 依次读 N 个文件
- **Plan / Blueprint Stage 执行**：内部评审结束后多一步 Codex dispatch + 整合（预估 +5-10min），Codex 不可用按 agents/README.md §三 三选一降级

## v7.3.6 —— 多决策点支持：数字决策点 + 字母选项（`1A 2B`）

背景：v7.3.5 单决策点编号化后，实际使用中遇到**一个暂停点需要同时确认多个独立决策**的场景（如 PRD 评审收尾时「PRD 通过？」+「排期方案？」同时浮现）。v7.3.5 没定义多决策点格式，AI 自发用 `①②③` 分隔决策点，但圆圈数字需要输入法切换，用户打字不便。

本版固化多决策点格式：**决策点用数字（1./2./3.），选项用字母（A./B./C./D.），用户回复 `1A 2B` 这种组合**。

- **RULES.md 暂停输出规范第 2 条扩展**：
  - 2.1 单决策点（不变）：选项 1/2/3/4 编号
  - 2.2 多决策点（新增）：决策点用 `1.` `2.` `3.` 分隔，内部选项用 `A.` `B.` `C.` `D.`，用户回 `1A 2B`
  - 2.3 何时合并 vs 拆分：同时到达且独立 → 合并；后者依赖前者结果 → 拆分；上限 3 个决策点
  - 2.4 打字友好性原则：优先英文键盘直接敲出的字符，禁止 ①②③ / 罗马数字 / emoji 编号
- **模糊确认处理更新**：支持 `1A 2B` / `1A2B` / `1a 2b`（大小写不敏感）解析；数量不匹配 → 回问补齐
- **SKILL.md 红线 #10 摘要补充**：明确单决策点 vs 多决策点的编号字符规则
- **正反例对比新增**：反例 2 展示 `①1 ②2` 为何被禁；正例 2 展示 PRD+排期实际场景用 `1A 2B`

### 用户打字成本对比

| 格式 | 示例 | 字符数 | 输入法切换 |
|------|------|--------|-----------|
| v7.3.5 单决策 | `1` | 1 | 否 |
| v7.3.6 多决策（2 项）| `1A 2B` | 5 | 否 |
| ❌ 禁止（圆圈）| `①1 ②2` | 5 但需切换 | **是** |

多决策点使用指引：
```
⏸️ 请确认以下两件事（回复 "1A 2B" 这种组合即可）

1. PRD 是否通过：
   A. 通过 ← 💡 推荐
   B. 修改某条
   C. 忽略某条（需说明理由）
   D. 其他指示

2. 排期方案：
   A. 并行推进 ← 💡 推荐
   B. F003a 优先
   C. F013 优先
   D. 其他指示

回复示例：`1A 2A` 双采纳 / `1A 2B` / `1B 2A` / 自然语言
```

非暂停点文本（如 arch-code-review 的 ①②③ 路径标签、roadmap 验收条件编号）不受影响——本规则只管"用户需要打字回复"的暂停点格式。

### 单决策点禁止套多决策壳（v7.3.6 后补反例 3）

AI 引入多决策点格式后可能过度泛化，把**单决策点**也套 `1. {决策} / A./B./C.` 壳，让用户要回 `1A`。硬规则明确：**只有 ≥2 个独立决策点**才启用数字+字母格式；1 个决策就是 1 个决策，直接数字选项。

```
❌ 反例 3：
⏸️ 是否同步 DEPENDENCY-REQUESTS.md DEP-003？
1. 是否同步 DEPENDENCY-REQUESTS.md DEP-003？
   - A. 立即修正（💡 推荐）
   - B. 暂缓
   - C. 其他指示
（外层 "1." 是虚的 + 用户要回 `1A`）

✅ 正例 3：
⏸️ 请选择（回复数字即可）
1. 立即修正 DEPENDENCY-REQUESTS.md DEP-003 ← 💡 推荐
2. 暂缓（保留文档现状）
3. 其他指示
（用户回 `1` 完事）
```

## v7.3.5 —— 暂停点选项编号化（用户回复数字即可）

背景：用户观察到当前暂停点用描述式选项（`- 跳过（推荐）` / `- 跑 Browser E2E`），用户需要打字回复，不如直接敲数字快。本次改为所有可选项编号化（1/2/3...），用户回复数字即直达对应动作。

- **RULES.md「暂停输出规范」加第 2 条硬规则**（选项编号化）：
  - 所有可选项必须以 `1/2/3...` 编号列出
  - 第一项是 PMO 推荐（与 💡 建议 一致，标注「💡 推荐」）
  - 最后一项始终为「其他指示（自由输入）」
  - 提示语统一："⏸️ 请选择（回复数字即可）"
  - ❌ 禁止描述式选项（`- 跳过` / `- 跑 E2E`）
  - ❌ 禁止用字母（A/B/C）—— 统一数字
  - 模糊确认处理更新：用户回纯数字 → 直接映射到对应选项执行
  - 附"反例 vs 正例"对比
- **SKILL.md 红线 #10 微调**：明确"所有可选项必须编号列出，用户回数字即可"
- **roles/pmo.md 更新具体模板**：
  - PM 验收 + commit + push 合并暂停点：1-4 编号（推荐 1 / 本地 commit / 修复 / 其他）
  - Test Stage 前置确认：A/B/C → 1/2/3（立即执行 / 延后 / 跳过 / 其他）
- **FLOWS.md 问题排查流程**：选项改编号化
- **RULES.md §四流转链 + Test Stage 相关段**：A/B/C 全部替换为 1/2/3
- **STATUS-LINE.md**：A/B/C 提及改数字

核心体验变化：

```
❌ v7.3.4 前（用户要打字）：
⏸️ 请回复
- 跳过（推荐，直接 PM 验收）
- 跑 Browser E2E
- 其他指示

✅ v7.3.5（用户回数字）：
⏸️ 请选择（回复数字即可）
1. 跳过 Browser E2E，直接进入 PM 验收 ← 💡 推荐
2. 跑 Browser E2E（+15-25 min）
3. 其他指示（自由输入）
```

用户可回 `1` / `2` / `3` 或自然语言覆盖默认。打字量从一串降为一个字符。

注：现存 Feature 目录内可能已有按旧模板写的暂停点，不回溯修改；PMO 下次输出暂停点时按新模板即可。

## v7.3.4 —— 暂停点压缩（P0）：UI+全景合并 + 验收+commit+push 合并

背景：v7.3.3 跑 Feature 发现典型流程有 6-8 个暂停点，反复打断用户。前期讨论后确认走「方案 A：批量确认」，本次是 P0 阶段：合并两组暂停点（UI+全景、PM 验收+commit+push）。核心原则不变——**人类在关键节点把关**，但关键节点更集中、更聚焦。

### 合并 1：UI Design + Panorama Design → 一个「设计批」暂停点

**原因**：Feature UI 和全景增量同步是同一次设计讨论的两面（风格/配色/布局/语言对齐），分两次确认让用户反复打断。

- **重构 stages/ui-design-stage.md**：
  - 职责扩展为"Feature UI + 全景增量同步"一次性产出
  - 🔴 全景是产品真相，修改必须谨慎：默认增量合并（append / modify-in-place），禁止重写
  - 新增硬规则：
    - 对全景的任何修改必须在 sitemap.md 添加标红注释 `<!-- 🟡 {日期}: {FeatureID} 变更摘要 -->`
    - 执行报告必须列出全景 diff（sitemap 页面清单 + overview.html DOM 差异摘要）
    - 不允许删除现有页面或导航（属于 Feature Planning 范畴）
    - 结构性变更红线（删页面/重构导航/改核心业务流程状态机）→ DONE_WITH_CONCERNS，建议走 Planning
  - Output Contract 新增「全景同步状态」必填字段（同步了 / 显式跳过，二选一）
- **重构 stages/panorama-design-stage.md**：
  - 定位收窄为"Feature Planning 流程的全景重建模式"专用
  - Feature 流程不再触发本 Stage
  - 保留差异清单、风险提示、用户授权必达等硬规则
- **flow-transitions.md 更新**：Feature 流程的 UI 待确认 / 全景待确认 两行合并为「设计批 待确认」一行

### 合并 2：PM 验收 + commit + push → 一个合并暂停点（3 选 1）

**原因**：PM 验收通过 → 手动问用户是否 commit → 手动问是否 push，三步是连续决策，合并一个暂停点更顺。
**原则**：PMO 可以自动 commit（本地），**push 由用户决定**（保留用户控制远程推送的权力）。

- **roles/pmo.md 新增「PM 验收 + commit + push 合并暂停点」章节**：
  - PMO 在 PM 完成验收后自动执行本地 commit（含所有 Feature 产物 + 规范的 commit message）
  - 合并暂停点给用户 **3 选 1**：
    - 1️⃣ ✅ 通过 → 自动 commit + push（推到 origin/{branch}）
    - 2️⃣ ✅ 通过 → 仅本地 commit，不 push（用户稍后手动推送）
    - 3️⃣ ❌ 不通过 → 补充信息，回到对应阶段修复
  - push 失败不吞错：⏸️ 报告原因让用户手动处理
  - 3️⃣ 修复派发规则：按问题类型回退到 Review / Test / Plan / UI Design 对应 Stage；commit 保留不 revert；每轮修复 append 新 commit + 新 retry 记录
- **RULES.md §七 Git 提交规则升级**：
  - 从"用户要求时提交"改为"PM 验收通过后 PMO 自动 commit"
  - commit 产物清单扩充（含 state.json / review-log.jsonl / dispatch_log/ / retros/ 等审计产物）
  - commit message 模板标准化（含 AC 覆盖 / Review 通过情况 / 测试通过情况 / 耗时偏差摘要）
  - 🔴 push 硬规则：PMO 禁止自动 push；必须用户显式选择；禁止 push --force 到主分支
- **flow-transitions.md 更新**：Feature 流程的「PM 验收 → ✅ 已完成」改为「PM 验收 → 验收+commit+push 待处理 → ✅ 已完成」
- **完成报告模板新增「📦 Commit & Push 状态」段**：记录 commit hash / 分支 / push 状态
- **state.json schema 扩展（v7.3.4）**：
  - `_schema_version` 升级到 v7.3.4
  - `_instructions.stage_enum_v7_3_4`：Feature 流程合法 current_stage 枚举
  - `_instructions.commit_push_tracking`：stage_contracts.pm_acceptance 新增 commit_hash / push_status 字段

### 暂停点数量变化

```
改前（v7.3.3 / 典型 Feature）：6-8 个暂停点
  流程确认 + PRD + UI + 全景 + 方案 + Test 前置 + Browser E2E? + PM 验收 + push?

改后（v7.3.4 / 典型 Feature）：4-5 个暂停点
  流程确认 + PRD + 设计批(UI+全景) + 方案 + [Test 前置] + [Browser E2E?] + 验收+commit+push(3 选 1)
  （方括号是按 localconfig / TC 标注自动判断，多数情况不打扰用户）

典型简单 Feature（无 UI）：3 个暂停点
  流程确认 + PRD + 方案 + 验收+commit+push(3 选 1)

数量砍 30-50%，保留的是真正需要人类把关的契约核心。
```

### 未动的（保留 P1/P2 观察后再决定）

- 方案 A 的 #5（Blueprint 按复杂度决定暂停）— P2，风险相对高，等 P0 跑几个 Feature 验证
- 方案 A 的 #6（Test Stage 前置配置化）— P1，先观察用户对 A/B/C 三选一的实际选择分布
- 其他非压缩类改进（PMO 拆分、validator 等）— 前几轮讨论否掉了，不做

### 文件变更

- `skills/teamwork/stages/ui-design-stage.md`（重构：扩展为 UI + 全景增量）
- `skills/teamwork/stages/panorama-design-stage.md`（重构：仅保留全景重建模式）
- `skills/teamwork/rules/flow-transitions.md`（Feature 流程合并行）
- `skills/teamwork/RULES.md`（§四 Feature 流转逻辑 + §七 Git 提交规则升级）
- `skills/teamwork/FLOWS.md`（阶段链 + 流程步骤描述）
- `skills/teamwork/roles/pmo.md`（新增「PM 验收 + commit + push 合并暂停点」章节 + 完成报告加 Commit & Push 状态段）
- `skills/teamwork/templates/feature-state.json`（schema v7.3.4 + 新字段说明）

## v7.3.3 —— Stage 耗时度量闭环

背景：之前 dispatch.md 有预估（"预计 20-30 分钟"）但 Stage 结束没统计实际耗时。v7.3 改造完成后无法用数据验证效果，只能凭感觉判断"是快了还是慢了"。本次补齐耗时度量闭环，让每个 Feature 跑完自动有数据可复盘。

- **state.json schema 扩展**（templates/feature-state.json）：
  - `stage_contracts[stage]` 新增 `started_at` / `completed_at` / `duration_minutes`
  - `executor_history[]` 每条扩展为 `started_at / completed_at / duration_minutes / estimated_minutes / variance_pct / dispatches_count / retry_count / user_wait_seconds`
  - `planned_execution[stage]` 新增 `estimated_minutes` 字段（来自 AI Execution Plan）
- **review-log.jsonl schema 扩展**（templates/review-log.jsonl）：
  - 新增 6 字段：`started_at / duration_minutes / estimated_minutes / variance_pct / dispatches_count / retry_count / user_wait_seconds`
  - 示例更新为含耗时数据的完整行
  - 新增字段计算规则说明
- **AI Execution Plan 扩展为 4 行**（SKILL.md 「AI Plan 模式规范」）：
  - 新增第 4 行 `Estimated: {N} min`
  - AI 基于本 Feature 规模（AC 数、文件数）动态估算
  - 3 个典型示例全部更新
- **PMO 阶段摘要加耗时行**（roles/pmo.md）：
  - 每次 Stage 完成后的 PMO 摘要必须包含「⏱️ 实际耗时：N min（预估 M min，偏差 ±X%）」
  - 偏差 > +50% 自动加 ⚠️ 标识；偏差 < -30% 加 🟢 标识（预估过保守）
- **Feature 完成报告加耗时统计章节**（roles/pmo.md / RULES.md 8️⃣-D）：
  - 耗时统计表：每行一个 Stage + 合计（预估/实际/偏差/dispatches/retry/用户等待）
  - 耗时分析段：超预估 Stage 列表 + 客观原因 + 可操作优化建议
  - 区分 AI 实际耗时 vs 用户等待时间
- **各 stages/*.md 加 Expected duration baseline**：
  - plan-stage: 20-40 min（主对话）/ 15-20 min（Subagent）
  - blueprint-stage: 25-45 min（主对话）/ 30-60 min（Subagent）
  - blueprint-lite-stage: 8-15 min
  - ui-design-stage: Subagent 20-40 min / 主对话 8-15 min
  - panorama-design-stage: 增量 15-25 min / 重建 30-50 min
  - dev-stage: 主对话 ≤3 文件 15-25 min / Subagent 中等 30-60 min / 大改 60-120 min
  - review-stage: hybrid 10-20 min（三路并行墙钟）/ 全 subagent 15-25 min
  - test-stage: hybrid 15-30 min（环境 2-5 + 集成 5-15 + API E2E 10-25）
  - browser-e2e-stage: 每场景 2-3 min，总计 10-20 min
- **retros/*.md 模板加耗时度量段**（templates/retro.md）：
  - §1.1 耗时度量表（从 state.json.executor_history 聚合）
  - 跨 Feature 趋势分析：多个 retros 对比可发现规律（哪个 Stage 总是超预估）
- **RULES.md 8️⃣-D 新增**：Feature 完成报告必须输出耗时统计，不得跳过

核心收益：
- 每个 Feature 自动产出耗时数据，不再靠感觉判断
- 多个 Feature 跑完后可做横向对比（"Blueprint 总是超预估" → 设计有问题）
- Retro 从"主观经验记录"变成"数据驱动改进"
- v7.3 系列改造的净效果有数据可测（本轮加字段，下一个真 Feature 跑完即有数据）

Micro 流程不强制输出耗时（本身已是最短路径，加统计反成仪式）。

## v7.3.2 —— STATUS.md 废弃，state.json 成为 Feature 目录唯一状态文件

背景：v7.3 引入 state.json 做机读权威源，但保留 STATUS.md 作为"人读视图 + compact 恢复锚点"，导致字段重叠、双源头维护、恢复规则歧义。v7.3.2 彻底砍掉 STATUS.md，让 state.json 同时承担机读权威和人读详情（JSON 本身可读），ROADMAP.md 继续承担全局人读视图。

- **state.json 位置迁移**：从仓库根 `.teamwork/state/{feature_id}.json` 移到 `{Feature}/state.json`
  - 和 PRD/TC/TECH 等 Feature 产物同目录，单 Feature 查询无需跨目录
  - 跨 Feature 聚合依然可行（glob `docs/features/*/state.json`）
- **STATUS.md 废弃**：
  - `templates/status.md` 删除
  - `TEMPLATES.md` / `templates/README.md` 索引移除 status.md，新增 feature-state.json 和 verify-ac.py
  - 新 Feature 不再创建 STATUS.md，state.json 承担原职责
- **遗留 STATUS.md 处理**（向后兼容）：
  - 不删除已有文件（保留历史）
  - PMO 不再维护它
  - state.json 不存在但 STATUS.md 存在 → PMO 基于 STATUS.md 信息初始化 state.json 后忽略
- **规则更新**（所有对 STATUS.md 的引用全面替换）：
  - `SKILL.md` 红线 #1 / #14 / 热路径索引 / 文件索引
  - `RULES.md` §四流转链 / 功能完成 8️⃣ / 抽查规则 / 角色交接 / PMO 摘要更新
  - `rules/gate-checks.md` 原「STATUS.md 流转约束同步更新」段改写为「state.json 流转状态同步更新」
  - `rules/naming.md` Feature 目录标准结构 + BG 反向引用字段 + CHG 记录位置
  - `roles/pmo.md` state.json 维护规范全段重写（位置、流转前后、compact 恢复、遗留文件处理）
  - `roles/pm.md` 功能目录初始化描述
  - `stages/dev-stage.md` worktree 记录位置
  - `CONTEXT-RECOVERY.md` 恢复决策树 / Feature 看板 / compact 快速路径
  - `STATUS-LINE.md` compact 恢复快速路径 / 待确认恢复规则
  - `INIT.md` 扫描进度 / Feature 目录结构 / 红线 #1
  - `templates/feature-state.json` 位置字段 + 替代说明
  - `templates/roadmap.md` / `templates/teamwork-space.md` 引用更新
  - `codex-agents/hooks.json` 描述更新
- **验证**：
  - `grep -r "STATUS\.md"` 剩余都是 v7.3.2 明确标注的"遗留说明"或"废弃说明"
  - `grep -r "\.teamwork/state"` 零命中（位置已全迁移）
  - `templates/status.md` 文件已删除

简化效果：
- Feature 状态维护点从 4 处降到 3 处（state.json + review-log.jsonl + ROADMAP.md）
- 双权威冲突彻底消除
- Compact 恢复单一锚点（state.json），不再需要和 flow-transitions.md 交叉校验 STATUS.md

## v7.3.1 —— v7.3 收尾

前序 v7.3 改造完成后发现三个未对齐点，本次小版本收尾修复，不引入新机制。

- **agents/README.md §一 速查表与 AI Plan 模式对齐**（消除双权威冲突）：
  - 章节标题从「执行方式决策（PMO 必读）」改为「执行方式参考（默认推荐 + 判断原则）」
  - 删除"PMO 查下表决定 / 禁止凭感觉判断"的硬绑定语言
  - 表头从「执行方式」改为「默认 approach」，标识 🤖/主对话 改为 main-conversation/subagent/hybrid/AI 自主
  - 删除"🔴 禁止降级 Sonnet"等与"AI 自主"冲突的硬规则
  - 新增"AI Plan 偏离指引"章节，说明何时偏离默认 approach
- **Execution Plan 从 6 字段精简为 3 行核心**（去除重复仪式）：
  - Plan 只保留 Approach / Rationale / Role specs loaded 三项
  - Steps / Expected Output / Key Context 由各 Stage 契约、dispatch 文件、产物 frontmatter 承载（不重复）
  - SKILL.md 新增 3 个典型示例（Plan Stage / Dev Stage / Review Stage）
  - 每个 Feature × 8 Stage 的仪式文字量从 ~160 行降至 ~24 行
- **各 Stage 的 Plan 指引段落精简**（单一权威指向）：
  - plan/blueprint/blueprint-lite/ui-design/panorama/browser-e2e 的"AI Plan 模式指引"压缩到 2-3 行，指向 SKILL.md 和 agents/README.md §一
  - dev/review/test 保留本 Stage 特殊的 approach 判断逻辑（规模/复杂度/三视角独立性/环境独立性）
  - SKILL.md 中原"典型 approach 选择指引"表删除（和 agents/README.md §一 重复）
- **verify-ac.py 从示例脚本落地为可直接跑的标准实现**：
  - 新增 `templates/verify-ac.py`（Python 3 标准库实现，无 yq / 外部工具依赖）
  - 自带 YAML frontmatter 简化解析器，同时兼容 PyYAML（如已装）
  - 自测覆盖：文件缺失 / 覆盖通过 / 覆盖不完整 三种场景 exit code 分别为 1 / 0 / 3
  - 可直接从 `{SKILL_ROOT}/templates/verify-ac.py` 调用，项目无需复制
  - 删除旧 `templates/verify-ac.example.sh`（示例化处理太弱，实际没人落地）
  - prd.md / tc.md / blueprint-stage.md 所有引用更新

## v7.3
- **Stage 三契约化（规范契约，不规范过程）**：
  - 每个 Stage 文件重构为 Input Contract / Process Contract / Output Contract 三段式
  - 删除所有 Stage 对"必须 Subagent 执行"的硬绑定
  - 执行方式（主对话 / Subagent / 混合）由 AI 在 Plan 模式每次 Stage 开始时自主规划
  - 多视角独立性从"规则要求"转为"产物结构约束"：三份 review 产物独立 generated_at、独立 files_read、不互相引用（grep 校验）
  - 覆盖文件：stages/{plan, blueprint, blueprint-lite, dev, review, test, ui-design, panorama-design, browser-e2e}-stage.md 全部重写
- **AI Plan 模式规范**（SKILL.md 新增章节 + 红线 #14）：
  - AI 必须在每个 Stage 开始前输出 Execution Plan 块（含 Approach / Rationale / Steps / Expected Output / Loaded Role Specs & Standards / Key Context）
  - Plan 写入 state.json.planned_execution[stage]，审计可追溯
  - 硬规则：角色切换时必须 cite 对应 roles/*.md 的关键要点（防止凭记忆执行）
  - 实际执行偏离 Plan 时必须更新 Plan + 记录偏离理由
- **AC↔Test 结构化绑定（消除需求→代码漂移根源）**：
  - PRD.md 头部新增 YAML frontmatter：acceptance_criteria[]（id/description/priority/test_refs/ui_refs）
  - TC.md 头部新增 YAML frontmatter：tests[]（id/file/function/covers_ac/level/priority）
  - 新增 templates/verify-ac.example.sh 作为覆盖校验脚本示例
  - Output Contract 硬要求：每条 PRD AC 至少有 1 个 covers_ac 测试 + 所有测试通过
- **主对话产物协议（补齐 Subagent 协议反面）**：
  - agents/README.md §六 新增：主对话直接执行任务的产物落盘规范
  - YAML frontmatter 必填：executor/task/feature/started_at/completed_at/status/files_read/concerns
  - 覆盖场景：Plan Stage PRD 起草、Blueprint TC/TECH、Review 架构师视角、Test 环境启动、Browser E2E、UI 还原验收、PM 验收
  - templates/dispatch.md 顶部加适用范围声明：仅适用于 Subagent dispatch
  - review-log.jsonl schema 扩展：新增 executor / artifact_path / dispatch_file 字段
- **state.json 机读状态机**（模板 + PMO 维护规范）：
  - 新增 templates/feature-state.json 定义 Feature 级流转状态机
  - 位置：.teamwork/state/{feature_id}.json
  - 字段：current_stage / completed_stages / legal_next_stages / stage_contracts（input/process/output satisfied）/ planned_execution / blocking / executor_history / worktree
  - roles/pmo.md 新增「state.json 维护规范」：流转前读、流转后写，机器校验 target ∈ legal_next_stages
  - 与 STATUS.md 的关系：state.json 是机读权威源，STATUS.md 是人读视图，compact 恢复以 state.json 为准
- **流程确认必须展示步骤**（SKILL.md 红线 #15）：
  - PMO 初步分析中，选定流程类型后必须给出「本流程的完整步骤描述」（阶段链 + 每步做什么 + 暂停点）
  - 用户基于步骤描述确认流程类型
  - 不给步骤描述直接问「走什么流程」= 违规
- **Micro 流程放宽**（FLOWS.md §六 + SKILL.md 红线 #1）：
  - PMO 可直接改代码（白名单内零逻辑变更），不强制 Subagent，也**不要求 Execution Plan**
  - 真正轻量通道：只保留 PMO 分析 → 用户确认流程（含步骤描述）→ PMO 直接改 → 用户验收 的最小闭环
  - 改动限于 Micro 白名单（零逻辑变更：资源/文案/样式/配置常量/注释）
  - 事后审计：检查准入条件、逻辑变更混入、阶段链完整性
- **RULES.md §四流转链描述与实际实现对齐**：
  - 删除滞后的"Dev 含架构师 CR"、"Test 含 QA 审查"、"Codex 独立 Stage"描述
  - 更新为 v7.3 契约化后的准确流转链（Dev → Review 三路独立 → Test 环境独立 → Browser E2E → PM 验收）
- **status.md 显示名映射动态化**：
  - 显示名图标根据 state.json.planned_execution[stage].approach 动态渲染
  - 💬 = main-conversation / 🤖 = subagent / 💬🤖 = hybrid
  - 默认推荐列标注每个 Stage 的推荐 approach（但 AI 可按场景创新）
- 不做的改动（保留）：
  - 六种流程分类不变
  - dispatch 文件协议（v7.2）保留，Subagent 场景继续用
  - Key Context 6 类结构保留，在主对话任务中同样必需
  - Feature Planning / 工作区级 Planning / 问题排查流程规则不变

## v7.2
- Subagent Progress 可见性三段式协议（主对话 TodoWrite 预声明 + Progress Log 实时自述 + 事后回放）：
  - 背景：通用宿主 API 下 Subagent → 主对话无实时通道（同步阻塞模型），用户主对话黑盒等待体感差；plan 模式 / TodoWrite 在 Subagent 内不回流主对话
  - 三段式替代实时流：
    - 阶段 1（PMO 前置）：dispatch 前在主对话 TodoWrite 预声明 Subagent Step 列表（从 stage 文件「执行流程」抽取，粒度对齐 Expected deliverables）
    - 阶段 2（Subagent 中途）：执行中实时 append dispatch 文件的 Progress Log 段，记录 step-start / step-done / step-concern / step-blocked / degradation / subagent-done 等事件（硬规则：禁止最后一次性补全）
    - 阶段 3（PMO 事后）：读 Progress Log 转成主对话时间轴回放，step-start/done 映射为 TodoWrite 状态更新，异常事件高亮
  - templates/dispatch.md 新增 `## Progress Log` 必填段（含必填事件类型表 / 模板段 / 反模式）+ 设计原则第 8 条「Progress 可见性双保险」+ PMO 使用流程 Step 1/Step 3 新增 TodoWrite 预声明 + Progress Log 回显步骤
  - agents/README.md §二 2.5 新增「Progress Log 实时维护」硬规则 + §四 字段责任划分表新增 Progress Log 行（Subagent 填）+ §四 启动前自问新增「主对话 TodoWrite 预声明」检查 + §四 Subagent prompt 极简结构新增 Progress Log 要求（规则 3）+ §四 完成后处理新增「读 Progress Log 转主对话时间轴」步骤 + 新增「Progress 可见性协议」完整章节（三段式图示 + 用户体验目标对照 + 可选切分粒度策略）
  - 切分 Subagent 粒度作为可选加强（不默认）：满足"Stage >15 分钟 + 无强上下文依赖 + 用户明确敏感"三条件时启用
- API E2E 脚本化改造（从"逐条 curl"到"脚本驱动"）：
  - 核心变化：Subagent 不再一条条 curl，而是把 TC.md 场景翻译成 Python 脚本 → 执行 → 解读 JSON 输出 → 生成报告
  - 收益：Token 消耗从 N 场景 × 2 轮 LLM 降到 1 次生成 + 1 次解读；脚本可重跑（RD 修复后 `python api-e2e.py` 即可，无需再发 Subagent）；脚本可进 CI；脚本落盘为 Feature 交付物
  - 脚本位置：`{子项目}/tests/e2e/F{编号}-{功能名}/api-e2e.py`（+ README.md 记录 env 要求）
  - 脚本语言：Python 3.10+ + requests（禁止 bash+curl 组合——可移植性差）
  - 断言硬要求：每场景至少覆盖 4 类断言（status / body / DB / 副作用）中的 2 类；所有环境值走 env var；DB 校验必须走只读 DSN
  - 脚本标准化：函数名 `test_API_E2E_{N}_{描述}`，Runner 统一捕获异常输出 JSON，exit code 体现整体结果
  - e2e-registry 联动：P0/P1 级 case 必须注册，REGISTRY.md 新增「脚本路径」「最后跑通」两列
  - agents/api-e2e.md 整体重写：新增 §五脚本生成规范 + §六落盘注册流程 + §七新报告格式 + §九降级处理
  - agents/integration-test.md 顶部澄清：集成测试 = 调用既有测试命令（不生成脚本）；API E2E = 独立脚本（另一种职责），🚫 集成测试不做 curl 级黑盒
  - stages/test-stage.md §六红线新增「API E2E 脚本化交付」5 项硬要求 + Expected deliverables 明确脚本 + registry 更新
  - templates/e2e-registry.md 表结构增加「脚本路径」「最后跑通」列，api 类 case 必须填脚本路径（browser 类留 `-`）
- Key Context 结构化字段（dispatch 文件增强）：
  - 核心思想：PMO 是唯一贯穿全流程的角色，它手里有 Subagent 读不到的关键信息（历史决策、跨 Feature 约束、历史陷阱、降级授权、优先级权衡、本轮聚焦点），必须结构化注入 dispatch 文件，而不是让 Subagent 自己推断
  - 位置：dispatch 文件新增「🎯 Key Context」section，6 类子字段（历史决策锚点 / 本轮聚焦点 / 跨 Feature 约束 / 已识别风险 / 降级授权 / 优先级容忍度）
  - 🔴 硬规则：PMO 必须逐项判断，**无则写「-」**（证明已判断），严禁留空或删字段；无判断痕迹 → Subagent 返回 NEEDS_CONTEXT
  - 反模式防范：只写 Subagent 从 Input files 里读不到的信息，禁止复制 PRD/TECH 摘要
  - INDEX.md 增加「关键约束」列，摘录最关键一条，便于人工审查时识别本 Feature 累积的历史决策/风险
  - templates/dispatch.md 新增 Key Context 完整模板 + 设计原则第 7 条
  - agents/README.md §四 4.1 字段责任表新增 Key Context 行 + PMO 启动前自问清单新增逐项判断项 + Key Context 硬规则段（含正反例）
- Dispatch 文件协议（文件化 Subagent 交接）：
  - 核心思想：每次 Subagent dispatch 生成一个 markdown 文件，文件即入参即审计记录，消除「PMO 构造 prompt 字符串」和「PMO 写 dispatch 日志」的重复劳动
  - 位置：`{Feature}/dispatch_log/{NNN}-{subagent-id}.md` + `INDEX.md` 汇总视图
  - Subagent prompt 从 100+ 行简化为 ~5 行（只指向 dispatch 文件路径 + append Result 要求）
  - 🔴 硬规则：未生成 dispatch 文件不得 dispatch / Subagent 必须 append Result 否则视为 FAILED / PMO 必须更新 INDEX
  - 未 append Result / 超时卡死 → PMO 接管写 Result（含 degradation WARN），降级主对话执行
  - 降级 WARN 日志直接写入 dispatch 文件 Result 区域，审计链完整
  - 并行 dispatch 各用独立文件（Batch 字段标同批次），重新 dispatch 新文件 + Previous 字段追溯
  - 跨宿主天然兼容：Claude Task / Codex agent spawn / Gemini 主对话 / 主对话降级都只需"读这个文件"
  - 新增 `templates/dispatch.md`（含完整字段定义 + INDEX 模板 + PMO 使用流程 + 生命周期）
  - agents/README.md §四 4.1 用「Dispatch 文件协议」替代原「Prompt 结构」章节；§四 4.2 启动前检查新增「dispatch 文件已生成」前置条件；§四 4.3 完成后处理新增 Result append 校验 + INDEX 更新
  - rules/naming.md 新增 dispatch 文件编号规则 + Feature 目录标准结构（含 dispatch_log/）
  - INIT.md 创建基础目录段新增 Feature 子目录说明
- 降级兜底 WARN 日志强制规范：
  - standards/backend.md §四 日志规范新增「降级兜底逻辑 WARN 日志规则」硬规则（含必须字段：降级原因 + 原路径 + 兜底路径 + 业务上下文，含反例示例，Code Review 缺失即阻塞）
  - standards/common.md CR 规范遵守检查新增降级 WARN 必检项
  - agents/README.md §四 dispatch 新增「降级兜底必须输出 WARN 日志」统一规范，覆盖 Subagent dispatch 失败、Codex CLI 不可用降级 Sonnet、宿主不支持 TodoWrite、worktree 不可用、hook 缺失等所有宿主兼容兜底路径
  - agents/README.md §五 BLOCKED/FAILED 升级策略标注 WARN 日志要求，静默降级明确定性为违反闭环验证红线
- 效率优化（减少流程税）：
  - Stage 内部子步骤简化 PMO relay：跨 Stage 保留完整校验，Stage 内部改用轻量标记（📌 Blueprint 1/4）
  - Subagent 输入改文件路径优先：减少 PMO 摘要转述的信息衰减，Subagent 自行读原文
  - Blueprint Stage 改为 Subagent 执行：4 步内部闭环，主对话 context 不被占用
  - 敏捷需求新增 BlueprintLite Stage（轻量蓝图：QA 简化 TC + RD 实现计划，无评审），替代原 3 步独立执行，Dev Stage 保持单一职责
- 叙事重构：从"虚拟团队"改为"角色视角 + 流程规范"定位
  - SKILL.md description: "AI Agent Team" → "AI-driven structured development process with role-based perspectives"
  - README 中英文同步更新：强调角色视角切换和质量门禁，而非团队协作
  - INIT.md 写入模板：从"多角色协作流程"改为"结构化开发流程"
- 跨宿主兼容（Claude Code / Codex CLI / Gemini CLI）：
  - 硬编码路径 `.claude/skills/teamwork/` → `{SKILL_ROOT}` 变量（~20 处）
  - INIT.md 宿主环境检测 + 指令文件自适应写入（CLAUDE.md / AGENTS.md / GEMINI.md）
  - agents/README.md §四 dispatch 抽象层（Task 工具 / Codex agent spawn / 主对话降级）
  - codex-agents/ 目录：6 个 Codex 自定义 agent toml 定义
  - TodoWrite 降级：宿主不支持时回退 markdown 进度块
  - hooks 双宿主：Codex 版去掉 PreCompact/PostCompact
  - install.sh 安装脚本：自动检测宿主 + 一键部署
  - SKILL.md 新增「宿主环境适配」章节

## v7.1
- 问题 10 清理：STATUS-LINE.md 阶段对照表 / templates/status.md 显示名映射 / agents/README.md 速查表 / gate-checks.md 示例 / 全局旧阶段名引用清理
- 问题 11 Worktree 集成：.teamwork_localconfig.md 新增 worktree 策略字段（off/auto/manual），INIT.md 启动检测，Dev Stage worktree 创建/清理生命周期，flow-transitions.md 标注 worktree 触发点

## v7
- 8 Stage 架构重构：
  - stages/ 目录（8 个 stage）：Plan / UI Design / Panorama Design / Blueprint / Dev / Review / Test / Browser E2E
  - agents/ 只保留任务单元规范（被 stage 引用，不被 PMO 直接 dispatch）
  - roles/ 保留 6 个角色定义
  - rules/ 保留转移表 + 门禁 + 编号
- Dev → Review → Test 三段式：Dev 纯开发+单测，Review 三路并行（架构师CR∥Codex∥QA审查），Test 并行（集成∥E2E）
- Plan Stage：PM 写 PRD + PL-PM 讨论 + 技术评审合并为一个 stage
- Blueprint Stage：QA 写 TC + TC 评审 + RD 技术方案 + 架构师评审合并为一个 stage
- Chain → Stage 全局重命名
- Codex Review 合入 Review Stage（不再独立 dispatch）
- Panorama Design Stage 从 UI Design Stage 拆出独立

## v6
- roles/ 与 agents/ 分离：ROLES.md（1,635 行）拆为 roles/ 目录（7 个角色文件）+ 索引（~25 行）
  - agents/ 只保留真正的 Subagent spec（6 个 + 子规范）
  - 主对话评审规范（prd-review / tc-review / arch-tech-review）合并到对应 roles/ 文件
  - 角色定义按需加载，PMO 不再需要读 1,635 行的 ROLES.md

## v5
- 新增第五种流程「敏捷需求」：轻量级流程适用于小改动
- 新增第六种流程「Micro」：零逻辑变更的最轻量通道（资源替换/文案/样式/配置常量），防止 PMO 因"改动太小"而越界写代码
- PMO 反模式补充：小改动决策树 + "自己做更快"反模式 + commit/push 必须用户验收
- PMO 预检分层体系（L1 基础/L2 测试环境/L3 E2E）：所有 Subagent dispatch 前必须完成对应级别预检（红线 #13）
- PMO 恢复/待命场景强制给出优先级建议：Feature 看板必须附 💡 建议 + 📝 理由，禁止只列状态让用户自行判断
- Pre-flight Check 合并到强制流转校验块：新增「📖 流转类型」必填字段（🚀自动/⏸️暂停/🔀条件），查表结果嵌入校验输出，消除两步分离导致跳过预检的问题
- 4 个轻量 Subagent 回归主对话执行：PRD 技术评审、TC 技术评审、架构师方案评审、QA Lead 质量总结改为 PMO 切换角色在主对话执行，减少冷启动开销提升速度（spec 文件保留作为角色规范）
- 新增 agents/README.md §一「执行方式速查表」：PMO 判断 Subagent vs 主对话的集中决策指引（含判断原则 + 全阶段速查表），热路径索引已添加入口
- P0 单一权威源重构：RULES.md 从 2,004 行精简到 ~1,645 行（-18%）
  - 转移表副本（99 行）→ 删除，权威源：rules/flow-transitions.md
  - 门禁校验格式（91 行）→ 删除，权威源：rules/gate-checks.md（同步更新为最新版含流转类型字段）
  - Bug 处理流程（177 行）→ 迁移到 FLOWS.md，RULES.md 改为引用
  - 暂停条件 4 个子章节合并为 1 个「暂停输出规范」（-99 行）
  - UI 变更规则 6 次重复压缩为 1 条（-55 行）
  - 编号规则（82 行）→ 迁移到 rules/naming.md
  - 最终结果：RULES.md 2,004 → 1,418 行（-29.2%）
  - PMO 热路径索引更新为指向拆分后的权威文件
- 阶段名消歧义重命名：PRD 评审→PRD 技术评审 / TC 评审→TC 技术评审 / 架构师 Review→架构师方案评审（88 处 / 22 文件），消除"执行步骤"与"用户确认"的命名混淆
- 状态行功能编号必填：Feature/敏捷/Bug/Micro 流程的功能/Bug 编号从可选改为必填
- 流转校验精简为 1 行：`📋 {A} → {B}（📖 {类型}，查 flow-transitions.md ✅）`，降低 PMO 跳过校验的成本
- QA Lead 质量总结环节移除：Verify Stage / Browser E2E 通过后直接进入 PM 验收，简化流程。角色从 8 个降为 7 个。敏捷需求砍掉环节从 7 个降为 6 个
- Designer 两步设计：Feature 流程中 Designer 拆为 Step 1（当前 Feature UI）+ Step 2（全景同步），各自独立确认
- Codex CLI 通用执行引擎移除，Codex CLI 仅用于独立 Codex Code Review 阶段（不可用时可降级 Sonnet 或跳过）
- TEMPLATES.md 拆分为 templates/ 目录（16 个独立模板文件）
- RULES.md 热路径拆分为 rules/ 目录
- INIT.md CLAUDE.md 注入段精简（红线改为索引引用）
- 前端开发规范大幅扩充
- Hooks 脚本健壮性改进（换行符 bug 修复、降级逻辑、超时调整）
- 规则去重：建立单一权威定义 + 引用模式
- 明确协作模型（单人 vs 多人）

## v4
- 中台子项目支持（business / midplatform）
- PL-PM Teams 讨论机制
- E2E 回归测试中心
- QA Lead 质量总结阶段
- 自下而上影响升级评估

## v3
- 业务架构与技术架构对齐方案落地
- Product Lead 三种工作模式
- CHG 变更记录机制
- Workspace Planning 流程

## v2
- 多子项目模式
- Hooks 自动化（SessionStart / PreCompact / Stop）
- 按需加载文件机制

## v1
- 基础 8 角色协作框架
- Feature / Bug / 问题排查 / Feature Planning 四种流程
