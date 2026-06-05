# PM Acceptance Stage

---

## 怎么做

### 1. 加载上下文
读 PRD.AC · TEST-REPORT.md · screenshots/*.png(若 browser_e2e 启用)

### 2. PM 逐条 AC 对照实现
主对话身份切换到 PM · 站在用户视角

### 3. (可选)主对话试用
若可本地跑 · PM 实测一遍关键路径

### 4. 🔴 emit 三选项暂停点 · 等用户拍板(R5 用户决策点)

PM 做完 AC 验收后 · **必 emit 三选项 R5 暂停点 markdown · 然后停 · 等用户回 1/2/3** · AI 不可自决 decision:

🔴 **`auto_mode=true` 也必停此暂停点** —— 产品决策权(approved_and_ship / approved_no_ship / rejected_with_feedback)是用户专属 · AI 不能替拍(违 R3)。auto 仅跳过技术/设计/评审类暂停点(详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))。


```markdown
⏸️ PM 验收完成 · AC <N/N> 通过 · 请你拍板:

1. **approved_and_ship** 💡 推荐(若 AC 全过且可发布)
   理由:<1 句> · 动作:进 ship stage(push 分支 + 建 MR · Phase 1 仍有"等你平台合并"暂停点)
2. **approved_no_ship**
   理由:完成但暂不发(等协同 / 等时机)· 动作:Feature 直接 completed · 不 ship
3. **rejected_with_feedback**
   理由:你发现需返工的问题 · 动作:带 feedback 回退(见 §回退选项)
```

🔴 **三选项都是用户决策 · AI 自选 = 越权**:
- 哪怕选"保守"的 `approved_no_ship` 也越权 —— 它让 Feature 跳过 ship 直接 completed
- "避免未授权 push" 不是自选 `approved_no_ship` 的理由:`approved_and_ship` 进 ship 后 · Phase 1 仍有"等用户在平台合并"暂停点 · push/merge 不会自动发生
- AI 自决 decision = 违 R5(用户决策点)+ R3(用户决策被 AI 代替)

### 5. complete --decision --note(用户拍板后才跑)

用户回 1/2/3 → AI 跑 `pm_acceptance-complete --decision <用户所选>`:
- rejected_with_feedback 时 --note 必填(state.py 强校验)
- approved_and_ship → 自动转 ship
- approved_no_ship → 自动转 completed
- rejected_with_feedback → 留 pm_acceptance · emit `pause_options_markdown` 列回退选项(见 §回退选项)

---

## 回退选项(rejected_with_feedback)

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
| 4. emit 三选项暂停点 | `stages/pm-acceptance-stage.md` | § 怎么做 4 | emit 三选项 · 用户拍板 · AI 不自决 |
| 5. complete --decision --note | — | — | (用户拍板后才跑) |


📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**:
- ship-start 前置 `pm_acceptance.evidence.decision=approved_and_ship`(绕过 PM 验收 → FAIL)
- rejected 必传 `--note`(state.py 必填校验)
- rejected → state.py emit `pause_options_markdown` 4 选项 · 用户选 1/2/3/4 → PMO 显式跑命令(reset-prev / raw-write)· 自动 audit

**SOP**(违反 → 漏 bug 进 ship / 越权):
- 逐条 AC 对照 TEST-REPORT 实际数据 · 不靠"看起来 OK"口述
- 🔴 三选项 decision 必用户拍板 · AI emit 三选项后停 · 不可自决(含"保守"的 `approved_no_ship`)
- rejected 必明确 finding · note 含具体改什么
- `approved_no_ship` 仅用于真正"完成但等时机"(协同其他 Feature) · 不用作躲避决策

---

## Output Contract(产物形态参考)

> 📋 **起草模板**(避免找历史 Feature 抄):
> - PM-NOTE.md(可选)→ `{SKILL_ROOT}/templates/pm-note.md`(含 AC 逐条对照 + 三选项决策 + rejected finding 列表)
> - state.json 决策 → 由 `state.py pm_acceptance-complete --decision ...` 写 · 无文件模板

### `state.json 决策落库`
stage_contracts.pm_acceptance.evidence.decision · 无文件产物

### `(可选)PM-NOTE.md`
决策说明 · rejected 时含 finding 列表

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `PM_ACCEPTANCE_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
