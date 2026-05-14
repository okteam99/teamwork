# Scripts Policy — teamwork 可执行脚本统一规范（v7.3.10+P0-137）

> 🔴 **单源原则**：teamwork 所有可执行脚本（业务逻辑层）统一 **python3**。
> bash 仅留宿主级 hook 薄壳（如 CC `settings.json` 的 `SessionStart` / `PreCompact` 等），且**不承载业务逻辑**。

---

## 1. 为什么 python > bash

| 维度 | python3 | bash |
|---|---|---|
| 跨宿主可执行 | ✅ CC / Codex / Gemini 任一宿主显式调用 | ❌ 仅 CC `hooks.json` 自动触发 |
| 可验证 | ✅ stdout JSON + exit_code → R7 evidence-binding 入 state.json | ❌ stderr/echo 静默，无审计 |
| 失败可见 | ✅ 非零退出 → AI 必须处理 | ❌ echo warn 继续，无人看 |
| 测试覆盖 | ✅ `tools/tests/test_*.py` pytest 强制 | ❌ 无回归保护 |
| spec 体系 | ✅ 与 state.py / sync-drift.py / init_triage.py 同型 | ❌ 引入 hook 间接层 |
| 依赖底线 | python3（teamwork 已强依赖） | + bash + 宿主 hook 框架 |

**核心结论**：python3 已是 teamwork L3 物化层既定底线（state.py / init_triage.py / sync-drift.py / verify-panorama.py 全部 python）。再叠加 bash 业务脚本 = 给单宿主加优化、给跨宿主加债。

---

## 2. 规则

### R-SP-1 业务脚本一律 python3

新增任何可执行脚本（**有业务逻辑** · 非纯宿主 lifecycle 转发）：

- ✅ 必须写在 `tools/*.py`
- ✅ 必须 `#!/usr/bin/env python3` + `chmod +x`
- ✅ 必须有对应 `tools/tests/test_*.py`（pytest · ≥3 case：happy / edge / failure）
- ❌ 不得新增 `hooks/*.sh` 承载业务（即使是"小脚本"）
- ❌ 不得在 `install.sh` 之外的 bash 文件里写业务流程

### R-SP-2 调用一律 spec 显式 cite

所有 python 工具调用必须在对应 stage spec 里 **显式 cite**，不依赖宿主 hook 自动触发：

```markdown
📌 **post-feature 调用**（脚本物理拦截 · 不靠 PMO 自觉）：

```bash
python3 {SKILL_ROOT}/tools/post-feature.py --project-dir {...} --feature {...}
```
```

理由：
- spec cite + state.json evidence-binding = 跨宿主一致的物理拦截
- 宿主 hook 自动触发 = CC-only · Codex/Gemini 永远漂移

### R-SP-3 hook 仅承载宿主 lifecycle 转发

`hooks/*.sh` 仅允许做**两类事**：

1. CC `settings.json` 的 SessionStart / PreCompact / PostCompact / Stop 等**宿主独有事件的薄壳**——这些事件没有 python 等价物，必须 bash
2. 薄壳内容仅做"调 python"或"读 prompt 文件"，**禁止业务逻辑**

```bash
# ✅ 允许（薄壳）
#!/bin/bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/teamwork/tools/session-restore.py"

# ❌ 禁止（业务逻辑）
#!/bin/bash
if [ -f "$STATUS" ]; then
    if grep -q "✅" "$STATUS"; then ...
```

### R-SP-4 输出 JSON

所有 python 工具 stdout **必须 JSON**（参考 state.py / sync-drift.py 格式）：

```json
{
  "verdict": "OK" | "WARN" | "FAIL" | "BLOCKED",
  "action": "...",
  "...": "..."
}
```

理由：
- AI 能机器解析 + 引用具体字段
- state.json evidence-binding 直接存 stdout
- 跨宿主一致

### R-SP-5 退出码契约

| exit | 含义 | AI 处理 |
|---|---|---|
| 0 | PASS · 正常 | 继续 |
| 1 | WARN · 非阻断（如派生视图刷新失败、提醒缺失） | 记录入 state.json · 继续 |
| 2 | FAIL / BLOCKED · 阻断（state.json 不一致 / 真值损坏 / 参数非法） | ⏸️ PMO 暂停 · 用户介入 |

### R-SP-6 render-first 优于 verify-first（v7.3.10+P0-141 新增）

