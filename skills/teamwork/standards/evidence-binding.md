# 事实字段 evidence-binding 规范（v7.3.10+P0-103 抽出 · 原 SKILL.md 红线 #16）

> 🔴 **本文件是「事实字段证据绑定」的唯一权威源**。SKILL.md 红线 R7（证据闭环）顶层 cite 本文件 · 各 stage spec / role sub-file 引用本文件而非红线条号。
>
> 🟢 **抽出来源**：v7.3.10+P0-101 引入红线 #16 → v7.3.10+P0-103 红线归并时降级到 L2 专项规范层（红线层级化 · 详见 SKILL.md「红线生命周期管理」）。

---

## 一、核心规则

所有"事实型字段"（来自外部观察的判定 · 含**否定 / 空集 / 不可用 / 不存在 / 0 命中**等声明）必须含 evidence binding：

```
{
  "command": "string · 实际执行的 bash 命令",
  "stdout":  "string · 完整 stdout 原文 · 不允许改写为状态值",
  "exit_code": "integer · 0/1/127 等",
  "<时间字段>": "string · ISO 8601 UTC · 例：detected_at / pushed_at / created_at"
}
```

**缺 evidence = 流程违规 = 字段无效**。

---

## 二、为什么必须 evidence binding（实战触发）

> v7.3.10+P0-101 实战 case：用户「codex 为什么不可以用」case · PMO 凭印象写 `state.external_cross_review.available_external_clis: []` 但实际 `command -v codex` 显示 `/usr/local/bin/codex`。
>
> 根因：缺乏 evidence binding 机制 + 缺乏物理拦截手段（仅靠规则约束 AI "不要凭印象" 没用）+ 状态字段与事实字段未区分。

**stdout 原文是物理拦截**：AI 没法编造真实命令输出 · 一旦要求**写入 state.json evidence schema 的 stdout 字段**必须真跑 · 这是物理层拦截 · 不依赖 AI 自觉。

🟢 **物理拦截层级**（v7.3.10+P0-112 修订）：
- ✅ **state.json evidence schema 的 stdout 字段** 必须含真实 bash 输出（拦截层级）
- ❌ **主对话不要 verbatim 贴 stdout**（与 v7.3.10+P0-105 silent execution 协同 · 主对话只给精炼结论）
- 设计：拦截放 state.json 层（schema 完整性）· 主对话保持轻量（用户视角）

实战示例（external 探测）：

```
✅ 主对话（精炼结论）：
   🌐 External 探测：codex ✅ 可用 / claude ⏭️ 同源跳过 / gemini ❌ 未安装

✅ state.json（完整 evidence · 审计层）：
   external_cross_review.detection_evidence = {
     command: "command -v codex 2>&1; echo \"codex_exit=$?\"; ...",
     stdout: "/usr/local/bin/codex\ncodex_exit=0\n...",
     exit_code: 0,
     detected_at: "2026-05-08T08:30:00Z"
   }

❌ 反模式（v7.3.10+P0-101 之前 · v7.3.10+P0-112 删除）：
   主对话「🌐 External 探测」段 verbatim 贴 stdout + exit code
   → 主对话变重 · 与 silent execution 冲突
```

---

## 三、事实字段 vs 状态字段（边界）

| 类别 | 来源 | 是否需 evidence | 例子 |
|------|------|----------------|------|
| **事实字段** | 外部观察判定 | 🔴 必须 evidence | available_external_clis / mr_url / feature_pushed_at / tests_passed / pm_self_check.code_context_read |
| **状态字段** | PMO 自判状态机 | ❌ 不需要 | current_stage / phase / verdict / completed_stages / legal_next_stages / output_satisfied |

**区分原则**：能由外部命令验证真伪的 = 事实字段 · PMO 内部状态机推导的 = 状态字段。

---

## 四、事实字段 evidence schema 全表

| 字段路径 | evidence schema | 必填条件 |
|---------|----------------|---------|
| `external_cross_review.available_external_clis` | `detection_evidence = { command, stdout, exit_code, detected_at }` | Triage Step 4 探测后必填 |
| `ship.feature_pushed_at` / `ship.merge_target_pushed_at` | `*_push_evidence = { command, stdout, exit_code, pushed_at }` | Ship Stage push 后必填 |
| `ship.mr_url` + `ship.mr_creation_method` | `mr_creation_evidence = { method, command/url, stdout 或 user_visited_url, created_at }` | Ship Stage MR 创建后必填 |
| `tests_passed` / 各阶段测试断言 | 命令 stdout 原文 + exit code（落 review-log.jsonl） | 任何"已通过"声明必填 |
| `pm_self_check.code_context_read` | 实际读取证据（grep 历史 ToolUse 可验） | PM 验收输出 self-check 必填 |

---

## 五、PMO 出口校验（Stage 结束必做）

```
for field in 本 Stage 写入的事实字段:
    if field 在事实字段范围:
        if field._evidence 缺失 OR field._evidence.stdout 为空 OR command 字段缺失:
            → 🔴 阻断 Stage 出口
            → 主对话输出违规告警："字段 {path} 缺 evidence binding · 请补 bash 实测 + 写入 state.json stdout 字段"
            → 不得执行 § 2.3 Step 6 Write
            → 状态保持当前 Stage · 等待补证据后重走出口
```

详见 `roles/pmo-state-mgmt.md` § 2.3 Step 1.5 + § 2.4「事实字段 evidence-binding 出口校验」。

---

## 六、违规处置

- **PMO 自检发现**：立即在主对话告警 + 列出缺 evidence 的字段清单 + 给出补救命令模板（bash 实测 + 贴 stdout）· 不得 Write · 不得流转
- **用户/外部反馈发现**（事后）：作为 Bug 流程处理（PMO 起 Bug · 走 fix→ship 简化流程 · evidence 补全后回写）

---

## 七、反模式（v7.3.10+P0-101 实战触发 case）

- ❌ `available_external_clis: []` 但无 `detection_evidence` → 物理拦截：贴 `command -v codex` 完整 stdout + exit code
- ❌ `mr_url: "https://..."` 但无 `mr_creation_evidence` → 必填 method（cli/url-fallback）+ 实际命令或访问 URL
- ❌ `feature_pushed_at: "2026-05-05T..."` 但无 push stdout → 必填 `git push` 命令的 stdout（含 remote ref 行）
- ❌ "我看了一下没有" / "印象中应该是" → 🔴 这些是状态字段思维 · 事实字段必须 bash 实测后贴原文

---

## 八、与红线的关系

**SKILL.md 红线 R7（证据闭环）顶层包含三层**：
1. RD/QA 声称完成必附实际命令输出（原 #9）
2. AI Plan 模式 · 声明即承诺（原 #14）
3. **事实字段 evidence-binding 详见本文件**（原 #16 全文降级）

红线层只保留一句话引用 · 详细 schema / 反模式 / 出口校验 全部落本文件单源。

---

## 九、相关文件

- `templates/feature-state.json` — 各事实字段配套 `*_evidence` 子对象 schema
- `roles/pmo-state-mgmt.md` § 2.3 + § 2.4 — Stage 出口校验执行点
- `stages/triage-stage.md` Step 4 — `available_external_clis` 探测 + evidence 写入
- `stages/ship-stage.md` Step 2.3 — `mr_url` + `mr_creation_evidence` 写入

末。
