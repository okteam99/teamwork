# Teamwork 初始化流程

> 🔴 每次 `/teamwork` 启动时必须按顺序执行「启动必做」3 步。
> 「按需加载」由各角色在执行阶段自行加载，不在启动时执行。
> 「首次初始化」仅在 teamwork_space.md 不存在时执行。

---

## 启动必做（每次，按顺序执行）

### Step 0: 解析 /teamwork 命令行（🔴 v7.3.9+P0-11 新增）

**解析规则（第一个 token 决定 AUTO_MODE）**：

```
/teamwork auto [需求]         → AUTO_MODE=true，需求 = "[需求]"
/teamwork auto 继续           → AUTO_MODE=true，继续进行中 Feature
/teamwork auto ship F{编号}   → AUTO_MODE=true，进入 Ship Stage（MR 模式 · v7.3.10+P0-15）
/teamwork [需求]              → AUTO_MODE=false（手动，默认）
/teamwork 继续                → AUTO_MODE=false
/teamwork force-init          → FORCE_INIT=true（v7.3.10+P0-17：忽略 version 缓存，强制全量校验 CLAUDE.md/AGENTS.md）
/teamwork init --force        → 同 force-init 别名
/teamwork（无参）              → AUTO_MODE=false，输出看板
```

**AUTO_MODE 作用域 = 单次命令周期**（仅本次 /teamwork 生命周期有效）：

```
├── 用户重新输入 /teamwork（不带 auto）→ AUTO_MODE 自动重置为 false
├── 运行中用户消息含「停 / 暂停 / manual / 等一下 / 先等等」→ 立即 AUTO_MODE=false，当前和后续 ⏸️ 恢复
├── 会话跨 compact 后 → AUTO_MODE 默认 false（需重新 /teamwork auto ... 开启）
└── 🔴 不写入 localconfig / state.json（不持久化，避免"以为关了其实没关"的事故面）
```

**AUTO_MODE=true 时 PMO 行为变更（速查）**：

```
🔴 元规则（P0-11-A）：暂停点需要的"决策内容"如果已被 auto 命令承载（「是否继续/恢复/启动」类）→ 豁免；
   若需新的业务判断 / 技术分歧 / 破坏性授权 / 红线处理 → 保留。

✅ 豁免（按 💡 自动推进，不等用户）：
├── 普通方案 / PRD / UI / TC / TECH 草稿 review 后流转
├── 阶段切换（Stage A → Stage B）
├── Plan Stage 入口 preflight（4 硬门禁全 ✅ 时）
├── dispatch 前检 / review 结果接受 / 摘要流转
├── 外部依赖已就绪 → 恢复流程（P0-11-A：auto 命令已承载"恢复"意图）
├── Planning / PL 模式最终汇总确认（P0-11-A：auto 命令已承载"推进"意图）
├── 🟡 Test Stage → Browser E2E Stage（P0-11-B：auto 默认跳过 Browser E2E，留痕后直接进 PM 验收）
└── 非强制保留的 ⏸️ 暂停点（见 flow-transitions.md 顶部豁免表）

🔴 强制保留（仍 ⏸️，不受 auto 影响）：
1. Ship Stage worktree 清理待确认（用户偏好不可替决）
2. 破坏性 git / DB 操作（force push / hard reset / drop 表 / 删分支）
3. 需求类型 / 使用流程识别有歧义或多候选
4. 15 条绝对红线触发时
5. 架构师 Review 输出 MUST-CHANGE
6. 用户消息出现「？/ 确认下 / 等我看看 / 核对一下」等意图不确定语气
7. Blueprint Stage / Review Stage concerns 需用户判断
8. Micro 流程「用户验收」和「升级确认」
9. PM 验收三选项
10. Ship Stage push FAILED（v7.3.10+P0-15：push feature 失败 → 用户 2 选 1）
11. Dev / Test Stage BLOCKED 或 FAILED / Review Stage FAILED
```

**反模式（P0-11-A 实战教训）**：
- ❌ auto 命令明说"推进到 Blueprint 完成"，却被中间"外部依赖恢复确认"卡住 → 把用户命令意图当空气
- ❌ 把所有 ⏸️ 都当强制保留 → auto 模式坍缩为手动模式，违反设计意图

