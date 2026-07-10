# Scripts Policy — teamwork 可执行脚本统一规范

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
| spec 体系 | ✅ 与 state.py / bootstrap.py 同型 | ❌ 引入 hook 间接层 |
| 依赖底线 | python3（teamwork 已强依赖） | + bash + 宿主 hook 框架 |

**核心结论**：python3 已是 teamwork L3 物化层既定底线（state.py / bootstrap.py / verify-panorama.py 全部 python）。再叠加 bash 业务脚本 = 给单宿主加优化、给跨宿主加债。

---

## 2. 规则

### R-SP-1 业务脚本一律 python3

新增任何可执行脚本（**有业务逻辑** · 非纯宿主 lifecycle 转发）：

- ✅ 必须写在 `tools/*.py`
- ✅ 必须 `#!/usr/bin/env python3` + `chmod +x`
- ✅ 必须有对应 `tools/tests/test_*.py`（pytest · ≥3 case：happy / edge / failure）
- ❌ 不得新增任何宿主 hooks（🔴 v8.213 hooks 已全退役 · hooks/ 目录已删 · bootstrap 只做历史清理）
- ❌ 不得在 hook .sh 之外的 bash 文件里写业务流程

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

~~`hooks/*.sh` 仅允许做两类事~~(🔴 v8.213 起 hooks 全退役 · 本段仅存历史判据)：

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

所有 python 工具 stdout **必须 JSON**（参考 state.py 格式）：

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

### R-SP-6 ~ R-SP-7（v8 已废弃）

> v7 的 `render-status-line.py` / `render-afk-skip.py` / `render-flow-transition.py` / `render-decision-pause.py` 工具及关联的 feature_context auto-fill 机制,在 v8 中被 `state.py` 各命令的自 emit 行为(状态行 + JSON brief + 暂停点 markdown)取代,本节原内容已删除。

### R-SP-8 每条「🔴/必须」规则必须含「下游消费者」标注

> 🚨 **实战触发**：API-F048-Ollama 代理网关 case · 4.6 instance 自承"我跳的步骤都没有下游消费者标注"——只写"🔴 必须"但没说"跳了谁会发现 / 哪个下游会失败"· AI 内部评估为"只是仪式"而跳掉。
>
> 4.6 原话：「我跳"写了没人读"的步骤 · 不跳"下游有人依赖"的步骤」。

#### 核心规则

```
🔴 spec 中每条「🔴/必须/必填/必读/禁止/不得/强制」级规则
 = MUST 同段内含「下游消费者」标注：跳了之后谁/哪个下游会发现 / 失败 / 拒绝。

❌ writer-only 反模式（命中 → P0-146 候选修复）：
 "🔴 必须创建 state.json" ← 没写跳了谁会坏
 "🔴 PRD-REVIEW.md 必需" ← 同上
 "🔴 角色切换必须 cite" ← 同上

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
 - "state.py emit 内 cite spec hint"

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

#### 当前阶段实测数据（初始扫描）

```
Total 🔴/必须 rules: 411
With consumer: 153 (37.2%)
Missing consumer: 258 (62.8%) ← 修复方向
```

P0-146 处理 top 30 (~12% of missing) · 后续 patch 渐进推进。

---

## 3. 已存在的 python 工具（参考样板）

| 工具 | 职责 | 模式 |
|---|---|---|
| `tools/state.py` | state.json schema/状态机/evidence-binding 单源 | 子命令 + JSON 输出 |
| `tools/bootstrap.py` | session bootstrap · 骨架维护 + 历史 hooks/注入段清理 | 一次性 boot · JSON 输出 |
| `tools/verify-panorama.py` | 全景设计物化校验 | 校验 + JSON 输出 |
| `tools/post-feature.py` | Feature 收尾 · KNOWLEDGE check + ROADMAP render | 多职责聚合|

---

## 4. 迁移路径

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
❌ 业务流程在 bash hook 里直接写(hook 只做事件转发 · 业务逻辑走 python)
❌ spec 不 cite 工具调用 · 仅靠宿主 hook 自动触发（破坏 R-SP-2 · CC-only 陷阱）
❌ python 工具无对应 test_*.py（破坏 R-SP-1 · 无回归保护）

---

## 6. 与红线层级关系

- 本规范属 **L2 standards 层**（按需 read）
- L1 红线不新增条目（路径 B · 不走路径 C）
- L3 物化层 = `tools/*.py` + `tools/tests/test_*.py`
- 触发：新增脚本时必读 · PMO 起 P0 patch 涉及 hooks/ 或 tools/ 时必读
