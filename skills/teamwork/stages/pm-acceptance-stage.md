# PM Acceptance Stage

---

## 怎么做

### 1. 加载上下文
读 PRD.AC · TEST-REPORT.md · screenshots/*.png(若 browser_e2e 启用)

### 2. PM 逐条 AC 对照实现
主对话身份切换到 PM · 站在用户视角

### 3. (可选)主对话试用
若可本地跑 · PM 实测一遍关键路径

### 4. 给出三选项决策
approved_and_ship / approved_no_ship / rejected_with_feedback

### 5. complete --decision --note
rejected_with_feedback 时 --note 必填(state.py 强校验)
- approved_and_ship → 自动转 ship
- approved_no_ship → 自动转 completed
- rejected_with_feedback → 留 pm_acceptance · emit `pause_options_markdown` 列回退选项(见 §回退选项)

---

## 回退选项(rejected_with_feedback · v8.10)

pm_acceptance rejected 不强制 fix-retry(反馈类型多样)· state.py emit 4 选项给用户决策:

```
1. 代码 bug → state.py reset-prev → dev-fix → review → test → pm_acceptance 完整重走
2. AC / 需求改 → state.py jump-to-stage --to goal --reason "..." → 改 PRD + 重 review
3. UI 设计改 → state.py jump-to-stage --to ui_design --reason "..." → 改 UI
4. 放弃 Feature → state.py ship-phase --action close-unmerged --abandon=true
```

**为什么不像 review/test 走 stage 内 fix-retry**:
- pm_acceptance rejected 的反馈类型多(代码/需求/设计/放弃)· 单一 fix-retry 不够
- PM 反馈本质是流程层判断 · 适合"暂停 + 用户决策"模式
- raw-write 自动写 concerns WARN(audit 留痕)· 不是 R5 红线违规

**与 review/test fix-retry 的差异**:
| stage | 失败模式 | 处理 |
|---|---|---|
| review | NEEDS_REVISION | stage 内 fix-retry(代码 fix · 同性质) |
| test | exit_code 非 0 | stage 内 fix-retry(代码 fix · 同性质) |
| pm_acceptance | rejected | 暂停点选项(反馈多样 · 用户决策回哪) |

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | — | — | (读 PRD.AC + TEST-REPORT + 截图) |
| 2. PM 逐条 AC 对照实现 | `roles/pm.md` | § 验收规范 | 对照 TEST-REPORT 实际数据 · 不口述 OK |
| 3. (可选)主对话试用 | — | — | (无) |
| 4. 给出三选项决策 | `stages/pm-acceptance-stage.md` | § 三选项判定 | approved_and_ship / approved_no_ship / rejected_with_feedback |
| 5. complete --decision --note | — | — | (无) |


**输出格式**(每个 substep 动手前必在主对话输出):
```
📖 cite:
- <spec> § <段>:"<引该段 1 句关键原文 · 证明真读>"
```

**强约束**(R5+P0-11 软约束 · 用户监督):
- 标 "—" 的 substep 无 cite 要求(状态机操作 / 用户暂停 / 已物化)
- 其余 substep **动手前必输出 cite 块** · 缺 cite 视为 process 违规(用户可叫停)
- cite 必含 § 段标题 + 至少 1 句原文(原文必真实存在于该 spec · 不可瞎编)
- AI 在 stage 内多次切角色 · 每次切换前重新 cite 该角色规范

**为什么 cite**:
- brief 列路径(P0-4)只解决"AI 找不到路径"· 不保证 AI 真读
- complete 时校验太晚(AI 已做完)
- substep 动手前 cite = 事前提醒 · 强制 AI 翻一眼 spec
- 物化死角(state.py 看不到 markdown Read 动作)· 软约束 + 用户监督兜底

## 质量基线

📎 **物化拦截**:
- ship-start 前置 `pm_acceptance.evidence.decision=approved_and_ship`(绕过 PM 验收 → FAIL)
- rejected 必传 `--note`(state.py 必填校验)
- rejected → state.py emit `pause_options_markdown` 4 选项 · 用户选 1/2/3/4 → PMO 显式跑命令(reset-prev / raw-write)· 自动 audit

**SOP**(违反 → 漏 bug 进 ship):
- 逐条 AC 对照 TEST-REPORT 实际数据 · 不靠"看起来 OK"口述
- rejected 必明确 finding · note 含具体改什么
- `approved_no_ship` 仅用于真正"完成但等时机"(协同其他 Feature) · 不用作躲避决策

---

## Output Contract(产物形态参考)

### `state.json 决策落库`
stage_contracts.pm_acceptance.evidence.decision · 无文件产物

### `(可选)PM-NOTE.md`
决策说明 · rejected 时含 finding 列表

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `PM_ACCEPTANCE_SPEC`
- 入口规范:[../TRIAGE.md](../TRIAGE.md)
