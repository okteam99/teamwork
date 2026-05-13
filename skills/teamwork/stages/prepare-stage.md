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

### Step 1: 宿主自报 + SKILL_ROOT 解析（v7.3.10+P0-128 改 · PMO 注入 · 不再脚本探测）

PMO 在主对话内自报（system prompt 已知 · 不需脚本探测）：

| 宿主 | host enum | SKILL_ROOT |
|----|----|----|
| Claude Code | `claude-code` | `~/.claude/skills/teamwork` |
| Codex CLI | `codex-cli` | `~/.codex/skills/teamwork`（或类似）|
| Gemini CLI | `gemini-cli` | `~/.gemini/skills/teamwork` |
| 其他 / 不能识别 | `unknown` | 取已 read 的 SKILL.md 路径反推 |

PMO 把 host + skill_root + skill_version 作为命令行参数注入 [tools/init_triage.py](../tools/init_triage.py)（详 Step 3）· 脚本不做探测 · 输出 JSON 原样回显这三字段供 audit。

🔴 **silent execution**：不输出"宿主检测结果 = X"等中间状态。

### Step 2: 版本缓存校验（v7.3.10+P0-128 改 · 物化到 init_triage.py · prompt 层只处理结果）

PMO 不再自己读 .teamwork_localconfig.md.teamwork_version · 一并由 init_triage.py 探测（读 .teamwork_localconfig.md frontmatter）+ 比对 PMO 注入的 --skill-version · 输出 JSON `version_match` 布尔。

PMO 处理 advisory：

```
init_triage.py 输出 advisories[] 含 topic=version-mismatch（severity=WARN）：
  ├── 一致路径（无此 advisory · version_match=true）→ 跳过 CLAUDE.md / AGENTS.md 全量 diff（fast path · silent）
  ├── 不一致路径（advisory 命中）→ 全量校验 CLAUDE.md / AGENTS.md（diff + 漂移自愈）+ 回写 LOCAL_VERSION 到 .teamwork_localconfig.md
  └── SKILL_VERSION = null → PMO 在注入 --skill-version 前已发现 → ⚠️ 提示用户 SKILL.md frontmatter 损坏 · 不进 init
```

🔴 **silent execution**（v7.3.10+P0-105）：
- 一致路径：完全不输出
- 不一致路径：内部回写 · 不输出"版本不一致" / "字符级一致" / "已同步"
- 仅异常输出 ⚠️（CLAUDE.md 真实漂移 / SKILL.md frontmatter 损坏）

🔴 **CLAUDE.md / AGENTS.md drift 同步**（v7.3.10+P0-135 撤 P0-126 carve-out · init_triage.py 内部自动调 sync-drift.py）：

PMO 跑 init_triage.py（R9 红线）时 · 若 version-mismatch 且 target 文件含 teamwork-pointer marker · 自动调 [tools/sync-drift.py](../tools/sync-drift.py) 升级。无需 PMO 二次调用。

```
init_triage.py 内部 sync 决策：
├── version_match=true → skipped (version_match=true)
├── host=unknown → skipped（不知 target 文件名）
├── host claude/codex 但 target 不存在 → skipped（防污染非 teamwork 项目 · 提示跑 install.sh）
├── target 存在但缺 marker → skipped（提示跑 install.sh 或 sync-drift --init）
├── target 存在 + marker 存在 + version-mismatch → 自动 sync-drift 升级
└── --no-sync flag → skipped（debug 逃生舱）
```

audit_line 含 sync 结果 · 例：`sync-drift=upgraded(v7.3.10+P0-100→v7.3.10+P0-135)` 或 `sync-drift=noop` 或 `sync-drift=skipped`。

手工调用 sync-drift.py（install.sh / 首次注入 / debug）：

```bash
python3 {SKILL_ROOT}/tools/sync-drift.py \
  --target {项目根}/CLAUDE.md \
  --source {SKILL_ROOT}/templates/host-instruction-injection.md \
  --skill-version {SKILL_VERSION} \
  [--init]      # marker 不存在时首次插入（install.sh 自动加）
  [--dry-run]   # 看 diff 不写
```