> 🔴 **结构化输出**（格式固定 · 字段枚举有限）一律走 **render-first**：工具持单源 · AI 传参 · 工具回吐合规输出。**禁止**让 AI 自己拼接结构化输出再事后 verify。

#### 适用判定（A/B/C 三档）

```
A 档 · 纯结构化（必须 render）
├── 状态行（6 字段固定 + emoji 间距 + 路径边界）
├── ⚡ auto skip 日志（固定 3 段）
├── 📋 阶段流转校验行（cite flow-transitions.md L行号 + 原文）
├── 📚 决策参考块（HITL 绝对路径清单）
├── 暂停点决策菜单（编号 + 💡 + 末项「其他指示」）
├── 🧭 Execution Plan 5 行块
└── Feature 完成报告框架

B 档 · 半结构化（hybrid · 工具给骨架 · AI 填语义内容）
├── PMO 初步分析（流程类型 + 阶段链 + 步骤描述）
├── Code Review finding 行（role/severity/位置/建议）
└── Schema 影响分析 + FK 决策表

C 档 · 纯 narrative（保持 verify · 不适合 render）
├── PRD / TC / TECH 主体内容
├── Code Review finding 实际语义
└── 用户对话回应
```

#### render-first 工具五条原则

```
1. 工具持单源 · spec 仅 cite 工具用法 · 不复述格式
   └── 改格式只动 .py + tests · spec 不动

2. 参数即合规校验
   └── stage / role / flow / pause-point 等 enum 校验
   └── 非法即 exit 2 · stderr JSON 含 cite spec hint · AI 知道去哪修

3. JSON stderr + plain stdout
   └── stdout = 给人 / AI cite 用的"成品"（多行 markdown / 纯文本）
   └── stderr = JSON · 含 version / 用过的参数 / verdict · 走 R7 evidence binding 入 state.json

4. 嵌入工具版本号到 stderr 审计 JSON
   └── 不污染 stdout 视觉
   └── verify 工具（后置兜底）按 state.json 中的 evidence binding 判断 AI 是否真调过工具

5. 渐进切换 · 不强制
   ├── 第一阶段：spec 加 "推荐调 X 工具"
   ├── 第二阶段：spec 加 "必须调 X 工具 · 否则审计 WARN"（state.json.concerns）
   └── 第三阶段：硬强制 · CI 拒绝无 evidence binding 的 final response
```

#### 当前阶段速查

| 工具 | 阶段 | 升格 patch |
|---|---|---|
| `tools/render-status-line.py` | **第二阶段**（必须调 · 漏调 = WARN）| v7.3.10+P0-142 升格 |
| `tools/render-afk-skip.py` | **第二阶段**（必须调 · 命中 HITL 自动拒绝）| v7.3.10+P0-143 |
| `tools/render-flow-transition.py` | **第二阶段**（必须调 · 工具读 spec 防编造 L行号）| v7.3.10+P0-143 |
| `tools/render-decision-pause.py` | **第二阶段**（必须调 · 强制 📚 绝对路径 + 末项自动补）| v7.3.10+P0-143 |

#### 与 verify-first 工具配合

```
render-* 工具（前置 · 让 AI 拿合规输出）
   ↓
AI 把工具 stdout 拼进 final response
   ↓
verify-output-format（后置 · 兜底 · 未来 P1+1）
   ├── 检查 state.json evidence_binding 是否含本次响应的 render-* 调用
   ├── 检查输出整体结构（render + narrative 组合合规）
   └── 检查 R5c 反模式措辞（AI 自创的 narrative 部分）
```

两层防御：render 防"格式错"（结构性保证）+ verify 防"AI 没调"（行为性保证）。

#### 已落地的 render 工具

| 工具 | 档位 | 落地 patch | feature context |
|---|---|---|---|
| `tools/render-status-line.py` | A | v7.3.10+P0-141 | ✅ auto-fill 7 字段（P0-144）|
| `tools/render-afk-skip.py` | A | v7.3.10+P0-143 | 无需（参数都是 per-call）|
| `tools/render-flow-transition.py` | A | v7.3.10+P0-143 | 无需（与 feature 无关）|
| `tools/render-decision-pause.py` | A | v7.3.10+P0-143 | ✅ --auto-refs 按 class 发现（P0-144）|

#### 已落地的 verify / scan 工具

| 工具 | 用途 | 落地 patch |
|---|---|---|
| `tools/scan-spec-consumer.py` | R-SP-8 writer-only 规则扫描（spec consumer coverage report）| v7.3.10+P0-146 |
| `tools/diff-html-vs-panorama.py` | Designer 全景对齐 DOM diff（panorama overview.html vs feature preview）| v7.3.10+P0-147 |

