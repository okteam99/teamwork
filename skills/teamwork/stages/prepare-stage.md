# Prepare Stage：mode B 重型准备 + 流程类型识别（v7.3.10+P0-106 新建）

> mode B（execute）执行流程的**入口准备 stage** · 仅在 triage 分诊为 mode B 时触发。
>
> 🟢 **流程级 Stage**（与 triage-stage 同源 · v7.3.10+P0-106 拆出）：
> - 触发频率：仅 mode B execute 路径（A/C/D/E 不触发）
> - 状态归属：**幂等不持久化**——prepare 不写持久 state（创建 state.json 是流程类型识别后的事）
> - 写操作禁令：本 Stage 不动业务文件 · 仅环境校验 + 项目级 read
>
> 🔴 契约优先：本文件规范 Input / Process / Output 三契约。

---

## 本 Stage 职责

把"mode B 重型流程"的准备工作集中在此 stage：
- 环境兜底（CLAUDE.md / 项目空间 / Feature 看板）
- 项目级扫描（KNOWLEDGE / ADR）
- 流程类型识别（5 种闭集）
- 流程感知懒加载（角色 / 外部模型 / state.json 创建按需）

详细抽出来源：
- 原 stages/init-stage.md Step 1.2 / Step 2 / Step 3（环境层）
- 原 stages/triage-stage.md Step 2-9（项目级 + 流程层）

---

## Input Contract

### 必读输入

```
- triage 分诊已判定为 mode B（标志：用户消息含推进动词 / 不是 query/resume/status/discuss）
- 用户原始消息 + 命令前缀（auto / 普通）
- triage 已经 read 的：用户消息（无项目级文件）
```

### 进入条件

```
- triage-stage 已分诊为 mode B
- 红线 R8 写操作硬门禁仍生效（PMO 未输出"流程步骤描述 + 用户确认"前禁止任何写）
```

---

## 入口 Read 顺序（v7.3.10+P0-106 固定）

🔴 按以下顺序 Read · 字节一致利于 prompt cache 命中。详见 [standards/prompt-cache.md](../standards/prompt-cache.md)。

```
Step 1: roles/pmo.md                            ← 角色层（L0 稳定）
Step 2: SKILL.md § 项目级文档信息架构           ← 知识地图（L0 稳定 · 已注入）
Step 3: SKILL.md frontmatter                    ← 框架版本（L0 稳定）
Step 4: 项目根/.teamwork_localconfig.md         ← 项目缓存层（L1）
Step 5: HOST_INSTRUCTION_FILE（CLAUDE.md / AGENTS.md）← 宿主指令文件（L1）
Step 6: KNOWLEDGE.md / teamwork_space.md / ADR INDEX  ← 项目层（L1 · 按需）
Step 7: 用户消息 + 命令前缀（已在主对话）        ← 动态入口（L3）
```

---

## Process Contract

### Step 1: SKILL_ROOT 检测 + 宿主识别（原 init Step 1）

```
检测主对话宿主：
  ├── Claude Code 主对话 → SKILL_ROOT = ~/.claude/skills/teamwork
  ├── Codex CLI 主对话 → SKILL_ROOT = ~/.codex/skills/teamwork（或类似）
  ├── Gemini CLI 主对话 → SKILL_ROOT = ~/.gemini/skills/teamwork
  └── 通用 / 无法识别 → 记录为 unknown · 走兜底路径

设定 host_main_model 字段（用于后续异质性约束）：
  ├── Claude Code → host_main_model = "claude-code"
  ├── Codex CLI → host_main_model = "codex-cli"
  ├── Gemini CLI → host_main_model = "gemini-cli"
  └── unknown → host_main_model = "unknown"
```

🔴 **silent execution**：不输出"宿主检测结果 = X"等中间状态。

### Step 2: 版本缓存校验（原 init Step 1.2）

```
读取 SKILL.md frontmatter version → SKILL_VERSION
读取 .teamwork_localconfig.md teamwork_version → LOCAL_VERSION

比对：
  ├── ⚡ 一致 → 跳过 CLAUDE.md / AGENTS.md 全量 diff（fast path）
  ├── 🔄 不一致 / null → 全量校验 CLAUDE.md / AGENTS.md（diff + 漂移自愈）+ 回写 LOCAL_VERSION
  └── 🚨 SKILL_VERSION = null → 走全量校验 + ⚠️ 提示
```

🔴 **silent execution**（v7.3.10+P0-105）：
- 一致路径：完全不输出
- 不一致路径：内部回写 · 不输出"版本不一致" / "字符级一致" / "已同步"
- 仅异常输出 ⚠️（CLAUDE.md 真实漂移 / SKILL.md frontmatter 损坏）

### Step 3: 项目空间加载（原 init Step 2）