**Browser E2E auto 默认跳过（P0-11-B 新增）**：
- `AUTO_MODE=true` + `TC.md` 含 Browser E2E AC → **默认跳过 Browser E2E Stage**，直接进 PM 验收
- 留痕：`state.json.stage_contracts.browser_e2e = {status: "SKIPPED_BY_AUTO", skipped_at, skip_reason}` + `review-log.jsonl` 追加一行
- PM 验收 / 完成报告必须显式标注「⚠️ Browser E2E 已按 auto 模式跳过」
- 例外（不跳过）：命令含「含 browser e2e / 带 e2e / run e2e」关键词、`TC.md required_even_in_auto=true`、手动模式

**跳过日志**：每跳过一个暂停点，PMO 输出一行 `⚡ auto skip: {决策简述} | 💡 {建议} | 📝 {理由}`，便于事后追溯。

📎 详见 `roles/pmo.md`「⚡ auto 模式暂停点豁免规则」+「🟡 Browser E2E auto 默认跳过」章节、`STATUS-LINE.md` 状态行 `⚡ AUTO` 徽章、`rules/flow-transitions.md` 顶部「auto 模式豁免速查」块。

---

### Step 1: 检测宿主环境 + 校验指令文件（🔴 最先做）

**Step 1.1: 检测宿主环境并设定 SKILL_ROOT**

```
检测当前 AI 工具：
├── 存在 Task 工具 + .claude/ 目录 → 宿主 = Claude Code
│   └── SKILL_ROOT = .claude/skills/teamwork
│   └── HOST_INSTRUCTION_FILE = CLAUDE.md
├── 存在 .codex/ 目录 或 codex 命令可用 → 宿主 = Codex CLI
│   └── SKILL_ROOT = .agents/skills/teamwork
│   └── HOST_INSTRUCTION_FILE = AGENTS.md
├── 存在 .gemini/ 目录 → 宿主 = Gemini CLI
│   └── SKILL_ROOT = .gemini/skills/teamwork（如支持）
│   └── HOST_INSTRUCTION_FILE = GEMINI.md
└── 均不匹配 → 宿主 = 通用
    └── SKILL_ROOT = 从 SKILL.md 所在目录推断
    └── HOST_INSTRUCTION_FILE = AGENTS.md（开放标准）

输出：「🔧 宿主环境：{宿主名} | SKILL_ROOT={路径}」
```

**Step 1.2: 校验宿主指令文件（🔴 v7.3.10+P0-17 版本缓存优化）**

🟢 v7.3.10+P0-17 引入**版本缓存机制**：复用本地已有的 `.teamwork_localconfig.md` 作缓存标志，版本一致直接跳过 CLAUDE.md / AGENTS.md 的 Read + 字符 diff，节省 ~65-75% 启动 token。

**Step 1.2-a：读取 skill 版本号**

```
读取 SKILL.md frontmatter 的 version 字段：
├── 找到（当前应为 7.3.10+P0-23）→ SKILL_VERSION = 该值
└── 缺失 / 无法解析 → SKILL_VERSION = null（降级为全量校验，输出一次 ⚠️ 提示）
```

**Step 1.2-b：读取本地版本缓存（复用 localconfig）**

```
读取 项目根/.teamwork_localconfig.md 的 teamwork_version 字段：
├── 文件不存在 → LOCAL_VERSION = null（首次 / 新 clone → 走全量）
├── 字段不存在 / 为空 → LOCAL_VERSION = null（旧版 localconfig → 走全量 + 本次写入）
├── 字段有值 → LOCAL_VERSION = 该值
└── 文件损坏 / 解析失败 → LOCAL_VERSION = null + ⚠️ 提示 + 走全量
```

**Step 1.2-c：版本比对 + 校验策略**

