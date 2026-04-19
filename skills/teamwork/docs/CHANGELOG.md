# Changelog

## v7.3.9 + P0 简化（当前）

> P0 是 v7.3.9 落地后的一轮"反刍"简化：抽取重复描述、收敛 preflight 暂停点、修正依赖安装时机表述。无破坏性变更，向前兼容 v7.3.9 state.json 与 localconfig。

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
