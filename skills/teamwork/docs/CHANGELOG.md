# Changelog

## v7（当前）
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
