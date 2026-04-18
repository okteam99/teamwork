# Changelog

## v7.3.3（当前）—— Stage 耗时度量闭环

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