```
🔴 穷举检查原则：判定"不存在"前必须检查所有合理位置。

检查 teamwork_space.md：
  ├── 搜索：{项目根}/teamwork_space.md → {项目根}/docs/teamwork_space.md
  ├── 找到 → 读取，加载子项目清单 + docs_root 路由
  ├── 未找到 → 进入「首次初始化」流程
  └── 不输出 "📦 已加载项目空间（X 个子项目）" banner（v7.3.10+P0-105 silent）

检查 .teamwork_localconfig.md（多人协作）：
  ├── 存在 → 读取 scope / worktree 策略 / cache 版本
  ├── 不存在 → 默认 scope=all + worktree=auto · 不提示
  └── 用户主动说"我只负责 XX" → 创建 localconfig

检查 worktree 环境（worktree ≠ off 时）：
  ├── git worktree list 检测当前是否在某 Feature worktree
  ├── 在 → 记录当前 worktree 对应 Feature 编号
  ├── 不在 → 正常（Goal-Plan Stage 入口按策略创建）
  └── git 不可用 → worktree 降级 off + ⚠️
```

### Step 4: 用户输入承接（红线 R3 · v7.3.10+P0-105 隐式承接）

```
🟢 承接是隐式的（不输出"我已收到你的输入"）：
  - PMO 实际承接（在内部状态机记录）· 红线 R3
  - 不输出承接确认文本
  - 不输出"现在直接定位 X" / "进入 prepare-stage 等

唯一允许的输出（异常分支）：
  - 用户输入完全无法解析（乱码 / 空消息）→ ⚠️ 提示重新输入
  - 用户输入触发 BLOCKER（跨 Feature 冲突 / 红线违规预警）→ ⏸️ 决策模板
```

### Step 5: KNOWLEDGE 扫描（原 triage Step 2）

读取项目级 `KNOWLEDGE.md` · 根据用户消息关键词扫描 Gotcha / Convention / Architecture · 输出「📚 相关项目事实」段。

**有命中时**：

```markdown
## 📚 相关项目事实（KNOWLEDGE 扫描）

- Gotcha 命中（X 条）：{KNOWLEDGE.md 引用 + 简述}
- Convention 命中（Y 条）：...
- Architecture 命中（Z 条）：...
```

**无命中时**（v7.3.10+P0-30 渲染降级）：一行带过：

```markdown
📚 KNOWLEDGE 扫描：均无相关条目
```

🔴 无命中也必须输出此行（扫描结果不可省略）· 但不展开 0 命中子标题。

### Step 6: ADR 索引扫描（原 triage Step 3）

扫描已有 Feature 的 `adrs/INDEX.md` · 识别与当前需求相关的历史决策。

**有命中**：

```markdown
## 📜 相关 ADR（历史决策扫描）
- {ADR ID}：{标题}（{Feature 引用}）
```

**无命中**（渲染降级）：

```markdown
📜 ADR 扫描：均无相关决策
```

### Step 7: 流程类型识别（原 triage Step 5 · 5 种闭集）

🔴 **流程类型仅 5 种**（v7.3.10+P0-106 删 "问题排查"·该场景已由 triage mode A query 接管）：

```
1. Feature 流程        ← 完整 8 stage（PRD/UI/TC/TECH/Code/Review/Test/Ship）
2. Bug 流程            ← 简化（fix → ship）
3. Micro 流程          ← 最简（必读规范 → 改 → 自查）
4. 敏捷需求流程         ← 精简 PRD + 后续完整
5. Feature Planning 流程 ← 仅写文档（PROJECT/ROADMAP/sitemap · v7.3.10+P0-106 精简后不含讨论部分）
```

🔴 **R2 流程类型闭集**：禁止自创变体名（"Feature 变更" / "Feature 流程类型" 等均违规）。

判定规则：
- 用户描述含"实现 / 创建 / 重构" + 完整需求 → Feature
- 用户描述含"修复 / 报错 / 异常" + Feature 编号或具体缺陷 → Bug
- 用户描述含"改名 / 重命名 / 单文件改 / 删除 / 小改" + 单点动作 → Micro
- 用户描述含"快速实现 / MVP / 先做最简版" → 敏捷需求
- 用户描述含"Roadmap / 全景设计 / 跨 Feature 规划" → Feature Planning

### Step 8: 流程感知懒加载（v7.3.10+P0-106 新增）

按流程类型按需触发后续准备：

| Step | Feature | Bug | Micro | 敏捷 | Planning |
|------|---------|-----|-------|------|---------|
| Step 9 角色可用性扫描 | ✅ 全角色 | ✅ 部分（RD + QA）| ❌ 跳过（仅 RD）| ✅ 部分 | ❌ 跳过 |
| Step 10 外部模型探测 | ✅ | ❌ | ❌ | ✅ | ❌ |
| Step 11 Feature 看板 | ✅ | ✅（看冲突）| ❌ | ✅ | ❌ |
| Step 12 流程步骤描述输出 | ✅ 完整 | ✅ 简版 | ✅ 极简 | ✅ 简版 | ✅ 极简 |
| Step 13 双对齐暂停 | ✅ | ✅ | ✅ | ✅ | ✅（v7.3.10+P0-106 仅写文档前确认）|
| Step 14 state.json 创建 | ✅ 完整 | ✅ Bug 简版 | ✅ 轻量 MICRO-{id} | ✅ 简版 | ❌ Planning 不创建 Feature state |

### Step 9: 角色可用性扫描（按流程类型懒加载 · 原 triage Step 4）