物理保护：sync-drift.py 仅动 `<!-- TEAMWORK_BEGIN:X -->` ... `<!-- TEAMWORK_END:X -->` 之间内容 · 用户在 marker 外的编辑**永不动**。idempotent · 同版本重跑 = noop。

### Step 3: 项目空间加载（v7.3.10+P0-126 改 · 走 tools/init_triage.py 单源）

🔴 **物化拦截**（治本 P0-118-B 系列：触发时机过窄 / 空骨架标识符错配 / 用户告知盲区 / monorepo 路径模糊）：原本散在本 Stage Step 3 的 4 块扫描（teamwork_space / TROUBLESHOOTING / GLOSSARY / global_schema_docs）+ worktree 探测 + 版本比对 全部下沉到 [tools/init_triage.py](../tools/init_triage.py) 一次调用。

📌 **state.py 同范式调用**（PMO 注入已知 host / skill_root / skill_version · 脚本不探测）：

```bash
python3 {SKILL_ROOT}/tools/init_triage.py \
  --cwd {项目根 cwd} \
  --host {claude-code | codex-cli | gemini-cli | unknown} \
  --skill-root {SKILL_ROOT} \
  --skill-version {SKILL.md frontmatter version}
```

stdout = 单次结构化 JSON（PMO 一次引入对话 · 不再各自 Glob/Read）：

```json
{
  "verdict": "OK",
  "host": "claude-code",
  "project_root": "...",          // git root（cwd 在 git repo 内）/ cwd（fallback）
  "project_root_source": "git" | "cwd",
  "version_match": true | false,  // skill_version vs local_version（脚本读 .teamwork_localconfig.md）
  "project_files": {
    "teamwork_space.md": {"exists": ..., "path": ...},
    ".teamwork_localconfig.md": {"exists": ..., "path": ...},
    "TROUBLESHOOTING.md": {"exists": true, "is_empty_skeleton": ..., "created_now": ...},
    "GLOSSARY.md":        {"exists": true, "is_empty_skeleton": ..., "created_now": ...}
  },
  "global_schema_docs": {
    "docs": ["..."], "evidence": {"command": "...", "exit_code": 0, ...}
  },
  "worktree": {"available": true, "current_branch": "...", "worktree_count": ...},
  "advisories": [
    {"severity": "INFO", "topic": "first-init", "message": "..."},
    {"severity": "INFO", "topic": "skeleton-created", "message": "..."},
    {"severity": "INFO", "topic": "empty-skeleton", "message": "..."},
    {"severity": "WARN", "topic": "version-mismatch", "message": "..."}
  ]
}
```

PMO 处理 advisories：
- `first-init` → 走首次初始化流程（teamwork_space.md 引导用户创建）
- `skeleton-created` / `empty-skeleton` → 用户首次相关动作时一句话提示补充
- `version-mismatch` → 走全量 CLAUDE.md / AGENTS.md drift 校验（仍是 prompt 层 + 用户确认 · 脚本不动）

🔴 **脚本不做的事**（明确边界 · 类比 state.py 红线）：
- 不探测 host（PMO 知道 · 注入即可）
- 不动 CLAUDE.md / AGENTS.md（drift 同步高风险 · 留 prompt 层 + 用户确认）
- 不创建 worktree（属 Goal-Plan Stage 业务）
- 不写 state.json（属 state.py · 本脚本只做 bootstrap 探测 + 空骨架创建）

🔴 **bootstrap 例外条款**（与红线 R8 协同）：init_triage.py 的"不存在 → 复制空骨架"动作属 bootstrap · 不算业务写 · 不需 R8 用户确认（类比 state.py raw-write 的逃生舱契约边界）。

🔴 **silent execution**（v7.3.10+P0-105 协同）：脚本 silent · PMO 仅在 advisories 含 `severity=WARN` 或 `topic ∈ {first-init, skeleton-created}` 时主对话提示一句 · 否则不输出。

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

🔴 **渲染必含**（v7.3.10+P0-115 cite + v7.3.10+P0-118-A 骨架 · 非决策类暂停点 · 不强制 📚 决策参考）：

⬇️ 末尾骨架（阶段值 = `triage` enum「⏸️ 双对齐待确认」 · prepare 期 worktree 尚未建 · 第三行省略或 📍 当前分支）：