```
SKILL_VERSION 与 LOCAL_VERSION 比对：

├── ⚡ 一致（fast path · 99%+ 场景）
│   ├── 跳过 {HOST_INSTRUCTION_FILE} 的 Read 和逐字符 diff
│   ├── 输出：「⚡ CLAUDE.md 校验跳过（teamwork_version={VERSION} 命中缓存）」
│   └── 🔴 安全假设：上次启动已完成全量校验并写回 version，CLAUDE.md 已同步到该版本
│
├── 🔄 不一致 / null（full path · skill 升级 / 首次 / 降级场景）
│   ├── 执行全量校验（流程同 P0-17 前）：
│   │   ├── {HOST_INSTRUCTION_FILE} 不存在 → 创建并写入下方模板
│   │   ├── 存在 → 读取 `## Teamwork 协作模式` 段落，对照下方模板逐字符 diff（含空行/标点/emoji）
│   │   │   ├── 段落缺失 → 追加
│   │   │   ├── 🔴 任何字符差异（新增/删除/修改，无论多小）→ 替换为预期内容（漂移自愈）
│   │   │   ├── 完整匹配（bit-for-bit 一致）→ 不改文件
│   │   │   └── 禁止 AI 凭"大致差不多"判定跳过 —— 漂移检测语义就是严格 diff
│   │   └── 🔴 多指令文件（CLAUDE.md + AGENTS.md 并存）→ 每个文件都写入相同内容
│   ├── 回写：更新 `.teamwork_localconfig.md` 的 `teamwork_version: {SKILL_VERSION}`
│   │   ├── localconfig 不存在 → 按 templates/config.md 创建最小版（只填 scope:all + teamwork_version）
│   │   └── localconfig 存在但无 teamwork_version 段 → 追加该段
│   └── 输出：「🔄 CLAUDE.md 已同步（{LOCAL_VERSION or "缺失"} → {SKILL_VERSION}）」
│
└── 🚨 SKILL_VERSION = null（skill frontmatter 损坏 / 旧版 skill）
    └── 走全量校验 + 不写回 localconfig（无权威版本号可写）+ ⚠️ 提示"SKILL.md version 缺失"
```

**逃生舱（force full verify）**：

```
用户输入 `/teamwork force-init` 或 `/teamwork init --force`：
├── 本次启动无论版本是否一致，强制走 full path
├── 用于怀疑 CLAUDE.md 被外部工具手改 / 缓存脏污时的兜底
└── 完成后仍回写最新 SKILL_VERSION
```

**设计要点（P0-17 决策记录）**：
- ✅ localconfig 已在 gitignore（见 templates/config.md L77-78）→ 每个开发者各自维护版本缓存，不产生跨机器冲突
- ✅ 漂移自愈仍保留：skill 升级会触发版本号变化 → 下次启动自动跑全量 diff 修复 CLAUDE.md → 写回新版本 → 此后跳过
- ⚠️ 用户手改 CLAUDE.md 但未升级 skill → 版本仍命中 → 跳过校验 → 用户修改被保留（"respect user edits" 默认行为；若要强制恢复模板，用 `/teamwork force-init`）
- ⚠️ 用户手改 localconfig 的 teamwork_version（伪造）→ 未触发全量校验 → 已在模板注释中明确"禁止手改"，依赖纪律 + force-init 兜底

**写入内容**：
```markdown
## Teamwork 协作模式

本项目使用 Teamwork 流程框架：一个 AI 以完整团队方式工作，在不同阶段切换专业视角（PMO/PM/QA/RD/架构师等），通过质量门禁确保产出质量。
启动方式：`/teamwork [需求]` 或 `/teamwork 继续`。
🔴 激活后必须先读取 INIT.md 完成初始化检查，再接收需求。

### 🔴 PMO 每次阶段变更必做（3 件事，缺一不可）

1. 输出 1 行校验：`📋 {A} → {B}（📖 {🚀/⏸️}，来源：flow-transitions.md L{行号} "{原文}"）`
   🔴 必须引用 flow-transitions.md 的实际行号+原文片段，禁止只写"查 ✅"。编造行号 = 伪造证据。
2. 🚀自动 → 直接执行，禁止询问 | ⏸️暂停 → 给建议+理由，等确认
3. 按顺序逐步走，禁止跳过/合并/自创步骤

### 🔴 绝对红线（15 条）