后续候选：`render-execution-plan.py` / `render-stage-summary.py` / `render-feature-completion-report.py` / `verify-output-format.py`（兜底）等（每个独立 patch · 触发即加）。

### R-SP-7 feature context auto-fill（v7.3.10+P0-144 新增）

> 🔴 **PMO 调 render-* 工具时常用参数（feature_id / flow_type / current_stage / branch / worktree_path / merge_target / ext_model）一律从 state.json auto-fill** · spec 调用示例只写 per-call 语义参数（--role / --next-step / --pause-point / --decision）。

#### 发现优先级

```
1. 工具显式 --feature-dir 参数（最高 · 测试 / 多 Feature 场景用）
2. $TEAMWORK_FEATURE 环境变量（推荐 · 在 Feature 目录 export 一次）
3. 从 CWD 向上 walk · 找含 state.json 且 parent 路径含 'features/' 段的目录
4. 找不到 → 返回 None · 工具按显式参数走（不强制 context）
```

#### 参数合并语义（_feature_context.merge_param）

```
explicit 非空 → 用 explicit · 若 context 也有值且不同 → audit JSON 记 overrides_from_context
explicit 为 None / 空 → 用 context 值 · audit JSON 记 source: state.json
两者皆 None → fail + cite hint
```

#### 实现单源

`tools/_feature_context.py`（~120 行）：
- `FeatureContext` dataclass（11 字段 · 与 state.json schema 同型）
- `load(explicit_dir)` 按发现优先级返回 ctx 或 None
- `merge_param(explicit, context_value)` → `(effective, was_overridden)`
- 工具自行决定哪些字段强制要求 / 哪些可缺

#### 调用对比

```bash
# Before（P0-141~143 · PMO 每次传 9 参数）
python3 tools/render-status-line.py --flow Feature --role PMO --stage dev \
  --feature "F042" --path /abs --branch f/F042 --merge-target main --worktree-path /abs/wt \
  --next-step "等用户确认 TC"

# After（P0-144 · PMO 传 2 参数 · 其余 7 自动）
export TEAMWORK_FEATURE=/abs/feature
python3 tools/render-status-line.py --role PMO --next-step "等用户确认 TC"
```

#### 边界

- ❌ 不在 Feature 流程（问题排查 / Feature Planning）→ context 找不到 · 必须显式传
- ❌ state.json 损坏 → fall back 到显式参数
- ✅ `--no-context` flag 强制禁用 auto-fill（调试用）
- ✅ 显式参数永远优先 · audit JSON 留痕

### R-SP-8 每条「🔴/必须」规则必须含「下游消费者」标注（v7.3.10+P0-146 新增）

> 🚨 **实战触发**：API-F048-Ollama 代理网关 case · 4.6 instance 自承"我跳的步骤都没有下游消费者标注"——只写"🔴 必须"但没说"跳了谁会发现 / 哪个下游会失败"· AI 内部评估为"只是仪式"而跳掉。
>
> 4.6 原话：「我跳"写了没人读"的步骤 · 不跳"下游有人依赖"的步骤」。

#### 核心规则

```
🔴 spec 中每条「🔴/必须/必填/必读/禁止/不得/强制」级规则
   = MUST 同段内含「下游消费者」标注：跳了之后谁/哪个下游会发现 / 失败 / 拒绝。

❌ writer-only 反模式（命中 → P0-146 候选修复）：
   "🔴 必须创建 state.json"                  ← 没写跳了谁会坏
   "🔴 PRD-REVIEW.md 必需"                   ← 同上
   "🔴 角色切换必须 cite"                    ← 同上

✅ 含消费者推荐写法：
   "🔴 创建 state.json — Blueprint 入口 enter-stage 校验前置 gate · 缺则 exit 1"
   "🔴 写 PRD-REVIEW.md — Blueprint QA 读此文件确认评审覆盖 · 缺则 QA 重审整 PRD"
   "🔴 cite 关键要点 — 不 cite 评审退化为自我对话（实证 API-F048 case · 4.6 自承）"
```

#### 下游消费者标志的有效形式