```
内部角色（固定可用）：pl / rd / qa / designer / pmo / architect

external 角色（PMO 直接判定 · v7.3.10+P0-101 evidence-binding · v7.3.10+P0-112 物理拦截层级修正）：
  必须 bash 实测：
    command -v codex 2>&1 ; echo "codex_exit=$?" ; command -v claude 2>&1 ; ...
  
  完整 stdout 写入 state.json（审计层 · 物理拦截）：
    state.external_cross_review.detection_evidence = {
      command, stdout, exit_code, detected_at
    }
  
  主对话只输出精炼结论（silent execution · v7.3.10+P0-105 / +P0-112）：
    ✅ "🌐 External 探测：codex ✅ 可用 / claude ⏭️ 同源跳过 / gemini ❌ 未安装"
    ❌ 不要 verbatim 贴 stdout / exit_code（与 silent execution 冲突）
  
  详见 standards/evidence-binding.md（v7.3.10+P0-112 物理拦截层级 = state.json schema · 不在主对话）
```

🔴 **流程感知懒加载**：Micro / Planning 流程跳过本 Step。

### Step 10: 外部模型探测（按流程类型懒加载）

仅 Feature / 敏捷 流程触发。详见 [standards/external-model-usage.md](../standards/external-model-usage.md)。

### Step 11: Feature 看板加载（按流程类型懒加载）

仅 Feature / Bug / 敏捷 流程触发（看是否有冲突 Feature）。Micro / Planning 跳过。

### Step 12: 流程步骤描述输出（红线 R4(c) · 原 triage Step 6-7）

按流程类型输出对应步骤描述 + 阶段链 + 预期产出。

### Step 13: 双对齐暂停（原 triage Step 8）

⏸️ 用户回 ok / auto 或反馈意见。

### Step 14: state.json 创建（原 triage Step 9 · 按流程懒加载）

```
Feature / Bug / Micro / 敏捷 → 创建 state.json（按流程类型 schema）
Feature Planning → 不创建 Feature state（仅写 PROJECT/ROADMAP/sitemap · 这是 Planning 流程的产物）
```

详见 templates/feature-state.json schema。

---

## Output Contract

### 输出产物

```
1. state.json（如适用 · 按流程类型）
2. 流程步骤描述输出（主对话）
3. 用户确认（双对齐暂停后）
4. 跳转：进入对应流程的第一个业务 stage
   ├── Feature → Goal-Plan Stage
   ├── Bug → 第一个 fix stage
   ├── Micro → RD 身份切换 + 必读 + 改 + 自查
   ├── 敏捷 → 精简 PRD Stage
   └── Feature Planning → 仅写 PROJECT/ROADMAP/sitemap（无 Stage 链）
```

### 出口校验（v7.3.10+P0-101 evidence 完整性 · 见 pmo-state-mgmt.md § 2.4）

如创建了 state.json：
- 事实字段 evidence-binding 完整性校验
- output_satisfied = true 或 ⚠️ 阻断

---

## 主对话输出 Tier 应用

详见 [standards/output-tiers.md](../standards/output-tiers.md)。

```
Tier 1（必看）：
  - KNOWLEDGE 扫描结果（命中段）
  - 流程类型识别结论 + 步骤描述
  - 双对齐暂停模板

Tier 2（命中折叠）：
  - ADR 命中
  - 角色可用性结果（external 探测 stdout · evidence-binding 必输出）

Tier 3（默认不输出）：
  - silent execution（环境校验 / 缓存命中 / 项目空间加载 · 已 v7.3.10+P0-105 强化）
  - 框架仪式（"进入 prepare-stage" / "Step X 进行中" 等禁止）
```

---

## 与 triage-stage 的边界

```
triage-stage = 5 mode 分诊（仅看用户输入 · 不读项目级文件）
prepare-stage = mode B 重型准备（吸收原 init/triage 大部分 Step · 仅 mode B 触发）
```

prepare-stage 的入口是"triage 分诊为 mode B"·出口是"用户确认 + state.json 创建（如适用）+ 进入对应流程的第一个 stage"。

---

## 与原 init-stage.md 的关系（v7.3.10+P0-107 完成迁移）

```
v7.3.10+P0-106 之前：init-stage.md 包含 Step 0/1/1.2/2/3
v7.3.10+P0-106：标 deprecated（保留物理文件兼容引用）
v7.3.10+P0-107：扫描 22 处实际引用 + 批量迁移 + 物理删除 init-stage.md
                docs/CHANGELOG.md 历史段 + standards/output-tiers.md 反模式 case 保留 init-stage 字符串作为历史

迁移路径：
  - Step 0 命令解析 → 迁到 triage-stage.md 动作 1
  - Step 1 SKILL_ROOT 检测 → 迁到本文件 Step 1
  - Step 1.2 版本校验 → 迁到本文件 Step 2
  - Step 2 项目空间 → 迁到本文件 Step 3
  - Step 3 Feature 看板 → 迁到 triage-stage.md § D · status / 本文件 Step 11
  - Step 3.5 角色可用性 → 迁到本文件 Step 9
```

末。