1. 代码写权归 RD（v7.3.10+P0-20）：代码 / 测试 / 构建配置的写操作 = RD 本职，必须由 RD 角色执行（主对话切换 / Subagent 均可），RD 必须先 Read 规范、改后自查；PMO 本职写权仅限流程审计文件（state.json/ROADMAP.md/review-log.jsonl）+ 纯文档（README/注释/CHANGELOG），需标注「📝 PMO 直接修改」。Micro 流程不是红线例外，是省 Stage 的最短 RD 闭环（主对话 PMO→RD 身份切换）。Ship Stage 行为（v7.3.10+P0-15）：Ship Stage PMO 不做本地 merge / push merge_target / 冲突解决，只负责净化 + push feature + 生成 MR 链接。
2. 流程只有六种：Feature / Bug / 问题排查 / Feature Planning / 敏捷需求 / Micro
3. 禁止擅自简化：每种需求走完整流程，用户明确说「跳过」才可豁免
4. 所有用户输入必须由 PMO 先承接
5. 暂停点必须等用户明确确认
6. 需求类型只能填规定的六种
7. 使用流程只能填规定的六种
8. Feature Planning 只产出文档，禁止产出代码
9. 闭环验证：声称"已完成"必须附带实际命令输出
10. 暂停点必须给建议（💡）和理由（📝）
11. PMO 未输出初步分析前禁止写操作
12. 非暂停点（🚀）禁止插入确认/询问
13. Subagent dispatch 前必须完成对应级别预检（L1/L2/L3）
14. AI Plan 模式：每个 Stage 开始前必须输出 Execution Plan（3-4 行核心），未输出不得开始 Stage 工作
15. 流程确认：选定流程类型后、用户确认前必须给出完整流程步骤描述，不给步骤描述直接问「走什么流程」= 违规

### 工作原则

1. 不要假设用户清楚自己想要什么。动机或目标不清晰时，停下来讨论，不要带着猜测往前跑。
2. 目标清晰但路径不是最短的，直接说并建议更好的办法。
3. 遇到问题追根因，不打补丁。每个决策都要能回答"为什么"。
4. 输出说重点，砍掉一切不改变决策的信息。
```

### Step 2: 加载项目空间

```
🔴 穷举检查原则：判定"不存在"前必须检查所有合理位置，禁止只查一个路径就下结论。

检查 teamwork_space.md：
├── 搜索：{项目根}/teamwork_space.md → {项目根}/docs/teamwork_space.md
├── 找到 → 读取，加载子项目清单
├── 未找到 → 进入「首次初始化」流程（见下方）
└── 输出：「📦 已加载项目空间（X 个子项目）」

检查 .teamwork_localconfig.md（多人协作）：
├── 存在 → 读取 scope（all / 指定子项目列表）+ worktree 策略（off/auto/manual）
├── 不存在 → 默认 scope=all（单人模式），worktree=off（v7.3.9+P0-9 决策保留保守默认），不提示不打断
│   └── 用户如需并行 Feature 隔离 → 主动改 localconfig 为 auto/manual（详见 templates/config.md 决策说明）
└── 用户主动说"我只负责 XX" → 那时再创建 localconfig