```
1. 工具校验失败：
   - "exit 1 / exit 2 / BLOCKED / verify fail"
   - "state.py XXX 子命令 reject"
   - "render-* 工具 cite spec hint"

2. 下游 Stage 拒绝：
   - "Blueprint 入口 gate 校验"
   - "QA 重审整 PRD"
   - "架构师 CR 打回"

3. 用户可见后果：
   - "用户无法验证 PMO 是否跑过"
   - "实证 case PTR-F001-BUG-013 / ADMIN-F012 / API-F048"

4. 状态损坏 / 漂移：
   - "state.json 与 PRD 分裂"
   - "评审退化为自我对话"
   - "ROADMAP 派生值漂移"
```

#### 物化扫描

`tools/scan-spec-consumer.py` 扫描所有 spec 文件 · 输出：
- Total 🔴/必须 规则数
- With consumer 数（已合规）
- Missing consumer 数（修复候选）
- 候选清单（按 file:line 排序 · 含 section context）

```bash
# 看摘要
python3 tools/scan-spec-consumer.py --limit 30

# Markdown 人类可读
python3 tools/scan-spec-consumer.py --output-format markdown --limit 30

# 全量
python3 tools/scan-spec-consumer.py --limit 0
```

#### 渐进切换

```
第一阶段（P0-146 · 当前）：
   - 加 R-SP-8 原则
   - 修复 top 30 writer-only 规则（4.6 case 直接命中的 + 高影响）
   - 加 scan 工具（非强制 · 列清单）

第二阶段（待定）：
   - 修复 missing consumer 比例从 62.8% → ≤30%
   - 新 spec 规则 PR review 时 scan 工具 fail → reject merge

第三阶段（待定）：
   - 全量修复 · ratio_missing → ≤10%
   - scan 工具 exit 2 if missing > N · CI 强制
```

#### 当前阶段实测数据（v7.3.10+P0-146 初始扫描）

```
Total 🔴/必须 rules: 411
With consumer: 153 (37.2%)
Missing consumer: 258 (62.8%)  ← 修复方向
```

P0-146 处理 top 30 (~12% of missing) · 后续 patch 渐进推进。

---

## 3. 已存在的 python 工具（参考样板）

| 工具 | 职责 | 模式 |
|---|---|---|
| `tools/state.py` | state.json schema/状态机/evidence-binding 单源 | 子命令 + JSON 输出 |
| `tools/init_triage.py` | session bootstrap · audit_line | 一次性 boot · JSON 输出 |
| `tools/sync-drift.py` | marker-aware CLAUDE.md/AGENTS.md 同步 | marker 单向渲染 |
| `tools/verify-panorama.py` | 全景设计物化校验 | 校验 + JSON 输出 |
| `tools/post-feature.py` | Feature 收尾 · KNOWLEDGE check + ROADMAP render | 多职责聚合（v7.3.10+P0-137 新增）|

---

## 4. 迁移路径（v7.3.10+P0-137 立账）

| 旧 bash 脚本 | 状态 | 备注 |
|---|---|---|
| `hooks/post-feature.sh` | **退役** | → `tools/post-feature.py`（本 patch） |
| `hooks/session-restore.sh` | 保留 | CC SessionStart 薄壳 · 待评估是否 python 化 |
| `hooks/post-compact.sh` | 保留 | CC PostCompact 薄壳 · 待评估是否 python 化 |
| `hooks/post-stop.sh` | 保留 | CC Stop 薄壳 · 待评估是否 python 化 |
| `hooks/post-subagent.sh` | 保留 | 薄壳 · 待评估是否 python 化 |

🟢 **渐进迁移**：后续 patch 评估剩余 bash 脚本是否还有"宿主薄壳之外"的业务逻辑。如有 → 拆出到 `tools/*.py` + bash 仅留转发。

---

## 5. 反模式黑名单

❌ 新增 `hooks/post-X.sh` 写业务（绕过本 policy 的隐蔽路径）
❌ python 工具 stdout 非 JSON（破坏 R-SP-4）
❌ 业务流程在 `install.sh` 里直接写（install 只做部署）
❌ spec 不 cite 工具调用 · 仅靠宿主 hook 自动触发（破坏 R-SP-2 · CC-only 陷阱）
❌ python 工具无对应 test_*.py（破坏 R-SP-1 · 无回归保护）

---

## 6. 与红线层级关系

- 本规范属 **L2 standards 层**（按需 read）
- L1 红线不新增条目（路径 B · 不走路径 C）
- L3 物化层 = `tools/*.py` + `tools/tests/test_*.py`
- 触发：新增脚本时必读 · PMO 起 P0 patch 涉及 hooks/ 或 tools/ 时必读