```
---
🔄 Teamwork 模式 | 流程：{流程类型} | 角色：PMO | {功能字段(如已有)} | 阶段：⏸️ 双对齐待确认 | 下一步：⏸️ 用户回 ok / auto / 反馈
📁 {项目根}
📍 当前分支：{git branch --show-current}（worktree 待 Step 13.5 用户确认后创建）
```

### Step 13.5: 环境准备执行（v7.3.10+P0-145 新增 · 治本 worktree/state.json 时序 gap）

🔴 **本 Step 不暂停 · 用户已在 Step 13 确认 environment_config（triage Step 7.5-8 探测 + 确认）**。

> 🚨 **修复的 bug**：v7.3.10+P0-145 之前的时序是
> 1. prepare-stage Step 14 创建 state.json（主工作区）
> 2. Goal-Plan Stage 入口创建 worktree（clean checkout · state.json 不跟过去）
> → state.json 与后续 PRD 分裂在两个分支
>
> **本 Step（13.5）把 worktree 创建提前到 state.json 创建之前** · 让两者诞生时就在同一 worktree · 时序问题消失。

按流程类型懒加载：
- **Feature / 敏捷 / Bug（复杂 → Feature 流程）**：执行环境准备序列（worktree_mode=auto/manual 时创建 worktree）
- **Micro**：执行环境准备序列（worktree_mode=auto/manual 时创建 chore worktree）
- **Feature Planning**：跳过 worktree（Planning 不出代码）
- **问题排查**：跳过 worktree（无具体 Feature）

#### 自动执行序列（worktree_mode in [auto, manual] 时）

```bash
# Step 1: 处理工作区状态（按 triage 决定的 dirty_resolution）
case state.environment_config.dirty_resolution in
  "stash")  git stash push -m "auto stash before {Feature 全名}" ;;
  "commit") git status --porcelain ;;  # 用户已自行 commit · 验证已干净
  "force")  ;;                          # 用户授权强制继续 · state.concerns 记录授权时刻
  null)     ;;                          # triage 时工作区已干净
esac

# Step 2: Fetch base
git fetch origin {state.environment_config.merge_target}
git rev-parse --verify "origin/{state.environment_config.merge_target}"

# Step 3: 创建 worktree
git worktree add {worktree.path} -b {state.environment_config.branch} "origin/{state.environment_config.merge_target}"

# Step 4: 切到 worktree（后续 Step 14 state.json 创建在 worktree CWD 下执行）
cd {worktree.path}
```

🔴 **关键约束**：`git worktree add` 必须显式指定 base（`origin/{merge_target}`），不能依赖隐式 HEAD。

🟢 **P0-3 懒装依赖模型**：worktree 创建**不触发**依赖安装（`npm install` / `pip install` / `go mod download`）。

#### 异常分支（仅异常时走 · 常规情况不打断用户）

| 异常 | 处理 |
|------|------|
| base 分支不可达（fetch 失败 / 远端配置错） | BLOCKED → state.concerns 加 WARN + ⏸️ 暂停（异常分支） |
| 分支名冲突（triage 时未发现 · 竞态） | state.concerns + ⏸️ 暂停（让用户决策：续用 / 改名 / 删除重建） |
| worktree add 失败 | 按 worktree 降级链（auto → manual → off）· state.concerns + 不暂停（继续 off 模式 · state.json 留主工作区） |
| stash 失败 | state.concerns + ⏸️ 暂停（让用户人工处理） |

#### worktree=off 场景

跳过 Step 3-4。Step 14 state.json 创建仍在当前 CWD（项目根 / 主工作区） · 与 PRD 同位。

### Step 14: state.json 创建（原 triage Step 9 · 按流程懒加载）

🔴 **执行位置（v7.3.10+P0-145 修订）**：CWD 已在 Step 13.5 切到 worktree（如启用）· state.json 创建落在 worktree 内 · 与后续 PRD / 评审产物同位。

```
Feature / Bug / Micro / 敏捷 → 创建 state.json（按流程类型 schema）
Feature Planning → 不创建 Feature state（仅写 PROJECT/ROADMAP/sitemap · 这是 Planning 流程的产物）
```

调用 [tools/state.py init-feature](../tools/state.py)（或对应子命令）· artifact_root 相对 CWD（=worktree 根 · 如启用）解析。

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