检查 worktree 环境（worktree ≠ off 时）：
├── 执行 git worktree list → 检测当前是否在某个 Feature worktree 中
├── 在 worktree 中 → 记录当前 worktree 对应的 Feature 编号
├── 不在 worktree 中 → 正常（📎 v7.3.8：Plan Stage 入口按策略创建，不再等到 Dev Stage；v7.3.9：创建走 preflight 暂停点，base 显式指向 origin/{merge_target}）
└── git 不可用 → worktree 降级为 off，输出提示
```

### Step 3: 扫描进度 + 输出看板

```
扫描各子项目 docs/features/*/state.json（v7.3.2）：
├── 读取 current_stage / legal_next_stages / blocking / updated_at
├── 排除 current_stage == "completed" 的 Feature
├── state.json 不存在但目录有 PRD.md → 推断阶段，初始化 state.json
├── 遇到遗留 STATUS.md（v7.2/v7.3 早期）→ 读取作为初始化参考后忽略
└── 汇总为 Feature 看板（按 updated_at 降序）

📋 Feature 状态看板
| 子项目 | Feature | 当前阶段 | 合法下一阶段 | 阻塞 | 最后更新 |
|--------|---------|----------|--------------|------|----------|

🔴 有进行中 Feature → 必须给出优先级建议（💡 + 📝 理由），不能只列状态
无进行中 Feature → 等待新需求
```

---

## 按需加载（不在启动时执行，角色需要时加载）

| 文件 | 加载时机 | 加载者 |
|------|----------|--------|
| docs/KNOWLEDGE.md | 各角色执行时参考 | 当前角色 |
| docs/architecture/ARCHITECTURE.md | RD 技术方案 / 架构师 Review / Dev Stage | RD / 架构师 Subagent |
| docs/architecture/database-schema.md | RD 涉及 DB 变更时 | RD（主对话或 Subagent） |
| docs/PROJECT.md | PM 编写 PRD / PL 讨论产品方向 | PM / PL |
| design/sitemap.md + overview.html | Designer 设计阶段 | Designer Subagent |
| docs/ROADMAP.md | Feature Planning / PMO 完成报告 | PM / PMO |
| DEPENDENCY-REQUESTS.md | scope ≠ all（多人协作）时扫描外部依赖 | PMO |

**按需加载规则**：
```
├── 各角色 Subagent 启动时，PMO 在 prompt 中注入所需文件（见 agents/README.md §四）
├── 主对话角色切换时，PMO 按需读取相关文件
├── 不存在的文件：记录但不阻塞，首次需要时由对应角色创建
│   ├── ARCHITECTURE.md 不存在 → Dev Stage 首次执行时扫描代码自动生成基础版
│   ├── database-schema.md 不存在 → RD 涉及 DB 时扫描 migration/Model 自动生成
│   ├── PROJECT.md 不存在 → PM 首次 Feature Planning 时创建
│   └── KNOWLEDGE.md 不存在 → 无历史知识，正常执行
└── 自动生成的文档为基础版本，后续由架构师在 Code Review 阶段持续完善
```

---

## 首次初始化（teamwork_space.md 不存在时）

### 创建项目空间

```
扫描项目结构：
├── ≥2 个子项目 → 生成 teamwork_space.md 草稿 → ⏸️ 用户确认后写入
├── 1 个子项目 → 提示确认，生成 teamwork_space.md
└── 未发现子项目 → 询问用户定义项目名
🔴 禁止在用户确认前写入 teamwork_space.md
```

### 创建基础目录

```bash
mkdir -p docs/decisions
mkdir -p {子项目路径}/docs/features
mkdir -p {子项目路径}/docs/architecture

# Feature 目录标准结构（创建 Feature 时由 PMO 按需生成，非 INIT 一次创建）
# {子项目路径}/docs/features/{缩写}-F{编号}-{功能名}/
#   ├── state.json              🔴 v7.3.2：Feature 状态机（替代 STATUS.md）
#   ├── PRD.md / TC.md / tech.md / UI.md
#   ├── dispatch_log/          🔴 每个 Feature 必有，首次 Subagent dispatch 时创建
#   │   ├── INDEX.md
#   │   └── {NNN}-{subagent}.md
#   └── bugfix/ optimization/  （可选）
```

### 项目扫描

```
自动识别：项目类型 / 技术栈 / 是否需要 UI / 子项目结构
```

### Codex CLI 检测

```
codex --version 可用 → codex_cli_available = true
不可用 → false（不影响其他流程，仅 Codex Code Review 跳过）
```

### 输出初始化报告

```
📋 Teamwork 初始化完成
================================
✅ CLAUDE.md 已校验
📦 项目空间：已加载（X 个子项目）
🤖 Codex CLI：✅ 可用 / ❌ 未安装

| 缩写 | 名称 | 技术栈 | 需要 UI |
|------|------|--------|---------|

请输入需求开始第一个功能。
```

### 已初始化项目恢复报告（teamwork_space.md 存在时替代初始化报告）

> Step 3 扫描完成后直接输出此报告。

```
📋 Teamwork 项目恢复
================================
📦 项目空间：{路径}（{X} 个子项目）

📋 进行中 Feature：
| 子项目 | Feature | 当前阶段 | 当前角色 | 最后更新 |
|--------|---------|----------|----------|----------|

💡 建议：{优先推进项 + 理由}

可选操作：
├── 📝 提交新需求
├── 🔄 继续进行中的 Feature
└── 📋 查看某子项目 ROADMAP
```
